# Memory Design and Data Handling Note
**Project:** Software Engineering QA Agent  
**Group:** Group O  
**Week:** 6 — Memory, State and Interoperability  

---

## 1. Overview

Week 5 established that all agent state is in-run only — discarded when `run_agent()` returns. Week 6 makes one justified case of **persistent memory** concrete: a **test-run history store** that records the outcome of every agent run so that the agent and the human operator can reason about patterns across runs (e.g., repeated failures on the same test, known flaky tests, which requirements are linked most often).

This document defines what is stored, why, how it is structured, who can access it, and when it is deleted.

---

## 2. Memory Types in This System

| Memory layer | Scope | Where it lives | Week introduced |
|---|---|---|---|
| **In-run session state** | One `run_agent()` call | Python dict in-process | Week 5 |
| **Audit trace** | One run, permanent | `evidence/traces/agent_runs/<run_id>.json` | Week 5 |
| **Run history store** | Cross-run, persistent | `memory/run_history.json` (new, Week 6) | Week 6 |
| **Known-flaky-test register** | Cross-run, human-curated | `memory/known_flaky_tests.json` (new, Week 6) | Week 6 |

The audit trace already existed from Week 5. The two new files are the Week 6 memory additions.

---

## 3. Justified Use Case: Prior Test-Run History

### 3.1 Why this memory is warranted

Without cross-run memory the agent treats every failure report as its first. A human operator has to manually look at past traces to notice that the same test has failed three times in a row, or that a particular requirement (e.g., SRC-007) is linked to every failing test. Persisting a lightweight run summary enables:

1. **Recurring failure detection.** If the same `failed_test` name appears in ≥ 2 runs, the agent can include that context in its Sense step ("this test has failed N times before").
2. **Known-flaky-test suppression.** Tests recorded as flaky by a human can be flagged in the draft notes so the operator knows to treat the failure sceptically.
3. **Requirement hot-spot awareness.** If a particular source document (e.g., `user_stories.md` chunk 3) is repeatedly linked, that signals a fragile area of the specification.

### 3.2 What the memory changes (and what it does not)

The memory **informs** but does not **control**. Specifically:

- The agent **may** include prior-run context in the Sense digest (as a `"prior_context"` field) when the same `failed_test` has been seen before.
- The agent **may not** skip the retrieval step because a past run found sources, change its stop conditions, or alter the draft content based on memory alone.
- The human operator **must** still review the draft; prior history is displayed as context, not as a decision.
- If the history store is unavailable (file locked, disk full), the agent runs without prior context, not with a stale read. `SERVICE_UNAVAILABLE` is not raised for this; the run proceeds and logs a warning.

---

## 4. Data Design

### 4.1 Run history store (`memory/run_history.json`)

A JSON array. One entry is appended atomically after every `run_agent()` call that reaches a terminal state (any stop reason except `SERVICE_UNAVAILABLE` before the loop starts).

```json
[
  {
    "run_id": "3f9a1b2c...",
    "recorded_utc": "2026-10-07T14:32:01Z",
    "failed_test": "test_requirement_parser_empty_input",
    "stop_reason": "COMPLETED",
    "iterations_used": 3,
    "retrievals_used": 2,
    "draft_id": "DRAFT-a3b4c5d6e7f8",
    "linked_source_ids": ["SRC-003", "SRC-007"],
    "elapsed_seconds": 47.2
  }
]
```

**Fields stored:**

| Field | Why stored | Sensitivity |
|---|---|---|
| `run_id` | Links back to the full audit trace for inspection | Low — a UUID |
| `recorded_utc` | Ordering and retention calculation | Low |
| `failed_test` | The key for recurrence detection | Medium — reveals test names |
| `stop_reason` | Pattern analysis (how often does it fail vs. complete?) | Low |
| `iterations_used` | Efficiency tracking | Low |
| `retrievals_used` | Retrieval pattern | Low |
| `draft_id` | Links to the draft file for the human to find | Low |
| `linked_source_ids` | Requirement hot-spot detection | Low |
| `elapsed_seconds` | Latency tracking | Low |

**Fields NOT stored:** `title`, `expected`, `actual`, `notes`, full source excerpts, model analysis text, raw model decisions. These remain only in the full audit trace, which is already stored per-run in `evidence/traces/agent_runs/`.

### 4.2 Known-flaky-test register (`memory/known_flaky_tests.json`)

A JSON object keyed by `failed_test` name. Entries are created and deleted only by a **human operator** — never written by the agent.

```json
{
  "test_requirement_parser_empty_input": {
    "flagged_by": "human",
    "flagged_utc": "2026-10-07T10:00:00Z",
    "reason": "Non-deterministic on CI due to file ordering"
  }
}
```

The agent reads this file at Sense time (if it exists) and adds a `"flaky_warning"` field to the digest when the current `failed_test` is listed. The agent never writes to this file.

---

## 5. How Memory Is Used in the Agent Loop

The only change to the loop is in the **Sense** step. `_sense()` is extended to:

1. Load `memory/run_history.json` (if it exists); filter entries where `failed_test` matches the current report.
2. Load `memory/known_flaky_tests.json` (if it exists); check if `failed_test` is listed.
3. Add a `"prior_context"` key to the digest only if at least one prior run exists for this test.

```python
"prior_context": {
  "prior_run_count": 3,
  "last_stop_reason": "COMPLETED",
  "flaky_warning": "Non-deterministic on CI due to file ordering"   # only if in register
}
```

The model can use this context to make a better-targeted query (e.g., citing the specific requirement area that was linked last time), but it cannot act on it in any way that bypasses validation or skips a required step.

Memory is **never** used to:
- Pre-fill the draft
- Skip retrieval
- Alter stop conditions or limits
- Infer a fix or root cause that bypasses the retrieval step

---

## 6. Who Can Access the Memory

| Actor | Run history | Flaky register |
|---|---|---|
| Agent (read) | Yes — Sense step only | Yes — Sense step only |
| Agent (write) | Yes — append after run | **No** |
| Human operator (read) | Yes | Yes |
| Human operator (write) | Yes (manual cleanup / retention) | **Yes** (sole author) |
| External services | No | No |
| Web interface (`/agent` route) | Reads run history to show recurrence count to user | No |

The memory files are **local files only**. They are not synced to any external service, API, or database. They stay within the project directory. They are listed in `.gitignore` to prevent accidental commit of operational data.

---

## 7. Data Handling

### 7.1 What is stored vs. what is not

The run history record is a **summary**, not a copy of the trace. The most sensitive parts of a run — the failure description text, the model's raw analysis, source excerpts — remain only in the per-run audit trace under `evidence/traces/agent_runs/`. If the history store were leaked, it would reveal test names and requirement IDs, not the content of the requirements or the model's analysis.

### 7.2 Retention and deletion

| Data | Retention policy | Deletion mechanism |
|---|---|---|
| Run history entries | 90 days or 500 entries, whichever comes first | Trimmed on write: entries older than 90 days or beyond the 500-entry limit are removed before the new entry is appended. |
| Known-flaky register entries | Until a human removes them | Human deletes the key from the JSON file. |
| Full audit traces | Kept indefinitely for evidence purposes | Manual deletion by a project owner. |

The 90-day / 500-entry limit is enforced by `_trim_history()` in `src/memory_service.py`, called atomically with the append. This prevents unbounded file growth without requiring a separate cron job.

### 7.3 Atomic writes

The history file is written using a write-then-rename pattern (`tmpfile → rename`) to avoid a corrupt state if the process is interrupted mid-write.

### 7.4 Failure handling

If the history store cannot be read (file corrupt, disk full, permission error):
- The agent logs a warning and proceeds without prior context.
- The run is not blocked; `SERVICE_UNAVAILABLE` is not raised.

If the history store cannot be written after a run:
- A warning is added to the run result (`"memory_warning"` field).
- The run result and audit trace are still returned normally.

---

## 8. Memory Does Not Silently Control Decisions

To demonstrate that memory improves the task without controlling critical decisions:

| Scenario | What memory does | What it does NOT do |
|---|---|---|
| Same test failed 3 times before | Adds `prior_run_count: 3` to Sense digest | Does not change iteration limit, skip retrieval, or pre-fill the draft |
| Test is in the flaky register | Adds `flaky_warning` to Sense digest | Does not automatically mark the draft as "flaky" or suppress the run |
| Linked sources from a past run exist | Not included (past sources are not passed to the model) | Does not seed this run's evidence or replace retrieval |
| History store unavailable | Run proceeds without prior context, warning logged | Does not stop the run or raise `SERVICE_UNAVAILABLE` |

Every decision the agent makes is still validated by the same deterministic guards from Week 5. Prior-run context is advisory input to the model — it does not grant the model any additional authority or bypass any approval control.

---

## 9. MCP-Style Interface (Integration Deliverable)

To satisfy the Week 6 "implement one external integration OR document one project capability as an MCP-style interface" requirement, the **run history query capability** is documented as an MCP-style tool interface below.

This is a specification of how an external client (e.g., a CI system or another agent) could call the QA agent's memory query capability if it were exposed. It is not yet implemented as a live MCP server; it is a documented interface.

```json
{
  "name": "query_run_history",
  "description": "Query the QA agent's run history for a given test name. Returns recurrence count, last outcome, and linked requirement IDs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "failed_test": {
        "type": "string",
        "description": "The exact test identifier to look up.",
        "minLength": 1,
        "maxLength": 200
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of past runs to return. Default 5.",
        "minimum": 1,
        "maximum": 20
      }
    },
    "required": ["failed_test"],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "ok": { "type": "boolean" },
      "failed_test": { "type": "string" },
      "run_count": { "type": "integer" },
      "last_stop_reason": { "type": "string" },
      "linked_source_ids": {
        "type": "array",
        "items": { "type": "string" }
      },
      "runs": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "recorded_utc": { "type": "string" },
            "stop_reason": { "type": "string" },
            "draft_id": { "type": "string" }
          }
        }
      }
    }
  }
}
```

Authorization: read-only, local session only. Does not expose full audit trace content, draft content, or model analysis text.

---

## 10. Summary

| Question | Answer |
|---|---|
| What is stored? | Run summary: test name, stop reason, linked requirement IDs, timing, draft ID |
| Why? | Recurrence detection and known-flaky-test awareness |
| Who can read it? | Agent (Sense step), human operator, web interface |
| Who can write it? | Agent appends run summaries; human curates the flaky register |
| How long is it kept? | 90 days or 500 entries for run history; indefinitely for audit traces |
| How is it deleted? | Automatic trim on write (run history); manual (flaky register, traces) |
| Does it control decisions? | No — it is advisory input to the Sense step only; all guards still apply |
| Is it synced externally? | No — local files only, listed in `.gitignore` |
