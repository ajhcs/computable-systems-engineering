import copy,sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import engineering_references as source
import check_engineering_references as pack
class EngineeringReferenceTests(unittest.TestCase):
 def setUp(self): self.d=json.loads((source.PACK/'source/projection.json').read_text())
 def test_matched_pack(self):self.assertEqual(len(pack.check_pack()['checks']),4)
 def test_abort_scope_drift_rejected(self):
  t=next(t for t in self.d['slices']['tmt-maintenance']['transitions'] if any(s['name']=='Abort' for s in t['signals']))
  t['source_name']='Narrow Band Phasing'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_event_drift_rejected(self):
  self.d['slices']['tmt-maintenance']['transitions'][0]['signals'][0]['name']='Completion'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_strict_predicate_substitution_rejected(self):
  self.d['slices']['tmt-timing']['source_expression']='p1<maxTime'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_2016_default_mix_rejected(self):
  self.d['slices']['tmt-timing']['limit_seconds']=3000
  with self.assertRaises(ValueError):source.check(self.d)
 def test_cardinality_drift_rejected(self):
  p=next(p for p in self.d['slices']['ape-composition']['parts'] if p['type_name']=='PositionActuator');p['upper']=180
  with self.assertRaises(ValueError):source.check(self.d)
 def test_invented_actuator_owner_rejected(self):
  self.d['slices']['ape-composition']['parts'][0]['owner_id']='Segment'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_missing_optical_connector_rejected(self):
  self.d['slices']['ape-optical']['connectors'].pop()
  with self.assertRaises(ValueError):source.check(self.d)
 def test_nested_path_drift_rejected(self):
  x=next(x for x in self.d['slices']['ape-optical']['trace'] if x['id']=='_16_6_1_382e050d_1263291033578_413964_11573')
  x['attributes']['propertyPath']='invented-direct-lens'
  with self.assertRaises(ValueError):pack.check_pack(self.d)
 def test_fixed_binding_rejected_as_class_default(self):
  text=(source.PACK/'derived/tmt-timing.sysml').read_text()
  with self.assertRaises(ValueError):pack.check_timing_translation(text.replace('Real default := 1800.0','Real = 1800.0'))
 def test_fixed_initial_value_rejected_as_class_default(self):
  text=(source.PACK/'derived/tmt-timing.sysml').read_text()
  with self.assertRaises(ValueError):pack.check_timing_translation(text.replace('Real default := 1800.0','Real := 1800.0'))
 def test_unverified_refine_claim_rejected(self):
  text=(source.PACK/'derived/tmt-timing.sysml').read_text()+' doc /* v1 refine link remains in source trace */'
  with self.assertRaises(ValueError):pack.check_timing_translation(text)
 def test_owner_role_in_child_compartment_rejected(self):
  cells=json.loads((source.PACK/'rendered/03-ape-composition.geometry.json').read_text())
  parts=self.d['slices']['ape-composition']['parts'];p=next(p for p in parts if p['name']=='seg')
  label=next(c for c in cells if c['kind']=='text' and c.get('source_id')==p['id'])
  box=next(c for c in cells if c['kind']=='box' and c.get('source_id')==p['type_id'])
  label.update(x=box['x']+16,y=box['y']+85)
  with self.assertRaises(ValueError):pack.check_composition_notation(cells,parts)
 def test_context_visibility_widening_rejected(self):
  text=(source.PACK/'derived/ape-optical.sysml').read_text()
  for role in ['ut3','ape_t']:
   with self.subTest(role=role):
    with self.assertRaises(ValueError):pack.check_optical_translation(text.replace('private part '+role,'part '+role))
 def test_missing_proxy_stereotype_rejected(self):
  self.d['slices']['ape-optical']['port_stereotypes'].pop()
  with self.assertRaises(ValueError):source.check(self.d)
 def test_missing_proxy_trace_rejected(self):
  s=self.d['slices']['ape-optical'];sid=s['port_stereotypes'][0]['id']
  s['trace']=[r for r in s['trace'] if r['id']!=sid]
  with self.assertRaises(ValueError):source.check(self.d)
 def test_port_translation_qualification_required(self):
  text=(source.PACK/'derived/ape-optical.sysml').read_text()
  with self.assertRaises(ValueError):pack.check_optical_translation(text.replace('Original untyped SysML 1.6 ProxyPort','Original untyped port',1))
 def test_source_boundary_discrepancy(self):
  s=self.d['slices']['tmt-timing'];self.assertEqual(s['source_expression'],'p1<=maxTime');self.assertEqual(s['limit_seconds'],1800)
  self.assertEqual([(v,v<=s['limit_seconds'],v<1800) for v in [1799,1800,1801]],[(1799,True,True),(1800,True,False),(1801,False,False)])
if __name__=='__main__':unittest.main()
