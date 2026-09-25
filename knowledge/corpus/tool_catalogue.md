# Tool Catalogue and Tool/API Schemas

Project: Software Engineering QA Agent
Group: Group O
Week: 4 — Tools and Function Calling

This catalogue defines the first two explicit tools for the Software Engineering QA Agent. The tools continue the Week 1 workflow and the Week 1 AI Boundary Matrix. The model may request a tool by name. Deterministic application code validates the request, checks authorization, and then executes the tool. The model does not invent tool results, execute tests, or submit issues.

## Allow-list

Approved tools:

- retrieve_project_evidence
- create_issue_draft

Requests for run_tests, submit_issue, merge_pr, deploy or shell are rejected before any side effect. These remain higher-impact actions and require human approval in a later week.

## Tool 1: retrieve_project_evidence

Purpose: Retrieve current authorized project documentation from the Week 3 controlled corpus and return source-grounded evidence. This satisfies the Week 4 requirement that at least one tool retrieves current application data.

Authorization: Allowed for a local developer session. Read-only. The tool may use only files listed in the source register. It must not access secrets, modify the repository, or run shell commands.

Input schema: query is a required string of 3 to 300 characters. top_k is an optional integer from 1 to 5 and defaults to 3.

Output schema: ok, grounded, sources and answer. Sources include source id, file name, chunk id, score and excerpt. If the corpus does not support the question, the tool uses the Week 3 insufficient-information message.

Failure behaviour: a missing or short query returns VALIDATION_ERROR without calling the model. An unavailable corpus, index or model returns SERVICE_UNAVAILABLE and does not invent an answer. An unexpected retrieval payload returns UNEXPECTED_TOOL_RESPONSE.

## Tool 2: create_issue_draft

Purpose: Create a low-risk simulated side effect by writing a draft issue or pull-request note as a local record. This implements user story US-09. The record remains a draft. It is not posted to GitHub and is not treated as an approved defect decision.

Authorization: Creating a draft is allowed. Submitting, merging, deploying or running tests is not allowed. If a caller requests submit, merge, deploy or execute, the tool refuses that higher-impact action. A valid draft may still be stored, but submitted remains false.

Input schema: title is required and must be 8 to 120 characters. failed_test is required. expected, actual and notes are optional.

Output schema: ok, draft_id, status, path and submitted. Status is always draft. submitted is always false.

Failure behaviour: missing title or failed_test returns VALIDATION_ERROR and writes no file. A submit or merge request returns UNAUTHORIZED. A write failure returns SERVICE_UNAVAILABLE.

## Orchestration rule

All tool calls pass through the application tool service. That module applies the allow-list, validates the input schema, executes only approved tools, and records a trace for Week 4 evidence.
