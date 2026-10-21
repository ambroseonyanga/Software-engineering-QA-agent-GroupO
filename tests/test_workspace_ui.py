"""Offline regression checks; model responses and run outcomes are fixtures."""
import json
import unittest
from unittest.mock import patch
from tests import test_workflow as fixtures
from src import workflow_service as service
from src import workflow_runner as runner
from src.workflow_report import report_bytes


class WorkspaceUITests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    create = fixtures.WorkflowTests.create
    token = fixtures.WorkflowTests.token

    def suggestions(self):
        state = self.create()
        proposal = fixtures.proposed(fixtures.PASS)
        del proposal['code']
        with patch('src.workflow_service.complete', return_value={'text': json.dumps({'tests': [proposal, dict(proposal, title='Unselected proposal')]}), 'model': 'offline-fixture'}):
            service.generate(state['id'], proposals_only=True)
        return service.read(state['id'])

    def test_manual_entry_creates_requirement_records(self):
        response = self.client.post('/workflow', data={'csrf_token': self.token(), 'manual_text': 'FR-001 Add values\nThe system shall add two values.\nFR-001-AC01: Two plus three equals five.', 'code_path': str(self.code), 'adapter': 'python'})
        self.assertEqual(response.status_code, 302)
        state = service.read(response.location.split('/')[-1].split('?')[0])
        self.assertEqual(state['pdf_name'], 'Manual requirements')
        self.assertEqual(state['requirements'][0]['id'], 'FR-001')
        self.assertFalse((service.folder(state['id']) / 'requirements.pdf').exists())

    def test_code_is_generated_only_for_approved_descriptions(self):
        state = self.suggestions()
        self.assertEqual(state['status'], 'review')
        self.assertTrue(all('code' not in test for test in state['tests']))
        with self.assertRaises(ValueError):
            runner.start(state['id'])
        service.prepare_approval(state['id'], ['T01'])
        with self.assertRaises(ValueError):
            runner.start(state['id'])
        with patch('src.workflow_service.complete', return_value={'text': json.dumps({'tests': [fixtures.proposed(fixtures.PASS)]}), 'model': 'offline-fixture'}) as model:
            service.generate_approved_code(state['id'])
        model.assert_called_once()
        state = service.read(state['id'])
        self.assertEqual(state['status'], 'approved')
        self.assertIn('code', state['tests'][0])
        self.assertNotIn('code', state['tests'][1])
        self.assertEqual([t['id'] for t in service.verify_approval(state)], ['T01'])
        state['status'] = 'cancelled'
        self.assertTrue(report_bytes(state).startswith(b'PK'))

    def test_code_generation_failure_remains_reviewable_and_unrunnable(self):
        state = self.suggestions()
        service.prepare_approval(state['id'], ['T01'])
        with patch('src.workflow_service.complete', side_effect=RuntimeError('fixture failure')):
            service.generate_approved_code(state['id'])
        state = service.read(state['id'])
        self.assertEqual(state['status'], 'review')
        self.assertIsNone(state['approval'])
        self.assertTrue(all('code' not in t for t in state['tests']))
        with self.assertRaises(ValueError):
            runner.start(state['id'])

    def test_duplicate_approval_and_invalid_selection_rejected(self):
        state = self.suggestions()
        response = self.client.post('/workflow/' + state['id'] + '/approve', data={'csrf_token': self.token()})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'role="alert"', response.data)
        self.assertEqual(service.read(state['id'])['status'], 'review')
        with self.assertRaises(ValueError):
            service.prepare_approval(state['id'], ['T99'])
        service.prepare_approval(state['id'], ['T01'])
        with self.assertRaises(ValueError):
            service.prepare_approval(state['id'], ['T01'])

    def test_all_screens_render_without_and_with_session(self):
        state = self.suggestions()
        for path in ['/dashboard', '/projects', '/activity', '/settings'] + ['/projects/' + state['id'] + '/' + s for s in ['overview','requirements','cases','executions','reports']]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'aria-current="page"', response.data)
        state.update(status='completed', results=[{'id': 'T01', 'status': 'failed', 'seconds': .1, 'output': '<script>fixture</script>', 'detail': 'Fixture assertion failure'}])
        service.save(state)
        response = self.client.get('/workflow/' + state['id'] + '?screen=results')
        self.assertIn(b'Save Issue Draft', response.data)
        self.assertIn(b'&lt;script&gt;fixture&lt;/script&gt;', response.data)
        self.assertNotIn(b'<script>fixture</script>', response.data)

    def test_assistant_uses_existing_knowledge_service(self):
        with patch('src.app.answer_question', return_value={'answer': 'Fixture answer', 'grounded': True}) as answer:
            response = self.client.post('/api/assistant', data={'question': 'What is covered?'})
        answer.assert_called_once_with('What is covered?')
        self.assertEqual(response.json['answer'], 'Fixture answer')
        self.assertEqual(self.client.post('/api/assistant', data={'question': ''}).status_code, 400)
        self.assertEqual(self.client.post('/api/assistant', data={'question': 'Test'}, headers={'Origin':'https://example.org'}).status_code, 403)
