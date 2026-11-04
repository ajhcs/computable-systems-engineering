"""Bounded, revision-bound discovery and explicit presentation selections."""
import base64
from collections import Counter
import difflib
from hashlib import sha256
import json
from pathlib import Path
import re

from verifier import components as library

SCHEMA='cse.component-agent/1'
SELECTION='cse.component-selection/1'
MAX_PAGE=50
MAX_SELECTION=50

class RequestError(ValueError):
    def __init__(self,code,message,**details):
        super().__init__(message);self.code=code;self.details=details

def revision(root=library.LIBRARY):
    return sha256((Path(root)/'index.json').read_bytes()).hexdigest()

def compact(row):
    result={key:row[key] for key in ('id','name','family','file','sha256')}
    result.update(category=row.get('category'),approval_state=row.get('approval_state'),
                  context=row['mapping']['principle'],sysml_v2=row['mapping']['sysml_v2'],
                  variant_of=row.get('variant_of'))
    return result

def ranked(query='',sysml=None,family=None,root=library.LIBRARY):
    if not isinstance(query,str) or len(query)>256:raise RequestError('invalid_query','Query must be text of at most 256 characters.')
    words=re.findall(r'[\w]+',query.casefold());rows=[]
    for row in library.inventory(root):
        if family and family.casefold()!=row['family'].casefold():continue
        if sysml and sysml not in row['mapping']['sysml_v2']+row['mapping']['sysml_v1']:continue
        # Names and declared facets are searchable. Descriptive prose and
        # engineering caveats cannot make unrelated objects match a query.
        identity=(row['id']+' '+row['name']).casefold()
        facets=' '.join([row['family'],row.get('category',''),row['mapping']['principle']]).casefold()
        if not all(w in identity+' '+facets for w in words):continue
        score=(1000 if query and row['id'].casefold()==query.casefold() else
               900 if query and row['name'].casefold()==query.casefold() else
               sum(20 if w in re.findall(r'\w+',row['name'].casefold()) else 10 if w in identity else 1 for w in words))
        rows.append((score,row))
    return [r for _,r in sorted(rows,key=lambda pair:(-pair[0],pair[1]['id']))]

def search(query='',sysml=None,family=None,limit=20,cursor=None,root=library.LIBRARY):
    if type(limit) is not int or not 1<=limit<=MAX_PAGE:raise RequestError('invalid_limit','Limit must be an integer from 1 to 50.')
    scope={'query':query,'sysml':sysml,'family':family};rev=revision(root);offset=0
    if cursor:
        try:
            if len(cursor)>2048:raise ValueError()
            token=json.loads(base64.urlsafe_b64decode(cursor.encode('ascii')))
            if token['revision']!=rev:raise RequestError('stale_cursor','The catalog changed; repeat the search without its cursor.')
            if token['scope']!=scope:raise RequestError('cursor_scope_mismatch','Reuse the same filters with this cursor.')
            offset=token['offset']
            if type(offset) is not int or offset<0:raise ValueError()
        except RequestError:raise
        except (ValueError,KeyError,TypeError,UnicodeError) as exc:raise RequestError('invalid_cursor','Use a next_cursor returned by this search.') from exc
    rows=ranked(query,sysml,family,root);end=offset+limit
    next_cursor=base64.urlsafe_b64encode(json.dumps({'revision':rev,'scope':scope,'offset':end},sort_keys=True).encode()).decode() if end<len(rows) else None
    return {'schema':SCHEMA,'status':'pass','catalog_sha256':rev,'filters':scope,'total':len(rows),
            'returned':len(rows[offset:end]),'items':[compact(r) for r in rows[offset:end]],'next_cursor':next_cursor}

def resolve(ids,root=library.LIBRARY,maximum=MAX_SELECTION):
    if not isinstance(ids,list) or not 1<=len(ids)<=maximum or any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,199}',x) for x in ids):
        raise RequestError('invalid_selection',f'Select between 1 and {maximum} exact component IDs.')
    if len(set(ids))!=len(ids):raise RequestError('duplicate_id','Each selected component ID must occur once.')
    rows={r['id']:r for r in library.inventory(root)};missing=[id for id in ids if id not in rows]
    if missing:raise RequestError('unknown_component_id','Unknown IDs were refused; no files were written.',unknown_ids=missing,suggestions={id:difflib.get_close_matches(id,rows,n=3,cutoff=.65) for id in missing})
    return [rows[id] for id in ids]

def selection(ids,root=library.LIBRARY):
    resolve(ids,root)
    return {'schema':SELECTION,'catalog_sha256':revision(root),'component_ids':ids}

def read_selection(path,root=library.LIBRARY):
    if Path(path).stat().st_size>65536:raise RequestError('invalid_selection','Selection JSON exceeds 64 KiB.')
    try:data=json.loads(Path(path).read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as exc:raise RequestError('invalid_selection','Selection must be UTF-8 JSON.') from exc
    if not isinstance(data,dict) or set(data)!={'schema','catalog_sha256','component_ids'} or data['schema']!=SELECTION:
        raise RequestError('invalid_selection','Use the documented component-selection/1 record.')
    if data['catalog_sha256']!=revision(root):raise RequestError('stale_selection','The library changed; inspect the selected IDs and create a new selection record.')
    return resolve(data['component_ids'],root)

def facets(root=library.LIBRARY):
    rows=library.inventory(root)
    return {'schema':SCHEMA,'status':'pass','catalog_sha256':revision(root),'count':len(rows),
            'families':dict(sorted(Counter(r['family'] for r in rows).items())),
            'sysml_contexts':dict(sorted(Counter(x for r in rows for x in set(r['mapping']['sysml_v2']+r['mapping']['sysml_v1'])).items()))}

def destination(out,root=library.LIBRARY,directory=False):
    path=Path(out).expanduser().resolve();runtime=Path(root).resolve().parents[1]
    if path==runtime or path.is_relative_to(runtime):raise RequestError('protected_destination','Write project artifacts outside the installed plugin/repository.')
    if path.exists() and (not directory or not path.is_dir() or any(path.iterdir())):
        raise RequestError('destination_exists','Choose a new file or an empty export directory; existing outputs are preserved.')
    return path

def export(format,out,rows,root=library.LIBRARY):
    # Canonicalize IDs before checking destination or invoking a writer. Caller
    # fields such as SVG paths, model bindings or labels have no authority.
    trusted=resolve([r['id'] for r in rows],root,maximum=len(library.inventory(root)))
    if format not in ('svg','drawio','kernspan'):raise RequestError('invalid_argument','Export format must be svg, drawio or kernspan.')
    if format=='kernspan' and len(trusted)!=len(library.inventory(root)):
        raise RequestError('requires_full_catalog','The Kernspan atlas requires the complete catalog; export with --all and filter in its search API.')
    dest=destination(out,root,directory=True)
    result=library.export(format,dest,trusted,root)
    result.update(schema=SCHEMA,catalog_sha256=revision(root),component_ids=[r['id'] for r in trusted],model_changes=False)
    return result

def contract():
    return {'schema':SCHEMA,'status':'pass','limits':{'search_default':20,'search_maximum':50,'selection_maximum':50,'inline_maximum':8},
            'identity':'Exact component IDs identify artwork; catalog_sha256 binds discovery/selection to its revision. Model IDs are separate.',
            'commands':{
                'catalog':{'effect':'read_only','purpose':'Discover available families and SysML context facets.'},
                'list':{'effect':'read_only','purpose':'Ranked paged search; pass next_cursor with unchanged filters.'},
                'show':{'effect':'read_only','purpose':'Fetch complete source/treatment/mapping details by exact ID.'},
                'selection':{'effect':'read_only','purpose':'Emit a revision-bound selection JSON record from exact IDs.'},
                'preview':{'effect':'writes_new_local_file','purpose':'Create a self-contained accessible shortlist UI; its controls change selection only.'},
                'export':{'effect':'writes_new_local_directory','purpose':'Export explicit IDs, a valid selection record, a bounded query, or explicitly --all.'},
                'check':{'effect':'read_only','purpose':'Check component bytes, SVG references and static adapter freshness.'}},
            'search_inputs':{'query':'text, at most 256 characters','sysml':'exact declared context from catalog','family':'exact family from catalog','limit':'integer 1..50; default 20','cursor':'next_cursor from the preceding page with unchanged filters'},
            'selection_record':{'schema':SELECTION,'catalog_sha256':'64-character index SHA-256','component_ids':'1..50 distinct exact IDs; additional fields refused'},
            'errors':['invalid_argument','artifact_error','invalid_query','invalid_limit','invalid_cursor','stale_cursor','cursor_scope_mismatch','invalid_selection','unknown_component_id','duplicate_id','stale_selection','selection_required','query_too_broad','no_matches','protected_destination','destination_exists','inline_limit','invalid_destination','requires_full_catalog'],
            'ui_transport':'Portable local HTML; no MCP server or native ChatGPT widget is registered by this skills-only plugin.'}
