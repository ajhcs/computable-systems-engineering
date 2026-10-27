import unittest,copy,json,sys,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import render_diagram_style_prototypes as styles
class StyleReferenceTests(unittest.TestCase):
 def test_all_matched_semantics_and_geometry(self):
  for sid in list(styles.STYLES)+['instrument-record-print']:
   for stem in styles.FILES:
    with self.subTest(treatment=sid,view=stem):
     a=E.parse(styles.P/'rendered'/(stem+'.svg')).getroot();b=E.parse(styles.O/sid/(stem+'.svg')).getroot()
     self.assertEqual(styles.svg_semantics(a),styles.svg_semantics(b))
     self.assertEqual(styles.drawio_semantics(E.parse(styles.P/'rendered'/(stem+'.drawio')).getroot()),styles.drawio_semantics(E.parse(styles.O/sid/(stem+'.drawio')).getroot()))
     self.assertEqual((styles.P/'rendered'/(stem+'.geometry.json')).read_bytes(),(styles.O/sid/(stem+'.geometry.json')).read_bytes())
 def test_new_source_family_controls(self):
  for sid in ['technical-ledger','engineering-standard']:
   for stem in ['05-tmt-exposure']:
    source=R/'examples/engineering-reference-extension/rendered'
    self.assertEqual(styles.svg_semantics(E.parse(source/(stem+'.svg')).getroot()),styles.svg_semantics(E.parse(styles.O/sid/(stem+'.svg')).getroot()))
    self.assertEqual(styles.drawio_semantics(E.parse(source/(stem+'.drawio')).getroot()),styles.drawio_semantics(E.parse(styles.O/sid/(stem+'.drawio')).getroot()))
    self.assertEqual((source/(stem+'.geometry.json')).read_bytes(),(styles.O/sid/(stem+'.geometry.json')).read_bytes())
 def test_transition_arrow_loss_detected(self):
  a=E.parse(styles.P/'rendered/01-tmt-maintenance.svg').getroot();b=copy.deepcopy(a)
  e=next(e for e in b.iter() if 'marker-end' in e.attrib);del e.attrib['marker-end']
  self.assertNotEqual(styles.svg_semantics(a),styles.svg_semantics(b))
 def test_composition_diamond_loss_detected(self):
  a=E.parse(styles.P/'rendered/03-ape-composition.drawio').getroot();b=copy.deepcopy(a)
  e=next(e for e in b.iter() if 'startArrow=diamond' in e.attrib.get('style',''))
  e.set('style',e.attrib['style'].replace('startArrow=diamond','startArrow=none'))
  self.assertNotEqual(styles.drawio_semantics(a),styles.drawio_semantics(b))
 def test_cardinality_change_detected(self):
  a=E.parse(styles.P/'rendered/03-ape-composition.svg').getroot();b=copy.deepcopy(a)
  e=next(e for e in b.iter() if e.text=='pact [183]');e.text='pact [61]'
  self.assertNotEqual(styles.svg_semantics(a),styles.svg_semantics(b))
 def test_composite_boundary_geometry_change_detected(self):
  a=E.parse(styles.P/'rendered/01-tmt-maintenance.svg').getroot();b=copy.deepcopy(a)
  e=next(e for e in b.iter() if e.tag.endswith('rect') and e.attrib.get('x')=='650');e.set('x','687')
  self.assertNotEqual(styles.svg_semantics(a),styles.svg_semantics(b))
 def test_recolor_preserves_wrapping_and_neighbor_properties(self):
  original='shape=stencil(white-token);whiteSpace=wrap;html=0;fontSize=18;strokeWidth=2;dashed=0;customText=white;strokeColor=white;labelBackgroundColor=#ffffff;'
  recolored=styles.recolor_drawio_style(original,{'white':'#FAFAF7','#ffffff':'#FAFAF7'})
  self.assertEqual(recolored,'shape=stencil(white-token);whiteSpace=wrap;html=0;fontSize=18;strokeWidth=2;dashed=0;customText=white;strokeColor=#FAFAF7;labelBackgroundColor=#FAFAF7;')
  self.assertEqual(styles.noncolor_drawio_style(original),styles.noncolor_drawio_style(recolored))
 def test_corrupted_wrapping_style_detected(self):
  a=E.parse(R/'examples/engineering-reference-extension/rendered/05-tmt-exposure.drawio').getroot();b=copy.deepcopy(a)
  cell=next(e for e in b.iter() if 'whiteSpace=wrap' in e.get('style',''));cell.set('style',cell.get('style').replace('whiteSpace=wrap','#FAFAF7Space=wrap'))
  self.assertNotEqual(styles.drawio_semantics(a),styles.drawio_semantics(b))
if __name__=='__main__':unittest.main()
