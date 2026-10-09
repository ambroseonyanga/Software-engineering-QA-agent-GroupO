import json
import secrets
from urllib.parse import urlsplit

from flask import Flask, render_template, request, session, redirect, url_for, abort, jsonify
from jsonschema import ValidationError

try:
    from .qa_service import analyse_requirement
    from .rag_service import answer_question
    from .tool_service import invoke_tool
    from .tool_router import handle_tool_request
    from .agent import run_agent
    from .memory_service import HistoryStore, MemoryUnavailable, query_run_history
except ImportError:  # pragma: no cover - allows running as a script from src/
    from qa_service import analyse_requirement
    from rag_service import answer_question
    from tool_service import invoke_tool
    from tool_router import handle_tool_request
    from agent import run_agent
    from memory_service import HistoryStore, MemoryUnavailable, query_run_history


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384
app.secret_key = secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict", HISTORY_PATH=None)


def history_store():
    return HistoryStore(app.config["HISTORY_PATH"])


@app.before_request
def local_request_boundary():
    # This is a single-operator loopback application, not a remotely hosted service.
    if urlsplit(request.host_url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        abort(403)
    if request.method == "POST" and request.headers.get("Origin") not in {None, request.host_url.rstrip("/")}:
        abort(403)


def history_token():
    if "history_csrf" not in session:
        session["history_csrf"] = secrets.token_urlsafe(32)
    return session["history_csrf"]


def page_context(**overrides):
    context = {
        "result": None,
        "requirement": "",
        "rag_question": "",
        "rag_answer": "",
        "rag_sources": [],
        "rag_grounded": False,
        "tool_name": "",
        "tool_result": None,
        "tool_result_text": "",
        "retrieve_query": "",
        "draft_title": "",
        "draft_failed_test": "",
        "draft_expected": "",
        "draft_actual": "",
        "draft_notes": "",
        "agent_result": None,
        "agent_form": {},
    }
    context.update(overrides)
    return context


@app.route("/", methods=["GET", "POST"])
def index():
    requirement_result = None
    requirement = ""

    if request.method == "POST":
        requirement = request.form.get("requirement", "").strip()

        if requirement:
            try:
                requirement_result = analyse_requirement(requirement)
            except Exception as error:
                requirement_result = f"Error: {error}"

    return render_template(
        "index.html",
        **page_context(
            result=requirement_result,
            requirement=requirement,
        ),
    )


@app.route("/ask", methods=["GET", "POST"])
def ask():
    rag_question = ""
    rag_response = {"answer": "", "sources": [], "grounded": False}

    if request.method == "POST":
        rag_question = request.form.get("rag_question", "").strip()
        if rag_question:
            try:
                rag_response = answer_question(rag_question)
            except Exception as error:
                rag_response = {
                    "answer": f"Error: {error}",
                    "sources": [],
                    "grounded": False,
                }

    return render_template(
        "index.html",
        **page_context(
            rag_question=rag_question,
            rag_answer=rag_response.get("answer", ""),
            rag_sources=rag_response.get("sources", []),
            rag_grounded=rag_response.get("grounded", False),
        ),
    )


@app.route("/tool", methods=["POST"])
def tool():
    tool_name = request.form.get("tool_name", "").strip()

    if tool_name == "retrieve_project_evidence":
        top_k = request.form.get("top_k", "3")
        try:
            top_k = int(top_k)
        except ValueError:
            pass  # The dispatcher returns a schema validation error.
        arguments = {
            "query": request.form.get("query", ""),
            "top_k": top_k,
        }
        result = invoke_tool(tool_name, arguments, generate=True)
        return render_template(
            "index.html",
            **page_context(
                tool_name=tool_name,
                tool_result=result,
                tool_result_text=json.dumps(result, indent=2),
                retrieve_query=arguments["query"],
            ),
        )

    if tool_name == "create_issue_draft":
        arguments = {
            "title": request.form.get("title", ""),
            "failed_test": request.form.get("failed_test", ""),
            "expected": request.form.get("expected", ""),
            "actual": request.form.get("actual", ""),
            "notes": request.form.get("notes", ""),
            "submit": request.form.get("submit", "").lower() in {"true", "1", "on"},
        }
        result = invoke_tool(tool_name, arguments)
        return render_template(
            "index.html",
            **page_context(
                tool_name=tool_name,
                tool_result=result,
                tool_result_text=json.dumps(result, indent=2),
                draft_title=arguments["title"],
                draft_failed_test=arguments["failed_test"],
                draft_expected=arguments["expected"],
                draft_actual=arguments["actual"],
                draft_notes=arguments["notes"],
            ),
        )

    result = invoke_tool(tool_name or "unknown", {})
    return render_template(
        "index.html",
        **page_context(
            tool_name=tool_name,
            tool_result=result,
            tool_result_text=json.dumps(result, indent=2),
        ),
    )


@app.route("/tool-request", methods=["POST"])
def tool_request():
    result = handle_tool_request(request.form.get("request", ""))
    return render_template("index.html", **page_context(
        tool_name="QA request", tool_result=result,
        tool_result_text=json.dumps(result, indent=2),
    ))


@app.route("/agent", methods=["POST"])
def agent():
    form = {key: request.form.get(key, "").strip() for key in ("title", "failed_test", "expected", "actual")}
    task = {key: value for key, value in form.items() if value or key in ("title", "failed_test")}
    form["use_history"] = request.form.get("use_history", "")
    result = run_agent(task, memory_store=history_store(), use_history=form.get("use_history") == "on")
    return render_template("index.html", **page_context(agent_result=result, agent_form=form))


@app.route("/history")
def history():
    failed_test = request.args.get("failed_test", "")
    result = query_run_history({"failed_test": failed_test, "limit": 20}, history_store()) if failed_test else None
    return render_template("history.html", failed_test=failed_test, history=result, csrf_token=history_token())


@app.route("/api/history")
def history_api():
    arguments = request.args.to_dict()
    if "limit" in arguments:
        try:
            arguments["limit"] = int(arguments["limit"])
        except ValueError:
            pass
    result = query_run_history(arguments, history_store())
    return jsonify(result), (200 if result["ok"] else 503 if result["error"] == "SERVICE_UNAVAILABLE" else 400)


@app.route("/history/delete", methods=["POST"])
def delete_history():
    expected = session.get("history_csrf", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, supplied):
        abort(403)
    try:
        history_store().delete(request.form.get("run_id", ""))
    except (ValidationError, ValueError):
        abort(400)
    except MemoryUnavailable:
        return "History could not be deleted. Please retry once storage is available.", 503
    return redirect(url_for("history", failed_test=request.form.get("failed_test", "")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
