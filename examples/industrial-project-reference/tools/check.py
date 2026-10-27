#!/usr/bin/env python3
"""Check selected NIST derivative contracts, not original model truth or rendering."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
from reference_media import inspect_svg, inspect_png

CASES = ('wireless-robot-controller', 'nist-electronics-makecoupler')
VIEWS = ('endpoint-ledger', 'port-topology')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_case(case):
    if case == 'xppu-scenario15':
        raise ValueError('xppu-scenario15 is held pending GPL modification and corresponding-source review')
    require(case in CASES, 'Unsupported industrial reference case: ' + case)


def nums(text):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]


def validate_wireless_ledger(ledger, facts):
    require(ledger['nativeModel'].startswith('https://github.com/rcandell/wireless-factory-sysml/blob/' + ledger['pin'] + '/'), 'Wireless source locator must be public and pinned')
    require('derivative fact ledger' in ledger['recordKind'], 'Wireless ledger must declare derivative status')
    roles = ledger['roles']
    require(len(roles) == 7 and sum(r['aggregation'] == 'none' for r in roles) == 6, 'Wireless requires six references and one owned transceiver')
    transceiver = next(r for r in roles if r['name'] == 'xcvr')
    require((transceiver['aggregation'], transceiver['visibility'], transceiver['lower'], transceiver['upper']) == ('composite', 'private', '1', '*'), 'Wireless inherited xcvr ownership/visibility/bounds changed')
    require(len(ledger['ports']) == 4 and len(ledger['connectors']) == 7, 'Wireless selected port/connector count changed')
    require(all(c['direction'] == 'undirected' and len(c['ends']) == 2 for c in ledger['connectors']), 'Wireless connectors must remain binary and undirected')
    require(not any(e['path'] == 'DataPort' for c in ledger['connectors'] for e in c['ends']), 'Wireless DataPort must remain unconnected')
    require(Counter(f['kind'] for f in facts) == {'PortUsage': 4, 'PartUsage': 7, 'ConnectionUsage': 7}, 'Wireless recorded linked facts have unexpected selected scope')
    for role in roles:
        matches = [f for f in facts if f['kind'] == 'PartUsage' and f['name'] == role['name']]
        require(len(matches) == 1, 'Wireless repeated/missing native role: ' + role['name'])
        f = matches[0]
        require((f['composite'], f['visibility'], str(f['lower']), str(f['upper'])) == (role['aggregation'] == 'composite', role['visibility'], role['lower'], role['upper']), 'Wireless recorded native ownership/visibility/bounds disagree: ' + role['name'])
        # This derivative deliberately lifts the selected inherited features
        # into one explicit view type; it does not recreate source inheritance.
        package = 'WirelessRobotControllerSelected'
        owner_name = 'RobotControllerSelectedView'
        owner_qualified = package + '::' + owner_name
        owner = f.get('owner') or {}
        feature_name = role['name'] if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', role['name']) else "'" + role['name'] + "'"
        require((owner.get('kind'), owner.get('name'), owner.get('qualified')) == ('PartDefinition', owner_name, owner_qualified) and f['qualified'] == owner_qualified + '::' + feature_name, 'Wireless declared selected-view owner disagrees: ' + role['name'])
        types = [(t.get('kind'), t.get('name'), t.get('qualified')) for t in f.get('types', [])]
        require(types == [('PartDefinition', role['typeName'], package + '::' + role['typeName'])], 'Wireless declared part type disagrees: ' + role['name'])
    def endpoint(feature):
        ref = feature['ownedReferenceSubsetting']['referencedFeature']
        chain = ref.get('chainingFeature') or [ref]
        return '.'.join(f['name'] for f in chain)
    got = Counter(frozenset(endpoint(e) for e in f['endFeature']) for f in facts if f['kind'] == 'ConnectionUsage')
    expected = Counter(frozenset(e['path'] for e in c['ends']) for c in ledger['connectors'])
    require(got == expected, 'Wireless recorded native endpoints disagree with selected derivative ledger')


def validate_wireless_view(folder, view, ledger):
    mapping = json.loads((folder / (view + '-mapping.json')).read_text())
    svg = ET.parse(folder / (view + '.svg')).getroot()
    drawio = ET.parse(folder / (view + '.drawio')).getroot()
    elements = mapping['elements']
    expected_ids = [e['id'] for e in elements]
    visible = [e for e in svg.iter() if 'data-source-ids' in e.attrib]
    cells = [e for e in drawio.findall('.//mxCell') if e.get('id') not in ('0', '1')]
    require(len(expected_ids) == len(set(expected_ids)), view + ': duplicate mapping IDs')
    require(Counter(e.get('id') for e in visible) == Counter(expected_ids) == Counter(e.get('id') for e in cells), view + ': missing/extra/repeated presentation element')
    by_svg = {e.get('id'): e for e in visible}
    by_cell = {e.get('id'): e for e in cells}
    connectors = {c['id']: c for c in ledger['connectors']}
    roles = {r['id']: r for r in ledger['roles']}
    role_glyphs = []
    if view == 'port-topology':
        for element in svg.iter():
            css = element.get('style', '')
            if element.tag.endswith('style'):
                css += ''.join(element.itertext())
            require(not re.search(r'(?:^|[;{])\s*stroke-dasharray\s*:', css, re.I), view + ': unsupported CSS role-outline override')
            if element.tag.rsplit('}', 1)[-1] in ('svg', 'g'):
                require('stroke-dasharray' not in element.attrib, view + ': unsupported inherited role-outline override')
    drawn = []
    for item in elements:
        s, c, geometry = by_svg[item['id']], by_cell[item['id']], item['geometry']
        trace = ' '.join(item['sourceIds'])
        require(s.get('data-source-ids') == trace == c.get('sourceIds'), view + ': source trace mismatch')
        cg = c.find('mxGeometry')
        if 'points' in geometry:
            flat = [n for p in geometry['points'] for n in p]
            require(nums(s.get('points', '')) == flat, view + ': changed SVG route')
            source = cg.find("mxPoint[@as='sourcePoint']")
            target = cg.find("mxPoint[@as='targetPoint']")
            points = [[float(source.get('x')), float(source.get('y'))]]
            points += [[float(p.get('x')), float(p.get('y'))] for p in cg.findall("Array[@as='points']/mxPoint")]
            points += [[float(target.get('x')), float(target.get('y'))]]
            require(points == geometry['points'], view + ': changed editable route')
            require(not s.get('marker-start') and not s.get('marker-end') and 'startArrow=none;' in c.get('style', '') and 'endArrow=none;' in c.get('style', ''), view + ': invented connector direction')
            require(json.loads(c.get('endpointTrace')) == item['endpoints'], view + ': editable endpoint trace mismatch')
            if item['kind'] == 'connector':
                require(len(item['sourceIds']) == 1 and item['direction'] == 'undirected', view + ': connector trace/direction changed')
                source_id = item['sourceIds'][0]
                require(item['endpoints'] == connectors[source_id]['ends'], view + ': connector endpoint meaning changed')
                drawn.append(source_id)
        else:
            box = [geometry[k] for k in ('x', 'y', 'w', 'h')]
            require([float(cg.get(k)) for k in ('x', 'y', 'width', 'height')] == box, view + ': editable box changed')
            if item['kind'] == 'label':
                require(nums(s.get('data-box', '')) == box, view + ': label box changed')
                lines = [t.text or '' for t in s.iter() if t.tag.endswith('tspan')]
                require(lines == item['display'] and c.get('value') == '\n'.join(item['display']), view + ': visible/editable label changed')
            else:
                require([float(s.get(k)) for k in ('x', 'y', 'width', 'height')] == box, view + ': SVG box changed')
            if view == 'port-topology' and item['kind'] == 'entity':
                depicted_roles = [roles[source_id] for source_id in item['sourceIds'] if source_id in roles]
                if depicted_roles:
                    require(len(depicted_roles) == 1, view + ': ambiguous role glyph')
                    role = depicted_roles[0]
                    is_reference = role['aggregation'] == 'none'
                    dash = s.get('stroke-dasharray')
                    svg_style_ok = nums(dash or '') == [9, 5] if is_reference else dash in (None, 'none')
                    editable_dashes = [part.split('=', 1)[1] for part in c.get('style', '').split(';') if part.startswith('dashed=')]
                    require(svg_style_ok and editable_dashes == ['1' if is_reference else '0'], view + ': reference/owned role glyph style changed: ' + role['name'])
                    role_glyphs.append(role['id'])
    if view == 'port-topology':
        require(Counter(role_glyphs) == Counter(roles.keys()), view + ': all seven role glyphs must preserve ownership meaning')
    require(Counter(drawn) == Counter(connectors.keys()), view + ': complete seven-connector coverage required')
    media = inspect_svg(folder / (view + '.svg'), folder / 'font-source.json', folder / 'FONT-OFL-LICENSE.txt')
    png = inspect_png(folder / (view + '.png'))
    require(not png['metadata'], view + ': PNG contains unreviewed embedded metadata')
    return {'view': view, 'elements': len(elements), 'connectors': len(drawn), 'embedded_fonts': len(media['embedded_fonts'])}


def validate_coupler_ledger(ledger):
    require('derivative fact ledger' in ledger['recordKind'], 'MakeCoupler ledger must declare derivative status')
    nodes = ledger['nodes']
    calls = [n for n in nodes if n['kind'] == 'CallBehaviorAction']
    parameters = [n for n in nodes if n['kind'] == 'ActivityParameterNode']
    require(len(calls) == 17 and len(parameters) == 2 and len(ledger['parameters']) == 2, 'MakeCoupler selected call/parameter scope changed')
    require(len({n['id'] for n in calls}) == 17 and len(ledger['orderedCallIDs']) == 17 and len(set(ledger['orderedCallIDs'])) == 17, 'MakeCoupler repeated/missing call identity: require 17 distinct calls and unique ordering')
    require(Counter(n['id'] for n in calls) == Counter(ledger['orderedCallIDs']), 'MakeCoupler repeated/missing call identity')
    pins = [p for n in calls for p in n['pins']]
    require(Counter(p['kind'] for p in pins) == {'InputPin': 33, 'OutputPin': 25}, 'MakeCoupler selected pin scope changed')
    require(len({p['id'] for p in pins}) == 58, 'MakeCoupler repeated pin identity')
    require(all(p['multiplicity'] == ['1', '1'] for p in pins), 'MakeCoupler pin multiplicity changed')
    work_orders = [p for p in pins + ledger['parameters'] if p['name'] == 'workOrderIN']
    require(work_orders and all(p['type']['status'] == 'untyped' and p['type']['id'] is None and p['type']['name'] is None for p in work_orders), 'MakeCoupler untyped workOrderIN must stay unresolved')
    edges = ledger['edges']
    require(len(edges) == 16 and all(e['kind'] == 'ControlFlow' and not e['guardPresent'] for e in edges), 'MakeCoupler must retain only the 16 unguarded ControlFlow edges; no ObjectFlow')
    require(all(e['source'] != e['target'] for e in edges), 'MakeCoupler self-loop ControlFlow is outside the selected sequence')
    require(Counter((e['source'], e['target']) for e in edges) == Counter(zip(ledger['orderedCallIDs'], ledger['orderedCallIDs'][1:])), 'MakeCoupler sequence direction or distinct call ordering changed')
    return {'calls': 17, 'input_pins': 33, 'output_pins': 25, 'control_flows': 16, 'object_flows': 0, 'presentation': 'held'}


def validate(root=BASE):
    root = Path(root)
    release = json.loads((root / 'release.json').read_text())
    require(release['included_cases'] == list(CASES) and release['held_cases'] == ['xppu-scenario15'], 'Industrial scope must include both NIST cases and hold xPPU')
    require(not (root / 'xppu-scenario15').exists(), 'Held xPPU payload is not allowed in this release')
    wireless = root / CASES[0]
    coupler = root / CASES[1]
    require(not list(coupler.glob('activity-reading*')), 'Held MakeCoupler presentation cannot silently rejoin the release')
    for folder in (wireless, coupler):
        require((folder / 'NIST-LICENSE.md').is_file() and (folder / 'SOURCE-LICENSE.md').is_file(), 'Missing NIST derivative notices')
        require(not list(folder.glob('author-original*')), 'Original author graphic cannot rejoin the derivative release')
    for name, field in [('model.sysml', 'wireless_supplied_model_sha256'), ('native-linked-facts.json', 'wireless_recorded_linked_facts_sha256')]:
        require(hashlib.sha256((wireless / name).read_bytes()).hexdigest() == release[field], 'Wireless supplied model/facts binding changed: ' + name)
    ledger = json.loads((wireless / 'semantic-ledger.json').read_text())
    validate_wireless_ledger(ledger, json.loads((wireless / 'native-linked-facts.json').read_text()))
    views = [validate_wireless_view(wireless, view, ledger) for view in VIEWS]
    coupler_result = validate_coupler_ledger(json.loads((coupler / 'semantic-ledger.json').read_text()))
    manifest = json.loads((root / 'artifacts.json').read_text())
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and p != root / 'artifacts.json'}
    require(actual == set(manifest['sha256']), 'Incomplete or extra industrial artifact inventory')
    for name, digest in manifest['sha256'].items():
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, 'Changed industrial artifact: ' + name)
    return {'status': 'pass', 'included_cases': list(CASES), 'wireless_presentations': views, 'makecoupler': coupler_result, 'fresh_parser_run': 'not_run', 'fresh_browser_render': 'not_run', 'limits': 'Bounded supplied-derivative consistency only; no raw source qualification, source authenticity, execution, native editor or engineering acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='Require an included case; both retained NIST contracts are checked')
    args = parser.parse_args()
    try:
        if args.case:
            require_case(args.case)
        print(json.dumps(validate()))
    except (ValueError, KeyError, TypeError, StopIteration, OSError, ET.ParseError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
