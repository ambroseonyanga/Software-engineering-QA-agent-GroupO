import json

from flask import Flask, render_template, request

try:
    from .qa_service import analyse_requirement
    from .rag_service import answer_question
    from .tool_service import invoke_tool
except ImportError:  # pragma: no cover - allows running as a script from src/
    from qa_service import analyse_requirement
    from rag_service import answer_question
    from tool_service import invoke_tool


app = Flask(__name__)


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
        arguments = {
            "query": request.form.get("query", ""),
            "top_k": request.form.get("top_k") or 3,
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
            "submit": request.form.get("submit", ""),
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
