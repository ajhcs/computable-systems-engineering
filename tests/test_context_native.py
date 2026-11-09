"""Actual linked native references and bounded context coverage controls.

The base inventory is parsed from the existing connected fixture. Mutations below
exercise reference handling after that parse; they are not fresh parser evidence
for the mutated declarations or configuration/behavior proofs.
"""
from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.configuration import reconcile
from verifier.context import assemble_context
from verifier.context_native import add_native_references, REFERENCE_CLAIM_SCOPE
from verifier.foundation import check_profile
from verifier.sysml import check_sysml, CLASSES, JAR

BASE = ROOT / 'examples/configuration-review/connected'
CURRENT = 'parts:LinkContext::current'
PEER = 'parts:LinkContext::enterprise'
HISTORICAL = 'parts:LinkContext::historical'
CONNECTION = 'connections:LinkContext::dataLink'
DATA = 'port_definitions:LinkLibrary::Data'
OUTPUT = 'ports:LinkLibrary::Sensor::output'
GROUPS = ('part_definitions', 'parts', 'concerns', 'use_cases', 'actions',
          'states', 'requirements', 'constraints', 'attributes', 'events',
          'ports', 'port_definitions', 'connections')


def graph_inputs(native):
    """Existing direct typing/containment only; no inferred connector incidence."""
    index = {group + ':' + row['qualified_name']: {'category': group, 'record': row}
             for group in GROUPS for row in native['inventory'].get(group, [])
             if row.get('qualified_name')}
    graph = {key: {} for key in index}
    by_name = {}
    for key, item in index.items():
        by_name.setdefault(item['record']['qualified_name'], []).append(key)
    for key, item in index.items():
        row = item['record']
        target = 'part_definitions:' + str(row.get('type'))
        if item['category'] == 'parts' and target in graph:
            graph[key][target] = ['native_direct_type']
        for parent in by_name.get(row['qualified_name'].rsplit('::', 1)[0], []):
            graph[parent][key] = ['native_qualified_containment']
    return index, graph


def closure(graph, root):
    pending, visited, result = deque([root]), {root}, []
    while pending:
        key = pending.popleft()
        result.append(key)
        for target in sorted(graph[key]):
            if target not in visited:
                visited.add(target)
                pending.append(target)
    return result


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Install the pinned SysML parser for actual native reference controls')
class NativeFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = check_sysml([BASE / 'library.sysml', BASE / 'current.sysml'],
                                 syntax_only=True)
        if cls.native['status'] != 'pass':
            raise AssertionError(cls.native)
        scope = json.loads((BASE / 'scope.json').read_text())
        if reconcile(scope, cls.native['inventory'])['status'] != 'pass':
            raise AssertionError('Existing connected fixture no longer reconciles its own scope')
        cls.profile = {'version': 'foundation-1.0', 'source_sha256': cls.native['model_sha256'],
                       'terms': {}, 'elements': {}, 'relations': [], 'use_cases': {},
                       'allocations': {}, 'capabilities': {}}
        for identity, selection in [('CURRENT', scope['root']),
                                    ('PEER', scope['external_roles']['Enterprise'])]:
            cls.profile['terms']['T_' + identity] = {
                'namespace': 'Synthetic.ReferenceReview', 'revision': '1',
                'label': identity.lower(), 'definition': 'The supplied ' + identity.lower() + ' declaration.',
                'kind': 'resource'}
            cls.profile['elements'][identity] = {
                'kind': 'resource', 'term': 'T_' + identity,
                'native_name': selection['native_name']}
        checked = check_profile(cls.profile, cls.native)
        if checked['status'] != 'pass':
            raise AssertionError(checked)

    def references(self, native=None):
        selected = deepcopy(self.native if native is None else native)
        index, graph = graph_inputs(selected)
        unresolved = add_native_references(index, graph,
                                           connections=selected['inventory']['connections'])
        return selected, index, graph, unresolved


class NativeReferenceControls(NativeFixture):
    def test_actual_connection_preserves_external_peer_and_declared_port_type(self):
        original = deepcopy(self.native)
        native, index, graph, unresolved = self.references()
        self.assertEqual(unresolved, [])
        self.assertTrue({CURRENT, PEER, CONNECTION, DATA, OUTPUT} <= set(closure(graph, CURRENT)))
        self.assertEqual(native, self.native)
        self.assertEqual(self.native, original)
        self.assertEqual(index[CONNECTION]['record']['ends'], [
            {'path': ['LinkContext::current', 'LinkLibrary::System::sensor',
                      'LinkLibrary::Sensor::output'], 'status': 'supported',
             'reason': 'Linked static part/port feature chain'},
            {'path': ['LinkContext::enterprise', 'LinkLibrary::Receiver::input'],
             'status': 'supported', 'reason': 'Linked static part/port feature chain'}])

    def test_reference_traversal_is_reciprocal_without_a_flow_direction_claim(self):
        native, index, graph, unresolved = self.references()
        for context in (CURRENT, PEER):
            self.assertIn(CONNECTION, graph[context])
            self.assertIn(context, graph[CONNECTION])
        self.assertIn(CURRENT, closure(graph, PEER))
        self.assertIn('not_configuration_or_flow', REFERENCE_CLAIM_SCOPE)
        reversed_native = deepcopy(self.native)
        reversed_native['inventory']['connections'][0]['ends'].reverse()
        _, _, reversed_graph, reversed_unresolved = self.references(reversed_native)
        self.assertEqual(graph, reversed_graph)
        self.assertEqual(unresolved, reversed_unresolved)

    def test_shared_types_do_not_attach_unreferenced_instances(self):
        _, _, graph, _ = self.references()
        for root in (HISTORICAL, 'parts:LinkContext::secondReceiver'):
            with self.subTest(root=root):
                self.assertNotIn(CONNECTION, closure(graph, root))
                self.assertNotIn(CURRENT, closure(graph, root))
                self.assertNotIn(PEER, closure(graph, root))
        self.assertNotIn(CONNECTION, graph[OUTPUT])

    def test_usage_owner_anchors_an_exact_relative_endpoint_chain(self):
        native = deepcopy(self.native)
        row = native['inventory']['connections'][0]
        row.update(qualified_name='LinkContext::current::localLink',
                   owner='LinkContext::current', owner_kind='PartUsage')
        row['ends'][0]['path'] = row['ends'][0]['path'][1:]
        _, _, graph, unresolved = self.references(native)
        self.assertEqual(unresolved, [])
        self.assertIn('connections:LinkContext::current::localLink', closure(graph, CURRENT))
        self.assertIn(PEER, closure(graph, CURRENT))
        self.assertNotIn(PEER, closure(graph, HISTORICAL))
        self.assertEqual(row['ends'][0]['path'][0], 'LinkLibrary::System::sensor')

    def test_native_definition_ancestry_and_conjugate_original_are_one_way(self):
        native = deepcopy(self.native)
        original = next(row for row in native['inventory']['port_definitions']
                        if row['qualified_name'] == 'LinkLibrary::Data')
        conjugate = deepcopy(original)
        conjugate.update(qualified_name='Synthetic::ConjugatedData', is_conjugated=True,
                         original_port_definition='LinkLibrary::Data')
        native['inventory']['port_definitions'].append(conjugate)
        output = next(row for row in native['inventory']['ports']
                      if row['qualified_name'] == 'LinkLibrary::Sensor::output')
        output['type'] = 'Synthetic::ConjugatedData'
        _, _, graph, unresolved = self.references(native)
        self.assertEqual(unresolved, [])
        self.assertIn('port_definitions:Synthetic::ConjugatedData', closure(graph, CURRENT))
        self.assertIn(DATA, closure(graph, CURRENT))
        self.assertNotIn('port_definitions:Synthetic::ConjugatedData', graph[DATA])
        self.assertIn('part_definitions:LinkLibrary::Sensor',
                      graph['part_definitions:LinkLibrary::InheritedSensor'])
        self.assertNotIn('part_definitions:LinkLibrary::InheritedSensor',
                         graph['part_definitions:LinkLibrary::Sensor'])

    def test_missing_port_type_and_supertype_are_explicit_unresolved_references(self):
        native = deepcopy(self.native)
        native['inventory']['port_definitions'] = []
        inherited = next(row for row in native['inventory']['part_definitions']
                         if row['qualified_name'] == 'LinkLibrary::InheritedSensor')
        inherited['supertypes'] = ['Missing::Base']
        _, _, graph, unresolved = self.references(native)
        self.assertTrue(any(row['rule'] == 'native_port_type' and OUTPUT in row['ids']
                            and row['status'] == 'unknown' for row in unresolved))
        self.assertTrue(any(row['rule'] == 'native_definition_ancestry'
                            and row['status'] == 'unknown' for row in unresolved))
        self.assertIn(OUTPUT, closure(graph, CURRENT))

    def test_missing_endpoint_declaration_cannot_supply_complete_coverage(self):
        native = deepcopy(self.native)
        native['inventory']['connections'][0]['ends'][1]['path'][-1] = 'Missing::input'
        _, _, graph, unresolved = self.references(native)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['status'], 'unknown')
        self.assertTrue({CURRENT, PEER, CONNECTION} <= set(unresolved[0]['ids']))
        self.assertEqual(unresolved[0]['claim_scope'], REFERENCE_CLAIM_SCOPE)
        self.assertNotIn(PEER, closure(graph, CURRENT))

    def test_unsupported_endpoint_and_binding_are_not_silently_admitted(self):
        for variant in ('endpoint', 'binding', 'variable'):
            with self.subTest(variant=variant):
                native = deepcopy(self.native)
                row = native['inventory']['connections'][0]
                if variant == 'endpoint':
                    row['ends'][0]['status'] = 'unsupported'
                elif variant == 'binding':
                    row['kind'] = 'BindingConnectorAsUsage'
                else:
                    row['is_variant'] = True
                _, _, graph, unresolved = self.references(native)
                self.assertEqual(len(unresolved), 1)
                self.assertEqual(unresolved[0]['status'], 'unsupported')
                self.assertIn(CURRENT, unresolved[0]['ids'])
                self.assertNotIn(PEER, closure(graph, CURRENT))

    def test_anonymous_connector_is_unresolved_without_a_synthetic_native_identity(self):
        native = deepcopy(self.native)
        native['inventory']['connections'][0].update(qualified_name=None, name=None)
        _, index, graph, unresolved = self.references(native)
        self.assertEqual(set(index), set(graph))
        self.assertFalse(any(key.startswith('connections:') for key in graph))
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['rule'], 'native_anonymous_connection')
        self.assertTrue({CURRENT, PEER} <= set(unresolved[0]['ids']))
        self.assertIsNone(unresolved[0]['scope_hint']['qualified_name'])
        self.assertEqual(unresolved[0]['scope_hint']['owner'], 'LinkContext')

    def test_unavailable_endpoints_retain_a_conservative_context_location(self):
        native = deepcopy(self.native)
        native['inventory']['connections'][0].update(ends=[], supported=False)
        _, _, graph, unresolved = self.references(native)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['status'], 'unknown')
        hint = unresolved[0]['scope_hint']
        self.assertTrue(hint['conservative_same_context'])
        self.assertEqual(hint['owner'], 'LinkContext')
        self.assertEqual(hint['owner_kind'], 'Package')
        self.assertEqual(hint['source'], 'examples/configuration-review/connected/current.sysml')
        self.assertEqual(hint['endpoint_anchors'], [])
        self.assertNotIn(CONNECTION, closure(graph, CURRENT))

    def test_deterministic_idempotent_graph_updates_and_work_cap(self):
        native, index, graph, unresolved = self.references()
        before = deepcopy((native, index, graph, unresolved))
        repeated = add_native_references(index, graph,
                                         connections=native['inventory']['connections'])
        self.assertEqual((native, index, graph, repeated), before)
        with patch('verifier.context_native.MAX_REFERENCE_WORK', 1):
            with self.assertRaisesRegex(ValueError, 'work cap'):
                add_native_references(index, graph)


class NativeReferenceIntegration(NativeFixture):
    def test_assembled_native_context_retains_named_adjacency_peer_and_port_type(self):
        result = assemble_context(deepcopy(self.native), profile=deepcopy(self.profile),
                                  element_id='CURRENT', limit=512)
        self.assertEqual(result['status'], 'pass', result['findings'])
        self.assertTrue(result['coverage']['complete'])
        self.assertIn('T_PEER', result['concepts'])
        self.assertEqual(result['native_context']['connections'][0]['qualified_name'],
                         'LinkContext::dataLink')
        self.assertTrue(any(row['qualified_name'] == 'LinkLibrary::Data'
                            for row in result['native_context']['port_definitions']))
        self.assertIs(result['native_context']['connection_semantics']['directed'], False)
        self.assertEqual(result['semantic_review'], 'not_run')
        self.assertEqual(result['required_review'], 'not_evaluated')

    def test_unresolved_native_connections_cannot_be_complete(self):
        for variant, expected in [('missing', 'unknown'), ('unsupported', 'unsupported'),
                                  ('anonymous', 'unknown'), ('no_endpoints', 'unknown')]:
            with self.subTest(variant=variant):
                native = deepcopy(self.native)
                connection = native['inventory']['connections'][0]
                if variant == 'missing':
                    connection['ends'][1]['path'][-1] = 'Missing::input'
                elif variant == 'unsupported':
                    connection['ends'][0]['status'] = 'unsupported'
                elif variant == 'anonymous':
                    connection.update(qualified_name=None, name=None)
                else:
                    connection.update(ends=[], supported=False)
                result = assemble_context(native, profile=deepcopy(self.profile),
                                          element_id='CURRENT', limit=512)
                self.assertEqual(result['status'], expected, result['findings'])
                self.assertFalse(result['coverage']['complete'])
                self.assertTrue(result['coverage']['unresolved'])

    def test_shared_type_historical_context_is_a_valid_separate_control(self):
        profile = deepcopy(self.profile)
        profile['terms']['T_HISTORICAL'] = {
            'namespace': 'Synthetic.ReferenceReview', 'revision': '1',
            'label': 'historical', 'definition': 'The explicitly distinct historical usage.',
            'kind': 'resource'}
        profile['elements']['HISTORICAL'] = {
            'kind': 'resource', 'term': 'T_HISTORICAL', 'native_name': 'LinkContext::historical'}
        for anonymous in (False, True):
            with self.subTest(anonymous=anonymous):
                native = deepcopy(self.native)
                if anonymous:
                    native['inventory']['connections'][0].update(qualified_name=None, name=None)
                result = assemble_context(native, profile=profile, element_id='HISTORICAL', limit=512)
                self.assertEqual(result['status'], 'pass', result['findings'])
                self.assertTrue(result['coverage']['complete'])
                self.assertEqual(result['native_context']['connections'], [])
                self.assertNotIn('T_CURRENT', result['concepts'])
                self.assertNotIn('T_PEER', result['concepts'])

    def test_partial_endpoint_context_remains_unresolved_for_same_context_selection(self):
        profile = deepcopy(self.profile)
        profile['terms']['T_HISTORICAL'] = {
            **profile['terms']['T_CURRENT'], 'label': 'historical',
            'definition': 'The explicitly distinct historical usage.'}
        profile['elements']['HISTORICAL'] = {
            'kind': 'resource', 'term': 'T_HISTORICAL', 'native_name': 'LinkContext::historical'}
        for variant in ('empty_path', 'unsupported_chain', 'missing_context'):
            with self.subTest(variant=variant):
                native = deepcopy(self.native)
                other = native['inventory']['connections'][0]['ends'][1]
                if variant == 'empty_path':
                    other.update(path=[], status='unsupported')
                elif variant == 'unsupported_chain':
                    other['status'] = 'unsupported'
                else:
                    other['path'] = other['path'][-1:]
                result = assemble_context(native, profile=profile,
                                          element_id='HISTORICAL', limit=512)
                self.assertNotEqual(result['status'], 'pass', result)
                self.assertFalse(result['coverage']['complete'])
                gap = next(row for row in result['coverage']['unresolved']
                           if row['rule'].startswith('native_connection'))
                self.assertIn(CURRENT, gap['ids'])
                self.assertIn(CURRENT, gap['scope_hint']['endpoint_anchors'])
                self.assertTrue(gap['scope_hint']['conservative_same_context'])

    def test_small_limit_discloses_known_native_dependencies(self):
        result = assemble_context(deepcopy(self.native), profile=deepcopy(self.profile),
                                  element_id='CURRENT', limit=1)
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['coverage']['complete'])
        self.assertIn(CONNECTION, result['coverage']['omitted_ids'])
        self.assertIn(DATA, result['coverage']['omitted_ids'])
        self.assertIn('foundation:PEER', result['coverage']['omitted_ids'])
        self.assertEqual(result['coverage']['returned_elements'], 1)


if __name__ == '__main__':
    unittest.main()
