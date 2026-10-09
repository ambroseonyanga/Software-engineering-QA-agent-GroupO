# Memory Design and Data Handling Note
**Project:** Software Engineering QA Agent  
**Group:** Group O  
**Week:** 6 — Memory, State and Interoperability  

---

## 1. Overview

Week 5 kept working state within a run and saved separate audit traces. Week 6 adds one justified case of **persistent memory**: a **triage-run history store** that lets the agent and operator find earlier reports for the same test. These are reported failures, not independently executed test results.

This document defines what is stored, why, how it is structured, who can access it, and when it is deleted.

---

## 2. Memory Types in This System

| Memory layer | Scope | Where it lives | Week introduced |
|---|---|---|---|
| **In-run session state** | One `run_agent()` call | Python dict in-process | Week 5 |
| **Audit trace** | One run, permanent | `evidence/traces/agent_runs/<run_id>.json` | Week 5 |
| **Run history store** | Cross-run, persistent | `memory/run_history.sqlite3` (new, Week 6) | Week 6 |
| **Known-flaky-test register** | Proposed, not implemented | Proposed `memory/known_flaky_tests.json` | Deferred |

The audit trace already existed from Week 5. The SQLite store is the implemented Week 6 addition. The original flaky-register proposal is retained in section 4.2 for context.

---

## 3. Justified Use Case: Prior Test-Run History

### 3.1 Why this memory is warranted

Without cross-run memory the agent treats every failure report as its first. A human operator has to manually look at past traces to find previous triage work. Persisting a lightweight run summary enables:

1. **Previous report awareness.** When history reuse is selected, the Sense digest includes the number of previous reports and the last triage outcome for the same `failed_test`.
2. **Operator lookup.** The history page shows previous summaries and their draft and source IDs. Repeated source links can be inspected, but do not establish a defect or fragile requirement by themselves.

The originally proposed flaky-test suppression is not implemented. Repeated reports alone do not show that a test is flaky.

### 3.2 What the memory changes (and what it does not)

The memory **informs** but does not **control**. Specifically:

- The agent **may** include prior-run context in the Sense digest (as a `"prior_context"` field) when the operator selects history reuse and the same `failed_test` has been seen before.
- The agent **may not** skip the retrieval step because a past run found sources, change its stop conditions, or alter the draft content based on memory alone.
- The human operator **must** still review the draft; prior history is displayed as context, not as a decision.
- If the history store is unavailable (file locked, disk full), the agent runs without prior context, not with a stale read. `SERVICE_UNAVAILABLE` is not raised for this; the run proceeds and logs a warning.

---

## 4. Data Design

### 4.1 Run history store (`memory/run_history.sqlite3`)

A SQLite `runs` table stores the run ID, test identifier, timestamp and a JSON summary. One entry is saved transactionally when a run reaches final processing. Invalid input and initial audit-storage failure return before saving. The following is an illustrative summary, not a recorded execution:

```json
[
  {
    "run_id": "3f9a1b2c1234567890abcdef12345678",
    "recorded_utc": "2026-10-07T14:32:01Z",
    "failed_test": "test_requirement_parser_empty_input",
    "provenance": "human_reported_failure",
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
| `provenance` | Identifies the record as a human-reported failure | Low |
| `stop_reason` | Triage outcome, not a test pass/fail result | Low |
| `iterations_used` | Efficiency tracking | Low |
| `retrievals_used` | Retrieval pattern | Low |
| `draft_id` | Links to the draft file for the human to find | Low |
| `linked_source_ids` | Up to five references for operator inspection | Low |
| `elapsed_seconds` | Latency tracking | Low |

**Fields NOT stored:** `title`, `expected`, `actual`, `notes`, full source excerpts, model analysis text, raw model decisions. These remain only in the full audit trace, which is already stored per-run in `evidence/traces/agent_runs/`.

### 4.2 Proposed known-flaky-test register (not implemented)

The original design proposed a JSON object at `memory/known_flaky_tests.json`, keyed by `failed_test`, with entries managed only by a **human operator**. This remains a proposal; the current application neither creates nor reads this file. The original illustrative structure is retained below:

```json
{
  "test_requirement_parser_empty_input": {
    "flagged_by": "human",
    "flagged_utc": "2026-10-07T10:00:00Z",
    "reason": "Non-deterministic on CI due to file ordering"
  }
}
```

The proposed `flaky_warning` is not part of the implemented Sense digest. Adding it later would require verified evidence and an explicit review process.

---

## 5. How Memory Is Used in the Agent Loop

History is loaded before the loop, passed into **Sense**, and saved after terminal processing:

1. If reuse is selected, query SQLite for an exact match to the trimmed `failed_test` identifier.
2. Add `prior_context` only when an earlier retained report exists. Pass only the report count and last outcome to the model.
3. Save a bounded summary when the run finishes. Record explicit workflow transitions in the audit trace; see [the state model](week6-state-model.drawio).

```python
"prior_context": {
  "prior_report_count": 3,
  "last_stop_reason": "COMPLETED",
  "meaning": "Previous triage reports, not independently verified test executions."
}
```

The model can recognise that earlier triage work exists. Previous sources and notes are not supplied to it, and history cannot bypass validation or replace fresh retrieval.

Memory is **never** used to:
- Pre-fill the draft
- Skip retrieval
- Alter stop conditions or limits
- Infer a fix or root cause that bypasses the retrieval step

---

## 6. Who Can Access the Memory

| Actor | Run history | Flaky register |
|---|---|---|
| Agent (read) | Optional lookup before Sense | Not implemented |
| Agent (write) | Yes — append after run | **No** |
| Human operator (read) | Yes, through `/history` or the local query API | Not implemented |
| Human operator (write) | Individual deletion through `/history/delete` | Not implemented |
| External services | No | No |
| Web interface (`/agent` route) | Reads run history to show recurrence count to user | No |

The SQLite database is local and excluded from Git through `memory/` in `.gitignore`. It is not synced externally. The app binds to loopback and checks Host and browser POST Origin headers. This is a trusted single-operator application, without multi-user authentication; filesystem access depends on the operating-system account.

---

## 7. Data Handling

### 7.1 What is stored vs. what is not

The run history record is a **summary**, not a copy of the trace. The most sensitive parts of a run — the failure description text, the model's raw analysis, source excerpts — remain only in the per-run audit trace under `evidence/traces/agent_runs/`. If the history store were leaked, it would reveal test names and requirement IDs, not the content of the requirements or the model's analysis.

### 7.2 Retention and deletion

| Data | Retention policy | Deletion mechanism |
|---|---|---|
| Run history entries | Up to 90 days and 500 entries | Expired entries are trimmed on access; saving retains the newest 500. The operator can delete an individual summary with a session CSRF token. |
| Known-flaky register entries | Proposed only | Not implemented. |
| Full audit traces | Kept indefinitely for evidence purposes | Manual deletion by a project owner. |

The limits are enforced by `HistoryStore._connection()` and `HistoryStore.save()` in `src/memory_service.py`. Expiry is maintenance on access, not a background job. Deleting a summary does not remove separate traces, drafts, exported evidence or backups. SQLite `secure_delete` is enabled, but does not guarantee erasure from disk snapshots.

### 7.3 Atomic writes

The implementation uses SQLite transactions instead of the proposed JSON write-then-rename pattern. Insertion and record-cap trimming commit together. The lock timeout is two seconds, and duplicate run IDs cannot overwrite earlier summaries.

### 7.4 Failure handling

If the history store cannot be read (file corrupt, disk full, permission error):
- The agent logs a warning and proceeds without prior context.
- The run is not blocked; `SERVICE_UNAVAILABLE` is not raised.

If the history store cannot be written after a run:
- A warning is added to the run result (`"memory_warnings"` list).
- The run result and audit trace are still returned normally.

An already-created draft remains in the result if saving history fails. The separate query capability returns `SERVICE_UNAVAILABLE` when storage cannot be read; the agent itself continues with a warning.

---

## 8. Memory Does Not Silently Control Decisions

To demonstrate that memory improves the task without controlling critical decisions:

| Scenario | What memory does | What it does NOT do |
|---|---|---|
| Same test has 3 earlier reports and reuse is selected | Adds `prior_report_count: 3` to Sense digest | Does not claim three verified failures, change limits, skip retrieval or pre-fill the draft |
| Flaky-test handling | Deferred proposal | Does not flag or suppress a report automatically |
| Linked sources from a past run exist | Not included (past sources are not passed to the model) | Does not seed this run's evidence or replace retrieval |
| History store unavailable | Run proceeds without prior context, warning logged | Does not stop the run or raise `SERVICE_UNAVAILABLE` |

Every decision the agent makes is still validated by the same deterministic guards from Week 5. Prior-run context is advisory input to the model — it does not grant the model any additional authority or bypass any approval control.

The saved [live demonstration](../../evidence/traces/week6_memory_demo.json) used a synthetic report in two separate Qwen3:8b processes. The second loaded one previous report; both retrieved fresh evidence and created unsubmitted drafts. Deletion survived reopening the store. All seven demonstration checks passed. The [46-test result](../../evidence/traces/week6_verification.json) also covers retention, concurrency, corruption and guards. This demonstrates continuity, not a measured improvement in diagnosis.

---

## 9. MCP-Style Interface (Integration Deliverable)

To satisfy the Week 6 "implement one external integration OR document one project capability as an MCP-style interface" requirement, the **run history query capability** is documented as an MCP-style tool interface below.

This is a specification of how an external client (e.g., a CI system or another agent) could call the QA agent's memory query capability if it were exposed. It is not yet implemented as a live MCP server; it is a documented interface.

The Python capability is implemented in `src/memory_service.py`, with a local `GET /api/history` adapter. The schema below describes successful responses. Invalid inputs return `ok: false` with `VALIDATION_ERROR` (HTTP 400); unavailable storage returns `SERVICE_UNAVAILABLE` (HTTP 503). No matches return HTTP 200 with zero count, null last outcome and an empty `runs` array. See the [interface specification](Week6_Interface_Specification.docx) for the complete boundary.

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
      "last_stop_reason": { "type": ["string", "null"] },
      "runs": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "recorded_utc": { "type": "string" },
            "stop_reason": { "type": "string" },
            "draft_id": { "type": ["string", "null"] },
            "failed_test": { "type": "string" },
            "provenance": { "const": "human_reported_failure" },
            "iterations_used": { "type": "integer", "minimum": 0 },
            "retrievals_used": { "type": "integer", "minimum": 0 },
            "elapsed_seconds": { "type": "number", "minimum": 0 },
            "linked_source_ids": { "type": "array", "maxItems": 5, "items": { "type": "string" } }
          }
        }
      }
    }
  }
}
```

Authorization: read-only, local session only. Does not expose full audit trace content, draft content, or model analysis text.

Query access performs housekeeping: it initialises an absent store and prunes expired records. It cannot add reports or invoke tools. Deletion is a separate operator POST action protected by a session CSRF token, not a model capability.

---

## 10. Summary

| Question | Answer |
|---|---|
| What is stored? | Run summary: test name, stop reason, linked requirement IDs, timing, draft ID |
| Why? | Find earlier triage reports for the same test |
| Who can read it? | Agent (Sense step), human operator, web interface |
| Who can write it? | Application saves summaries; local operator can delete them |
| How long is it kept? | 90 days or 500 entries for run history; indefinitely for audit traces |
| How is it deleted? | Expiry on access, record cap on save, or individual operator deletion; traces remain separate |
| Does it control decisions? | No — it is advisory input to the Sense step only; all guards still apply |
| Is it synced externally? | No — local files only, listed in `.gitignore` |
