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

## Evidence and design

- [Week 4 architecture](docs/architecture/week4-architecture.drawio)
- [Tool catalogue](docs/architecture/tool-catalogue.md)
- [Executable JSON schemas](src/tool_contracts.py)
- [Failure/authorization evidence](docs/evaluation/tool-authorization.md)
- [Week 4 progress report (Word)](docs/weekly-reports/Week4-ProgressReport.docx)

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
