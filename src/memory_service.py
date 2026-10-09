"""Bounded local triage history. Records describe reports, not executed tests."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import ValidationError, validate
try:
    from .agent_contracts import STOP_REASONS
except ImportError:
    from agent_contracts import STOP_REASONS

HISTORY_PATH = Path(__file__).resolve().parents[1] / "memory" / "run_history.sqlite3"
RETENTION_DAYS = 90
MAX_RECORDS = 500
QUERY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "failed_test": {"type": "string", "minLength": 1, "maxLength": 200},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
    }, "required": ["failed_test"],
}
RECORD_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "run_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
        "failed_test": {"type": "string", "minLength": 1, "maxLength": 200},
        "stop_reason": {"type": "string", "enum": list(STOP_REASONS)},
        "iterations_used": {"type": "integer", "minimum": 0},
        "retrievals_used": {"type": "integer", "minimum": 0},
        "draft_id": {"type": ["string", "null"], "maxLength": 80},
        "linked_source_ids": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 100}},
        "elapsed_seconds": {"type": "number", "minimum": 0, "maximum": 1000000},
    },
    "required": ["run_id", "failed_test", "stop_reason", "iterations_used", "retrievals_used", "draft_id", "linked_source_ids", "elapsed_seconds"],
}


class MemoryUnavailable(RuntimeError):
    pass


class HistoryStore:
    def __init__(self, path=None, now=None):
        self.path = Path(path) if path is not None else HISTORY_PATH
        self.now = now or (lambda: datetime.now(timezone.utc))

    @contextmanager
    def _connection(self):
        connection = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=2)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA secure_delete=ON")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, failed_test TEXT NOT NULL, recorded REAL NOT NULL, summary TEXT NOT NULL)")
            cutoff = self.now().timestamp() - RETENTION_DAYS * 86400
            connection.execute("DELETE FROM runs WHERE recorded < ?", (cutoff,))
            yield connection
            connection.commit()
        except (OSError, sqlite3.Error, json.JSONDecodeError) as error:
            if connection is not None:
                connection.rollback()
            raise MemoryUnavailable("Local history is unavailable; no previous context was used.") from error
        finally:
            if connection is not None:
                connection.close()

    def save(self, summary):
        validate(summary, RECORD_SCHEMA)
        if not summary["failed_test"].strip():
            raise ValueError("Test identifier cannot be blank.")
        recorded = self.now()
        entry = {**summary, "failed_test": summary["failed_test"].strip(),
                 "recorded_utc": recorded.isoformat(), "provenance": "human_reported_failure"}
        with self._connection() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?)", (
                entry["run_id"], entry["failed_test"], recorded.timestamp(), json.dumps(entry)))
            db.execute("DELETE FROM runs WHERE run_id IN (SELECT run_id FROM runs ORDER BY recorded DESC, rowid DESC LIMIT -1 OFFSET ?)", (MAX_RECORDS,))
        return entry

    def query(self, failed_test, limit=5):
        validate({"failed_test": failed_test, "limit": limit}, QUERY_SCHEMA)
        failed_test = failed_test.strip()
        if not failed_test:
            raise ValueError("Test identifier cannot be blank.")
        with self._connection() as db:
            count = db.execute("SELECT COUNT(*) FROM runs WHERE failed_test=?", (failed_test,)).fetchone()[0]
            rows = db.execute("SELECT summary FROM runs WHERE failed_test=? ORDER BY recorded DESC, rowid DESC LIMIT ?", (failed_test, limit)).fetchall()
            runs = [json.loads(row[0]) for row in rows]
            # Treat a manually modified/corrupt record as unavailable, never as model instructions.
            for run in runs:
                try:
                    validate({k: run[k] for k in RECORD_SCHEMA["required"]}, RECORD_SCHEMA)
                    if run["failed_test"] != failed_test:
                        raise ValueError("Mismatched history record")
                except (ValidationError, KeyError, TypeError, ValueError) as error:
                    raise MemoryUnavailable("Local history contains an invalid record.") from error
        return {"ok": True, "failed_test": failed_test, "run_count": count,
                "last_stop_reason": runs[0]["stop_reason"] if runs else None, "runs": runs}

    def delete(self, run_id):
        validate(run_id, RECORD_SCHEMA["properties"]["run_id"])
        with self._connection() as db:
            deleted = db.execute("DELETE FROM runs WHERE run_id=?", (run_id,)).rowcount
        return bool(deleted)


def query_run_history(arguments, store=None):
    """Project capability documented as an MCP-style interface; not an MCP server."""
    try:
        validate(arguments, QUERY_SCHEMA)
        return (store or HistoryStore()).query(arguments["failed_test"], arguments.get("limit", 5))
    except (ValidationError, ValueError):
        return {"ok": False, "error": "VALIDATION_ERROR", "message": "Supply a test identifier (1–200 characters) and a limit from 1 to 20."}
    except MemoryUnavailable as error:
        return {"ok": False, "error": "SERVICE_UNAVAILABLE", "message": str(error)}
