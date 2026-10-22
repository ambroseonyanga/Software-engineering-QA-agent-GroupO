# Tool authorization evidence

The model-facing tools are retrieve_project_evidence and create_issue_draft. Input/output schemas and the allow-list are enforced by src/tool_contracts.py and src/tool_service.py. Publication, deployment, merging and arbitrary shell execution are not planner capabilities. The separate QA workflow requires approval and an explicit Run action before sandbox execution.

Current offline authorization cases are included in evidence/traces/offline_regression_20261022.json. The retained tests cover missing parameters, prohibited actions, unavailable retrieval, malformed responses and local draft behavior. Model decisions are scripted in offline checks.

Current live model-selected tool decisions and actual outcomes are recorded in evidence/traces/milestones_20261022T154858Z/verification.json. The retrieval demonstration performs real retrieval after a live model decision; answer generation is disabled for that tool demonstration. The draft demonstration creates a synthetic local record with submitted=false. The prohibited-action request must perform no side effect. See the editable Tool_Authorization_Evidence.docx for the current evidence summary.

The final 36-scenario dataset is separate and has not been run.
