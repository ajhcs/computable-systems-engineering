"""Fail-closed progression checks for the capability delivery ledger.

Evidence files are local observations, not authenticated engineer acceptance.
The checker never runs arbitrary commands supplied in a ledger.
"""
from hashlib import sha256
from pathlib import Path


LAYERS = ('semantics', 'source', 'visual', 'interaction', 'cli', 'mcp',
          'codex_site_tools', 'chatgpt_component', 'persistence', 'validation', 'exports')
STATES = {'planned', 'active', 'blocked', 'proved', 'not_applicable'}


def inspect(ledger, root):
    root = Path(root).resolve()
    findings = []

    def issue(location, reason):
        findings.append({'location': location, 'reason': reason})

    if not isinstance(ledger, dict) or ledger.get('version') != 'cse-workbench-parity-1':
        return {'status': 'error', 'findings': [{'reason': 'Invalid ledger version'}]}
    capabilities = ledger.get('capabilities')
    if not isinstance(capabilities, list) or not capabilities:
        return {'status': 'error', 'findings': [{'reason': 'No capability inventory'}]}
    seen, active, closed, all_complete = set(), [], [], True
    previous_closed = True
    all_operations = set()
    for capability in capabilities:
        cid = capability.get('id')
        if not isinstance(cid, str) or cid in seen:
            issue('capabilities', 'Missing or duplicate capability identity')
        seen.add(cid)
        if capability.get('status') not in STATES - {'not_applicable'}:
            issue(cid, 'Invalid capability status')
        if capability.get('status') == 'active':
            active.append(cid)
            if not previous_closed:
                issue(cid, 'An earlier capability has not closed')
        if capability.get('status') == 'proved' and not previous_closed:
            issue(cid, 'An earlier capability has not closed')
        operations = capability.get('operations', [])
        if not operations:
            issue(cid, 'No operation inventory')
        operation_ids, complete = set(), bool(operations)
        for operation in operations:
            oid = operation.get('id')
            location = f'{cid}/{oid}'
            if not isinstance(oid, str) or oid in operation_ids:
                issue(location, 'Missing or duplicate operation identity')
            operation_ids.add(oid)
            if oid in all_operations:
                issue(location, 'Operation identity is not project-unique')
            all_operations.add(oid)
            for field in ('outcome', 'authority', 'contract', 'runtime', 'acceptance'):
                if not operation.get(field):
                    issue(location, f'Missing {field}')
            cells = operation.get('layers', {})
            if set(cells) != set(LAYERS):
                issue(location, 'Applicable layers must be explicitly inventoried')
            for layer in LAYERS:
                cell = cells.get(layer, {})
                state = cell.get('status')
                where = f'{location}/{layer}'
                if state not in STATES:
                    issue(where, 'Invalid cell status')
                if state == 'active' and capability.get('status') != 'active':
                    issue(where, 'Implementation is active outside the admitted capability')
                if state == 'not_applicable':
                    if not cell.get('reason'):
                        issue(where, 'Not applicable requires a semantic reason')
                elif state == 'proved':
                    evidence = cell.get('evidence', [])
                    if not evidence:
                        issue(where, 'Proved cell needs revision-bound evidence')
                    for entry in evidence:
                        if entry.get('result') != 'pass' or not entry.get('test_id'):
                            issue(where, 'Evidence must name a passing test')
                        inputs = entry.get('inputs', {})
                        if not inputs:
                            issue(where, 'Evidence has no source bindings')
                        for name, expected in inputs.items():
                            path = (root / name).resolve()
                            if (not path.is_relative_to(root) or not path.is_file()
                                    or sha256(path.read_bytes()).hexdigest() != expected):
                                issue(where, f'Missing or stale evidence input: {name}')
                        log = entry.get('receipt', {})
                        name = log.get('path', '')
                        path = (root / name).resolve()
                        if (not name or not path.is_relative_to(root) or not path.is_file()
                                or sha256(path.read_bytes()).hexdigest() != log.get('sha256')):
                            issue(where, 'Missing or altered execution receipt')
                else:
                    complete = False
        if capability.get('status') == 'proved' and not complete:
            issue(cid, 'Capability is marked proved with incomplete cells')
        if capability.get('status') == 'proved' and complete:
            closed.append(cid)
        else:
            all_complete = False
        previous_closed = previous_closed and capability.get('status') == 'proved' and complete
    if len(active) > 1:
        issue('capabilities', 'Only one capability may be active')
    if ledger.get('active_capability') != (active[0] if len(active) == 1 else None):
        issue('capabilities', 'Active capability pointer disagrees with ledger')
    inventory_complete = ledger.get('inventory_status') == 'reconciled'
    return {'status': 'fail' if findings else 'pass', 'active': active, 'closed': closed,
            'inventory_complete': inventory_complete,
            'workbench_complete': all_complete and inventory_complete and not findings,
            'findings': findings,
            'claim': 'ledger consistency and evidence freshness; not engineering acceptance'}
