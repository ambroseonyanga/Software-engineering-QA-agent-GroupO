"""One model decision, one validated tool call; no autonomous loop."""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from jsonschema import ValidationError, validate

try:
    from .qa_service import MODEL, OLLAMA_URL
    from .tool_contracts import DECISION_SCHEMA, TOOL_SCHEMAS
    from .tool_service import invoke_tool, _error
except ImportError:
    from qa_service import MODEL, OLLAMA_URL
    from tool_contracts import DECISION_SCHEMA, TOOL_SCHEMAS
    from tool_service import invoke_tool, _error

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "tool-router-v1.0.txt"
TRACE_DIR = ROOT / "evidence" / "traces" / "tool_requests"


def decide_tool(user_request):
    payload = {
        "model": MODEL,
        "system": PROMPT_PATH.read_text(encoding="utf-8") + "\nTool input schemas:\n" + json.dumps(TOOL_SCHEMAS),
        "prompt": user_request,
        "format": DECISION_SCHEMA,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": 350, "num_ctx": 4096},
    }
    request = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.load(response)
    if body.get("error"):
        raise RuntimeError(body["error"])
    return json.loads(body["response"])


def handle_tool_request(user_request, *, decide_fn=None, generate=True, draft_dir=None, trace_dir=None):
    if not isinstance(user_request, str) or not 3 <= len(user_request.strip()) <= 2000:
        return _error("VALIDATION_ERROR", "Request must contain 3 to 2000 characters.")
    trace_dir = Path(trace_dir) if trace_dir is not None else TRACE_DIR
    request_id = uuid4().hex
    trace_path = trace_dir / f"{request_id}.json"
    # Ensure audit storage is writable before any draft can be created.
    record = {
        "request_id": request_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL if decide_fn is None else "test double",
        "prompt_version": PROMPT_PATH.name, "request": user_request,
        "max_tool_calls": 1, "state": "started",
    }
    try:
        trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    except OSError:
        return _error("SERVICE_UNAVAILABLE", "Audit storage is unavailable.", status=503)
    started = time.monotonic()
    try:
        decision = (decide_fn or decide_tool)(user_request)
        validate(decision, DECISION_SCHEMA)
        record["decision"] = decision
        if decision["tool"] == "none":
            result = {"ok": False, "error": "NO_TOOL_SELECTED", "message": decision["message"]}
        else:
            result = invoke_tool(
                decision["tool"], decision["arguments"], generate=generate,
                draft_dir=draft_dir, record_trace=False,
            )
    except (ValidationError, ValueError, KeyError, TypeError):
        result = _error("UNEXPECTED_TOOL_RESPONSE", "The model returned an invalid tool decision.", status=502)
    except (OSError, RuntimeError):
        result = _error("SERVICE_UNAVAILABLE", "The local model is unavailable or timed out.", status=503)
    record.update(state="finished", elapsed_seconds=round(time.monotonic() - started, 3), result=result)
    try:
        trace_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    except OSError:
        # Preserve the actual outcome: a draft may already exist. Do not encourage retry.
        result = {**result, "audit_warning": "Final trace could not be saved; inspect any draft before retrying."}
    return {**result, "request_id": request_id}
