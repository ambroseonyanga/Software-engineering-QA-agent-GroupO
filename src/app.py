from flask import Flask, render_template, request

try:
    from .qa_service import analyse_requirement
    from .rag_service import answer_question
except ImportError:  # pragma: no cover - allows running as a script from src/
    from qa_service import analyse_requirement
    from rag_service import answer_question


app = Flask(__name__)


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
        result=requirement_result,
        requirement=requirement,
        rag_question="",
        rag_answer="",
        rag_sources=[],
        rag_grounded=False,
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
        result=None,
        requirement="",
        rag_question=rag_question,
        rag_answer=rag_response.get("answer", ""),
        rag_sources=rag_response.get("sources", []),
        rag_grounded=rag_response.get("grounded", False),
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)