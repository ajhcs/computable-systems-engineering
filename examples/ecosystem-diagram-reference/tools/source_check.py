"""Read-only correspondence checks for three selected source-safe reference derivatives.

Pass means these declared source/model/presentation contracts agree. It does not
establish real-world validity, execution equivalence or source authenticity. Existing parser facts are checked, not freshly reparsed.
"""
from pathlib import Path
import json,hashlib,re,copy,itertools,xml.etree.ElementTree as ET
from cases import KEYS, require_release_scope
def validate_source(root):
 R=Path(root);keys=KEYS;require_release_scope(R);checks=[]
 def ck(name,ok,detail=None):
  checks.append({'check':name,'passed':bool(ok),'detail':detail})
  if not ok:raise ValueError((name,detail))
 def end(x):
  c=x.get('chain',[])
  return '.'.join(t.rsplit('::',1)[-1] for t in c) if c else x['qualified'].rsplit('::',1)[-1]
 frozen=json.loads((R/'validation/frozen-ledgers.json').read_text())
 for name,h in frozen.items():ck('frozen source ledger '+name,hashlib.sha256((R/'source'/name).read_bytes()).hexdigest()==h)
 models={};ledgers={};views={}
 for key in keys:
  f=json.loads((R/'native'/(key+'.facts.json')).read_text())
  ck(key+' parse/link',f.get('parse_has_errors') is False,f.get('issues'))
  ck(key+' source binding',f['source_file']=='models/'+key+'.sysml' and f['source_sha256']==hashlib.sha256((R/f['source_file']).read_bytes()).hexdigest())
  models[key]=f['elements']
  ledgers[key]=json.loads((R/'source'/(key[0]+'-ledger.json')).read_text())
  views[key]=json.loads((R/'rendered'/(key+'.view.json')).read_text())
  ck(key+' nonblank SVG',len(ET.parse(R/'rendered'/(key+'.svg')).getroot())>=3 and len(views[key]['nodes'])>0)
  nativeids={x['id'] for x in f['elements']}
  ck(key+' all displayed nodes trace native facts',all(n['native_id'] in nativeids for n in views[key]['nodes']))
  ck(key+' all drawn edges trace native facts',all(n['native_id'] in nativeids for n in views[key]['edges']))
  ck(key+' XML editable presentation',ET.parse(R/'rendered'/(key+'.drawio')).getroot().tag=='mxfile')
 # C native unit/quantity extraction and printed independent totals.
 es=models[keys[0]];l=ledgers[keys[0]];tasks=[]
 for n in l['tasks']:
  f=next(e for e in es if e['name']==n['id']);attrs={e['qualified'].rsplit('::',1)[-1]:e for e in es if e['owner']==f['qualified'] and e['kind']=='AttributeUsage' and e['value']}
  vals={}
  for q in ['startOffset','duration']:
   a=attrs[q];v=a['value'][0];ck('C typed hour quantity '+n['id']+q,'ISQBase::DurationValue' in a['types'] and v.get('operator')=='[' and v['arguments'][1]['referent']['qualified']=='SI::hour');vals[q]=v['arguments'][0]['value']
  ck('C printed task duration '+n['id'],vals['duration']==n['duration_h']);ck('C chart offset '+n['id'],vals['startOffset']==n['start_h'])
  alloc=next(e for e in es if e['kind']=='AllocationUsage' and end(e['source'])==n['id']);ck('C crew assignment '+n['id'],end(alloc['targets'][0])==n['crew'])
  tasks.append((n['id'],n['crew'],vals['startOffset'],vals['duration']))
 def metrics(ts):return round(sum(t[3] for t in ts),6),round(max(t[2]+t[3] for t in ts),6)
 ck('C independently printed labor/makespan',metrics(tasks)==(3.6,1.0))
 ck('C no overlapping intervals per source crew code',all(r!=rr or st+d<=ss+1e-9 or ss+dd<=st+1e-9 for (id,r,st,d),(ii,rr,ss,dd) in itertools.combinations(tasks,2)))
 mut=copy.deepcopy(tasks);id,r,st,d=mut[7];mut[7]=(id,r,st,.8);ck('C negative altered duration rejected',metrics(mut)!=(3.6,1))
 ck('C all 11 bars preserve task quantities',len(views[keys[0]]['nodes'])==11 and all((n['start_h'],n['duration_h'],n['crew'])==(next(t for t in l['tasks'] if t['id']==n['id'])['start_h'],next(t for t in l['tasks'] if t['id']==n['id'])['duration_h'],next(t for t in l['tasks'] if t['id']==n['id'])['crew']) for n in views[keys[0]]['nodes']))
 # D endpoint categories and undirectedness against independent source endpoint sets.
 es=models[keys[1]];l=ledgers[keys[1]]
 for category,prefix,port in [('communications','DC','comm'),('electrical','DE','electrical')]:
  got={frozenset((end(e['source']),end(e['targets'][0]))) for e in es if e['kind']=='ConnectionUsage' and (e['name'] or '').startswith(prefix)};want={frozenset((n['source']+'.'+port,n['target']+'.'+port)) for n in l[category]};ck('D exact '+category+' connections',got==want)
  ck('D negative omitted connection detected '+category,len(got)>0 and got-{next(iter(got))}!=want)
 ck('D matrix exactly 30 symmetric comm cells',len(views[keys[1]]['annotations'])==30 and len({a['native_id'] for a in views[keys[1]]['annotations']})==15)
 ck('D electrical edges stay undirected',len(views[keys[1]]['edges'])==3 and all(not e['directed'] for e in views[keys[1]]['edges']))
 # E native archive provenance and client-to-supplier directions.
 es=models[keys[2]];l=ledgers[keys[2]];alloc=[e for e in es if e['kind']=='AllocationUsage'];got={(end(e['source']),end(e['targets'][0])) for e in alloc};want={(e['native_source'],e['native_target']) for e in l['allocations']};ck('E all four source allocations and directions',got==want and len(alloc)==4)
 for a in l['allocations']:
  native=next(e for e in alloc if end(e['source'])==a['native_source'] and end(e['targets'][0])==a['native_target']);ck('E preserved source XMI '+a['id'],a['id'] in native['docs'][0])
 ck('E negative reversed allocation rejected',{(y,x) for x,y in got}!=want);ck('E exactly eight mirrored cells',len(views[keys[2]]['annotations'])==8 and len({a['native_id'] for a in views[keys[2]]['annotations']})==4)
 # Presentation-to-native matrix correspondence: counts alone cannot qualify a matrix.
 for key in [keys[1],keys[2]]:
  byid={e['id']:e for e in models[key]}
  for i,a in enumerate(views[key]['annotations']):
   e=byid[a['native_id']];source,target=end(e['source']),end(e['targets'][0])
   if key==keys[1]:ok=frozenset((source.split('.')[0],target.split('.')[0]))==frozenset((a['row'],a['column']))
   else:
    rr=ledgers[key]['roles'];forward=(rr[a['row']],rr[a['column']])==(source,target);reverse=(rr[a['column']],rr[a['row']])==(source,target);ok=(forward and a['symbol']=='→') or (reverse and a['symbol']=='←')
   ck(key+' exact native matrix cell '+str(i),ok)
 for n in views[keys[0]]['nodes']:
  ck('C rendered bar scale '+n['id'],abs(n['x']-(755+660*n['start_h']))<1e-6 and abs(n['w']-660*n['duration_h'])<1e-6)
 for name,o in ledgers[keys[2]]['objects'].items():
  group,feature=ledgers[keys[2]]['roles'][name].split('.');typeName={'logical':'Logical','lan':'Lan','protocol':'Protocol'}[group];q='ApeAllocation::'+typeName+'::'+feature
  n=next(e for e in models[keys[2]] if e['kind']=='PortUsage' and e['qualified']==q)
  ck('E selected source identity on port '+name,any(o['id'] in doc for doc in n['docs']))
  if name!='ASMLCS_Control_if':ck('E public visibility preserved '+name,n['visibility']==o['visibility']=='public')

 # Independent geometry checks: node-boundary endpoints and no unrelated-node intersections.
 def on_border(p,n):
  x,y=p;xx,yy,w,h=n['x'],n['y'],n['w'],n['h'];return ((abs(x-xx)<1e-5 or abs(x-(xx+w))<1e-5) and yy-1e-5<=y<=yy+h+1e-5) or ((abs(y-yy)<1e-5 or abs(y-yy-h)<1e-5) and xx-1e-5<=x<=xx+w+1e-5)
 def intersects(a,b,n):
  x,y=a;xx,yy=b;left,top,right,bottom=n['x']+.2,n['y']+.2,n['x']+n['w']-.2,n['y']+n['h']-.2
  if x==xx:return left<x<right and max(min(y,yy),top)<min(max(y,yy),bottom)
  if y==yy:return top<y<bottom and max(min(x,xx),left)<min(max(x,xx),right)
  raise AssertionError('only orthogonal segments supported')
 for key,v in views.items():
  by={n['id']:n for n in v['nodes']}
  ck(key+' all node rectangles inside canvas',all(0<n['x'] and n['x']+n['w']<v['width'] and 0<n['y'] and n['y']+n['h']<v['height'] for n in by.values()))
  for e in v['edges']:
   ck(key+' endpoint boundary '+e['id'],on_border(e['points'][0],by[e['source']]) and on_border(e['points'][-1],by[e['target']]))
   hits=[n['id'] for n in by.values() if n['id'] not in [e['source'],e['target']] and any(intersects(a,b,n) for a,b in zip(e['points'],e['points'][1:]))]
   ck(key+' unrelated node crossings '+e['id'],not hits,hits)
 return {'status':'pass','source_and_geometry_assertions':len(checks),'views':len(keys),'checks':checks}
