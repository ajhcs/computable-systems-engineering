"""Agent discovery, revision-bound selections and accessible UI contracts."""
import base64,json,subprocess,sys,tempfile,unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import component_agent as a
import component_ui as ui
from verifier import components as c

class Markup(HTMLParser):
    def __init__(self):super().__init__();self.elements=[]
    def handle_starttag(self,tag,attrs):self.elements.append((tag,dict(attrs)))

class AgentTests(unittest.TestCase):
    def cli(self,*args):
        proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/icons.py'),*args],capture_output=True,text=True)
        self.assertFalse(proc.stderr);return proc,json.loads(proc.stdout)

    def test_ranked_power_search_ignores_unrelated_caveat_prose(self):
        r=a.search('power');self.assertEqual(r['items'][0]['id'],'interface-pwr')
        self.assertNotIn('interface-dat',{r['id'] for r in r['items']});self.assertEqual(r['total'],9)
        self.assertNotIn('mapping',r['items'][0]);self.assertNotIn('sources',r['items'][0])

    def test_bounded_pages_cover_all_ids_once(self):
        ids=[];cursor=None
        while True:
            page=a.search(limit=50,cursor=cursor);self.assertLessEqual(page['returned'],50)
            ids += [r['id'] for r in page['items']];cursor=page['next_cursor']
            if cursor is None:break
        self.assertEqual(len(ids),1076);self.assertEqual(ids,sorted(set(ids)))

    def test_cursor_scope_and_revision_are_checked(self):
        cursor=a.search('pulley',limit=1)['next_cursor']
        with self.assertRaisesRegex(a.RequestError,'same filters'):a.search('spring',cursor=cursor)
        with patch.object(a,'revision',return_value='changed'):
            with self.assertRaisesRegex(a.RequestError,'catalog changed'):a.search('pulley',cursor=cursor)
        for bad in ['not-base64',base64.urlsafe_b64encode(b'[]').decode()]:
            with self.assertRaises(a.RequestError):a.search(cursor=bad)

    def test_page_limits_and_zero_results(self):
        for limit in (0,51,-1,True):
            with self.assertRaises(a.RequestError):a.search(limit=limit)
        r=a.search('not an actual component');self.assertEqual(r['returned'],0);self.assertIsNone(r['next_cursor'])

    def test_exact_and_duplicate_ids(self):
        self.assertEqual(a.resolve(['mech-pulley'])[0]['id'],'mech-pulley')
        for ids in [[],['../index'],['mech-pulley','mech-pulley'],[None],['unavailable-id']]:
            with self.assertRaises(a.RequestError):a.resolve(ids)

    def test_selection_revision_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'selection.json';d=a.selection(['mech-pulley']);p.write_text(json.dumps(d))
            self.assertEqual(a.read_selection(p)[0]['id'],'mech-pulley')
            d['catalog_sha256']='old';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(a.RequestError,'library changed'):a.read_selection(p)
            d=a.selection(['mech-pulley']);d['model_binding']='invented';p.write_text(json.dumps(d))
            with self.assertRaises(a.RequestError):a.read_selection(p)

    def test_cli_machine_errors_and_bounded_default(self):
        proc,r=self.cli('list');self.assertEqual(proc.returncode,0);self.assertEqual(r['returned'],20);self.assertTrue(r['next_cursor'])
        for args,code in [(('show','nonexistent'),'unknown_component_id'),(('list','--limit','0'),'invalid_limit'),(('list','--limit','x'),'invalid_argument')]:
            proc,r=self.cli(*args);self.assertEqual(proc.returncode,2);self.assertEqual(r['error']['code'],code)

    def test_exports_require_selection_and_preserve_existing_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'exported'
            proc,r=self.cli('export','--format','svg','--out',str(p));self.assertEqual(r['error']['code'],'selection_required');self.assertFalse(p.exists())
            proc,r=self.cli('export','--format','svg','--ids','nonexistent','--out',str(p));self.assertEqual(r['error']['code'],'unknown_component_id');self.assertFalse(p.exists())
            proc,r=self.cli('export','--format','svg','--ids','mech-pulley','--out',str(p));self.assertEqual(proc.returncode,0);self.assertFalse(r['model_changes'])
            before=(p/'components/mech-pulley.svg').read_bytes()
            proc,r=self.cli('export','--format','svg','--ids','mech-spring','--out',str(p));self.assertEqual(r['error']['code'],'destination_exists');self.assertEqual((p/'components/mech-pulley.svg').read_bytes(),before)

    def test_broad_query_and_protected_destination_refused(self):
        with tempfile.TemporaryDirectory() as t:
            proc,r=self.cli('export','--format','svg','--query','','--out',t);self.assertEqual(r['error']['code'],'query_too_broad')
        with self.assertRaises(a.RequestError):a.destination(c.LIBRARY/'bad')

    def test_explicit_whole_library_export_remains_available(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'whole-library'
            proc,r=self.cli('export','--format','svg','--all','--out',str(target))
            self.assertEqual(proc.returncode,0);self.assertEqual(r['count'],1076)
            self.assertEqual(len(list(target.rglob('*.svg'))),1076)

    def test_kernspan_partial_selection_is_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'partial'
            proc,r=self.cli('export','--format','kernspan','--ids','mech-pulley','--out',str(target))
            self.assertEqual(r['error']['code'],'requires_full_catalog');self.assertFalse(target.exists())

    def test_ui_stable_accessible_ids_and_no_model_mutations(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'view.html';result=ui.render(['mech-pulley','mech-spring'],p);self.assertFalse(result['model_changes'])
            parser=Markup();parser.feed(p.read_text());els=parser.elements
            ids=[attrs['id'] for _,attrs in els if 'id' in attrs];self.assertEqual(len(ids),len(set(ids)))
            images=[attrs for tag,attrs in els if tag=='img'];self.assertTrue(all(x.get('alt') for x in images));self.assertEqual(len(images),2)
            checks=[attrs for tag,attrs in els if tag=='input'];self.assertTrue(all(x.get('aria-label') and x.get('data-action')=='select-component' for x in checks))
            self.assertEqual({x['value'] for x in checks},{'mech-pulley','mech-spring'})
            self.assertEqual(len([x for tag,x in els if tag=='button']),2)
            self.assertFalse(any(tag=='iframe' for tag,_ in els))
            self.assertIn('data-selected-ids',p.read_text())

    def test_inline_limit_and_duplicate_ids_write_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'view.html'
            for ids in [['mech-pulley']*9,['mech-pulley']*2]:
                with self.assertRaises(a.RequestError):ui.render(ids,p)
                self.assertFalse(p.exists())

    def test_context_mapping_and_corpus_bytes_unchanged(self):
        self.assertEqual(c.validate()['components'],1076)
        self.assertEqual(c.component('interface-fnc')['mapping']['sysml_v2'],['Dependency'])
        self.assertEqual(a.contract()['ui_transport'].split(';')[0],'Portable local HTML')

if __name__=='__main__':unittest.main()
