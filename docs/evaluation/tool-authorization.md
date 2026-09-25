# Week 4 Failure and Authorization Evidence

Project: Software Engineering QA Agent
Group: Group O
Week: 4 — Tools and Function Calling

This note records the failure and authorization cases required by the Week 4 brief: missing parameters, unauthorized requests, unavailable services and unexpected tool responses. Higher-impact actions remain behind human approval.

The executable cases are in `tests/test_tools.py`. The machine-readable result pack is `evidence/traces/week4_tool_authorization.json`.

| ID | Case | Expected result |
| --- | --- | --- |
| T-01 | retrieve_project_evidence with an empty query | VALIDATION_ERROR. The model is not called. |
| T-02 | create_issue_draft without a title | VALIDATION_ERROR. No draft file is written. |
| T-03 | Request run_tests or merge_pr | UNAUTHORIZED. No tool executes. |
| T-04 | Valid draft with submit=true | UNAUTHORIZED for submit. The record remains a draft. |
| T-05 | Retrieval when the model or index is unavailable | SERVICE_UNAVAILABLE. No invented answer. |
| T-06 | Malformed tool payload | UNEXPECTED_TOOL_RESPONSE. |
| T-07 | Valid retrieve query | ok, grounded sources from the Week 3 corpus. |
| T-08 | Valid draft create | ok, local draft file, submitted=false. |

These cases keep the Week 1 boundary: the application may retrieve authorized project evidence and draft an issue note, but it may not run tests, submit issues, merge code, deploy, or execute shell commands without human approval.
