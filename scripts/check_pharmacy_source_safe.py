#!/usr/bin/env python3
"""Check agreement within the released pharmacy derivatives, using no raw source.

This fixed-reference checker is not a SysML parser, original-source verifier,
image renderer, or acceptance gate. Model extraction supports only the small
declaration shape used by these three projections and rejects other bodies.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'examples/pharmacy-source-view-reference'
SCOPES = {'DemoCFP': (4, 4, 5), 'HSFillSystem': (7, 6, 8), 'HFFillSystem': (8, 7, 10)}
LICENSE_SHA256 = 'e84ddeddbd41569bb4e0cfb98a90cdcb3bc37eaac6482f7e04887ad895d4c850'
VIEW_FILES = {
    'SOURCE-LICENSE.md', 'candidate.drawio', 'candidate.png', 'candidate.svg',
    'engineering-reading.md', 'model.sysml', 'native.facts.json',
    'native.layout.puml', 'native.png', 'native.puml', 'native.svg',
    'semantic-ledger.json', 'supplementary-full-direct-properties.sysml',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def indexed(rows, key, label):
    result = {}
    for row in rows:
        require(key in row, f'{label}: missing {key}')
        require(row[key] not in result, f'{label}: duplicate {key}')
        result[row[key]] = row
    return result


def model_roles(text, view, package):
    """Read this fixture's quoted direct part declarations, not general SysML."""
    clean = re.sub(r'(?:\bdoc\s*)?/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    require(re.search(r'\bpackage\s+' + re.escape(package) + r'\s*\{', clean),
            f'{view}: model package')
    starts = list(re.finditer(r"part\s+def\s+'" + re.escape(view) + r"'\s*\{", clean))
    require(len(starts) == 1, f'{view}: selected model definition')
    start, depth = starts[0].end(), 1
    end = start
    while end < len(clean) and depth:
        depth += (clean[end] == '{') - (clean[end] == '}')
        end += 1
    require(depth == 0, f'{view}: unclosed model definition')
    body = clean[start:end - 1]
    pattern = re.compile(
        r"public\s+(?P<ref>ref\s+)?part\s+'(?P<name>[^']+)'\s*:\s*"
        + re.escape(package) + r"::'(?P<type>[^']+)'\s*"
        r"(?:\[(?P<lower>\d+)\.\.(?P<upper>\d+|\*)\])?\s*\{\s*\}")
    result = {}
    for match in pattern.finditer(body):
        name = match['name']
        require(name not in result, f'{view}: duplicate model role')
        result[name] = (match['type'], not bool(match['ref']),
                        match['lower'] or '1', match['upper'] or '1')
    require(not pattern.sub('', body).strip(), f'{view}: unsupported model body')
    return result


def role_tuple(row):
    return (row['type_name'], row['source_aggregation'] == 'composite',
            str(row['lower']), str(row['upper']))


def relationship_labels(labels, prop, composite, presentation, label):
    """Check this reference's explicit relationship and unnamed-alias wording."""
    contradiction = 'referenced resource' if composite else 'owned part'
    require(not any(contradiction in line.casefold() for line in labels),
            label + ': contradictory ' + presentation + ' relationship label')
    aliases = [line for line in labels if 'derived alias' in line.casefold()]
    if prop['source_name'] is None:
        prefix = ('Unnamed source role; derived alias: ' if presentation == 'SVG'
                  else 'Derived alias: ')
        require(aliases == [prefix + prop['derived_name']],
                label + ': ' + presentation + ' unnamed alias wording')
    else:
        require(not aliases, label + ': unexpected ' + presentation + ' alias')


def svg_rect(element, label):
    """Read one explicit, untransformed rectangle in the supported SVG subset."""
    rects = [e for e in element if e.tag == '{http://www.w3.org/2000/svg}rect']
    require(len(rects) == 1, label + ': expected one direct SVG rectangle')
    try:
        bounds = tuple(float(rects[0].attrib[key]) for key in ('x', 'y', 'width', 'height'))
    except (KeyError, ValueError):
        raise ValueError(label + ': unsupported SVG rectangle coordinates')
    require(all(math.isfinite(number) for number in bounds) and bounds[2] > 0 and bounds[3] > 0,
            label + ': invalid SVG rectangle bounds')
    return bounds


def check_svg_spatial(root, boundary, element, parents, composite, label):
    """Check explicit rectangle geometry only; other rendering remains untested.

    The fixed reference layout has a root-level boundary, owned cards directly
    inside it and reference cards in a root-level reference group. Transforms,
    nested viewports and CSS affecting these glyphs are unsupported, rather than
    silently interpreted as unchanged coordinates.
    """
    parent = parents.get(element)
    supported_parent = (parent is boundary if composite else
                        parent is not None and parent.tag == '{http://www.w3.org/2000/svg}g'
                        and parent.get('id') == 'shared-references' and parents.get(parent) is root)
    require(parents.get(boundary) is root and supported_parent,
            label + ': unsupported SVG containment ancestry')
    require(not any(e.tag.rsplit('}', 1)[-1] == 'style' for e in root.iter()),
            label + ': unsupported SVG geometry stylesheet')
    relevant = [root, boundary, parent, *boundary.iter(), *element.iter()]
    for node in relevant:
        require(not any(key.rsplit('}', 1)[-1] in {'transform', 'style'} for key in node.attrib),
                label + ': unsupported SVG transform or geometry style')
    bx, by, bw, bh = svg_rect(boundary, label + ' boundary')
    x, y, width, height = svg_rect(element, label + ' card')
    if composite:
        require(bx <= x and by <= y and x + width <= bx + bw and y + height <= by + bh,
                label + ': owned SVG card outside boundary')
    else:
        require(x + width <= bx or bx + bw <= x or y + height <= by or by + bh <= y,
                label + ': referenced SVG card overlaps owned boundary')


def check_view(view, ledger, facts, model, supplementary, svg, drawio, puml):
    selected_count, owned_count, full_count = SCOPES[view]
    require(ledger['view_id'] == view, f'{view}: ledger identity')
    rows = ledger['properties']
    expected = indexed(rows, 'derived_name', view + ' ledger')
    indexed(rows, 'source_id', view + ' source IDs')
    require(len(rows) == selected_count, f'{view}: selected scope count')
    require(sum(p['source_aggregation'] == 'composite' for p in rows) == owned_count,
            f'{view}: owned/reference counts')
    require(all(p['source_aggregation'] in {'composite', 'none'} for p in rows),
            f'{view}: unsupported aggregation')
    for row in rows:
        require(row['source_visibility'] == 'public', f'{view}: role visibility')
        bounds = (str(row['lower']), str(row['upper']))
        name = row['derived_name']
        bounded = ('0', '*') if view == 'HFFillSystem' and name in {
            'autoUofU', 'xSKU', 'manualFillSystem'} else (
            ('1', '*') if name in {'finger', 'roboticDispSystem'} else ('1', '1'))
        require(bounds == bounded, f'{view}/{name}: frozen cardinality')
        require((row['source_aggregation'] == 'none') ==
                (view != 'DemoCFP' and name == 'VTS'), f'{view}/{name}: frozen ownership')
    require(model_roles(model, view, 'PharmacySourceDiagramSlices') ==
            {name: role_tuple(row) for name, row in expected.items()},
            f'{view}: model/ledger roles differ')
    all_rows = rows + ledger['excluded_model_properties']
    full = indexed(all_rows, 'derived_name', view + ' supplementary ledger')
    require(len(full) == full_count, f'{view}: supplementary scope count')
    require(model_roles(supplementary.decode('utf-8'), view, 'PharmacyStructuralSlices') ==
            {name: role_tuple(row) for name, row in full.items()},
            f'{view}: supplementary/ledger roles differ')
    receipt = ledger['supplementary_projection_receipt']
    require(ledger['supplementary_complete_direct_property_projection'] ==
            'supplementary-full-direct-properties.sysml', f'{view}: supplementary filename')
    require(receipt['sha256'] == sha256(supplementary).hexdigest() and
            receipt['direct_property_count'] == full_count, f'{view}: supplementary hash/count')

    selected = facts['selected']
    qualified = 'PharmacySourceDiagramSlices::' + view
    require(selected.get('kind') == 'PartDefinition', f'{view}: native selected kind')
    require(facts['view'] == 'TREE' and selected['name'] == view and
            selected['qualified'] == qualified, f'{view}: native selection')
    require(facts['parse_has_errors'] is False and not facts['parse_issues'],
            f'{view}: historical native parse issues')
    native = indexed(facts['parts'], 'name', view + ' native facts')
    require(set(native) == set(expected), f'{view}: native role set')
    indexed(facts['parts'], 'id', view + ' native IDs')
    for name, row in native.items():
        prop = expected[name]
        require(row.get('kind') == 'PartUsage', f'{view}/{name}: native part kind')
        require(row['owner'] == qualified and row['owner_id'] == selected['id'] and
                row['qualified'] == prop['qualified'] == qualified + '::' + name,
                f'{view}/{name}: native owner/identity')
        require(row['visibility'] == prop['source_visibility'] and len(row['definitions']) == 1,
                f'{view}/{name}: native visibility/type')
        definition = row['definitions'][0]
        require(definition.get('kind') == 'PartDefinition', f'{view}/{name}: native definition kind')
        require((definition['name'], row['composite'], str(row['lower']), str(row['upper'])) ==
                role_tuple(prop), f'{view}/{name}: native type/ownership/cardinality')
        require(definition['qualified'] == 'PharmacySourceDiagramSlices::' + prop['type_name'],
                f'{view}/{name}: native type identity')

    root = ET.fromstring(svg)
    parents = {child: parent for parent in root.iter() for child in parent}
    boundary = [e for e in root.iter() if e.get('id') == 'system-boundary']
    require(len(boundary) == 1 and boundary[0].get('data-native-id') == selected['id'] and
            boundary[0].get('data-source-id') == ledger['source_root_id'], f'{view}: SVG boundary')
    cards = indexed([e.attrib for e in root.iter()
                     if e.tag.endswith('}g') and e.get('data-relationship')],
                    'data-source-id', view + ' SVG cards')
    require(set(cards) == {p['source_id'] for p in rows}, f'{view}: SVG role set')
    objects = ET.fromstring(drawio).findall('.//object')
    editable = indexed([e.attrib for e in objects], 'source_id', view + ' draw.io roles')
    require(set(editable) == set(cards), f'{view}: draw.io role set')
    native_aliases = indexed([
        {'id': match[1], 'alias': match[0]} for match in re.findall(
            r'^comp .*? as (E\d+) .*?\[\[psysml:([^ ]+) \]\]', puml, flags=re.M)
    ], 'id', view + ' native aliases')
    require(set(native_aliases) == {selected['id']} | {p['id'] for p in native.values()},
            f'{view}: native node identities')
    edges = re.findall(r'^(E\d+) ([*o]--) (E\d+) \[\[psysml:([^ ]+) \]\]', puml, flags=re.M)
    expected_edges = []
    for prop in rows:
        name, source_id = prop['derived_name'], prop['source_id']
        fact, card, edit = native[name], cards[source_id], editable[source_id]
        relation = 'composition' if fact['composite'] else 'reference'
        for key, value in {'data-native-id': fact['id'], 'data-owner-id': selected['id'],
                           'data-model-qualified': fact['qualified'],
                           'data-type-id': fact['definitions'][0]['id'],
                           'data-lower': str(fact['lower']), 'data-upper': str(fact['upper']),
                           'data-relationship': relation}.items():
            require(card.get(key) == value, f'{view}/{name}: SVG {key}')
        element = next(e for e in root.iter() if e.attrib is card)
        require((parents.get(element) is boundary[0]) == fact['composite'],
                f'{view}/{name}: SVG containment')
        check_svg_spatial(root, boundary[0], element, parents, fact['composite'],
                          f'{view}/{name}')
        labels = [''.join(e.itertext()) for e in element if e.tag.endswith('}text')]
        relationship_labels(labels, prop, fact['composite'], 'SVG', f'{view}/{name}')
        bounds = (str(prop['lower']), str(prop['upper']))
        count = bounds[0] if bounds[0] == bounds[1] else bounds[0] + ' or more'
        require('Count: ' + count in labels and 'Type: ' + prop['type_name'] in labels and
                ('Owned part' in labels if fact['composite'] and prop['source_name'] else True) and
                ('Referenced resource' in labels if not fact['composite'] else True),
                f'{view}/{name}: visible SVG role labels')
        require('Role: ' + (prop['source_name'] or '(unnamed source role)') in labels,
                f'{view}/{name}: visible SVG role identity')
        edit_labels = edit.get('label', '').splitlines()
        relationship_labels(edit_labels, prop, fact['composite'], 'draw.io', f'{view}/{name}')
        require('Count: ' + count in edit_labels and 'Type: ' + prop['type_name'] in edit_labels and
                'Role: ' + (prop['source_name'] or '(unnamed source role)') in edit_labels,
                f'{view}/{name}: visible draw.io labels')
        for key, value in {'native_id': fact['id'], 'model_qualified': fact['qualified'],
                           'relationship': relation, 'lower': str(fact['lower']),
                           'upper': str(fact['upper'])}.items():
            require(edit.get(key) == value, f'{view}/{name}: draw.io {key}')
        obj = next(e for e in objects if e.attrib is edit)
        cell = obj.find('mxCell')
        require(cell is not None and cell.get('parent') == ('system' if fact['composite'] else '1'),
                f'{view}/{name}: draw.io containment')
        glyph = '*--' if fact['composite'] else 'o--'
        expected_edges.append((native_aliases[selected['id']]['alias'], glyph,
                               native_aliases[fact['id']]['alias'], fact['membership_id']))
    require(sorted(edges) == sorted(expected_edges), f'{view}: retained native membership endpoints/glyphs')
    return {'view': view, 'selected_roles': selected_count, 'owned_parts': owned_count,
            'referenced_resources': selected_count - owned_count, 'supplementary_roles': full_count}


def check_file_names(names):
    expected = {'README.md'} | {view + '/' + name for view in SCOPES for name in VIEW_FILES}
    require(set(names) == expected, 'package file allowlist: missing or unexpected file')


def check_bundle(base=BASE):
    paths = [p for p in base.rglob('*') if p.is_file() or p.is_symlink()]
    require(not any(p.is_symlink() for p in paths), 'package symlink')
    check_file_names([p.relative_to(base).as_posix() for p in paths])
    checks = []
    for view in SCOPES:
        folder = base / view
        require(sha256((folder / 'SOURCE-LICENSE.md').read_bytes()).hexdigest() == LICENSE_SHA256,
                f'{view}: full pinned source license notice')
        checks.append(check_view(
            view, json.loads((folder / 'semantic-ledger.json').read_text()),
            json.loads((folder / 'native.facts.json').read_text()),
            (folder / 'model.sysml').read_text(),
            (folder / 'supplementary-full-direct-properties.sysml').read_bytes(),
            (folder / 'candidate.svg').read_text(), (folder / 'candidate.drawio').read_text(),
            (folder / 'native.puml').read_text()))
    return {'status': 'pass', 'checker_version': 'pharmacy-derivative-consistency/2',
            'checker_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'checked_inputs': {p.relative_to(base).as_posix(): sha256(p.read_bytes()).hexdigest()
                               for p in sorted(paths)},
            'claim_scope': 'released_derivative_consistency_only', 'views': checks,
            'original_source_verification': 'not_run', 'fresh_sysml_parse': 'not_run',
            'rendered_image_fidelity': 'not_run', 'engineering_acceptance': 'not_established'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    args = parser.parse_args()
    try:
        result = check_bundle(args.base)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(json.dumps({'status': 'fail', 'claim_scope': 'released_derivative_consistency_only',
                          'error': str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
