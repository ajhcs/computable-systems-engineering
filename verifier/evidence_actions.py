"""Derive next-evidence questions from an existing scoped concept review.

This view adds no engineering obligations, owners, policy or accepted evidence.
It cannot close findings or turn reported material into observed validation.
"""
from copy import deepcopy


def next_evidence(review):
    record = review.get('workflow', {}).get('record') or {}
    questions = record.get('questions', {})
    plans = record.get('evidence', {})
    items = []
    seen = set()
    for finding in review.get('findings', []):
        if finding['status'] == 'pass':
            continue
        ids = set(finding.get('ids', []))
        for key in list(ids):
            ids.update(questions.get(key, {}).get('affects', []))
        signature = (finding['rule'], tuple(sorted(ids)), finding['detail'])
        if signature in seen:
            continue
        seen.add(signature)
        repair = finding['status'] in ('error', 'fail', 'unsupported', 'not_run')
        matching = {key: deepcopy(plan) for key, plan in plans.items()
                    if key in ids or plan['target'] in ids}
        items.append({'rule': finding['rule'], 'status': finding['status'],
            'affected_ids': sorted(ids), 'question': finding['detail'],
            'action_class': 'repair_or_select_supported_check' if repair else 'obtain_evidence_or_engineer_decision',
            'existing_plans': matching, 'responsible_party': None,
            'closure': 'unresolved; no evidence acquired or decision authenticated'})
    items.sort(key=lambda x: (x['action_class'] != 'repair_or_select_supported_check',
                               x['rule'], x['affected_ids'], x['question']))
    return {'version': 'concept-evidence-actions-1.0', 'status': review['status'],
        'claim_scope': 'derived_next_evidence_questions_only',
        'project': deepcopy(review.get('project')),
        'model_sha256': review.get('model_sha256'),
        'scope_sha256': review.get('scope_sha256'),
        'sources': deepcopy(review.get('sources', {})),
        'coverage': deepcopy(review.get('coverage', {})), 'actions': items,
        'unexecuted_plans': {key: deepcopy(plan) for key, plan in plans.items()
                             if plan['mode'] == 'plan' and plan['result'] == 'not_run'},
        'limits': ['Action ordering is tool repair before evidence questions, not an engineering risk ranking.',
            'The engineer selects the next investigation and nominates responsible parties.',
            'Source notes guide methods; they do not establish project capability, authority or policy.',
            'No finding, requirement or evaluation result was changed; no plan was executed.',
            'A documentary pass does not mean there are no real-world evidence gaps.'],
        'validation': 'not_performed', 'acceptance': 'not_evaluated'}
