"""Bounded counts on delivered text, with explicit budgets and no rewriting."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.prose import check_text, MAX_FINDINGS, SNIPPET_CHARACTERS


class ProseTests(unittest.TestCase):
    def test_concise_technical_text_and_exact_boundary(self):
        text = 'The controller waits 250 ms.\n\nThe conveyor remains idle.'
        report = check_text(text, kind='description', sentence_words=5,
                            paragraph_words=5, document_words=9)
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['counts'], {'words': 9, 'sentences': 2, 'paragraphs': 2})
        failed = check_text(text, kind='description', document_words=8)
        self.assertEqual(failed['status'], 'fail')
        self.assertEqual(failed['findings'][0]['limit'], 8)

    def test_excessive_realistic_paragraph_has_exact_location(self):
        text = ('Scope.\n\nThe controller moves the workpiece after the upstream sensor '
                'confirms its position and the receiving conveyor reports an idle state.')
        report = check_text(text, kind='description', sentence_words=15, paragraph_words=18)
        self.assertEqual(report['status'], 'fail')
        self.assertEqual({f['rule'] for f in report['findings']},
                         {'CSE-PROSE-SENTENCE', 'CSE-PROSE-PARAGRAPH'})
        for finding in report['findings']:
            self.assertEqual((finding['line'], finding['column']), (3, 1))
            self.assertEqual(text[finding['start']:finding['end']], finding['text'])

    def test_units_decimals_identifiers_and_quotations_are_counted(self):
        text = 'SRC-01 waits 2.5 ms. "The gate remains idle."'
        report = check_text(text, kind='description', document_words=8)
        self.assertEqual(report['counts'], {'words': 8, 'sentences': 2, 'paragraphs': 1})
        self.assertEqual(report['status'], 'pass')

    def test_missing_invalid_budgets_and_nontext_cannot_pass(self):
        for kwargs in ({}, {'sentence_words': 0}, {'paragraph_words': True},
                       {'sentence_words': '25'}, {'document_words': -1},
                       {'paragraph_words': 2.5}):
            self.assertEqual(check_text('Text.', kind='description', **kwargs)['status'], 'error')
        for text in ('', ' \n', 'Data\x00.', b'bytes'):
            self.assertEqual(check_text(text, kind='description', document_words=5)['status'], 'error')
        self.assertEqual(check_text('Text.', kind='guessed', document_words=5)['status'], 'error')

    def test_no_terminal_punctuation_or_blank_line_bypass(self):
        report = check_text('one two three\n\nfour five six', kind='procedure',
                            sentence_words=2, document_words=5)
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['counts']['words'], 6)
        self.assertEqual(len(report['findings']), 3)

    def test_dense_violations_keep_total_failure_and_bound_diagnostics(self):
        text = ('The valve shall remain closed.\n\n' * (MAX_FINDINGS + 10)).rstrip()
        report = check_text(text, kind='description', sentence_words=1,
                            paragraph_words=1, document_words=1)
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['total_findings'], 2 * (MAX_FINDINGS + 10) + 1)
        self.assertEqual(report['returned_findings'], MAX_FINDINGS)
        self.assertTrue(report['findings_truncated'])
        first = report['findings'][0]
        self.assertEqual((first['start'], first['end']), (0, len(text)))
        self.assertEqual(first['count'], 5 * (MAX_FINDINGS + 10))
        self.assertTrue(first['text_truncated'])
        self.assertEqual(len(first['text']), SNIPPET_CHARACTERS)
        self.assertLess(len(json.dumps(report)), 70_000)
        self.assertEqual(report['findings'][3]['line'], 3)
        self.assertEqual(report['findings'][3]['column'], 1)

    def test_long_single_violation_snippet_is_bounded_without_findings_cap(self):
        text = 'word ' * 1000
        report = check_text(text, kind='description', document_words=10)
        self.assertEqual(report['status'], 'fail')
        self.assertFalse(report['findings_truncated'])
        self.assertEqual(report['total_findings'], 1)
        self.assertEqual(report['findings'][0]['count'], 1000)
        self.assertEqual(report['findings'][0]['end'], len(text.rstrip()))
        self.assertTrue(report['findings'][0]['text_truncated'])

    def test_cli_is_readonly_and_retains_budget(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as directory:
            path = Path(directory)/'report.txt'
            original = b'The pump shall stop. The valve should close. The operator may wait.'
            path.write_bytes(original)
            result = subprocess.run([sys.executable, str(ROOT/'scripts/prose.py'), str(path),
                '--kind', 'description', '--document-words', '4', '--json'],
                capture_output=True, text=True)
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report['limits']['document_words'], 4)
            self.assertEqual(path.read_bytes(), original)
            path.write_bytes(b'\xff\xfe')
            invalid = subprocess.run([sys.executable, str(ROOT/'scripts/prose.py'), str(path),
                '--kind', 'description', '--document-words', '4', '--json'],
                capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(json.loads(invalid.stdout)['status'], 'error')
            html = Path(directory)/'report.html'
            html.write_text('<p>Text.</p>')
            unsupported = subprocess.run([sys.executable, str(ROOT/'scripts/prose.py'), str(html),
                '--kind', 'description', '--document-words', '4', '--json'],
                capture_output=True, text=True)
            self.assertEqual(unsupported.returncode, 2)


if __name__ == '__main__':
    unittest.main()
