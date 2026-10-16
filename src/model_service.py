"""Shared Groq transport; credentials stay in the environment."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
API_URL = "https://api.groq.com/openai/v1/chat/completions"


class ModelUnavailable(RuntimeError):
    pass


class RateLimited(ModelUnavailable):
    pass


def load_prompt(name):
    return (ROOT / "prompts" / name).read_text(encoding="utf-8-sig")


def complete(system, user, *, temperature=0.2, max_tokens=2048, schema=None):
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise ModelUnavailable("Set GROQ_API_KEY in the application environment before using the model.")
    if schema:
        system += "\nReturn only one JSON object matching this schema:\n" + json.dumps(schema)
    payload = {"model": MODEL, "messages": [{"role": "system", "content": system},
               {"role": "user", "content": user}], "temperature": temperature,
               "max_completion_tokens": max_tokens, "stream": False}
    if schema:
        payload["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "User-Agent": "qa-agent/1.0"}, method="POST")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise RateLimited("Groq rate limit reached. Wait before retrying; no automatic retry was made.") from None
        raise ModelUnavailable(f"Groq request failed (HTTP {error.code}). Check model access and account configuration.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ModelUnavailable("Could not reach Groq or the request timed out. Check your connection and retry later.") from None
    except (ValueError, UnicodeError):
        raise ModelUnavailable("Groq returned an unreadable response. No decision was executed.") from None
    try:
        choice = body["choices"][0]
        content = choice["message"]["content"]
        if choice.get("finish_reason") != "stop":
            raise ModelUnavailable("The model did not finish its response. No incomplete decision was executed.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError()
    except (KeyError, IndexError, TypeError, ValueError):
        raise ModelUnavailable("Groq returned an empty or unexpected response.") from None
    return {"text": content.strip(), "model": body.get("model", MODEL),
            "usage": body.get("usage", {}), "elapsed_seconds": round(time.perf_counter()-start, 3),
            "finish_reason": choice["finish_reason"]}
