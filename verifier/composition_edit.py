"""Source-preserving candidate edits for physical composition.

This is an in-memory edit boundary, not project persistence or an acceptance
service. All engineering facts come from the pinned Pilot parser. The bounded
token handling below edits parser-selected ranges; it is not a SysML parser.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re
from uuid import UUID, uuid4, uuid5

from .sysml import _parser_output


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


class CompositionDocument:
    """Candidate document whose registry persists explicitly with its sources."""

    def __init__(self, source, *, project_id=None, registry=None):
        self.project_id = str(UUID(project_id)) if project_id else str(uuid4())
        self.source = source
        self.parsed = parse(source)
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
        self.revision = sha256(source.encode('utf-8')).hexdigest()

    def inspect(self):
        native = elements(self.parsed)
        return {'project_id': self.project_id, 'source_sha256': self.revision,
                'elements': [{'element_id': identity, **native[name]}
                             for identity, name in self.registry.items()]}

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
        if self.parsed.get('documents'):
            raise EditError('linked_records', 'Rename needs documentary binding reconciliation')
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
        if not isinstance(references, list):
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
        changes.sort()
        if any(a[1] > b[0] for a, b in zip(changes, changes[1:])):
            raise EditError('overlapping_edits', 'Native edit spans overlap')
        source = self.source
        for a, b, text in reversed(changes):
            source = source[:a] + text + source[b:]
        registry = {identity: mapped(name) for identity, name in self.registry.items()}
        candidate = CompositionDocument(source, project_id=self.project_id, registry=registry)
        expected = mapped(fingerprint(self.parsed))
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
