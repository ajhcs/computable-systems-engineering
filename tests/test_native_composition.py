#!/usr/bin/env python3
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from check_native_composition import validate_facts,invariant_svg,main
from render_native_composition import styled_svg,recolor_style
from parsed_v2_renderer_contracts import preflight
BASE=ROOT/"examples/native-v2-composition"
class NativeProofTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.facts=json.loads((BASE/"native.facts.json").read_text())
  cls.source=json.loads((ROOT/"examples/engineering-reference/source/projection.json").read_text())["slices"]["ape-composition"]
  cls.puml=(BASE/"native.puml").read_text();cls.svg=(BASE/"native.svg").read_text()
 def test_matched_native_and_five_treatments(self):self.assertEqual(main()["styled_semantic_primitive_equality"],5)
 def reject_mutation(self,change):
  f=copy.deepcopy(self.facts);change(f)
  with self.assertRaises(ValueError):validate_facts(f,self.source,self.puml,self.svg)
 def test_wrong_owner_rejected(self):self.reject_mutation(lambda f:f["parts"][1].update(owner=f["parts"][0]["qualified"]))
 def test_wrong_count_rejected(self):self.reject_mutation(lambda f:f["parts"][0].update(lower=60))
 def test_identity_substitution_rejected(self):self.reject_mutation(lambda f:f["parts"][0].update(id=f["parts"][1]["id"]))
 def test_non_composite_rejected(self):self.reject_mutation(lambda f:f["parts"][0].update(composite=False))
 def test_visibility_change_rejected(self):self.reject_mutation(lambda f:f["parts"][0].update(visibility="public"))
 def test_implicit_bound_relabel_rejected(self):self.reject_mutation(lambda f:f["parts"][2].update(multiplicity_origin="explicit"))
 def test_native_endpoint_change_rejected(self):
  with self.assertRaises(ValueError):validate_facts(self.facts,self.source,self.puml.replace("E1 *-- E3","E2 *-- E3"),self.svg)
 def test_svg_identity_missing_rejected(self):
  with self.assertRaises(ValueError):validate_facts(self.facts,self.source,self.puml,self.svg.replace("psysml:"+self.facts["parts"][0]["id"],"psysml:wrong"))
 def test_text_geometry_and_href_changes_detected(self):
  for altered in [self.svg.replace("ActiveSegmentedMirror</text>","Wrong</text>"),
                  self.svg.replace('viewBox="0 0 1141 345"','viewBox="0 0 1142 345"'),
                  self.svg.replace("psysml:"+self.facts["selected"]["id"],"psysml:wrong"),
                  self.svg.replace("stroke-width:0.5","stroke-width:9")]:
   self.assertNotEqual(invariant_svg(altered),invariant_svg(self.svg))
 def test_only_parsed_color_properties_recolored(self):
  p={"canvas":"#EEEEEE","line":"#111111","ink":"#222222"}
  self.assertEqual(recolor_style("white-space:pre;stroke:#181818;stroke-width:0.5;custom:#FFFFFF",p),
                   "white-space:pre;stroke:#111111;stroke-width:0.5;custom:#FFFFFF")
 def test_unknown_native_family_rejected(self):
  with self.assertRaises(ValueError):preflight("TREE",{})
 def test_legacy_family_views_rejected(self):
  for family in ["ACTION","STATE","INTERCONNECTION","SEQUENCE"]:
   with self.assertRaisesRegex(ValueError,"linked parsed-v2"):preflight(family,{"origin":"source-v1-redraw"})
 def test_current_partial_native_inventory_cannot_pass(self):
  for family in ["ACTION","STATE","INTERCONNECTION","SEQUENCE"]:
   with self.assertRaises(ValueError):preflight(family,{"origin":"linked-native-v2","parsed_model_sha256":"a"*64,"tool_sha256":"b"*64})
 def test_incomplete_audit_fields_rejected(self):
  from parsed_v2_renderer_contracts import REQUIRED
  r={"origin":"linked-native-v2","parsed_model_sha256":"a"*64,"tool_sha256":"b"*64,
     "id":"test-id","kind":"test-kind","owner":"test-owner","unsupported":[],"unresolved":[]}
  for field in REQUIRED["ACTION"]:r[field]={"status":"resolved","value":["test-only fact"],"evidence":["test-only identity"]}
  for field in REQUIRED["ACTION"]:
   bad=copy.deepcopy(r);bad[field]={"status":"unknown","value":[],"evidence":[]}
   with self.assertRaises(ValueError):preflight("ACTION",bad)
 def test_empty_topology_rejected(self):
  from parsed_v2_renderer_contracts import REQUIRED
  r={"origin":"linked-native-v2","parsed_model_sha256":"a"*64,"tool_sha256":"b"*64,
     "id":"test-id","kind":"test-kind","owner":"test-owner","unsupported":[],"unresolved":[]}
  for field in REQUIRED["ACTION"]:r[field]={"status":"resolved","value":[],"evidence":["test-only identity"]}
  with self.assertRaisesRegex(ValueError,"Empty required topology"):preflight("ACTION",r)
 def test_unresolved_endpoint_rejected(self):
  with self.assertRaises(ValueError):preflight("INTERCONNECTION",{"origin":"linked-native-v2","parsed_model_sha256":"a"*64,"tool_sha256":"b"*64,"id":"test","kind":"test","owner":"test","unsupported":[],"unresolved":["omb.lg1.in_oif"]})
 def test_svg_path_or_diamond_mutation_rejected(self):
  import xml.etree.ElementTree as E
  for tag,attribute,value in [("path","d","M0,0 C0,0 0,0 0,0"),("polygon","points","0,0,1,1,2,2,3,3,0,0")]:
   root=E.fromstring(self.svg);next(e for e in root.iter() if e.tag.endswith("}"+tag)).set(attribute,value)
   with self.assertRaises(ValueError):validate_facts(self.facts,self.source,self.puml,E.tostring(root,encoding="unicode"))
 def test_open_diamond_drift_detected(self):
  self.assertNotEqual(invariant_svg(self.svg),invariant_svg(self.svg.replace('fill="#181818"','fill="none"')))
 def test_hidden_or_translucent_glyph_drift_detected(self):
  for altered in [self.svg.replace('stroke-width:1.0;','stroke-width:1.0;opacity:0;'),self.svg.replace('stroke-width:1.0;','stroke-width:1.0;display:none;')]:
   self.assertNotEqual(invariant_svg(self.svg),invariant_svg(altered))
if __name__=="__main__":unittest.main()
