from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import sys
import unittest
from unittest.mock import patch

from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from src.app import app
from src import workflow_service as service
from src import workflow_runner as runner
from src.workflow_report import report_bytes


def sample_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 730 Td (Workflow verification fixture: FR-006 shall accept plans at the income limit.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def proposed(code, title='Workflow verification test'):
    return {'title': title, 'requirement': 'FR-006', 'expected': 'The stated assertion holds.',
            'limitations': 'Synthetic workflow verification only, not a completed SRS evaluation.', 'code': code}


PASS = 'import unittest\nfrom calculator import add\nclass Check(unittest.TestCase):\n def test_add(self):\n  self.assertEqual(add(2, 3), 5)\n'
FAIL = 'import unittest\nclass Check(unittest.TestCase):\n def test_failure(self):\n  self.assertEqual(1, 2)\n'


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix='qa-workflow-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.code = self.root / 'application'
        self.code.mkdir()
        (self.code / 'calculator.py').write_text('def add(a,b): return a+b', encoding='utf-8')
        (self.code / '.env').write_text('PASSWORD=do-not-copy', encoding='utf-8')
        (self.code / 'settings.py').write_text('SECRET_KEY="do-not-copy"', encoding='utf-8')
        environment = patch.dict(os.environ, {'QA_WORKFLOW_HOME': str(self.root / 'sessions')})
        environment.start()
        self.addCleanup(environment.stop)
        self.client = app.test_client()

    def create(self, adapter='python', source=None):
        return service.create(sample_pdf(), 'verification.pdf', str(source or self.code), adapter, 'FR-006')

    def generate(self, state, tests=None):
        with patch('src.workflow_service.complete', return_value={'text': json.dumps({'tests': tests or [proposed(PASS), proposed(FAIL)]}), 'model': 'mock-model-for-workflow-verification'}):
            service.generate(state['id'])
        return service.read(state['id'])

    def token(self):
        self.client.get('/workflow')
        with self.client.session_transaction() as state:
            return state['workflow_csrf']

    def test_pdf_upload_connects_snapshot_without_secrets(self):
        response = self.client.post('/workflow', data={'csrf_token': self.token(), 'requirements_pdf': (BytesIO(sample_pdf()), 'requirements.pdf'), 'code_path': str(self.code), 'adapter': 'python'}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 302)
        session_id = response.location.rsplit('/', 1)[1].split('?')[0]
        state = service.read(session_id)
        self.assertIn('FR-006', state['pages'][0]['text'])
        self.assertEqual(list(state['manifest']), ['calculator.py'])
        self.assertEqual(self.client.get(response.location).status_code, 200)

    def test_invalid_pdf_and_blank_pdf_rejected(self):
        with self.assertRaises(ValueError):
            service.create(b'not a pdf', 'fake.pdf', str(self.code), 'python', '')
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        data = BytesIO()
        writer.write(data)
        with self.assertRaisesRegex(ValueError, 'no readable text'):
            service.create(data.getvalue(), 'scan.pdf', str(self.code), 'python', '')

    def test_selected_approval_and_tamper_rejection(self):
        state = self.generate(self.create())
        service.approve(state['id'], ['T01'])
        approved = service.read(state['id'])
        self.assertEqual([test['id'] for test in service.verify_approval(approved)], ['T01'])
        approved['tests'][0]['code'] += '\n# edited'
        with self.assertRaisesRegex(ValueError, 'code changed'):
            service.verify_approval(approved)

    def test_source_snapshot_tamper_rejected(self):
        state = self.generate(self.create())
        service.approve(state['id'], ['T01'])
        (service.folder(state['id']) / 'source/calculator.py').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'snapshot changed'):
            service.verify_approval(service.read(state['id']))

    def test_unapproved_execution_and_forged_selection_rejected(self):
        state = self.generate(self.create())
        with self.assertRaises(ValueError):
            runner.start(state['id'])
        with self.assertRaises(ValueError):
            service.approve(state['id'], ['T99'])
        self.assertEqual(self.client.post('/workflow/' + state['id'] + '/approve', data={'tests': 'T01'}).status_code, 403)

    def test_malformed_model_code_is_not_reviewable(self):
        state = self.generate(self.create(), [proposed('invalid python !')])
        self.assertEqual(state['status'], 'generation_failed')

    def test_multiple_methods_and_simple_functions_are_supported(self):
        group = PASS + '\n def test_second(self):\n  self.assertEqual(1, 1)\n'
        self.assertIn('test_second', service.validate_code(group))
        converted = service.validate_code('def test_value():\n assert 1 == 1\n')
        self.assertIn('class GeneratedFunctionTests', converted)
        self.assertIn('def test_value(self)', converted)
        with self.assertRaisesRegex(ValueError, 'fixture'):
            service.validate_code('def test_value(client):\n assert client\n')

    def test_one_unsupported_proposal_does_not_discard_valid_tests(self):
        state = self.generate(self.create(), [proposed(PASS), proposed('def test_bad(client):\n assert client\n')])
        self.assertEqual(state['status'], 'review')
        self.assertEqual(len(state['tests']), 1)
        self.assertEqual(len(state['generation_warnings']), 1)

    def test_large_document_and_source_context_is_bounded(self):
        (self.code / 'validation.py').write_text('# ' + '\u2603' * 20000, encoding='utf-8')
        state = self.create()
        state['pages'] = [{'page': n, 'text': 'FR-006-AC01 shall accept equality. ' * 3000} for n in range(1, 32)]
        evidence = service.context(state)
        self.assertLessEqual(len(json.dumps(evidence, ensure_ascii=True)), 8000)
        self.assertLessEqual(sum(len(p['text']) for p in evidence['requirements']), 2400)
        self.assertLessEqual(sum(len(f['text']) for f in evidence['source_files']), 3500)

    def test_request_uses_small_completion_budget(self):
        state = self.create()
        with patch('src.workflow_service.complete', return_value={'text': json.dumps({'tests': [proposed(PASS)]}), 'model': 'mock'}) as model:
            service.generate(state['id'])
        self.assertEqual(model.call_args.kwargs['max_tokens'], 2200)

    def test_old_session_migrates_to_requirement_list_without_reupload(self):
        state = self.create()
        del state['requirements']
        del state['requirements_version']
        state['pages'] = [{'page': 2, 'text': 'FR-001 Add values\nThe system shall add two values.\nFR-001-AC01: Two plus three equals five.'}]
        service.save(state)
        loaded = service.read(state['id'])
        self.assertEqual(loaded['requirements'][0]['id'], 'FR-001')
        page = self.client.get('/workflow/' + state['id'] + '?screen=requirements')
        self.assertIn(b'Requirements by ID', page.data)
        self.assertNotIn(b'Review extracted requirements', page.data)
        self.assertNotIn(b'name="requirements"', page.data)

    def test_generation_uses_records_instead_of_raw_pdf_pages(self):
        state = self.create()
        state['pages'][0]['text'] = 'UNRELATED RAW DOCUMENT TEXT'
        evidence = service.context(state)
        self.assertNotIn('UNRELATED RAW DOCUMENT TEXT', json.dumps(evidence))
        self.assertIn('id', evidence['requirements'][0])

    def test_bounded_output_and_process_timeout(self):
        rc, output, reason = runner.command([sys.executable, '-c', 'print("x" * 200000)'], limit=1000)
        self.assertEqual(reason, 'output_limit')
        self.assertLessEqual(len(output), 1000)
        rc, output, reason = runner.command([sys.executable, '-c', 'import time; time.sleep(5)'], timeout=0.2)
        self.assertEqual(reason, 'timeout')

    def test_approve_all_through_route(self):
        state = self.generate(self.create())
        response = self.client.post('/workflow/' + state['id'] + '/approve',
                                    data={'csrf_token': self.token(), 'tests': ['T01', 'T02']})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(service.read(state['id'])['approval']['tests']), 2)

    def test_report_matches_recorded_outcomes_and_unselected_tests(self):
        state = self.generate(self.create())
        service.approve(state['id'], ['T01'])
        state = service.read(state['id'])
        state.update(status='completed', results=[{'id': 'T01', 'status': 'failed', 'seconds': 0.1, 'exit_code': 1, 'detail': 'Example assertion failure', 'output': 'Example log'}])
        service.save(state)
        response = self.client.get('/workflow/' + state['id'] + '/report')
        self.assertEqual(response.status_code, 200)
        document = Document(BytesIO(response.data))
        content = '\n'.join(p.text for p in document.paragraphs)
        self.assertIn('0 passed and 1 failed', content)
        self.assertIn('Not selected for approval', content)

    @unittest.skipUnless(os.environ.get('QA_DOCKER_TESTS') == '1', 'Explicit Docker verification only')
    def test_real_budgetme_selected_tests_and_word_report(self):
        code = 'from decimal import Decimal\nfrom types import SimpleNamespace\nfrom django.test import SimpleTestCase\nfrom budgetbuddy.services.budget_validation import validate_budget_within_income\nclass Check(SimpleTestCase):\n def test_equality(self):\n  form=SimpleNamespace(cleaned_data={"name":"Food","allocated_amount":Decimal("70000"),"DELETE":False})\n  result=validate_budget_within_income(100000,"monthly",30000,SimpleNamespace(forms=[form]))\n  self.assertTrue(result[0])\n  self.assertEqual(result[2],Decimal("100000"))\n'
        state = self.generate(self.create('budgetme', Path.home() / 'Desktop/capstone/BudgetMe'), [proposed(code), proposed(FAIL), proposed(FAIL, 'Unselected test must not run')])
        service.approve(state['id'], ['T01', 'T02'])
        state = service.read(state['id'])
        state['approval']['reviewer'] = 'Automated workflow verification'
        state['status'] = 'queued'
        service.save(state)
        runner.CANCEL[state['id']] = threading.Event()
        runner.execute(state['id'])
        result = service.read(state['id'])
        self.assertEqual(result['status'], 'completed', result.get('error'))
        self.assertEqual([(r['id'], r['status']) for r in result['results']], [('T01', 'passed'), ('T02', 'failed')], result['results'])
        if os.environ.get('QA_REPORT_CHECK_PATH'):
            Path(os.environ['QA_REPORT_CHECK_PATH']).write_bytes(report_bytes(result))
        self.assertTrue(report_bytes(result).startswith(b'PK'))

    @unittest.skipUnless(os.environ.get('QA_DOCKER_TESTS') == '1', 'Explicit Docker verification only')
    def test_real_container_timeout(self):
        code = 'import unittest\nclass Check(unittest.TestCase):\n def test_timeout(self):\n  while True: pass\n'
        state = self.generate(self.create(), [proposed(code, 'Deliberate timeout verification')])
        service.approve(state['id'], ['T01'])
        state = service.read(state['id'])
        state['approval']['reviewer'] = 'Automated timeout verification'
        state['status'] = 'queued'
        service.save(state)
        runner.CANCEL[state['id']] = threading.Event()
        with patch('src.workflow_runner.TEST_TIMEOUT_SECONDS', 2):
            runner.execute(state['id'])
        result = service.read(state['id'])
        self.assertEqual(result['status'], 'completed', result.get('error'))
        self.assertEqual(result['results'][0]['status'], 'timeout')


if __name__ == '__main__':
    unittest.main()
