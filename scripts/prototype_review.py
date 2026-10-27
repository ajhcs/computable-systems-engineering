#!/usr/bin/env python3
"""Review explicit prototype evidence with the existing CSE sampled monitor."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier.prototype_review import inspect_prototype


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model',nargs='+');p.add_argument('--manifest',required=True)
    p.add_argument('--manifest-sha256',required=True,help='retained obligation-manifest byte digest; not acceptance')
    p.add_argument('--evidence',required=True);p.add_argument('--run-record',required=True)
    p.add_argument('--artifact',action='append',default=[],help='explicit ID=PATH; no paths/commands are opened from a model')
    p.add_argument('--json',action='store_true');args=p.parse_args();artifacts={}
    for value in args.artifact:
        key,sep,path=value.partition('=')
        if not sep or not key or not path or key in artifacts:p.error('Artifacts require distinct ID=PATH arguments')
        artifacts[key]=path
    report=inspect_prototype(args.model,args.manifest,args.manifest_sha256,args.evidence,args.run_record,artifacts)
    if args.json:print(json.dumps(report,sort_keys=True,indent=2))
    else:
        print(report['status']+': selected local prototype trace verification; validation not performed; standards conformity not assessed')
        print('Monitor: '+report['monitor_status'])
        for finding in report['findings']:print(finding['status']+' '+finding['rule']+': '+finding['detail'])
    return 0 if report['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
