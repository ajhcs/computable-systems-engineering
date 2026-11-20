"""Challenge premature progression, stale evidence and concealed interface gaps."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.workbench_parity import inspect, LAYERS


def ledger():
    operation = {'id': 'composition.rename', 'outcome': 'Rename a part',
                 'authority': 'model.sysml', 'contract': 'physical composition',
                 'runtime': 'pinned Pilot', 'acceptance': ['identity', 'source', 'hosts'],
                 'layers': {k: {'status': 'planned', 'evidence': []} for k in LAYERS}}
    return {'version': 'cse-workbench-parity-1', 'inventory_status': 'reconciling',
            'active_capability': 'composition', 'capabilities': [
                {'id': 'composition', 'status': 'active', 'operations': [operation]}]}


class ParityTests(unittest.TestCase):
    def test_valid_inventory_is_not_workbench_completion(self):
        result = inspect(ledger(), ROOT)
        self.assertEqual(result['status'], 'pass')
        self.assertFalse(result['workbench_complete'])
        self.assertEqual(result['closed'], [])

    def test_incomplete_capability_cannot_be_marked_proved(self):
        data = ledger(); data['capabilities'][0]['status'] = 'proved'
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')

    def test_no_second_capability_or_hidden_layer_work(self):
        data = ledger(); second = deepcopy(data['capabilities'][0])
        second['id'] = 'sequence'; second['operations'][0]['id'] = 'sequence.edit'
        data['capabilities'].append(second)
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')
        second['status'] = 'planned'; second['operations'][0]['layers']['visual']['status'] = 'active'
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')

    def test_missing_interface_and_unexplained_not_applicable(self):
        data = ledger(); del data['capabilities'][0]['operations'][0]['layers']['chatgpt_component']
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')
        data = ledger(); cell = data['capabilities'][0]['operations'][0]['layers']['mcp']
        cell['status'] = 'not_applicable'
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')

    def test_proof_without_execution_receipt_is_rejected(self):
        data = ledger(); cell = data['capabilities'][0]['operations'][0]['layers']['validation']
        cell.update(status='proved', evidence=[{'result': 'pass', 'test_id': 'not_observed'}])
        self.assertEqual(inspect(data, ROOT)['status'], 'fail')

    def test_source_and_receipt_changes_invalidate_evidence(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            root = Path(directory); source = root / 'model.sysml'; receipt = root / 'receipt.json'
            source.write_text('package Synthetic;')
            receipt.write_text('{"status":"pass"}')
            data = ledger(); cell = data['capabilities'][0]['operations'][0]['layers']['source']
            cell.update(status='proved', evidence=[{'result': 'pass', 'test_id': 'source_preservation',
                'inputs': {'model.sysml': sha256(source.read_bytes()).hexdigest()},
                'receipt': {'path': 'receipt.json', 'sha256': sha256(receipt.read_bytes()).hexdigest()}}])
            self.assertEqual(inspect(data, root)['status'], 'pass')
            source.write_text('package Changed;')
            self.assertEqual(inspect(data, root)['status'], 'fail')
            source.write_text('package Synthetic;'); receipt.write_text('{"status":"fail"}')
            self.assertEqual(inspect(data, root)['status'], 'fail')

    def test_actual_inventory_has_only_physical_composition_admitted(self):
        data = json.loads((ROOT / 'docs/workbench/parity.json').read_text())
        report = inspect(data, ROOT)
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['active'], ['physical_composition'])
        self.assertFalse(report['workbench_complete'])


if __name__ == '__main__':
    unittest.main()
