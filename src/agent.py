"""Week 5: a bounded plan-act-observe agent for QA failure triage.

Goal: link ONE reported test failure to authorized project requirements and
save ONE local draft issue for a human. The model only chooses the next action.
Deterministic code validates every decision, enforces the limits in
agent_contracts.LIMITS, executes tools through the Week 4 allow-list, records a
trace, and decides when the run stops.

Loop per iteration:  Sense -> Decide -> Validate -> Act -> Observe -> Stop/Re-plan
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from jsonschema import ValidationError, validate

try:
    from .agent_contracts import (
        AGENT_ACTIONS, DECISION_SCHEMA, LIMITS, MODEL_FORMAT_SCHEMA,
        STOP_REASONS, TASK_SCHEMA,
    )
    from .qa_service import MODEL, OLLAMA_URL
    from .tool_service import BLOCKED_TOOLS, HIGHER_IMPACT_FLAGS, invoke_tool
except ImportError:  # pragma: no cover - allows running as a script from src/
    from agent_contracts import (
        AGENT_ACTIONS, DECISION_SCHEMA, LIMITS, MODEL_FORMAT_SCHEMA,
        STOP_REASONS, TASK_SCHEMA,
    )
    from qa_service import MODEL, OLLAMA_URL
    from tool_service import BLOCKED_TOOLS, HIGHER_IMPACT_FLAGS, invoke_tool

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "agent-planner-v1.0.txt"
TRACE_DIR = ROOT / "evidence" / "traces" / "agent_runs"

GOAL = "Link one reported test failure to project requirements and prepare one local draft issue for human review."
# Names a model might emit for actions the agent must never take.
PROHIBITED_NAMES = set(BLOCKED_TOOLS) | set(HIGHER_IMPACT_FLAGS) | {"submit_issue", "run", "commit", "push"}
EXCERPT_CHARS_FOR_PROMPT = 200


# --------------------------------------------------------------------------- Decide
def decide_with_model(digest):
    """One constrained-JSON decision from the local model. Raises on failure."""
    payload = {
        "model": MODEL,
        "system": PROMPT_PATH.read_text(encoding="utf-8"),
        "prompt": "STATE (JSON):\n" + json.dumps(digest, indent=1) + "\n\nChoose the next action.",
        "format": MODEL_FORMAT_SCHEMA,
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


# --------------------------------------------------------------------------- Sense
def _sense(state):
    """Build the compact state the model is allowed to see."""
    limits = state["limits"]
    return {
        "goal": GOAL,
        "failure_report": state["task"],  # untrusted data
        "limits_remaining": {
            "iterations": limits["max_iterations"] - state["iteration"] + 1,
            "retrievals": limits["max_retrievals"] - state["retrievals"],
        },
        "history": state["history"][-4:],
    }


def _compact_sources(sources, chars=EXCERPT_CHARS_FOR_PROMPT):
    return [
        {"source_id": s.get("source_id"), "source": s.get("source"),
         "chunk_id": s.get("chunk_id"), "score": round(s.get("score") or 0, 3),
         "excerpt": (s.get("excerpt") or "")[:chars]}
        for s in sources
    ]


def _norm(query):
    return " ".join(query.lower().split())


def _compose_notes(state, analysis, run_id):
    """Notes are built by the application: deterministic evidence, then labelled model opinion."""
    lines = ["Requirement evidence (retrieved by the application):"]
    if state["evidence"]:
        for s in state["evidence"][:5]:
            lines.append(f"- {s['source_id'] or 'unregistered'} {s['source']} chunk {s['chunk_id']} (score {s['score']:.3f})")
    else:
        lines.append("- None above the similarity threshold. This failure is NOT linked to a documented requirement.")
    analysis = (analysis or "").strip()
    if analysis:
        lines.append("Model-suggested analysis (unverified; not a confirmed cause): " + analysis)
    lines.append(f"Agent run: {run_id}. Draft only; a human must review before any submission.")
    return "\n".join(lines)[:2000]


def _persist(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- Run
def run_agent(task, *, decide_fn=None, retrieve_fn=None, draft_dir=None, trace_dir=None,
              limits=None, clock=time.monotonic, fault_injection=None):
    """Run one bounded triage. Always returns a dict with stop_reason; never raises for expected faults."""
    limits = {**LIMITS, **(limits or {})}
    try:
        validate(task, TASK_SCHEMA)
        if not task["title"].strip() or not task["failed_test"].strip():
            raise ValidationError("title and failed_test must not be blank")
    except ValidationError as error:
        return _finish_early("REJECTED_INPUT", error.message)
    task = {k: str(v).strip() for k, v in task.items()}

    trace_dir = Path(trace_dir) if trace_dir is not None else TRACE_DIR
    run_id = uuid4().hex
    trace_path = trace_dir / f"{run_id}.json"
    record = {
        "run_id": run_id, "started_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL if decide_fn is None else "test double",
        "prompt_version": PROMPT_PATH.name, "goal": GOAL, "task": task, "limits": limits,
        "fault_injection": fault_injection, "state": "started", "steps": [],
    }
    # Audit first: if the trace cannot be written, no tool may run.
    try:
        trace_dir.mkdir(parents=True, exist_ok=True)
        _persist(trace_path, record)
    except OSError:
        return _finish_early("SERVICE_UNAVAILABLE", STOP_REASONS["SERVICE_UNAVAILABLE"])

    decide = decide_fn or decide_with_model
    started = clock()
    state = {
        "task": task, "limits": limits, "iteration": 1, "retrievals": 0, "history": [],
        "evidence": [], "completed_queries": set(), "consecutive_failures": 0,
        "invalid_decisions": 0, "draft": None,
    }
    stop_reason, message = None, ""
    audit_warning = None

    while stop_reason is None:
        if state["iteration"] > limits["max_iterations"]:
            stop_reason, message = "STOPPED_MAX_ITERATIONS", STOP_REASONS["STOPPED_MAX_ITERATIONS"]
            break
        if clock() - started > limits["time_budget_seconds"]:
            stop_reason, message = "STOPPED_TIME_BUDGET", STOP_REASONS["STOPPED_TIME_BUDGET"]
            break

        step = {"iteration": state["iteration"], "tool": None}
        digest = _sense(state)                                              # SENSE
        step["sense"] = {"limits_remaining": digest["limits_remaining"], "history_items": len(digest["history"])}
        obs = {"iteration": state["iteration"]}

        t0 = clock()
        try:                                                                # DECIDE
            decision = decide(digest)
        except (OSError, RuntimeError) as error:
            detail = f"{type(error).__name__}: {error}"[:300]
            stop_reason, message = "STOPPED_MODEL_UNAVAILABLE", STOP_REASONS["STOPPED_MODEL_UNAVAILABLE"]
            step.update(decision=None, error=detail, guard=None, decision_seconds=round(clock() - t0, 3),
                        observation={**obs, "action": None, "outcome": "model_unavailable", "detail": detail,
                                     "stop_reason": stop_reason})
            record["steps"].append(step)
            break
        except (ValueError, KeyError, TypeError) as error:
            decision, step["decision_error"] = None, f"{type(error).__name__}: {error}"[:300]
        step["decision_seconds"] = round(clock() - t0, 3)
        step["decision"] = decision

        # VALIDATE (deterministic guards; the model has no authority here)
        action, guard = None, None
        if decision is None:
            guard = "invalid: no parseable decision"
        elif not isinstance(decision, dict):
            guard = "invalid: decision is not an object"
        elif any(decision.get(flag) is True for flag in HIGHER_IMPACT_FLAGS) or \
                str(decision.get("action", "")).strip().lower() in PROHIBITED_NAMES:
            stop_reason, message = "HANDOFF_APPROVAL_REQUIRED", (
                "The model proposed a blocked or higher-impact action. Nothing was executed; a human must decide.")
            guard = "blocked: action outside the approved list"
            obs.update(action=str(decision.get("action", ""))[:60], outcome="blocked", detail=message)
        else:
            try:
                validate(decision, DECISION_SCHEMA)
                action = decision["action"].strip()
                if action not in AGENT_ACTIONS:
                    guard, action = f"invalid: unknown action '{action[:40]}'", None
                elif action == "retrieve_project_evidence" and len((decision.get("query") or "").strip()) < 3:
                    guard, action = "invalid: retrieve needs a query of at least 3 characters", None
            except ValidationError as error:
                guard = f"invalid: {error.message[:150]}"
        if guard and guard.startswith("invalid"):
            state["invalid_decisions"] += 1
            obs.update(action=None, outcome="invalid_decision", detail=guard)
            if state["invalid_decisions"] >= limits["max_invalid_decisions"]:
                stop_reason, message = "STOPPED_INVALID_DECISIONS", STOP_REASONS["STOPPED_INVALID_DECISIONS"]
        elif stop_reason is None:
            # ACT / OBSERVE
            if action == "ask_human":
                stop_reason, message = "HANDOFF_NEEDS_INFO", (decision.get("message") or "").strip() or STOP_REASONS["HANDOFF_NEEDS_INFO"]
                obs.update(action=action, outcome="handoff", detail=message[:300])
                guard = "accepted"
            elif action == "retrieve_project_evidence":
                query = decision["query"].strip()
                if state["retrievals"] >= limits["max_retrievals"]:
                    guard = "blocked: retrieval budget exhausted"
                    obs.update(action=action, query=query, outcome="blocked", detail="No retrievals left. Create the draft or ask_human.")
                elif _norm(query) in state["completed_queries"]:
                    guard = "blocked: duplicate query"
                    obs.update(action=action, query=query, outcome="blocked", detail="Query already used. Change the wording or choose another action.")
                else:
                    guard = "accepted"
                    state["retrievals"] += 1
                    step["tool"], step["tool_arguments"] = action, {"query": query, "top_k": 3}
                    t1 = clock()
                    result = invoke_tool(action, {"query": query, "top_k": 3}, generate=False,
                                         retrieve_fn=retrieve_fn, record_trace=False)
                    step["tool_seconds"] = round(clock() - t1, 3)
                    step["tool_result"] = {k: result.get(k) for k in ("ok", "grounded", "error", "status", "message")}
                    step["tool_result"]["sources"] = _compact_sources(result.get("sources") or [], 280)
                    if result.get("ok"):
                        state["consecutive_failures"] = 0
                        state["completed_queries"].add(_norm(query))
                        if result.get("grounded"):
                            known = {(e["source"], e["chunk_id"]) for e in state["evidence"]}
                            state["evidence"] += [s for s in result["sources"] if (s["source"], s["chunk_id"]) not in known]
                            state["evidence"].sort(key=lambda s: -(s.get("score") or 0))
                            obs.update(action=action, query=query, outcome="grounded", sources=_compact_sources(result["sources"]))
                        else:
                            obs.update(action=action, query=query, outcome="not_grounded",
                                       detail="Nothing scored above the similarity threshold. Re-plan with different wording or ask_human.")
                    else:
                        state["consecutive_failures"] += 1
                        obs.update(action=action, query=query, outcome="tool_error",
                                   detail=f"{result.get('error')}: {result.get('message')}"[:300])
            elif action == "create_issue_draft":
                if state["draft"] is not None:
                    guard = "blocked: draft limit reached"
                    obs.update(action=action, outcome="blocked", detail="A draft already exists.")
                elif not state["completed_queries"]:
                    guard = "blocked: retrieval must be attempted first"
                    obs.update(action=action, outcome="blocked",
                               detail="No successful retrieval yet. Run retrieve_project_evidence (or ask_human) before drafting.")
                else:
                    guard = "accepted"
                    arguments = {**task, "notes": _compose_notes(state, decision.get("analysis"), run_id)}
                    step["tool"], step["tool_arguments"] = action, {k: arguments[k] for k in ("title", "failed_test")}
                    t1 = clock()
                    result = invoke_tool(action, arguments, draft_dir=draft_dir, record_trace=False)
                    step["tool_seconds"] = round(clock() - t1, 3)
                    step["tool_result"] = {k: result.get(k) for k in ("ok", "draft_id", "status", "path", "submitted", "error", "message")}
                    if result.get("ok"):
                        state["draft"] = result
                        stop_reason, message = "COMPLETED", STOP_REASONS["COMPLETED"]
                        obs.update(action=action, outcome="draft_saved", detail=result.get("path"))
                    else:
                        state["consecutive_failures"] += 1
                        obs.update(action=action, outcome="tool_error",
                                   detail=f"{result.get('error')}: {result.get('message')}"[:300])
            if stop_reason is None and state["consecutive_failures"] >= limits["max_consecutive_failures"]:
                stop_reason, message = "STOPPED_TOOL_FAILURE", STOP_REASONS["STOPPED_TOOL_FAILURE"]

        step["guard"] = guard
        step["observation"] = {**obs, "stop_reason": stop_reason}
        record["steps"].append(step)
        state["history"].append({k: v for k, v in obs.items() if v is not None})
        state["iteration"] += 1
        if stop_reason is None:
            try:
                _persist(trace_path, record)
            except OSError:
                stop_reason, message = "SERVICE_UNAVAILABLE", "Trace storage failed mid-run; stopped for safety."

    linked = [{k: s[k] for k in ("source_id", "source", "chunk_id", "score")} for s in state["evidence"][:5]]
    handoff = stop_reason != "COMPLETED"
    record.update(state="finished", stop_reason=stop_reason, message=message, human_handoff=handoff,
                  iterations_used=len(record["steps"]), retrievals_used=state["retrievals"],
                  elapsed_seconds=round(clock() - started, 3), linked_sources=linked,
                  draft=state["draft"], finished_utc=datetime.now(timezone.utc).isoformat())
    try:
        _persist(trace_path, record)
    except OSError:
        audit_warning = "Final trace could not be saved; inspect any draft before retrying."
    result = {
        "ok": stop_reason == "COMPLETED", "stop_reason": stop_reason, "message": message,
        "human_handoff": handoff, "run_id": run_id, "iterations_used": len(record["steps"]),
        "retrievals_used": state["retrievals"], "linked_sources": linked, "draft": state["draft"],
        "trace_path": str(trace_path),
        "steps": [{"iteration": s["iteration"], "action": (s.get("decision") or {}).get("action") if isinstance(s.get("decision"), dict) else None,
                   "outcome": s["observation"].get("outcome"), "detail": s["observation"].get("detail") or s["observation"].get("query")}
                  for s in record["steps"]],
    }
    if audit_warning:
        result["audit_warning"] = audit_warning
    return result


def _finish_early(stop_reason, message):
    return {"ok": False, "stop_reason": stop_reason, "message": message, "human_handoff": True,
            "iterations_used": 0, "retrievals_used": 0, "linked_sources": [], "draft": None, "steps": []}
