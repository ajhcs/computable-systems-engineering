"""Selected original message-order fidelity; timing and engine equivalence excluded."""
from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference-extension'
def local(s):return s.rsplit('}',1)[-1]
def xa(e,k):return next((v for n,v in e.attrib.items() if n.startswith('{') and local(n)==k),None)
def duration_record_semantics(e):
 """Exact selected original fields/children, excluding formatting and vendor extensions."""
 return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[duration_record_semantics(c) for c in e if local(c.tag)!='Extension']]
def check_duration_closure(root,d=None):
 d=d or json.loads((P/'source/sequence-projection.json').read_text())
 identified=[e for e in root.iter() if xa(e,'id')]
 if len({xa(e,'id') for e in identified})!=len(identified):raise ValueError('Duplicate selected source ID')
 idx={xa(e,'id'):e for e in identified}
 receipt=json.loads((P/'validation/sequence-duration-source-receipt.json').read_text())
 constraints=[e for e in root.iter() if xa(e,'type')=='uml:DurationConstraint']
 if len(constraints)!=3:raise ValueError('Lost selected duration constraint')
 duration_ids=[];literal_ids=[];minimum_values=[];observation_ids=set()
 for constraint in constraints:
  intervals=[e for e in constraint if xa(e,'type')=='uml:DurationInterval']
  if len(intervals)!=1:raise ValueError('Lost selected interval specification')
  for role in ['min','max']:
   id=intervals[0].get(role)
   if id not in idx or xa(idx[id],'type')!='uml:Duration':raise ValueError('Dangling selected duration '+role+' reference')
   duration=idx[id];duration_ids.append(id)
   for obs in [e for e in duration if local(e.tag)=='observation']:
    ref=xa(obs,'idref')
    if ref not in idx or xa(idx[ref],'type')!='uml:DurationObservation':raise ValueError('Dangling selected duration observation')
    observation_ids.add(ref)
   literals=[e for e in duration if xa(e,'type')=='uml:LiteralString']
   if role=='min':
    if len(literals)!=1:raise ValueError('Missing original minimum LiteralString')
    minimum_values.append(literals[0].get('value'));literal_ids.append(xa(literals[0],'id'))
   elif any(local(e.tag)=='expr' for e in duration):raise ValueError('Source maximum gained an invented value expression')
  # Constrained messages and observation event references must remain within this bundle.
  for scope in [constraint]+[idx[id] for id in observation_ids]:
   for e in scope.iter():
    ref=xa(e,'idref')
    if ref and ref not in idx:raise ValueError('Dangling selected duration/message event reference')
 if len(set(duration_ids))!=6 or len(set(literal_ids))!=3 or len(observation_ids)!=6:raise ValueError('Incomplete selected duration closure')
 if sorted(minimum_values)!=['2000s','60s','60s']:raise ValueError('Original raw duration strings changed')
 if set(duration_ids)!=set(d['retained_duration_record_ids']) or set(literal_ids)!=set(d['retained_duration_literal_ids']):raise ValueError('Duration projection closure drift')
 if d['retained_original_records']!=len(identified) or len(identified)!=37:raise ValueError('Retained record count drift')
 if {r['id'] for r in receipt['duration_records']}!=set(duration_ids):raise ValueError('Duration source receipt scope drift')
 for row in receipt['duration_records']:
  digest=hashlib.sha256(json.dumps(duration_record_semantics(idx[row['id']]),separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
  if digest!=row['original_semantic_sha256']:raise ValueError('Appended duration differs from pinned original record')
 return {'duration_records':6,'literal_string_records':3,'minimum_raw_values':minimum_values,'maxima_without_value_expressions':3,'closed_observation_references':6,'retained_original_records':37}

def check(d=None,native=None,model=None):
 d=d or json.loads((P/'source/sequence-projection.json').read_text());native=native or json.loads((P/'validation/tmt-sequence-native-semantics.json').read_text());model=model or (P/'derived/tmt-sequence-order.sysml').read_text()
 receipt=json.loads((P/'validation/native-inventory-inputs.json').read_text())['models']['tmt-sequence-order']
 if hashlib.sha256(model.encode()).hexdigest()!=receipt['model_sha256']:raise ValueError('Model changed after actual native inventory; regenerate parser/native evidence')
 if hashlib.sha256((P/'validation'/receipt['native_semantic_file']).read_bytes()).hexdigest()!=receipt['native_semantic_sha256']:raise ValueError('Native inventory bytes changed; recheck actual tool evidence')
 xml=E.parse(P/'source/tmt-sequence-order.xml').getroot();idx={xa(e,'id'):e for e in xml.iter() if xa(e,'id')};i=idx[d['interaction_id']]
 duration_closure=check_duration_closure(xml,d)
 original=[]
 for line in [e for e in i if local(e.tag)=='lifeline']:
  original.append([idx[xa(c,'idref')].get('message') for c in line if local(c.tag)=='coveredBy'])
 ids=[m['id'] for m in d['messages']]
 if original!=[ids,ids] or [m['signal'] for m in d['messages']]!=['Abort','Maintenance Alignment','Abort']:raise ValueError('Source lifeline message order drift')
 for m in d['messages']:
  e=idx[m['id']]
  if (m['sort'],m['send_event'],m['receive_event'],m['signature_id'])!=(e.get('messageSort'),e.get('sendEvent'),e.get('receiveEvent'),e.get('signature')) or m['sort']!='asynchSignal':raise ValueError('Original message endpoints/sort drift')
  if m['signal']!=idx[m['signature_id']].get('name'):raise ValueError('Signal identity drift')
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
 svg=E.parse(P/'rendered/06-tmt-sequence-order.svg').getroot();drawn=[e for e in svg.iter() if e.get('data-sort')]
 if [e.get('data-source-id') for e in drawn]!=ids:raise ValueError('Rendered order drift')
 for m,e in zip(d['messages'],drawn):
  if (e.get('data-send-event'),e.get('data-receive-event'),e.get('data-sort'))!=(m['send_event'],m['receive_event'],m['sort']):raise ValueError('Rendered event endpoint drift')
 dx=E.parse(P/'rendered/06-tmt-sequence-order.drawio').getroot();cells=[e for e in dx.iter('mxCell') if e.get('edge')=='1']
 if [(e.get('sourceId'),e.get('sendEvent'),e.get('receiveEvent'),e.get('value'),e.get('messageSort')) for e in cells]!=[(m['id'],m['send_event'],m['receive_event'],m['signal'],m['sort']) for m in d['messages']]:raise ValueError('Editable exchange drift')
 if len(d['duration_constraints'])!=3 or any(c['disposition']!='source-only; not transcribed as exact timed assertions' for c in d['duration_constraints']):raise ValueError('Lost source-only duration distinction')
 return {'original_messages':3,'original_occurrence_endpoints':6,'native_resolved_endpoints':6,'native_local_successions':4,'source_only_duration_constraints':3,'scope':'selected untimed exchange order; no asynchSignal simulation or complete timed migration'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
