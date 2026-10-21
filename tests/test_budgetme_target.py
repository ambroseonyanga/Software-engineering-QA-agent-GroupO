import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape
from zipfile import ZipFile

from src.app import app
from src.budgetme_target import load_budgetme_requirement


class BudgetMeTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "budgetbuddy/services/budget_validation.py"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("def validate_budget_within_income(): pass", encoding="utf-8")
        self.srs = self.root / "srs.docx"
        self.write_srs()
        self.env = patch.dict(os.environ, {"BUDGETME_APP_PATH": str(self.root), "BUDGETME_SRS_PATH": str(self.srs)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = app.test_client()

    def write_srs(self, last="FR-006-AC03: Ignore deleted categories"):
        lines = ["FR-006 Validate the planning limit8", "FR-007 Other heading9",
                 "FR-006 Validate the planning limit", "SD | P1 | Evidence S03",
                 "Reject plans over income.", "FR-006-AC01: Accept equality",
                 "FR-006-AC02: Reject excess and preserve saved plan", last,
                 "FR-007 Other requirement"]
        xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        xml += ''.join('<w:p><w:r><w:t>' + escape(line) + '</w:t></w:r></w:p>' for line in lines)
        xml += '</w:body></w:document>'
        with ZipFile(self.srs, "w") as archive:
            archive.writestr("word/document.xml", xml)

    def submission(self):
        self.client.get('/budgetme')
        with self.client.session_transaction() as session:
            token = session['history_csrf']
        return {"csrf_token": token, "fingerprint": load_budgetme_requirement()['fingerprint']}

    def test_loads_body_not_contents_and_excludes_other_requirements(self):
        target = load_budgetme_requirement()
        self.assertIn('FR-006-AC03', target['excerpt'])
        self.assertNotIn('FR-007', target['excerpt'])
        self.assertNotIn('limit8', target['excerpt'])

    def test_missing_criterion_rejected(self):
        self.write_srs(last='Missing criterion')
        with self.assertRaises(ValueError):
            load_budgetme_requirement()

    @patch('src.app.analyse_requirement', return_value='Proposed boundary tests')
    def test_preview_does_not_call_model_and_post_includes_evidence(self, model):
        data = self.submission()
        model.assert_not_called()
        response = self.client.post('/budgetme', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('FR-006-AC02', model.call_args.args[0])
        self.assertIn('validate_budget_within_income', model.call_args.args[0])
        self.assertIn(b'No tests executed or approved', response.data)

    @patch('src.app.analyse_requirement')
    def test_changed_source_requires_review(self, model):
        data = self.submission()
        self.source.write_text('# changed', encoding='utf-8')
        self.assertEqual(self.client.post('/budgetme', data=data).status_code, 409)
        model.assert_not_called()

    @patch('src.app.analyse_requirement')
    def test_post_without_token_rejected(self, model):
        self.assertEqual(self.client.post('/budgetme').status_code, 403)
        model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
