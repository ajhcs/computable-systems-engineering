import base64,json,sys,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier import components as c

class ComponentsTest(unittest.TestCase):
    def test_complete_coverage_and_original_hashes(self):
        rows=c.inventory();self.assertEqual(len(rows),1076)
        self.assertEqual(c.validate()['status'],'pass')
        byid={r['id']:r for r in rows}
        preserved=json.loads((c.LIBRARY/'sources/preservation.json').read_text())
        self.assertEqual(len(preserved['primary_icons']),341)
        for old in preserved['primary_icons']:
            now=byid[old['id']];self.assertEqual(now['sha256'],old['sha256']);self.assertEqual(now['approval_state'],old['approval_state'])
        self.assertEqual(sum(x['approval_state']=='approved' for x in byid.values()),10)

    def test_semantic_context_preserves_distinctions(self):
        self.assertIn('PartUsage',c.component('mech-pulley')['mapping']['sysml_v2'])
        self.assertIn('PortUsage',c.component('interface-pwr')['mapping']['sysml_v2'])
        for r in c.select(family='status')+c.select(family='navigation'):
            self.assertEqual(r['mapping']['sysml_v2'],[])
        for r in c.inventory():
            self.assertFalse(r['mapping']['formal_sysml_glyph'])
            self.assertTrue(r['mapping']['rationale'])
        self.assertIsNone(c.component('../index.json'))

    def test_drawio_preserves_vector_bytes_and_unbound_metadata(self):
        row=c.component('mech-spring-variant-a')
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'library.xml';c.drawio([row],path)
            entries=json.loads(ET.parse(path).getroot().text);self.assertEqual(len(entries),1)
            model=ET.fromstring(entries[0]['xml']);obj=model.find('./root/object')
            self.assertEqual(obj.get('cseId'),row['id']);self.assertEqual(obj.get('cseModelBinding'),'unbound')
            style=obj.find('mxCell').get('style');image=style.split('image=data:image/svg+xml,')[1].split(';')[0]
            self.assertEqual(base64.b64decode(image),(c.LIBRARY/row['file']).read_bytes())

    def test_extracted_document_uses_its_actual_coordinate_bounds(self):
        row=c.component('palette-refined-documents-documents-page1-title-block')
        root=ET.parse(c.LIBRARY/row['file']).getroot();x,y,w,h=map(float,root.get('viewBox').split())
        rect=next(e for e in root.iter(c.SVG+'rect') if e.get('x')=='930')
        self.assertLessEqual(x,float(rect.get('x')));self.assertLessEqual(y,float(rect.get('y')))
        self.assertGreaterEqual(x+w,float(rect.get('x'))+float(rect.get('width')))
        self.assertGreaterEqual(y+h,float(rect.get('y'))+float(rect.get('height')))
        artwork=c.component('palette-src-foundation-foundation-arrowheads-hollow-triangle-artwork')
        symbol=ET.parse(c.LIBRARY/artwork['file']).getroot()
        self.assertFalse(any(e.tag==c.SVG+'rect' and e.get('width')=='300' for e in symbol.iter()))
        self.assertTrue(any(e.tag==c.SVG+'path' for e in symbol.iter()))

    def test_corruption_fails_validation(self):
        row=dict(c.component('mech-pulley'))
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'index.json').write_text(json.dumps({'schema':'cse.component-library/1','count':1,'components':[row]}))
            target=p/row['file'];target.parent.mkdir();target.write_text('<svg/>')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):c.validate(p)
            row['file']='../escape.svg';(p/'index.json').write_text(json.dumps({'schema':'cse.component-library/1','count':1,'components':[row]}))
            with self.assertRaisesRegex(ValueError,'Invalid component path'):c.validate(p)

    def test_svg_export_is_individually_editable(self):
        rows=c.select(query='mech-pulley-variant')
        self.assertEqual(len(rows),3)
        with tempfile.TemporaryDirectory() as t:
            c.export('svg',t,rows)
            self.assertEqual(len(list(Path(t).rglob('*.svg'))),3)
            self.assertTrue((Path(t)/'components.json').exists())
            for row in json.loads((Path(t)/'components.json').read_text())['components']:
                self.assertTrue((Path(t)/row['file']).exists())

    def test_kernspan_exports_full_searchable_atlas(self):
        rows=c.inventory()
        with tempfile.TemporaryDirectory() as t:
            c.export('kernspan',t)
            self.assertTrue((Path(t)/'cse_components.rs').exists())
            self.assertTrue((Path(t)/'atlas.png').exists())
            self.assertEqual(json.loads((Path(t)/'components.json').read_text())['count'],len(rows))
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'whole library'):c.export('kernspan',t,[rows[0]])

if __name__=='__main__':unittest.main()
