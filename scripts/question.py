#!/usr/bin/env python3
"""Start, record or answer a source-bound engineering capacity question."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier.core import _pairs
from verifier.foundation import read_regular, Invalid, ID
from verifier.inquiry import VERSION, MARKER, QUERIES, draft_model, write_draft, inspect_inquiry, render_text


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('start');p.add_argument('output');p.add_argument('--text',required=True);p.add_argument('--package',default='QuestionModel')
    p=sub.add_parser('prepare');p.add_argument('spec');p.add_argument('output');p.add_argument('--package',required=True)
    p=sub.add_parser('answer');p.add_argument('model');p.add_argument('--source',action='append',default=[])
    p.add_argument('--alternative');p.add_argument('--unavailable',action='append',default=[])
    p.add_argument('--format',choices=('json','text'),default='json');p.add_argument('--audience',choices=('beginner','expert'),default='beginner')
    sub.add_parser('catalog')
    args=parser.parse_args(argv)
    if args.command=='catalog':
        print(json.dumps({'version':VERSION,'trusted_queries':QUERIES,'draft_operations':{
            'start':'Exclusive create of an incomplete native question draft; no facts inferred',
            'prepare':'Exclusive create from explicit structured draft data; native validation not run'}},indent=2,sort_keys=True));return 0
    try:
        if args.command in ('start','prepare'):
            if args.command=='start':
                record={'version':VERSION,'question':{'text':args.text,'basis':None},'sources':{},'functions':{},'resources':{},'alternatives':{}}
            else:
                record=json.loads(read_regular(args.spec,1_000_000).decode('utf-8'),object_pairs_hook=_pairs,
                    parse_constant=lambda x:(_ for _ in ()).throw(Invalid('Nonfinite value')))
            write_draft(args.output,draft_model(record,args.package))
            report={'status':'draft_created','claim_scope':'native_question_draft_emission','model':str(Path(args.output).absolute()),
                    'native_status':'not_run','acceptance':'not_evaluated','message':'Draft only; bind supplied sources and run question answer. No source intent or feasibility inferred.'}
            print(json.dumps(report,indent=2));return 0
        paths={}
        for item in args.source:
            sid,separator,path=item.partition('=')
            if not separator or not ID.fullmatch(sid) or not path or sid in paths:
                raise Invalid('Sources need distinct declared ID=PATH arguments')
            paths[sid]=path
        report=inspect_inquiry(args.model,paths,args.alternative,args.unavailable)
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as exc:
        report={'version':VERSION,'status':'error','claim_scope':'input_or_draft_emission','evaluation':'not_run',
            'request':vars(args),'model_sha256':None,'sources':{},'alternatives':{},
            'findings':[{'rule':'input_or_draft','status':'error','ids':[],'detail':str(exc)}],
            'behavior':'not_run','operational_continuity':'unknown','acceptance':'not_evaluated'}
    print(render_text(report,args.audience=='expert') if getattr(args,'format','json')=='text' else json.dumps(report,sort_keys=True,indent=2))
    return 0 if report['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
