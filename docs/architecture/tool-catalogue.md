# Tool Catalogue and Tool/API Schemas

Project: Software Engineering QA Agent
Group: Group O
Week: 4 — Tools and Function Calling

This catalogue defines the first two explicit tools for the Software Engineering QA Agent. The tools continue the Week 1 workflow and the Week 1 AI Boundary Matrix. The model may request a tool by name. Deterministic application code validates the request, checks authorization, and then executes the tool. The model does not invent tool results, execute tests, or submit issues.

## Allow-list

Approved tools:

- `retrieve_project_evidence`
- `create_issue_draft`

Requests for `run_tests`, `submit_issue`, `merge_pr`, `deploy` or `shell` are rejected before any side effect. These remain higher-impact actions and require human approval in a later week.

## Tool 1: retrieve_project_evidence

Purpose: Retrieve current authorized project documentation from the Week 3 controlled corpus and return source-grounded evidence. This satisfies the Week 4 requirement that at least one tool retrieves current application data.

Authorization: Allowed for a local developer session. Read-only. The tool may use only files listed in `knowledge/source_register.csv`. It must not access secrets, modify the repository, or run shell commands.

### Input schema

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| query | string | Yes | 3 to 300 characters |
| top_k | integer | No | 1 to 5. Default 3 |

### Output schema

| Field | Type | Meaning |
| --- | --- | --- |
| ok | boolean | True when the tool completed validation and retrieval |
| grounded | boolean | True when at least one chunk met the retrieval threshold |
| sources | array | Source id, file name, chunk id, score and excerpt |
| answer | string | Grounded answer, or the Week 3 insufficient-information message |

### Failure behaviour

| Condition | Error | Behaviour |
| --- | --- | --- |
| Missing or short query | VALIDATION_ERROR | No retrieval and no model call |
| Invalid top_k | VALIDATION_ERROR | No retrieval |
| Corpus, index or model unavailable | SERVICE_UNAVAILABLE | No invented answer |
| Unexpected retrieval payload | UNEXPECTED_TOOL_RESPONSE | Safe error, no write |

## Tool 2: create_issue_draft

Purpose: Create a low-risk simulated side effect by writing a draft issue or pull-request note as a local record. This implements user story US-09. The record remains a draft. It is not posted to GitHub and is not treated as an approved defect decision.

Authorization: Creating a draft is allowed. Submitting, merging, deploying or running tests is not allowed. If a caller requests `submit`, `merge`, `deploy` or `execute`, the tool refuses that higher-impact action. A valid draft may still be stored, but `submitted` remains false.

### Input schema

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| title | string | Yes | 8 to 120 characters |
| failed_test | string | Yes | Identifies the failed test or observed problem |
| expected | string | No | Expected behaviour when known |
| actual | string | No | Actual behaviour when known |
| notes | string | No | Additional QA notes |
| submit | boolean | No | If true, the submit request is rejected |

### Output schema

| Field | Type | Meaning |
| --- | --- | --- |
| ok | boolean | True when a draft record was stored |
| draft_id | string | Identifier such as DRAFT-001 |
| status | string | Always `draft` |
| path | string | Relative path under `evidence/drafts` |
| submitted | boolean | Always false |

### Failure behaviour

| Condition | Error | Behaviour |
| --- | --- | --- |
| Missing title or failed_test | VALIDATION_ERROR | No file is written |
| Submit, merge, deploy or execute requested | UNAUTHORIZED | Draft may be stored; it is not submitted |
| Draft folder cannot be written | SERVICE_UNAVAILABLE | No silent success |
| Unexpected write payload | UNEXPECTED_TOOL_RESPONSE | No silent success |

## Orchestration rule

All tool calls pass through `src/tool_service.py`. That module is the application orchestration layer. It applies the allow-list, validates the input schema, executes only approved tools, and records a trace in `evidence/traces/week4_tool_calls.json`.
