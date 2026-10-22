import io,json,os,sys,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import model_service,qa_service
from src.output_format import render_output
from src.rag_service import load_documents

class IntegrationTests(unittest.TestCase):
 def test_payload_too_large_has_actionable_error(self):
  error=urllib.error.HTTPError('https://example.invalid',413,'too large',{},None)
  with patch.dict(os.environ,{'GROQ_API_KEY':'test-key'}),patch('src.model_service.urllib.request.urlopen',side_effect=error) as call:
   with self.assertRaisesRegex(model_service.ModelUnavailable,'request as too large'):model_service.complete('s','u')
   self.assertEqual(call.call_count,1)
 def body(self,text='ready',finish='stop'):
  return io.BytesIO(json.dumps({'choices':[{'message':{'content':text},'finish_reason':finish}],'usage':{'total_tokens':10}}).encode())
 def test_missing_key_makes_no_network_request(self):
  with patch.dict(os.environ,{},clear=True),patch('src.model_service.urllib.request.urlopen') as call:
   with self.assertRaises(model_service.ModelUnavailable):model_service.complete('s','u')
   call.assert_not_called()
 def test_messages_separate_requirement_from_system(self):
  with patch.dict(os.environ,{'GROQ_API_KEY':'test-key'}),patch('src.model_service.urllib.request.urlopen',return_value=self.body()) as call:
   model_service.complete('instructions','requirement');p=json.loads(call.call_args.args[0].data)
   self.assertEqual(p['messages'],[{'role':'system','content':'instructions'},{'role':'user','content':'requirement'}])
   self.assertNotIn('test-key',json.dumps(p))
 def test_rate_limit_is_not_retried(self):
  error=urllib.error.HTTPError('https://example.invalid',429,'quota',{},None)
  with patch.dict(os.environ,{'GROQ_API_KEY':'test-key'}),patch('src.model_service.urllib.request.urlopen',side_effect=error) as call:
   with self.assertRaises(model_service.RateLimited):model_service.complete('s','u')
   self.assertEqual(call.call_count,1)
 def test_truncated_decision_is_rejected(self):
  with patch.dict(os.environ,{'GROQ_API_KEY':'test-key'}),patch('src.model_service.urllib.request.urlopen',return_value=self.body('{','length')):
   with self.assertRaises(model_service.ModelUnavailable):model_service.complete('s','u')
 def test_invalid_response_body_is_safe_error(self):
  with patch.dict(os.environ,{'GROQ_API_KEY':'test-key'}),patch('src.model_service.urllib.request.urlopen',return_value=io.BytesIO(b'<html>gateway error</html>')):
   with self.assertRaisesRegex(model_service.ModelUnavailable,'unreadable response'):model_service.complete('s','u')
 def test_qa_loads_exact_v12(self):
  with patch('src.qa_service.complete',return_value={'text':'answer'}) as call:
   self.assertEqual(qa_service.analyse_requirement('input'),'answer')
   self.assertEqual(call.call_args.args,(model_service.load_prompt('prompt-v1.2.txt'),'input'))
 def test_html_and_table_cells_are_escaped(self):
  html=str(render_output('A | B\n--- | ---\n<script>x</script> | <img src=x onerror=x>'))
  self.assertIn('<table>',html);self.assertNotIn('<script>',html);self.assertNotIn('<img',html)
 def test_assignment_records_are_not_retrieved(self):
  names={d['source'] for d in load_documents()}
  self.assertTrue({'project_charter.md','user_stories.md','ai_boundary_matrix.md','tool_catalogue.md','agent_task_contract.md','budgetme_features.md','budgetme_architecture.md','budgetme_api.md','budgetme_testing.md'} <= names)
  self.assertFalse(any('progress' in name.lower() or 'evaluation' in name.lower() for name in names))
if __name__=='__main__':unittest.main()
