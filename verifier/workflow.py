"""Bounded engineering workflow views carried in an authoritative native model.

Documentary relationships and reported assessments are not native behavior,
qualified evidence, an acceptance channel, or an independent required review.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re
import tempfile
from pathlib import Path

from .core import _pairs
from .foundation import Invalid, _object, read_regular
from .sysml import check_sysml, ROOT

VERSION = 'workflow-1.0'
MARKER = 'CSE-WORKFLOW/1.0'
JOBS = ('concept', 'scenarios', 'requirements', 'architecture', 'trade-study')
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}\Z')
NATIVE_ID = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,63}\Z')
GROUPS = ('sources', 'elements', 'relations', 'workflows', 'decisions', 'questions', 'trade_studies', 'evidence')
KINDS = {'need':'concerns', 'goal':'concerns', 'concept':'concerns', 'criterion':'concerns',
         'actor':'parts', 'system':'parts', 'element':'parts', 'element_definition':'part_definitions', 'function':'actions',
         'scenario':'actions', 'step':'actions', 'requirement':'requirements'}
DECIMAL = re.compile(r'-?[0-9]{1,32}(?:\.[0-9]{1,32})?\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
STATES = ('proposed', 'accepted', 'deferred', 'superseded')
LIMITS = [
    'Checks cover native bindings, documentary structure, supplied-byte provenance and declared draft completeness.',
    'Documentary relationships do not prove native ownership, connections, executable flow or behavior.',
    'Element definitions form a definition-level documentary hierarchy, not instantiated parts or native inheritance.',
    'Trade comparison is qualitative; numeric values and weights are documentary inputs, not calculated scores.',
    'Evidence plans and reported assessments are distinct from independently qualified verification or validation.',
    'Recorded decisions and hashes do not authenticate assent or establish a protected runner.',
    'This adapter checks one explicitly supplied model; imported dependencies outside it are not frozen.',
]


def _string(value, where, empty=True, cap=4096):
    if type(value) is not str or len(value) > cap or (not empty and not value.strip()):
        raise Invalid(f'{where} needs {"nonempty " if not empty else ""}text of at most {cap} characters')


def _map(value, where, cap=64):
    if type(value) is not dict or len(value) > cap or any(type(k) is not str or not ID.fullmatch(k) for k in value):
        raise Invalid(f'{where} needs at most {cap} distinct valid IDs')


def _ids(value, where):
    if type(value) is not list or len(value) > 64 or any(type(k) is not str or not ID.fullmatch(k) for k in value) or len(set(value)) != len(value):
        raise Invalid(f'{where} needs at most 64 distinct IDs')


def _basis(value, where):
    if value is not None and (type(value) is not str or not ID.fullmatch(value)):
        raise Invalid(f'{where} needs a source ID or null')


def _enum(value, allowed, where):
    if type(value) is not str or value not in allowed:
        raise Invalid(f'{where} has an unsupported value')


def _decimal(value, where, nonnegative=False):
    if value is not None and (type(value) is not str or not DECIMAL.fullmatch(value) or (nonnegative and value.startswith('-'))):
        raise Invalid(f'{where} needs a bounded exact decimal string or null')


def schema(record):
    _object(record, ('version','question',*GROUPS), 'workflow')
    if record['version'] != VERSION: raise Invalid('Unsupported workflow record version')
    _object(record['question'], ('text','basis'), 'question')
    _string(record['question']['text'], 'question.text')
    _basis(record['question']['basis'], 'question.basis')
    all_ids = set()
    for group in GROUPS:
        if group == 'workflows':
            if type(record[group]) is not dict or set(record[group])-set(JOBS): raise Invalid('Unknown workflow token')
        else:
            _map(record[group], group, 512 if group == 'relations' else 64)
            if all_ids & set(record[group]): raise Invalid('New record identities must be globally distinct')
            all_ids.update(record[group])
    for key,s in record['sources'].items():
        _object(s, ('sha256','excerpt','kind'), key)
        if type(s['sha256']) is not str or not DIGEST.fullmatch(s['sha256']): raise Invalid(f'{key} needs SHA-256')
        _string(s['excerpt'], key+'.excerpt', False)
        _enum(s['kind'], ('provided','assumption','proposal','reported_observation'), key+'.kind')
    for key,e in record['elements'].items():
        _object(e, ('kind','native_name','label','description','basis','status'), key)
        _enum(e['kind'], KINDS, key+'.kind')
        _string(e['native_name'], key+'.native_name', False)
        _string(e['label'], key+'.label', False, 120)
        if '\n' in e['label'] or '\r' in e['label']: raise Invalid('Labels must be single-line')
        _string(e['description'], key+'.description'); _basis(e['basis'], key+'.basis')
        _enum(e['status'], STATES, key+'.status')
    for key,r in record['relations'].items():
        _object(r, ('kind','from','to','basis','label'), key)
        for f in ('kind','from','to'): _string(r[f], key+'.'+f, False, 120)
        _basis(r['basis'], key+'.basis'); _string(r['label'], key+'.label', r['kind'] not in ('information_to','controls'), 120)
        if '\n' in r['label'] or '\r' in r['label']: raise Invalid('Relation labels must be single-line')
    for job,w in record['workflows'].items():
        _object(w, ('focus','summary','conditions','outcome','next_decision'), job)
        _ids(w['focus'], job+'.focus')
        for f in ('summary','conditions','outcome','next_decision'): _string(w[f],job+'.'+f)
    for key,d in record['decisions'].items():
        _object(d, ('text','status','by','basis','affects'), key)
        _string(d['text'],key+'.text'); _string(d['by'],key+'.by')
        _enum(d['status'],STATES,key+'.status');_basis(d['basis'],key+'.basis');_ids(d['affects'],key+'.affects')
    for key,q in record['questions'].items():
        _object(q, ('text','affects','blocking'),key)
        _string(q['text'],key+'.text');_ids(q['affects'],key+'.affects')
        if type(q['blocking']) is not bool:raise Invalid('Question blocking flag must be boolean')
    for key,t in record['trade_studies'].items():
        _object(t, ('question','alternatives','criteria','assessments','method','preference_basis','recommendation'),key)
        for f in ('question','method','recommendation'): _string(t[f],key+'.'+f)
        _ids(t['alternatives'],key+'.alternatives');_map(t['criteria'],key+'.criteria');_map(t['assessments'],key+'.assessments')
        _basis(t['preference_basis'],key+'.preference_basis')
        for cid,c in t['criteria'].items():
            _object(c, ('kind','measure','unit','weight','basis'),cid)
            _enum(c['kind'],('constraint','goal'),cid+'.kind')
            _string(c['measure'],cid+'.measure');_string(c['unit'],cid+'.unit')
            _decimal(c['weight'],cid+'.weight',True);_basis(c['basis'],cid+'.basis')
        for aid,cells in t['assessments'].items():
            _map(cells,aid+'.assessments')
            for cid,cell in cells.items():
                _object(cell,('finding','value','basis','uncertainty'),aid+'.'+cid)
                _enum(cell['finding'],('supported','contradicted','unknown'),cid+'.finding')
                _decimal(cell['value'],cid+'.value');_basis(cell['basis'],cid+'.basis');_string(cell['uncertainty'],cid+'.uncertainty')
    for key,e in record['evidence'].items():
        _object(e,('target','purpose','mode','method','environment','basis','result','limitations'),key)
        _string(e['target'],key+'.target',False);_enum(e['purpose'],('verification','validation','qualification','analysis'),key+'.purpose')
        _enum(e['mode'],('plan','assessment'),key+'.mode');_enum(e['result'],('not_run','supported','contradicted','unknown'),key+'.result')
        for f in ('method','environment','limitations'): _string(e[f],key+'.'+f)
        _basis(e['basis'],key+'.basis')
        if e['mode']=='plan' and e['result']!='not_run':raise Invalid('Evidence plans must retain result not_run')
    if len(json.dumps(record,ensure_ascii=False,separators=(',',':')).encode())>1_000_000:raise Invalid('Workflow record exceeds1MB')
    return record


def _status(states):
    states = list(states)
    return next((s for s in ('error','unsupported','fail','unknown','not_run') if s in states),'pass') if states else 'not_run'


def _base(workflow,ids,review):
    return {'version':'workflow-report-1.0','request':{'workflow':workflow,'ids':deepcopy(ids),'review':review},
            'model_sha256':None,'model_files':[],'record_sha256':None,'native_parser':None,'native_status':'not_run',
            'input_stability':'not_run','document_owner':None,'sources':{},'selected_workflow':workflow,'selected_ids':[],
            'record':None,'bindings':{},'native_inventory':{},'findings':[],'checks':[],'status':'not_run',
            'claim_scope':'workflow_document_structure_source_binding_and_declared_draft_completeness',
            'limits':list(LIMITS),'view':{},'required_review':'not_evaluated','acceptance':'not_evaluated',
            'conditional_analysis':'not_run'}



def _native_failure(report,native):
    """Retain native diagnostics in the workflow finding contract."""
    report['status']=native.get('status','error')
    report['findings']=[]
    for original in native.get('findings',[]):
        finding=deepcopy(original)
        finding.setdefault('rule',finding.get('code','native_validation'))
        finding.setdefault('status',report['status'])
        finding.setdefault('ids',[])
        report['findings'].append(finding)
    report['parser_issues']=deepcopy(native.get('parser_issues',[]))
    for issue in report['parser_issues']:
        if issue.get('severity')=='ERROR':
            finding={'rule':'native_parser','status':'error','ids':[],
                'detail':issue.get('message','Native parser refused the model.')}
            for key in ('source','line'):
                if key in issue:finding[key]=issue[key]
            report['findings'].append(finding)
    return report


def analyze(record,native,source_evidence,*,workflow,ids=None,review=False):
    report=_base(workflow,ids,review);report['native_status']=native.get('status','error');report['native_parser']=native.get('parser')
    report['model_sha256']=native.get('model_sha256');report['model_files']=deepcopy(native.get('model_files',[]));report['sources']=deepcopy(source_evidence)
    def issue(rule,status,affected,detail):report['findings'].append({'rule':rule,'status':status,'ids':list(affected),'detail':detail})
    def check(name,status,scope,detail):report['checks'].append({'id':name,'status':status,'scope':scope,'detail':detail})
    if native.get('status')!='pass':
        return _native_failure(report,native)
    check('native','pass','native_syntax','Pinned native syntax checks passed; no behavior executed')
    try:
        schema(record)
        if workflow not in JOBS:raise Invalid('Unknown selected workflow')
        if ids is not None:_ids(ids,'selected IDs')
    except (ValueError,TypeError,KeyError,RecursionError) as exc:
        issue('record_schema','error',[],str(exc));report['status']='error';return report
    report['record']=deepcopy(record);report['record_sha256']=sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    report['native_inventory']=deepcopy({k:[{a:b for a,b in x.items() if a!='body'} for x in v] for k,v in native.get('inventory',{}).items()})
    elements=record['elements'];relations=record['relations'];sources=record['sources'];inventory=native.get('inventory',{})
    aliases=set()
    for key,e in sorted(elements.items()):
        category=KINDS[e['kind']];matches=[x for x in inventory.get(category,[]) if x.get('qualified_name')==e['native_name']]
        if len(matches)!=1:issue('native_binding','fail',[key],'Expected exactly one parsed element of the declared category');continue
        alias=(e['kind'],e['native_name'])
        if alias in aliases:issue('native_alias','fail',[key],'One native identity cannot become two distinct instances of the same role')
        aliases.add(alias);report['bindings'][key]={'id':key,'kind':e['kind'],'native_name':e['native_name'],'native_category':category,**deepcopy(matches[0])}
    def ref(key,kind=None):
        if key not in elements:issue('reference','fail',[key],'Referenced element is absent');return False
        if kind and elements[key]['kind'] not in kind:issue('reference_kind','fail',[key],'Referenced element has the wrong declared kind');return False
        return True
    def basis(value,affected):
        if value is not None and value not in sources:issue('source_reference','fail',affected,'Referenced source ID is absent')
    for ekey,e in elements.items():basis(e['basis'],[ekey])
    basis(record['question']['basis'],[])
    rules={'addresses':({'function','system','element'},{'need','requirement'}),'derives_from':({'requirement'},{'need','goal','requirement'}),
           'allocated_to':({'function'},{'element','system'}),'scenario_of':({'scenario'},{'concept'}),
           'precedes':({'step'},{'step'}),'participates_in':({'actor','system','element'},{'scenario'}),
           'interfaces_with':({'system','element'},{'system','element'}),
           'information_to':({'function','system','element'},{'function','system','element'}),
           'controls':({'need','goal','requirement','criterion','function','system','element'},{'function','system','element'})}
    hierarchy={}
    for key,r in relations.items():
        ok=ref(r['from']) and ref(r['to']);basis(r['basis'],[key])
        if not ok:continue
        left=elements[r['from']]['kind'];right=elements[r['to']]['kind']
        if r['kind']=='decomposes':
            if left!=right or left not in ('function','system','element','element_definition','scenario'):issue('relation_kind','fail',[key],'Decomposition needs same-kind admitted endpoints')
            hierarchy.setdefault(r['from'],[]).append(r['to'])
        elif r['kind'] not in rules:issue('relation_unsupported','unsupported',[key],'Relation kind is not admitted; no fallback graph semantics')
        elif left not in rules[r['kind']][0] or right not in rules[r['kind']][1]:issue('relation_kind','fail',[key],'Relation endpoints have the wrong kinds')
        if r['from']==r['to'] and r['kind']=='decomposes':issue('decomposition_cycle','fail',[key],'Documentary decomposition cannot contain itself')
    colors={}
    def cycle(node):
        if colors.get(node)==1:return True
        if colors.get(node)==2:return False
        colors[node]=1
        if any(cycle(child) for child in hierarchy.get(node,[])):return True
        colors[node]=2
        return False
    if any(cycle(x) for x in hierarchy):issue('decomposition_cycle','fail',[],'Documentary decomposition contains a cycle')
    for job,w in record['workflows'].items():
        for key in w['focus']:ref(key)
    for key,d in record['decisions'].items():
        for target in d['affects']:ref(target)
        basis(d['basis'],[key])
    for key,q in record['questions'].items():
        for target in q['affects']:ref(target)
    for key,t in record['trade_studies'].items():
        for aid in t['alternatives']:ref(aid,{'concept'})
        for cid,c in t['criteria'].items():ref(cid,{'criterion'});basis(c['basis'],[key,cid])
        basis(t['preference_basis'],[key])
        for aid,cells in t['assessments'].items():
            if aid not in t['alternatives']:issue('trade_reference','fail',[key,aid],'Assessment alternative is outside this study')
            for cid,cell in cells.items():
                if cid not in t['criteria']:issue('trade_reference','fail',[key,cid],'Assessment criterion is outside this study')
                basis(cell['basis'],[key,aid,cid])
    for key,e in record['evidence'].items():ref(e['target']);basis(e['basis'],[key,e['target']])
    structural=_status(x['status'] for x in report['findings']);structural='pass' if structural=='not_run' else structural
    check('structure',structural,'documentary_types_references_native_bindings','Checked explicit record types, native identities and documentary references')
    if structural!='pass':report['status']=structural;return report
    if review:
        issue('required_review','unsupported',[],'Independent required review is not admitted by workflow checks; use its separate manifest/evidence contract')
        check('required_review','unsupported','independent_review','Not evaluated');report['status']='unsupported';return report
    w=record['workflows'].get(workflow)
    requested=list(ids) if ids is not None else list(w['focus'] if w else [])
    if any(x not in elements for x in requested):issue('selection','error',requested,'Selected element is absent');report['status']='error';return report
    selected=set(requested);selected_relations={k:r for k,r in relations.items() if r['from'] in selected or r['to'] in selected}
    included=set(selected);reasons={k:['requested' if ids is not None else 'workflow_focus'] for k in selected}
    for rid,r in selected_relations.items():
        for endpoint in (r['from'],r['to']):included.add(endpoint);reasons.setdefault(endpoint,[]).append('endpoint_of:'+rid)
    relevant_trades={k:t for k,t in record['trade_studies'].items() if workflow=='trade-study' and (not requested or set(t['alternatives'])&included or set(t['criteria'])&included)}
    for tid,t in relevant_trades.items():
        for dependency in set(t['alternatives'])|set(t['criteria']):
            included.add(dependency);reasons.setdefault(dependency,[]).append('trade_study:'+tid)
    report['selected_ids']=sorted(included)
    relevant_decisions={k:d for k,d in record['decisions'].items() if not d['affects'] or set(d['affects'])&included}
    relevant_questions={k:q for k,q in record['questions'].items() if not q['affects'] or set(q['affects'])&included}
    relevant_evidence={k:e for k,e in record['evidence'].items() if e['target'] in included}
    used=set()
    def gather(value):
        if type(value) is dict:
            for k,v in value.items():
                if k in ('basis','preference_basis') and v is not None:used.add(v)
                else:gather(v)
        elif type(value) is list:
            for v in value:gather(v)
    gather(record['question']);gather([elements[k] for k in included]);gather(selected_relations);gather(relevant_decisions);gather(relevant_evidence);gather(relevant_trades)
    for sid in sorted(used | set(source_evidence)):
        e=source_evidence.get(sid)
        if e is None:issue('source_missing','unknown',[sid],'Explicit source input was not supplied; interpretation/evidence remains unresolved')
        elif e.get('status')!='pass':issue('source_binding',e.get('status','error'),[sid],e.get('detail','Source did not bind'))
    source_status=_status(x['status'] for x in report['findings'] if x['rule'].startswith('source_'));source_status='pass' if source_status=='not_run' else source_status
    check('source_binding',source_status,'selected_supplied_byte_provenance','Matched supplied digests/excerpts; truth and interpretation are not established')
    if not record['question']['text'].strip():issue('draft_question','unknown',[],'The current engineering question is missing')
    if not w:issue('draft_workflow','unknown',[],f'No declared {workflow} view yet')
    else:
        if not requested:issue('draft_focus','unknown',[],'Select the element(s) relevant to the current question')
        for field in ('summary','conditions','outcome','next_decision'):
            if not w[field].strip():issue('draft_context','unknown',[],f'{workflow}: {field.replace("_"," ")} remains to be supplied')
    for key in sorted(included):
        if not elements[key]['description'].strip():issue('draft_description','unknown',[key],'Meaning/rationale is still missing')
        if elements[key]['basis'] is None:issue('draft_basis','unknown',[key],'Source or explicit proposal basis is still missing')
    for key,d in relevant_decisions.items():
        if d['status']=='accepted' and (not d['by'].strip() or d['basis'] is None):issue('decision_basis','unknown',[key],'Accepted is a recorded label; decision-maker/basis is missing and assent is not authenticated')
    for key,q in relevant_questions.items():
        if q['blocking']:issue('blocking_question','unknown',[key],q['text'] or 'A consequential question remains unresolved')
    for key,e in relevant_evidence.items():
        if not e['method'].strip() or not e['environment'].strip():issue('evidence_plan','unknown',[key,e['target']],'Evidence method/environment remains to be supplied')
        if e['mode']=='assessment' and (e['basis'] is None or e['result'] in ('unknown','not_run')):issue('evidence_assessment','unknown',[key,e['target']],'Reported assessment or its evidence basis is unresolved')
    trade_rows={}
    for key,t in relevant_trades.items():
        if t['method']!='qualitative':issue('trade_method','unsupported',[key],'Only qualitative comparison is admitted; numeric scoring/ranking is not run')
        if not t['question'].strip() or not t['alternatives'] or not t['criteria']:issue('trade_draft','unknown',[key],'Decision, authored alternatives and criteria are needed for this matrix')
        rows=[]
        for aid in t['alternatives']:
            for cid,c in t['criteria'].items():
                cell=deepcopy(t['assessments'].get(aid,{}).get(cid))
                if cell is None:cell={'finding':'unknown','value':None,'basis':None,'uncertainty':'Assessment not supplied'}
                if cell['finding']=='unknown' or cell['basis'] is None:issue('trade_unknown','unknown',[key,aid,cid],'Criterion assessment/evidence is unresolved')
                if c['kind']=='constraint' and cell['finding']=='contradicted':issue('declared_constraint','fail',[key,aid,cid],'A reported constraint is contradicted; preferences cannot offset it')
                rows.append({'alternative':aid,'criterion':cid,'criterion_kind':c['kind'],'measure':c['measure'],'unit':c['unit'],**cell,'origin':'reported_documentary_assessment'})
        trade_rows[key]={'question':t['question'],'method':t['method'],'rows':rows,'recommendation':t['recommendation'],'selection':'not_made','score_computation':'not_run'}
    if workflow=='trade-study' and not relevant_trades:issue('trade_draft','unknown',[],'No authored trade study applies to this scope')
    completeness=_status(x['status'] for x in report['findings'] if not x['rule'].startswith('source_'));completeness='pass' if completeness=='not_run' else completeness
    check('declared_completeness',completeness,'selected_documentary_draft','Presence/link checks only; content quality and real performance not qualified')
    report['view']={'question':deepcopy(record['question']),'workflow':deepcopy(w),'elements':{k:deepcopy(elements[k]) for k in sorted(included)},
                    'relations':{k:{**deepcopy(r),'origin':'declared_workflow_document'} for k,r in sorted(selected_relations.items())},
                    'decisions':relevant_decisions,'questions':relevant_questions,'evidence':relevant_evidence,'trade_studies':trade_rows,
                    'boundary_ids':sorted(included-selected),'omitted_ids':sorted(set(elements)-included),'closure_reasons':{k:sorted(set(v)) for k,v in sorted(reasons.items())}}
    report['status']=_status(x['status'] for x in report['checks'])
    report['findings'].sort(key=lambda x:(x['rule'],x['ids'],x['detail']))
    return report


def inspect_workflow(model_path,source_paths=None,*,workflow='concept',ids=None,review=False,document_names=()):
    source_paths={} if source_paths is None else source_paths
    report=_base(workflow,ids,review);report['input_paths']={'model':str(model_path),'sources':{str(k):str(v) for k,v in source_paths.items()} if type(source_paths) is dict else {}}
    received=deepcopy(report['input_paths'])
    try:
        if type(document_names) is not tuple or set(document_names)-{'cseHumanTasks','cseOwnership'}:
            raise Invalid('Unsupported supplemental document request')
        raw=read_regular(model_path,5_000_000);raw.decode('utf-8');digest=sha256(raw).hexdigest();report['model_sha256']=digest
        directory=ROOT/'.tmp';directory.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='workflow-',dir=directory) as temp:
            snapshot=Path(temp)/'captured.sysml';snapshot.write_bytes(raw)
            native=check_sysml(snapshot,syntax_only=True,kind=None)
        native['model_files']=[{'path':str(model_path),'sha256':digest}]
        for records in native.get('inventory',{}).values():
            for item in records:item['source']=str(model_path)
        for finding in native.get('findings',[])+native.get('parser_issues',[]):
            if finding.get('source'):finding['source']=str(model_path)
        report['native_status']=native.get('status','error');report['native_parser']=native.get('parser')
        if native.get('status')!='pass':
            return _native_failure(report,native)
        docs=[x for x in native['inventory']['documents'] if x.get('name')=='cseWorkflow']
        if len(docs)!=1 or sum(x.get('qualified_name')==docs[0].get('owner') for x in native['inventory']['concerns'])!=1:raise Invalid('Exactly one cseWorkflow document on a parsed concern is required')
        lines=docs[0]['body'].strip().splitlines()
        if not lines or lines[0].strip()!=MARKER:raise Invalid('Unsupported workflow document header')
        payload='\n'.join(lines[1:])
        if len(payload.encode())>1_000_000:raise Invalid('Workflow record exceeds1MB')
        record=json.loads(payload,object_pairs_hook=_pairs,parse_constant=lambda value:(_ for _ in ()).throw(Invalid('Nonfinite JSON value')));schema(record)
        if type(source_paths) is not dict or set(source_paths)-set(record['sources']):raise Invalid('Only explicitly declared source IDs may be supplied')
        evidence={};source_bytes={}
        for sid,path in sorted(source_paths.items()):
            s=record['sources'][sid];entry={'path':str(path),'expected_sha256':s['sha256'],'actual_sha256':None,'kind':s['kind'],'excerpt':s['excerpt'],'status':'error','detail':'Source acquisition did not complete'};evidence[sid]=entry
            source_raw=read_regular(path,1_000_000);source_bytes[sid]=source_raw;entry['actual_sha256']=sha256(source_raw).hexdigest();text=source_raw.decode('utf-8')
            entry.update(status='pass',detail='Bytes and unique excerpt match; source truth/interpretation is not verified')
            if entry['actual_sha256']!=s['sha256']:entry.update(status='fail',detail='Supplied source revision is stale')
            elif text.count(s['excerpt'])!=1:entry.update(status='fail',detail='Source excerpt must occur exactly once')
        report=analyze(record,native,evidence,workflow=workflow,ids=ids,review=review);report['input_paths']=received;report['document_owner']=docs[0]['owner'];report['model_sha256']=digest;report['native_model_sha256']=native.get('model_sha256')
        if document_names:
            report['supplemental_documents']={name:deepcopy([x for x in native['inventory']['documents'] if x.get('name')==name]) for name in document_names}
        changed=read_regular(model_path,5_000_000)!=raw or native.get('model_sha256')!=digest
        changed=changed or any(read_regular(source_paths[k],1_000_000)!=v for k,v in source_bytes.items())
        if changed:
            report.update(status='error',input_stability='error',view={},conditional_analysis='not_run')
            report['findings'].append({'rule':'inputs_changed','status':'error','ids':[],'detail':'Model/source bytes changed or native digest mismatched'})
        else:report['input_stability']='pass'
        return report
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as exc:
        report.update(status='error',input_stability='not_completed',view={},conditional_analysis='not_run')
        report['input_paths']=received;report['findings'].append({'rule':'input_or_record','status':'error','ids':[],'detail':str(exc)})
        return report


def render_text(report,expert=False):
    lines=[f"Engineering job: {report['selected_workflow']}."]
    view=report.get('view',{});question=view.get('question',{}).get('text')
    if question:lines.append('Question: '+question)
    lines.append('Declared draft checks: '+report['status']+'.')
    w=view.get('workflow') or {}
    for field,title in [('summary','Current work'),('conditions','Operating/applicability conditions'),('outcome','Intended outcome'),('next_decision','Next decision')]:
        if w.get(field):lines.append(title+': '+w[field])
    if any(e['kind']=='element_definition' for e in view.get('elements',{}).values()):
        lines.append('Definition-level documentary hierarchy: these nodes are named definitions, not instantiated parts; native ownership and cardinality need separate proof.')
    for key,e in view.get('elements',{}).items():
        suffix=f" [{key}; {e['native_name']}]" if expert else ''
        lines.append(f"{e['label']}{suffix}: {e['description'] or 'Meaning remains incomplete'} ({e['status']}).")
    for key,r in view.get('relations',{}).items():
        es=view['elements'];a=es[r['from']]['label'];b=es[r['to']]['label']
        lines.append(f"Declared {r['kind'].replace('_',' ')}: {a} — {b}"+(f"; {r['label']}" if r['label'] else '')+(f" [{key}]" if expert else '')+'.')
    for key,d in view.get('decisions',{}).items():
        owner='; recorded by '+d['by'] if d['by'] else '; operator identity unspecified'
        lines.append('Recorded decision ('+d['status']+owner+'): '+(d['text'] or 'Intent remains incomplete')+(f" [{key}]" if expert else '')+'.')
    for key,q in view.get('questions',{}).items():
        lines.append('Open question'+(' (blocks this scope)' if q['blocking'] else '')+': '+(q['text'] or 'Question remains incomplete')+(f" [{key}]" if expert else '')+'.')
    for _,t in view.get('trade_studies',{}).items():
        lines.append('Trade question: '+t['question']+'. Qualitative matrix; no score or selection computed.')
        for row in t['rows']:
            a=view['elements'].get(row['alternative'],{}).get('label',row['alternative']);c=view['elements'].get(row['criterion'],{}).get('label',row['criterion'])
            lines.append(f"  {a} / {c}: reported {row['finding']}; value {row['value'] if row['value'] is not None else 'unknown'} {row['unit']}; {row['uncertainty'] or 'uncertainty not described'}.")
        if t['recommendation']:lines.append('Proposed recommendation: '+t['recommendation'])
    for _,e in view.get('evidence',{}).items():
        label=view['elements'][e['target']]['label'];lines.append(f"Evidence {e['mode']} for {label}: {e['purpose']}; method {e['method'] or 'unknown'}; environment {e['environment'] or 'unknown'}; reported result {e['result']}. {e['limitations']}")
    for f in report.get('findings',[]):lines.append(f"{f.get('status',report['status'])}: {f.get('detail','Check did not complete')}"+(f" [{f.get('rule',f.get('code','diagnostic'))}; {','.join(f.get('ids',[]))}]" if expert else ''))
    lines.append('Actual behavior/performance, independently qualified evidence, required review and engineering acceptance are not established by these draft checks.')
    if expert:lines.append(f"Model SHA-256: {report.get('model_sha256')}; record SHA-256: {report.get('record_sha256')}; input stability: {report.get('input_stability')}.")
    return '\n'.join(lines)+'\n'


def empty_record(text,workflow):
    if workflow not in JOBS:raise Invalid('Unknown engineering job')
    r={'version':VERSION,'question':{'text':text,'basis':None},**{k:{} for k in GROUPS}}
    r['workflows']={workflow:{'focus':[],'summary':'','conditions':'','outcome':'','next_decision':''}};schema(r);return r


def draft_model(record,package,base_text=None):
    schema(record)
    if type(package) is not str or not NATIVE_ID.fullmatch(package):raise Invalid('Package needs one simple valid name')
    payload=json.dumps(record,sort_keys=True,indent=2,ensure_ascii=False).replace('/*',r'\u002f*').replace('*/',r'*\u002f')
    lines=[]
    if base_text is not None:
        if type(base_text) is not str:raise Invalid('Base model must be captured UTF-8 text')
        if 'doc cseWorkflow' in base_text:raise Invalid('Base already contains workflow metadata; revise its existing authoritative record instead of adding a competing one')
        lines.append(base_text)
    lines.append("package '"+package+"' {")
    if base_text is None:
        if any(e['kind'] in ('actor','system','element') for e in record['elements'].values()):lines.append("  part def 'WorkflowElement';")
        names=set()
        for key,e in sorted(record['elements'].items()):
            prefix=package+'::'
            if not e['native_name'].startswith(prefix) or not NATIVE_ID.fullmatch(e['native_name'][len(prefix):]):raise Invalid('Draft emission supports explicitly declared direct package members only; use --base for existing native structures')
            name=e['native_name'][len(prefix):]
            if name in ('workflowContext','WorkflowElement'):raise Invalid('Native draft member conflicts with a reserved emitter name')
            if name in names:raise Invalid('Draft emitter cannot create duplicate native names for multiple roles; use --base')
            names.add(name)
            native='concern' if KINDS[e['kind']]=='concerns' else 'part' if KINDS[e['kind']]=='parts' else 'part def' if KINDS[e['kind']]=='part_definitions' else 'action' if KINDS[e['kind']]=='actions' else 'requirement'
            suffix=" : 'WorkflowElement'" if native=='part' else ''
            lines.append("  "+native+" '"+name+"'"+suffix+';')
    lines+=['  concern workflowContext {','    doc cseWorkflow /*'+MARKER,payload,'    */','  }','}']
    return '\n'.join(lines)+'\n'


def write_draft(path,text):
    p=Path(path)
    with p.open('x',encoding='utf-8',newline='') as f:f.write(text)
    return {'path':str(p),'sha256':sha256(p.read_bytes()).hexdigest(),'native_check':'not_run'}


def catalog():
    return {'version':'workflow-catalog-1.0','entrypoint':'workflow','jobs':list(JOBS),
            'operations':['catalog','start','prepare','check','view','diagram'],'record':MARKER,
            'trade_methods':['qualitative'],'diagram_views':['relations','hierarchy','sequence'],
            'diagram_semantics':'simplified documentary model views; renderer must be installed and checked separately',
            'required_review':'not_supported_by_this_wrapper','limits':list(LIMITS)}
