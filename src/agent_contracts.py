"""Executable Week 5 contract: limits, task input and decision schemas.

These constants are the single source of truth for the Agent Task Contract
(docs/architecture/agent-task-contract.md). The orchestrator enforces them;
the model never does.
"""

LIMITS = {
    "max_iterations": 6,             # decide/act cycles per run
    "max_retrievals": 3,             # retrieve_project_evidence calls per run
    "max_drafts": 1,                 # create_issue_draft calls per run
    "max_consecutive_failures": 2,   # tool errors in a row before stopping
    "max_invalid_decisions": 2,      # malformed/unknown model decisions per run
    "time_budget_seconds": 900,      # wall-clock budget (CPU inference is slow)
}

AGENT_ACTIONS = ("retrieve_project_evidence", "create_issue_draft", "ask_human")

# Terminal states. Anything other than COMPLETED is a human hand-off.
STOP_REASONS = {
    "COMPLETED": "Goal met: a local draft exists with evidence links. Human reviews and submits.",
    "HANDOFF_NEEDS_INFO": "The agent asked the human for missing facts.",
    "HANDOFF_APPROVAL_REQUIRED": "A decision named a blocked or higher-impact action. Nothing was executed.",
    "STOPPED_MAX_ITERATIONS": "Iteration limit reached without completing the goal.",
    "STOPPED_TIME_BUDGET": "Wall-clock budget exhausted.",
    "STOPPED_TOOL_FAILURE": "Repeated tool failures. No further attempts without a human.",
    "STOPPED_INVALID_DECISIONS": "The model repeatedly returned decisions the application rejected.",
    "STOPPED_MODEL_UNAVAILABLE": "The local model was unavailable or timed out.",
    "REJECTED_INPUT": "The failure report failed validation. The agent did not start.",
    "SERVICE_UNAVAILABLE": "Audit trace storage was unavailable. The agent did not start.",
}

# Human-supplied failure report. Treated as untrusted data everywhere.
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 8, "maxLength": 120},
        "failed_test": {"type": "string", "minLength": 1, "maxLength": 200},
        "expected": {"type": "string", "maxLength": 1000},
        "actual": {"type": "string", "maxLength": 1000},
    },
    "required": ["title", "failed_test"],
    "additionalProperties": False,
}

# Validation schema applied by the application. 'action' is checked in code so
# a blocked tool name can be routed to a hand-off instead of a generic error.
DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "minLength": 1, "maxLength": 60},
        "query": {"type": "string", "maxLength": 300},
        "analysis": {"type": "string", "maxLength": 600},
        "message": {"type": "string", "maxLength": 600},
    },
    "required": ["action", "message"],
    "additionalProperties": False,
}

# Schema sent to the model so constrained decoding can only emit approved actions.
MODEL_FORMAT_SCHEMA = {
    **DECISION_SCHEMA,
    "properties": {
        **DECISION_SCHEMA["properties"],
        "action": {"type": "string", "enum": list(AGENT_ACTIONS)},
    },
}
