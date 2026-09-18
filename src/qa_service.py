import json
import urllib.error
import urllib.request


MODEL = "qwen3:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT_SECONDS = 30


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

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "think": False,
        "options": {
            "num_predict": 400,
            "num_ctx": 2048,
            "temperature": 0.3,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    chunks = []

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                data = json.loads(line)
                if data.get("error"):
                    raise RuntimeError(data["error"])

                chunks.append(data.get("response") or "")

                if data.get("done"):
                    break
    except TimeoutError as error:
        raise RuntimeError("Qwen timed out while generating a response.") from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            "Could not reach Ollama. Start Ollama and confirm qwen3:8b is installed."
        ) from error

    answer = "".join(chunks).strip()
    if not answer:
        raise RuntimeError("Qwen returned an empty response.")

    return answer