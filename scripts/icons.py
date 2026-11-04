#!/usr/bin/env python3
"""Find, inspect, validate and export the CSE engineering component library."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier import components

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    listing=sub.add_parser('list');listing.add_argument('--query',default='');listing.add_argument('--sysml');listing.add_argument('--family')
    show=sub.add_parser('show');show.add_argument('id')
    sub.add_parser('check')
    export=sub.add_parser('export');export.add_argument('--format',choices=['svg','drawio','kernspan'],required=True);export.add_argument('--out',required=True);export.add_argument('--query',default='');export.add_argument('--sysml');export.add_argument('--family')
    a=p.parse_args()
    try:
        if a.command=='check':result=components.validate()
        elif a.command=='show':
            result=components.component(a.id)
            if result is None:raise ValueError('Unknown component ID: '+a.id)
        else:
            rows=components.select(a.query,a.sysml,a.family)
            result=components.export(a.format,a.out,rows) if a.command=='export' else [{'id':r['id'],'name':r['name'],'family':r['family'],'treatment':r.get('treatment'),'sysml_v2':r['mapping']['sysml_v2']} for r in rows]
        print(json.dumps(result,indent=2,ensure_ascii=False));return 0
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'error','detail':str(exc)}));return 2
if __name__=='__main__':raise SystemExit(main())
