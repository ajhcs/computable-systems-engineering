"""Project-selected ownership/agreement documentation; no approval enforcement."""
from copy import deepcopy
import json
import re
from .core import _pairs
from .foundation import Invalid,_object

VERSION='ownership-1.0'
MARKER='CSE-OWNERSHIP/1.0'
ROLES={'own','operate','fund','change','support','accept'}
FIELDS={'agreement','change_control','withdrawal','handoff','evaluation'}
ID=re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}\Z')


def ids(value,where):
    if type(value) is not list or len(value)>64 or any(type(x) is not str or not ID.fullmatch(x) for x in value) or len(set(value))!=len(value):
        raise Invalid(where+' needs a bounded distinct ID list')


def expectation(value):
    _object(value,('topic','kind','target','target_kind','roles','fields'),'ownership expectation')
    ids([value['target']],'target')
    if value['target_kind'] not in ('element','interface'):raise Invalid('Unsupported ownership target kind')
    if type(value['roles']) is not dict or set(value['roles'])-ROLES:raise Invalid('Unsupported selected ownership role')
    for role,parties in value['roles'].items():ids(parties,role)
    ids(value['fields'],'selected ownership fields')
    if set(value['fields'])-FIELDS or not (value['roles'] or value['fields']):raise Invalid('Select relevant ownership roles or facts')


def _claim(claim,keys,where):
    _object(claim,keys,where)
    if claim['status'] not in ('proposed','reported','unknown','withdrawn'):raise Invalid('Unsupported ownership claim state')
    if claim['basis'] is not None:ids([claim['basis']],where+' basis')


def schema(register):
    _object(register,('version','items'),'ownership register')
    if register['version']!=VERSION:raise Invalid('Unsupported ownership profile version')
    if type(register['items']) is not dict or len(register['items'])>64 or any(not ID.fullmatch(k) for k in register['items']):
        raise Invalid('Ownership items need a bounded ID map')
    for key,item in register['items'].items():
        _object(item,('target_kind','roles','facts'),key)
        if item['target_kind'] not in ('element','interface'):raise Invalid('Unsupported ownership target kind')
        if type(item['roles']) is not dict or set(item['roles'])-ROLES:raise Invalid('Unsupported ownership role')
        if type(item['facts']) is not dict or set(item['facts'])-FIELDS:raise Invalid('Unsupported ownership fact')
        for role,claim in item['roles'].items():
            _claim(claim,('parties','status','basis'),key+'.'+role);ids(claim['parties'],role)
        for field,claim in item['facts'].items():
            _claim(claim,('text','status','basis','refs'),key+'.'+field)
            if type(claim['text']) is not str or len(claim['text'])>4096:raise Invalid('Ownership fact text exceeds its contract')
            ids(claim['refs'],field+' references')
    return register


def inspect_ownership(workflow,selected):
    result={'version':VERSION,'status':'error','findings':[],'items':{},
        'claim_scope':'selected_ownership_and_interface_agreement_documentation',
        'actual_commitments':'not_authenticated','protected_authority':'not_evaluated','operational_continuity':'not_evaluated'}
    def issue(rule,status,ids,detail):result['findings'].append({'rule':rule,'status':status,'ids':ids,'detail':detail})
    try:
        docs=workflow.get('supplemental_documents',{}).get('cseOwnership',[])
        if not docs:
            issue('ownership_register_missing','fail',list(selected),'The selected ownership register is absent.');return result
        if len(docs)!=1:raise Invalid('Exactly one selected ownership document is required')
        doc=docs[0]
        if sum(x.get('qualified_name')==doc.get('owner') for x in workflow['native_inventory']['concerns'])!=1:
            raise Invalid('Ownership document must belong to one parsed concern')
        lines=doc['body'].strip().splitlines()
        if not lines or lines[0].strip()!=MARKER:
            issue('ownership_profile','unsupported',list(selected),'Unsupported ownership document header.');return result
        payload='\n'.join(lines[1:])
        if len(payload.encode())>1_000_000:raise Invalid('Ownership register exceeds 1 MB')
        register=json.loads(payload,object_pairs_hook=_pairs,parse_constant=lambda x:(_ for _ in ()).throw(Invalid('Nonfinite ownership data')))
        if type(register) is dict and register.get('version')!=VERSION:
            issue('ownership_profile','unsupported',list(selected),'Unsupported ownership profile version.');return result
        schema(register)
        record=workflow['record'];elements=record['elements'];relations=record['relations']
        for target,item in register['items'].items():
            if item['target_kind']=='element':
                if target not in elements or elements[target]['kind'] not in ('system','element'):
                    issue('ownership_target','fail',[target],'Owned constituent lacks a bound element/system identity.')
            elif target not in relations or relations[target]['kind']!='interfaces_with':
                issue('ownership_target','fail',[target],'Owned interface lacks a checked documentary interface relation.')
            for role,claim in item['roles'].items():
                if claim['basis'] is not None and claim['basis'] not in record['sources']:
                    issue('ownership_source_missing','fail',[target,role,claim['basis']],'Role basis references an absent source.')
                for party in claim['parties']:
                    if party not in elements or elements[party]['kind'] not in ('actor','system','element'):
                        issue('ownership_party','fail',[target,role,party],'Responsible party lacks an admitted native-bound identity.')
            for field,claim in item['facts'].items():
                if claim['basis'] is not None and claim['basis'] not in record['sources']:
                    issue('ownership_source_missing','fail',[target,field,claim['basis']],'Fact basis references an absent source.')
                for ref in claim['refs']:
                    if ref not in elements and ref not in relations and ref not in record['evidence']:
                        issue('ownership_reference','fail',[target,field,ref],'Referenced ownership context/evidence is absent.')
        def claim_check(claim,target,field):
            if claim['status']=='unknown' or claim['basis'] is None:
                issue('ownership_unknown','unknown',[target,field],'Responsibility/agreement fact or its basis remains unresolved.')
            if claim['status']=='withdrawn':
                issue('ownership_withdrawn','fail',[target,field],'A selected responsibility/agreement is recorded as withdrawn.')
            if claim['basis'] is not None:
                if workflow.get('sources',{}).get(claim['basis'],{}).get('status')!='pass':
                    issue('ownership_source_unchecked','unknown',[target,field,claim['basis']],'Supply/check the selected claim basis; declaration alone is not provenance.')
                if claim['status']=='reported' and record['sources'].get(claim['basis'],{}).get('kind')!='reported_observation':
                    issue('ownership_report_basis','fail',[target,field],'A proposal cannot be relabelled as a reported commitment.')
        for expected_id,expected in selected.items():
            target=expected['target'];actual=register['items'].get(target)
            if actual is None:
                issue('ownership_item_missing','fail',[expected_id,target],'A selected ownership/interface item was removed.');continue
            if actual['target_kind']!=expected['target_kind']:
                issue('ownership_target_changed','fail',[expected_id,target],'Expected constituent/interface scope changed.')
            for role,parties in expected['roles'].items():
                claim=actual['roles'].get(role)
                if claim is None:issue('ownership_role_missing','fail',[expected_id,target,role],'A selected responsibility is absent.');continue
                if set(claim['parties'])!=set(parties):issue('ownership_party_changed','fail',[expected_id,target,role],'Expected responsible party identities changed.')
                if not claim['parties']:issue('ownership_unknown','unknown',[target,role],'Identify the proposed responsible party/parties.')
                claim_check(claim,target,role)
            for field in expected['fields']:
                claim=actual['facts'].get(field)
                if claim is None:issue('ownership_fact_missing','fail',[expected_id,target,field],'A selected agreement/change/withdrawal fact is absent.');continue
                if not claim['text'].strip():issue('ownership_unknown','unknown',[target,field],'Explain the selected fact.')
                claim_check(claim,target,field)
            result['items'][target]={'target_kind':actual['target_kind'],'roles':{k:deepcopy(v) for k,v in actual['roles'].items() if k in expected['roles']},
                'facts':{k:deepcopy(v) for k,v in actual['facts'].items() if k in expected['fields']}}
    except (ValueError,TypeError,KeyError,RecursionError) as exc:
        issue('ownership_input','error',list(selected),str(exc))
    finally:
        states={x['status'] for x in result['findings']}
        result['status']=next((s for s in ('error','fail','unsupported','unknown') if s in states),'pass')
    return result
