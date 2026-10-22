"""Parser extraction refusal controls, including real ambiguous native identities."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import check_sysml, JAR, CLASSES

GROUPS = ('attributes', 'events', 'event_attributes', 'parts', 'part_definitions',
          'concerns', 'use_cases', 'actions', 'states', 'requirements', 'constraints', 'documents')
MODEL = ROOT / 'examples/sysml/ack.sysml'


class ParserContractTests(unittest.TestCase):
    def check(self, parsed, **options):
        with patch('verifier.sysml._parser_output', return_value=parsed):
            return check_sysml(MODEL, **options)

    def parsed(self):
        return {'issues': [], **{group: [] for group in GROUPS}}

    def test_unresolved_identified_requirement_is_error_not_exception(self):
        parsed = self.parsed()
        parsed['requirements'] = [{'id': 'R_ACK', 'name': 'Ambiguous', 'line': 2}]
        for syntax in (False, True):
            report = self.check(copy.deepcopy(parsed), syntax_only=syntax)
            self.assertEqual(report['status'], 'error')
            self.assertEqual(report['findings'][0]['code'], 'identity')
            self.assertEqual(report['results'], {})

    def test_unnamed_computational_binding_is_explicitly_unsupported(self):
        for group in ('requirements', 'parts', 'part_definitions', 'constraints'):
            parsed = self.parsed()
            parsed[group].append({'line': 2})
            report = self.check(parsed)
            self.assertEqual(report['status'], 'unsupported')
            self.assertEqual(report['findings'][0]['code'], 'unresolved_identity')

    def test_malformed_extraction_and_diagnostics_return_contract_error(self):
        for patch_value in ({'issues': {}}, {'issues': [None]}, {'requirements': [None]}, {'parts': {}}):
            parsed = self.parsed()
            parsed.update(patch_value)
            report = self.check(parsed, syntax_only=True)
            self.assertEqual(report['status'], 'error')
            self.assertEqual(report['findings'][0]['code'], 'parser_contract')

    @unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(), 'Pinned native parser unavailable')
    def test_actual_pilot_ambiguous_namespace_does_not_crash(self):
        source = MODEL.read_text()
        source = source.replace('requirement <R_ACK> TimelyAcknowledgment {',
                                'action def TimelyAcknowledgment;\n    requirement <R_ACK> TimelyAcknowledgment {')
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            path = Path(directory) / 'ambiguous.sysml'
            path.write_text(source)
            report = check_sysml(path, syntax_only=True)
        self.assertEqual(report['status'], 'error', report)
        self.assertTrue(any(issue['severity'] == 'WARNING' for issue in report['parser_issues']))
        self.assertTrue(any(item['code'] == 'identity' for item in report['findings']))


if __name__ == '__main__':
    unittest.main()
