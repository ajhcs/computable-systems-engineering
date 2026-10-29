"""Linked native connection endpoints, never reconstructed from source strings."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import check_sysml, JAR, CLASSES
from verifier.configuration import reconcile

def setUpModule():
    (ROOT/'.tmp').mkdir(exist_ok=True)


BASE = ROOT/'examples/configuration-review/connected'
CURRENT = BASE/'current.sysml'
LIBRARY = BASE/'library.sysml'
SOURCE = ['LinkContext::current', 'LinkLibrary::System::sensor', 'LinkLibrary::Sensor::output']
TARGET = ['LinkContext::enterprise', 'LinkLibrary::Receiver::input']


@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(), 'Install pinned parser')
class NativeConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = check_sysml([LIBRARY, CURRENT], syntax_only=True)

    def modified(self, current=None, library=None):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temp:
            temp=Path(temp); c=temp/'current.sysml'; l=temp/'library.sysml'
            c.write_text(CURRENT.read_text() if current is None else current)
            l.write_text(LIBRARY.read_text() if library is None else library)
            return check_sysml([l,c],syntax_only=True)

    def connection(self, report):
        self.assertEqual(report['status'],'pass',report)
        self.assertEqual(report['parser_issues'],[])
        self.assertEqual(len(report['inventory']['connections']),1)
        return report['inventory']['connections'][0]

    def test_named_binary_link_has_exact_context_and_declared_feature_paths(self):
        link=self.connection(self.native)
        self.assertTrue(link['supported'],link)
        self.assertEqual(link['qualified_name'],'LinkContext::dataLink')
        self.assertEqual(link['owner'],'LinkContext')
        self.assertEqual([end['path'] for end in link['ends']],[SOURCE,TARGET])
        self.assertEqual(link['source'],str(CURRENT.relative_to(ROOT)))
        self.assertEqual(link['line'],7)
        self.assertFalse(any(p.get('qualified_name')=='LinkContext::dataLink' for p in self.native['inventory']['parts']))

    def test_port_inventory_retains_owner_type_and_original_source(self):
        port=next(p for p in self.native['inventory']['ports'] if p['qualified_name']=='LinkLibrary::Sensor::output')
        self.assertEqual(port['owner'],'LinkLibrary::Sensor')
        self.assertEqual(port['type'],'LinkLibrary::Data')
        self.assertEqual(port['source'],str(LIBRARY.relative_to(ROOT)))
        self.assertEqual(port['line'],4)
        self.assertEqual(port['multiplicity'],{'status':'default','lower':1,'upper':1})
        self.assertFalse(port['is_variant'])

    def test_anonymous_link_and_reversed_end_order_preserve_undirected_identity(self):
        text=CURRENT.read_text().replace('connection dataLink connect current.sensor.output to enterprise.input;',
                                       'connect enterprise.input to current.sensor.output;')
        link=self.connection(self.modified(current=text))
        self.assertTrue(link['supported'],link)
        self.assertIsNone(link.get('qualified_name'))
        self.assertEqual([end['path'] for end in link['ends']],[TARGET,SOURCE])

    def test_historical_or_unselected_peer_retargeting_is_visible_in_linked_paths(self):
        for old,new,expected in [('current.sensor.output','historical.sensor.output','LinkContext::historical'),
                                 ('enterprise.input','secondReceiver.input','LinkContext::secondReceiver')]:
            with self.subTest(target=new):
                link=self.connection(self.modified(current=CURRENT.read_text().replace(old,new)))
                self.assertIn(expected,[end['path'][0] for end in link['ends']])

    def test_missing_link_is_not_fabricated_and_missing_port_retains_parser_error(self):
        absent=self.modified(current=CURRENT.read_text().replace('    connection dataLink connect current.sensor.output to enterprise.input;\n',''))
        self.assertEqual(absent['status'],'pass',absent)
        self.assertEqual(absent['inventory']['connections'],[])
        invalid=self.modified(library=LIBRARY.read_text().replace('        port output : Data;',''))
        self.assertEqual(invalid['status'],'error',invalid)
        self.assertTrue(invalid['parser_issues'])

    def test_inherited_port_keeps_its_declared_owner(self):
        link=self.connection(self.modified(library=LIBRARY.read_text().replace('part sensor : Sensor;','part sensor : InheritedSensor;')))
        self.assertEqual(link['ends'][0]['path'],SOURCE)

    def test_usage_owned_connection_retains_relative_path_and_native_owner(self):
        text=CURRENT.read_text().replace('part current : System;',
             'part current : System { connection localLink connect sensor.output to enterprise.input; }')
        text=text.replace('    connection dataLink connect current.sensor.output to enterprise.input;\n','')
        link=self.connection(self.modified(current=text))
        self.assertEqual(link['owner'],'LinkContext::current')
        self.assertEqual(link['owner_kind'],'PartUsage')
        self.assertEqual(link['ends'][0]['path'],SOURCE[1:])
        self.assertEqual(link['ends'][1]['path'],TARGET)

    def test_conjugated_port_links_original_type_and_preserves_variation_guard(self):
        scope=json.loads((BASE/'scope.json').read_text())
        for variable in (False,True):
            with self.subTest(variable=variable):
                library=LIBRARY.read_text().replace('port output : Data;', 'port output : ~Data;')
                library=library.replace('port def Data;', 'port def Data;\n    port def OtherData;')
                library=library.replace('port input : Data;', 'port input : OtherData;')
                if variable:
                    library=library.replace('port def Data;', 'variation port def Data;')
                report=self.modified(library=library)
                self.connection(report)
                inventory=report['inventory']
                port=next(p for p in inventory['ports'] if p['qualified_name']=='LinkLibrary::Sensor::output')
                definitions={d['qualified_name']:d for d in inventory['port_definitions']}
                conjugate=definitions[port['type']]
                self.assertTrue(conjugate['is_conjugated'])
                self.assertEqual(conjugate['original_port_definition'],'LinkLibrary::Data')
                original=definitions[conjugate['original_port_definition']]
                self.assertFalse(original['is_conjugated'])
                self.assertEqual(original['is_variation'],variable)
                result=reconcile(scope,inventory)
                self.assertEqual(result['status'],'unsupported' if variable else 'pass',result)
                if variable:
                    self.assertTrue(any(f['rule']=='port_type' and f['status']=='unsupported'
                                        for f in result['findings']),result)

    def test_binding_is_retained_as_unsupported_and_not_part_equipment(self):
        text=CURRENT.read_text().replace('connection dataLink connect current.sensor.output to enterprise.input;',
                                       'bind current.sensor.output = enterprise.input;')
        link=self.connection(self.modified(current=text))
        self.assertEqual(link['kind'],'BindingConnectorAsUsage')
        self.assertFalse(link['supported'])
        self.assertEqual([end['path'] for end in link['ends']],[SOURCE,TARGET])


if __name__=='__main__':
    unittest.main()
