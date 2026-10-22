#!/usr/bin/env python3
"""Build/check this synthetic gallery using the repository's existing engines."""
import argparse
import copy
from hashlib import sha256
from html import escape
import inspect
import re
import json
from pathlib import Path
import sys
import subprocess
import tempfile
from fractions import Fraction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from verifier import verify
from verifier.sysml import check_sysml
from verifier.visual_projection import write_presentation


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def put(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def inputs():
    paths = [p for p in sorted(HERE.iterdir()) if p.is_file()] + [HERE.parent / 'README.md', HERE.parent / 'index.html']
    return {str(p.relative_to(HERE)) if p.parent == HERE else '../' + p.name: digest(p) for p in paths}


def engines():
    # Changes require a rebuild, even if a previous gallery report passed.
    paths = sorted((ROOT / 'verifier').glob('*.py')) + [ROOT / 'tools/sysml/SysmlBridge.java', ROOT / 'scripts/verify.py'] + [p for p in sorted((ROOT / 'assets/diagram-style').rglob('*')) if p.is_file()]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def native(evidence=None, **kwargs):
    return check_sysml(str(HERE / 'station.sysml'), evidence=evidence, **kwargs)


def normalize(value):
    # Results remain portable between reviewed worktrees without changing source hashes.
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, str):
        return value.replace(str(HERE), 'examples/engineering-gallery/water-sampling')
    return value


def check_allocations(inventory, ledger):
    parts = {p['qualified_name']: p for p in inventory['parts']}
    documents = [d for d in inventory['documents'] if d.get('name') == 'cseViews']
    views = json.loads(documents[0]['body'].split('CSE-VIEWS/1.0', 1)[1])['views']
    functions = {n['id']: n['element'] for v in views if v['kind'] == 'function_tree' for n in v['nodes']}
    actions = {a['qualified_name'] for a in inventory['actions']}
    for name, typename in ledger['native_part_usages'].items():
        if name not in parts or parts[name].get('type') != 'WaterSampling::' + typename:
            raise ValueError('Native part usage/type mismatch: ' + name)
    for allocation in ledger['documentary_allocations']:
        if allocation['function'] not in functions or functions[allocation['function']] not in actions:
            raise ValueError('Documentary allocation references an unknown function: ' + allocation['function'])
        if allocation['performer'] not in parts:
            raise ValueError('Documentary allocation references an unknown performer: ' + allocation['performer'])


def evaluate():
    if 'manifest' not in inspect.signature(verify).parameters:
        raise ValueError('Gallery requires the finite manifest capability; integrate the reviewed capability increment first.')
    reports = {}
    profile = read('view-profile.json')
    for kind in ('concept', 'conops', 'scenario'):
        reports['shape-' + kind] = native(syntax_only=True, kind=kind, view_profile=profile)
    scope = read('scope.json')
    for name in ('pass', 'late', 'incomplete', 'no-receipt', 'over-limit'):
        reports['native-' + name] = native(evidence=read('evidence-' + name + '.json'), manifest=scope, review=True)
    over_limit = reports['native-over-limit']['results']
    for key, expected_status in [('R_ELAPSED__duration', 'fail'), ('R_RECORD__receipt', 'pass'), ('R_CORRELATION__correlation', 'pass')]:
        if over_limit[key]['check']['status'] != expected_status:
            raise ValueError('Over-limit fixture did not isolate the receipt-time quantity bound: ' + key)
    reports['influence'] = native(manifest=scope, generate_tests=True)
    inventory = reports['shape-concept']['inventory']
    kinds = {item['id']: group for group in ('concerns', 'requirements', 'use_cases') for item in inventory[group]}
    ledger = read('semantic-ledger.json')
    check_allocations(inventory, ledger)
    for field, wrong_value in [('performer', 'WaterSampling::missing'), ('function', 'NO_FUNCTION')]:
        bad_ledger = copy.deepcopy(ledger)
        bad_ledger['documentary_allocations'][0][field] = wrong_value
        try:
            check_allocations(inventory, bad_ledger)
        except ValueError as exc:
            reports['allocation-invalid-' + field] = {'status': 'fail', 'claim_scope': 'documentary_reference_and_kind_check_only', 'detail': str(exc)}
        else:
            raise ValueError('Invalid documentary allocation was accepted')
    for trace in ledger['typed_traces']:
        actual = (kinds.get(trace['from']), kinds.get(trace['to']))
        expected = {'justifies': ('requirements', 'concerns'), 'addresses': ('use_cases', 'requirements')}[trace['kind']]
        if actual != expected:
            raise ValueError('Invalid native documentary typed trace: ' + str(trace))
    finite = read('finite-scenarios.json')
    scope = read('finite-scope.json')
    reports['finite-pass'] = verify(finite, review=True, manifest=scope)
    reports['finite-focused'] = verify(finite, review=True, manifest=scope, selected=['FS_RECOVERY'])
    wrong = copy.deepcopy(scope)
    wrong['requirements'].append('FS_NOMINAL')
    reports['finite-wrong-kind-scope'] = verify(finite, review=True, manifest=wrong)
    duplicate = copy.deepcopy(scope)
    duplicate['requirements'].append('FR_HOLD')
    reports['finite-duplicate-scope'] = verify(finite, review=True, manifest=duplicate)
    with tempfile.TemporaryDirectory(prefix='gallery-null-', dir=ROOT / '.cache') as temporary:
        nullpath = Path(temporary) / 'null.json'
        nullpath.write_text('null')
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/verify.py'), str(HERE / 'finite-scenarios.json'), '--manifest', str(nullpath), '--review', '--json'], capture_output=True, text=True, check=False)
        if proc.returncode != 2 or 'Input error' not in proc.stderr:
            raise ValueError('CLI null manifest did not fail closed')
        reports['finite-null-scope'] = {'status': 'error', 'claim_scope': 'explicit_CLI_null_manifest_rejected', 'exit_code': proc.returncode}
    reports['finite-cap'] = verify(finite, review=True, manifest=scope, state_cap=1)
    missing = copy.deepcopy(finite)
    missing['scenarios']['FS_RECOVERY']['steps']['FX_CORRECT'].pop('produces')
    reports['finite-missing-data'] = verify(missing, review=True, manifest=scope)
    disabled = copy.deepcopy(finite)
    disabled['scenarios']['FS_NOMINAL']['steps']['FN_HANDOFF']['guard'] = {'all': [
        {'ref': 'labelReadable', 'op': '==', 'value': True},
        {'ref': 'labelReadable', 'op': '==', 'value': False}]}
    reports['finite-disabled-release'] = verify(disabled, review=True, manifest=scope)
    deleted = copy.deepcopy(finite)
    deleted['scenarios'].pop('FS_RECOVERY')
    deleted['traces'] = [t for t in deleted['traces'] if t['from'] != 'FS_RECOVERY']
    reports['finite-deleted-scenario'] = verify(deleted, review=True, manifest=scope)
    unclassified = copy.deepcopy(finite)
    unclassified['scenarios']['FS_EXTRA'] = copy.deepcopy(finite['scenarios']['FS_MAINTENANCE'])
    unclassified['scenarios']['FS_EXTRA']['steps'] = {'EX_' + k: v for k, v in unclassified['scenarios']['FS_EXTRA']['steps'].items()}
    unclassified['traces'].append({'from': 'FS_EXTRA', 'to': 'FR_PAUSE', 'kind': 'addresses'})
    reports['finite-unclassified-scenario'] = verify(unclassified, review=True, manifest=scope)
    mapping = read('finite-mapping.json')
    finite_kinds = {i: 'need' if s['category'] == 'need' else 'requirement' for i, s in finite['statements'].items()}
    finite_kinds.update({i: 'scenario' for i in finite['scenarios']})
    allowed = {'need-concern': ('need', 'concerns'), 'additional-formalization': ('requirement', 'use_cases'), 'scenario-use-case': ('scenario', 'use_cases')}
    for item in mapping['mappings']:
        if (finite_kinds.get(item['finite']), kinds.get(item['native'])) != allowed[item['kind']]:
            raise ValueError('Invalid separate-artifact mapping: ' + str(item))
    reports['trace-mapping'] = {'status': 'pass', 'claim_scope': 'typed_ID_alignment_only', 'native_documentary_traces': ledger['typed_traces'], 'separate_artifact_mapping': mapping}
    expected = {'allocation-invalid-performer': 'fail', 'allocation-invalid-function': 'fail', 'shape-concept': 'pass', 'shape-conops': 'pass', 'shape-scenario': 'pass', 'native-pass': 'pass', 'native-late': 'fail', 'native-incomplete': 'unknown', 'native-no-receipt': 'fail', 'native-over-limit': 'fail', 'finite-pass': 'pass', 'finite-focused': 'pass', 'finite-wrong-kind-scope': 'fail', 'finite-duplicate-scope': 'error', 'finite-null-scope': 'error', 'finite-cap': 'unknown', 'finite-missing-data': 'fail', 'finite-disabled-release': 'fail', 'finite-deleted-scenario': 'fail', 'finite-unclassified-scenario': 'fail', 'trace-mapping': 'pass'}
    for name, status in expected.items():
        if reports[name]['status'] != status:
            raise ValueError(f'{name}: expected {status}, got {reports[name]["status"]}')
    # Event influence generation is unsupported. Preserve this alongside sampled coverage.
    influence = reports['influence']['test_generation']
    if not influence.get('synthetic'):
        raise ValueError('Influence report lost its synthetic classification')
    return normalize(reports), inventory, expected


def sequence_svg(view):
    participants = view['participants']
    positions = {p['id']: 170 + i * 340 for i, p in enumerate(participants)}
    width, height = max(850, 340 * len(participants)), 180 + len(view['exchanges']) * 115
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">', f'<title id="title">{escape(view["id"])} documentary exchange sequence</title>', '<desc id="desc">List order and endpoints from parsed cseViews. No native behavior, timing or topology inferred.</desc>', '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="#23374b"/></marker></defs>', '<rect width="100%" height="100%" fill="#faf9f5"/>', '<g font-family="sans-serif" fill="#182b3b">', f'<text x="25" y="32" font-size="22">{escape(view["id"])} · Documentary exchange sequence</text>', '<text x="25" y="60" font-size="15">Synthetic model-derived presentation · no executable timing or native interaction claim</text>']
    for p in participants:
        x = positions[p['id']]
        parts += [f'<rect x="{x-105}" y="85" width="210" height="50" rx="4" fill="#e4edf2" stroke="#23374b"/>', f'<text x="{x}" y="116" text-anchor="middle" font-size="18">{escape(p["id"])}</text>', f'<path d="M{x} 135V{height-30}" stroke="#758391" stroke-dasharray="5 6"/>']
    for i, ex in enumerate(view['exchanges']):
        y = 210 + i * 115
        x1, x2 = positions[ex['from']], positions[ex['to']]
        parts += [f'<text x="25" y="{y-47}" font-size="14">{escape(ex["id"])}</text>', f'<text x="{min(x1,x2)+12}" y="{y-20}" font-size="17">{escape(ex["message"])}</text>', f'<path d="M{x1} {y}H{x2}" stroke="#23374b" stroke-width="2" marker-end="url(#arrow)"/>']
    return '\n'.join(parts + ['</g></svg>'])


def build(output):
    if output.exists():
        raise ValueError('Output must be a fresh directory')
    reports, inventory, expected = evaluate()
    output.mkdir(parents=True)
    for name, report in reports.items():
        put(output / (name + '.json'), report)
    result = write_presentation([str(HERE / 'station.sysml')], output / 'function-tree', view_id='FT_STATION', target_width=2400, show_ids=True)
    if result['status'] != 'pass':
        raise ValueError('Function-tree presentation failed')
    documents = [d for d in inventory['documents'] if d.get('name') == 'cseViews']
    viewdata = json.loads(documents[0]['body'].split('CSE-VIEWS/1.0', 1)[1])
    tree = next(v for v in viewdata['views'] if v['kind'] == 'function_tree')
    selected = [n for n in tree['nodes'] if n['level'] <= 1]
    omitted = [n['id'] for n in tree['nodes'] if n['level'] > 1]
    labels = {'F0': ['Manage sample handoff'], 'F1': ['Receive sample'], 'F2': ['Preserve handoff', 'record'], 'F3': ['Release sample'], 'F4': ['Maintain station']}
    # Scoped view: retain only explicit root-to-level-1 parent edges, never crop.
    overview = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-labelledby="t d"><title id="t">Synthetic remote sample station: scoped function overview</title><desc id="d">Root and four first-level functions. Eight level-2 details omitted; full model-linked tree available in the gallery. No execution order implied.</desc><rect width="1200" height="420" fill="#faf9f5"/><g font-family="sans-serif" fill="#182b3b"><text x="30" y="44" font-size="28">Synthetic remote sample station</text><text x="30" y="78" font-size="24">Scoped function overview · root + level 1 · 8 detailed functions omitted</text>']
    for x in [150, 450, 750, 1050]:
        overview.append(f'<path d="M600 184V214H{x}V244" fill="none" stroke="#576d7d" stroke-width="2"/>')
    for node in selected:
        x, y = (420, 115) if node['level'] == 0 else (list(labels).index(node['id']) * 300 - 285, 244)
        w = 360 if node['level'] == 0 else 270
        overview.append(f'<rect x="{x}" y="{y}" width="{w}" height="92" rx="5" fill="#e4edf2" stroke="#23374b"/>')
        for j, text in enumerate(labels[node['id']]):
            overview.append(f'<text x="{x+16}" y="{y+33+j*28}" font-size="24">{escape(text)}</text>')
        overview.append(f'<text x="{x+16}" y="{y+80}" font-size="18">{node["id"]} · level {node["level"]}</text>')
    overview.append('<text x="30" y="385" font-size="24">Documentary decomposition only · no execution order or acceptance claim</text></g></svg>')
    (output / 'overview.svg').write_text(''.join(overview))
    put(output / 'overview-ledger.json', {'source_model_sha256': reports['shape-concept']['model_sha256'], 'view': tree['id'], 'included': selected, 'display_labels': [{'id': n['id'], 'native_element': n['element'], 'lines': labels[n['id']]} for n in selected], 'omitted_ids': omitted, 'edges': [{'from': n['parent'], 'to': n['id']} for n in selected if n['parent']], 'claim': 'scoped documentary decomposition; source parent edges only'})
    sequence_ids = []
    for view in viewdata['views']:
        if view['kind'] == 'sequence':
            sequence_ids.append(view['id'])
            (output / (view['id'] + '.svg')).write_text(sequence_svg(view))
    # Derive display arithmetic from the already parsed cseType and monitor result.
    quantity_attribute = next(a for a in inventory['attributes'] if a['qualified_name'] == 'WaterSampling::Station::processingElapsed')
    quantity_doc = next(d for d in inventory['documents'] if d.get('name') == 'cseType' and d['owner'] == quantity_attribute['qualified_name'])
    match = re.fullmatch(r'CSE-INT/2\.0\s+range (-?\d+) (-?\d+) scale ([0-9.]+) unit (\w+)\s*', quantity_doc['body'])
    if not match:
        raise ValueError('Unexpected parsed quantity annotation')
    minimum, maximum, scale, unit = match.groups()
    observed_ticks = read('evidence-pass.json')['observations'][3]['WaterSampling::station::processingElapsed']
    quantity_clause = reports['native-pass']['results']['R_ELAPSED__duration']['compiled_clause']
    monitor = reports['native-pass']['results']['R_RECORD__receipt']['check']
    deadline_ticks = monitor['results']['R_RECORD__receipt']['deadline_ticks']
    deadline_ms = deadline_ticks * Fraction(monitor['clock_period_ms'])
    put(output / 'quantity-reading.json', {'claim_scope': 'exact_display_arithmetic_only', 'source_attribute': quantity_attribute['qualified_name'], 'source_type': quantity_attribute['type'], 'domain_ticks': [int(minimum), int(maximum)], 'scale': scale, 'unit': unit, 'observed_example_ticks': observed_ticks, 'observed_example_quantity': str(observed_ticks * Fraction(scale)), 'quantity_compiled_clause': quantity_clause, 'response_requirement': 'R_RECORD__receipt', 'response_deadline_ticks': deadline_ticks, 'clock_period_ms': monitor['clock_period_ms'], 'response_deadline_ms': str(deadline_ms), 'limits': 'Display calculation from parsed type annotation, supplied synthetic ticks, actual compiled receipt-time quantity condition and R_RECORD response deadline; no physical model or new requirement evaluator.'})
    rows = ''.join(f'<tr><td><a href="{name}.json">{name}</a></td><td>{escape(report["status"])}</td><td>{escape(str(report.get("claim_scope", "finite declared model")))}</td></tr>' for name, report in reports.items())
    body = '<h1>Remote sample station</h1><p class="lede">A wholly synthetic engineering case, from operational intent to bounded checks.</p><p>All thresholds, policies, allocations and components are fictional demonstration choices. This is sample logistics, with no water-treatment, analytical-validity or public-health suitability claim.</p><nav><a href="../station.sysml">Shared SysML source</a> · <a href="../finite-scenarios.json">Separate finite model</a> · <a href="../semantic-ledger.json">Semantic ledger</a> · <a href="../README.md">Reading and reproduction guide</a></nav><h2>Read the operation</h2><p>The operator presents a labeled container. The station records its identity and returns a receipt. The courier reconciles the pickup manifest and obtains a custody record. An unreadable label instead causes a hold; corrected identity precedes a new receipt. A custodian suspends intake for inspection; release back to operation remains a separate decision.</p><h2>Functions, not execution order</h2><p>One root, four branches and two subordinate functions per branch. Parentage and allocation are documentary; components and functions retain distinct types. Open the full-width view and scroll rather than shrink labels.</p><a href="function-tree/index.html">Open editable model-derived function tree</a><div class="diagram"><img src="function-tree/view.svg" alt="Function decomposition: receive sample, preserve handoff record, release sample, maintain station"></div><h2>Ordered exchanges</h2><p>These simplified documentary presentations use parsed participants and ordered exchanges. They are neither native SysML interaction diagrams nor executable activities. No ports, connector topology, timing, containment or ownership follows from these lines.</p>'
    for sid in sequence_ids:
        body += f'<div class="diagram"><img src="{sid}.svg" alt="{sid}: ordered documentary participant exchanges"></div>'
    body += '<h2>What was checked</h2><p>Native sampled traces and correlated events remain separate from the separately authored finite guard/effect/data model. Typed mappings check referenced kinds and IDs, never semantic equivalence. The finite consistency check is pointwise satisfiability; progress means a completion path exists from each reachable state, not inevitable completion. Generated influence pairs are synthetic, not observations or FLIP coverage. Event influence generation is unsupported.</p><table><thead><tr><th>Report</th><th>Result</th><th>Claim scope</th></tr></thead><tbody>'+rows+'</tbody></table><p>Pass means only the named local computation completed within its declared limits. Required-review manifests bind fictional inventories; they do not authenticate approval. No protected execution, native editor roundtrip, physical feasibility or stakeholder acceptance is claimed.</p>'
    (output / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Synthetic remote sample station</title><style>body{font:18px/1.6 system-ui,sans-serif;color:#182b3b;background:#faf9f5;margin:0 auto;padding:48px 24px;max-width:1100px}h1{font-size:48px;line-height:1.1}h2{margin-top:48px}a{color:#155d87}nav{padding:20px;background:#e4edf2}.lede{font-size:25px}.diagram{overflow:auto;border:1px solid #a5b2bd;margin:28px 0;background:white}.diagram img{max-width:none;display:block}table{border-collapse:collapse;width:100%;font-size:15px;table-layout:fixed}td{overflow-wrap:anywhere}th,td{text-align:left;padding:10px;border-bottom:1px solid #a5b2bd}tr:nth-child(even){background:#eef1f1}:focus-visible{outline:3px solid #ad4b19;outline-offset:4px}</style><main>'+body+'</main></html>\n')
    files = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    put(output / 'build-manifest.json', {'version': 1, 'claim': 'local synthetic artifact freshness and expected outcomes; not authenticated acceptance', 'inputs': inputs(), 'engines': engines(), 'expected_status': expected, 'files': files})


def check():
    output = HERE / 'generated'
    manifest = json.loads((output / 'build-manifest.json').read_text())
    if manifest['inputs'] != inputs() or manifest['engines'] != engines():
        raise ValueError('Source or engine changed: rebuild gallery in a fresh directory and review the new outputs')
    actual = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'build-manifest.json'}
    if (output / 'preview-receipt.json').exists():
        receipt = json.loads((output / 'preview-receipt.json').read_text())
        if receipt['svg_sha256'] != digest(output / 'overview.svg') or receipt['png_sha256'] != digest(output / 'overview.png'):
            raise ValueError('Rendered preview is stale')
    if actual != manifest['files']:
        raise ValueError('Generated gallery output drift, deletion or addition')
    # Rebuild deterministic textual/vector artifacts, catching stale geometry too.
    with tempfile.TemporaryDirectory(prefix='gallery-rebuild-', dir=ROOT / '.cache') as temporary:
        fresh = Path(temporary) / 'gallery'
        build(fresh)
        optional = {'overview.png', 'preview-receipt.json', 'build-manifest.json'}
        rebuilt = {str(p.relative_to(fresh)): digest(p) for p in sorted(fresh.rglob('*')) if p.is_file() and p.name not in optional}
        stored = {k: v for k, v in actual.items() if k not in optional}
        if rebuilt != stored:
            raise ValueError('Rebuilt report, HTML, SVG or source-map drift')
        if json.loads((fresh / 'build-manifest.json').read_text())['expected_status'] != manifest['expected_status']:
            raise ValueError('Expected outcome inventory drift')
    print('PASS synthetic gallery freshness, typed mapping and expected positive/negative outcomes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path, help='fresh output directory, normally on /workspace')
    group.add_argument('--check', action='store_true', help='check tracked generated output and rerun computations')
    args = parser.parse_args()
    try:
        check() if args.check else build(args.output)
    except (OSError, ValueError, KeyError) as exc:
        print('Gallery error: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
