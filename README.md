# Software Engineering QA Agent — Group O

BSE4104 capstone. A local Flask application connects a code folder, accepts requirements, proposes tests, records review, executes approved cases in Docker and produces an editable Word QA report. Project Knowledge answers from selected saved records and repository-bound evidence. Bounded failure triage can prepare a local issue draft. It does not publish issues, merge code or deploy applications.

## Run on Windows

Use Python 3.13. Create a virtual environment, install requirements.txt, set GROQ_API_KEY in the launching environment and restart that terminal. Keep credentials out of Git.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B -m src.app
```

Open http://127.0.0.1:5000. The app is a trusted local demonstration, bound to loopback with debug disabled; it has no multi-user login. The default model is qwen/qwen3.8-27b through Groq. GROQ_MODEL can override it, but a changed configuration needs evaluation. Model calls have a 90-second timeout and no automatic retry after a rate limit. Only public, synthetic or authorized inputs should be used: questions, reports and selected excerpts are sent to Groq.

## Project and evidence handling

Connect a local application folder. Public repository URL cloning is not implemented. The existing BudgetMe checkout was matched to GitHub commit a55e0b28ba5ce00c0ca6034854abbab9ae444938 on 22 October 2026. The connection copied 100 supported files into session storage, not into this submission repository. Later source changes require a fresh snapshot and review.

Sessions, uploads, requirements, proposals, source snapshots, approvals and execution evidence are under %LOCALAPPDATA%/GroupOQA/sessions; QA_WORKFLOW_HOME can override that path outside the repository. Snapshot filters exclude .git, dependency directories, environment files, databases, credentials by filename and settings.py. These filters do not establish that every source excerpt is free of hardcoded sensitive data.

The CSV and Excel source registers both contain 19 authorized Markdown documents: five QA Agent governance records and 14 BudgetMe records. BudgetMe material includes six SRS groups preserving 30 functional requirements and 90 acceptance criteria, the four original repository summaries, and four focused documents covering data rules, authentication/API contracts, test coverage and observed failures. SRS-derived requirements, proposed quality targets, open decisions and measured results retain distinct provenance. QA Agent governance and target-system evidence have different purposes. Project failure analysis searches supplied session requirements and its bound repository corpus. An unbound project does not fall back to QA Agent documents. Global legacy retrieval still searches the authorized register. Restart the application after code/corpus changes.

Project Knowledge includes selected saved requirements, cases/results/drafts, source excerpts and bound corpus evidence. Its complete serialized question/context is capped at 6000 characters, with a 700-token answer allowance. Sources shown are those actually included. Similarity and a source filename are not proof of support. A generated answer does not establish a passing test.

## Safe test workflow

Review proposed descriptions and generated code, approve selected cases and explicitly choose Run. Approval binds code and source hashes. Tests run in isolated Docker containers with no network, a non-root user, a read-only root filesystem, temporary writable storage, resource/output limits and a 90-second test timeout. BudgetMe uses a disposable SQLite test database. The original source checkout is not mounted or edited. Current adapters support BudgetMe/Django and Python/unittest projects with dependencies already in the image.

Start Docker Desktop and prepare the local base image if missing:

```powershell
docker build -t budgetme-sandbox:local -f sandbox/workflow/Dockerfile.base sandbox/budgetme
```

Reports distinguish passed assertions, failed assertions, execution errors, skipped cases and tests not run. A generated test setup error is not automatically an application defect. PDF extraction requires readable text; scanned-PDF OCR and automatic dependency installation are not supported.

## Tools agent and memory

The model-facing allow-list contains retrieve_project_evidence and create_issue_draft. Schema validation and permissions remain deterministic. Drafts are local and unsubmitted. The bounded triage agent has six iterations, three retrievals, one draft, two consecutive tool failures, two invalid decisions and a 900-second budget checked between iterations. It must retrieve before drafting and hand control back when needed.

SQLite history retains at most 500 validated triage summaries for up to 90 days. Standalone triage supports opt-in reuse of prior report count and last outcome; fresh retrieval and all guards still apply. Project failure analysis currently uses use_history=False: it saves the current summary but does not consult earlier summaries. Reopening a store is not claimed as a process-restart demonstration. Deleting a summary does not delete traces, drafts or backups.

query_run_history has a local HTTP adapter at GET /api/history and an MCP-style interface specification. An actual MCP server is not required or claimed.

## Evidence and deliverables

- [Evaluation results](docs/evaluation/Evaluation_Results.docx)
- [RAG evaluation](docs/evaluation/RAG_Evaluation.docx)
- [Source register](knowledge/Corpus_Source_Register.xlsx)
- [Tool evidence](docs/evaluation/Tool_Authorization_Evidence.docx)
- [Failure catalogue](docs/evaluation/Failure_Catalogue.docx)
- [Final scenario dataset](docs/evaluation/Final_Evaluation_Dataset.csv) and [measured results](docs/evaluation/Final_Evaluation_Results.csv)
- [Week 7 report](docs/weekly-reports/Week7-ProgressReport.docx)
- [Final engineering report](docs/Final_Engineering_Report.docx)
- [Presentation](docs/presentation/Final_Presentation.pptx)
- [Evidence index](evidence/final/README.md)
- [Current system architecture SVG](docs/architecture/final-system-architecture.svg)
- [Existing RAG architecture SVG](docs/architecture/updated-rag-architecture.svg)
- [Agent architecture SVG](docs/architecture/week5-agent-architecture.svg)
- [State model SVG](docs/architecture/state-model.svg)

The earlier SVG diagrams remain available as milestone views; the final system SVG describes the current combined boundaries. Week 1–6 Word reports and the required AI Engineering Log remain under docs/. Week 2 is an early model baseline, not an evaluation of a workflow that did not yet exist.

Current offline checks: evidence/traces/offline_regression_20261022.json. Current live Week 3–6 verification: evidence/traces/milestones_20261022T154858Z/verification.json. That pack retains actual outcomes and earlier failures, with synthetic demonstrations labelled. The 36 scenarios have been executed: 31 full passes and five partial results (86.1% full pass), with AI-assisted rubric review and explicit retests. All 66 offline checks passed. The separate BudgetMe suite ran 51 existing tests plus two signup checks: 49 passed and four assertions failed. See docs/evaluation/Evaluation_Results.docx and evidence/final/scenario_assessment.json. Human acceptance review, verified contributions and release tagging remain separate tasks.

Offline checks can be run with unittest, but some historical test classes write evidence files in tearDownClass. Use temporary destinations when preserving earlier records. tests/test-groq.py is a live baseline evaluation script, not an offline regression test. The current live verification scripts enforce request budgets and retain failed attempts; do not run them without authorized data and available quota.

Reproduce the scenario run with `.\.venv\Scripts\python.exe -B scripts/evaluate_final.py --budgetme C:/path/to/BudgetMe --pace 40`. Use `--only 6,16,19` for an explicit targeted retest. This sends public/synthetic selected context to Groq and saves dated evidence; it does not automatically assess qualitative answers. `scripts/verify_budgetme_suite.py` runs the verified connected snapshot with disposable SQLite settings and no network. Earlier attempts remain retained. Screenshots and capture provenance are under evidence/screenshots/.
