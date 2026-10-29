"""Current-system artifact fidelity with real native configuration mutations."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verifier.configuration import inspect_configuration
from verifier.configuration_view import render_artifacts,write_view,check_view,FILES
from verifier.sysml import JAR,CLASSES

def setUpModule():
    (ROOT/'.tmp').mkdir(exist_ok=True)



def report():
    return {'status':'pass','model_sha256':'a'*64,'scope_sha256':'b'*64,'model_files':[{'path':'synthetic.sysml','sha256':'a'*64}],
            'checker_sha256':'c'*64,'native':{'status':'pass','parser':'Synthetic unit control'},'findings':[],
            'limits':['Declaration and adjacency only.'],
            'system_view':{'version':'configuration-system-view-1.0','status':'pass','scope':'selected_configuration_obligations',
            'nodes':{'$root':{'native_name':'Context::current','type':'Library::System','parent':None,'kind':'root'},
                     'Sensor':{'native_name':'Library::System::sensor','type':'Library::Sensor','parent':'$root','kind':'selected_role'},
                     'Enterprise':{'native_name':'Context::enterprise','type':'Library::Receiver','parent':None,'kind':'external_role'}},
            'edges':{'Link':{'native_name':'Context::dataLink','owner':'Context','from':{'role':'Sensor','port':'Library::Sensor::output','path':['Context::current','Library::System::sensor','Library::Sensor::output']},'to':{'role':'Enterprise','port':'Library::Receiver::input','path':['Context::enterprise','Library::Receiver::input']},'kind':'native_connection','directed':False}},
            'omissions':[],'open_alternatives':['Library::HistoricalSystem']}}


class ArtifactTests(unittest.TestCase):
    def test_native_diagnostics_are_visible_escaped_and_preserve_status(self):
        r=report();r['native']['parser_issues']=[{'severity':'WARNING','source':'<source>','line':7,'message':'<warning>'}]
        a=render_artifacts(r)
        self.assertIn('Native diagnostics: 1 (1 warning)',a['system.svg'])
        self.assertIn('&lt;warning&gt;',a['index.html']);self.assertIn('&lt;source&gt;:7',a['index.html'])
        self.assertEqual(json.loads(a['view.json'])['status'],'pass')
        self.assertIn('Native diagnostics: 0 (0 warnings)',render_artifacts(report())['system.svg'])

    def test_deterministic_editable_svg_and_bound_ledger(self):
        r=report();a=render_artifacts(r);self.assertEqual(a,render_artifacts(deepcopy(r)))
        svg=ET.fromstring(a['system.svg']);self.assertEqual(svg.tag,'{http://www.w3.org/2000/svg}svg')
        self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}script'))
        ledger=json.loads(a['view.json']);self.assertEqual(ledger['system_view'],r['system_view'])
        self.assertEqual(ledger['edge_aliases'],{'C1':'Link'})
        self.assertIn('undirected',a['index.html']);self.assertIn('Library::HistoricalSystem',a['index.html'])

    def test_source_labels_are_escaped_and_anonymous_connections_are_named_honestly(self):
        r=report();r['system_view']['nodes']['Sensor']['native_name']='<script>alert("x")</script>'
        r['findings']=[{'id':'<bad>','status':'unknown','detail':'<script>bad()</script>'}]
        r['system_view']['edges']['Link']['native_name']=None
        a=render_artifacts(r);ET.fromstring(a['system.svg'])
        self.assertNotIn('<script>',a['system.svg']);self.assertNotIn('<script>',a['index.html'])
        self.assertIn('anonymous connection owned by Context',a['index.html'])

    def test_long_port_alias_is_bounded_without_losing_native_identity(self):
        r=report();port='Library::Sensor::'+'W'*400
        r['system_view']['edges']['Link']['from'].update(port=port,path=['Context::current','Library::System::sensor',port])
        a=render_artifacts(r);svg=ET.fromstring(a['system.svg'])
        labels=[e for e in svg.iter() if e.get('data-native-port')==port]
        self.assertEqual(len(labels),1);self.assertEqual(labels[0].text,'W'*25+'…')
        self.assertIn(port,a['index.html']);self.assertEqual(json.loads(a['view.json'])['system_view']['edges']['Link']['from']['port'],port)

    def test_all_artifact_tampering_is_detected_without_trusting_saved_metadata(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            out=Path(d)/'view';write_view(report(),out)
            self.assertEqual(check_view(report(),out)['status'],'pass')
            for name in FILES:
                with self.subTest(name=name):
                    original=(out/name).read_bytes();(out/name).write_bytes(original+b'\nchanged')
                    checked=check_view(report(),out);self.assertEqual(checked['status'],'fail')
                    self.assertIn(name,checked['findings'][0]['files']);(out/name).write_bytes(original)

    def test_overwrite_extra_files_and_symlink_artifacts_are_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            out=Path(d)/'view';write_view(report(),out)
            with self.assertRaises(FileExistsError):write_view(report(),out)
            (out/'extra').write_text('Unexpected');self.assertEqual(check_view(report(),out)['status'],'error');(out/'extra').unlink()
            saved=Path(d)/'saved.svg';(out/'system.svg').rename(saved);(out/'system.svg').symlink_to(saved)
            self.assertEqual(check_view(report(),out)['status'],'error')

    def test_partial_view_remains_unsuccessful_even_when_artifact_fidelity_passes(self):
        r=report();r['status']=r['system_view']['status']='fail';r['system_view']['edges']={}
        r['system_view']['omissions']=[{'id':'Link','status':'fail','reason':'Missing retained native connection'}]
        r['findings']=[{'id':'Link','status':'fail','detail':'Missing retained native connection'}]
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            out=Path(d)/'view';self.assertEqual(write_view(r,out)['status'],'fail')
            checked=check_view(r,out);self.assertEqual(checked['view_status'],'pass');self.assertEqual(checked['status'],'fail')
            self.assertIn('Missing retained native connection',(out/'index.html').read_text())

    def test_missing_graph_or_orphan_edge_cannot_be_presented_as_supported(self):
        with self.assertRaises(ValueError):render_artifacts({'status':'pass'})
        r=report();r['system_view']['edges']['Link']['to']['role']='Historical'
        with self.assertRaises(ValueError):render_artifacts(r)
        r=report();r['system_view']['edges']['Link']['directed']=True
        with self.assertRaises(ValueError):render_artifacts(r)


@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(),'Pinned native parser required')
class NativeArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.models=[]
        fixture=ROOT/'examples/configuration-review/connected'
        for name in ('library.sysml','current.sysml'):
            p=self.base/name;p.write_bytes((fixture/name).read_bytes());self.models.append(p)
        self.scope=self.base/'scope.json';self.scope.write_bytes((fixture/'scope.json').read_bytes())
        self.digest=sha256(self.scope.read_bytes()).hexdigest()

    def inspect(self):
        return inspect_configuration(self.models,self.scope,self.digest)

    def test_published_connected_view_matches_fresh_native_reconciliation(self):
        fixture=ROOT/'examples/configuration-review/connected'
        scope=fixture/'scope.json'
        fresh=inspect_configuration([fixture/'library.sysml',fixture/'current.sysml'],
                                    scope,sha256(scope.read_bytes()).hexdigest())
        self.assertEqual(fresh['status'],'pass',fresh)
        checked=check_view(fresh,fixture/'generated')
        self.assertEqual(checked['status'],'pass',checked)
        # The public README illustration must keep the same selected identities
        # and endpoint semantics as the newly parsed model, and its PNG must
        # remain bound to that exact editable source.
        assets=ROOT/'assets/readme'
        receipt=json.loads((assets/'render-receipt.json').read_text())
        self.assertEqual(receipt['native_view_ledger_sha256'],sha256((fixture/'generated/view.json').read_bytes()).hexdigest())
        source=assets/'connected-overview.svg'
        elements={e.get('data-native'):e for e in ET.parse(source).iter() if e.get('data-native')}
        graph=fresh['system_view']
        self.assertEqual(set(elements),{n['native_name'] for n in graph['nodes'].values()}|{e['native_name'] for e in graph['edges'].values()})
        edge=next(iter(graph['edges'].values()));drawn=elements[edge['native_name']]
        self.assertEqual(drawn.get('data-directed'),'false')
        self.assertEqual(drawn.get('data-from-port'),edge['from']['port'])
        self.assertEqual(drawn.get('data-to-port'),edge['to']['port'])
        self.assertFalse(any('marker-end' in element.attrib for element in drawn.iter()))
        render=next(item for item in receipt['assets'] if item['png']=='assets/readme/connected-context.png')
        self.assertEqual(render['source_sha256'],sha256(source.read_bytes()).hexdigest())
        self.assertEqual(render['png_sha256'],sha256((assets/'connected-context.png').read_bytes()).hexdigest())

    def test_native_warning_outside_selected_context_is_presented(self):
        p=self.models[1]
        p.write_text(p.read_text().replace('part historical : System;', 'part historical : System { part sensor : Sensor [0] redefines System::sensor; }'))
        r=self.inspect();self.assertEqual(r['status'],'pass',r)
        warnings=[i for i in r['native']['parser_issues'] if i.get('severity')=='WARNING']
        self.assertTrue(warnings,r)
        a=render_artifacts(r)
        for issue in warnings:self.assertIn(issue['message'],a['index.html'])
        self.assertIn('Native parser diagnostics',a['index.html'])
        self.assertIn('Native diagnostics: 1 (1 warning)',a['system.svg'])

    def test_real_native_graph_roundtrip_then_source_and_scope_staleness(self):
        r=self.inspect();self.assertEqual(r['status'],'pass',r)
        self.assertTrue(r['system_view']['edges']);out=self.base/'view';write_view(r,out)
        self.assertEqual(check_view(self.inspect(),out)['status'],'pass')
        self.models[0].write_text(self.models[0].read_text()+'\n// Updated source revision\n')
        self.assertEqual(check_view(self.inspect(),out)['status'],'fail')
        # Scope revision drift invalidates checking before any old artifact can
        # be treated as evidence for the new retained obligation set.
        self.scope.write_text(self.scope.read_text()+'\n')
        stale=self.inspect();self.assertEqual(stale['status'],'error')
        self.assertNotEqual(check_view(stale,out)['status'],'pass')

    def test_removed_added_and_retargeted_native_connections_cannot_keep_saved_view_valid(self):
        r=self.inspect();self.assertEqual(r['status'],'pass',r);out=self.base/'view';write_view(r,out)
        original=self.models[1].read_text()
        line='connection dataLink connect current.sensor.output to enterprise.input;'
        self.assertIn(line,original)
        for text in (original.replace(line,''),original.replace('to enterprise.input','to secondReceiver.input'),
                     original.replace(line,line+'\nconnection extraLink connect current.sensor.output to secondReceiver.input;')):
            with self.subTest(text=text):
                self.models[1].write_text(text);fresh=self.inspect()
                self.assertNotEqual(check_view(fresh,out)['status'],'pass')
                if 'extraLink' in text:
                    self.assertEqual(fresh['status'],'pass',fresh)
                    self.assertTrue(any('extraLink' in str(x) for x in fresh['system_view']['omissions']))

    def test_cli_views_from_foreign_directory_and_returns_nonzero_on_tampering(self):
        args=[sys.executable,'-B',str(ROOT/'scripts/configuration.py')]
        common=[*map(str,self.models),'--scope',str(self.scope),'--scope-sha256',self.digest,'--json']
        out=self.base/'view'
        created=subprocess.run([*args,'view',*common,'--output',str(out)],cwd=self.base,capture_output=True,text=True)
        self.assertEqual(created.returncode,0,created.stdout+created.stderr)
        checked=subprocess.run([*args,'check-view',*common,'--view',str(out)],cwd=self.base,capture_output=True,text=True)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
        (out/'index.html').write_text((out/'index.html').read_text().replace('Current system','Fabricated system'))
        bad=subprocess.run([*args,'check-view',*common,'--view',str(out)],cwd=self.base,capture_output=True,text=True)
        self.assertNotEqual(bad.returncode,0);self.assertEqual(json.loads(bad.stdout)['status'],'fail')


if __name__=='__main__':unittest.main()
