"""Regression coverage for separating target evidence from QA Agent governance."""
import json
import unittest
from unittest.mock import patch
from src import model_service, rag_service


class ProjectEvidenceTests(unittest.TestCase):
    def state(self):
        return {'name':'BudgetMe','knowledge_repository':'https://github.com/Joritace/BudgetMe','requirements':[]}

    def test_target_pipeline_excludes_qa_agent_documents(self):
        pipeline=rag_service.project_pipeline(self.state())
        register=rag_service.load_source_register()
        expected={d['path'] for d in rag_service.load_documents()
                  if register[d['path']].get('origin','').split(';',1)[0].rstrip('/')==self.state()['knowledge_repository']}
        self.assertTrue(expected)
        self.assertEqual({d['path'] for d in pipeline.documents},expected)
        self.assertTrue(all(d['source'].startswith('budgetme_') for d in pipeline.documents))

    def test_unbound_project_does_not_fall_back_to_global_corpus(self):
        result=rag_service.project_retrieve({'name':'Other','requirements':[]},'signup requirements')
        self.assertFalse(result['grounded'])
        self.assertEqual(result['sources'],[])

    def test_session_requirement_keeps_its_identifier_and_provenance(self):
        state={'name':'Other','requirements':[{'id':'SYN-R01','text':'A local draft requires a title.'}]}
        pipeline=rag_service.project_pipeline(state)
        result=pipeline.answer('local draft requires title',generate=False)
        self.assertEqual(result['sources'][0]['source_id'],'SYN-R01')
        self.assertIn('User-supplied',result['sources'][0]['authority'])

    def test_transfer_query_retrieves_minimum_amount(self):
        result=rag_service.project_retrieve(self.state(),'What minimum transfer amount is implemented?')
        self.assertTrue(any('UGX 500' in item['text'] for item in result['sources']))

    def test_optional_reasoning_control_is_sent_only_when_requested(self):
        import io,os
        body=json.dumps({'choices':[{'message':{'content':'ready'},'finish_reason':'stop'}]}).encode()
        with patch.dict(os.environ,{'GROQ_API_KEY':'synthetic-key'}),patch('src.model_service.urllib.request.urlopen',return_value=io.BytesIO(body)) as call:
            model_service.complete('system','synthetic input',reasoning_effort='none')
            self.assertEqual(json.loads(call.call_args.args[0].data)['reasoning_effort'],'none')


if __name__=='__main__':unittest.main()
