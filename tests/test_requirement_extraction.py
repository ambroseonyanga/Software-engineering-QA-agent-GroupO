import unittest

from src.requirement_extraction import extract_requirements


class RequirementExtractionTests(unittest.TestCase):
    def test_contents_are_ignored_and_criteria_continue_across_pages(self):
        result = extract_requirements([
            {'page': 1, 'text': 'Contents\nFR-006 Planning limit .... 10\nFR-007 Categories .... 11'},
            {'page': 10, 'text': 'FR-006 Planning limit\nSD | P1 | Evidence S03\nThe system shall reject excessive plans.\nFR-006-AC01: Accept equality.\nFR-006-AC02: Reject excess'},
            {'page': 11, 'text': 'and preserve the saved plan.\nFR-007 Categories\nPT | P2 | Evidence S04\nThe system should validate names.'},
        ])
        self.assertEqual([r['id'] for r in result], ['FR-006', 'FR-007'])
        self.assertEqual(result[0]['page'], 10)
        self.assertIn('preserve the saved plan', result[0]['criteria'][1]['text'])
        self.assertEqual(result[1]['status'], 'Proposed target')

    def test_plain_requirements_get_traceable_local_ids(self):
        result = extract_requirements([{'page': 3, 'text': 'Project introduction. Users must be able to sign out. The app shall reject a negative amount.'}])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'REQ-001')
        self.assertEqual(result[0]['page'], 3)
        self.assertNotIn('Project introduction', result[0]['text'])

    def test_document_without_requirements_does_not_invent_them(self):
        self.assertEqual(extract_requirements([{'page': 1, 'text': 'Title page and project background.'}]), [])
