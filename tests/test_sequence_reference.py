import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_sequence_reference as c
class SequenceTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((c.P/'source/sequence-facts.json').read_text());self.n=json.loads((c.P/'validation/tmt-sequence-native-semantics.json').read_text());self.m=(c.P/'derived/tmt-sequence-order.sysml').read_text()
 def test_curated_facts_and_saved_native_order(self):
  result=c.check();self.assertEqual((result['curated_messages'],result['curated_occurrence_endpoints'],result['saved_native_resolved_endpoints']),(3,6,6))
 def test_curated_participant_name_drift_rejected(self):
  self.d['lifelines'][0]['name']='wrongParticipant'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_curated_peas_visibility_widening_rejected(self):
  self.d['lifelines'][1]['visibility']='public'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_curated_participant_identity_substitution_rejected(self):
  self.d['lifelines'][0]['id']=self.d['lifelines'][1]['id']
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_curated_represented_property_substitution_rejected(self):
  self.d['lifelines'][1]['represents']=self.d['lifelines'][0]['represents']
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_explicit_empty_inputs_do_not_load_defaults(self):
  for field,value in [('d',{}),('native',[]),('model','')]:
   with self.subTest(field=field):
    with self.assertRaises(ValueError):c.check(**{field:value})
 def test_invalid_input_types_rejected(self):
  for field,value in [('d',[]),('native',{}),('model',[]),('native',[{}])]:
   with self.subTest(field=field,value=value):
    with self.assertRaises(ValueError):c.check(**{field:value})
 def test_order_drift(self):
  self.d['messages'].reverse()
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_message_sort_changed(self):
  self.d['messages'][0]['sort']='synchCall'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_native_target_changed(self):
  f=next(f for f in self.n if f['kind']=='FlowUsage');next(x for x in f['owned_feature_references'] if x['name']=='targetEvent')['subsetted'][0]['chain'][-1]='wrong'
  with self.assertRaises(ValueError):c.check(native=self.n)
 def test_native_signal_type_changed(self):
  next(f for f in self.n if f['kind']=='FlowUsage')['payload_type']=['TMTSequenceOrderDerived::Wrong']
  with self.assertRaises(ValueError):c.check(native=self.n)
 def test_invented_exact_timer(self):
  with self.assertRaises(ValueError):c.check(model=self.m+' attribute exactDelay = 60;')
 def test_private_visibility_widening(self):
  with self.assertRaises(ValueError):c.check(model=self.m.replace('private part peas','part peas'))
 def test_source_xml_in_json_rejected(self):
  self.d['duration_constraints']=[{'source_xml':'<ownedRule />'}]
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_timing_scope_cannot_be_widened(self):
  self.d['timing_scope']='exact 60 seconds'
  with self.assertRaises(ValueError):c.check(d=self.d)
 def test_local_event_endpoint_reorder_rejected(self):
  self.d['lifelines'][0]['ordered_events'].reverse()
  with self.assertRaises(ValueError):c.check(d=self.d)
if __name__=='__main__':unittest.main()
