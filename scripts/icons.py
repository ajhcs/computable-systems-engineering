#!/usr/bin/env python3
"""Discover a bounded shortlist, inspect exact IDs, then export selected artwork."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier import components
import component_agent as agent

class Parser(argparse.ArgumentParser):
    def error(self,message):raise agent.RequestError('invalid_argument',message)

def selectors(parser):
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--ids',nargs='+');group.add_argument('--selection');group.add_argument('--query');group.add_argument('--all',action='store_true')
    parser.add_argument('--sysml');parser.add_argument('--family')

def requested(args):
    if args.ids is not None or args.selection or args.all:
        if args.sysml or args.family:raise agent.RequestError('invalid_argument','Use filters with --query, not an explicit selection or --all.')
    if args.ids is not None:return agent.resolve(args.ids)
    if args.selection:return agent.read_selection(args.selection)
    if args.all:return components.inventory()
    if args.query is None and not (args.sysml or args.family):raise agent.RequestError('selection_required','Choose exact --ids, --selection, a bounded query/filter, or explicitly --all.')
    rows=agent.ranked(args.query or '',args.sysml,args.family)
    if not rows:raise agent.RequestError('no_matches','No components matched; refine the query or inspect catalog facets.')
    if len(rows)>agent.MAX_SELECTION:raise agent.RequestError('query_too_broad','Search first, then select exact IDs or refine the query.',matched=len(rows),limit=agent.MAX_SELECTION)
    return rows

def main():
    try:
        p=Parser(description=__doc__);p.add_argument('--pretty',action='store_true');sub=p.add_subparsers(dest='command',required=True)
        listing=sub.add_parser('list');listing.add_argument('--query',default='');listing.add_argument('--sysml');listing.add_argument('--family');listing.add_argument('--limit',type=int,default=20);listing.add_argument('--cursor')
        show=sub.add_parser('show');show.add_argument('id')
        select=sub.add_parser('selection');select.add_argument('--ids',nargs='+',required=True)
        for command in ('catalog','contract','check'):sub.add_parser(command)
        preview=sub.add_parser('preview');preview.add_argument('--ids',nargs='+',required=True);preview.add_argument('--out',required=True)
        export=sub.add_parser('export');export.add_argument('--format',choices=['svg','drawio','kernspan'],required=True);export.add_argument('--out',required=True);selectors(export)
        a=p.parse_args()
        if a.command=='check':result=components.validate()
        elif a.command=='contract':result=agent.contract()
        elif a.command=='catalog':result=agent.facets()
        elif a.command=='show':
            result={'schema':agent.SCHEMA,'status':'pass','catalog_sha256':agent.revision(),'component':agent.resolve([a.id])[0]}
        elif a.command=='selection':result=agent.selection(a.ids)
        elif a.command=='list':result=agent.search(a.query,a.sysml,a.family,a.limit,a.cursor)
        elif a.command=='preview':
            from component_ui import render
            result=render(a.ids,a.out)
        else:result=agent.export(a.format,a.out,requested(a))
        print(json.dumps(result,indent=2 if a.pretty else None,ensure_ascii=False));return 0
    except agent.RequestError as exc:
        print(json.dumps({'schema':agent.SCHEMA,'status':'error','error':{'code':exc.code,'message':str(exc),**exc.details}}));return 2
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'schema':agent.SCHEMA,'status':'error','error':{'code':'artifact_error','message':str(exc)}}));return 2
if __name__=='__main__':raise SystemExit(main())
