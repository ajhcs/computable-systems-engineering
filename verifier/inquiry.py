"""Source-bound question views and conditional capacity arithmetic in native models.

CSE-INQUIRY is a bounded structured documentation contract, not executable SysML
behavior. Source quotes/hashes establish provenance, not interpretation truth.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
import re

from .core import _pairs
from .foundation import Invalid, ID, _object, _text, read_regular
from .sysml import check_sysml
from . import flow_consistency

VERSION = 'inquiry-1.1'
MARKER = 'CSE-INQUIRY/1.0'
MAX_ITEMS = 64
DECIMAL = re.compile(r'[0-9]{1,32}(?:\.[0-9]{1,32})?\Z')
QUERIES = {'inquiry.answer': {'input': MARKER, 'claim': 'declared_conditional_function_capacity',
    'entrypoint': 'question answer', 'sources': 'explicit ID=PATH inputs only',
    'model_selected_executor': False}}
LIMITS = ('Capacity arithmetic is conditional on declared capability, rates and composition assumptions. '
          'It does not qualify real capability/capacity, scheduling, continuity, recovery or safety. '
          'Source bytes/quotes do not validate their interpretation or authenticate decisions.')


def _map(value, where):
    if type(value) is not dict or len(value) > MAX_ITEMS or any(type(k) is not str or not ID.fullmatch(k) for k in value):
        raise Invalid(f'{where} needs at most {MAX_ITEMS} valid distinct IDs')


def _label(text, where):
    _text(text, where)
    if len(text) > 120 or any(ord(c) < 32 for c in text):
        raise Invalid(f'{where} needs a single-line label of at most 120 characters')


def _basis(value, where):
    if value is not None and (type(value) is not str or not ID.fullmatch(value)):
        raise Invalid(f'{where} needs a source ID or null')


def _quantity(value, where):
    if value is None: return
    _object(value, ('value','unit','basis'), where)
    if type(value['value']) is not str or not DECIMAL.fullmatch(value['value']):
        raise Invalid(f'{where}.value needs a nonnegative exact decimal string with <=32 whole/fraction digits')
    if type(value['unit']) is not str or not ID.fullmatch(value['unit']):
        raise Invalid(f'{where}.unit needs an explicit nominal unit ID; no conversion is inferred')
    _basis(value['basis'],where+'.basis')


def schema(record):
    if type(record) is not dict:raise Invalid('Inquiry record must be an object')
    fields=('version','question','sources','functions','resources','alternatives')
    _object(record, fields+(('flow_checks',) if record.get('version')=='inquiry-1.1' else ()), 'inquiry',required=fields)
    if len(json.dumps(record,ensure_ascii=False,allow_nan=False).encode())>1_000_000:raise Invalid('Inquiry record exceeds 1 MB')
    if record['version'] not in ('inquiry-1.0',VERSION): raise Invalid('Unsupported inquiry record version')
    _object(record['question'], ('text','basis'), 'question');_text(record['question']['text'],'question.text')
    _basis(record['question']['basis'],'question.basis')
    for group in ('sources','functions','resources','alternatives'): _map(record[group],group)
    if set(record['functions']) & set(record['resources']): raise Invalid('Function and resource IDs must be distinct')
    for key,s in record['sources'].items():
        _object(s,('sha256','excerpt','kind'),key)
        if type(s['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',s['sha256']): raise Invalid(key+' needs a lowercase source SHA-256')
        _text(s['excerpt'],key+'.excerpt')
        if s['kind'] not in ('provided','assumption','proposal','reported_observation'): raise Invalid(key+' has unsupported source classification')
    for key,f in record['functions'].items():
        _object(f,('native_name','label','demand','minimum_assignments','minimum_basis'),key)
        _text(f['native_name'],key+'.native_name');_label(f['label'],key+'.label');_quantity(f['demand'],key+'.demand')
        if f['minimum_assignments'] is not None and (type(f['minimum_assignments']) is not int or not 0 <= f['minimum_assignments'] <= 512):
            raise Invalid(key+' minimum assignment count needs 0..512 or null')
        _basis(f['minimum_basis'],key+'.minimum_basis')
    for key,r in record['resources'].items():
        _object(r,('native_name','label'),key);_text(r['native_name'],key+'.native_name');_label(r['label'],key+'.label')
    for key,a in record['alternatives'].items():
        _object(a,('label','assignments','composition','concurrency_basis'),key);_label(a['label'],key+'.label')
        if type(a['assignments']) is not list or len(a['assignments'])>512: raise Invalid(key+' needs at most 512 assignments')
        _map(a['composition'],key+'.composition');_basis(a['concurrency_basis'],key+'.concurrency_basis')
        for p in a['assignments']:
            _object(p,('function','resource','capability','capability_basis','capacity','rationale','rationale_basis'),key+'.assignment')
            if type(p['function']) is not str or p['function'] not in record['functions'] or type(p['resource']) is not str or p['resource'] not in record['resources']:
                raise Invalid(key+' assignment refers outside the declared function/resource scope')
            if p['capability'] not in ('capable','incapable','unknown'): raise Invalid(key+' needs declared capable/incapable/unknown')
            _basis(p['capability_basis'],key+'.capability_basis');_quantity(p['capacity'],key+'.capacity')
            _text(p['rationale'],key+'.rationale');_basis(p['rationale_basis'],key+'.rationale_basis')
        if len({(p['function'],p['resource']) for p in a['assignments']}) != len(a['assignments']): raise Invalid(key+' has duplicate assignments')
        for f,c in a['composition'].items():
            if f not in record['functions']: raise Invalid(key+' composition refers outside the function scope')
            _object(c,('method','basis'),key+'.composition');_text(c['method'],key+'.method');_basis(c['basis'],key+'.basis')
    flows=record.get('flow_checks',{})
    _map(flows,'flow_checks')
    flow_consistency.schema(flows,record,_quantity,_label,_basis)


def _status(statuses):
    order={'pass':0,'unknown':1,'fail':2,'unsupported':3,'error':4}
    return max(statuses,default='pass',key=lambda s:order.get(s,4))


def decimal(value):
    """Exact finite decimal display for arithmetic on admitted decimal literals."""
    negative=value<0;value=abs(value);d=value.denominator;k=0
    while (10**k)%d:
        k+=1
        if k>32:raise Invalid('Computed value lacks a finite decimal within the admitted 32 places')
    digits=str(value.numerator*(10**k//d)).rjust(k+1,'0')
    text=digits if not k else (digits[:-k]+'.'+digits[-k:]).rstrip('0').rstrip('.')
    return ('-' if negative else '')+text


def _base(alternative, unavailable):
    return {'version':VERSION,'status':'unknown','claim_scope':'declared_conditional_function_capacity',
            'request':{'alternative':alternative,'unavailable':deepcopy(unavailable)},
            'model_sha256':None,'sources':{},'native_status':'not_run','findings':[],
            'alternatives':{},'evaluation':'not_run','evaluated_hypothesis':None,'operational_continuity':'unknown',
            'behavior':'not_run','required_review':'not_evaluated','acceptance':'not_evaluated','limits':LIMITS}


def analyze(record,native,source_evidence,alternative=None,unavailable=None):
    unavailable=[] if unavailable is None else unavailable
    report=_base(alternative,unavailable);report['model_sha256']=native.get('model_sha256');report['native_status']=native.get('status','error')
    report['native_parser']=native.get('parser');report['sources']=deepcopy(source_evidence)
    def issue(rule,status,ids,detail): report['findings'].append({'rule':rule,'status':status,'ids':ids,'detail':detail})
    try: schema(record)
    except (ValueError,TypeError,KeyError,RecursionError) as exc:
        issue('record_schema','error',[],str(exc));report['status']='error';return report
    report['record']=deepcopy(record)
    report['question']=deepcopy(record['question']);report['record_sha256']=sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if native.get('status')!='pass':
        report['status']=native.get('status','error');issue('native_basis',report['status'],[],'Native parser/shape checks did not pass');return report
    if alternative is not None and alternative not in record['alternatives']:
        issue('query_selection','error',[],'Selected alternative is absent')
    if type(unavailable) is not list or len(unavailable)>MAX_ITEMS or any(type(r) is not str or r not in record['resources'] for r in unavailable) or len(set(unavailable))!=len(unavailable):
        issue('query_selection','error',[],'Unavailable IDs must be distinct resources in the declared question scope')
    for group,category in (('functions','actions'),('resources','parts')):
        identities=[]
        for key,e in record[group].items():
            matches=[x for x in native.get('inventory',{}).get(category,[]) if x.get('qualified_name')==e['native_name']]
            if len(matches)!=1: issue('native_binding','fail',[key],'Expected one parsed native element of the admitted kind')
            identities.append(e['native_name'])
        if len(set(identities))!=len(identities): issue('native_identity','fail',list(record[group]),'Aliases cannot duplicate a native identity in the shared question scope')
    def references(value):
        if type(value) is dict:
            for key,v in value.items():
                if (key=='basis' or key.endswith('_basis')) and v is not None and v not in record['sources']:
                    issue('basis_reference','fail',[], 'Referenced source '+str(v)+' is absent')
                else: references(v)
        elif type(value) is list:
            for v in value:references(v)
    references({k:record[k] for k in ('question','functions','alternatives')})
    references(record.get('flow_checks',{}))
    for key,s in record['sources'].items():
        evidence=source_evidence.get(key)
        if not evidence: issue('source_missing','unknown',[key],'Supply the referenced source explicitly; model records cannot open files')
        elif evidence['status']!='pass': issue('source_binding',evidence['status'],[key],evidence['detail'])
    if report['findings']:
        report['status']=_status(x['status'] for x in report['findings']);return report
    flows=record.get('flow_checks',{})
    if flows:
        report['claim_scope']='declared_conditional_resource_analysis'
        report['flow_checks']=flow_consistency.analyze(flows,record['sources'],decimal)
        if record['question']['basis'] is None:
            issue('basis_unknown','unknown',[],'Record the source or assumption for the engineering question.')
        if not record['functions'] and not record['alternatives']:
            report['evaluation']='completed'
            report['evaluated_hypothesis']={'kind':'declared_mean_flow_conditions',
                'unavailable':[],'question_conditions_inferred':False}
            report['status']=_status([r['status'] for r in report['flow_checks'].values()]+[f['status'] for f in report['findings']])
            return report
    if not record['functions'] or not record['alternatives']:
        issue('scope_missing','unknown',[],'Identify the work, its workload/unit and the available means; a bare question remains a draft')
        report['status']='unknown';return report
    def require_basis(basis,where,issues):
        if basis is None: issues.append({'rule':'basis_unknown','status':'unknown','ids':[where],'detail':'Record the source or explicit assumption for '+where});return False
        if basis not in record['sources']:
            issues.append({'rule':'basis_reference','status':'fail','ids':[where,basis],'detail':'Referenced source is absent'});return False
        return True
    question_issues=[];require_basis(record['question']['basis'],'the engineering question',question_issues)
    resource_labels={k:v['label'] for k,v in record['resources'].items()}
    resource_labels={k:(record['resources'][k]['native_name'] if list(resource_labels.values()).count(label)>1 else label) for k,label in resource_labels.items()}
    function_labels={k:v['label'] for k,v in record['functions'].items()}
    function_labels={k:(record['functions'][k]['native_name'] if list(function_labels.values()).count(label)>1 else label) for k,label in function_labels.items()}
    report['evaluated_hypothesis']={'unavailable':sorted(unavailable),
        'availability':'All declared means assumed available except these selected losses',
        'question_conditions_inferred':False}
    report['unavailable_resources']=[{'id':r,'label':resource_labels[r],'native_name':record['resources'][r]['native_name']} for r in sorted(unavailable)]
    chosen=[alternative] if alternative else sorted(record['alternatives'])
    for aid in chosen:
        a=record['alternatives'][aid];rows=[];alt_issues=deepcopy(question_issues)
        remaining=[p for p in a['assignments'] if p['resource'] not in unavailable]
        shared={r for r in record['resources'] if len({p['function'] for p in remaining if p['resource']==r})>1}
        for fid,f in sorted(record['functions'].items()):
            before=[p for p in a['assignments'] if p['function']==fid];pairs=[p for p in remaining if p['function']==fid]
            issues=[];assignment_issues=[];assignment_status='pass';capacity_status='unknown';total=None
            minimum=f['minimum_assignments']
            if minimum is None or not require_basis(f['minimum_basis'],'assignment minimum for '+f['label'],assignment_issues):
                assignment_status='unknown'
                if minimum is None:assignment_issues.append({'rule':'minimum_unknown','status':'unknown','ids':[fid],'detail':'Supply the declared assignment minimum for '+f['label']})
            elif len(pairs)<minimum:
                assignment_status='fail'
                assignment_issues.append({'rule':'assignment_shortfall','status':'fail','ids':[fid],
                    'detail':f"{f['label']} has {len(pairs)} remaining assignments against unchanged minimum {minimum}; gap {minimum-len(pairs)}"})
            demand=f['demand']
            if demand is None: issues.append({'rule':'demand_unknown','status':'unknown','ids':[fid],'detail':'Supply workload and unit for '+f['label']})
            else:require_basis(demand['basis'],'workload for '+f['label'],issues)
            capable=[]
            for p in pairs:
                require_basis(p['rationale_basis'],'assignment rationale for '+resource_labels[p['resource']],issues)
                require_basis(p['capability_basis'],'declared capability of '+resource_labels[p['resource']],issues)
                if p['capability']=='unknown':issues.append({'rule':'capability_unknown','status':'unknown','ids':[fid,p['resource']],'detail':'Establish what '+resource_labels[p['resource']]+' can do for '+f['label']})
                elif p['capability']=='capable':
                    capable.append(p)
                    if p['capacity'] is None:issues.append({'rule':'capacity_unknown','status':'unknown','ids':[fid,p['resource']],'detail':'Supply the rate/capacity and operating conditions for '+resource_labels[p['resource']]})
                    else:
                        require_basis(p['capacity']['basis'],'capacity for '+resource_labels[p['resource']],issues)
                        if demand is not None and p['capacity']['unit']!=demand['unit']:
                            issues.append({'rule':'unit_incompatible','status':'unsupported','ids':[fid,p['resource']],'detail':'Capacity/workload units differ; no conversion is supported'})
            if shared & {p['resource'] for p in pairs}:
                require_basis(a['concurrency_basis'],'simultaneous per-function rates for shared means',issues)
            composition=a['composition'].get(fid)
            if composition is not None and composition['method'] not in ('sum','single','unknown'):
                issues.append({'rule':'composition_unsupported','status':'unsupported','ids':[fid],'detail':'The declared capacity combination is not supported'})
            if len(capable)>1:
                composition=a['composition'].get(fid)
                if composition is None or composition['method']=='unknown':issues.append({'rule':'composition_unknown','status':'unknown','ids':[fid],'detail':'Decide whether capacities for '+f['label']+' are independently additive'})
                elif composition['method']!='sum':issues.append({'rule':'composition_unsupported','status':'unsupported','ids':[fid],'detail':'Only explicitly additive independent capacities are supported; no provider is chosen automatically'})
                else:require_basis(composition['basis'],'independent additive capacity for '+f['label'],issues)
            if not issues and demand is not None:
                total=sum((Fraction(p['capacity']['value']) for p in capable),Fraction(0))
                capacity_status='pass' if total>=Fraction(demand['value']) else 'fail'
            else:capacity_status=_status(x['status'] for x in issues)
            rows.append({'id':fid,'label':function_labels[fid],'native_name':f['native_name'],
                'assignments_before':len(before),'assignments_remaining':len(pairs),'minimum_assignments':minimum,
                'assignment_gap':None if minimum is None else max(0,minimum-len(pairs)),
                'assignment_status':assignment_status,'declared_capable_remaining':len(capable),
                'demand':deepcopy(demand),'capacity':None if total is None else {'value':decimal(total),'unit':demand['unit']},
                'margin':None if total is None else {'value':decimal(total-Fraction(demand['value'])),'unit':demand['unit']},
                'capacity_assumptions':(['Per-function rates for shared means are assumed simultaneously attainable.'] if shared & {p['resource'] for p in pairs} and a['concurrency_basis'] is not None else [])+
                    (['These separate providers are assumed independently additive.'] if len(capable)>1 and composition is not None and composition['method']=='sum' else []),
                'capacity_status':capacity_status,'remaining_assignments':[{**deepcopy(p),'resource_label':resource_labels[p['resource']]} for p in pairs],
                'findings':assignment_issues+issues,'status':_status([assignment_status,capacity_status])})
            alt_issues.extend(assignment_issues+issues)
        status=_status([r['status'] for r in rows]+[x['status'] for x in alt_issues])
        report['alternatives'][aid]={'label':a['label'],'status':status,'functions':rows,'findings':alt_issues,
            'removed_assignments':[deepcopy(p) for p in a['assignments'] if p['resource'] in unavailable]}
    report['findings']+=question_issues
    report['evaluation']='completed'
    report['status']=_status([a['status'] for a in report['alternatives'].values()]+
        [f['status'] for f in report.get('flow_checks',{}).values()]+[f['status'] for f in report['findings']])
    report['summary']={s:[k for k,a in report['alternatives'].items() if a['status']==s] for s in ('pass','fail','unknown','unsupported','error')}
    return report


def inspect_inquiry(model_path,source_paths,alternative=None,unavailable=None):
    report=_base(alternative,[] if unavailable is None else unavailable)
    report['input_paths']={'model':str(model_path),'sources':{str(k):str(v) for k,v in source_paths.items()} if type(source_paths) is dict else {}}
    paths=deepcopy(report['input_paths'])
    try:
        before=read_regular(model_path,5_000_000);report['model_sha256']=sha256(before).hexdigest()
        native=check_sysml(model_path,syntax_only=True,kind='concept')
        report['native_status']=native.get('status','error');report['native_parser']=native.get('parser')
        if native.get('status')!='pass':
            report['status']=native.get('status','error');report['findings']=native.get('findings',[]);return report
        docs=[d for d in native['inventory']['documents'] if d.get('name')=='cseInquiry']
        if len(docs)!=1:raise Invalid('Expected exactly one cseInquiry document in this question model')
        if not any(x.get('qualified_name')==docs[0]['owner'] for x in native['inventory']['concerns']):raise Invalid('cseInquiry must document a parsed concern')
        lines=docs[0]['body'].strip().splitlines()
        if not lines or lines[0].strip()!=MARKER:raise Invalid('Unsupported inquiry document header')
        payload='\n'.join(lines[1:]);
        if len(payload.encode())>1_000_000:raise Invalid('Inquiry record exceeds 1 MB')
        record=json.loads(payload,object_pairs_hook=_pairs,parse_constant=lambda x:(_ for _ in ()).throw(Invalid('Nonfinite value')))
        schema(record)
        if type(source_paths) is not dict or any(k not in record['sources'] for k in source_paths):raise Invalid('Only explicit declared source IDs can be supplied')
        evidence={};report['sources']=evidence;source_bytes={}
        for sid,path in source_paths.items():
            s=record['sources'][sid]
            evidence[sid]={'path':str(path),'expected_sha256':s['sha256'],'actual_sha256':None,'kind':s['kind'],
                           'excerpt':s['excerpt'],'status':'error','detail':'Source acquisition did not complete'}
            raw=read_regular(path,1_000_000);source_bytes[sid]=raw;actual=sha256(raw).hexdigest();evidence[sid]['actual_sha256']=actual
            text=raw.decode('utf-8');status='pass';detail='Bytes and unique source excerpt match; interpretation is not verified'
            if actual!=s['sha256']:status='fail';detail='Referenced source revision is stale'
            elif text.count(s['excerpt'])!=1:status='fail';detail='Source excerpt must occur exactly once in supplied source'
            evidence[sid]={'path':str(path),'expected_sha256':s['sha256'],'actual_sha256':actual,'kind':s['kind'],
                           'excerpt':s['excerpt'],'status':status,'detail':detail}
        report=analyze(record,native,evidence,alternative,unavailable)
        report['input_paths']=paths
        report['document_owner']=docs[0]['owner']
        if read_regular(model_path,5_000_000)!=before or native.get('model_sha256')!=sha256(before).hexdigest() or any(read_regular(source_paths[s],1_000_000)!=raw for s,raw in source_bytes.items()):
            report.pop('flow_checks',None)
            report['status']='error';report['evaluation']='not_run';report['alternatives']={};report['evaluated_hypothesis']=None;report.pop('summary',None)
            report['input_stability']='error'
            report['findings'].append({'rule':'inputs_changed','status':'error','ids':[],'detail':'Model/source changed during check or parser digest mismatched'})
        else:report['input_stability']='pass'
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as exc:
        report.pop('flow_checks',None)
        report['input_paths']=paths;report['input_stability']='not_completed';report.pop('summary',None)
        report['status']='error';report['evaluation']='not_run';report['alternatives']={};report['evaluated_hypothesis']=None
        report['findings'].append({'rule':'input_or_record','status':'error','ids':[],'detail':str(exc)})
    return report


def render_text(report,expert=False):
    lines=['Recorded question: '+report.get('question',{}).get('text','Engineering question')]
    flow_only=bool(report.get('flow_checks')) and not report['alternatives']
    if flow_only:
        lines.append('Hypothesis: explicitly declared mean-flow conditions; resource availability is not evaluated.')
    elif report.get('evaluated_hypothesis') is None:
        lines.append('Hypothesis not evaluated; received query and input/scope findings are retained.')
    elif report.get('unavailable_resources'):
        lines.append('Hypothesis: '+', '.join(r['label'] for r in report['unavailable_resources'])+' unavailable.')
        lines.append('Other declared means are assumed available for this calculation.')
    else:
        lines.append('Hypothesis: no resources selected unavailable; all declared means are assumed available.')
    lines.append('Results apply to this selected hypothesis. Conditions in the recorded question are not inferred from its text.')
    lines.append((f"Selected resource analyses: {report['status']} (conditional)." if report.get('flow_checks') else
                  f"Selected alternative checks: {report['status']} (conditional)."))
    for flow in report.get('flow_checks',{}).values():
        lines.append('Flow consistency: '+flow['label']+' — '+flow['status']+' (conditional; applicability not independently validated).')
        if flow['predicted_L'] is not None:
            lines.append('  Predicted mean count '+flow['predicted_L']['value']+' '+flow['predicted_L']['unit']+'; tolerance and declared conditions are retained in JSON.')
    for aid,a in report['alternatives'].items():
        collision=sum(x['label']==a['label'] for x in report['alternatives'].values())>1
        lines.append(a['label']+(' ['+aid+']' if expert or collision else '')+': '+a['status']+'.')
        for r in a['functions']:
            minimum='unknown' if r['minimum_assignments'] is None else str(r['minimum_assignments'])
            wording='assignment remains' if r['assignments_remaining']==1 else 'assignments remain'
            lines.append(f"  {r['label']}: {r['assignments_remaining']} {wording}; minimum {minimum} — {r['assignment_status']}.")
            if r['capacity'] is not None:
                unit=r['demand']['unit'].replace('_per_','/')
                lines.append(f"  Declared capacity {r['capacity']['value']} versus workload {r['demand']['value']} {unit} — {r['capacity_status']}.")
                margin=Fraction(r['margin']['value'])
                lines.append('  '+('Shortfall '+decimal(-margin) if margin<0 else 'Declared headroom '+decimal(margin))+' '+unit+'.')
            else:lines.append('  Capacity answer: '+r['capacity_status']+'.')
            for assumption in r['capacity_assumptions']:lines.append('  Assumption: '+assumption)
            for p in r['remaining_assignments']:lines.append('  '+p['resource_label']+' (declared '+p['capability']+'): '+p['rationale'])
            if r['assignment_status']=='fail':
                lines.append(f"  Next decision: {r['label']} needs {r['assignment_gap']} additional distinct assignments to meet unchanged minimum {r['minimum_assignments']}, or an explicit engineering proposal to revise that criterion. Adequate rate does not close this assignment gap.")
            if r['capacity_status']=='fail':lines.append('  Next decision: investigate additional capable means or revise the workload through an explicit engineering decision.')
            elif r['capacity_status']=='pass':lines.append('  Next decision: confirm capability/rate assumptions and operating conditions with appropriate evidence.')
    findings=report.get('findings',[])+[f for a in report['alternatives'].values() for f in a['findings']]+[f for flow in report.get('flow_checks',{}).values() for f in flow['findings']]
    seen=set()
    for f in findings:
        if f.get('rule')=='assignment_shortfall':continue
        if f['detail'] not in seen:lines.append('Next fact: '+f['detail']);seen.add(f['detail'])
    if len(report['alternatives'])>1:
        met=[a['label'] for a in report['alternatives'].values() if a['status']=='pass']
        lines.append('Alternatives meeting the declared checks: '+(', '.join(met) if met else 'none established')+'. No selection is made.')
    lines.append('Actual process applicability and operational qualification are not established; staffing adequacy is not evaluated.' if flow_only else
        'Actual capability/capacity qualification and operational continuity: unknown. Behavior not run; engineering review/acceptance not established.')
    if expert:
        lines.append('Model SHA-256: '+str(report.get('model_sha256')))
        for sid,s in sorted(report['sources'].items()):lines.append(sid+': expected '+s['expected_sha256']+', actual '+str(s['actual_sha256'])+'; '+s['status'])
    lines.append('Received query and available model/source evidence are inspectable in JSON.'+
                 (' Native bindings and conditional arithmetic are also retained.' if report['alternatives'] or report.get('flow_checks') else ' Calculation was not completed.'))
    return '\n'.join(lines)


def draft_model(record,package):
    schema(record)
    if not ID.fullmatch(package):raise Invalid('Draft package needs a plain ASCII identifier')
    names=[]
    for group in ('functions','resources'):
        for e in record[group].values():
            prefix=package+'::';name=e['native_name'][len(prefix):] if e['native_name'].startswith(prefix) else ''
            if not ID.fullmatch(name):raise Invalid('Draft generation supports direct members in the selected package only')
            names.append(name)
    if len(set(names))!=len(names) or any(n in ('Resource','EngineeringQuestion') for n in names):raise Invalid('Draft native names collide or use scaffold-reserved names')
    payload=json.dumps(record,indent=2,ensure_ascii=False)
    if len(payload.encode())>1_000_000:raise Invalid('Generated inquiry record exceeds 1 MB')
    payload=payload.replace('*/','*\\u002f')
    statements=['package '+package+' {','    part def Resource;']
    statements += ['    part '+r['native_name'].split('::')[-1]+' : Resource;' for r in record['resources'].values()]
    statements += ['    action def '+f['native_name'].split('::')[-1]+';' for f in record['functions'].values()]
    statements += ['    concern <Q> EngineeringQuestion {','        doc cseInquiry /*',MARKER,payload,'        */','    }','}']
    return '\n'.join(statements)+'\n'


def write_draft(path,text):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:stream.write(text)
