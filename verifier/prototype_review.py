"""Bounded prototype verification: explicit artifacts, observation origin and scope.

No model-supplied command or code is executed. This is not a protected runner or
an ISO conformity assessment. Existing native CSE checks supply behavior verdicts.
"""
from datetime import datetime
from hashlib import sha256
import json
import re
from .core import _pairs
from .foundation import read_regular
from .language import SENTENCE
from .sysml import check_sysml

VERSION='prototype-evaluation-1.0'
ROLES={'implementation','observer','driver','execution_log','monitor_input','data_store'}


def _json(raw):
    return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,
                      parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite JSON value')))


def _text(value, where, cap=4096):
    if type(value) is not str or not value.strip() or len(value)>cap:
        raise ValueError(where+' needs bounded nonempty text')


def inspect_prototype(models,manifest_path,manifest_sha256,evidence_path,run_path,artifact_paths):
    report={'version':VERSION,'status':'error','claim_scope':'selected_local_prototype_trace_verification',
        'verification_method':'sampled_trace_analysis','validation':'not_performed',
        'standards_conformity':'not_assessed','decision_authentication':'not_provided',
        'findings':[],'monitor_status':'not_run','native_check':None,'artifact_checks':{},'results_usable':False}
    captured=[]
    def issue(rule,status,detail):report['findings'].append({'rule':rule,'status':status,'detail':detail})
    def capture(path,cap=5_000_000):
        raw=read_regular(path,cap);captured.append((path,raw,cap));return raw
    try:
        if type(models) not in (list,tuple) or not 1<=len(models)<=32:
            raise ValueError('Supply 1..32 explicit model paths')
        if type(artifact_paths) is not dict or len(artifact_paths)>32:
            raise ValueError('Supply bounded explicit artifact paths')
        model_raw=[capture(p) for p in models]
        manifest_raw=capture(manifest_path,1_000_000);evidence_raw=capture(evidence_path,5_000_000)
        run_raw=capture(run_path,1_000_000)
        if sha256(manifest_raw).hexdigest()!=manifest_sha256:
            raise ValueError('Selected obligation manifest differs from the retained review basis')
        record=_json(run_raw);evidence=_json(evidence_raw);manifest=_json(manifest_raw)
        if type(evidence) is not dict or type(manifest) is not dict:
            raise ValueError('Evidence and obligation manifest must be JSON objects')
        fields={'version','system_of_interest','purpose','verification_method','evidence_origin','observation_mode',
                'adapter','signal_definitions','artifacts','run','selected_obligations','unresolved','claim_limits','standards_basis'}
        if type(record) is not dict or set(record)!=fields or record['version']!=VERSION:
            raise ValueError('Expected the versioned prototype-evaluation record and known fields')
        for field in ('system_of_interest','purpose'):
            if type(record[field]) is not str or not record[field].strip() or len(record[field])>4096:
                raise ValueError('Declare '+field+' for the selected verification')
        report['system_of_interest']=record['system_of_interest'];report['purpose']=record['purpose']
        if record['verification_method']!='sampled_trace_analysis' or record['observation_mode']!='transaction_sequence':
            issue('method','unsupported','Only row-local transaction-decision/result observation analysis is supported here')
        if record['evidence_origin']!='executed_local_prototype':
            issue('evidence_origin','unknown','Authored samples are not evidence of executed prototype transactions')
        if record['adapter'] not in ('repair_reuse_sqlite_v3','recorded_boolean_signals_v1'):
            issue('adapter','unsupported','Unknown adapter; no arbitrary observer or command will be loaded')
        report['observation_correspondence']='recomputed_from_captured_sql_state' if record['adapter']=='repair_reuse_sqlite_v3' else 'recorded_signals_only'
        if type(record['signal_definitions']) is not dict or not record['signal_definitions']:
            raise ValueError('Declare signal meanings and decision/result observation phases')
        for name,definition in record['signal_definitions'].items():
            if type(name) is not str or not name.strip() or len(name)>4096 or type(definition) is not dict or set(definition)!={'meaning','phase'} or not definition['meaning'] or definition['phase'] not in ('decision_state','committed_state','returned_output'):
                raise ValueError('Invalid signal definition')
            _text(definition['meaning'],'signal meaning')
        if type(record['claim_limits']) is not list or len(record['claim_limits'])>64 or not record['claim_limits'] or any(type(x) is not str or not x.strip() for x in record['claim_limits']):
            raise ValueError('Declare limits of the verification claim')
        for value in record['claim_limits']:_text(value,'claim limit')
        report['claim_limits']=record['claim_limits']
        if type(record['unresolved']) is not list or len(record['unresolved'])>128:raise ValueError('unresolved must be a list')
        for item in record['unresolved']:
            if type(item) is not dict or set(item)!={'id','description','scope'} or not item['id'] or not item['description'] or item['scope'] not in ('blocks_selected_scope','outside_selected_scope'):
                raise ValueError('Invalid unresolved-condition record')
            _text(item['id'],'unresolved ID',128);_text(item['description'],'unresolved description')
            if item['scope']=='blocks_selected_scope':issue('unresolved','unknown',item['id']+': '+item['description'])
        report['unresolved']=record['unresolved']
        if type(record['standards_basis']) is not list or len(record['standards_basis'])>16:raise ValueError('standards_basis must be a list')
        for standard in record['standards_basis']:
            if type(standard) is not dict or set(standard)!={'reference','application','conformity_assessment'} or not standard['reference'] or not standard['application']:
                raise ValueError('Invalid standards applicability record')
            _text(standard['reference'],'standard reference',256);_text(standard['application'],'standard application')
            if standard['conformity_assessment']!='not_performed':
                issue('standards_claim','unsupported','This checker does not establish whole-standard conformity')
        report['standards_basis']=record['standards_basis']
        execution=record['run']
        if type(execution) is not dict or set(execution)!={'id','start_utc','end_utc','exit_code','transaction_count','capture_boundary'} or not execution['id'] or not execution['capture_boundary']:
            raise ValueError('Expected explicit execution identity, boundary, times, exit and transaction count')
        _text(execution['id'],'run ID',128);_text(execution['capture_boundary'],'capture boundary')
        for key in ('start_utc','end_utc'):_text(execution[key],key,96)
        times=[datetime.fromisoformat(execution[k]) for k in ('start_utc','end_utc')]
        if any(t.tzinfo is None for t in times) or times[1]<times[0] or type(execution['exit_code']) is not int or type(execution['transaction_count']) is not int or not 1<=execution['transaction_count']<=10000:
            raise ValueError('Invalid execution bounds')
        if execution['exit_code']!=0:issue('execution_incomplete','error','The recorded prototype execution did not complete successfully')
        report['execution']=execution
        if type(record['selected_obligations']) is not list or not 1<=len(record['selected_obligations'])<=512 or any(type(x) is not str for x in record['selected_obligations']) or len(set(record['selected_obligations']))!=len(record['selected_obligations']):
            raise ValueError('Expected distinct selected obligation IDs')
        selected={x['id']+'__'+x['constraint'] for x in manifest['expected']}
        if set(record['selected_obligations'])!=selected:issue('obligation_scope','fail','Run selection differs from the independently retained manifest')
        artifacts=record['artifacts']
        if type(artifacts) is not dict or not artifacts or len(artifacts)>32:raise ValueError('Expected bounded explicit artifact identities')
        if set(artifact_paths)-set(artifacts):raise ValueError('Undeclared artifact arguments')
        raw_by_role={}
        for key,item in artifacts.items():
            _text(key,'artifact ID',128)
            if type(item) is not dict or set(item)!={'role','sha256'} or item['role'] not in ROLES:
                raise ValueError('Invalid artifact role or fields')
            if type(item['sha256']) is not str or not re.fullmatch(r'[0-9a-f]{64}',item['sha256']):
                raise ValueError('Artifact identity needs a lowercase SHA-256')
            if key not in artifact_paths:
                issue('artifact_missing','unknown','Supply artifact '+key);continue
            raw=capture(artifact_paths[key]);actual=sha256(raw).hexdigest()
            status='pass' if actual==item['sha256'] else 'fail'
            report['artifact_checks'][key]={'role':item['role'],'status':status,'sha256':actual}
            if status!='pass':issue('artifact_revision','fail','Artifact bytes changed: '+key)
            raw_by_role.setdefault(item['role'],[]).append(raw)
        for role in ('implementation','observer','driver','execution_log','monitor_input'):
            if len(raw_by_role.get(role,[]))!=1:issue('artifact_role','unknown','Need one checked '+role+' artifact')
        if len(raw_by_role.get('monitor_input',[]))==1 and raw_by_role['monitor_input'][0]!=evidence_raw:
            issue('evidence_binding','fail','Reviewed evidence is not the declared monitor input artifact')
        events=None
        if len(raw_by_role.get('execution_log',[]))==1:
            raw=raw_by_role['execution_log'][0]
            lines=raw.decode('utf-8').splitlines()
            if len(lines)>10000:raise ValueError('Transaction capture exceeds bound')
            events=[_json(line.encode()) for line in lines if line.strip()]
            if any(type(event) is not dict or type(event.get('sequence')) is not int for event in events):
                raise ValueError('Each captured transaction must have an integer sequence and object content')
            if len(events)!=execution['transaction_count'] or len(events)!=len(evidence.get('observations',[])):
                issue('capture_count','fail','Capture, run receipt and monitor observation counts differ')
            if [e.get('sequence') for e in events]!=list(range(1,len(events)+1)):
                issue('capture_sequence','fail','Transaction sequence is missing, reordered or duplicated')
            if record['adapter']=='repair_reuse_sqlite_v3':
                from prototypes.repair_reuse_observer import validate_capture
                for event in events:validate_capture(event)
        native=check_sysml(models,manifest=manifest,evidence=evidence,review=True)
        report['native_check']=native;report['monitor_status']=native['status']
        report['model_sha256']=native.get('model_sha256');report['manifest_sha256']=sha256(manifest_raw).hexdigest()
        results=native.get('results',{});signals=set()
        for key,result in results.items():
            sentence=result.get('compiled_clause');match=SENTENCE.fullmatch(sentence) if type(sentence) is str else None
            if match is None or not match.group('always'):
                issue('temporal_projection','unsupported',key+': transaction-index observations support only always clauses; no physical clock/deadline claim')
            signals.update(result.get('binding',{}).values())
        if not signals:issue('signal_scope','unknown','No supported observation signals were compiled')
        if signals-set(record['signal_definitions']):issue('signal_definition','unknown','A bound signal lacks its meaning/phase definition')
        if events is not None:
            if record['adapter']=='repair_reuse_sqlite_v3':
                from prototypes.repair_reuse_observer import observe
                from pathlib import Path
                registered=Path(__file__).resolve().parents[1]/'prototypes/repair_reuse_observer.py'
                if raw_by_role.get('observer')!=[registered.read_bytes()]:
                    issue('observer_adapter_revision','unknown','Captured observer differs from the registered adapter; old evidence is not silently reinterpreted')
                projected=[observe(event) for event in events]
            elif record['adapter']=='recorded_boolean_signals_v1':
                projected=[e['observation'] for e in events]
            else:projected=[]
            for index,(expected,row) in enumerate(zip(projected,evidence.get('observations',[]))):
                expected={k:v for k,v in expected.items() if k in signals}
                if set(row)-set(expected) or any(k in expected and expected[k]!=v for k,v in row.items()):
                    issue('observation_correspondence','fail','Monitor row differs from captured transaction result at '+str(index))
                elif set(row)!=set(expected):issue('observation_missing','unknown','Observation signal missing at '+str(index))
        statuses=[native['status']]+[x['status'] for x in report['findings']]
        report['status']=next((s for s in ('error','fail','unsupported','unknown') if s in statuses),'pass')
        report['results_usable']=report['status']=='pass'
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError) as exc:
        issue('prototype_input','error',str(exc));report['status']='error'
    finally:
        try:
            if any(read_regular(path,cap)!=raw for path,raw,cap in captured):
                issue('input_changed','error','A captured model, manifest, evidence, run or artifact changed during review')
                report['status']='error';report['results_usable']=False
        except (OSError,ValueError) as exc:
            issue('input_changed','error',str(exc));report['status']='error';report['results_usable']=False
    return report
