"""Source-preserving candidate edits for physical composition.

This is an in-memory edit boundary, not project persistence or an acceptance
service. All engineering facts come from the pinned Pilot parser. The bounded
token handling below edits parser-selected ranges; it is not a SysML parser.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re
import subprocess
from pathlib import PurePosixPath
from uuid import UUID, uuid4, uuid5

from .sysml import _parser_output
from .composition_records import rebind_document, rebind_json, strict_json, slots
from .configuration import reconcile as reconcile_configuration


class EditError(ValueError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def codepoint_index(source, offset):
    """Convert an Xtext UTF-16 boundary; refuse a split surrogate pair."""
    if type(offset) is not int or offset < 0:
        raise EditError('source_span', 'Invalid UTF-16 offset')
    raw = source.encode('utf-16-le')
    if offset * 2 > len(raw):
        raise EditError('source_span', 'Offset exceeds source')
    try:
        return len(raw[:offset * 2].decode('utf-16-le'))
    except UnicodeError as exc:
        raise EditError('source_span', 'Offset splits a Unicode character') from exc


def bounds(source, span, prefix=''):
    if span.get('encoding') != 'utf16':
        raise EditError('source_span', 'Unknown coordinate encoding')
    offset, length = span.get(prefix + 'offset'), span.get(prefix + 'length')
    if type(length) is not int or length <= 0:
        raise EditError('source_span', 'Missing or empty source span')
    return codepoint_index(source, offset), codepoint_index(source, offset + length)


def parse(source):
    if not isinstance(source, str) or len(source.encode('utf-8')) > 5_000_000:
        raise EditError('input', 'Source must be UTF-8 text at most 5 MB')
    try:
        parsed = _parser_output(source, 60)
    except subprocess.TimeoutExpired as exc:
        raise EditError('parser_timeout', 'Native parsing exceeded its 60-second limit; no candidate was published') from exc
    except (RuntimeError, ValueError, OSError) as exc:
        raise EditError('parser', str(exc)) from exc
    # An unresolved reference can be a warning. Never author over such input.
    if parsed.get('error') or parsed.get('issues'):
        raise EditError('native_diagnostics', json.dumps(parsed.get('issues', [])))
    if not isinstance(parsed.get('parts'), list) or not isinstance(parsed.get('part_definitions'), list):
        raise EditError('parser_contract', 'Missing native part inventory')
    return parsed


def elements(parsed):
    result = {}
    for group in ('parts', 'part_definitions'):
        for row in parsed[group]:
            name = row.get('qualified_name')
            if not name or name in result:
                raise EditError('identity', 'Missing or duplicate resolved part identity')
            result[name] = {'kind': group, **row}
    return result


def fingerprint(parsed):
    """Compare all extracted native facts, excluding presentation coordinates."""
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()
                    if k not in ('source_span', 'line', 'reference_spans')}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean(parsed)


def replace_identity(value, before, after):
    if isinstance(value, str):
        return after + value[len(before):] if value == before or value.startswith(before + '::') else value
    if isinstance(value, dict):
        return {k: replace_identity(v, before, after) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_identity(v, before, after) for v in value]
    return value


def project_name(name):
    if (not isinstance(name, str) or not name or len(name) > 512 or '\\' in name
            or '\x00' in name or ':' in name or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..') for p in name.split('/'))):
        raise EditError('file_name', 'Use a normalized project-relative POSIX filename')
    return name


class CompositionDocument:
    """Candidate document whose registry persists explicitly with its sources."""

    def __init__(self, source, *, project_id=None, registry=None, linked_records=None):
        self.project_id = str(UUID(project_id)) if project_id else str(uuid4())
        self.is_bundle = isinstance(source, dict)
        self.files = dict(source) if self.is_bundle else {'model.sysml': source}
        if not self.files or len(self.files) > 128:
            raise EditError('input', 'Supply 1 through 128 explicit model files')
        for name in self.files:
            project_name(name)
        self.linked_records = deepcopy(linked_records) if linked_records is not None else {}
        if not isinstance(self.linked_records, dict) or len(self.files) + len(self.linked_records) > 128:
            raise EditError('input', 'Too many project files or invalid linked-record map')
        self.ranges, chunks, cursor, total = [], [], 0, 0
        for name, text in sorted(self.files.items()):
            project_name(name)
            if not isinstance(text, str):
                raise EditError('input', 'Model files must be UTF-8 text')
            total += len(text.encode('utf-8'))
            self.ranges.append((cursor, cursor + len(text), name))
            chunk = text if text.endswith('\n') else text + '\n'
            chunks.append(chunk)
            cursor += len(chunk) + 1
        self.source = '\n'.join(chunks) if self.is_bundle else source
        # A single source preserves its existing coordinates and digest contract.
        if not self.is_bundle:
            self.ranges = [(0, len(source), 'model.sysml')]
        for name, record in self.linked_records.items():
            project_name(name)
            if name in self.files or not isinstance(record, dict) or set(record) != {'kind', 'text'}:
                raise EditError('linked_records', 'Each distinct linked file needs kind and exact text')
            try:
                slots(strict_json(record['text']), record['kind'])
            except (ValueError, TypeError, KeyError, RecursionError) as exc:
                raise EditError('linked_records', str(exc)) from exc
            total += len(record['text'].encode('utf-8'))
        if total > 5_000_000:
            raise EditError('input', 'Combined project input exceeds 5 MB')
        self.parsed = parse(self.source)
        native = elements(self.parsed)
        if registry is None:
            self.registry = {str(uuid5(UUID(self.project_id), name)): name for name in native}
        else:
            self.registry = dict(registry)
            if (len(set(self.registry.values())) != len(self.registry)
                    or set(self.registry.values()) != set(native)):
                raise EditError('reconciliation', 'Registry and parsed identities disagree')
            for identity in self.registry:
                UUID(identity)
        manifest = [{'path': name, 'sha256': sha256(text.encode('utf-8')).hexdigest()}
                    for name, text in sorted(self.files.items())]
        manifest += [{'path': name, 'kind': record['kind'],
                      'sha256': sha256(record['text'].encode('utf-8')).hexdigest()}
                     for name, record in sorted(self.linked_records.items())]
        self.revision = (sha256(source.encode('utf-8')).hexdigest() if not self.is_bundle and not self.linked_records
                         else sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
        self.reconciliation = []
        self.configuration_reviews = [
            {'file': name, 'scope_sha256': sha256(record['text'].encode('utf-8')).hexdigest(),
             'report': reconcile_configuration(strict_json(record['text']), self.parsed)}
            for name, record in sorted(self.linked_records.items()) if record['kind'] == 'retained_configuration']

    def inspect(self):
        native = elements(self.parsed)
        rows = []
        for identity, name in self.registry.items():
            row = {'element_id': identity, **native[name]}
            start, end = bounds(self.source, row['source_span'])
            a, b, file = self.file_range(start, end)
            row['source_location'] = {'file': file, 'line': self.files[file][:start-a].count('\n') + 1,
                                     'offset': start-a, 'length': end-start, 'encoding': 'codepoints'}
            rows.append(row)
        return {'project_id': self.project_id,
                'bundle_sha256' if self.is_bundle or self.linked_records else 'source_sha256': self.revision,
                'elements': rows, 'configuration_reviews': deepcopy(self.configuration_reviews),
                'reconciliation': deepcopy(self.reconciliation)}

    def file_range(self, start, end):
        for a, b, name in self.ranges:
            if a <= start <= end <= b:
                return a, b, name
        raise EditError('source_span', 'Edit crosses a source boundary or synthetic separator')

    def candidate_files(self, changes):
        local = {name: [] for name in self.files}
        for start, end, text in changes:
            a, b, name = self.file_range(start, end)
            local[name].append((start-a, end-a, text))
        result = dict(self.files)
        for name, edits in local.items():
            for a, b, replacement in reversed(sorted(edits)):
                result[name] = result[name][:a] + replacement + result[name][b:]
        return result

    def set_multiplicity(self, element_id, lower, upper, *, expected_source_sha256):
        """Author finite bounds on one native usage, retaining all source trivia."""
        if expected_source_sha256 != self.revision:
            raise EditError('stale_revision', 'Source changed before candidate preparation')
        if (type(lower) is not int or type(upper) is not int
                or not 0 <= lower <= upper <= 2_147_483_647):
            raise EditError('multiplicity', 'Supply integer bounds 0 <= lower <= upper <= 2147483647')
        if not isinstance(element_id, str) or element_id not in self.registry:
            raise EditError('identity', 'Unknown engineering element')
        name = self.registry[element_id]
        item = elements(self.parsed)[name]
        if item['kind'] != 'parts':
            raise EditError('element_kind', 'Multiplicity belongs to a part usage, not its definition')
        span = item['source_span']
        declaration = bounds(self.source, span)
        edited_range = None
        changes = []
        if 'multiplicity_offset' in span:
            edited_range = bounds(self.source, span, 'multiplicity_')
            a, b = edited_range
            if not declaration[0] <= a < b <= declaration[1]:
                raise EditError('source_span', 'Multiplicity is not local to the selected declaration')
            lo_tokens, hi_tokens = span.get('multiplicity_lower_tokens'), span.get('multiplicity_upper_tokens')
            if not isinstance(lo_tokens, list) or not isinstance(hi_tokens, list) or not hi_tokens:
                raise EditError('source_span', 'Native bound token coordinates unavailable')
            for tokens, value in ((lo_tokens, str(lower)),
                                  (hi_tokens, str(upper) if lo_tokens or lower == upper else f'{lower}..{upper}')):
                for index, token in enumerate(tokens):
                    start, end = bounds(self.source, token)
                    if not a < start < end < b:
                        raise EditError('source_span', 'Bound token exceeds its native range')
                    changes.append((start, end, value if index == 0 else ''))
        else:
            offset = codepoint_index(self.source, span.get('multiplicity_insert_offset'))
            if not declaration[0] < offset < declaration[1]:
                raise EditError('source_span', 'Native multiplicity insertion anchor unavailable')
            spelling = str(lower) if lower == upper else f'{lower}..{upper}'
            changes.append((offset, offset, f' [{spelling}]'))
        changes.sort()
        if any(a[1] > b[0] for a, b in zip(changes, changes[1:])):
            raise EditError('overlapping_edits', 'Native bound tokens overlap')
        # Identity does not change, but unknown structured contracts cannot be
        # silently bypassed. Their typed adapters still decide admissibility.
        try:
            for document in self.parsed.get('documents', []):
                rebind_document(document['body'], document.get('name'), lambda value: value)
            for record in self.linked_records.values():
                rebind_json(record['text'], record['kind'], lambda value: value)
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            raise EditError('linked_records', str(exc)) from exc
        files = self.candidate_files(changes)
        candidate = CompositionDocument(files if self.is_bundle else files['model.sysml'],
                                        project_id=self.project_id, registry=self.registry,
                                        linked_records=self.linked_records)
        expected = fingerprint(self.parsed)
        for row in expected['parts']:
            if row['qualified_name'] == name:
                row['multiplicity'] = {'status': 'literal', 'lower': lower, 'upper': upper}
        if fingerprint(candidate.parsed) != expected:
            raise EditError('semantic_delta', 'Reparse changed facts outside the requested multiplicity')
        references = self.parsed.get('reference_spans')
        if not isinstance(references, list) or len(references) > 16384:
            raise EditError('parser_contract', 'Native reference spans unavailable')
        retained = []
        for ref in references:
            if ref.get('resolved') is not True:
                raise EditError('unresolved_reference', 'Native reference is unresolved')
            a, b = bounds(self.source, ref)
            if edited_range and edited_range[0] <= a < b <= edited_range[1]:
                continue
            retained.append((ref.get('feature'), ref.get('target')))
        after = [(r.get('feature'), r.get('target')) for r in candidate.parsed['reference_spans']]
        if retained != after:
            raise EditError('reference_delta', 'Resolved references outside the edited bound changed')
        return candidate

    def rename(self, element_id, new_name, *, expected_source_sha256):
        if expected_source_sha256 != self.revision:
            raise EditError('stale_revision', 'Source changed before candidate preparation')
        if not isinstance(new_name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', new_name):
            raise EditError('name', 'Supply a simple SysML name of at most 64 characters')
        if element_id not in self.registry:
            raise EditError('identity', 'Unknown engineering element')
        old = self.registry[element_id]
        item = elements(self.parsed)[old]
        new = old.rsplit('::', 1)[0] + '::' + new_name
        if new == old:
            return self
        if new in elements(self.parsed):
            raise EditError('name_collision', 'Sibling identity already exists')
        # Documentary/analytical bindings require their own typed atomic adapter.
        # Refuse those candidates until that adapter exists, rather than miss one.
        renames = {old: new}
        # An unnamed redefinition derives its local name from the renamed role.
        # Preserve that overriding element's identity as well as the base role.
        for _ in range(len(self.registry)):
            added = False
            for name, row in elements(self.parsed).items():
                targets = row.get('redefines', [])
                if (name not in renames and len(targets) == 1 and targets[0] in renames
                        and 'name_offset' not in row['source_span']):
                    renames[name] = name.rsplit('::', 1)[0] + '::' + new_name
                    added = True
            if not added:
                break

        def mapped(value):
            # Apply longest exact namespace prefixes first; no fuzzy matching.
            if isinstance(value, str):
                for before in sorted(renames, key=len, reverse=True):
                    if value == before or value.startswith(before + '::'):
                        return renames[before] + value[len(before):]
                return value
            if isinstance(value, dict):
                return {k: mapped(v) for k, v in value.items()}
            if isinstance(value, list):
                return [mapped(v) for v in value]
            return value
        start, end = bounds(self.source, item['source_span'], 'name_')
        changes = [(start, end, new_name)]
        references = self.parsed.get('reference_spans')
        if not isinstance(references, list) or len(references) > 16384:
            raise EditError('parser_contract', 'Native reference spans unavailable')
        for ref in references:
            if ref.get('resolved') is not True:
                raise EditError('unresolved_reference', 'Native reference is unresolved')
            target = ref['target']
            if mapped(target) == target:
                continue
            a, b = bounds(self.source, ref)
            text = self.source[a:b]
            matches = list(re.finditer(r'[A-Za-z][A-Za-z0-9_]*', text))
            tokens = [m.group() for m in matches]
            target_tokens = target.split('::')
            if not tokens or tokens != target_tokens[-len(tokens):]:
                raise EditError('reference_form', 'Reference spelling needs an explicit adapter')
            spellings = mapped(target).split('::')[-len(tokens):]
            for token, replacement in zip(matches, spellings):
                if token.group() != replacement:
                    changes.append((a + token.start(), a + token.end(), replacement))
        expected_bodies = []
        for document in self.parsed.get('documents', []):
            try:
                body, findings = rebind_document(document['body'], document.get('name'), mapped)
                expected_bodies.append(body)
                if body != document['body']:
                    a, b = bounds(self.source, document['source_span'], 'body_')
                    token = self.source[a:b]
                    if not token.startswith('/*') or not token.endswith('*/'):
                        raise EditError('source_span', 'Unsupported documentation body token')
                    raw, raw_findings = rebind_document(token[2:-2], document.get('name'), mapped)
                    # Pilot normalizes leading whitespace on documentation lines.
                    # Compare the complete JSON meaning, then retain the exact
                    # source formatting; do not reconstruct it from getBody().
                    raw_payload = raw.lstrip().split('\n', 1)[1]
                    parsed_payload = body.lstrip().split('\n', 1)[1]
                    if raw_findings != findings or strict_json(raw_payload) != strict_json(parsed_payload):
                        raise EditError('source_span', 'Documentation token and parsed body disagree')
                    changes.append((a+2, b-2, raw))
            except (ValueError, KeyError, TypeError, RecursionError) as exc:
                raise EditError('linked_records', str(exc)) from exc
        linked = deepcopy(self.linked_records)
        reconciliation = []
        for name, record in linked.items():
            try:
                rewritten, findings = rebind_json(record['text'], record['kind'], mapped)
                if findings and record['kind'] == 'retained_configuration':
                    reconciliation.append({'file': name, 'status': 'reconciliation_required',
                                           'retained_sha256': sha256(record['text'].encode('utf-8')).hexdigest(),
                                           'changes': findings})
                record['text'] = rewritten
            except (ValueError, KeyError, TypeError, RecursionError) as exc:
                raise EditError('linked_records', str(exc)) from exc
        changes.sort()
        if any(a[1] > b[0] for a, b in zip(changes, changes[1:])):
            raise EditError('overlapping_edits', 'Native edit spans overlap')
        files = self.candidate_files(changes)
        registry = {identity: mapped(name) for identity, name in self.registry.items()}
        candidate = CompositionDocument(files if self.is_bundle else files['model.sysml'],
                                        project_id=self.project_id, registry=registry, linked_records=linked)
        candidate.reconciliation = reconciliation
        expected = mapped(fingerprint(self.parsed))
        for document, body in zip(expected.get('documents', []), expected_bodies):
            document['body'] = body
        # Only the selected declaration's local name changes. The independent
        # reparse must retain every other fact exposed by the current bridge.
        for group in ('parts', 'part_definitions'):
            for row in expected[group]:
                if row['qualified_name'] in renames.values():
                    row['name'] = new_name
        if fingerprint(candidate.parsed) != expected:
            raise EditError('semantic_delta', 'Reparse changed facts outside the requested rename')
        before_refs = [(r.get('feature'), mapped(r.get('target'))) for r in references]
        after_refs = [(r.get('feature'), r.get('target')) for r in candidate.parsed['reference_spans']]
        if before_refs != after_refs:
            raise EditError('reference_delta', 'Resolved reference correspondence changed')
        return candidate
