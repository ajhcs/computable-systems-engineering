"""One inventory of independently distributable skill copies.

Keep copies for standalone use; verify equality rather than replacing them with
runtime imports that would make one skill depend on another skill's directory.
"""
from hashlib import sha256
from .foundation import read_regular

DRAFTING = ('develop-system-concept','develop-conops','develop-operational-scenarios')
COPY_GROUPS = {
    'operational-helper': tuple('skills/'+s+'/scripts/conops.py' for s in DRAFTING[1:]),
    'operational-contract': tuple('skills/'+s+'/references/record.md' for s in DRAFTING[1:]),
    'launcher': tuple('skills/'+s+'/scripts/cse.py' for s in DRAFTING),
    'sysml-contract': tuple('skills/'+s+'/references/sysml.md' for s in DRAFTING),
    'work-review': tuple('skills/'+s+'/references/work-review.md' for s in (*DRAFTING,'generate-engineering-diagrams')),
}


def check_copies(root):
    groups={};status='pass'
    for key,paths in COPY_GROUPS.items():
        try:
            digests={p:sha256(read_regular(root/p,1_000_000)).hexdigest() for p in paths}
            state='pass' if len(set(digests.values()))==1 else 'fail'
            groups[key]={'status':state,'canonical':paths[0],'sha256':digests}
            if state!='pass' and status!='error':status=state
        except (OSError,ValueError) as exc:
            groups[key]={'status':'error','detail':str(exc)};status='error'
    return {'version':'standalone-copy-inventory-1.0','status':status,'groups':groups,
            'claim_scope':'declared_standalone_copy_equality_only',
            'acceptance':'not_evaluated'}
