"""Presentation builder: all selected nodes/relations/numbers originate in linked v2 facts.
Frozen ledgers supply source provenance, explanatory labels and layout only.
"""
from pathlib import Path
import argparse,json,re,html,textwrap,hashlib,xml.etree.ElementTree as E
import drawing
from cases import KEYS, require_case, require_release_scope
R=Path(__file__).resolve().parents[1]
def esc(x):return html.escape(str(x),quote=True)
def endpoint(ref):
 ch=ref.get('chain',[])
 return '.'.join(x.rsplit('::',1)[-1] for x in ch) if ch else (ref['qualified'] or '').rsplit('::',1)[-1]
def guard(e):
 if e['kind']=='FeatureReferenceExpression':return endpoint(e['referent'])
 if e.get('operator')=='not':return 'not '+guard(e['arguments'][0])
 raise ValueError(e)
def quantity(e):
 if e.get('operator')!='[' or e['arguments'][1]['referent']['qualified']!='SI::hour':raise ValueError('Unsupported duration expression')
 return e['arguments'][0]['value']
def load(key):
 require_case(key)
 d=json.loads((R/'native'/(key+'.facts.json')).read_text())
 if d.get('parse_has_errors') is not False or d['source_sha256']!=hashlib.sha256((R/'models'/(key+'.sysml')).read_bytes()).hexdigest():raise ValueError('Stale or invalid native facts: '+key)
 return d['elements']
from drawing import Drawing, THEMES, INK, MUTED

def main():
 p=argparse.ArgumentParser(description='Generate C/D/E SVG, view JSON, notes and editable geometry into a new explicit directory. No browser or PNG rendering.')
 p.add_argument('--output',type=Path,required=True)
 args=p.parse_args()
 require_release_scope(R)
 output=args.output.expanduser().resolve()
 if output==R or R in output.parents:
  p.error('Output must be outside the curated reference directory')
 if output.exists():
  p.error('Output must be a new directory; existing artifacts are never overwritten')
 output.mkdir(parents=True)
 drawing.OUT=output
 es=load(KEYS[0]);ledger=json.loads((R/'source/C-ledger.json').read_text());ns={e['name']:e for e in es if e['name'] and re.fullmatch('C[0-9]{2}',e['name'])};alloc={endpoint(e['source']):endpoint(e['targets'][0]) for e in es if e['kind']=='AllocationUsage'};tasks=[]
 for id,n in ns.items():
  attrs={e['qualified'].rsplit('::',1)[-1]:e for e in es if e['owner']==n['qualified'] and e['kind']=='AttributeUsage' and e['value']}
  tasks.append({'id':id,'native':n,'label':n['docs'][0].split('; source task')[0],'crew':alloc[id],'start':quantity(attrs['startOffset']['value'][0]),'duration':quantity(attrs['duration']['value'][0])})
 tasks.sort(key=lambda t:t['id']);d=Drawing(KEYS[0],1520,1105,'Maintenance schedule','')
 d.body.append('<g data-region="equipment-details">');d.rect(48,124,1424,73,'#fff','#c3cdda',6)
 for x,label,value in [(68,'EQUIPMENT','VC distiller'),(435,'LOCATION','Engine room 3'),(835,'MAINTENANCE','Scheduled · 200 hours')]:
  d.text(x,145,label,11.5,MUTED,weight=600);d.text(x,177,value,18,INK,weight=500)
 d.body.append('</g><g data-region="schedule-totals">');d.rect(1055,22,417,78,'#edf1f6','#c3cdda',6)
 d.body.append('<line x1="1273" y1="34" x2="1273" y2="88" stroke="#c3cdda"/>')
 for x,label,value in [(1080,'LABOR',f'{sum(t["duration"] for t in tasks):.1f} h'),(1310,'ELAPSED',f'{max(t["start"]+t["duration"] for t in tasks):.1f} h')]:
  d.text(x,44,label,12,MUTED,weight=600);d.text(x,83,value,32,INK,weight=500)
 d.body.append('</g>')
 x0=755;scale=660
 # Complete, alternating rows span the register and time panel.
 for i in range(11):
  d.rect(48,280+i*66,1424,66,'#ffffff' if i%2==0 else '#edf1f6')
  d.body.append(f'<line x1="48" y1="{346+i*66}" x2="1472" y2="{346+i*66}" stroke="#dde3eb"/>')
 for i in range(11):
  x=x0+i*scale/10;d.body.append(f'<line x1="{x}" y1="265" x2="{x}" y2="1006" stroke="{ "#a6b3c4" if i in [0,5,10] else "#d9e0e9"}"/>');d.text(x,247,f'{i/10:.1f}',14,MUTED,'middle',mono=True)
 d.text(x0,215,'ELAPSED TIME  /  HOURS',12,MUTED,weight=600)
 for col,x in [('ID',64),('MAINTENANCE TASK',120),('CREW',549),('DURATION (h)',694)]:d.text(x,247,col,12,MUTED,'end' if col.startswith('DURATION') else 'start',600)
 crewcolors={'A2':'#185b9d','B1':'#985909','C1':'#13776c','D1':'#70409d'};crewthemes={'A2':'blue','B1':'amber','C1':'teal','D1':'purple'}
 for i,t in enumerate(tasks):
  y=313+i*66;crew=t['crew'];bg,accent,pattern=THEMES[crewthemes[crew]]
  d.text(64,y+6,t['id'],13,MUTED,mono=True,owner=t['id']);d.text(120,y+6,t['label'],18,INK,weight=500,owner=t['id'])
  d.rect(538,y-17,55,34,bg,rx=6);d.text(565.5,y+6,crew,16,accent,'middle',owner=t['id'],mono=True)
  d.text(694,y+6,f'{t["duration"]:.1f}',18,INK,'end',owner=t['id'],mono=True)
  d.box(t['id'],f'{t["duration"]:g} h',x0+t['start']*scale,y-14,t['duration']*scale,28,kind='TimedTask',fill=crewcolors[crew],native=t['native'])
  d.nodes[-1].update(start_h=t['start'],duration_h=t['duration'],crew=crew)
 d.note(0,0,'Source FFBD 37.5X3 / RAS 37.5X37. Starts are chart readings at 0.1 h resolution. Crew codes are source identifiers, not proved staffing counts. Printed food strainer wording retained; no cross-crew dependency inferred.')
 d.save()
 # D: separate source line categories; matrix removes crossings without adding hierarchy or arrow direction.
 es=load(KEYS[1]);ledger=json.loads((R/'source/D-ledger.json').read_text());ns={e['name']:e for e in es if e['kind']=='PartUsage' and e['owner']==ledger['context']};cn=[e for e in es if e['kind']=='ConnectionUsage' and e['name'] and e['name'].startswith('DC')];en=[e for e in es if e['kind']=='ConnectionUsage' and e['name'] and e['name'].startswith('DE')]
 order=list(ns);names={k:ns[k]['docs'][0].strip().removesuffix(' domain.') for k in order};d=Drawing(KEYS[1],1290,1140,'Smart Grid: two interaction layers','NIST SP 1108 · January 2010 · Fig. 3-1 · Seven domains, with undirected source relationships')
 d.body.append('<g data-panel="communication">');d.rect(32,138,1226,672,'#f7f8fa','#c3cdda',7);d.rect(33,139,1224,63,'#e5eaf2',rx=6)
 d.text(52,178,'Communication',20,INK,weight=600);d.text(1238,178,'15 undirected relationships',14,MUTED,'end');d.note(48,195,'Filled symmetric cells preserve the source’s “Secure Communication Flows” legend; they are not security verification.')
 x0,y0,cell=435,330,101
 links={frozenset((endpoint(e['source']).split('.')[0],endpoint(e['targets'][0]).split('.')[0])):e for e in cn}
 for i,k in enumerate(order):
  d.box(k,names[k],48,y0+i*66,360,58,kind='PartUsage',fill='#ffffff',native=ns[k]);d.lines(x0+i*cell+cell/2,261,textwrap.wrap(names[k],12),13,owner=k)
  for j,k2 in enumerate(order):
   x,y=x0+j*cell,y0+i*66;d.body.append(f'<rect x="{x}" y="{y}" width="{cell-3}" height="58" rx="3" fill="{"#e5eaf2" if i==j else "#fff" if i%2==0 else "#edf1f6"}" stroke="#d3dbe5"/>')
   if i==j:d.text(x+cell/2,y+35,'—',16,'#738196','middle')
   elif frozenset((k,k2)) in links:
    e=links[frozenset((k,k2))];d.body.append(f'<circle data-relation="{e["id"]}" data-row="{k}" data-col="{k2}" cx="{x+cell/2}" cy="{y+29}" r="9" fill="#126c64"><title>{esc(e["name"]+": "+names[k]+" ↔ "+names[k2])}</title></circle>');d.annotations.append({'kind':'matrix-cell','native_id':e['id'],'row':k,'column':k2})
 d.body.append('</g><g data-panel="electrical">');d.rect(32,830,1226,207,'#f7f8fa','#c3cdda',7);d.rect(33,831,1224,63,'#e5eaf2',rx=6)
 d.text(52,870,'Electrical',20,INK,weight=600);d.text(1238,870,'3 undirected connections',14,MUTED,'end');d.note(48,882,'No arrowheads in the original: ordering here does not assert one-way power flow.')
 pos={'bulkGeneration':(48,940),'transmission':(361,940),'distribution':(674,940),'customer':(987,940)}
 for k,(x,y) in pos.items():d.box(k+'-electrical',names[k],x,y,240,75,kind='PartUsage',fill='#edf3eb',native=ns[k])
 for e in en:
  a=endpoint(e['source']).split('.')[0];b=endpoint(e['targets'][0]).split('.')[0];x,y=pos[a];xx,yy=pos[b];d.edge(e['name'],a+'-electrical',b+'-electrical',[(x+240,y+37.5),(xx,yy+37.5)],native=e,directed=False,dash=True)
 d.note(48,1085,'Matrix symmetry represents the same connection twice; a blank off-diagonal cell means no line in this selected source figure.');d.note(48,1110,'Domain grouping is descriptive. Introduced view-context parts and adapter ports do not assert ownership or physical interfaces.');d.note(48,1135,'Source wording “secure” is preserved; no mandatory authority or security rule is imposed on CSE.');d.body.append('</g>');d.save()
 # E: directional source allocations, shown symmetrically with explicit direction in each cell.
 es=load(KEYS[2]);ledger=json.loads((R/'source/E-ledger.json').read_text());allocs=[e for e in es if e['kind']=='AllocationUsage'];names=['ASMLCS_Control_if','fpCtrlLan','fpImcsLan','imData','ccs','tcp/ip'];roles=ledger['roles'];inverse={v:k for k,v in roles.items()};aliases=json.loads((R/'source/display-aliases.json').read_text())['E']
 d=Drawing(KEYS[2],1510,1000,'APE interface allocation','')
 d.body.append('<g data-panel="allocation-matrix">');d.rect(32,138,1446,746,'#f7f8fa','#c3cdda',7);d.rect(33,139,1444,91,'#e5eaf2',rx=6)
 d.text(52,174,'4 allocations',18,INK,weight=600);d.text(52,205,'8 mirrored cells',14,MUTED)
 d.body.append('<g data-region="projection-key">');d.rect(447,160,26,27,'#fff','#596b81',3);d.rect(447,160,26,27,'url(#projectionTexture)',rx=3);d.text(486,179,'Interface modeled as a port',14,INK);d.body.append('</g><g data-region="direction-key">')
 d.text(1000,175,'→',22,'#126c64',weight=500);d.text(1037,175,'Row allocated to column',14,INK)
 d.text(1000,207,'←',22,'#17568f',weight=500);d.text(1037,207,'Column allocated to row',14,INK);d.body.append('</g>')
 x0,y0,cw,rh=388,350,175,82
 pair={}
 for e in allocs:
  a,b=endpoint(e['source']),endpoint(e['targets'][0]);pair[(inverse[a],inverse[b])]=e
 for i,k in enumerate(names):
  role=roles[k];group,feat=role.split('.');q=ledger['package']+'::'+{'logical':'Logical','lan':'Lan','protocol':'Protocol'}[group]+'::'+feat;n=next(e for e in es if e['qualified']==q and e['kind']=='PortUsage')
  d.box(k,k,48,y0+i*rh,310,rh-5,kind='PortUsage',fill='#ffffff',native=n)
  d.lines(x0+i*cw+cw/2,278,textwrap.wrap(aliases[k]['display'],20),15,owner=k)
  d.text(x0+i*cw+cw/2,326,k,11.5,MUTED,'middle',owner=k,mono=True)
  for j,k2 in enumerate(names):
   x,y=x0+j*cw,y0+i*rh;d.rect(x,y,cw-4,rh-5,'#e5eaf2' if i==j else '#fff' if i%2==0 else '#edf1f6','#d3dbe5',3)
   if i==j:d.text(x+cw/2,y+47,'—',16,'#738196','middle')
   elif (k,k2) in pair or (k2,k) in pair:
    e=pair.get((k,k2),pair.get((k2,k)));symbol='→' if (k,k2) in pair else '←';d.rect(x+3,y+3,cw-10,rh-11,'#d7eee9' if symbol=='→' else '#dce9f8',rx=3);d.text(x+cw/2,y+51,symbol,30,'#126c64' if symbol=='→' else '#17568f','middle',weight=500,owner=e['name']);d.annotations.append({'kind':'matrix-cell','native_id':e['id'],'row':k,'column':k2,'symbol':symbol})
 d.note(0,0,'Human-readable names are presentation aliases; native identifiers remain unchanged beneath each name. No CCS expansion or undocumented payload fields are invented.')
 for line in ledger['limits']:d.note(0,0,line)
 d.body.append('</g>');d.save()
 print('Generated three derivative SVG/geometry companions; PNG rendering and visual acceptance not run.')

if __name__=='__main__':main()
