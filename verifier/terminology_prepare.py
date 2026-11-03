"""Prepare separate English-profile candidates from explicit selected bindings.

Exact string matching maintains declared uses; it does not discover concepts,
infer parts of speech, edit prose, approve terminology or adopt a review scope.
"""
from copy import deepcopy
from hashlib import sha256
import difflib
import json
from pathlib import Path
import re

from .foundation import (Invalid, NATIVE, _schema, _object, _text, _list,
                         digest, load_profile, read_regular, term_digest)
from .sysml import check_sysml
from .terminology import check_english, english_schema, text_digest, SEVERITY

VERSION = 'english-preparation-1.0'
MATCH_CAP = 1_000_000


def _matches(text, forms, preserved):
    matches = set()
    for form in forms:
        pattern = (r'(?<!\w)' if form[0].isalnum() else '') + re.escape(form) + (r'(?!\w)' if form[-1].isalnum() else '')
        for match in re.finditer(pattern, text):
            if not any(span['start'] < match.end() and match.start() < span['end'] for span in preserved):
                matches.add((match.start(), match.end()))
    return sorted(matches)


def _body(profile, native, view):
    element = profile['elements'].get(view['element'])
    inventory = native.get('inventory', {})
    if element is None or len([item for item in inventory.get(NATIVE[element['kind']], [])
            if item.get('qualified_name') == element['native_name']]) != 1:
        raise Invalid('Selected document owner needs one existing native element of its declared kind')
    documents = [item for item in inventory.get('documents', [])
                 if item.get('owner') == element['native_name'] and item.get('name') == view['document']]
    if len(documents) != 1:
        raise Invalid('Select one existing named native document')
    text = documents[0]['body'].strip()
    _text(text, 'Selected native text')
    return text


def _initial_scope(profile, selection):
    _object(selection, ('version', 'revision', 'rules', 'terms', 'views', 'phrases'), 'selection')
    if selection['version'] != 'english-selection-1.0':
        raise Invalid('Unsupported English selection version')
    _list(selection['terms'], 'Selected term IDs')
    if (any(type(key) is not str or key not in profile['terms'] for key in selection['terms']) or
            len(set(selection['terms'])) != len(selection['terms'])):
        raise Invalid('Select distinct existing catalog term IDs; concepts and approval are not inferred')
    scope = deepcopy(selection)
    scope['version'] = 'english-1.0'
    scope['terms'] = {key: term_digest(profile['terms'][key]) for key in selection['terms']}
    if type(scope['views']) is not dict or not scope['views'] or len(scope['views']) > 512:
        raise Invalid('Select 1..512 explicit native views')
    for view in scope['views'].values():
        _object(view, ('element', 'document', 'uses', 'preserved'), 'Selected view')
        _list(view['uses'], 'Selected uses'); _list(view['preserved'], 'Selected preserved spans')
        for use in view['uses']:
            _object(use, ('term', 'slot', 'element'), 'Selected use', required=('term', 'slot'))
            use.update(start=0, end=1)
        for span in view['preserved']:
            _object(span, ('text', 'kind', 'basis'), 'Selected source/literal')
            span.update(start=0, end=1)
        view['text_sha256'] = '0'*64
    # Full schema validation follows actual span resolution; placeholder spans
    # must never be emitted or used as a successful check input.
    return scope


def propose(profile: dict, native: dict, *, selection: dict | None = None,
            before_native: dict | None = None, revision: str | None = None) -> tuple[dict, dict | None]:
    """Return a preparation report and optional separate candidate; mutate nothing."""
    report = {'version': VERSION, 'status': 'error', 'operation': 'not_generated',
        'claim_scope': 'draft_profile_preparation_only', 'findings': [], 'changes': [],
        'text_changes': [], 'language_status': 'not_run', 'retained_scope': 'not_advanced',
        'meaning_equivalence': 'not_evaluated', 'acceptance': 'not_evaluated',
        'limits': {'matching_character_checks': MATCH_CAP, 'text_characters': 4096, 'items_per_group': 512}}
    candidate = None
    def issue(rule, status, ids, detail):
        report['findings'].append({'rule': rule, 'status': status, 'ids': ids, 'detail': detail})
    try:
        _schema(profile)
        if type(native) is not dict or native.get('status') != 'pass':
            raise Invalid('Current native parsing/linking must pass before preparation')
        candidate = deepcopy(profile)
        initial = 'english' not in profile
        if initial:
            if selection is None:
                raise Invalid('Initial preparation requires an explicit English selection')
            scope = _initial_scope(profile, selection)
        else:
            if selection is not None:
                raise Invalid('Existing English scope cannot be replaced by preparation; propose scope changes separately')
            english_schema(profile['english'])
            _text(revision, 'Explicit proposed draft revision')
            baseline = native if native.get('model_sha256') == profile['source_sha256'] else before_native
            if type(baseline) is not dict or baseline.get('model_sha256') != profile['source_sha256']:
                raise Invalid('Changed native source requires the before-model revision matching the retained profile source pin')
            old = check_english(profile, baseline)
            blocking = [item for item in old['findings'] if item['status'] in SEVERITY and item['status'] != 'pass'
                        and not item['rule'].startswith('CSE-PHRASE/')]
            if blocking:
                issue('preparation_baseline', 'fail', [], 'Prior identities, text hashes, terms or use bindings are stale/invalid; preparation cannot hide them')
                report['baseline_findings'] = blocking
                return report | {'status': 'fail'}, None
            scope = deepcopy(profile['english'])
            report['before_scope_sha256'] = digest(profile['english'])
        if revision is not None:
            _text(revision, 'Proposed draft revision'); scope['revision'] = revision
        candidate['english'] = scope
        candidate['source_sha256'] = native['model_sha256']
        work = 0
        for view_id, view in sorted(scope['views'].items()):
            text = _body(candidate, native, view)
            old_text = None if initial else _body(profile, baseline, profile['english']['views'][view_id])
            if text == old_text:
                # Prior validation established these exact spans. An unrelated
                # source edit does not turn an explicit subset into "all uses".
                continue
            preserved = []
            unresolved = False
            for span in view['preserved']:
                _text(span['text'], 'Preserved source/literal')
                locations = [match.span() for match in re.finditer(re.escape(span['text']), text)]
                work += len(text)
                if work > MATCH_CAP:
                    issue('preparation_limit', 'unknown', [view_id], 'Exact matching exceeded its declared work cap')
                    unresolved = True; break
                if len(locations) != 1:
                    issue('preparation_preserved_span', 'unknown', [view_id], 'Preserved text is absent or ambiguous; no source text or span is rewritten')
                    unresolved = True
                else:
                    preserved.append(dict(span, start=locations[0][0], end=locations[0][1]))
            if unresolved:
                continue
            groups = {}
            for index, use in enumerate(view['uses']):
                _object(use, ('term', 'slot', 'start', 'end', 'element'), 'Selected use', required=('term', 'slot', 'start', 'end'))
                key = (use['term'], use['slot'], use.get('element', view['element']))
                if use['term'] not in scope['terms'] or use['term'] not in candidate['terms']:
                    raise Invalid('Every use needs an explicitly selected existing term')
                groups.setdefault(key, []).append(index)
            proposed_spans = []
            for (term_id, slot, target), indices in sorted(groups.items()):
                term = candidate['terms'][term_id]
                forms = term.get('approved_forms', [term['label']])
                work += len(text)*len(forms)
                if work > MATCH_CAP:
                    issue('preparation_limit', 'unknown', [view_id], 'Exact matching exceeded its declared work cap')
                    unresolved = True; break
                locations = _matches(text, forms, preserved)
                if len(locations) != len(indices):
                    issue('preparation_use_match', 'unknown', [view_id, target, term_id],
                          'Expected '+str(len(indices))+' selected authored occurrence(s); found '+str(len(locations))+' exact approved-form match(es). Resolve absent/ambiguous uses explicitly')
                    unresolved = True; continue
                for index, (start, end) in zip(indices, locations):
                    view['uses'][index].update(start=start, end=end)
                    proposed_spans.append((start, end))
            if any(a[1] > b[0] for a, b in zip(sorted(proposed_spans), sorted(proposed_spans)[1:])):
                issue('preparation_overlap', 'unknown', [view_id], 'Selected concepts or forms overlap; no meaning is inferred from matching words')
                unresolved = True
            if unresolved:
                continue
            view.update(text_sha256=text_digest(text), preserved=preserved)
            if not initial:
                if old_text != text:
                    report['text_changes'].append({'view': view_id, 'diff': ''.join(difflib.unified_diff(
                        [line+'\n' for line in old_text.splitlines()], [line+'\n' for line in text.splitlines()],
                        fromfile='before', tofile='candidate', n=0))})
        if report['findings']:
            report['status'] = max((item['status'] for item in report['findings']), key=SEVERITY.get)
            return report, None
        _schema(candidate); english_schema(scope)
        check = check_english(candidate, native)
        report.update(language_status=check['status'], language_findings=check['findings'],
                      candidate_scope_sha256=digest(scope), operation='candidate_generated')
        for key in ('source_sha256', 'english'):
            if profile.get(key) != candidate[key]:
                # Field paths retain the exact old/new bindings without dumping
                # a second vocabulary or native inventory into normal output.
                if key == 'source_sha256':
                    report['changes'].append({'path': key, 'before': profile[key], 'candidate': candidate[key]})
                elif initial:
                    report['changes'].append({'path': 'english', 'before': None, 'candidate_scope_sha256': digest(scope)})
                else:
                    for field in ('revision', 'views'):
                        if profile['english'][field] != scope[field]:
                            report['changes'].append({'path': 'english.'+field, 'before': profile['english'][field], 'candidate': scope[field]})
        report['status'] = check['status']
        return report, candidate
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        issue('preparation_input', 'error', [], str(exc))
        return report | {'status': 'error'}, None


def prepare_profile(model_path, profile_path, output_path, *, selection_path=None,
                    before_model_path=None, revision=None):
    """Capture real files, parse actual native documents and create a new file only."""
    captured = []
    def capture(path, cap):
        raw = read_regular(path, cap); captured.append((path, raw, cap)); return raw
    try:
        current = capture(model_path, 5_000_000)
        profile_raw = capture(profile_path, 1_000_000)
        profile, profile_pin = load_profile(profile_path)
        if profile_pin != sha256(profile_raw).hexdigest():
            raise Invalid('Profile changed between capture and loading')
        selection = None
        if selection_path is not None:
            selection_raw = capture(selection_path, 1_000_000)
            selection, selection_pin = load_profile(selection_path)
            if selection_pin != sha256(selection_raw).hexdigest():
                raise Invalid('Selection changed between capture and loading')
        native = check_sysml(Path(model_path), syntax_only=True)
        if type(native) is not dict:
            raise Invalid('Native parser returned a malformed report')
        if native.get('model_sha256') != sha256(current).hexdigest():
            raise Invalid('Native source changed between capture and parsing')
        before = None
        if before_model_path is not None:
            previous = capture(before_model_path, 5_000_000)
            before = native if previous == current else check_sysml(Path(before_model_path), syntax_only=True)
            if type(before) is not dict:
                raise Invalid('Before-model parser returned a malformed report')
            if before.get('model_sha256') != sha256(previous).hexdigest():
                raise Invalid('Before-model changed between capture and parsing')
        report, candidate = propose(profile, native, selection=selection, before_native=before, revision=revision)
        report['inputs'] = {'model_sha256': sha256(current).hexdigest(), 'profile_file_sha256': profile_pin}
        if selection_path is not None:
            report['inputs']['selection_file_sha256'] = selection_pin
        if before_model_path is not None:
            report['inputs']['before_model_sha256'] = sha256(previous).hexdigest()
        if any(read_regular(path, cap) != raw for path, raw, cap in captured):
            raise Invalid('A captured input changed during preparation; no candidate was written')
        report['input_stability'] = 'pass'
        if candidate is not None:
            serialized = json.dumps(candidate, ensure_ascii=False, indent=2)+'\n'
            if len(serialized.encode('utf-8')) > 1_000_000:
                raise Invalid('Prepared candidate exceeds the existing 1 MB profile limit')
            # Exclusive creation also rejects an existing live profile, symlink
            # or hard link. No model or input profile is ever edited.
            with Path(output_path).open('x', encoding='utf-8') as stream:
                stream.write(serialized)
            report['candidate_path'] = str(Path(output_path).resolve())
            report['candidate_file_sha256'] = sha256(read_regular(output_path, 1_000_000)).hexdigest()
            if any(read_regular(path, cap) != raw for path, raw, cap in captured):
                report.update(status='error', operation='candidate_unusable',
                    input_stability='error',
                    detail='A captured input changed while writing; retain the candidate for review but do not use its result')
        return report
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        return {'version': VERSION, 'status': 'error', 'operation': 'not_generated',
                'claim_scope': 'draft_profile_preparation_only', 'detail': str(exc),
                'retained_scope': 'not_advanced', 'acceptance': 'not_evaluated'}
