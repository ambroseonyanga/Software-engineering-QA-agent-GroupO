import json
from datetime import datetime, timezone
from pathlib import Path


try:
    from .rag_service import answer_question
except ImportError:  # pragma: no cover - allows running as a script from src/
    from rag_service import answer_question


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR = PROJECT_ROOT / "evidence" / "drafts"
TRACE_PATH = PROJECT_ROOT / "evidence" / "traces" / "week4_tool_calls.json"

ALLOWED_TOOLS = {
    "retrieve_project_evidence",
    "create_issue_draft",
}

BLOCKED_TOOLS = {
    "run_tests",
    "submit_issue",
    "merge_pr",
    "deploy",
    "shell",
}

HIGHER_IMPACT_FLAGS = ("submit", "merge", "deploy", "execute")

RETRIEVE_OUTPUT_KEYS = ("ok", "grounded", "sources", "answer")
DRAFT_OUTPUT_KEYS = ("ok", "draft_id", "status", "path", "submitted")


def _error(code, message, status=400, **extra):
    result = {
        "ok": False,
        "error": code,
        "status": status,
        "message": message,
    }
    result.update(extra)
    return result


def _truthy(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value, default):
    if value is None or value == "":
        return default
    return int(value)


def _next_draft_id(draft_dir):
    highest = 0
    for path in draft_dir.glob("DRAFT-*.json"):
        suffix = path.stem.replace("DRAFT-", "", 1)
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"DRAFT-{highest + 1:03d}"


def _append_trace(record):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

    traces = []
    if TRACE_PATH.exists():
        try:
            traces = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
            if not isinstance(traces, list):
                traces = []
        except json.JSONDecodeError:
            traces = []

    traces.append(record)
    TRACE_PATH.write_text(
        json.dumps(traces, indent=2),
        encoding="utf-8",
    )


def normalize_tool_result(tool_name, result):
    if not isinstance(result, dict):
        return _error(
            "UNEXPECTED_TOOL_RESPONSE",
            "The tool returned a result that was not an object.",
            status=500,
        )

    if result.get("error") in {
        "VALIDATION_ERROR",
        "UNAUTHORIZED",
        "SERVICE_UNAVAILABLE",
        "UNEXPECTED_TOOL_RESPONSE",
    }:
        return result

    required = (
        RETRIEVE_OUTPUT_KEYS
        if tool_name == "retrieve_project_evidence"
        else DRAFT_OUTPUT_KEYS
    )
    missing = [key for key in required if key not in result]
    if missing:
        return _error(
            "UNEXPECTED_TOOL_RESPONSE",
            "The tool returned an unexpected payload.",
            status=500,
            missing_fields=missing,
        )

    return result


def retrieve_project_evidence(arguments, generate=True, retrieve_fn=None):
    query = str(arguments.get("query") or "").strip()
    if len(query) < 3:
        return _error(
            "VALIDATION_ERROR",
            "query is required and must contain at least 3 characters.",
        )
    if len(query) > 300:
        return _error(
            "VALIDATION_ERROR",
            "query must be 300 characters or fewer.",
        )

    try:
        top_k = _as_int(arguments.get("top_k"), 3)
    except (TypeError, ValueError):
        return _error("VALIDATION_ERROR", "top_k must be an integer between 1 and 5.")

    if top_k < 1 or top_k > 5:
        return _error("VALIDATION_ERROR", "top_k must be an integer between 1 and 5.")

    try:
        if retrieve_fn is not None:
            rag_result = retrieve_fn(query, top_k)
        else:
            rag_result = answer_question(query, generate=generate, top_k=top_k)
    except RuntimeError as error:
        return _error(
            "SERVICE_UNAVAILABLE",
            str(error),
            status=503,
        )
    except Exception as error:
        return _error(
            "SERVICE_UNAVAILABLE",
            f"Retrieval is currently unavailable: {error}",
            status=503,
        )

    if not isinstance(rag_result, dict):
        return normalize_tool_result("retrieve_project_evidence", rag_result)

    sources = []
    for item in rag_result.get("sources") or []:
        if not isinstance(item, dict):
            return normalize_tool_result("retrieve_project_evidence", {"ok": True})
        sources.append({
            "source_id": item.get("source_id", ""),
            "source": item.get("source", ""),
            "chunk_id": item.get("chunk_id"),
            "score": item.get("score"),
            "excerpt": (item.get("text") or "")[:280],
        })

    answer = rag_result.get("answer") or ""
    if not answer and not rag_result.get("grounded"):
        answer = "I could not find sufficient information in the project documentation."

    return {
        "ok": True,
        "grounded": bool(rag_result.get("grounded")),
        "sources": sources,
        "answer": answer,
        "query": query,
        "top_k": top_k,
    }


def create_issue_draft(arguments, draft_dir=None):
    draft_dir = Path(draft_dir) if draft_dir is not None else DRAFTS_DIR
    title = str(arguments.get("title") or "").strip()
    failed_test = str(arguments.get("failed_test") or "").strip()
    expected = str(arguments.get("expected") or "").strip()
    actual = str(arguments.get("actual") or "").strip()
    notes = str(arguments.get("notes") or "").strip()

    if len(title) < 8 or len(title) > 120:
        return _error(
            "VALIDATION_ERROR",
            "title is required and must be between 8 and 120 characters.",
        )
    if not failed_test:
        return _error(
            "VALIDATION_ERROR",
            "failed_test is required.",
        )

    record = {
        "title": title,
        "failed_test": failed_test,
        "expected": expected,
        "actual": actual,
        "notes": notes,
        "status": "draft",
        "submitted": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    try:
        draft_dir.mkdir(parents=True, exist_ok=True)
        draft_id = _next_draft_id(draft_dir)
        path = draft_dir / f"{draft_id}.json"
        record["draft_id"] = draft_id
        try:
            record["path"] = str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            record["path"] = str(path)
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    except OSError as error:
        return _error(
            "SERVICE_UNAVAILABLE",
            f"The draft store is unavailable: {error}",
            status=503,
        )

    return {
        "ok": True,
        "draft_id": draft_id,
        "status": "draft",
        "path": record["path"],
        "submitted": False,
        "title": title,
    }


def invoke_tool(
    tool_name,
    arguments=None,
    generate=True,
    retrieve_fn=None,
    draft_dir=None,
    record_trace=True,
):
    arguments = dict(arguments or {})
    tool_name = str(tool_name or "").strip()

    higher_impact_requested = any(_truthy(arguments.get(flag)) for flag in HIGHER_IMPACT_FLAGS)

    if tool_name in BLOCKED_TOOLS or tool_name not in ALLOWED_TOOLS:
        result = _error(
            "UNAUTHORIZED",
            (
                f"{tool_name or 'This action'} is not an approved tool. "
                "Higher-impact actions require human approval and are outside the Week 4 allow-list."
            ),
            status=403,
            tool=tool_name,
        )
    elif tool_name == "retrieve_project_evidence":
        result = retrieve_project_evidence(
            arguments,
            generate=generate,
            retrieve_fn=retrieve_fn,
        )
        result = normalize_tool_result(tool_name, result)
    elif tool_name == "create_issue_draft":
        result = create_issue_draft(arguments, draft_dir=draft_dir)
        result = normalize_tool_result(tool_name, result)
        if result.get("ok") and higher_impact_requested:
            result = _error(
                "UNAUTHORIZED",
                "Submitting, merging or deploying an issue requires human approval. The record remains a draft.",
                status=403,
                draft_id=result.get("draft_id"),
                record_status="draft",
                path=result.get("path"),
                submitted=False,
            )
    else:
        result = _error(
            "UNAUTHORIZED",
            "The requested tool is not on the allow-list.",
            status=403,
            tool=tool_name,
        )

    if record_trace:
        _append_trace({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "arguments": {
                key: arguments[key]
                for key in arguments
                if key in {
                    "query",
                    "top_k",
                    "title",
                    "failed_test",
                    "submit",
                    "merge",
                    "deploy",
                    "execute",
                }
            },
            "ok": bool(result.get("ok")),
            "error": result.get("error"),
            "status": result.get("status"),
        })

    return result
