# Software Engineering QA Agent — Group O

BSE4104 capstone, Makerere University. Week 4 adds two approved tools and a
single model-selected tool call to the requirement-analysis and RAG application.

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
# Run the eight retained tool tests
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
# Offline guard tests: scripted decisions, real retrieval and draft writes (28 tests incl. Week 4)
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v

# Capture the three live traces with local qwen3:8b (slow on CPU; results are kept as observed)
.\.venv\Scripts\python.exe scripts\capture_week5_traces.py
```

Traces are written to `evidence/traces/agent_runs/` and summarised in `evidence/traces/week5_live_demo.json`.
Trace 3 uses a labelled fault injection (the first retrieval raises) to show recovery.

- [Agent architecture](docs/architecture/week5-agent-architecture.drawio) ([SVG](docs/architecture/week5-agent-architecture.svg))
- [Agent task contract](docs/architecture/agent-task-contract.md) (limits are executable in `src/agent_contracts.py`)
- [Planner prompt](prompts/agent-planner-v1.0.txt)

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

The saved 19-test verification is a historical result. Only the original eight
tests remain in `tests/`; the expanded suite must be restored to reproduce all
19 checks. Running the retained tests updates `week4_tool_authorization.json`.
The assignment-required AI Engineering Log still needs to be supplied.
