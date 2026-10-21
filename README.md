# Software Engineering QA Agent — Group O

BSE4104 capstone, Makerere University. The application connects a requirements PDF and a local codebase, suggests executable Python tests, records approval of selected tests, runs them in Docker and produces an editable Word QA report. It also answers project questions, prepares local issue drafts and runs bounded failure triage. It does not publish issues.

## Run locally on Windows

Requires Python 3.13, internet access and a Groq API key. Save `GROQ_API_KEY` as a Windows user environment variable, then restart the terminal and any application launching Python. Keep the value out of source files and Git.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Check presence without printing the key:
.\.venv\Scripts\python.exe -c "import os; print('Key available' if os.getenv('GROQ_API_KEY') else 'Key missing')"
.\.venv\Scripts\python.exe -B -m src.app
```

Open http://127.0.0.1:5000. The app binds to loopback with debug disabled. It is a trusted local demonstration with no multi-user login. Use authorised or synthetic inputs: requirements, questions, failure reports and selected excerpts are sent to Groq. Retrieval, drafts and the history database remain local. Each model request has a 90-second timeout; rate limits stop the request without automatic retries.

The default model is `qwen/qwen3.8-27b`; `GROQ_MODEL` can override it. A different model needs its own evaluation. The application reads these files directly:

| Capability | Prompt | Temperature | Completion limit |
| --- | --- | --- | --- |
| Candidate tests | `prompts/prompt-v1.2.txt` | 0.3 | 2048 |
| PDF and code test proposals | `prompts/workflow-tests.txt` | 0.2 | 2200 |
| Project answers | `prompts/rag-answer-v1.0.txt` | 0.2 | 1200 |
| One tool decision | `prompts/tool-router-v1.0.txt` | 0 | 1000 |
| Agent planning | `prompts/agent-planner-v1.1.txt` | 0 | 1000 |

The separate Week 2 evaluation script uses its own saved settings. Its scores cannot be assumed to apply unchanged to these application settings. Tool and planner calls request JSON mode; code validates the returned object before allowing actions.

## Use the workspace

- **QA workflow:** upload a text-based PDF, enter the local application folder, select BudgetMe/Django or Python/unittest, and review the automatically extracted requirements list and source file list. Generate suggestions directly; there is no requirement-selection step. Select some or all tests, approve them, run them in Docker, and download the Word report. Approval and execution are separate actions.
- **Test cases:** paste a requirement and inspect candidate tests. These are proposals for review, not test executions.
- **Project knowledge:** ask about the registered project documents. Inspect the excerpts as well as the answer.
- **Failure triage:** enter a reported failure. The agent retrieves evidence and may save one local draft, or hands back control with a stop reason.
- **Tools:** ask for one approved capability or use the direct forms.
- **History:** look up an exact test identifier and optionally delete a summary.

The RAG corpus contains five registered documents and currently 26 chunks. The source register allows only authorised files inside `knowledge/corpus`. Retrieval uses 180-word chunks, TF-IDF and cosine similarity, retaining at most three chunks scoring at least 0.08. Restart the app after changing the corpus or register. A retained match is not proof that a source answers the question. The charter and user stories include planned capabilities; implementation limits are stated in the tool and agent contracts.

## Demonstrate the two tools

In **Tools**, try these requests when API quota is available:

1. `What actions require human approval before an issue is submitted?`
2. `Create a local issue draft titled Proposed tests lack requirement links. Failed test: QA-LINK-01. Expected: each proposed test links to a requirement. Actual: no links shown. Do not submit.`
3. `Run a shell command and deploy this project now.`

Inspect the actual tool result and trace. Draft records stay under `evidence/drafts` with `submitted: false`. Model-routed traces are under `evidence/traces/tool_requests`. The model-facing tools still block execution, publication and deployment. The separate QA workflow checks local human approval before Docker execution.

## PDF to sandbox workflow

Start Docker Desktop before running tests. The workflow uses the local `budgetme-sandbox:local` image prepared with `sandbox/budgetme/Dockerfile` and its dependency list. If that image is missing, restore the dependencies-only base with:

```powershell
docker build -t budgetme-sandbox:local -f sandbox/workflow/Dockerfile.base sandbox/budgetme
```

Sessions, uploaded PDFs, source snapshots, proposals, approval records and execution evidence are stored under `%LOCALAPPDATA%\GroupOQA\sessions`, outside the repository. `QA_WORKFLOW_HOME` can override the storage folder. Source snapshots exclude environment files, databases, uploads, dependency folders, credentials by filename and `settings.py`. Review source excerpts for hardcoded secrets before sending them to Groq. The original codebase is never mounted in the test containers or edited.

Each request proposes up to three tests. Each proposal is a test group containing up to 20 synchronous unittest methods. Simple standalone test functions without fixtures are adapted to unittest before review. Unsupported proposals are omitted with an explanation; other valid proposals remain available. The backend validates the response schema and Python syntax without executing it. Approval records the code hashes and source snapshot hash; changed snapshots or approved code cannot run. Only selected tests are copied into a trusted image. Each test runs separately with no network, a non-root user, a read-only root filesystem, a temporary writable `/tmp`, a 512 MB memory limit, one CPU, 64 processes and a 90-second timeout. Container output is bounded. Cancel stops the current run. Temporary build contexts, containers and run images are cleaned up; the dependency base remains reusable.

The current adapters support BudgetMe's Django application with a disposable SQLite database and standard Python unittest projects using dependencies already in the image. Other languages, browser automation, scanned-PDF OCR and automatic dependency installation are not supported. Suggestions use at most 2,400 characters of extracted requirement records and 3,500 characters of selected Python source, with an 8,000-character limit on the serialized context; they do not establish full requirements coverage. Word reports distinguish assertion failures, execution errors, skipped tests, timeouts and tests not run. Reports do not require another model call. A new code version or revised test set requires a new session after approval.

The workflow verification uses scripted model responses and synthetic requirements to check wiring without consuming API quota. The optional Docker check runs a real BudgetMe calculation test and a deliberately failing verification test, while leaving a third test unselected:

```powershell
$env:QA_DOCKER_TESTS = '1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_workflow.py'
Remove-Item Env:QA_DOCKER_TESTS
```

## Bounded triage and memory

The agent follows Sense, Decide, Validate, Act, Observe, then Stop or Re-plan. Code enforces six iterations, three retrieval attempts, one draft, two consecutive tool failures, two invalid decisions and a 900-second budget checked between iterations. A retrieval must complete before drafting, even if it finds no useful source. Draft facts come from the human report; model analysis is labelled unverified.

Each run reaching final processing saves a summary in `memory/run_history.sqlite3`, excluded from Git. Optional reuse sends only the prior report count and last outcome to the model. It cannot skip fresh retrieval or change permissions. History retains at most 500 summaries for up to 90 days, with expiry on access. Deleting a summary does not delete traces, drafts or backups.

To demonstrate continuity, use a unique synthetic test ID, run triage with history enabled, restart the app, and repeat that ID. Inspect the earlier-report count and fresh retrieval. Then delete a summary from History and query again. This procedure makes live model calls; do not run it while the quota is blocked.

`GET /api/history?failed_test=YOUR-TEST-ID&limit=5` is the implemented local adapter. The [Word interface specification](docs/architecture/Week6_Interface_Specification.docx) documents an MCP-style capability; the project does not implement an MCP server.

## Verification and current gaps

```powershell
# Offline: scripted model decisions/transport, real local retrieval and temporary storage
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v

# Live: run only when quota is available and within the agreed remaining request budget
.\.venv\Scripts\python.exe -B scripts/verify_groq_workflows.py --max-requests 35
```

The live runner writes a new timestamped folder, stops at HTTP 429 and never retries automatically. Its maximum applies to that invocation, not the account's lifetime use. Count earlier requests before choosing the remaining budget. It includes 15 RAG questions, tool routing, three agent scenarios and memory reuse with a reopened store. The recovery scenario deliberately fails its first retrieval and is labelled as fault injection. Reopening a store in one process is not a process-restart test.

Current evidence, revised 16 October 2026:

- [54 offline checks passed](evidence/traces/offline_verification_20261016.json).
- [15 retrieval-only cases](evidence/traces/rag_retrieval_20261016.json): 12 matched the expected-file/empty-result criterion. This is not a model-answer pass rate; the [RAG evaluation](docs/evaluation/RAG_Evaluation.docx) explains incomplete evidence and irrelevant matches.
- [Live Groq interruption](evidence/traces/groq_workflows_20261016T153951Z/verification.json): one baseline QA response succeeded; the first RAG call received HTTP 429. No further live calls were made. RAG generation, routed tools, three agent traces and the refreshed memory demonstration remain pending.
- Earlier `week4_live_demo.json`, `week6_memory_demo.json` and verification files describe the previous local Qwen3:8b setup. They remain historical evidence and do not prove the migrated workflows work with Groq.

The original Week 5 live-demo file is absent. Do not treat a script that could generate traces as evidence that the traces exist. Individual contributions, ClickUp links and human implementation review remain pending confirmation. The earlier 16 October verification used route rendering and output escaping checks. The 21 October UI verification below adds browser inspection.

## Deliverables

- [RAG architecture](docs/architecture/week3-rag-architecture.drawio) and [source register](knowledge/Corpus_Source_Register.xlsx)
- [Tool architecture](docs/architecture/week4-architecture.drawio), [catalogue](docs/architecture/Tool_Catalogue.docx) and [authorization evidence](docs/evaluation/Tool_Authorization_Evidence.docx)
- [Agent architecture](docs/architecture/week5-agent-architecture.drawio) and [task contract](docs/architecture/agent-task-contract.md)
- [State model](docs/architecture/week6-state-model.drawio) and [existing memory design](docs/architecture/week6-memory-design.md)
- [Week 3 report](docs/weekly-reports/Week3-ProgressReport.docx), [Week 4 report](docs/weekly-reports/Week4-ProgressReport.docx), [Week 5 report](docs/weekly-reports/Week5-ProgressReport.docx), [Week 6 report](docs/weekly-reports/Week6-ProgressReport.docx)

The editable draw.io files describe the current architecture. Existing SVG/PNG diagrams are earlier snapshots. Weekly reports remain editable Word documents. The AI Engineering Log is a required assignment record; update it only from actual prompts, changes, decisions and reviews.


## Six screen workspace update 21 October 2026

The Flask workspace now has Dashboard, Projects, Requirements, Test Review,
Execution, and Results & Reports screens. Projects lists saved QA sessions;
each session uses its own source snapshot. The shared layout includes persistent
light and dark themes and a collapsible assistant. The assistant uses the existing
indexed project knowledge service; it does not query uploaded session requirements.

Start from Requirements. Connect an application folder and upload a text PDF or
enter requirements manually. If both are provided, manual text takes precedence.
Use requirement IDs, shall/must statements, and acceptance criteria to help extraction.
Choose Suggest tests to generate descriptions without executable code. In Test
Review, approve selected descriptions to generate their code automatically. Inspect
that code and session activity in Execution, then start the sandbox separately.
Existing sessions that already contain code retain their original approval flow.
Code generation failures return the descriptions to review and leave them unrunnable.

Results & Reports shows recorded outcomes and existing Word/evidence downloads.
Failed assertions include an editable local issue-draft form connected to the existing
draft tool. This does not submit an issue to an external tracker. Unselected proposals
do not receive code in the new workflow and are still included in reports.

Verification used offline model fixtures and temporary storage outside this repository.
The selected regression suite ran 58 checks: 56 passed and two optional Docker checks
were skipped. Browser inspection covered the dashboard in both themes, assistant
expansion, manual requirement submission, and requirements layouts at 390, 820 and
1265 pixel viewport widths. Mobile and tablet checks found no page overflow. Browser
logs reported no warnings or errors during the manual-entry check. Live Groq generation,
real Docker execution and a full accessibility audit were not performed for this update.
See `evidence/traces/ui_refinement_20261021.json` and `tests/test_workspace_ui.py`.

Run the relevant offline checks from the project folder with the tests folder on the
Python import path (the existing memory tests import shared fixtures from that folder):

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'tests')
.\.venv\Scripts\python.exe -B -m unittest tests.test_workflow tests.test_workspace_ui tests.test_requirement_extraction tests.test_integration tests.test_memory tests.test_budgetme_target
```


## Current project navigation

This correction supersedes the earlier six-screen global navigation described above.
The application opens on Dashboard. The global sidebar contains Dashboard, Projects,
Recent Activity and Settings. Dashboard uses saved project summaries and events;
it has no requirement form or run controls. Projects uses cards and a Connect New
Project view. Connection takes a source snapshot before requirements are added.

Selecting a project opens five separate views: Overview, Requirements, Test Cases,
Executions and Reports. These tabs appear only inside a selected project. New
snapshots retain their source path for grouping. Older snapshots, which did not
record that path, are grouped by their saved project name and test environment.

Requirements supports PDF upload and individual entries with an ID, title and
description. Duplicate IDs are rejected. Requirements are locked after approval;
connect a new snapshot to revise them. Before approval, a requirement update
archives and clears earlier proposals. Cases are grouped under their requirement,
including acceptance-criterion references such as FR-014-AC02 under FR-014.
Pending cases can be edited, approved or rejected. Editing a rejected case restores
it to review. Approval generates code; it does not execute it. Additional pending
cases can be approved while earlier approved cases remain ready. Approved code
hashes and snapshot checks remain enforced. Execution requires an explicit Run.

Reports uses recorded outcomes and output. Failure analysis calls the existing
bounded triage agent only when Analyze Failure is selected. Saved analysis and
issue drafts stay linked to the selected snapshot. Word and evidence exports use
the existing routes. The contextual assistant uses selected project records when
opened within a project; outside it, the existing project-knowledge service is used.
Light and dark themes persist in browser storage. The main palette is blue and slate;
green is reserved for successful outcomes.

Verification: 69 checks ran, with 67 passed and two optional Docker checks skipped.
Browser checks covered global navigation, all five project tabs, both themes,
case edit/reject/approval, code readiness without execution, project connection,
individual requirement entry, contextual assistant expansion and layouts at 390,
820 and 1280 pixels. Mutation checks used an isolated, clearly labelled offline
fixture. Existing BudgetMe records were inspected without rerunning their tests.
Live Groq responses, new Docker runs and a full accessibility audit were not verified.
The original prototype artifact could not be retrieved from the referenced chat;
the correction follows the user's explicit navigation, layout and colour requirements.
See `tests/test_project_navigation.py` and
`evidence/traces/ui_prototype_correction_20261021.json`.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'tests')
.\.venv\Scripts\python.exe -B -m unittest tests.test_workflow tests.test_workspace_ui tests.test_project_navigation tests.test_requirement_extraction tests.test_integration tests.test_memory tests.test_budgetme_target
```
