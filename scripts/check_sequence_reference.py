"""Selected reviewed-derivative message-order correspondence; original source, source-style rendering, timing and engine equivalence excluded."""
from pathlib import Path
from engineering_references import validate_fact_content
import json,re,hashlib,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference-extension'
def local(s):return s.rsplit('}',1)[-1]
def xa(e,k):return next((v for n,v in e.attrib.items() if n.startswith('{') and local(n)==k),None)
# Selected participant assertions; original-source validation remains separate.
EXPECTED_PARTICIPANTS=[
 ('_18_0_5_baa02e2_1458099294143_628657_152079','_18_0_5_baa02e2_1454128060627_462855_170075','analysisDriver','public'),
 ('_18_0_5_baa02e2_1458099294144_32845_152081','_17_0_2_3_41e01aa_1389728908413_724070_61695','peas','private')]
def check(d=None,native=None,model=None):
 d=json.loads((P/'source/sequence-facts.json').read_text()) if d is None else d
 native=json.loads((P/'validation/tmt-sequence-native-semantics.json').read_text()) if native is None else native
 model=(P/'derived/tmt-sequence-order.sysml').read_text() if model is None else model
 if not isinstance(d,dict) or not d:raise ValueError('Invalid or empty curated sequence facts')
 for key,fields in [('lifelines',{'id','represents','name','visibility','ordered_messages','ordered_events'}),('messages',{'id','signal','sort','send_event','receive_event'})]:
  rows=d.get(key)
  if not isinstance(rows,list) or not rows or any(not isinstance(row,dict) or not fields<=row.keys() for row in rows):raise ValueError('Invalid or empty curated sequence '+key)
 if not isinstance(native,list) or not native or any(not isinstance(row,dict) or not isinstance(row.get('kind'),str) for row in native):raise ValueError('Invalid or empty saved native inventory')
 if not isinstance(model,str) or not model.strip():raise ValueError('Invalid or empty model text')
 receipt=json.loads((P/'validation/native-inventory-inputs.json').read_text())['models']['tmt-sequence-order']
 if hashlib.sha256(model.encode()).hexdigest()!=receipt['model_sha256']:raise ValueError('Model changed after actual native inventory; regenerate parser/native evidence')
 if hashlib.sha256((P/'validation'/receipt['native_semantic_file']).read_bytes()).hexdigest()!=receipt['native_semantic_sha256']:raise ValueError('Native inventory bytes changed; recheck actual tool evidence')
 validate_fact_content(d)
 if d.get('schema')!='reviewed-sequence-facts/1':raise ValueError('Wrong derivative sequence fact schema')
 participants=[(p['id'],p['represents'],p['name'],p['visibility']) for p in d['lifelines']]
 if participants!=EXPECTED_PARTICIPANTS:raise ValueError('Curated participant identity/name/visibility drift')
 code=re.sub(r'doc\s*/\*.*?\*/','',model,flags=re.S)
 for _,_,name,visibility in EXPECTED_PARTICIPANTS:
  matches=re.findall(r'(?:(private)\s+)?part\s+'+re.escape(name)+r'\s*\{',code)
  if len(matches)!=1 or ('private' if matches[0] else 'public')!=visibility:raise ValueError('Curated participant differs from bounded model visibility/name')
 ids=[m['id'] for m in d['messages']]
 if [line['ordered_messages'] for line in d['lifelines']]!=[ids,ids] or [m['signal'] for m in d['messages']]!=['Abort','Maintenance Alignment','Abort']:raise ValueError('Curated local message order drift')
 if len(d['messages'])!=3 or any(m['sort']!='asynchSignal' for m in d['messages']):raise ValueError('Curated message sort/count drift')
 expected_events=[[m['send_event'] for m in d['messages']],[m['receive_event'] for m in d['messages']]]
 if [line['ordered_events'] for line in d['lifelines']]!=expected_events:raise ValueError('Curated endpoint order drift')
 flows=[x for x in native if x['kind']=='FlowUsage'];prefix='TMTSequenceOrderDerived::maintenanceMessageOrder::'
 expected={'initialAbort':('initialAbortSent','initialAbortReceived','Abort'),'maintenance':('maintenanceSent','maintenanceReceived','MaintenanceAlignment'),'finalAbort':('finalAbortSent','finalAbortReceived','Abort')}
 if {x['name'] for x in flows}!=set(expected) or len(flows)!=3:raise ValueError('Lost native messages')
 for f in flows:
  sent,received,payload=expected[f['name']]
  if f['payload_type']!=['TMTSequenceOrderDerived::'+payload]:raise ValueError('Wrong native payload type')
  refs={x['name']:x for x in f['owned_feature_references']}
  if refs['sourceEvent']['subsetted'][0]['chain']!=[prefix+'analysisDriver',prefix+'analysisDriver::'+sent] or refs['targetEvent']['subsetted'][0]['chain']!=[prefix+'peas',prefix+'peas::'+received]:raise ValueError('Wrong resolved native message endpoint')
 successions={(x['source'],x['targets'][0]) for x in native if x['kind']=='SuccessionAsUsage'}
 expected_succ={(prefix+p+'::'+a,prefix+p+'::'+b) for p,a,b in [('analysisDriver','initialAbortSent','maintenanceSent'),('analysisDriver','maintenanceSent','finalAbortSent'),('peas','initialAbortReceived','maintenanceReceived'),('peas','maintenanceReceived','finalAbortReceived')]}
 if successions!=expected_succ or sum(x['kind']=='SuccessionAsUsage' for x in native)!=4:raise ValueError('Native local event order drift')
 if 'private part peas' not in model:raise ValueError('Original peas property visibility widened')
 if re.search(r'\battribute\b|\bconstraint\b|\bafter\b',re.sub(r'doc\s*/\*.*?\*/','',model,flags=re.S)):raise ValueError('Invented timed/computed assertion in order-only slice')
 if d['timing_scope']!='excluded; original duration constraints are not transcribed as executable assertions' or d['excluded_duration_constraints']!=3:raise ValueError('Lost untimed scope distinction')
 return {'curated_messages':len(d['messages']),'curated_occurrence_endpoints':sum(len(p['ordered_events']) for p in d['lifelines']),'saved_native_resolved_endpoints':len(flows)*2,'saved_native_local_successions':len(successions),'excluded_duration_constraints':d['excluded_duration_constraints'],'claim_scope':'reviewed-derivative-correspondence','original_source_validation':'not_run; raw source inputs excluded','source_style_rendering':'not_distributed; fresh supported rendering is pending','scope':'selected untimed derivative versus saved native facts; no asynchSignal simulation or complete timed migration'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
