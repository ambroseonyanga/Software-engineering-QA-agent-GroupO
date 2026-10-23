# Tool authorization evidence

We expose two model-facing tools, retrieve_project_evidence and create_issue_draft. Input/output schemas and the allow-list are enforced by src/tool_contracts.py and src/tool_service.py. Publication, deployment, merging and arbitrary shell execution are not planner capabilities. The separate QA workflow requires approval and an explicit Run action before sandbox execution.

We retained the offline authorization cases in evidence/traces/offline_regression_20261022.json. The retained tests cover missing parameters, prohibited actions, unavailable retrieval, malformed responses and local draft behavior. Model decisions are scripted in offline checks.

We recorded live model-selected tool decisions and actual outcomes in evidence/traces/milestones_20261022T154858Z/verification.json. The retrieval demonstration performs real retrieval after a live model decision; answer generation is disabled for that tool demonstration. The draft demonstration creates a synthetic local record with submitted=false. The prohibited-action request must perform no side effect. See the editable Tool_Authorization_Evidence.docx for the current evidence summary.

We kept the final 36-scenario dataset separate from these demonstrations. Its 22 October outcomes are in evidence/final/scenario_assessment.json, and the 23 October follow-up outcomes are in evidence/traces/final_evaluation_20261023T101922Z/scenario_assessment.json.
