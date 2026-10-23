# Final evidence index

We prepared this pack on 22 October 2026 to consolidate retained evidence and final-format deliverables. We included measured scenario outcomes and retained interruptions. Human acceptance review, release tagging, ClickUp completion and MUELE submission are not inferred from test execution.

## Recorded results for 22 October 2026

- Offline regression: 66 checks passed, zero failures/errors. The model is mocked/scripted in offline cases. See evidence/traces/offline_regression_20261022.json.
- RAG: 15 current generated-answer cases, all assessed PASS under the stated AI-assisted rubric. See docs/evaluation/RAG_Evaluation.docx, evidence/final/rag_assessment.json and evidence/traces/milestones_20261022T154858Z/verification.json. This is one run, not an independent human review or a final system reliability score.
- Tools: live model selected retrieval and local draft creation successfully; a prohibited shell/deploy request selected no tool. Retrieval answer generation was disabled for the router demonstration. The same run contains raw tools/ and drafts/ records.
- Memory: two opt-in live runs completed; the second saw prior_report_count=1 and still retrieved fresh target evidence. Deletion changed retained summaries from 2 to 0. See evidence/traces/agent_memory_20261022T160322Z/verification.json. Stores were reopened in one process; a process-restart test is not claimed.
- Scenario run: 36 executed, 31 full passes and five partial results after explicit retests, 86.1% full pass. See docs/evaluation/Evaluation_Results.docx, Final_Evaluation_Results.csv and scenario_assessment.json. Partial results are excluded from the pass rate.
- BudgetMe suite: 51 existing tests plus two corrected signup checks, 49 passed and four assertions failed. The initial suite had six failures; fixing the sandbox template path resolved two. Both signup checks passed. Raw output: evidence/traces/budgetme_tests_20261022T173303Z/.
- Approved execution: two planning boundary assertions passed against the pinned source through the real approval/run path.
- Further memory check: the explicit scenario retest completed two opt-in runs, received prior_report_count=1 in the second, retrieved fresh evidence and read the persisted summary from a separate Python process. This does not claim a full application restart.

## Three selected Week 5 traces

- Normal: evidence/traces/milestones_20261022T154858Z/agent/8d1df4864c3548c19ccbdf7fc84725f8.json
- Adversarial: evidence/traces/milestones_20261022T152829Z/agent/bb7c66010a8b4d01b9b86f941137ef7e.json
- Recovery: evidence/traces/agent_memory_20261022T160322Z/agent/ef7f9f3d8ea04c1a89d86429d14844e2.json

The three scenarios use clearly synthetic reports, not verified BudgetMe defects. The recovery trace records an intentionally injected retrieval error, then real BudgetMe retrieval and a local draft. The adversarial report did not expand the tool allow-list. Earlier output-limit/network failures remain in their dated run folders.

## What the documents mean

We built the QA Agent as our capstone product and used BudgetMe as the target application. Its current 14 target corpus records combine four original source summaries, six SRS groups and four focused evidence documents. The source-derived requirements and proposed targets retain their labels; the test-coverage and failure documents identify the exact retained execution record. Project analysis uses session requirements plus its bound repository corpus. Global legacy retrieval still serves QA Agent governance questions.

The project failure-analysis route sets use_history=False: it records the new summary but does not consult earlier summaries. Opt-in reuse is demonstrated through standalone triage and the dedicated memory traces. History never grants approval or skips fresh evidence retrieval.

## Deliverables

The main engineering report has ten pages plus an evidence appendix. The editable presentation has 15 slides and presenter notes. The RAG evaluation, tool evidence, failure catalogue and Week 7 report are editable Word documents. The dataset and measured results are CSV. The original evaluated input is preserved as evaluated_dataset.csv, matching the run's recorded hash. The Excel source register matches the unchanged eight-column CSV schema and 19 registered sources. We kept the architecture SVGs and their existing originals.

## Integrity and remaining work

We kept every raw outcome as observed. Generated-test setup errors are not confirmed application defects. The missing-username fixture was corrected and retested. Five scenario outcomes remain partial: overview completeness, proposal/result attribution, conflict clarification, setup diagnosis and stop/handoff behavior. Four target assertions remain unresolved; the target repository was not changed. The engineering report, presentation, Week 7 report and failure catalogue reflect the measured results. Individual contribution/ClickUp task links and acceptance reviews require real human confirmation.

sha256_manifest.csv identifies the packaged file versions. It is a file-integrity index, not proof of test correctness or an independently audited release. The pack contains source and evidence, but no credentials, local session databases, virtual environment or production database.

The Knowledge screenshot captures an additional live UI question using normal defaults, outside the scored dataset. Approved-execution screenshots display the retained two-assertion run. Capture provenance is recorded in evidence/screenshots/captures.json.

Corpus expansion on 22 October 2026: 19 documents in total, 14 target-bound and five QA Agent governance records. All 30 FR records and 90 acceptance criteria are preserved, with related SD/PT quality requirements and open clarifications. Fresh TF-IDF indexes contain 86 global chunks and 60 target chunks. All 34 retrieval checks and 66 offline checks passed. The actual Project Knowledge evidence assembly includes the new requirements within its request bound. See evidence/traces/corpus_expansion_20261022.json and evidence/traces/corpus_index_20261022/verification.json. Earlier answer-generation scores and formal reports describe their recorded nine-document baseline; no new generation score is inferred from retrieval checks.
