"""Synthetic local-source and distribution-boundary checks; no real raw fixtures."""
import hashlib,json,sys,tempfile,unittest
import xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from check_original_reference_sources import check_local_slices
from engineering_references import validate_fact_content
class SourceBoundaryTests(unittest.TestCase):
 def setUp(self):(R/'work').mkdir(exist_ok=True)
 def test_explicit_local_identity_and_missing_inputs(self):
  with tempfile.TemporaryDirectory(dir=R/'work') as tmp:
   p=Path(tmp)/'synthetic.xml';data=b'<synthetic><node id="fixture" /></synthetic>';p.write_bytes(data)
   expected={'synthetic.xml':hashlib.sha256(data).hexdigest()}
   self.assertEqual(check_local_slices(tmp,expected)['claim_scope'],'optional-local-source-slice-identity')
   p.write_bytes(b'<synthetic><changed /></synthetic>')
   with self.assertRaises(ValueError):check_local_slices(tmp,expected)
   with self.assertRaises(FileNotFoundError):check_local_slices(tmp,{'absent.xml':'0'*64})
 def test_matching_hash_does_not_hide_malformed_xml(self):
  with tempfile.TemporaryDirectory(dir=R/'work') as tmp:
   p=Path(tmp)/'synthetic.xml';data=b'<synthetic>';p.write_bytes(data)
   with self.assertRaises(ET.ParseError):check_local_slices(tmp,{'synthetic.xml':hashlib.sha256(data).hexdigest()})
 def test_raw_record_or_code_cannot_enter_public_fact_contract(self):
  for bad in [{'source_xml':'<ownedRule />'},{'nested':{'records':[]}},{'note':'<packagedElement />'},{'note':'ALH.getCurrentTime()'}]:
   with self.subTest(bad=bad):
    with self.assertRaises(ValueError):validate_fact_content(bad)
 def test_distributed_facts_remain_small_explicit_contracts(self):
  for name in ['engineering-reference/source/view-facts.json','engineering-reference-extension/source/action-facts.json','engineering-reference-extension/source/sequence-facts.json']:
   value=json.loads((R/'examples'/name).read_text());validate_fact_content(value)
   self.assertIn('not independent',value['claim_scope'])
 def test_sequence_candidate_is_local_and_unrendered(self):
  import xml.etree.ElementTree as ET
  from render_sequence_reference import main
  with tempfile.TemporaryDirectory(dir=R/'work') as tmp:
   main(tmp);root=ET.parse(Path(tmp)/'06-tmt-sequence-order.svg').getroot()
   self.assertEqual(len([e for e in root.iter() if e.get('data-sort')=='asynchSignal']),3)
   self.assertNotIn('retained in XML',' '.join(root.itertext()))
   self.assertFalse((Path(tmp)/'06-tmt-sequence-order.png').exists())
 def test_no_raw_xml_or_old_projection_shipped(self):
  for root in [R/'examples/engineering-reference',R/'examples/engineering-reference-extension']:
   self.assertEqual(list(root.rglob('*.xml')),[])
   self.assertEqual(list(root.rglob('projection.json')),[])
   self.assertEqual(list(root.rglob('sequence-projection.json')),[])
if __name__=='__main__':unittest.main()
