"""Bounded selected-source fidelity, not complete SysML semantic equivalence."""
from pathlib import Path
import json,xml.etree.ElementTree as E,hashlib,re,base64,zlib
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference-extension'
def local(t):return t.rsplit('}',1)[-1]
def attr(e,k):return next((v for n,v in e.attrib.items() if n.startswith('{') and local(n)==k),None)
def check(d=None,g=None,native=None,model=None):
 d=d or json.loads((P/'source/projection.json').read_text());g=g or json.loads((P/'rendered/05-tmt-exposure.geometry.json').read_text());native=native or json.loads((P/'validation/tmt-exposure-native-semantics.json').read_text());model=model or (P/'derived/tmt-exposure.sysml').read_text()
 receipt=json.loads((P/'validation/native-inventory-inputs.json').read_text())['models']['tmt-exposure']
 if hashlib.sha256(model.encode()).hexdigest()!=receipt['model_sha256']:raise ValueError('Model changed after actual native inventory; regenerate parser/native evidence')
 if hashlib.sha256((P/'validation'/receipt['native_semantic_file']).read_bytes()).hexdigest()!=receipt['native_semantic_sha256']:raise ValueError('Native inventory bytes changed; recheck actual tool evidence')
 root=E.parse(P/'source/tmt-exposure.xml').getroot();idx={attr(e,'id'):e for e in root.iter() if attr(e,'id')};activity=idx[d['activity_id']]
 original_edges={(attr(e,'id'),attr(e,'type'),e.get('source'),e.get('target')) for e in activity if local(e.tag)=='edge'}
 ledger_edges={(e['id'],e['kind'],e['source'],e['target']) for e in d['edges']}
 drawn_edges={(e['source_id'],e['flow_type'],e['source'],e['target']) for e in g if e['kind']=='edge'}
 if not original_edges==ledger_edges==drawn_edges or len(original_edges)!=7:raise ValueError('Original control/object flow correspondence changed')
 mapping={'uml:InitialNode':'initial','uml:ActivityFinalNode':'final','uml:SendSignalAction':'send','uml:AcceptEventAction':'accept','uml:ActivityParameterNode':'parameter','uml:ForkNode':'fork','uml:JoinNode':'join'}
 kinds={c['source_id']:c['kind'] for c in g}
 for node in d['nodes']:
  if attr(idx[node['id']],'type')!=node['kind'] or kinds.get(node['id'])!=mapping[node['kind']]:raise ValueError('Lost/changed Activity node notation')
 send=next(n for n in d['nodes'] if n['kind']=='uml:SendSignalAction');source=idx[send['id']]
 if send['onPort']!=source.get('onPort') or idx[send['onPort']].get('name')!='PEAS2SHOut':raise ValueError('Changed original onPort')
 expected={('start','exposureFork'),('exposureFork','sendCommand'),('exposureFork','awaitAck'),('sendCommand','exposureJoin'),('awaitAck','exposureJoin'),('exposureJoin','done')}
 pairs={(x['source'].rsplit('::',1)[-1],x['targets'][0].rsplit('::',1)[-1]) for x in native if x['kind']=='SuccessionAsUsage'}
 if pairs!=expected or sum(x['kind']=='SuccessionAsUsage' for x in native)!=6:raise ValueError('Native fork/join successions changed')
 ns=next(x for x in native if x['kind']=='SendActionUsage')
 if ns['sender']!='TMTExposureDerived::PEASContext::PEAS2SHOut':raise ValueError('Native sender does not resolve source port')
 if 'new SH_Take_exposure_Cmd(dit) via PEAS2SHOut' not in model:raise ValueError('Lost input payload or port')
 # No receive port in the selected source; do not derive one.
 if re.search(r'action awaitAck accept SH_Take_exposure_Ack\s+(?:via|from)',model):raise ValueError('Invented receive endpoint')
 if re.search(r'first\s+sendCommand\s+then\s+awaitAck',model):raise ValueError('Serialized fork branches')
 if {(a,b) for a,b in re.findall(r'first\s+(\w+)\s+then\s+(\w+)\s*;',model)}!=expected:raise ValueError('Derived control graph changed')
 sv=E.parse(P/'rendered/05-tmt-exposure.svg').getroot()
 sg={(e.get('data-source-id'),e.get('data-flow-type'),e.get('data-source'),e.get('data-target')) for e in sv.iter() if local(e.tag)=='polyline'}
 if sg!=original_edges:raise ValueError('SVG flow endpoints changed')
 dx=E.parse(P/'rendered/05-tmt-exposure.drawio').getroot()
 dg={(e.get('sourceId'),e.get('flowType'),e.get('source'),e.get('target')) for e in dx.iter('mxCell') if e.get('edge')=='1'}
 if dg!=original_edges:raise ValueError('Editable flow endpoints changed')
 final_id=next(n['id'] for n in d['nodes'] if n['kind']=='uml:ActivityFinalNode')
 final_cell=next(e for e in dx.iter('mxCell') if e.get('sourceId')==final_id)
 encoded=re.search(r'shape=stencil\(([^)]+)\)',final_cell.get('style',''))
 if not encoded:raise ValueError('Editable activity-final glyph is not a bullseye')
 glyph=E.fromstring(zlib.decompress(base64.b64decode(encoded[1]),-15))
 if [e.get('color') for e in glyph.iter('fillcolor')]!=['#FFFFFF','#172F45'] or len(list(glyph.iter('ellipse')))!=2:raise ValueError('Editable activity-final glyph lost white ring/filled center')
 evaluation=json.loads((P/'validation/timing-evaluation.json').read_text())
 if [(e['input_seconds'],e['actual_boolean']) for e in evaluation['rows']]!=[(1799,True),(1800,True),(1801,False)]:raise ValueError('Wrong actual native timing boundary result')
 return {'source_nodes':7,'source_edges':7,'native_successions':6,'native_resolved_send_port':True,'native_timing_boundaries':3,'scope':'bounded slice correspondence; no behavior simulation or full graphical conformance'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
