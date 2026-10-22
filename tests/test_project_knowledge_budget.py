import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import app as module


class KnowledgeBudgetTests(unittest.TestCase):
    def test_large_records_fit_budget_and_keep_corpus(self):
        context = {key: [{'id': str(i), 'text': 'x' * 20000} for i in range(40)]
                   for key in ('requirements', 'tests', 'results', 'issue_drafts', 'source_files', 'file_index')}
        context['corpus_evidence'] = [{'path': 'knowledge/corpus/budgetme_features.md', 'text': 'BudgetMe budget planning.'}]
        payload = module.bounded_knowledge_payload('q' * 2000, context)
        self.assertLessEqual(len(payload), 6000)
        self.assertIn('BudgetMe budget planning.', payload)
        self.assertIn('omitted or truncated', payload)

    def test_endpoint_budgets_model_input_and_reports_only_sent_sources(self):
        state = dict(name='BudgetMe', status='ready', requirements=[{'id': 'R' + str(i), 'text': 'x' * 10000} for i in range(30)],
                     tests=[], results=[], manifest={})
        corpus = [{'path': 'knowledge/corpus/budgetme_features.md', 'text': 'BudgetMe manages budget plans.'}]
        with patch.object(module.workflow_service, 'read', return_value=state), \
             patch.object(module, 'project_corpus_context', return_value=corpus), \
             patch.object(module.workflow_service, 'complete', return_value={'text': 'BudgetMe manages budget plans.'}) as model:
            response = module.app.test_client().post('/api/assistant', data={'session_id': 'test', 'question': 'what is this project about'})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(model.call_args.args[1]), 6000)
        self.assertEqual(model.call_args.kwargs['max_tokens'], 700)
        sent = json.loads(model.call_args.args[1])['project_context']
        expected = [s['path'] for s in sent['corpus_evidence']] + [r['id'] for r in sent['requirements']]
        self.assertEqual(response.json['sources'], expected)


if __name__ == '__main__':
    unittest.main()
