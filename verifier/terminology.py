"""Controlled English for selected engineering terms and native authored text.

Use the existing foundation vocabulary, explicit grammatical slots and bounded
project rules. No unrestricted prose parser or dictionary approval is inferred.
"""
from hashlib import sha256
from pathlib import Path
import re

from .foundation import (Invalid, NATIVE, _schema as foundation_schema, _object, _map,
                         _text, _list, digest, load_profile, read_regular,
                         term_digest, term_findings)

VERSION = 'english-1.0'
STANDARD = {'name': 'ASD-STE100', 'issue': '9', 'date': '2025-01-15',
            'source': 'https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf',
            'supported_rule': '1.11', 'coverage': 'selected_declared_technical_noun_uses'}
RULES = {'ASD-STE100-1.11', 'CSE-TERM-POS', 'CSE-PHRASES'}
SEVERITY = {'pass': 0, 'unknown': 1, 'unsupported': 2, 'fail': 3, 'error': 4}


def text_digest(text):
    return sha256(text.encode('utf-8')).hexdigest()


def _sha(value, where):
    if type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value):
        raise Invalid(f'{where} needs a lowercase SHA-256')


def _span(value, where):
    if any(type(value[x]) is not int for x in ('start', 'end')) or not 0 <= value['start'] < value['end'] <= 4096:
        raise Invalid(f'{where} needs character bounds 0 <= start < end <= 4096')


def english_schema(scope):
    _object(scope, ('version', 'revision', 'rules', 'terms', 'views', 'phrases'), 'english')
    if scope['version'] != VERSION:
        raise Invalid('Unsupported controlled-English profile version')
    _text(scope['revision'], 'english.revision')
    for field in ('terms', 'views', 'phrases'):
        _map(scope[field], f'english.{field}')
    _list(scope['rules'], 'english.rules')
    if any(type(x) is not str for x in scope['rules']) or len(scope['rules']) != len(set(scope['rules'])):
        raise Invalid('english.rules needs unique rule identifiers')
    for key, pin in scope['terms'].items():
        _sha(pin, f'english.terms.{key}')
    for key, view in scope['views'].items():
        _object(view, ('element', 'document', 'text_sha256', 'uses', 'preserved'), key)
        _text(view['element'], f'{key}.element'); _text(view['document'], f'{key}.document')
        _sha(view['text_sha256'], f'{key}.text_sha256')
        for field in ('uses', 'preserved'):
            _list(view[field], f'{key}.{field}')
        spans = []
        for use in view['uses']:
            _object(use, ('term', 'slot', 'start', 'end', 'element'), f'{key}.use', required=('term', 'slot', 'start', 'end'))
            _text(use['term'], f'{key}.use.term'); _span(use, f'{key}.use')
            if 'element' in use:
                _text(use['element'], f'{key}.use.element')
            if use['slot'] not in ('noun', 'verb'):
                raise Invalid(f'{key}.use.slot needs noun or verb')
            spans.append((use['start'], use['end']))
        if any(a[1] > b[0] for a, b in zip(sorted(spans), sorted(spans)[1:])):
            raise Invalid(f'{key} term uses overlap')
        for source in view['preserved']:
            _object(source, ('start', 'end', 'text', 'kind', 'basis'), f'{key}.preserved')
            _span(source, f'{key}.preserved'); _text(source['text'], f'{key}.preserved.text')
            _text(source['basis'], f'{key}.preserved.basis')
            if source['kind'] not in ('quotation', 'original_note', 'identifier', 'interface_literal'):
                raise Invalid(f'{key}.preserved.kind needs quotation, original_note, identifier or interface_literal')
    for key, rule in scope['phrases'].items():
        _object(rule, ('phrase', 'repair', 'severity'), f'english.phrases.{key}')
        _text(rule['phrase'], f'{key}.phrase'); _text(rule['repair'], f'{key}.repair')
        if rule['severity'] not in ('required', 'advice'):
            raise Invalid(f'{key}.severity needs required or advice')


def check_english(profile, native, *, review=False, retained_scope_sha256=None, phrase_work_cap=1_000_000):
    report = {'checker_version': VERSION, 'status': 'error', 'required_review': bool(review),
              'claim_scope': 'selected_controlled_english', 'standard_basis': STANDARD.copy(),
              'findings': [], 'selected_terms': [], 'checked_views': [],
              'limits': {'items_per_group': 512, 'text_characters': 4096, 'phrase_character_checks': phrase_work_cap},
              'acceptance': 'not_evaluated'}

    def issue(rule, status, ids, phrase, detail, repair, **extra):
        report['findings'].append({'rule': rule, 'status': status, 'ids': ids, 'phrase': phrase,
                                  'detail': detail, 'repair': repair, **extra})

    try:
        foundation_schema(profile)
        scope = profile.get('english')
        if scope is None:
            issue('CSE-ENGLISH-PROFILE', 'unknown', [], '', 'No selected controlled-English profile.',
                  'Select the project terms and rules before describing drafting as conforming.')
            report['status'] = 'unknown'
            return report
        english_schema(scope)
        if type(phrase_work_cap) is not int or phrase_work_cap < 1:
            raise Invalid('Phrase work cap must be a positive integer')
        report.update(scope_sha256=digest(scope), scope_revision=scope['revision'], profile_sha256=digest(profile),
                      source_sha256=profile['source_sha256'], selected_rules=scope['rules'], selected_terms=sorted(scope['terms']))
        if review and retained_scope_sha256 is None:
            issue('CSE-SCOPE', 'unknown', [], '', 'Required terminology review needs the retained rule/term scope digest.',
                  'Supply the separately retained scope revision; drafting checks still run.')
        elif retained_scope_sha256 is not None and retained_scope_sha256 != report['scope_sha256']:
            issue('CSE-SCOPE', 'fail', [], scope['revision'], 'Selected terminology scope changed.',
                  'Review the scope change instead of deleting selected terms or rules to pass.')
        for rule in sorted(set(scope['rules']) - RULES):
            issue(rule, 'unsupported', [], rule, 'Selected rule has no deterministic implementation.',
                  'Retain the unresolved rule or select a supported check with the engineer.')
        if 'CSE-TERM-POS' not in scope['rules'] or 'ASD-STE100-1.11' not in scope['rules']:
            issue('CSE-SCOPE', 'unknown', [], '', 'The strict English profile needs its noun-consistency and declared-part-of-speech rules.',
                  'Retain the selected strict rules; do not label a reduced check conforming.')
        if scope['phrases'] and 'CSE-PHRASES' not in scope['rules']:
            issue('CSE-SCOPE', 'fail', [], 'CSE-PHRASES', 'Declared phrase rules were not selected.',
                  'Select the rules or explicitly review their removal.')
        if not scope['terms'] or not scope['views']:
            issue('CSE-SCOPE', 'unknown', [], '', 'Select nonempty English terminology and native authored views.',
                  'Select the concepts and exact authored text for this drafting question.')
        if type(native) is not dict:
            raise Invalid('Native report must be an object')
        inventory = native.get('inventory', {})
        if type(inventory) is not dict:
            raise Invalid('Native inventory must be an object')
        for category in sorted({NATIVE[element['kind']] for element in profile['elements'].values()} | {'documents'}):
            items = inventory.get(category, [])
            if type(items) is not list or any(type(item) is not dict for item in items):
                raise Invalid('Native inventory ' + category + ' must be a list of objects')
        if native.get('status') != 'pass':
            status = native.get('status') if native.get('status') in SEVERITY else 'error'
            issue('CSE-NATIVE', status, [], '', 'Native parsing/linking did not pass.',
                  'Resolve native diagnostics before relying on the text bindings.')
        if native.get('model_sha256') != profile['source_sha256']:
            issue('CSE-SOURCE-REVISION', 'fail', [], '', 'The English profile refers to a different native source revision.',
                  'Reconcile the model change and update its source binding without changing accepted meaning.')
        for finding in term_findings(profile['terms']):
            if set(scope['terms']).intersection(finding['ids']):
                report['findings'].append(finding)
        # Labels/definitions and authored views have independent ID namespaces.
        # Preserve every selected text even when their human-readable IDs match.
        texts = []
        for term_id, pin in sorted(scope['terms'].items()):
            term = profile['terms'].get(term_id)
            if term is None:
                issue('CSE-CONCEPT', 'fail', [term_id], term_id, 'Selected engineering term is undefined.',
                      'Resolve its scoped definition; do not infer meaning from a matching label.')
                continue
            if pin != term_digest(term):
                issue('CSE-TERM-REVISION', 'fail', [term_id], term['label'], 'Selected definition, approved forms or grammatical class changed.',
                      'Review the terminology change and affected drafting before advancing the retained pin.')
            for field in ('label', 'definition'):
                texts.append(((term_id, field), term[field], []))

        def bound(element_id, ids, phrase):
            element = profile['elements'].get(element_id)
            if element is None or len([x for x in inventory.get(NATIVE[element['kind']], [])
                                      if x.get('qualified_name') == element['native_name']]) != 1:
                issue('CSE-ELEMENT', 'fail', ids, phrase, 'Expected one parsed native element of the declared kind.',
                      'Resolve the stable element identity and native category.')
                return None
            return element

        coverage = set()
        for view_id, view in sorted(scope['views'].items()):
            owner = bound(view['element'], [view_id, view['element']], view['element'])
            if owner is None:
                continue
            documents = [x for x in inventory.get('documents', [])
                         if x.get('owner') == owner['native_name'] and x.get('name') == view['document']]
            if len(documents) != 1:
                issue('CSE-VIEW', 'fail', [view_id, view['element']], view['document'], 'Expected one named native authored document.',
                      'Identify the exact native text; preserve source quotations and literals separately.')
                continue
            body = documents[0].get('body', '')
            if type(body) is not str:
                raise Invalid(f'{view_id}.text needs native document text')
            text = body.strip(); _text(text, f'{view_id}.text')
            report['checked_views'].append(view_id)
            texts.append(((view_id, view['element']), text, view['preserved']))
            if text_digest(text) != view['text_sha256']:
                issue('CSE-VIEW-REVISION', 'fail', [view_id, view['element']], text, 'Selected authored text changed.',
                      'Review the edited text and reconcile the exact term spans and revision together.')
            for source in view['preserved']:
                if source['end'] > len(text) or text[source['start']:source['end']] != source['text']:
                    issue('CSE-SOURCE-LITERAL', 'fail', [view_id, view['element']], source['text'], 'Preserved source/literal span is stale.',
                          'Retain the actual source text and reconcile its positions without rewriting it for conformance.')
            for use in view['uses']:
                term_id = use['term']; target_id = use.get('element', view['element'])
                phrase = text[use['start']:use['end']]; ids = [view_id, target_id, term_id]
                term = profile['terms'].get(term_id)
                if term is None or term_id not in scope['terms']:
                    issue('CSE-CONCEPT', 'fail', ids, phrase, 'Use has no selected scoped term.',
                          'Select and define the engineering concept; do not guess its meaning.')
                    continue
                target = bound(target_id, ids, phrase)
                if target is not None and (target['term'] != term_id or target['kind'] != term['kind']):
                    issue('CSE-TERM-BINDING', 'fail', ids, phrase, 'Use does not match the native element\'s defined concept and kind.',
                          'Reconcile the definition and native identity instead of selecting a similar label.')
                preserved = [source for source in view['preserved']
                             if source['start'] < use['end'] and use['start'] < source['end']]
                if preserved:
                    issue('CSE-SOURCE-LITERAL', 'unknown', ids, phrase, 'A preserved source/literal is not an authored English term use.',
                          'Keep the source unchanged and supply a separate controlled-English explanation.')
                    continue
                coverage.add(term_id)
                if use['slot'] != term.get('part_of_speech', 'noun'):
                    issue('CSE-TERM-POS', 'fail', ids, phrase, f'Declared {use["slot"]} slot uses a term approved as {term.get("part_of_speech", "noun")}.',
                          'Use the approved term in its declared grammatical role or propose a reviewed vocabulary change.')
                embedded = (use['start'] > 0 and re.match(r'\w', text[use['start']-1:use['start']]) and re.match(r'\w', phrase[:1]) or
                            use['end'] < len(text) and re.match(r'\w', text[use['end']:use['end']+1]) and re.match(r'\w', phrase[-1:]))
                if phrase not in term.get('approved_forms', [term['label']]) or use['end'] > len(text) or embedded:
                    rule = 'ASD-STE100-1.11' if term.get('part_of_speech', 'noun') == 'noun' else 'CSE-TERM-FORM'
                    issue(rule, 'fail', ids, phrase, f'The approved technical {term.get("part_of_speech", "noun")} is {term["label"]!r}.',
                          f'Use a declared form of {term["label"]!r} while preserving source meaning.', start=use['start'], end=use['end'])
        for term_id in sorted(set(scope['terms']) - coverage):
            issue('CSE-USE-COVERAGE', 'unknown', [term_id], term_id, 'Selected term has no authored native use.',
                  'Identify the term\'s exact noun/verb use in the native authored text.')
        work = sum(len(text)*len(scope['phrases']) for _, text, _ in texts)
        report['phrase_work_units'] = work
        if 'CSE-PHRASES' in scope['rules'] and work > phrase_work_cap:
            issue('CSE-LIMIT', 'unknown', [], 'CSE-PHRASES', 'Selected phrase checks exceed the declared work cap.',
                  'Retain the unresolved check and review a smaller selected view or explicit analysis limit.')
        elif 'CSE-PHRASES' in scope['rules']:
            for ids, text, preserved in sorted(texts, key=lambda item: item[0]):
                for rule_id, rule in sorted(scope['phrases'].items()):
                    pattern = (r'(?<!\w)' if rule['phrase'][0].isalnum() else '')+re.escape(rule['phrase'])+(r'(?!\w)' if rule['phrase'][-1].isalnum() else '')
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        sources = [source for source in preserved if source['start'] <= match.start() and source['end'] >= match.end()]
                        issue('CSE-PHRASE/'+rule_id, 'preserved' if sources else 'fail' if rule['severity'] == 'required' else 'advisory',
                              list(ids), match.group(), 'Source/literal retained: '+'; '.join(source['basis'] for source in sources) if sources else
                              'Selected project phrase rule requires an explicit expression.' if rule['severity'] == 'required' else
                              'Selected contextual writing advice.', 'Preserve the source wording; explain it separately.' if sources else rule['repair'],
                              start=match.start(), end=match.end())
        report['status'] = max((x['status'] for x in report['findings'] if x['status'] in SEVERITY), default='pass', key=SEVERITY.get)
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        issue('CSE-SCHEMA', 'error', [], '', str(exc), 'Repair the declared record while preserving source meaning and selected rules.')
        report['status'] = 'error'
    report['findings'].sort(key=lambda x: (x['rule'], x['ids'], x.get('start', -1), x['detail']))
    report['advisory_count'] = sum(x['status'] == 'advisory' for x in report['findings'])
    return report


def inspect(model_path, profile_path, *, review=False, retained_scope_sha256=None, native=None):
    from .sysml import check_sysml
    profile, profile_raw = load_profile(profile_path)
    before = sha256(read_regular(model_path, 5_000_000)).hexdigest()
    if native is None:
        native = check_sysml(Path(model_path), syntax_only=True)
    report = check_english(profile, native, review=review, retained_scope_sha256=retained_scope_sha256)
    native_digest = native.get('model_sha256') if type(native) is dict else None
    if (sha256(read_regular(model_path, 5_000_000)).hexdigest() != before or native_digest != before or
            sha256(read_regular(profile_path, 1_000_000)).hexdigest() != profile_raw):
        report['status'] = 'error'
        report['findings'].append({'rule': 'CSE-INPUT-CHANGED', 'status': 'error', 'ids': [], 'phrase': '',
            'detail': 'Model/profile changed during checking or parser digest mismatched.',
            'repair': 'Retain both revisions and rerun after reconciling concurrent edits.'})
    report['profile_file_sha256'] = profile_raw
    return report


def apply_drafting_profiles(report, model_paths):
    """Normal draft checks enforce a selected sibling profile without another flag."""
    paths = [Path(path) for path in model_paths]
    profiles = [(path, path.with_suffix('.english.json')) for path in paths
                if path.with_suffix('.english.json').exists() or path.with_suffix('.english.json').is_symlink()]
    if not profiles:
        return report
    try:
        if len(paths) != 1:
            raise Invalid('Selected English profiles over multiple native files are unsupported; retain this unresolved check')
        model, profile = profiles[0]
        result = inspect(model, profile, native=report if 'inventory' in report else None)
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, RecursionError) as exc:
        result = {'status': 'unsupported' if len(paths) != 1 else 'error', 'checker_version': VERSION,
                  'required_review': False, 'selected_terms': [], 'checked_views': [],
                  'findings': [{'rule': 'CSE-ENGLISH-PROFILE', 'status': 'unsupported' if len(paths) != 1 else 'error',
                    'ids': [], 'phrase': '', 'detail': str(exc),
                    'repair': 'Resolve the selected profile; ordinary drafting cannot silently skip its language checks.'}]}
    report['english'] = result
    report['status'] = max((report['status'], result['status']), key=lambda x: SEVERITY.get(x, 4))
    return report


def render_text(report, *, finding_limit=12):
    lines = [f'{report["status"]}: controlled English; {len(report["selected_terms"])} term(s), {len(report["checked_views"])} authored view(s).']
    findings = sorted(report['findings'], key=lambda x: (-SEVERITY.get(x['status'], -1), x['rule'], x['ids']))
    for finding in findings[:finding_limit]:
        lines.append(f'{finding["status"]} {finding["rule"]} [{", ".join(finding["ids"])}] {finding["phrase"]!r}: '
                     f'{finding["detail"]} Repair: {finding["repair"]}')
    if len(findings) > finding_limit:
        lines.append(f'{len(findings)-finding_limit} more finding(s); use --json for details.')
    return '\n'.join(lines)+'\n'
