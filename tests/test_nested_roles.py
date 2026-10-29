"""Real-parser controls for declared nested roles, not instance enumeration."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import check_sysml, JAR, CLASSES
from verifier.workflow import empty_record, analyze
from verifier.concept_review import starter, compare

MODEL = ROOT / 'examples/concept-review/nested-roles/roles.sysml'


@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(), 'Install pinned parser')
class NestedRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = check_sysml(MODEL, syntax_only=True)

    def test_exact_owners_and_same_named_roles_are_distinct(self):
        self.assertEqual(self.native['status'], 'pass', self.native['findings'])
        parts = {p['qualified_name']: p for p in self.native['inventory']['parts'] if p.get('name')}
        a = parts['NestedRoles::Machine::sensor']
        b = parts['NestedRoles::OtherMachine::sensor']
        self.assertEqual(a['owner'], 'NestedRoles::Machine')
        self.assertEqual(b['owner'], 'NestedRoles::OtherMachine')
        self.assertTrue(a['nested'])
        self.assertEqual(a['type'], 'NestedRoles::Sensor')
        self.assertEqual(a['types'], ['NestedRoles::Sensor'])
        self.assertTrue(a['is_composite'])
        self.assertFalse(parts['NestedRoles::machine']['nested'])
        # No invented inherited per-instance paths.
        self.assertNotIn('NestedRoles::machine::sensor', parts)

    def test_explicit_redefinition_subsetting_and_inheritance_targets(self):
        parts = {p['qualified_name']: p for p in self.native['inventory']['parts'] if p.get('name')}
        self.assertEqual(parts['NestedRoles::SelectedMachine::sensor']['redefines'], ['NestedRoles::Machine::sensor'])
        self.assertEqual(parts['NestedRoles::SelectedMachine::spare']['subsets'], ['NestedRoles::Machine::auxiliaries'])
        definitions = {p['qualified_name']: p for p in self.native['inventory']['part_definitions']}
        self.assertEqual(definitions['NestedRoles::SelectedMachine']['supertypes'], ['NestedRoles::Machine'])

    def test_suppressed_and_unknown_bounds_are_not_defaulted_to_present(self):
        parts = {p['qualified_name']: p for p in self.native['inventory']['parts'] if p.get('name')}
        self.assertEqual(parts['NestedRoles::SelectedMachine::disabled']['multiplicity'], {'status': 'literal', 'lower': 0, 'upper': 0})
        self.assertEqual(parts['NestedRoles::Machine::auxiliaries']['multiplicity']['status'], 'unsupported')
        self.assertEqual(parts['NestedRoles::Machine::sensor']['multiplicity'], {'status': 'default', 'lower': 1, 'upper': 1})
        self.assertEqual(parts['NestedRoles::SelectedMachine::sensor']['multiplicity']['status'], 'inherited')

    def record(self):
        r = empty_record('Who acquires?', 'concept')
        r['question']['basis'] = 'SRC'
        r['sources'] = {'SRC': {'sha256': sha256(b'Synthetic').hexdigest(), 'excerpt': 'Synthetic', 'kind': 'proposal'}}
        for key, kind, name in [('N', 'need', 'Need'), ('F', 'function', 'Acquire'), ('R', 'element', 'Machine::sensor'), ('OTHER', 'element', 'OtherMachine::sensor')]:
            r['elements'][key] = dict(kind=kind, native_name='NestedRoles::'+name, label=key, description='Synthetic role', basis='SRC', status='proposed')
        r['relations'] = {'A': dict(kind='allocated_to', **{'from': 'F', 'to': 'R'}, basis='SRC', label='Acquire using selected sensor'),
                          'N_LINK': dict(kind='addresses', **{'from': 'F', 'to': 'N'}, basis='SRC', label='Respond to need')}
        r['workflows']['concept'] = dict(focus=['F'], summary='Inspect role', conditions='Synthetic', outcome='Reviewable', next_decision='Observe')
        return r

    def test_nested_exact_identity_is_admitted_and_retained(self):
        r = self.record()
        result = analyze(r, self.native, {'SRC': {'status': 'pass'}}, workflow='concept')
        self.assertEqual(result['status'], 'pass', result['findings'])
        self.assertEqual(result['bindings']['R']['owner'], 'NestedRoles::Machine')
        self.assertEqual(result['bindings']['R']['source'], str(MODEL.relative_to(ROOT)))

    def test_removing_nested_role_cannot_reuse_a_same_named_sibling(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            path = Path(d)/'removed.sysml'
            path.write_text(MODEL.read_text().replace('part def OtherMachine { part sensor : Sensor; }', 'part def OtherMachine;'))
            native = check_sysml(path, syntax_only=True)
            self.assertEqual(native['status'], 'pass', native['findings'])
            record = self.record()
            record['elements']['R']['native_name'] = 'NestedRoles::OtherMachine::sensor'
            record['elements'].pop('OTHER')
            result = analyze(record, native, {'SRC': {'status': 'pass'}}, workflow='concept')
            self.assertEqual(result['status'], 'fail')
            self.assertTrue(any(f['rule'] == 'native_binding' and f['ids'] == ['R'] for f in result['findings']))

    def test_retained_allocation_scope_detects_sibling_retargeting(self):
        scope = starter('NESTED', 'Nested roles')
        scope['project'].update(question='Who acquires?', boundary='Synthetic machine', basis='SRC')
        scope['sources'] = {'SRC': sha256(b'Synthetic').hexdigest()}
        scope['topics'] = {'operation': {'applicability': 'included', 'rationale': 'Retain exact selected role'}}
        scope['expectations'] = {
            'ROLE': {'topic': 'operation', 'kind': 'element', 'element': 'R', 'element_kind': 'element', 'native_name': 'NestedRoles::Machine::sensor'},
            'ALLOCATION': {'topic': 'operation', 'kind': 'relation', 'relation_kind': 'allocated_to', 'from': 'F', 'to': 'R'}}
        r = self.record()
        self.assertEqual(compare(scope, r)[0], [])
        r['relations']['A']['to'] = 'OTHER'
        self.assertTrue(any(f['rule'] == 'missing_scoped_relation' for f in compare(scope, r)[0]))
        r = self.record(); r['elements']['R']['native_name'] = 'NestedRoles::OtherMachine::sensor'
        self.assertTrue(any(f['rule'] == 'scoped_identity_changed' for f in compare(scope, r)[0]))

    def test_nested_declaration_does_not_expand_sampled_execution_semantics(self):
        source = (ROOT/'examples/sysml/ack.sysml').read_text()
        source = source.replace('part controller : Controller;', 'part def Container { part controller : Controller;')
        source = source.rsplit('}', 1)[0] + '}\n}\n'
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            path = Path(d)/'nested-subject.sysml'; path.write_text(source)
            report = check_sysml(path)
        self.assertEqual(report['status'], 'unsupported', report['findings'])
        self.assertTrue(any('nested role' in f['detail'] for f in report['findings']))


if __name__ == '__main__':
    unittest.main()
