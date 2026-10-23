
"""Safe console logging for the Software Engineering QA Agent."""

import logging
from functools import wraps
import sys
import time
import uuid
from flask import g, request


COMPONENT_COLORS = {
    "HTTP": "90", "RAG": "36", "MODEL": "35",
    "AGENT": "33", "APPROVAL": "33", "TOOL": "34", "CODE": "34",
    "SANDBOX": "32", "RESULT": "32",
}


class ComponentFormatter(logging.Formatter):
    """Color terminal output only; never modify the shared log record."""

    def __init__(self, stream):
        super().__init__("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        self.use_color = bool(getattr(stream, "isatty", lambda: False)())

    def format(self, record):
        message = super().format(record)
        component = getattr(record, "component", "")
        color = "31" if record.levelno >= logging.ERROR else COMPONENT_COLORS.get(component)
        if self.use_color and color:
            return f"\033[{color}m{message}\033[0m"
        return message


class RoutineAccessFilter(logging.Filter):
    """Keep startup messages and errors, suppress duplicate access records."""

    def filter(self, record):
        return not (record.levelno < logging.WARNING
                    and ' - - [' in str(record.msg)
                    and isinstance(record.args, tuple)
                    and len(record.args) == 3)


def setup_logging():
    """Use one flushing console handler, including on Windows terminals."""
    # Enables native ANSI support or wraps legacy Windows consoles. Safe to repeat.
    from colorama import just_fix_windows_console
    just_fix_windows_console()
    logger = logging.getLogger("qa_agent")
    logger.setLevel(logging.INFO)
    if not any(getattr(handler, "_qa_console", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler._qa_console = True
        handler.setLevel(logging.INFO)
        handler.setFormatter(ComponentFormatter(handler.stream))
        logger.addHandler(handler)
    logger.propagate = False
    # Keep the startup URL visible while Flask hooks report routine requests.
    server_logger = logging.getLogger("werkzeug")
    server_logger.setLevel(logging.INFO)
    if not any(isinstance(item, RoutineAccessFilter) for item in server_logger.filters):
        server_logger.addFilter(RoutineAccessFilter())
    return logger


logger = setup_logging()


def log_event(component, action, **details):
    """Record a real application event without logging raw user inputs."""
    safe_details = {}

    for key, value in details.items():
        if key.lower() in {
            "password", "api_key", "token", "secret",
            "authorization", "prompt", "response", "content"
        }:
            continue

        if isinstance(value, (bool, int, float)):
            safe_details[key] = value
        elif isinstance(value, str):
            safe_details[key] = value[:120]

    suffix = " ".join(
        f"{key}={value!r}"
        for key, value in safe_details.items()
    )

    logger.info("[%s] %s %s", component, action, suffix,
                extra={"component": component.upper()})


def log_error(component, action, error):
    """Log an error type without exposing potentially sensitive details."""
    logger.error(
        "[%s] %s error_type=%s",
        component,
        action,
        type(error).__name__,
        extra={"component": component.upper()},
    )


def register_flask_logging(app):
    """Register HTTP request timing and outcome logging."""

    @app.before_request
    def begin_request_trace():
        g.request_started = time.perf_counter()
        g.request_trace_id = uuid.uuid4().hex[:8]

        if request.path.startswith("/static/"):
            return

        log_event(
            "HTTP",
            "Request received",
            request_id=g.request_trace_id,
            method=request.method,
            route=request.endpoint or "unknown",
        )

    @app.after_request
    def finish_request_trace(response):
        if request.path.startswith("/static/"):
            return response

        started = getattr(g, "request_started", None)
        duration_ms = (
            round((time.perf_counter() - started) * 1000, 1)
            if started is not None else 0
        )

        log_event(
            "HTTP",
            "Request completed",
            request_id=getattr(g, "request_trace_id", ""),
            status=response.status_code,
            duration_ms=duration_ms,
        )

        return response


def trace_operation(component, action):
    """Trace actual calls and safe outcomes without inspecting input content."""
    def decorate(function):
        @wraps(function)
        def traced(*args, **kwargs):
            operation_id = uuid.uuid4().hex[:8]
            started = time.perf_counter()
            log_event(component, action + " started", operation_id=operation_id)
            try:
                result = function(*args, **kwargs)
            except Exception as error:
                logger.error("[%s] %s failed operation_id=%s error_type=%s duration_ms=%.1f",
                             component, action, operation_id, type(error).__name__,
                             (time.perf_counter() - started) * 1000,
                             extra={"component": component})
                raise
            details = {"operation_id": operation_id,
                       "duration_ms": round((time.perf_counter() - started) * 1000, 1)}
            if isinstance(result, dict):
                for key in ("ok", "grounded", "submitted"):
                    if isinstance(result.get(key), bool):
                        details[key] = result[key]
                for key in ("sources", "retrieved"):
                    if isinstance(result.get(key), list):
                        details[key + "_count"] = len(result[key])
                if isinstance(result.get("status"), int):
                    details["status"] = result["status"]
            elif isinstance(result, list):
                details["items"] = len(result)
            log_event(component, action + " returned", **details)
            if isinstance(result, dict) and result.get("ok") is False:
                logger.error("[%s] %s returned an unsuccessful outcome operation_id=%s",
                             component, action, operation_id, extra={"component": component})
            return result
        return traced
    return decorate
