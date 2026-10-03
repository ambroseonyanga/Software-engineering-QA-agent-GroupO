# Agent Task Contract

Project: Software Engineering QA Agent
Group: Group O
Week: 5 — Agent Architecture and Bounded Autonomy

This contract defines the one bounded agent task implemented in `src/agent.py`. The numeric limits are executable constants in `src/agent_contracts.py`; the orchestrator enforces them, the model does not.

## Task

**Failure triage and draft preparation.** Given one human-reported test failure, the agent links the failure to authorized project requirements and prepares one local draft issue for human review. It supports user stories US-07 (investigate failed tests), US-09 (prepare an issue report), US-10 (review agent actions) and US-11 (control agent execution).

This task needs multi-step decisions because the right next step depends on what the last step returned. A retrieval may find nothing, so the agent must re-plan with different wording or hand off. A tool may fail, so the agent must retry within a limit or stop. A draft is only worth saving after evidence has been looked for.

**Goal state (done):** one draft exists in `evidence/drafts/` with `status: draft` and `submitted: false`, its notes list the retrieved requirement sources (or state that none were found), and a complete trace exists in `evidence/traces/agent_runs/`.

## Input

One failure report supplied by a human. It is untrusted data. Unknown fields are rejected.

| Field | Rule |
| --- | --- |
| title | required, 8 to 120 characters |
| failed_test | required, 1 to 200 characters |
| expected | optional, up to 1000 characters |
| actual | optional, up to 1000 characters |

## Actions

The model chooses one action per iteration. Constrained decoding offers only these three, and the application re-validates every decision.

| Action | Kind | Contract |
| --- | --- | --- |
| retrieve_project_evidence | Approved tool (Week 4) | query 3 to 300 characters. The agent calls it with top_k 3 and no generation, so it returns source evidence only. Read-only. |
| create_issue_draft | Approved tool (Week 4) | The application fills title, failed_test, expected and actual from the human report. The model supplies only a short analysis. The application writes the notes: retrieved sources first, then the model analysis labelled unverified. Always a local draft. |
| ask_human | Hand-off | Ends the run and returns the model's question or reason to the human. |

**Prohibited, never available:** run_tests, shell, submit_issue, merge_pr, deploy, secret access, and any submit, merge, deploy or execute flag. If a decision names one, the run stops with HANDOFF_APPROVAL_REQUIRED and nothing is executed. There is still no approval-and-execution path; a human performs those actions outside the agent.

## State

Held by the orchestrator for the current run only. It is not persisted between runs; persistent memory is Week 6 work.

| Field | Purpose |
| --- | --- |
| task | The validated failure report. |
| iteration | Current decide/act cycle number. |
| retrievals | Retrieval attempts made, including failed ones. |
| completed_queries | Normalized queries that returned successfully. Used to block repeats. |
| evidence | Grounded sources collected so far, best score first. |
| history | Compact observations. The model sees the last four. |
| consecutive_failures | Tool errors in a row. Reset by any successful tool result. |
| invalid_decisions | Rejected model decisions this run. |
| draft | The saved draft record, once it exists. |

## Loop

Sense, Decide, Validate, Act, Observe, then Stop or Re-plan.

1. **Sense.** Build a compact state: goal, failure report, limits remaining, last four observations.
2. **Decide.** The model returns one JSON decision under `prompts/agent-planner-v1.0.txt`.
3. **Validate.** Deterministic guards check the decision (see Guards).
4. **Act.** Execute the approved tool through `invoke_tool`, which re-applies the Week 4 allow-list and argument schemas.
5. **Observe.** Record the outcome as one of grounded, not_grounded, tool_error, blocked, invalid_decision, draft_saved or handoff.
6. **Stop or Re-plan.** Stop if a stop condition holds. Otherwise the next iteration re-plans from the new observation.

## Limits

| Limit | Value |
| --- | --- |
| Maximum iterations | 6 |
| Maximum retrieval attempts | 3 |
| Maximum drafts | 1 |
| Maximum consecutive tool failures | 2 |
| Maximum invalid decisions | 2 |
| Wall-clock budget | 900 seconds |

## Guards

- A draft is blocked until at least one retrieval has succeeded.
- A repeated query is blocked and not executed.
- A retrieval beyond the budget is blocked.
- A second draft is blocked.
- Draft facts come from the human report, never from model text.
- Decisions with unknown fields, unknown actions or missing required fields are rejected.
- A trace must be writable before any tool runs.

## Stop conditions and hand-off

Every stop other than COMPLETED is a human hand-off. The agent never overrides a limit; continuing after a limit requires a human to start a new run.

| Stop reason | Trigger |
| --- | --- |
| COMPLETED | A draft was saved. This stops the run immediately with no extra model call. |
| HANDOFF_NEEDS_INFO | The model chose ask_human. |
| HANDOFF_APPROVAL_REQUIRED | A decision named a blocked action or set submit, merge, deploy or execute. |
| STOPPED_MAX_ITERATIONS | Six iterations used without a draft. |
| STOPPED_TIME_BUDGET | 900 seconds exceeded. |
| STOPPED_TOOL_FAILURE | Two tool errors in a row. |
| STOPPED_INVALID_DECISIONS | Two rejected decisions. |
| STOPPED_MODEL_UNAVAILABLE | The decision call failed or timed out. |
| REJECTED_INPUT | The failure report failed validation. Nothing ran. |
| SERVICE_UNAVAILABLE | Trace storage was not writable. Nothing ran. |

**Human approval conditions** follow the Week 1 AI Boundary Matrix. The agent cannot submit or post an issue, run tests, merge, deploy, access secrets or continue past a stop condition. The human reviews the draft and the trace, then acts.

## Evidence

- Trace per run: `evidence/traces/agent_runs/<run_id>.json`. It records model, prompt version, limits, each step's sensed state, raw decision, guard result, tool arguments, tool result, timings and the final stop reason.
- Offline guard tests: `tests/test_agent.py`, with results in `evidence/traces/week5_agent_tests.json`. Model decisions in these tests are scripted; retrieval and draft writes are real.
- Live traces: `scripts/capture_week5_traces.py` runs three scenarios with the local Qwen3 model and writes `evidence/traces/week5_live_demo.json`.

## Known limitations

- The agent does not execute tests. It triages a failure that a human reports, because test execution stays blocked until the approval path exists.
- Retrieval is TF-IDF keyword matching over about 15 documents. A grounded result means a chunk scored above the threshold, not that it is the correct requirement.
- The model analysis is unverified opinion and is labelled so in the draft.
- CPU inference is slow, so a run can take several minutes.
