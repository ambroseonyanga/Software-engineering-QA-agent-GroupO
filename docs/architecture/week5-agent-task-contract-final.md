# Agent Task Contract
**Project:** Software Engineering QA Agent  
**Group:** Group O  
**Week:** 5 — Agent Architecture and Bounded Autonomy  
**Source of truth:** `src/agent_contracts.py`, `src/agent.py`

---

## 1. Goal

**Failure triage and draft preparation.**  
Given one human-reported test failure, the agent links the failure to authorized project requirements and prepares one local draft issue for human review. It does not run tests, submit issues, or take any action that modifies the repository, CI pipeline, or any external service.

This task benefits from multi-step agentic decision-making because the correct next action depends on what the previous step returned: a retrieval may find nothing (requiring re-planning with different wording), a tool may fail (requiring retry within a limit or hand-off), and a draft is only worth saving after at least one retrieval has been attempted.

**Goal state (done):** One draft exists in `evidence/drafts/` with `status: draft` and `submitted: false`, its notes list the retrieved requirement sources (or state that none were found), and a complete trace exists in `evidence/traces/agent_runs/<run_id>.json`.

---

## 2. Input

One failure report supplied by a human operator. It is treated as **untrusted data** throughout — the agent validates it against a JSON Schema before the loop starts and rejects unknown fields.

| Field | Type | Required | Rule |
|---|---|---|---|
| `title` | string | Yes | 8–120 characters |
| `failed_test` | string | Yes | 1–200 characters |
| `expected` | string | No | ≤1000 characters |
| `actual` | string | No | ≤1000 characters |

If validation fails, the run stops immediately with `REJECTED_INPUT` and no tool is called.

---

## 3. Approved Tools / Actions

The model chooses **one action per iteration**. The application re-validates every decision; constrained decoding via Ollama's `format` field additionally restricts what the model can emit structurally.

| Action | Kind | Contract |
|---|---|---|
| `retrieve_project_evidence` | Approved tool (Week 4) | `query` 3–300 chars, `top_k` fixed at 3. Returns source evidence only (`generate=False`). Read-only. Never modifies files. |
| `create_issue_draft` | Approved tool (Week 4) | The application fills `title`, `failed_test`, `expected`, `actual` from the **human report** — never from model text. The model supplies only a short `analysis` (≤600 chars), appended to `notes` labelled "unverified". Always a local draft; `submitted=false`. |
| `ask_human` | Hand-off action | Terminates the run and returns the model's question or reason to the human. No tool is invoked. |

**Permanently blocked — never executed:**  
`run_tests`, `submit_issue`, `merge_pr`, `deploy`, `shell`, and any decision that sets `submit`, `merge`, `deploy`, or `execute` to `true`. If the model names any of these, the run stops immediately with `HANDOFF_APPROVAL_REQUIRED`; nothing is executed and no partial state is retained.

---

## 4. Agent Loop

```
Sense → Decide → Validate → Act → Observe → Stop / Re-plan
```

**Step 1 — Sense:** The orchestrator (`_sense()` in `src/agent.py`) builds a compact state digest the model is allowed to see:
- The goal string
- The original failure report (untrusted data label)
- Limits remaining (iterations, retrievals)
- The last 4 observations from `state["history"]`

The model never sees internal counters, completed queries, or raw evidence scores.

**Step 2 — Decide:** The digest is sent to the local Qwen3:8b model via Ollama's `/api/generate` endpoint with `format: MODEL_FORMAT_SCHEMA`. Temperature = 0, max 350 tokens, 120-second timeout. The model returns one JSON object: `{ "action", "query", "analysis", "message" }`.

**Step 3 — Validate (deterministic guards):** The application independently validates:
- `HIGHER_IMPACT_FLAGS` (`submit`, `merge`, `deploy`, `execute`) → `HANDOFF_APPROVAL_REQUIRED`
- Action name against `PROHIBITED_NAMES` → `HANDOFF_APPROVAL_REQUIRED`
- JSON Schema validation against `DECISION_SCHEMA`
- Action in `AGENT_ACTIONS` list
- For retrieve: query ≥ 3 chars, not a repeated query, retrieval budget not exhausted
- For draft: at least one retrieval succeeded, no draft already exists

**Step 4 — Act:** All tool calls go through `invoke_tool()` in `src/tool_service.py`, which independently re-checks the allow-list and re-validates arguments (double-validation pattern). The model cannot bypass the guard layer to reach the tool layer.

**Step 5 — Observe:** Outcomes are classified as: `grounded`, `not_grounded`, `tool_error`, `blocked`, `invalid_decision`, `draft_saved`, `handoff`, or `model_unavailable`. The outcome is appended to `state["history"]` and written to the audit trace.

**Step 6 — Stop or Re-plan:** Stop conditions are evaluated. If none trigger, `state["iteration"]` is incremented and the loop repeats from Step 1 with the new observation in history.

---

## 5. State (in-run, not persisted)

State is held by the orchestrator as a Python dict for the duration of one `run_agent()` call only. It is not written to disk and is discarded when the call returns.

| Field | Type | Purpose |
|---|---|---|
| `task` | dict | The validated failure report. Immutable after input validation. |
| `iteration` | int | Current decide/act cycle number. |
| `retrievals` | int | Total retrieval attempts, including failed ones. |
| `completed_queries` | set | Normalized queries that returned `ok=True`. Blocks duplicate retrieval calls. |
| `evidence` | list | Grounded sources accumulated across all retrievals, deduplicated by `(source, chunk_id)`, sorted by score descending. |
| `history` | list | Growing list of compact observation dicts. Model sees only the last 4. |
| `consecutive_failures` | int | Tool errors in a row. Resets on any successful tool result. |
| `invalid_decisions` | int | Rejected model decisions in this run. |
| `draft` | dict or None | The saved draft record once it exists, else `None`. |

---

## 6. Limits

Defined in `src/agent_contracts.py` as `LIMITS`. The orchestrator enforces all limits; the model has no authority over them.

| Limit | Value | Enforcement point |
|---|---|---|
| Maximum iterations | 6 | Top of loop in `run_agent()` |
| Maximum retrieval attempts | 3 | Guard in the retrieve branch |
| Maximum drafts per run | 1 | Guard in the draft branch |
| Maximum consecutive tool failures | 2 | After Act step |
| Maximum invalid decisions | 2 | After Validate step |
| Wall-clock budget | 900 seconds | Top of loop |

---

## 7. Stop Conditions and Human Hand-off

Every stop reason other than `COMPLETED` is a **human hand-off**. The agent never overrides a limit; continuing after a limit requires a human to start a new run.

| Stop Reason | Trigger |
|---|---|
| `COMPLETED` | A draft was saved. Stops immediately; no extra model call. |
| `HANDOFF_NEEDS_INFO` | The model chose `ask_human`. |
| `HANDOFF_APPROVAL_REQUIRED` | Decision named a blocked action or set a higher-impact flag. Nothing was executed. |
| `STOPPED_MAX_ITERATIONS` | 6 iterations used without saving a draft. |
| `STOPPED_TIME_BUDGET` | 900 seconds elapsed. |
| `STOPPED_TOOL_FAILURE` | 2 consecutive tool errors. |
| `STOPPED_INVALID_DECISIONS` | 2 rejected model decisions. |
| `STOPPED_MODEL_UNAVAILABLE` | `decide_with_model()` raised an exception or timed out. |
| `REJECTED_INPUT` | Failure report failed JSON Schema validation. Agent never started. |
| `SERVICE_UNAVAILABLE` | Trace storage was not writable before run start. Agent never started. |

**Human approval conditions** follow the Week 1 AI Boundary Matrix. The agent cannot submit or post an issue, run tests, merge, deploy, access secrets, or continue past any stop condition. A human reviews the draft at `evidence/drafts/` and the trace at `evidence/traces/agent_runs/`, then acts outside the agent.

---

## 8. Guards Summary

| Guard | Consequence |
|---|---|
| Draft before any successful retrieval | Blocked; observation recorded |
| Repeated query (same normalized form) | Blocked; not counted as a failure |
| Retrieval beyond the 3-call budget | Blocked; observation recorded |
| Second draft attempt | Blocked; observation recorded |
| Draft facts from model text | Structurally impossible — app fills those fields from the human report |
| Decision with unknown fields / unknown action | Rejected; `invalid_decisions` counter incremented |
| Trace directory not writable | Run never starts (`SERVICE_UNAVAILABLE`) |

---

## 9. Evidence

| Evidence type | Location |
|---|---|
| Per-run audit trace (JSON) | `evidence/traces/agent_runs/<run_id>.json` |
| Offline guard tests (24 cases) | `tests/test_agent.py` + `evidence/traces/week5_agent_tests.json` |
| Live traces with Qwen3 model | `scripts/capture_week5_traces.py` → `evidence/traces/week5_live_demo.json` |
| Tool call summary log | `evidence/traces/week4_tool_calls.json` |

---

## 10. Known Limitations

- The agent does not execute tests. It triages a failure a human reports; test execution remains blocked until an approval path is built.
- Retrieval is TF-IDF keyword matching over ~15 documents. A grounded result means a chunk scored above 0.08 cosine similarity, not that it is the correct requirement.
- The model analysis in the draft is labelled "unverified opinion" and cannot be treated as a confirmed diagnosis.
- CPU inference with Qwen3:8b can be slow; a run may take several minutes within the 900-second budget.
