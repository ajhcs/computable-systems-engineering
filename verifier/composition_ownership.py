"""Source-bound ownership candidates for the physical-composition workbench.

Source locators are revision-bound parser metadata. They are not engineering IDs.
The public operation must also validate every affected presentation before save.
"""
from copy import deepcopy
from bisect import bisect_left
from hashlib import sha256
import json
import subprocess

from .composition_edit import (EditError, bounds, codepoint_index, elements,
                               fingerprint, renamed_native_facts)
from .sysml import _parser_output
from .composition_records import rebind_document, rebind_json, strict_json


def _namespaces(document):
    rows = document.parsed.get('source_span', {}).get('namespace_sources')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16384:
        raise EditError('parser_contract', 'Native namespace source inventory unavailable or over limit')
    if len({row.get('native_fragment') for row in rows}) != len(rows):
        raise EditError('parser_contract', 'Native namespace source locators are ambiguous')
    return rows


def _owner(document, target):
    if (not isinstance(target, dict) or set(target) != {'kind', 'identity', 'file', 'bundle_sha256'}
            or target['kind'] not in ('PartDefinition', 'PartUsage', 'Package', 'Namespace')
            or not isinstance(target['identity'], str) or target['file'] not in document.files):
        raise EditError('owner', 'Choose an existing native owner and explicit project source file')
    if target['bundle_sha256'] != document.revision:
        raise EditError('stale_revision', 'Destination source locator belongs to another captured bundle; inspect and select it again')
    if target['kind'] in ('PartDefinition', 'PartUsage'):
        name = document.registry.get(target['identity'])
        row = elements(document.parsed).get(name)
        if row is None or ('PartDefinition' if row['kind'] == 'part_definitions' else 'PartUsage') != target['kind']:
            raise EditError('owner', 'Destination engineering UUID does not identify the selected native owner kind')
        result = {**row, 'kind': target['kind']}
    else:
        rows = [row for row in _namespaces(document)
                if row.get('native_fragment') == target['identity'] and row.get('kind') == target['kind']]
        if len(rows) != 1 or (target['kind'] == 'Namespace') != (rows[0].get('is_root') is True):
            raise EditError('owner', 'Destination native namespace locator does not match this captured source')
        result = deepcopy(rows[0])
    if target['kind'] != 'Namespace':
        start, end = bounds(document.source, result['source_span'])
        if document.file_range(start, end)[2] != target['file']:
            raise EditError('source_span', 'Native owner body belongs to another source file')
    return result


def destinations(document):
    """Inspectable destinations; the candidate rechecks their exact locators."""
    rows = []
    for identity, name in document.registry.items():
        native = elements(document.parsed)[name]
        start, end = bounds(document.source, native['source_span'])
        rows.append({'target': {'kind': 'PartDefinition' if native['kind'] == 'part_definitions' else 'PartUsage',
                                'identity': identity, 'file': document.file_range(start, end)[2], 'bundle_sha256': document.revision},
                     'native_name': name, 'bundle_sha256': document.revision})
    for native in _namespaces(document):
        files = list(document.files) if native.get('is_root') else [document.file_range(*bounds(document.source, native['source_span']))[2]]
        for file in files:
            rows.append({'target': {'kind': native['kind'], 'identity': native['native_fragment'], 'file': file, 'bundle_sha256': document.revision},
                         'native_name': native.get('qualified_name'), 'bundle_sha256': document.revision})
    return rows


def _ordered_edits(changes):
    values = sorted(set(changes))
    for start, end, text in values:
        if type(start) is not int or type(end) is not int or start < 0 or start > end or not isinstance(text, str):
            raise EditError('source_span', 'Invalid ownership edit span')
    if any(a[1] > b[0] or a[0] == b[0] for a, b in zip(values, values[1:])):
        raise EditError('overlapping_edits', 'Ownership source edits overlap or share an insertion anchor')
    return values


def _rewrite(text, changes):
    result = text
    for start, end, value in reversed(_ordered_edits(changes)):
        if end > len(text):
            raise EditError('source_span', 'Ownership edit exceeds source')
        result = result[:start] + value + result[end:]
    return result


def _position(offset, edits):
    shift = 0
    for start, end, replacement in edits:
        if offset < start:
            break
        if start < offset < end:
            raise EditError('source_span', 'Reference boundary falls inside another rewritten token')
        if offset == start:
            return offset + shift
        shift += len(replacement) - (end - start)
    return offset + shift


def _canonical_facts(parsed):
    facts = fingerprint(parsed)
    # Only extracted top-level inventories lose traversal order on relocation.
    # Semantic lists within each native row remain ordered and exact.
    for key, rows in facts.items():
        if isinstance(rows, list):
            facts[key] = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))
    return facts


def _namespace_facts(document, mapped=lambda value: value):
    keys = ('kind', 'is_root', 'qualified_name', 'owner', 'owner_kind')
    rows = [{key: mapped(row.get(key)) if key in ('qualified_name', 'owner') else row.get(key)
             for key in keys} for row in _namespaces(document)]
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))


def _move_source(document, element_id, destination, composition_transition, *, expected_source_sha256):
    """Internal native step. Its intermediate view parents are not publishable."""
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Source changed before ownership candidate preparation')
    if not isinstance(element_id, str) or element_id not in document.registry:
        raise EditError('identity', 'Unknown captured engineering declaration')
    inventory = elements(document.parsed)
    old = document.registry[element_id]
    item, owner = inventory[old], _owner(document, destination)
    if item.get('owner') == owner.get('qualified_name') and item.get('owner_kind') == owner['kind']:
        raise EditError('same_owner', 'The selected declaration already has this native owner; file relocation is a separate operation')
    start, end = bounds(document.source, item['source_span'])
    document.file_range(start, end)
    if owner['kind'] != 'Namespace':
        owner_start, owner_end = bounds(document.source, owner['source_span'])
        if start <= owner_start < end or owner.get('qualified_name') == old or str(owner.get('qualified_name', '')).startswith(old+'::'):
            raise EditError('ownership_cycle', 'A declaration cannot own itself or its native ancestor')
    members = owner['source_span'].get('member_names') if owner['kind'] in ('PartDefinition', 'PartUsage') else owner.get('member_names')
    if not isinstance(members, list) or any(not isinstance(value, str) for value in members):
        raise EditError('parser_contract', 'Native destination membership names unavailable')
    if item.get('name') in members or item.get('id') is not None and item['id'] in members:
        raise EditError('name_collision', 'A destination member or alias already uses this name or short ID')
    local, token = item['source_span'].get('local_identity'), item['source_span'].get('local_reference')
    if (not isinstance(local, str) or not local or not isinstance(token, str) or not token
            or old != (item['owner']+'::' if item.get('owner') else '')+local):
        raise EditError('parser_contract', 'Native existing local identity/source spelling unavailable or inconsistent')
    # Relocation preserves an existing name. The separate new-name authoring
    # length limit must not reject an otherwise admitted imported declaration.
    new = (owner['qualified_name']+'::' if owner.get('qualified_name') else '') + local
    new_reference = (owner['source_span']['qualified_reference']+'::' if owner.get('qualified_name') else '') + token
    old_reference = item['source_span'].get('qualified_reference')
    if not isinstance(old_reference, str) or not old_reference:
        raise EditError('parser_contract', 'Native declaration qualified spelling unavailable')

    def mapped(value):
        if isinstance(value, str):
            return new+value[len(old):] if value == old or value.startswith(old+'::') else value
        if isinstance(value, list):
            return [mapped(row) for row in value]
        return value

    registry = {identity: mapped(name) for identity, name in document.registry.items()}
    if len(set(registry.values())) != len(registry):
        raise EditError('name_collision', 'Moved subtree collides with existing native identities')
    transition = None
    expected_composite = None
    if item['kind'] == 'parts':
        authored = item['source_span'].get('authored_reference')
        if type(authored) is not bool:
            raise EditError('parser_contract', 'Native authored reference-part form unavailable')
        expected_composite = not authored and owner['kind'] in ('PartDefinition', 'PartUsage')
        if expected_composite != item.get('is_composite'):
            transition = {'before': item.get('is_composite'), 'after': expected_composite}
    if composition_transition != transition or transition is not None and (
            not isinstance(composition_transition, dict) or set(composition_transition) != {'before', 'after'}
            or any(type(value) is not bool for value in composition_transition.values())):
        raise EditError('composition_transition', 'Acknowledge the exact observed native composition transition for this captured owner change: '+json.dumps(transition))

    changes, rewrites, repairs, dependencies, reference_aliases = [], {}, {}, {}, {}
    references = document.parsed.get('reference_spans')
    if not isinstance(references, list) or len(references) > 16384:
        raise EditError('parser_contract', 'Native reference inventory unavailable or over limit')
    intervals = sorted((*bounds(document.source, ref), index) for index, ref in enumerate(references))
    interval_starts = [row[0] for row in intervals]
    for index, ref in enumerate(references):
        if ref.get('resolved') is not True or not isinstance(ref.get('target'), str):
            raise EditError('unresolved_reference', 'Ownership editing needs resolved native source references')
        a, b = bounds(document.source, ref)
        # INode.getText() includes leading hidden trivia that getOffset/Length
        # excludes. Validate the actual native token spans instead of treating
        # that diagnostic string as a source-coordinate assertion.
        tokens = ref.get('source_tokens')
        if not isinstance(tokens, list) or not 1 <= len(tokens) <= 1024:
            raise EditError('parser_contract', 'Native reference source tokens unavailable')
        previous = a
        for token in tokens:
            left, right = bounds(document.source, token)
            if not previous <= left < right <= b or document.source[left:right] != token.get('text'):
                raise EditError('source_span', 'Native reference tokens disagree or overlap')
            previous = right
        if bounds(document.source, tokens[0])[0] != a or previous != b:
            raise EditError('source_span', 'Native reference boundary disagrees with its tokens')
        binding = ref.get('name_binding', {})
        aliases = [segment for segment in binding.get('segments', [])
                   if segment.get('kind') in ('alias_name', 'alias_short_name')]
        reference_aliases[index] = aliases
        dependency_spans = []
        for segment in aliases:
            if segment.get('alias_is_external') is True:
                continue  # Library declarations are not moved/edited here.
            alias_span = segment.get('alias_source_span')
            if not isinstance(alias_span, dict):
                dependency_spans = None
                break
            dependency_spans.append(bounds(document.source, alias_span))
        dependencies[index] = ({intervals[position][2] for left, right in dependency_spans
                               for position in range(bisect_left(interval_starts, left), bisect_left(interval_starts, right))
                               if intervals[position][1] <= right}
                              if dependency_spans is not None else None)
        if binding.get('status') != 'resolved':
            continue  # An unchanged unsupported spelling needs no rewrite.
        replacement = ref.get('target_reference')
        if not isinstance(replacement, str) or not replacement:
            raise EditError('parser_contract', 'Native target qualified source spelling unavailable')
        if aliases:
            # Qualifying the terminal declaration would discard an authored
            # alias dependency. Requalify the original alias where supported.
            if len(aliases) != 1 or aliases[0] is not binding['segments'][-1]:
                continue
            alias = aliases[0]
            alias_owner = alias.get('alias_owner_reference')
            alias_local = alias.get('alias_local_reference')
            if not alias_owner or not alias_local:
                continue
            if mapped(alias.get('alias_owner')) != alias.get('alias_owner'):
                if alias_owner != old_reference and not alias_owner.startswith(old_reference+'::'):
                    raise EditError('parser_contract', 'Native alias owner spelling disagrees with its identity')
                alias_owner = new_reference + alias_owner[len(old_reference):]
            replacement = alias_owner+'::'+alias_local
        elif mapped(ref['target']) != ref['target']:
            if replacement != old_reference and not replacement.startswith(old_reference+'::'):
                raise EditError('parser_contract', 'Native target identity and qualified spelling disagree')
            replacement = new_reference + replacement[len(old_reference):]
        if ''.join(token['text'] for token in tokens) != replacement:
            repairs[index] = {'changes': [(*bounds(document.source, token), replacement if token_index == 0 else '')
                                         for token_index, token in enumerate(tokens)],
                              'rewritten': (bounds(document.source, tokens[0])[0], len(replacement))}

    expected_bodies = []
    for record in document.parsed.get('documents', []):
        try:
            body, findings = rebind_document(record['body'], record.get('name'), mapped)
            expected_bodies.append(body)
            if body != record['body']:
                left, right = bounds(document.source, record['source_span'], 'body_')
                token = document.source[left:right]
                if not token.startswith('/*') or not token.endswith('*/'):
                    raise EditError('source_span', 'Unsupported native documentation token')
                raw, raw_findings = rebind_document(token[2:-2], record.get('name'), mapped)
                if raw_findings != findings or strict_json(raw.lstrip().split('\n', 1)[1]) != strict_json(body.lstrip().split('\n', 1)[1]):
                    raise EditError('source_span', 'Native document/source mapping disagrees')
                changes.append((left+2, right-2, raw))
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            if isinstance(exc, EditError):
                raise
            raise EditError('linked_records', str(exc)) from exc
    linked, reconciliation = deepcopy(document.linked_records), []
    for name, record in linked.items():
        try:
            rewritten, findings = rebind_json(record['text'], record['kind'], mapped)
            if findings and record['kind'] == 'retained_configuration':
                reconciliation.append({'file': name, 'status': 'reconciliation_required',
                                       'retained_sha256': sha256(record['text'].encode()).hexdigest(), 'changes': findings})
            record['text'] = rewritten
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            raise EditError('linked_records', str(exc)) from exc

    file = destination['file']
    newline = '\r\n' if '\r\n' in document.files[file] else '\n'
    if owner['kind'] == 'Namespace':
        file_start, file_end, _ = next(row for row in document.ranges if row[2] == file)
        at, until, prefix, suffix = file_end, file_end, newline, newline
    else:
        at, until = bounds(document.source, owner['source_span'], 'namespace_end_')
        terminal = document.source[at:until]
        if not owner_start <= at < until <= owner_end or terminal != owner['source_span'].get('namespace_end_text') or terminal not in (';', '}'):
            raise EditError('source_span', 'Native owner terminal keyword disagrees with its body')
        if terminal == ';':
            prefix, suffix = ' {'+newline, newline+'}'
        else:
            until, prefix, suffix = at, newline, newline

    def assemble():
        internal = _ordered_edits([(a-start, b-start, value) for a, b, value in changes if start <= a <= b <= end])
        external = [(a, b, value) for a, b, value in changes if not start <= a <= b <= end]
        if any(a < end and b > start for a, b, _ in external):
            raise EditError('overlapping_edits', 'A changed native record crosses the moved declaration')
        fragment = _rewrite(document.source[start:end], internal)
        top = _ordered_edits(external+[(start, end, ''), (at, until, prefix+fragment+suffix)])
        files = document.candidate_files(top)
        # Match the existing document's normalized parse-unit coordinates. The
        # final document still independently reparses and validates every file.
        chunks, new_ranges, cursor = [], {}, 0
        for name, text in sorted(files.items()):
            new_ranges[name] = cursor
            chunk = text if text.endswith('\n') else text+'\n'
            chunks.append(chunk)
            cursor += len(chunk)+1
        source = '\n'.join(chunks) if document.is_bundle else files['model.sysml']
        if len(source.encode('utf-8')) > 5_000_000:
            raise EditError('input', 'Ownership candidate parse unit exceeds 5 MB')
        local_edits = {name: [] for name in document.files}
        for left, right, value in top:
            file_a, _, name = document.file_range(left, right)
            local_edits[name].append((left-file_a, right-file_a, value))
        destination_a = next(a for a, _, name in document.ranges if name == file)
        fragment_at = new_ranges[file] + _position(at-destination_a, local_edits[file]) + len(prefix)

        def alias_anchor(position):
            if start <= position < end:
                return fragment_at + _position(position-start, internal)
            file_a, _, name = document.file_range(position, position)
            return new_ranges[name] + _position(position-file_a, local_edits[name])

        expected_refs, by_index = {}, {}
        for index, ref in enumerate(references):
            left, right = bounds(document.source, ref)
            rewritten = rewrites.get(index)
            if start <= left < right <= end:
                left_after = fragment_at + _position((rewritten[0] if rewritten else left)-start, internal)
                right_after = left_after+rewritten[1] if rewritten else fragment_at+_position(right-start, internal)
            else:
                file_a, _, name = document.file_range(left, right)
                edits = local_edits[name]
                left_after = new_ranges[name]+_position((rewritten[0] if rewritten else left)-file_a, edits)
                right_after = left_after+rewritten[1] if rewritten else new_ranges[name]+_position(right-file_a, edits)
            key = (left_after, right_after)
            if key in expected_refs:
                raise EditError('reference_delta', 'Moved native reference spans are ambiguous')
            expected_refs[key] = (ref.get('feature'), mapped(ref['target']),
                                  alias_facts(document.source, reference_aliases[index], alias_anchor, mapped))
            by_index[index] = key
        return files, source, expected_refs, by_index

    def alias_facts(source, aliases, anchor=lambda offset: offset, owner_mapping=lambda value: value):
        result = []
        for alias in aliases:
            external = alias.get('alias_is_external') is True
            span = alias.get('alias_source_span')
            if not external and not isinstance(span, dict):
                raise EditError('reference_form', 'A local alias lacks a native declaration source anchor')
            start = None if external else anchor(bounds(source, span)[0])
            owner = owner_mapping(alias.get('alias_owner'))
            if external and not owner:
                raise EditError('reference_form', 'A library alias lacks its native owning namespace')
            result.append((external, start, owner, alias.get('name'), alias['kind']))
        return tuple(result)

    def reference_facts(source, parsed, *, provisional=False):
        result = {}
        rows = parsed.get('reference_spans')
        if not isinstance(rows, list) or len(rows) > 16384:
            raise EditError('parser_contract', 'Candidate native reference inventory unavailable or over limit')
        for ref in rows:
            key = bounds(source, ref)
            if key in result or not provisional and ref.get('resolved') is not True:
                raise EditError('reference_delta', 'Native candidate reference is ambiguous or unresolved')
            aliases = [segment for segment in ref.get('name_binding', {}).get('segments', [])
                       if segment.get('kind') in ('alias_name', 'alias_short_name')]
            result[key] = (ref.get('feature'), ref.get('target') if ref.get('resolved') is True else None,
                           alias_facts(source, aliases))
        return result

    # First retain every original token spelling. Provisional parser output is
    # used only to identify lost bindings, never as a successful candidate or
    # engineering verdict. Repair alias declarations before their consumers.
    # This avoids qualifying a valid alias use merely because its declaration
    # still needs the new namespace spelling in the same pending source step.
    for round_index in range(33):
        files, source, expected_refs, by_index = assemble()
        try:
            provisional = _parser_output(source, 60)
        except subprocess.TimeoutExpired as exc:
            raise EditError('parser_timeout', 'Native reference binding probe exceeded its 60-second limit') from exc
        except (RuntimeError, ValueError, OSError) as exc:
            raise EditError('parser', str(exc)) from exc
        if provisional.get('error'):
            raise EditError('native_diagnostics', 'Native ownership reference probe failed: '+str(provisional['error']))
        if any('Syntax' in str(issue.get('code')) for issue in provisional.get('issues', [])):
            raise EditError('native_diagnostics', json.dumps(provisional['issues']))
        actual = reference_facts(source, provisional, provisional=True)
        drift = {index for index, key in by_index.items() if actual.get(key) != expected_refs[key]}
        if not drift:
            break
        if round_index == 32:
            raise EditError('reference_limit', 'Ownership reference repair exceeded 32 dependency rounds; no candidate was published')
        ready = [index for index in sorted(drift) if index in repairs and index not in rewrites
                 and dependencies[index] is not None and not dependencies[index] & drift]
        if not ready:
            raise EditError('reference_form', 'Remaining references have no safe dependency-ordered repair with the admitted qualified spellings')
        for index in ready:
            changes.extend(repairs[index]['changes'])
            rewrites[index] = repairs[index]['rewritten']
    candidate = type(document)(files if document.is_bundle else files['model.sysml'], project_id=document.project_id,
                               registry=registry, linked_records=linked)
    candidate.reconciliation = reconciliation
    if reference_facts(candidate.source, candidate.parsed) != expected_refs:
        raise EditError('reference_delta', 'Native source-span correspondence changed a retained reference target or feature')
    expected = renamed_native_facts(fingerprint(document.parsed), mapped)
    for record, body in zip(expected.get('documents', []), expected_bodies):
        record['body'] = body
    for group in ('parts', 'part_definitions'):
        for row in expected[group]:
            name = row['qualified_name']
            if name != new and not name.startswith(new+'::'):
                continue
            if name == new:
                if owner.get('qualified_name') is None:
                    row.pop('owner', None)
                else:
                    row['owner'] = owner['qualified_name']
                row['owner_kind'] = owner['kind']
                if group == 'parts':
                    row['is_composite'] = expected_composite
                    row['nested'] = owner['kind'] in ('PartDefinition', 'PartUsage') or bool(owner['source_span'].get('enclosing_part_definition')) or owner['source_span'].get('has_part_usage_ancestor') is True
            if group == 'parts' and not (row.get('part_definition') == new or str(row.get('part_definition', '')).startswith(new+'::')):
                context = owner.get('qualified_name') if owner['kind'] == 'PartDefinition' else owner['source_span'].get('enclosing_part_definition')
                if context is None:
                    row.pop('part_definition', None)
                else:
                    row['part_definition'] = context
    if _canonical_facts(expected) != _canonical_facts(candidate.parsed):
        raise EditError('semantic_delta', 'Native reparse changed facts outside the requested ownership/context transition')
    if _namespace_facts(document, mapped) != _namespace_facts(candidate):
        raise EditError('semantic_delta', 'Native reparse changed unrelated package identities or ownership')
    candidate.ownership_change = {'element_id': element_id, 'before': old, 'after': new,
                                  'destination': deepcopy(destination), 'composition_transition': transition,
                                  'reference_repair_rounds': round_index, 'repaired_reference_count': len(rewrites),
                                  'source_comment_policy': 'Preceding comments outside the native declaration stay at their original site'}
    return candidate
