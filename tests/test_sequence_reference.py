import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_sequence_reference as c
class SequenceTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((c.P/'source/sequence-projection.json').read_text());self.n=json.loads((c.P/'validation/tmt-sequence-native-semantics.json').read_text());self.m=(c.P/'derived/tmt-sequence-order.sysml').read_text()
 def test_source_native_and_rendered_order(self):self.assertEqual(c.check()['native_resolved_endpoints'],6)
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
 def duration_root(self):return c.E.parse(c.P/'source/tmt-sequence-order.xml').getroot()
 def test_duration_records_reference_closed(self):
  facts=c.check_duration_closure(self.duration_root())
  self.assertEqual((facts['duration_records'],facts['literal_string_records'],facts['closed_observation_references'],facts['retained_original_records']),(6,3,6,37))
 def test_each_missing_min_or_max_record_rejected(self):
  root=self.duration_root();ids=[c.xa(e,'id') for e in root if c.xa(e,'type')=='uml:Duration']
  for id in ids:
   with self.subTest(id=id):
    root=self.duration_root();root.remove(next(e for e in root if c.xa(e,'id')==id))
    with self.assertRaises(ValueError):c.check_duration_closure(root)
 def test_missing_duration_literal_rejected(self):
  root=self.duration_root();duration=next(e for e in root if c.xa(e,'type')=='uml:Duration' and any(c.xa(x,'type')=='uml:LiteralString' for x in e));duration.remove(next(x for x in duration if c.xa(x,'type')=='uml:LiteralString'))
  with self.assertRaises(ValueError):c.check_duration_closure(root)
 def test_dangling_duration_observation_rejected(self):
  root=self.duration_root();obs=next(e for e in root if c.xa(e,'type')=='uml:Duration').find('observation');obs.set(next(k for k in obs.attrib if c.local(k)=='idref'),'missing-observation')
  with self.assertRaises(ValueError):c.check_duration_closure(root)
 def test_invented_maximum_value_rejected(self):
  root=self.duration_root();interval=next(e for e in root.iter() if c.xa(e,'type')=='uml:DurationInterval');maximum=next(e for e in root if c.xa(e,'id')==interval.get('max'));ns='http://www.omg.org/spec/XMI/20131001';c.E.SubElement(maximum,'expr',{'{'+ns+'}type':'uml:LiteralString','{'+ns+'}id':'invented-max','value':'2000s'})
  with self.assertRaises(ValueError):c.check_duration_closure(root)
 def test_dangling_interval_endpoint_rejected(self):
  root=self.duration_root();next(e for e in root.iter() if c.xa(e,'type')=='uml:DurationInterval').set('min','missing-duration')
  with self.assertRaises(ValueError):c.check_duration_closure(root)
 def test_duplicate_duration_record_rejected(self):
  root=self.duration_root();import copy;root.append(copy.deepcopy(next(e for e in root if c.xa(e,'type')=='uml:Duration')))
  with self.assertRaises(ValueError):c.check_duration_closure(root)
if __name__=='__main__':unittest.main()
