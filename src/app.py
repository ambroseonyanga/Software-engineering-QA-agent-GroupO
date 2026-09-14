from flask import Flask, render_template, request
from qa_service import analyse_requirement


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    requirement = ""

    if request.method == "POST":
        requirement = request.form.get("requirement", "").strip()

        if requirement:
            try:
                result = analyse_requirement(requirement)
            except Exception as error:
                result = f"Error: {error}"

    return render_template(
        "index.html",
        result=result,
        requirement=requirement
    )


if __name__ == "__main__":
    app.run(debug=True)