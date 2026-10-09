# Software Engineering QA Agent — Group O

BSE4104 capstone, Makerere University. The application combines requirement analysis,
RAG, approved tools, a bounded triage agent and optional persistent triage context.

## Run locally (Windows PowerShell)

Requires Python 3.13 and Ollama with `qwen3:8b` installed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3:8b
# Start Ollama if it is not already running: ollama serve
.\.venv\Scripts\python.exe -m src.app
```

Open http://127.0.0.1:5000. The app binds to loopback with debug disabled.
Use authorized or synthetic project data only. This is a trusted local demo;
there is no multi-user authentication or production deployment configuration.

## Week 4 demonstration

Use **Process QA request** to let the model choose one approved tool:

1. Ask: `What actions require human approval in the QA agent project?`
   Inspect the answer, source IDs, excerpts and request ID.
2. Ask: `Create a local issue draft titled Cart total stays zero. Failed test:
   TC-CART-04. Expected: cart total updates after quantity change. Actual:
   displayed total stayed at zero. Do not submit it.`
   Open the returned path under `evidence/drafts`; verify `submitted: false`.
3. Ask to run a shell command or deploy. The router should decline. Even if
   the model proposes a prohibited tool, deterministic validation prevents execution.

The two direct forms remain available for manual tool testing. The QA app does
not execute tests, publish issues, merge, deploy or provide an approval bypass.

```powershell
# Run the current test suite
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Run the three demonstration requests above through the web interface. They make
up to three routing calls plus one grounded-answer call.
Each model call has a timeout; CPU inference can be slow. Failure is recorded
as failure, without substituting a mocked success. Requests, decisions and full
tool results are retained locally in `evidence/traces/tool_requests/`.

## Week 5 bounded agent

The **Run triage agent** form (route `/agent`) runs one goal-directed loop on a failure you report:
Sense, Decide, Validate, Act, Observe, then Stop or Re-plan. The model only picks the next action
(`retrieve_project_evidence`, `create_issue_draft` or `ask_human`). Code enforces the limits (6 iterations,
3 retrievals, 1 draft, 2 consecutive tool failures, 2 invalid decisions, 900 s), saves one local draft,
and hands off to a human on any other stop. It cannot run tests, submit, merge or deploy.

```powershell
# Offline checks: scripted decisions, real retrieval, draft writes and SQLite (46 tests)
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Traces are written to `evidence/traces/agent_runs/` and summarised in `evidence/traces/week5_live_demo.json`.
Trace 3 uses a labelled fault injection (the first retrieval raises) to show recovery.

- [Agent architecture](docs/architecture/week5-agent-architecture.drawio) ([SVG](docs/architecture/week5-agent-architecture.svg))
- [Agent task contract](docs/architecture/agent-task-contract.md) (limits are executable in `src/agent_contracts.py`)
- [Current planner prompt](prompts/agent-planner-v1.1.txt) (v1.0 retained for earlier traces)

## Week 6 memory and state demonstration

Each triage run that reaches final processing saves a small local summary in `memory/run_history.sqlite3`.
The database is excluded from Git. Reuse is optional: select **use history** in the
triage form to include the prior report count and last outcome for the exact test ID.
Reports are human-supplied; a repeated report does not prove a repeated test failure.

1. Enter a synthetic failure with a unique test ID and run the triage agent with history selected.
2. Restart the application and repeat the same test ID with history selected. Inspect
   the previous report count and the trace's fresh retrieval before drafting.
3. Open **Run history**, search that identifier and delete a summary. Search again to
   verify its removal. Deleting summaries does not delete separate traces or drafts.

The saved [live demonstration](evidence/traces/week6_memory_demo.json) used real local
Qwen3:8b in two separate processes. Both runs completed with fresh retrieval and
unsubmitted drafts; the second loaded one prior report. All seven demonstration
checks passed, including deletion after reopening the store. Its temporary database
was cleared; the retained synthetic traces and drafts are the evidence.

History retains up to 90 days and 500 summaries. Expiry is checked on access, and the
record cap is applied on save. The app is for a trusted local operator, with loopback
hosting, Host/Origin checks and CSRF-protected deletion, but no multi-user login.
Storage failures produce warnings without granting new authority or discarding an
already-created draft. The [46-test result](evidence/traces/week6_verification.json)
includes persistence, concurrency, retention, deletion and guard checks.

- [Editable state model](docs/architecture/week6-state-model.drawio)
- [Memory design and data handling](docs/architecture/week6-memory-design.md)
- [MCP-style interface specification (Word)](docs/architecture/Week6_Interface_Specification.docx)
- [Week 6 progress report (Word)](docs/weekly-reports/Week6-ProgressReport.docx)

The implemented query adapter is `GET /api/history?failed_test=YOUR-TEST-ID&limit=5`.
This is a local HTTP endpoint and documented MCP-style capability, not a live MCP server.

## Evidence and design

- [Week 4 architecture](docs/architecture/week4-architecture.drawio)
- [Tool catalogue](docs/architecture/tool-catalogue.md)
- [Executable JSON schemas](src/tool_contracts.py)
- [Failure/authorization evidence](docs/evaluation/tool-authorization.md)
- [Week 4 progress report (Word)](docs/weekly-reports/Week4-ProgressReport.docx)
- [Week 5 progress report (Word)](docs/weekly-reports/Week5-ProgressReport.docx)

The Markdown catalogue/evaluation documents are the current specifications.
Earlier Word copies and the broad context/DFD diagrams are historical snapshots;
the Week 4 architecture distinguishes implemented capabilities from future work.

Maintain weekly reports directly as editable Word (`.docx`) documents and
architecture diagrams as editable draw.io (`.drawio`) files. Update the Word report directly after
confirming individual contributions and Week 4 ClickUp task links.

Earlier verification files are historical snapshots. The current suite contains 46
checks; a direct test run also updates the older test modules' evidence files.
Human code review and confirmed individual contribution records remain outstanding.
