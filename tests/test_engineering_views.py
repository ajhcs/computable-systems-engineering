"""Synthetic structural defects and valid tailoring, plus real native/CLI binding."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.engineering_views import check_views
from verifier.sysml import CLASSES, JAR, check_sysml

MODEL = ROOT / 'examples/sysml/views/sample-handling.sysml'
PROFILE = ROOT / 'examples/sysml/views/task-profile.json'


def fixture():
    # Unit tests exercise the view contract; only integration tests claim parsing.
    body = MODEL.read_text().split('doc cseViews /*', 1)[1].split('*/', 1)[0].strip()
    data = json.loads('\n'.join(body.splitlines()[1:]))
    inventory = {group: [] for group in ('attributes', 'events', 'event_attributes', 'parts',
        'part_definitions', 'concerns', 'use_cases', 'actions', 'states', 'requirements', 'constraints', 'documents',
        'ports', 'port_definitions', 'connections')}
    inventory['actions'] = [{'qualified_name': node['element']} for node in data['views'][0]['nodes']]
    inventory['parts'] = [{'qualified_name': item['element']} for item in data['views'][1]['participants']]
    inventory['documents'] = [{'name': 'cseViews', 'owner_kind': 'Package', 'body': body}]
    return data, inventory, json.loads(PROFILE.read_text())


def run_case(data, inventory, profile=None):
    inventory = deepcopy(inventory)
    inventory['documents'][0]['body'] = 'CSE-VIEWS/1.0\n' + json.dumps(data)
    return check_views(inventory, profile)


class ViewQualityTests(unittest.TestCase):
    def setUp(self):
        self.data, self.inventory, self.profile = fixture()
        self.nodes = self.data['views'][0]['nodes']
        self.sequence = self.data['views'][1]

    def report(self, profile=True):
        return run_case(self.data, self.inventory, self.profile if profile else None)

    def codes(self, report):
        self.assertNotEqual(report['status'], 'pass', report)
        return {f['code'] for f in report['findings']}

    def test_valid_structure_and_explicit_claim_limit(self):
        original = deepcopy((self.inventory, self.profile))
        report = self.report()
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['claim_scope'], 'documentary_view_structure')
        self.assertTrue(report['human_review'])
        self.assertEqual((self.inventory, self.profile), original)
        self.assertEqual(len(report['profile_sha256']), 64)

    def test_unannotated_model_is_compatible_but_requested_view_cannot_pass(self):
        self.inventory['documents'] = []
        self.assertEqual(check_views(self.inventory)['status'], 'pass')
        self.assertIn('view_missing', self.codes(check_views(self.inventory, self.profile)))

    def test_missing_requested_level_and_coverage(self):
        self.nodes.pop()
        report = self.report()
        self.assertEqual(report['status'], 'unknown')
        self.assertTrue({'required_level', 'required_id'} <= self.codes(report))

    def test_invalid_roots(self):
        for mutation in ('missing', 'two', 'wrong_level', 'empty'):
            data = deepcopy(self.data)
            nodes = data['views'][0]['nodes']
            if mutation == 'missing':
                nodes[0]['parent'] = 'F1'
            elif mutation == 'two':
                nodes[1].update(parent=None, level=0)
            elif mutation == 'wrong_level':
                nodes[0]['level'] = 1
            else:
                nodes.clear()
            with self.subTest(mutation=mutation):
                self.assertIn('root', self.codes(run_case(data, self.inventory)))

    def test_orphan_and_skipped_levels(self):
        self.nodes[1]['parent'] = 'Absent'
        self.nodes[2]['level'] = 2
        self.assertTrue({'orphan', 'level'} <= self.codes(self.report()))

    def test_disconnected_cycle_and_self_cycle(self):
        self.nodes[1]['parent'] = 'F3'
        self.assertIn('cycle', self.codes(self.report()))
        self.nodes[1]['parent'] = 'F1'
        self.assertIn('cycle', self.codes(self.report()))

    def test_duplicate_ids_in_each_namespace(self):
        for location in ('view', 'node', 'participant', 'exchange', 'participant_exchange'):
            data = deepcopy(self.data)
            seq = data['views'][1]
            if location == 'view':
                data['views'].append(deepcopy(data['views'][0]))
            elif location == 'node':
                data['views'][0]['nodes'].append(deepcopy(self.nodes[0]))
            elif location == 'participant':
                seq['participants'].append(deepcopy(seq['participants'][0]))
            elif location == 'exchange':
                seq['exchanges'].append(deepcopy(seq['exchanges'][0]))
            else:
                seq['exchanges'][0]['id'] = 'OP'
            with self.subTest(location=location):
                self.assertIn('duplicate_id', self.codes(run_case(data, self.inventory)))

    def test_binding_roles_missing_and_ambiguous_native(self):
        self.nodes[1]['element'] = 'SampleHandling::station'
        self.sequence['participants'][0]['element'] = 'SampleHandling::CaptureSample'
        self.assertTrue({'function_binding', 'participant_binding'} <= self.codes(self.report()))
        _, inv, _ = fixture()
        inv['actions'].append(deepcopy(inv['actions'][0]))
        inv['parts'].append(deepcopy(inv['parts'][0]))
        data, _, _ = fixture()
        self.assertTrue({'function_binding', 'participant_binding'} <= self.codes(run_case(data, inv)))

    def test_native_aliases_do_not_invent_functions_or_participants(self):
        self.nodes[1]['element'] = self.nodes[0]['element']
        self.sequence['participants'][1]['element'] = self.sequence['participants'][0]['element']
        self.assertIn('duplicate_binding', self.codes(self.report()))

    def test_counts_are_task_specific_and_missing_parent_detected_even_min_zero(self):
        for field, target, bounds in (('level_counts', '1', {'min': 5}),
                ('level_counts', '1', {'max': 1}), ('child_counts', 'F0', {'min': 3}),
                ('child_counts', 'Absent', {'min': 0})):
            profile = deepcopy(self.profile)
            profile['views'][0][field] = {target: bounds}
            report = run_case(self.data, self.inventory, profile)
            with self.subTest(field=field, bounds=bounds):
                self.assertEqual(report['status'], 'unknown', report)
        # A root-only exploration and no timing are valid without deeper task scope.
        self.nodes[:] = self.nodes[:1]
        for exchange in self.sequence['exchanges']:
            exchange.pop('timing')
        self.assertEqual(self.report(profile=False)['status'], 'pass')

    def test_sequence_requires_nonempty_exchanges_and_declared_endpoints(self):
        self.sequence['exchanges'][0]['from'] = 'Absent'
        self.sequence['exchanges'][0]['message'] = '  '
        self.assertTrue({'endpoint', 'exchange_text'} <= self.codes(self.report()))
        self.sequence['exchanges'] = []
        self.assertIn('sequence_empty', self.codes(self.report(profile=False)))

    def test_self_exchange_and_documentary_order_are_permitted(self):
        self.sequence['exchanges'][0]['to'] = 'OP'
        self.sequence['exchanges'].reverse()
        # List order is the declared order; not a claim about a real trace.
        self.assertEqual(self.report()['status'], 'pass')

    def test_timing_required_only_by_profile(self):
        self.sequence['exchanges'][0].pop('timing')
        self.assertEqual(self.report(profile=False)['status'], 'pass')
        self.assertIn('timing', self.codes(self.report()))

    def test_invalid_timing_never_passes_even_when_optional(self):
        for values in ({'min': 3, 'max': 2}, {'min': -1}, {'max': float('inf')},
                {'max': float('nan')}, {'min': True}, {'max': '4'}, {'unit': ''},
                {'unit': 'meters'}, {'unit': []}, {'basis': ' '}):
            data = deepcopy(self.data)
            data['views'][1]['exchanges'][0]['timing'].update(values)
            with self.subTest(values=values):
                self.codes(run_case(data, self.inventory))
        self.sequence['exchanges'][0]['timing']['max'] = 0
        self.assertEqual(self.report()['status'], 'pass')

    def test_explicit_justified_exceptions_are_reported_without_semantic_acceptance(self):
        self.sequence['exchanges'][0].pop('timing')
        self.profile['views'][1]['exceptions'] = [{'rule': 'timing', 'target': 'E1',
            'rationale': 'Exploratory trigger; timing deferred pending measurement.'}]
        report = self.report()
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['exceptions'][0]['target'], 'E1')
        self.nodes[1]['parent'] = 'Absent'
        self.assertIn('orphan', self.codes(self.report()))

    def test_level_count_coverage_and_child_exceptions(self):
        tree = self.profile['views'][0]
        self.nodes.pop()
        tree['level_counts'] = {'1': {'min': 4}}
        tree['child_counts'] = {'F0': {'min': 4}}
        tree['exceptions'] = [{'rule': rule, 'target': target, 'rationale': 'Synthetic deferred scope.'}
            for rule, target in (('required_level', '2'), ('required_id', 'F3'), ('level_count', '1'), ('child_count', 'F0'))]
        report = self.report()
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(len(report['exceptions']), 4)

    def test_bad_or_unused_exceptions_are_errors_and_cannot_waive_structure(self):
        for exception in ({'rule': 'cycle', 'target': 'F1', 'rationale': 'Do not waive structure'},
                {'rule': 'timing', 'target': 'E1', 'rationale': ''},
                {'rule': 'timing', 'target': 'E1', 'rationale': 'Not actually missing'}):
            profile = deepcopy(self.profile)
            profile['views'][1]['exceptions'] = [exception]
            self.assertEqual(run_case(self.data, self.inventory, profile)['status'], 'error')

    def test_unknown_activity_does_not_substitute_for_tree(self):
        self.data['views'][0]['kind'] = 'activity'
        self.assertNotEqual(self.report()['status'], 'pass')
        self.assertEqual(self.report(profile=False)['status'], 'unsupported')

    def test_strict_contract_rejects_typos_versions_and_invalid_counts(self):
        for alteration in ('extra', 'version', 'bool_level', 'reverse_counts', 'bad_counts', 'wrong_kind', 'duplicate_profile', 'bad_list'):
            data, inventory, profile = fixture()
            if alteration == 'extra':
                data['views'][0]['execute'] = 'not allowed'
            elif alteration == 'version':
                profile['version'] = True
            elif alteration == 'bool_level':
                data['views'][0]['nodes'][0]['level'] = False
            elif alteration == 'reverse_counts':
                profile['views'][0]['level_counts'] = {'1': {'min': 3, 'max': 1}}
            elif alteration == 'bad_counts':
                profile['views'][0]['level_counts'] = {'01': {'min': 2}}
            elif alteration == 'wrong_kind':
                profile['views'][1]['required_levels'] = [0]
            elif alteration == 'duplicate_profile':
                profile['views'].append(deepcopy(profile['views'][0]))
            else:
                data['views'][0]['nodes'] = 'wrong'
            with self.subTest(alteration=alteration):
                self.assertEqual(run_case(data, inventory, profile)['status'], 'error')

    def test_duplicate_json_keys_wrong_owner_and_multiple_blocks(self):
        for body in ('CSE-VIEWS/9.0\n{}', 'CSE-VIEWS/1.0\n{"views":[],"views":[]}'):
            inv = deepcopy(self.inventory)
            inv['documents'][0]['body'] = body
            self.assertEqual(check_views(inv)['status'], 'error')
        self.inventory['documents'][0]['owner_kind'] = 'PartUsage'
        self.assertEqual(check_views(self.inventory)['status'], 'error')
        self.inventory['documents'] *= 2
        self.assertEqual(check_views(self.inventory)['status'], 'error')

    def test_requested_view_missing_and_wrong_kind(self):
        self.data['views'].pop()
        self.assertIn('view_missing', self.codes(self.report()))
        self.profile['views'][0]['kind'] = 'sequence'
        for field in ('required_levels', 'level_counts', 'child_counts'):
            self.profile['views'][0].pop(field)
        self.assertIn('view_kind', self.codes(self.report()))

    def workflow(self):
        record = {field: {} for field in ("question", "sources", "elements", "relations", "workflows", "decisions", "questions", "trade_studies", "evidence")}
        record["version"] = "workflow-1.0"
        for node in self.nodes:
            record["elements"][node["id"]] = {"kind": "function", "native_name": node["element"],
                "label": node["id"], "description": "Synthetic function", "basis": None, "status": "proposed"}
            if node["parent"] is not None:
                record["relations"]["D" + node["id"]] = {"kind": "decomposes", "from": node["parent"],
                    "to": node["id"], "basis": None, "label": ""}
        return record

    def with_workflow(self, record):
        inventory = deepcopy(self.inventory)
        inventory["documents"].append({"name": "cseWorkflow", "body": "CSE-WORKFLOW/1.0\n" + json.dumps(record)})
        return run_case(self.data, inventory, self.profile)

    def test_existing_workflow_hierarchy_must_match_without_duplicate_native_roles(self):
        record = self.workflow()
        report = self.with_workflow(record)
        self.assertEqual(report["status"], "pass", report)
        self.assertEqual(report["views"][0]["workflow_reconciliation"]["status"], "pass")
        for mutation in ("reversed", "extra_parent", "alias", "missing_edge", "missing_function"):
            changed = deepcopy(record)
            if mutation == "reversed":
                edge = changed["relations"]["DF1"]
                edge["from"], edge["to"] = edge["to"], edge["from"]
            elif mutation == "extra_parent":
                changed["relations"]["EXTRA"] = {**changed["relations"]["DF1"], "from": "F2"}
            elif mutation == "alias":
                changed["elements"]["ALIAS"] = deepcopy(changed["elements"]["F1"])
            elif mutation == "missing_edge":
                changed["relations"].pop("DF1")
            else:
                changed["elements"]["F1"]["kind"] = "step"
            with self.subTest(mutation=mutation):
                self.assertIn("workflow_conflict", self.codes(self.with_workflow(changed)))

    def test_workflow_external_parent_allowed_only_for_scoped_root_and_omissions_visible(self):
        record = self.workflow()
        record["elements"]["CONTEXT"] = {**record["elements"]["F0"], "native_name": "SampleHandling::Context"}
        record["relations"]["CONTEXT_EDGE"] = {"kind": "decomposes", "from": "CONTEXT", "to": "F0", "basis": None, "label": ""}
        self.assertEqual(self.with_workflow(record)["status"], "pass")
        record["relations"]["CONTEXT_EDGE"]["to"] = "F1"
        self.assertIn("workflow_conflict", self.codes(self.with_workflow(record)))
        record["relations"].pop("CONTEXT_EDGE")
        record["relations"]["OMITTED_EDGE"] = {"kind": "decomposes", "from": "F0", "to": "CONTEXT", "basis": None, "label": ""}
        report = self.with_workflow(record)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["views"][0]["workflow_reconciliation"]["omitted_children"], ["CONTEXT"])

    def test_workflow_metadata_malformed_or_future_version_refuses_reconciliation(self):
        for mutation in ("version", "containers", "relation", "extra"):
            record = self.workflow()
            if mutation == "version":
                record["version"] = "workflow-9.0"
            elif mutation == "containers":
                record["elements"] = []
            elif mutation == "relation":
                record["relations"]["DF1"]["to"] = "Absent"
            else:
                record["surprise"] = True
            with self.subTest(mutation=mutation):
                self.assertEqual(self.with_workflow(record)["status"], "error")

    def test_explicit_null_profile_cli_is_invalid_even_without_annotations(self):
        # No parser is needed: invalid explicit input must fail before it runs.
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            profile = Path(directory) / 'null.json'
            for value in ('null', '[]', 'false', '"invalid"'):
                profile.write_text(value)
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/sysml.py'),
                    str(ROOT / 'examples/sysml/concept.sysml'), '--syntax-only', '--view-profile', str(profile)],
                    text=True, capture_output=True)
                self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
                self.assertIn('must be a JSON object', result.stderr)

    def test_structure_finding_propagates_to_parent_and_legacy_path_unchanged(self):
        self.nodes[1]['parent'] = 'Absent'
        inv = deepcopy(self.inventory)
        inv['documents'][0]['body'] = 'CSE-VIEWS/1.0\n' + json.dumps(self.data)
        with patch('verifier.sysml._parser_output', return_value=inv):
            report = check_sysml(MODEL, syntax_only=True, view_profile=self.profile)
        self.assertEqual(report['status'], 'fail', report)
        self.assertIn('view_orphan', {f['code'] for f in report['findings']})
        inv['documents'] = []
        with patch('verifier.sysml._parser_output', return_value=inv):
            report = check_sysml(MODEL, syntax_only=True)
        self.assertEqual(report['status'], 'pass')
        self.assertNotIn('view_checks', report)


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(), 'Install pinned SysML parser')
class NativeViewIntegrationTests(unittest.TestCase):
    def test_real_parser_binds_native_actions_parts_and_profile(self):
        report = check_sysml(MODEL, syntax_only=True, view_profile=json.loads(PROFILE.read_text()))
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['view_checks']['status'], 'pass')
        self.assertEqual(len(report['inventory']['actions']), 4)

    def test_real_parser_reconciles_existing_workflow_and_rejects_conflicting_parent(self):
        unit = ViewQualityTests()
        unit.setUp()
        record = unit.workflow()
        record["question"] = {"text": "Synthetic sample-handling hierarchy", "basis": None}
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            model = Path(directory) / 'joint-metadata.sysml'
            source = MODEL.read_text().rsplit('}', 1)[0]
            for conflict in (False, True):
                if conflict:
                    record['relations']['DF1']['from'] = 'F2'
                block = 'concern workflowContext { doc cseWorkflow /*CSE-WORKFLOW/1.0\n' + json.dumps(record) + '\n*/ }\n}'
                model.write_text(source + block)
                report = check_sysml(model, syntax_only=True, view_profile=json.loads(PROFILE.read_text()))
                self.assertEqual(report['status'], 'fail' if conflict else 'pass', report)
                if conflict:
                    self.assertIn('view_workflow_conflict', {f['code'] for f in report['findings']})

    def test_all_three_entry_points_from_another_directory_and_nonzero_on_missing_level(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            for skill in ('develop-system-concept', 'develop-conops', 'develop-operational-scenarios'):
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'skills' / skill / 'scripts/cse.py'),
                    'check', str(MODEL), '--syntax-only', '--view-profile', str(PROFILE), '--json'],
                    cwd=directory, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertEqual(json.loads(result.stdout)['view_checks']['status'], 'pass')
            profile = json.loads(PROFILE.read_text())
            profile['views'][0]['required_levels'].append(3)
            bad = Path(directory) / 'missing-level.json'
            bad.write_text(json.dumps(profile))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/sysml.py'), str(MODEL),
                '--syntax-only', '--view-profile', str(bad)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn('view_required_level', result.stdout)
            self.assertIn('no behavior evaluated', result.stdout)


if __name__ == '__main__':
    unittest.main()
