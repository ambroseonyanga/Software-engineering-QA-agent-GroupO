import subprocess


MODEL = "qwen3:8b"


SYSTEM_PROMPT = """
You are a Software Engineering QA Assistant.

Your task is to analyse a software requirement and propose candidate QA tests.

Follow these rules:

1. Identify only behaviours explicitly supported by the requirement.
2. Classify every proposed test as:
   - Requirement-supported
   - Assumption-dependent
   - Recommendation
3. Do not invent requirements, system behaviour, test results, error messages,
   redirects, database behaviour, security mechanisms, performance thresholds,
   or implementation details.
4. If information is missing, clearly state what is missing.
5. Do not claim that a test was actually executed.
6. Separate assumptions and recommendations from requirement-supported behaviour.
7. Make proposed tests clear and testable.

Use this output structure:

Requirement Assessment:
Requirement-Supported Behaviours:
Candidate QA Tests:
Ambiguities and Missing Information:
Assumptions:
Recommendations:
Summary:
"""


def analyse_requirement(requirement):
    prompt = f"""
{SYSTEM_PROMPT}

Analyse the following software requirement:

{requirement}
"""

    result = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout