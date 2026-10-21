"""Project navigation and review regressions. All model/run results are fixtures."""
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from tests import test_workflow as fixtures
from src import workflow_service as service
from src.app import app


class ProjectNavigationTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    create = fixtures.WorkflowTests.create
    token = fixtures.WorkflowTests.token

    def proposal_state(self):
        state = self.create()
        proposal = fixtures.proposed(fixtures.PASS)
        proposal['requirement'] = state['requirements'][0]['id']
        del proposal['code']
        state.update(status='review', tests=[dict(proposal,id='T01'),dict(proposal,id='T02')])
        service.save(state)
        return state

    def test_first_screen_and_global_sidebar(self):
        self.assertTrue(self.client.get('/').location.endswith('/dashboard'))
        page = self.client.get('/dashboard').data.decode()
        sidebar = page.split('<nav aria-label="Main navigation">')[1].split('</nav>')[0]
        self.assertEqual(sidebar.count('<a '),4)
        for label in ['Dashboard','Projects','Recent Activity','Settings']:
            self.assertIn(label,sidebar)
        for label in ['Requirements','Test Cases','Executions','Reports']:
            self.assertNotIn(label,sidebar)
        self.assertNotIn('aria-label="Project workspace"',page)
        self.assertNotIn('id="code_path"',page)
        self.assertNotIn('name="requirements_pdf"',page)
        self.assertNotIn('Run Eligible Tests',page)

    def test_project_cards_group_snapshots_and_open_overview(self):
        state=self.create()
        self.create()
        page=self.client.get('/projects').data.decode()
        self.assertEqual(page.count('<article class="project-card">'),1)
        self.assertIn('2 snapshots',page)
        self.assertIn('Connect New Project',page)
        self.assertIn('/overview',page)

    def test_connect_first_then_add_individual_requirement(self):
        response=self.client.post('/projects/new',data={'csrf_token':self.token(),'name':'Calculator','code_path':str(self.code),'adapter':'python'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(response.location.endswith('/overview'))
        sid=response.location.split('/')[-2]
        self.assertEqual(service.read(sid)['requirements'],[])
        fields={'csrf_token':self.token(),'identifier':'FR-001','title':'Add values','text':'The system shall add two values.'}
        self.assertEqual(self.client.post('/projects/'+sid+'/requirements',data=fields).status_code,302)
        self.assertEqual(service.read(sid)['requirements'][0]['id'],'FR-001')
        self.assertEqual(self.client.post('/projects/'+sid+'/requirements',data=fields).status_code,400)
        self.assertEqual(len(service.read(sid)['requirements']),1)

    def test_upload_requirements_inside_project(self):
        state=service.connect(str(self.code),'python')
        response=self.client.post('/projects/'+state['id']+'/requirements',data={'csrf_token':self.token(),'requirements_pdf':(BytesIO(fixtures.sample_pdf()),'srs.pdf')},content_type='multipart/form-data')
        self.assertEqual(response.status_code,302)
        loaded=service.read(state['id'])
        self.assertTrue(loaded['requirements'])
        self.assertIn('FR-006',loaded['pages'][0]['text'])
        self.assertEqual(loaded['requirement_sources'][0]['name'],'srs.pdf')

    def test_project_tabs_are_distinct_views(self):
        state=self.proposal_state()
        for section in ['overview','requirements','cases','executions','reports']:
            response=self.client.get('/projects/'+state['id']+'/'+section)
            self.assertEqual(response.status_code,200)
            page=response.data.decode()
            tabs=page.split('<nav class="project-tabs"')[1].split('</nav>')[0]
            self.assertEqual(tabs.count('<a '),5)
            self.assertEqual(tabs.count('aria-current="page"'),1)
            if section!='cases':self.assertNotIn('Edit Case',page)
            if section!='requirements':self.assertNotIn('name="identifier"',page)
            if section!='executions':self.assertNotIn('Run Eligible Tests',page)

    def test_edit_reject_restore_and_grouping(self):
        state=self.proposal_state();sid=state['id']
        url='/projects/'+sid+'/cases/T01/'
        requirement_id=state['requirements'][0]['id']
        fields={'csrf_token':self.token(),'title':'Edited case','expected':'An edited expected result.','limitations':'Unit check only.','requirement':requirement_id}
        self.assertEqual(self.client.post(url+'edit',data=fields).status_code,302)
        self.assertEqual(service.read(sid)['tests'][0]['title'],'Edited case')
        self.assertEqual(self.client.post(url+'reject',data={'csrf_token':self.token()}).status_code,302)
        with self.assertRaises(ValueError):service.prepare_approval(sid,['T01'])
        self.assertEqual(self.client.post(url+'edit',data=fields).status_code,302)
        self.assertEqual(service.read(sid)['tests'][0]['review_status'],'pending')
        page=self.client.get('/projects/'+sid+'/cases').data
        self.assertIn(requirement_id.encode(),page)
        self.assertIn(b'Edited case',page)
        self.assertTrue(service.read(sid)['test_history'])
        self.assertEqual(self.client.post(url+'reject').status_code,403)

    def test_acceptance_criterion_links_group_under_parent_requirement(self):
        state=self.proposal_state()
        state['tests'][0]['requirement']=state['requirements'][0]['id']+'-AC01: Expected behaviour'
        service.save(state)
        page=self.client.get('/projects/'+state['id']+'/cases').data
        self.assertNotIn(b'Requirement link needs review',page)

    def test_incremental_approval_preserves_earlier_code_and_requires_explicit_run(self):
        state=self.proposal_state();sid=state['id']
        model_response={'text':json.dumps({'tests':[fixtures.proposed(fixtures.PASS)]}),'model':'fixture'}
        for test_id in ['T01','T02']:
            service.prepare_approval(sid,[test_id])
            with patch('src.workflow_service.complete',return_value=model_response) as model:
                service.generate_approved_code(sid)
            model.assert_called_once()
        approved=service.read(sid)
        self.assertEqual(len(service.verify_approval(approved)),2)
        with patch('src.workflow_routes.runner.start') as start:
            self.client.get('/projects/'+sid+'/executions')
            self.client.get('/projects/'+sid+'/reports')
            start.assert_not_called()
            response=self.client.post('/workflow/'+sid+'/run',data={'csrf_token':self.token()})
            self.assertEqual(response.status_code,302)
            start.assert_called_once_with(sid)
        with self.assertRaises(ValueError):service.review_case(sid,'T01','reject')

    def test_incremental_generation_failure_keeps_prior_approval(self):
        state=self.proposal_state();sid=state['id']
        service.prepare_approval(sid,['T01'])
        with patch('src.workflow_service.complete',return_value={'text':json.dumps({'tests':[fixtures.proposed(fixtures.PASS)]}),'model':'fixture'}):service.generate_approved_code(sid)
        before=service.read(sid)['approval']
        service.prepare_approval(sid,['T02'])
        with patch('src.workflow_service.complete',side_effect=RuntimeError('fixture')):service.generate_approved_code(sid)
        state=service.read(sid)
        self.assertEqual(state['approval'],before)
        self.assertEqual([t['id'] for t in service.verify_approval(state)],['T01'])
        self.assertNotIn('code',state['tests'][1])

    def test_contextual_assistant_reads_selected_project(self):
        state=self.create()
        with patch('src.workflow_service.complete',return_value={'text':'Fixture project answer'}) as model:
            response=self.client.post('/api/assistant',data={'question':'What is covered?','session_id':state['id'],'screen':'requirements'})
        self.assertEqual(response.json['answer'],'Fixture project answer')
        payload=json.loads(model.call_args.args[1])
        self.assertEqual(payload['project_context']['project'],state['name'])
        self.assertEqual(payload['project_context']['requirements'][0]['id'],state['requirements'][0]['id'])

    def test_reports_analysis_and_issue_drafts_stay_in_project(self):
        state=self.proposal_state();sid=state['id']
        state.update(status='completed',results=[{'id':'T01','status':'failed','seconds':.1,'output':'Fixture log','detail':'Fixture assertion failure'}])
        service.save(state)
        with patch('src.agent.run_agent',return_value={'message':'Fixture analysis','steps':[],'linked_sources':[],'stop_reason':'FIXTURE','draft':None}) as analyze:
            self.client.get('/projects/'+sid+'/reports')
            analyze.assert_not_called()
            response=self.client.post('/projects/'+sid+'/analysis/T01',data={'csrf_token':self.token()})
        self.assertEqual(response.status_code,302)
        self.assertEqual(service.read(sid)['failure_analyses']['T01']['message'],'Fixture analysis')
        fields={'csrf_token':self.token(),'test_id':'T01','title':'Fixture failure draft','failed_test':'T01','expected':'Expected fixture','actual':'Actual fixture','notes':''}
        with patch('src.tool_service.invoke_tool',return_value={'ok':True,'path':'fixture-draft-path'}) as draft:
            response=self.client.post('/projects/'+sid+'/issues',data=fields)
        self.assertEqual(response.status_code,302)
        draft.assert_called_once()
        self.assertEqual(service.read(sid)['issue_drafts'][0]['test_id'],'T01')
        page=self.client.get('/projects/'+sid+'/reports').data
        self.assertIn(b'Fixture analysis',page)
        self.assertIn(b'Fixture failure draft',page)
