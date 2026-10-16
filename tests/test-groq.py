
from pathlib import Path
from time import perf_counter, sleep
from datetime import datetime
from groq import Groq
from groq import RateLimitError, APIError
import json
import os

# ==========================================
# CONFIGURATION
# ==========================================

MODEL = "qwen/qwen3.8-27b"

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_FILE = BASE_DIR / "prompts" / "prompt-v1.2.txt"
RESULTS_DIR = BASE_DIR / "tests" / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError(
        "GROQ_API_KEY is not set. Set it in your terminal first."
    )

client = Groq()

system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

# ==========================================
# REQUIREMENTS AND EXPECTED BEHAVIOURS
# ==========================================

requirements = [
    {
        "id": "TC01",
        "category": "Functional",
        "requirement": (
            "An active registered user requests a password reset. "
            "Send a single-use link to their verified email. "
            "The link is valid for 15 minutes and expires at 15 minutes. "
            "A valid link lets the user set a new password. "
            "After success, the old password no longer works and the user "
            "must log in again."
        ),
        "expected_behavior": (
            "Cover link delivery, a valid reset, expiry just before and at "
            "15 minutes, reuse after success, rejection of the old password "
            "and no automatic login. Ask about password rules if needed; "
            "do not invent them."
        )
    },
    {
        "id": "TC02",
        "category": "Functional",
        "requirement": (
            "A guest can use a cart. Adding a new product sets quantity "
            "to 1; adding it again increases quantity by 1. Quantities "
            "are whole numbers from 1 to 10. Updating to 0 removes the "
            "product. Other invalid quantities are rejected without "
            "changing the cart. Total equals unit price times quantity, "
            "summed across items; no tax, shipping or discounts apply."
        ),
        "expected_behavior": (
            "Cover guest access, first and repeat addition, quantity "
            "updates, removal at zero, invalid quantities and "
            "recalculated totals. Use labelled example prices with "
            "correct arithmetic. Do not require login."
        )
    },
    {
        "id": "TC03",
        "category": "Boundary",
        "requirement": (
            "An upload accepts PDF files only, with a maximum size of "
            "5,000,000 bytes inclusive. Empty files are rejected. "
            "A rejected file must not be stored. Other file-validation "
            "rules are outside this requirement."
        ),
        "expected_behavior": (
            "Cover a non-empty PDF below and exactly at the limit, "
            "a PDF one byte above it, an empty PDF and a non-PDF. "
            "Rejected files must not be stored. Do not invent "
            "MIME-detection methods or error wording."
        )
    },
    {
        "id": "TC04",
        "category": "Access control",
        "requirement": (
            "In a project, an owner may invite members and remove other "
            "members. A member may view the member list but cannot invite "
            "or remove anyone. An unauthorised invite or removal must "
            "leave membership unchanged. The owner cannot remove their "
            "own membership."
        ),
        "expected_behavior": (
            "Cover owner permissions, member viewing, blocked member "
            "invite/removal, unchanged membership after denial and "
            "blocked owner self-removal. Do not prescribe an HTTP status "
            "or interface unless supplied."
        )
    },
    {
        "id": "TC05",
        "category": "State rules",
        "requirement": (
            "A booking starts as Pending. Only Pending bookings may be "
            "confirmed or cancelled. Confirming changes the state to "
            "Confirmed; cancelling changes it to Cancelled. Confirmed "
            "and Cancelled bookings reject further confirmation or "
            "cancellation requests and retain their state."
        ),
        "expected_behavior": (
            "Cover both allowed transitions and both actions from each "
            "terminal state. Check that rejected actions leave the state "
            "unchanged. Do not add refund or notification behaviour."
        )
    },
    {
        "id": "TC06",
        "category": "Missing procedure",
        "requirement": (
            "A staff member can download an existing invoice as a PDF. "
            "The PDF must show the same invoice number and total as the "
            "stored invoice. The interface, download procedure and "
            "storage location will be supplied later."
        ),
        "expected_behavior": (
            "Propose high-level download and content checks with a staff "
            "member and existing invoice as preconditions. Retain the "
            "known PDF and matching-value outcomes; ask for execution "
            "details without inventing buttons, URLs or paths."
        )
    },
    {
        "id": "TC07",
        "category": "Missing rule",
        "requirement": (
            "A user can submit an expense claim with an amount and "
            "receipt. A positive amount and attached receipt are "
            "required; otherwise reject the claim without storing it. "
            "Valid claims are stored as Pending. Treatment of a second "
            "submission with the same receipt has not been decided."
        ),
        "expected_behavior": (
            "Cover valid Pending storage, non-positive amounts and "
            "missing receipts with no storage. Ask what should happen "
            "to duplicate receipts; do not prescribe rejection or "
            "acceptance for duplicates."
        )
    },
    {
        "id": "TC08",
        "category": "Conflicting rules",
        "requirement": (
            "Two current documents describe report access. "
            "Requirement A says only managers may download monthly "
            "reports. Requirement B says all signed-in users may "
            "download them. No precedence is specified. Both "
            "documents agree that signed-out users must be denied "
            "access."
        ),
        "expected_behavior": (
            "Test manager access and signed-out denial where the "
            "sources agree. Identify the conflict for signed-in "
            "non-managers and ask which rule applies. Leave that "
            "outcome unresolved rather than choosing a document."
        )
    },
    {
        "id": "TC09",
        "category": "Performance",
        "requirement": (
            "In staging with 10,000 seeded products, run 100 concurrent "
            "virtual users for 10 minutes after a 2-minute warm-up. "
            "Each user sends one catalogue-search request every "
            "5 seconds. During the measured 10 minutes, the "
            "95th-percentile response time must be at most 800 ms "
            "and fewer than 1% of requests may fail."
        ),
        "expected_behavior": (
            "Preserve the dataset, concurrency, request interval, "
            "warm-up and measured duration. Use p95 <= 800 ms and "
            "failure rate < 1%, not averages or altered boundaries. "
            "Ask for endpoint and failure definition if absent. "
            "Do not claim measured results."
        )
    },
    {
        "id": "TC10",
        "category": "Insufficient evidence",
        "requirement": (
            "The checkout service should be reliable and easy to use. "
            "No workflows, measurable targets, implementation or "
            "execution evidence are supplied. Suggest what is needed "
            "to test it and say whether its quality can currently "
            "be confirmed."
        ),
        "expected_behavior": (
            "Ask for checkout workflows, operating conditions, "
            "reliability targets and usability criteria. State that "
            "quality cannot yet be confirmed. Do not invent thresholds, "
            "payment methods, test results or an executable test table."
        )
    }
]

# ==========================================
# TEST SELECTION
# ==========================================

# Set to None to run all 10 requirements.
# Or choose specific IDs, e.g. ["TC01", "TC03"].

SELECTED_TESTS = None

if SELECTED_TESTS is None:
    selected = requirements
else:
    selected = [
        test for test in requirements
        if test["id"] in SELECTED_TESTS
    ]

# ==========================================
# OUTPUT FILES
# ==========================================

run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

json_file = RESULTS_DIR / f"groq_results_{run_timestamp}.json"
text_file = RESULTS_DIR / f"groq_results_{run_timestamp}.txt"

results = []

# ==========================================
# RUN TESTS
# ==========================================

print(f"\nModel: {MODEL}")
print(f"Prompt: {PROMPT_FILE.name}")
print(f"Requirements selected: {len(selected)}")

for test in selected:

    test_id = test["id"]

    print("\n" + "=" * 65)
    print(f"{test_id} | {test['category']}")
    print("=" * 65)

    start = perf_counter()

    result = {
        "test_id": test_id,
        "category": test["category"],
        "requirement": test["requirement"],
        "expected_behavior": test["expected_behavior"],
        "actual_behavior": None,
        "result": "NOT EVALUATED",
        "observation": (
            "Candidate tests generated for review; "
            "no application test execution performed."
        ),
        "response_time_seconds": None,
        "total_tokens": None,
        "error": None
    }

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": test["requirement"]
                }
            ],
            reasoning_effort="none",
            temperature=0.1,
            max_completion_tokens=1500
        )

        elapsed = perf_counter() - start
        generated = response.choices[0].message.content or ""

        result["actual_behavior"] = generated
        result["response_time_seconds"] = round(elapsed, 2)

        if response.usage:
            result["total_tokens"] = response.usage.total_tokens

        print("\n===== GENERATED TEST CASES =====\n")
        print(generated)

        print("\n===== PERFORMANCE =====")
        print(f"Response time: {elapsed:.2f} seconds")
        print(f"Total tokens: {result['total_tokens']}")

    except RateLimitError as error:
        result["error"] = str(error)
        result["observation"] = (
            "Groq rate limit reached. "
            "This requirement was not processed."
        )

        print("\nRate limit reached.")
        print("Stopping to avoid repeated failed requests.")

        results.append(result)
        break

    except APIError as error:
        result["error"] = str(error)
        result["observation"] = (
            "Groq API error. No usable model output obtained."
        )

        print(f"\nAPI error for {test_id}: {error}")

    except Exception as error:
        result["error"] = str(error)
        result["observation"] = (
            "Request failed. No usable model output obtained."
        )

        print(f"\nError for {test_id}: {error}")

    results.append(result)

    # Brief spacing between API requests.
    sleep(2)

# ==========================================
# SAVE RESULTS
# ==========================================

with json_file.open("w", encoding="utf-8") as file:
    json.dump(
        {
            "model": MODEL,
            "prompt_file": str(PROMPT_FILE),
            "timestamp": run_timestamp,
            "results": results
        },
        file,
        indent=2,
        ensure_ascii=False
    )

with text_file.open("w", encoding="utf-8") as file:
    for result in results:
        file.write("=" * 65 + "\n")
        file.write(
            f"{result['test_id']} | {result['category']}\n"
        )
        file.write("=" * 65 + "\n\n")

        file.write("REQUIREMENT\n")
        file.write(result["requirement"] + "\n\n")

        file.write("EXPECTED BEHAVIOR (REFERENCE)\n")
        file.write(result["expected_behavior"] + "\n\n")

        file.write("GENERATED TEST CASES\n")
        file.write(
            (result["actual_behavior"] or "No response")
            + "\n\n"
        )

        file.write("EVALUATION STATUS\n")
        file.write(result["result"] + "\n\n")

        file.write("PERFORMANCE\n")
        file.write(
            f"Response time: "
            f"{result['response_time_seconds']} seconds\n"
        )
        file.write(
            f"Tokens: {result['total_tokens']}\n\n"
        )

        if result["error"]:
            file.write(
                f"ERROR\n{result['error']}\n\n"
            )

# ==========================================
# SUMMARY
# ==========================================

successful = sum(
    1 for result in results
    if result["actual_behavior"] is not None
)

failed = len(results) - successful

total_tokens = sum(
    result["total_tokens"] or 0
    for result in results
)

print("\n" + "=" * 65)
print("TEST GENERATION SUMMARY")
print("=" * 65)

print(f"Requirements selected: {len(selected)}")
print(f"Requirements processed: {len(results)}")
print(f"Successful responses: {successful}")
print(f"Request errors: {failed}")
print(f"Total tokens: {total_tokens}")

print(f"\nJSON results saved to: {json_file}")
print(f"Text results saved to: {text_file}")

