import copy,sys,unittest,json,tempfile,shutil
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import engineering_references as source
import check_engineering_references as pack
class EngineeringReferenceTests(unittest.TestCase):
 def setUp(self): self.d=json.loads((source.PACK/'source/view-facts.json').read_text())
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
  self.d['slices']['ape-optical']['nested_property_path']=['invented-direct-lens']
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
 def test_raw_projection_rejected(self):
  self.d['slices']['ape-optical']['records']=[{'attributes':{'name':'raw'}}]
  with self.assertRaises(ValueError):source.check(self.d)
 def test_embedded_xml_rejected(self):
  self.d['source_xml']='<ownedRule />'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_port_translation_qualification_required(self):
  text=(source.PACK/'derived/ape-optical.sysml').read_text()
  with self.assertRaises(ValueError):pack.check_optical_translation(text.replace('Original untyped SysML 1.6 ProxyPort','Original untyped port',1))
 def test_source_visibility_drift_rejected(self):
  self.d['slices']['ape-composition']['parts'][0]['visibility']='public'
  with self.assertRaises(ValueError):source.check(self.d)
 def test_visibility_adaptation_must_remain_explicit(self):
  self.d['slices']['ape-optical']['source_visibility']['lg1']='public'
  with self.assertRaises(ValueError):source.check(self.d)
 def check_edited_composition(self,edit):
  work=Path(__file__).resolve().parents[1]/'work';work.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=work) as temp:
   candidate=Path(temp)/'pack';shutil.copytree(source.PACK,candidate)
   path=candidate/'rendered/03-ape-composition.drawio';root=ET.parse(path).getroot()
   edge=next(e for e in root.iter('mxCell') if e.get('source_id')=='_15_0_baa02e2_1204997510902_964101_9752' and e.get('edge')=='1')
   edit(root,edge);path.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
   with self.assertRaises(ValueError):pack.check_pack(pack_dir=candidate)
 def test_actual_editable_composition_targetpoint_drift_rejected(self):
  def edit(root,edge):edge.find("mxGeometry/mxPoint[@as='targetPoint']").attrib.update(x='0',y='0')
  self.check_edited_composition(edit)
 def test_actual_editable_composition_ownerpoint_drift_rejected(self):
  def edit(root,edge):edge.find("mxGeometry/mxPoint[@as='sourcePoint']").attrib.update(x='0',y='0')
  self.check_edited_composition(edit)
 def test_actual_editable_composition_route_drift_rejected(self):
  def edit(root,edge):ET.SubElement(edge.find("mxGeometry/Array[@as='points']"),'mxPoint',{'x':'0','y':'0'})
  self.check_edited_composition(edit)
 def test_duplicate_tagged_editable_edge_rejected(self):
  def edit(root,edge):
   clone=copy.deepcopy(edge);clone.set('id','duplicate');root.find('diagram/mxGraphModel/root').append(clone)
  self.check_edited_composition(edit)
 def test_explicit_empty_or_invalid_projection_does_not_load_defaults(self):
  for value in [{},[],False,'',{'slices':{}}]:
   with self.subTest(value=value):
    with self.assertRaises(ValueError):pack.check_pack(projection=value)
 def test_actual_editable_composition_diamond_loss_rejected(self):
  def edit(root,edge):edge.set('style',edge.get('style').replace('startArrow=diamond','startArrow=none'))
  self.check_edited_composition(edit)
 def test_actual_editable_composition_open_diamond_rejected(self):
  def edit(root,edge):edge.set('style',edge.get('style').replace('startFill=1','startFill=0'))
  self.check_edited_composition(edit)
 def test_actual_editable_composition_wrong_end_glyph_rejected(self):
  def edit(root,edge):edge.set('style',edge.get('style').replace('endArrow=none','endArrow=open'))
  self.check_edited_composition(edit)
 def test_source_boundary_discrepancy(self):
  s=self.d['slices']['tmt-timing'];self.assertEqual(s['source_expression'],'p1<=maxTime');self.assertEqual(s['limit_seconds'],1800)
  self.assertEqual([(v,v<=s['limit_seconds'],v<1800) for v in [1799,1800,1801]],[(1799,True,True),(1800,True,False),(1801,False,False)])
if __name__=='__main__':unittest.main()
