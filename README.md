# Software Engineering QA Agent — Group O

BSE4104 capstone, Makerere University. The application proposes test cases from requirements, answers questions from registered project documents, prepares local issue drafts and runs bounded failure triage with optional history. It does not execute tests or publish issues.

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
| Project answers | `prompts/rag-answer-v1.0.txt` | 0.2 | 1200 |
| One tool decision | `prompts/tool-router-v1.0.txt` | 0 | 1000 |
| Agent planning | `prompts/agent-planner-v1.1.txt` | 0 | 1000 |

The separate Week 2 evaluation script uses its own saved settings. Its scores cannot be assumed to apply unchanged to these application settings. Tool and planner calls request JSON mode; code validates the returned object before allowing actions.

## Use the workspace

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

Inspect the actual tool result and trace. Draft records stay under `evidence/drafts` with `submitted: false`. Model-routed traces are under `evidence/traces/tool_requests`. Higher-impact actions are blocked even if a model requests them; no approval-and-execution path is implemented.

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

The original Week 5 live-demo file is absent. Do not treat a script that could generate traces as evidence that the traces exist. Individual contributions, ClickUp links and human implementation review remain pending confirmation. The current browser preview could not be inspected because no controllable browser was available; route rendering and output escaping were checked offline.

## Deliverables

- [RAG architecture](docs/architecture/week3-rag-architecture.drawio) and [source register](knowledge/Corpus_Source_Register.xlsx)
- [Tool architecture](docs/architecture/week4-architecture.drawio), [catalogue](docs/architecture/Tool_Catalogue.docx) and [authorization evidence](docs/evaluation/Tool_Authorization_Evidence.docx)
- [Agent architecture](docs/architecture/week5-agent-architecture.drawio) and [task contract](docs/architecture/agent-task-contract.md)
- [State model](docs/architecture/week6-state-model.drawio) and [existing memory design](docs/architecture/week6-memory-design.md)
- [Week 3 report](docs/weekly-reports/Week3-ProgressReport.docx), [Week 4 report](docs/weekly-reports/Week4-ProgressReport.docx), [Week 5 report](docs/weekly-reports/Week5-ProgressReport.docx), [Week 6 report](docs/weekly-reports/Week6-ProgressReport.docx)

The editable draw.io files describe the current architecture. Existing SVG/PNG diagrams are earlier snapshots. Weekly reports remain editable Word documents. The AI Engineering Log is a required assignment record; update it only from actual prompts, changes, decisions and reviews.
