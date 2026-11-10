"""Behavior and failure boundaries for the discoverable sampled-trace adapter."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.language import check_document
from verifier.sampled_trace import MAX_INPUT_BYTES, check_trace_bytes, schema_document


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def fixture():
    schema = schema_document()
    model = schema['example_document']
    model['observations'] = [{'request': False, 'response': False},
                             {'request': True, 'response': True}]
    model['complete'] = True
    return model, schema['example_scope']


def review(model, scope):
    raw_scope = encoded(scope)
    return check_trace_bytes(encoded(model), raw_scope,
                             scope_sha256=sha256(raw_scope).hexdigest())


class SampledTraceTests(unittest.TestCase):
    def test_schema_example_compiles_but_cannot_claim_an_executed_review(self):
        schema = schema_document()
        self.assertEqual(schema['status'], 'not_run')
        model, scope = schema['example_document'], schema['example_scope']
        self.assertEqual(check_document(model)['status'], 'pass')
        self.assertEqual(review(model, scope)['status'], 'unknown')

    def test_valid_adapter_preserves_existing_monitor_result_and_exact_raw_binding(self):
        model, scope = fixture()
        actual = review(model, scope)
        expected = check_document(model, review=True, expected=scope)
        self.assertEqual({k: actual[k] for k in expected}, expected)
        self.assertEqual(actual['status'], 'pass')
        self.assertEqual(actual['input_binding']['document_sha256'], sha256(encoded(model)).hexdigest())
        spaced_scope = json.dumps(scope, indent=2).encode()
        mismatch = check_trace_bytes(encoded(model), spaced_scope, scope_sha256=sha256(encoded(scope)).hexdigest())
        self.assertEqual(mismatch['error']['code'], 'scope_digest')

    def test_omitted_independent_obligation_stays_unknown(self):
        model, scope = fixture()
        scope['required'].append('R_MISSING')
        actual = review(model, scope)
        self.assertEqual(actual['status'], 'unknown')
        self.assertEqual(actual['scope']['missing'], ['R_MISSING'])

    def test_native_manifest_shape_is_not_silently_converted(self):
        model, _ = fixture()
        native_scope = {'version': 1, 'source_revision': 'synthetic-1',
                        'expected': [{'id': 'R_EXAMPLE', 'constraint': 'sample', 'source': 'SYN'}]}
        result = review(model, native_scope)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error']['code'], 'scope')

    def test_stale_scope_pin_fails_before_a_narrowed_scope_can_pass(self):
        model, scope = fixture()
        original = encoded(scope)
        scope['required'] = []
        actual = check_trace_bytes(encoded(model), encoded(scope), scope_sha256=sha256(original).hexdigest())
        self.assertEqual(actual['status'], 'error')
        self.assertEqual(actual['error']['code'], 'scope_digest')
        self.assertEqual(actual['results'], {})

    def test_null_or_nonobject_scope_cannot_select_candidate_obligations(self):
        model, _ = fixture()
        for scope in (None, False, 1, 'scope', []):
            with self.subTest(scope=scope):
                actual = review(model, scope)
                self.assertEqual(actual['status'], 'error')
                self.assertEqual(actual['error']['code'], 'scope_schema')
                self.assertTrue(actual['required_review'])
                self.assertEqual(actual['results'], {})

    def test_stale_document_pin_fails(self):
        model, scope = fixture()
        before = encoded(model)
        model['observations'][1]['response'] = False
        actual = check_trace_bytes(encoded(model), encoded(scope),
                                   scope_sha256=sha256(encoded(scope)).hexdigest(),
                                   document_sha256=sha256(before).hexdigest())
        self.assertEqual(actual['error']['code'], 'document_digest')

    def test_missing_or_invalid_scope_pin_is_not_a_required_pass(self):
        model, scope = fixture()
        for pin in (None, '', True, 'bad'):
            with self.subTest(pin=pin):
                actual = check_trace_bytes(encoded(model), encoded(scope), scope_sha256=pin)
                self.assertEqual(actual['status'], 'error')
                self.assertEqual(actual['error']['code'], 'scope_digest')

    def test_prior_guessed_schema_forms_are_rejected_without_coercion(self):
        model, scope = fixture()
        mutations = [
            lambda m: m.update(language_version=True),
            lambda m: m.update(actors={'ExampleUnit': {'type': 'actor'}}),
            lambda m: m['properties']['request'].pop('owner'),
            lambda m: m['properties']['request'].update(type='boolean'),
            lambda m: m.update(requirements=[{'id': 'R_EXAMPLE', 'text': m['requirements']['R_EXAMPLE']}]),
            lambda m: m['clock'].update(period=1),
            lambda m: m.update(source='unrecognized metadata'),
        ]
        for mutation in mutations:
            candidate = deepcopy(model)
            mutation(candidate)
            with self.subTest(model=candidate):
                self.assertEqual(review(candidate, scope)['status'], 'error')

    def test_failed_trace_retains_counterexample(self):
        model, scope = fixture()
        model['observations'][1]['response'] = False
        result = review(model, scope)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['results']['R_EXAMPLE']['counterexample']['index'], 1)

    def test_no_trigger_and_incomplete_window_cannot_pass(self):
        model, scope = fixture()
        model['observations'][1]['request'] = False
        self.assertEqual(review(model, scope)['status'], 'unknown')
        model, scope = fixture()
        model['complete'] = False
        self.assertEqual(review(model, scope)['status'], 'unknown')

    def test_duplicate_keys_nonfinite_and_malformed_json_are_errors(self):
        _, scope = fixture()
        for raw in (b'{"actors":{},"actors":{"ExampleUnit":{}}}', b'{"value":NaN}',
                    b'{"value":1e999}', b'[]\xff', b'{'):
            with self.subTest(raw=raw):
                actual = check_trace_bytes(raw, encoded(scope), scope_sha256=sha256(encoded(scope)).hexdigest())
                self.assertEqual(actual['status'], 'error')
                self.assertEqual(actual['error']['code'], 'json')

    def test_escaped_unpaired_surrogate_is_a_structured_input_error(self):
        model, scope = fixture()
        model['complete'] = '\ud800'
        actual = review(model, scope)
        self.assertEqual(actual['status'], 'error')
        self.assertEqual(actual['error']['code'], 'json')
        self.assertTrue(actual['required_review'])
        self.assertEqual(actual['results'], {})

    def test_input_byte_limit_is_an_error_not_a_verdict(self):
        _, scope = fixture()
        actual = check_trace_bytes(b' ' * (MAX_INPUT_BYTES + 1), encoded(scope),
                                   scope_sha256=sha256(encoded(scope)).hexdigest())
        self.assertEqual(actual['error']['code'], 'input_limit')

    def test_cli_schema_is_help_and_actual_trace_checks_exit_on_non_success(self):
        script = ROOT / 'scripts/sampled_trace.py'
        schema = subprocess.run([sys.executable, '-B', str(script), 'schema'], text=True,
                                capture_output=True, check=True)
        self.assertEqual(json.loads(schema.stdout)['status'], 'not_run')
        model, scope = fixture()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            directory = Path(tmp)
            document, manifest = directory / 'trace.json', directory / 'scope.json'
            document.write_bytes(encoded(model))
            manifest.write_bytes(encoded(scope))
            command = [sys.executable, '-B', str(script), 'trace', str(document),
                       '--scope', str(manifest), '--scope-sha256', sha256(manifest.read_bytes()).hexdigest()]
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'pass')
            model['observations'][1]['response'] = False
            document.write_bytes(encoded(model))
            failed = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(json.loads(failed.stdout)['status'], 'fail')
            model['observations'][1]['response'] = True
            model['complete'] = '\ud800'
            document.write_bytes(encoded(model))
            malformed = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(malformed.returncode, 0)
            self.assertEqual(json.loads(malformed.stdout)['error']['code'], 'json')
            self.assertNotIn('Traceback', malformed.stderr)
            model['complete'] = True
            document.write_bytes(encoded(model))
            manifest.write_text('null')
            null_scope = [*command[:-1], sha256(manifest.read_bytes()).hexdigest()]
            invalid_scope = subprocess.run(null_scope, text=True, capture_output=True)
            self.assertNotEqual(invalid_scope.returncode, 0)
            self.assertEqual(json.loads(invalid_scope.stdout)['error']['code'], 'scope_schema')
            document.unlink()
            absent = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(absent.returncode, 0)
            self.assertEqual(json.loads(absent.stdout)['error']['code'], 'input_io')


if __name__ == '__main__':
    unittest.main()
