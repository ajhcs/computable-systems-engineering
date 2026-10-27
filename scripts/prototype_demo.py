#!/usr/bin/env python3
"""Execute the optional local dummy application and review actual transactions."""
from datetime import datetime,timezone
from hashlib import sha256
import argparse,json
from pathlib import Path
import sys,uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prototypes.repair_reuse import Store,exercise,VERSION as PROTOTYPE_VERSION
from prototypes.repair_reuse_observer import observe
from verifier.core import load_json
from verifier.sysml import check_sysml
from verifier.prototype_review import inspect_prototype,VERSION

MEANINGS={
 'stockMismatch':('Book/physical mismatch in the stock-sensitive transaction decision state.','decision_state'),
 'adjustmentAuthorized':('Current session has stock-adjust authority at this decision.','decision_state'),
 'revocationEffective':('Requested read uses a known invalidated session/epoch. Unknown identity is not asserted as revoked.','decision_state'),
 'holdActive':('Target record is held in this transaction decision state; false when no record is targeted.','decision_state'),
 'retentionBasisKnown':('Target record has a reviewed fixture-only policy; no actual project retention period is supplied.','decision_state'),
 'dispositionAuthorityKnown':('Current session has disposition permission for the target record class.','decision_state'),
 'issueCommitted':('This committed transaction contains an actual positive issue movement.','committed_state'),
 'adjustmentCommitted':('This committed transaction contains an actual stock adjustment movement.','committed_state'),
 'adjustmentAuditRecorded':('The adjustment has a matching actor, part and action audit row in the same transaction.','committed_state'),
 'readServed':('The actual returned response contains a payload, including an empty payload.','returned_output'),
 'dispositionCommitted':('This transaction has a disposition ledger row and logical content removal.','committed_state'),
 'dispositionAuditRecorded':('This disposition has a matching actor, record and action audit row in the same transaction.','committed_state'),
 'copiesAccounted':('All declared SQL copy rows were removed and have matching disposition receipts. Physical erasure is unassessed.','committed_state'),
 'readAuthorized':('Separate observer derives current record-class read permission from raw session epoch and grant rows.','decision_state'),
 'issueAuthorized':('Separate observer derives current issue permission from raw session epoch and grant rows.','decision_state')}


def generate_run(output,models=None,manifest_path=None,faults=()):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    source_paths={'IMPLEMENTATION':ROOT/'prototypes/repair_reuse.py',
                  'OBSERVER':ROOT/'prototypes/repair_reuse_observer.py','DRIVER':Path(__file__).resolve()}
    source_bytes={key:path.read_bytes() for key,path in source_paths.items()}
    frozen=output/'source';frozen.mkdir()
    frozen_paths={}
    for key,raw in source_bytes.items():
        target=frozen/(key.lower()+'.py');target.write_bytes(raw);frozen_paths[key]=target
    models=[Path(p).resolve() for p in (models or [ROOT/'examples/prototype-evaluation/harness.sysml',ROOT/'examples/prototype-evaluation/authorization.sysml'])]
    manifest_path=Path(manifest_path or ROOT/'examples/prototype-evaluation/strict-manifest.json').resolve()
    start=datetime.now(timezone.utc).isoformat()
    store=Store(output/'dummy.sqlite',create=True,faults=faults);events=exercise(store)
    if any(path.read_bytes()!=source_bytes[key] for key,path in source_paths.items()):
        raise ValueError('Prototype/observer/driver source changed during execution; run is not qualified')
    end=datetime.now(timezone.utc).isoformat()
    capture=output/'transactions.jsonl';capture.write_text(''.join(json.dumps(e,sort_keys=True)+'\n' for e in events))
    manifest=load_json(manifest_path)
    compiled=check_sysml(models,manifest=manifest)
    (output/'compilation.json').write_text(json.dumps(compiled,indent=2)+'\n')
    if compiled['status']!='pass':raise ValueError('The selected native test obligations did not compile; compilation receipt retained')
    signals={physical for r in compiled['results'].values() for physical in r.get('binding',{}).values()}
    observations=[]
    for event in events:
        projection=observe(event)
        if signals-set(projection):raise ValueError('The reference observer does not define every selected native signal')
        observations.append({k:v for k,v in projection.items() if k in signals})
    evidence=output/'observations.json'
    evidence.write_text(json.dumps({'model_sha256':compiled['model_sha256'],'complete':True,'observations':observations},indent=2)+'\n')
    paths={**frozen_paths,'TRANSACTIONS':capture,'OBSERVATIONS':evidence,'DATABASE':output/'dummy.sqlite'}
    roles={'IMPLEMENTATION':'implementation','OBSERVER':'observer','DRIVER':'driver','TRANSACTIONS':'execution_log','OBSERVATIONS':'monitor_input','DATABASE':'data_store'}
    definitions={}
    for physical in signals:
        meaning,phase=MEANINGS[physical.rsplit('::',1)[-1]]
        definitions[physical]={'meaning':meaning,'phase':phase}
    record={'version':VERSION,'system_of_interest':'Optional local SQLite repair/reuse dummy prototype '+PROTOTYPE_VERSION,
        'purpose':'Verify selected transaction-level stock, access, hold and disposition obligations against an executed local dummy application.',
        'verification_method':'sampled_trace_analysis','evidence_origin':'executed_local_prototype','observation_mode':'transaction_sequence',
        'adapter':'repair_reuse_sqlite_v3','signal_definitions':definitions,
        'artifacts':{key:{'role':roles[key],'sha256':sha256(path.read_bytes()).hexdigest()} for key,path in paths.items()},
        'run':{'id':uuid.uuid4().hex,'start_utc':start,'end_utc':end,'exit_code':0,'transaction_count':len(events),
               'capture_boundary':'All 26 business transactions in the fixed dummy driver, excluding fixture/schema and session setup. Decision-state inputs plus committed/returned outputs; transaction index is not physical sample timing.'},
        'selected_obligations':[x['id']+'__'+x['constraint'] for x in manifest['expected']],
        'unresolved':[{'id':'REAL_POLICY','description':'Actual project retention periods, authority, obligations and stakeholder acceptance remain unknown. Fixture policy eligibility ticks are not adopted periods.','scope':'outside_selected_scope'},
                      {'id':'ENVIRONMENT','description':'No real inventory, identity provider, network/cache, external backup, secure-media erasure or production concurrency/scale qualification.','scope':'outside_selected_scope'}],
        'claim_limits':['Executed same-user local dummy application, not a protected or independently authenticated runner.',
            'Only row-local always clauses are supported by transaction-index projection; no wall-clock latency or retention duration claim.',
            'Declared SQL primary/export/backup rows and tombstone restore guard were exercised; external copies and physical erasure are unassessed.',
            'Fault injection, when selected, is an explicit test variant; faults='+','.join(sorted(faults))],
        'standards_basis':[{'reference':ref,'application':application,'conformity_assessment':'not_performed'} for ref,application in [
            ('ISO/IEC/IEEE 15288:2023','Tailored verification activity, purpose and evidence/claim boundaries.'),
            ('ISO/IEC/IEEE 29148:2018','Selected requirement identities and separate requirement/evidence/configuration records.'),
            ('ISO/IEC/IEEE 24765:2017','Stable systems/software engineering terminology; verification and validation distinguished.')]]}
    run_path=output/'run-record.json';run_path.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    (output/'artifact-paths.json').write_text(json.dumps({k:str(v) for k,v in paths.items()},indent=2)+'\n')
    manifest_sha=sha256(manifest_path.read_bytes()).hexdigest()
    report=inspect_prototype(models,manifest_path,manifest_sha,evidence,run_path,paths)
    (output/'review.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    (output/'invocation.json').write_text(json.dumps({'models':[str(p) for p in models],'manifest':str(manifest_path),'retained_manifest_sha256':manifest_sha,
        'run_record':str(run_path),'evidence':str(evidence),'artifacts':{k:str(v) for k,v in paths.items()},'faults':sorted(faults)},indent=2)+'\n')
    return report


def main():
    from prototypes.repair_reuse import FAULTS
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    p.add_argument('--model',action='append');p.add_argument('--manifest')
    p.add_argument('--fault',action='append',default=[],choices=sorted(FAULTS),help='explicit reference-test defect, isolated dummy data only')
    args=p.parse_args()
    try:report=generate_run(args.output,args.model,args.manifest,args.fault)
    except (OSError,ValueError) as exc:print(str(exc),file=sys.stderr);return 2
    print(json.dumps({'status':report['status'],'monitor_status':report['monitor_status'],'claim_scope':report['claim_scope'],
        'report':str(Path(args.output).resolve()/'review.json'),'validation':'not_performed','standards_conformity':'not_assessed'}))
    return 0 if report['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
