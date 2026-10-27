import sys,unittest,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_exposure_reference as c
class ExposureTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((c.P/'source/action-facts.json').read_text());self.g=json.loads((c.P/'rendered/05-tmt-exposure.geometry.json').read_text());self.n=json.loads((c.P/'validation/tmt-exposure-native-semantics.json').read_text());self.m=(c.P/'derived/tmt-exposure.sysml').read_text()
 def test_curated_facts_saved_native_and_presentations(self):
  result=c.check();self.assertEqual((result['curated_nodes'],result['curated_edges'],result['saved_native_successions']),(7,7,6))
 def test_two_node_inventory_cannot_claim_seven(self):
  self.d['nodes']=[n for n in self.d['nodes'] if n['kind'] in {'uml:SendSignalAction','uml:ActivityFinalNode'}]
  self.assertEqual(len(self.d['nodes']),2)
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_each_missing_selected_node_rejected(self):
  for node in self.d['nodes']:
   with self.subTest(kind=node['kind']):
    changed=copy.deepcopy(self.d);changed['nodes']=[n for n in changed['nodes'] if n['id']!=node['id']]
    with self.assertRaises(ValueError):c.check(d=changed)
 def test_replaced_node_identity_rejected(self):
  self.d['nodes'][0]['id']='invented-initial'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_duplicate_node_identity_rejected(self):
  self.d['nodes'][-1]=copy.deepcopy(self.d['nodes'][0])
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_node_kind_substitution_rejected(self):
  self.d['nodes'][0]['kind']='uml:ForkNode'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_explicit_empty_inputs_do_not_load_defaults(self):
  for field,value in [('d',{}),('g',[]),('native',[]),('model','')]:
   with self.subTest(field=field):
    with self.assertRaises(ValueError):c.check(**{field:value})
 def test_invalid_input_types_rejected(self):
  for field,value in [('d',[]),('g',{}),('native',{}),('model',[]),('native',[{}])]:
   with self.subTest(field=field,value=value):
    with self.assertRaises(ValueError):c.check(**{field:value})
 def test_missing_object_flow(self):
  self.d['edges']=[e for e in self.d['edges'] if e['kind']!='uml:ObjectFlow']
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_lost_join_glyph(self):
  next(e for e in self.g if e['kind']=='join')['kind']='fork'
  with self.assertRaises(ValueError):c.check(g=self.g)
 def test_serialized_native_branches(self):
  x=next(e for e in self.n if e['kind']=='SuccessionAsUsage' and e['source'].endswith('::exposureFork') and e['targets'][0].endswith('::awaitAck'));x['source']=x['source'].replace('exposureFork','sendCommand')
  with self.assertRaises(ValueError):c.check(native=self.n)
 def test_invented_receive_port(self):
  with self.assertRaises(ValueError):c.check(model=self.m.replace('accept SH_Take_exposure_Ack {','accept SH_Take_exposure_Ack via PEAS2SHOut {'))
 def test_changed_send_port(self):
  with self.assertRaises(ValueError):c.check(model=self.m.replace('via PEAS2SHOut','via AnotherPort'))
 def test_control_flow_endpoint_drift(self):
  next(e for e in self.g if e['kind']=='edge')['target']='wrong'
  with self.assertRaises(ValueError):c.check(g=self.g)
if __name__=='__main__':unittest.main()
