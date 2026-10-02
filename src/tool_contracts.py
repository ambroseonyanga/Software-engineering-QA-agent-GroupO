"""Executable Week 4 JSON schemas shared by validation and model routing."""

STRING = {"type": "string", "maxLength": 2000}
TOOL_SCHEMAS = {
    "retrieve_project_evidence": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 3, "maxLength": 300},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "create_issue_draft": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 8, "maxLength": 120},
            "failed_test": {"type": "string", "minLength": 1, "maxLength": 2000},
            "expected": STRING, "actual": STRING, "notes": STRING,
            **{key: {"type": "boolean"} for key in ("submit", "merge", "deploy", "execute")},
        },
        "required": ["title", "failed_test"],
        "additionalProperties": False,
    },
}

SOURCE_SCHEMA = {
    "type": "object",
    "properties": {
        "source_id": {"type": "string", "minLength": 1},
        "source": {"type": "string", "minLength": 1},
        "chunk_id": {"type": "integer", "minimum": 0},
        "score": {"type": "number", "minimum": 0, "maximum": 1.000001},
        "text": {"type": "string", "minLength": 1},
    },
    "required": ["source_id", "source", "chunk_id", "score", "text"],
}
RETRIEVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "grounded": {"type": "boolean"},
        "answer": {"type": "string"},
        "sources": {"type": "array", "items": SOURCE_SCHEMA},
    },
    "required": ["grounded", "answer", "sources"],
}

DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string", "enum": [*TOOL_SCHEMAS, "none"]},
        "arguments": {"type": "object"},
        "message": {"type": "string", "maxLength": 1000},
    },
    "required": ["tool", "arguments", "message"],
    "additionalProperties": False,
}
