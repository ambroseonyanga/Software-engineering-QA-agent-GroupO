import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_service import invoke_tool, normalize_tool_result


EVIDENCE_PATH = ROOT / "evidence" / "traces" / "week4_tool_authorization.json"


class ToolAuthorizationTests(unittest.TestCase):
    evidence = []

    def record(self, case_id, case, result, expected):
        self.evidence.append({
            "id": case_id,
            "case": case,
            "expected": expected,
            "ok": result.get("ok"),
            "error": result.get("error"),
            "status": result.get("status"),
            "draft_id": result.get("draft_id"),
            "submitted": result.get("submitted"),
            "grounded": result.get("grounded"),
        })

    def test_t01_empty_retrieve_query_does_not_call_model(self):
        called = {"value": False}

        def retrieve_fn(query, top_k):
            called["value"] = True
            raise AssertionError("retrieve should not run for an empty query")

        result = invoke_tool(
            "retrieve_project_evidence",
            {"query": ""},
            retrieve_fn=retrieve_fn,
            record_trace=False,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "VALIDATION_ERROR")
        self.assertFalse(called["value"])
        self.record(
            "T-01",
            "retrieve with empty query",
            result,
            "VALIDATION_ERROR, no model call",
        )

    def test_t02_draft_without_title_writes_no_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = invoke_tool(
                "create_issue_draft",
                {"failed_test": "login_test"},
                draft_dir=temp_dir,
                record_trace=False,
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "VALIDATION_ERROR")
            self.assertEqual(list(Path(temp_dir).glob("DRAFT-*.json")), [])
            self.record(
                "T-02",
                "create_issue_draft without title",
                result,
                "VALIDATION_ERROR, no file",
            )

    def test_t03_blocked_tools_are_unauthorized(self):
        for tool_name in ("run_tests", "merge_pr"):
            result = invoke_tool(tool_name, {}, record_trace=False)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "UNAUTHORIZED")
            self.assertEqual(result["status"], 403)
        self.record(
            "T-03",
            "call run_tests or merge_pr",
            result,
            "UNAUTHORIZED, no execution",
        )

    def test_t04_submit_flag_keeps_draft_unsubmitted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = invoke_tool(
                "create_issue_draft",
                {
                    "title": "Login failure on empty password",
                    "failed_test": "TC-LOGIN-01",
                    "expected": "Login is rejected",
                    "actual": "Error was not shown",
                    "submit": True,
                },
                draft_dir=temp_dir,
                record_trace=False,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "UNAUTHORIZED")
            self.assertFalse(result.get("submitted"))
            self.assertTrue(result.get("draft_id"))
            draft_path = Path(temp_dir) / f"{result['draft_id']}.json"
            self.assertTrue(draft_path.exists())
            saved = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "draft")
            self.assertFalse(saved["submitted"])
            self.record(
                "T-04",
                "create draft then request submit=true",
                result,
                "UNAUTHORIZED on submit. Draft stays draft",
            )

    def test_t05_unavailable_retrieval_does_not_invent_answer(self):
        def retrieve_fn(query, top_k):
            raise RuntimeError(
                "Could not reach Ollama. Start Ollama and confirm qwen3:8b is installed."
            )

        result = invoke_tool(
            "retrieve_project_evidence",
            {"query": "What stays deterministic?"},
            retrieve_fn=retrieve_fn,
            record_trace=False,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "SERVICE_UNAVAILABLE")
        self.assertNotIn("answer", result)
        self.record(
            "T-05",
            "retrieve when index or Ollama is down",
            result,
            "SERVICE_UNAVAILABLE, no invented answer",
        )

    def test_t06_malformed_tool_payload(self):
        result = normalize_tool_result("retrieve_project_evidence", {"unexpected": True})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "UNEXPECTED_TOOL_RESPONSE")
        self.record(
            "T-06",
            "tool returns malformed payload",
            result,
            "UNEXPECTED_TOOL_RESPONSE",
        )

    def test_t07_valid_retrieve_uses_week3_corpus(self):
        result = invoke_tool(
            "retrieve_project_evidence",
            {"query": "What stays deterministic in the QA agent?"},
            generate=False,
            record_trace=False,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["grounded"])
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.record(
            "T-07",
            "valid retrieve query",
            result,
            "ok, grounded sources",
        )

    def test_t08_valid_draft_is_not_submitted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = invoke_tool(
                "create_issue_draft",
                {
                    "title": "Cart total was not updated",
                    "failed_test": "TC-CART-04",
                    "expected": "Cart total updates after quantity change",
                    "actual": "Displayed total stayed at zero",
                },
                draft_dir=temp_dir,
                record_trace=False,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "draft")
            self.assertFalse(result["submitted"])
            self.assertTrue((Path(temp_dir) / f"{result['draft_id']}.json").exists())
            self.record(
                "T-08",
                "valid draft create",
                result,
                "ok, draft file, submitted=false",
            )

    @classmethod
    def tearDownClass(cls):
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "focus": "Week 4 failure and authorization evidence",
            "tools": ["retrieve_project_evidence", "create_issue_draft"],
            "test_count": len(cls.evidence),
            "results": cls.evidence,
        }
        EVIDENCE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
