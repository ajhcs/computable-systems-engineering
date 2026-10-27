"""Selected NIST derivative checks; no original-source or browser execution."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'examples/industrial-project-reference'
SPEC = importlib.util.spec_from_file_location('industrial_reference_check', BASE / 'tools/check.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class IndustrialReferenceTests(unittest.TestCase):
    def setUp(self):
        self.wireless = BASE / 'wireless-robot-controller'
        self.ledger = json.loads((self.wireless / 'semantic-ledger.json').read_text())
        self.facts = json.loads((self.wireless / 'native-linked-facts.json').read_text())
        self.coupler = json.loads((BASE / 'nist-electronics-makecoupler/semantic-ledger.json').read_text())

    def copied(self):
        parent = ROOT / '.tmp'
        parent.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(temp.cleanup)
        dest = Path(temp.name) / 'references'
        shutil.copytree(BASE, dest)
        return dest

    def test_both_nist_cases_have_explicit_limited_status(self):
        result = CHECK.validate()
        self.assertEqual(len(result['wireless_presentations']), 2)
        self.assertEqual(result['makecoupler']['presentation'], 'held')
        self.assertEqual(result['fresh_browser_render'], 'not_run')

    def test_xppu_request_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, 'held pending GPL'):
            CHECK.require_case('xppu-scenario15')

    def test_private_transceiver_cannot_be_made_public(self):
        next(r for r in self.ledger['roles'] if r['name'] == 'xcvr')['visibility'] = 'public'
        with self.assertRaisesRegex(ValueError, 'ownership/visibility/bounds'):
            CHECK.validate_wireless_ledger(self.ledger, self.facts)

    def test_data_port_cannot_gain_a_connector(self):
        self.ledger['connectors'][0]['ends'][0]['path'] = 'DataPort'
        with self.assertRaisesRegex(ValueError, 'unconnected'):
            CHECK.validate_wireless_ledger(self.ledger, self.facts)

    def test_native_endpoint_change_rejected(self):
        self.ledger['connectors'][0]['ends'][0]['path'] = 'xcvr.xcvr'
        with self.assertRaisesRegex(ValueError, 'native endpoints'):
            CHECK.validate_wireless_ledger(self.ledger, self.facts)

    def test_added_direction_on_wireless_graphic_rejected(self):
        dest = self.copied() / 'wireless-robot-controller'
        path = dest / 'port-topology.svg'
        svg = ET.parse(path)
        next(e for e in svg.getroot().iter() if e.tag.endswith('polyline') and e.get('stroke-width') == '2').set('marker-end', 'url(#arrow)')
        svg.write(path, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'invented connector direction'):
            CHECK.validate_wireless_view(dest, 'port-topology', self.ledger)

    def test_coupler_repeated_call_cannot_collapse(self):
        self.coupler['orderedCallIDs'][1] = self.coupler['orderedCallIDs'][0]
        with self.assertRaisesRegex(ValueError, 'call identity'):
            CHECK.validate_coupler_ledger(self.coupler)

    def test_control_flow_cannot_become_object_flow(self):
        self.coupler['edges'][0]['kind'] = 'ObjectFlow'
        with self.assertRaisesRegex(ValueError, 'no ObjectFlow'):
            CHECK.validate_coupler_ledger(self.coupler)

    def test_untyped_work_order_cannot_gain_a_type(self):
        pin = next(p for n in self.coupler['nodes'] for p in n.get('pins', []) if p['name'] == 'workOrderIN')
        pin['type'] = {'status': 'resolved', 'id': 'invented', 'name': 'WorkOrder'}
        with self.assertRaisesRegex(ValueError, 'must stay unresolved'):
            CHECK.validate_coupler_ledger(self.coupler)

    def test_missing_required_wireless_view_does_not_skip(self):
        dest = self.copied()
        (dest / 'wireless-robot-controller/endpoint-ledger.svg').unlink()
        with self.assertRaises((ValueError, OSError)):
            CHECK.validate(dest)

    def test_held_coupler_graphic_cannot_silently_rejoin(self):
        dest = self.copied()
        (dest / 'nist-electronics-makecoupler/activity-reading.svg').write_text('<svg/>')
        with self.assertRaisesRegex(ValueError, 'Held MakeCoupler presentation'):
            CHECK.validate(dest)

    def test_native_part_cannot_move_to_another_declared_owner(self):
        for changed in ({'name': 'IKApp'}, {'qualified': 'WirelessRobotControllerSelected::IKApp'}, {'kind': 'PartUsage'}):
            with self.subTest(changed=changed):
                facts = copy.deepcopy(self.facts)
                part = next(f for f in facts if f['kind'] == 'PartUsage' and f['name'] == 'xcvr')
                part['owner'].update(changed)
                with self.assertRaisesRegex(ValueError, 'declared selected-view owner'):
                    CHECK.validate_wireless_ledger(self.ledger, facts)

    def test_native_part_cannot_change_its_declared_type(self):
        facts = copy.deepcopy(self.facts)
        part = next(f for f in facts if f['kind'] == 'PartUsage' and f['name'] == 'xcvr')
        part['types'] = copy.deepcopy(next(f for f in facts if f['kind'] == 'PartUsage' and f['name'] == 'inverse Kinematics')['types'])
        with self.assertRaisesRegex(ValueError, 'declared part type'):
            CHECK.validate_wireless_ledger(self.ledger, facts)

    def test_reference_rectangle_cannot_lose_visible_dashed_outline(self):
        folder = self.copied() / 'wireless-robot-controller'
        path = folder / 'port-topology.svg'
        tree = ET.parse(path)
        next(e for e in tree.getroot().iter() if e.get('id') == 'WFC-01-port-topology-12').attrib.pop('stroke-dasharray')
        tree.write(path, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'reference/owned role glyph'):
            CHECK.validate_wireless_view(folder, 'port-topology', self.ledger)

    def test_reference_rectangle_cannot_lose_editable_dashed_outline(self):
        folder = self.copied() / 'wireless-robot-controller'
        path = folder / 'port-topology.drawio'
        tree = ET.parse(path)
        cell = next(e for e in tree.findall('.//mxCell') if e.get('id') == 'WFC-01-port-topology-12')
        cell.set('style', cell.get('style').replace('dashed=1;', 'dashed=0;'))
        tree.write(path, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'reference/owned role glyph'):
            CHECK.validate_wireless_view(folder, 'port-topology', self.ledger)

    def test_owned_transceiver_cannot_gain_reference_outline(self):
        folder = self.copied() / 'wireless-robot-controller'
        path = folder / 'port-topology.svg'
        tree = ET.parse(path)
        next(e for e in tree.getroot().iter() if e.get('id') == 'WFC-01-port-topology-7').set('stroke-dasharray', '9 5')
        tree.write(path, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'reference/owned role glyph'):
            CHECK.validate_wireless_view(folder, 'port-topology', self.ledger)

    def test_reference_outline_css_override_is_not_ignored(self):
        folder = self.copied() / 'wireless-robot-controller'
        path = folder / 'port-topology.svg'
        tree = ET.parse(path)
        next(e for e in tree.getroot().iter() if e.get('id') == 'WFC-01-port-topology-12').set('style', 'stroke-dasharray: none')
        tree.write(path, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'role-outline override'):
            CHECK.validate_wireless_view(folder, 'port-topology', self.ledger)

    def test_coupler_consistent_call_collapse_is_rejected(self):
        first, second = self.coupler['orderedCallIDs'][:2]
        next(n for n in self.coupler['nodes'] if n['id'] == second)['id'] = first
        self.coupler['orderedCallIDs'] = [first if value == second else value for value in self.coupler['orderedCallIDs']]
        for edge in self.coupler['edges']:
            for end in ('source', 'target'):
                if edge[end] == second:
                    edge[end] = first
        with self.assertRaisesRegex(ValueError, '17 distinct calls'):
            CHECK.validate_coupler_ledger(self.coupler)

    def test_coupler_self_loop_is_explicitly_rejected(self):
        edge = self.coupler['edges'][0]
        edge['target'] = edge['source']
        with self.assertRaisesRegex(ValueError, 'self-loop'):
            CHECK.validate_coupler_ledger(self.coupler)


if __name__ == '__main__':
    unittest.main()
