"""Bounded cross-representation checks for four pinned real engineering slices."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
import engineering_references as source
PACK=source.PACK
NAMES={'tmt-maintenance':'01-tmt-maintenance','tmt-timing':'02-tmt-timing','ape-composition':'03-ape-composition','ape-optical':'04-ape-optical'}
def require(ok,message):
 if not ok:raise ValueError(message)
def inside(point,cell,tol=2):
 x,y=point
 return cell['x']-tol<=x<=cell['x']+cell['w']+tol and cell['y']-tol<=y<=cell['y']+cell['h']+tol
def declarations(text):
 return re.sub(r'doc /\*.*?\*/','',text,flags=re.S)
def check_timing_translation(text):
 require(bool(re.search(r'attribute\s+maintenanceAlignmentTimeLimit\s*:\s*Real\s+default\s*:=\s*1800\.0\s*\{',declarations(text))),'Class default must remain overridable initialization, not fixed binding')
 require('p1 <= maxTime' in declarations(text),'Derived timing predicate drift')
 require('v1 refine link remains in source trace' not in text,'Unverified refine link claimed')
def check_optical_translation(text):
 code=declarations(text)
 for role,type_ in [('ut3','UnitTelescope'),('ape_t','APE_Telescope')]:
  require(bool(re.search(r'private\s+part\s+'+role+r'\s*:\s*'+type_,code)),'Owning-context private visibility drift: '+role)
 for role,type_ in [('lg1','LensGroup1'),('ada','NasmythAdapter')]:
  require(bool(re.search(r'(?<!private )part\s+'+role+r'\s*:\s*'+type_,code)) and not re.search(r'private\s+part\s+'+role+r'\s*:',code),'Nested-end visibility adaptation drift: '+role)
 require('flow ' not in code,'Invented optical item flow')
 require(text.count('Original untyped SysML 1.6 ProxyPort')==3,'Partial port semantics not disclosed in v2')
def check_composition_notation(cells,parts):
 child_boxes=[c for c in cells if c['kind']=='box' and c.get('source_id') in {p['type_id'] for p in parts}]
 for p in parts:
  label=(p['name']+' ['+str(p['lower'])+']') if p['name'] else '[1] (implicit)'
  rows=[c for c in cells if c['kind']=='text' and c.get('source_id')==p['id'] and c['value']==label]
  require(len(rows)==1,'Composition role/cardinality not at traced association end')
  row=rows[0];edge=next(c for c in cells if c['kind']=='edge' and c.get('source_id')==p['id'])
  require(abs(row['x']-edge['points'][-1][0])<160 and abs(row['y']-edge['points'][-1][1])<65,'Composition label is remote from part end')
  require(not any(inside((row['x'],row['y']),box) or inside((row['x']+row['w'],row['y']+row['h']),box) for box in child_boxes),'Owner role incorrectly displayed as child classifier feature')
  if not p['name']:require('mount' not in row['value'].lower(),'Source unnamed role must remain unnamed')
def check_edge_geometry(svg,drawio,edges):
 """Match every tagged rendered/editable edge to its selected geometry path."""
 expected={e['source_id']:e['points'] for e in edges}
 require(len(expected)==len(edges),'Duplicate selected geometry edge')
 rendered=[e for e in svg.iter() if e.tag.rsplit('}',1)[-1]=='polyline' and e.get('data-source-id')]
 editable=[e for e in drawio.iter('mxCell') if e.get('edge')=='1' and e.get('source_id')]
 for label,items,key in [('SVG',rendered,'data-source-id'),('draw.io',editable,'source_id')]:
  require(len(items)==len(expected) and {e.get(key) for e in items}==set(expected),label+': selected edge inventory drift')
 for e in rendered:
  try:values=[float(v) for v in e.get('points','').replace(',',' ').split()]
  except ValueError:raise ValueError('SVG: invalid edge coordinates')
  require(len(values)>=4 and len(values)%2==0,'SVG: missing edge endpoints')
  points=[values[i:i+2] for i in range(0,len(values),2)]
  require(points==expected[e.get('data-source-id')],'SVG: selected edge coordinates differ from geometry')
 for e in editable:
  geometry=e.find('mxGeometry');require(geometry is not None,'draw.io: missing edge geometry')
  starts=geometry.findall("mxPoint[@as='sourcePoint']");ends=geometry.findall("mxPoint[@as='targetPoint']")
  require(len(starts)==len(ends)==1,'draw.io: missing or duplicate edge endpoints')
  route=geometry.find("Array[@as='points']")
  middle=list(route) if route is not None else []
  try:points=[[float(p.attrib['x']),float(p.attrib['y'])] for p in starts+middle+ends]
  except (KeyError,ValueError):raise ValueError('draw.io: invalid edge coordinates')
  sid=e.get('source_id')
  require(points==expected[sid],'draw.io: selected edge coordinates differ from geometry')
  contract=next(edge for edge in edges if edge['source_id']==sid)
  style=dict(field.split('=',1) for field in e.get('style','').split(';') if '=' in field)
  require(style.get('startArrow')==('diamond' if contract['diamond'] else 'none'),'draw.io: start glyph differs from selected geometry')
  require(style.get('endArrow')==('open' if contract['arrow'] else 'none'),'draw.io: end glyph differs from selected geometry')
  require(style.get('dashed')==str(int(contract['dash'])),'draw.io: line kind differs from selected geometry')
  if contract['diamond']:require(style.get('startFill')=='1','draw.io: composite owner diamond is not filled')
def check_pack(projection=None,pack_dir=None):
 pack=Path(pack_dir) if pack_dir is not None else PACK
 d=json.loads((pack/'source/view-facts.json').read_text()) if projection is None else projection
 require(isinstance(d,dict) and bool(d) and isinstance(d.get('slices'),dict) and set(d['slices'])==set(NAMES),'Invalid or empty curated projection')
 source.check(d)
 checks=[]
 for name,view in NAMES.items():
  s=d['slices'][name];ids=set(s['selected_ids'])
  cells=json.loads((pack/'rendered'/(view+'.geometry.json')).read_text())
  tagged=[c for c in cells if c.get('source_id')]
  require(all(c['source_id'] in ids for c in tagged),name+': untraced geometry')
  svg=ET.parse(pack/'rendered'/(view+'.svg')).getroot()
  require({e.attrib['data-source-id'] for e in svg.iter() if e.attrib.get('data-source-id')}=={c['source_id'] for c in tagged},name+': SVG trace drift')
  drawio=ET.parse(pack/'rendered'/(view+'.drawio')).getroot()
  require({e.attrib['source_id'] for e in drawio.iter() if e.attrib.get('source_id')}=={c['source_id'] for c in tagged},name+': draw.io trace drift')
  edges=[c for c in tagged if c['kind']=='edge']
  boxes={c['source_id']:c for c in tagged if c['kind'] in ['box','dot','port']}
  check_edge_geometry(svg,drawio,edges)
  if name=='tmt-maintenance':
   require(len(edges)==9,'State view must retain nine transitions')
   by_id={c['source_id']:c for c in edges}
   for t in s['transitions']:
    e=by_id[t['id']]
    require(e['arrow'],'Transition must be directional')
    require(inside(e['points'][0],boxes[t['source']]),'Wrong state source endpoint '+t['id'])
    require(inside(e['points'][-1],boxes[t['target']]),'Wrong state target endpoint '+t['id'])
   text=' '.join((pack/'derived'/('tmt-maintenance.sysml')).read_text().split())
   statements=[
    "entry; then Initializing;",
    "entry action initTimer; then 'Correcting Rigid Body and Segment Figure';",
    "first Initializing accept InitComplete do action InitCompleteEffect {",
    "first StandBy accept MaintenanceAlignmentSignal then 'Maintenance Alignment';",
    "first 'Maintenance Alignment' accept Abort then StandBy;",
    "first 'Correcting Rigid Body and Segment Figure' accept Finished do action diffTime then 'Broad Band Phasing 1um';",
    "first 'Broad Band Phasing 1um' accept Finished do action diffTime then 'Narrow Band Phasing';",
    "first 'Maintenance Alignment'.'Narrow Band Phasing' accept Finished do action FinalDiffTime then StandBy;",
    "first StandBy accept Finished then done;"
   ]
   require(all(x in text for x in statements),'Derived lifecycle drift')
  elif name=='tmt-timing':
   text=(pack/'derived/tmt-timing.sysml').read_text()
   check_timing_translation(text)
   require('bind maintenanceAlignment.maxTime = maintenanceAlignmentTimeLimit;' in text,'Limit equality drift')
   require('bind maintenanceMaximum.maintenanceAlignment.p1 = peas.tFinal;' in text,'Duration equality drift')
   require(len(edges)==2 and not any(c['arrow'] for c in edges),'Binding view must use two equality lines')
   require(s['source_expression']=='p1<=maxTime' and s['limit_seconds']==1800,'Curated timing contract drift')
  elif name=='ape-composition':
   by_id={c['source_id']:c for c in edges}
   owner='_15_0_bf10301_1202464929960_949157_5982'
   for p in s['parts']:
    e=by_id[p['id']]
    require(e['diamond'] and not e['arrow'],'Composition marker drift')
    require(inside(e['points'][0],boxes[owner]) and inside(e['points'][-1],boxes[p['type_id']]),'Composition ownership geometry drift')
   check_composition_notation(cells,s['parts'])
   text=(pack/'derived'/'ape-composition.sysml').read_text()
   require('private part seg : Segment[61]' in text and 'private part pact : PositionActuator[183]' in text and 'private part mount : Mount' in text,'Derived composition drift')
  else:
   require(len(edges)==2 and not any(c['arrow'] for c in edges),'Invented optical item flow')
   by_id={c['source_id']:c for c in edges}
   for con in s['connectors']:
    e=by_id[con['id']];roles=[x['role'] for x in con['ends']]
    require(any(inside(e['points'][0],boxes[roles[0]]) and inside(e['points'][-1],boxes[roles[1]]) or inside(e['points'][0],boxes[roles[1]]) and inside(e['points'][-1],boxes[roles[0]]) for _ in [0]),'Optical end geometry drift')
   require(s['nested_property_path']==['_15_0_3c00182_1203339836217_958479_4963','_15_1_baa02e2_1210774914160_880510_12061'],'Nested optical path drift')
   text=(pack/'derived'/'ape-optical.sysml').read_text()
   require('connect object_oif to omb.lg1.in_oif;' in text and 'connect ut3.ada.FoV_oif to ape_t.object_oif' in text,'Derived optical connector drift')
   require('port in_oif {' in text,'Lost optical port')
   check_optical_translation(text)
  receipt=json.loads((pack/'rendered/visual-checks.json').read_text())
  row=next(x for x in receipt if x['file']==view+'.svg')
  for ext,key in [('svg','svg_sha256'),('png','png_sha256')]:
   require(hashlib.sha256((pack/'rendered'/(view+'.'+ext)).read_bytes()).hexdigest()==row[key],name+': stale image receipt')
  require(not row['clipped'],name+': clipped text')
  checks.append({'slice':name,'selected_fact_ids':len(ids),'claim_scope':'reviewed derivative-to-view correspondence'})
 return {'checks':checks,'scope':'Curated derivative contracts and selected derivative declarations; original-source validation not run; not general semantic equivalence, native execution, complete requirement satisfaction, or graphical conformance.'}
if __name__=='__main__': print(json.dumps(check_pack(),indent=2))
