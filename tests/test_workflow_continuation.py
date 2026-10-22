"""Regression checks for continuing a project after execution."""
import copy
import unittest
from unittest.mock import patch
from src import workflow_service as service
from src.app import app
from src import workflow_routes as routes


class ContinuationTests(unittest.TestCase):
    def state(self, status):
        return dict(id='a'*32, name='Project', adapter='python', created='2026-01-01',
            status=status, requirements=[{'id':'R1'}, {'id':'R2'}],
            tests=[{'id':'T01', 'requirement':'R1', 'review_status':'approved'}],
            results=[{'id':'T01','status':'passed'}], events=[],
            approval={'tests':{'T01':'hash'}}, finished='2026-01-02', error=None)

    def test_terminal_states_allow_generation_without_losing_run_evidence(self):
        for status in ['completed','blocked','cancelled']:
            with self.subTest(status=status):
                state=self.state(status)
                prior=copy.deepcopy(state)
                with patch.object(service,'read',return_value=state), patch.object(service,'save'):
                    service.prepare_requirement_batch(state['id'],['R2'])
                self.assertEqual(state['status'],'generation_queued')
                self.assertEqual(state['requirement_batch'],['R2'])
                self.assertEqual(state['results'],prior['results'])
                self.assertEqual(state['execution_history'][0]['approval'],prior['approval'])
                self.assertIsNone(state['approval'])
                self.assertEqual(state['tests'],prior['tests'])

    def test_active_operations_still_block_generation(self):
        for status in ['queued','running','generating','code_generating']:
            with patch.object(service,'read',return_value=self.state(status)), patch.object(service,'save') as save:
                with self.assertRaises(ValueError):service.prepare_requirement_batch('a'*32,['R2'])
                save.assert_not_called()

    def test_covered_requirements_still_rejected(self):
        with patch.object(service,'read',return_value=self.state('completed')), patch.object(service,'save'):
            with self.assertRaises(ValueError):service.prepare_requirement_batch('a'*32,['R1'])

    def test_issues_tab_order_and_drafts_location(self):
        keys=list(routes.PROJECT_VIEWS)
        self.assertEqual(keys[keys.index('executions')+1],'issues')
        with app.test_request_context():
            issues=app.jinja_env.get_template('project_issues.html')
            reports=app.jinja_env.get_template('project_reports.html')
            state=dict(id='a'*32, issue_drafts=[dict(title='Existing draft',test_id='T01',at='2026-01-01',path='draft.json')],results=[],tests=[],status='completed')
            self.assertIn('Existing draft',issues.render(state=state))
            self.assertNotIn('Existing draft',reports.render(state=state))
