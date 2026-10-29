"""Retained selection, selected-context membership, drift and unsupported proof tests."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.configuration import inspect_configuration, reconcile, render_text, schema
from verifier.sysml import CLASSES, JAR, check_sysml

def setUpModule():
    (ROOT/'.tmp').mkdir(exist_ok=True)


BASE = ROOT/'examples/configuration-review'
SCOPE = json.loads((BASE/'scope.json').read_text())
MODELS = [BASE/'library.sysml', BASE/'current.sysml']


def inventory():
    facts = {'part_definitions': [
        {'qualified_name': 'ConfigurationLibrary::'+name, 'supertypes': ['ConfigurationLibrary::BaseSystem'] if name == 'SelectedSystem' else []}
        for name in ('Sensor', 'Accessory', 'HistoricalSensor', 'AlternativeSystem', 'BaseSystem', 'SelectedSystem')],
        'parts': [
            {'qualified_name':'ConfigurationContext::current', 'type':'ConfigurationLibrary::SelectedSystem', 'nested':False, 'owner_kind':'Package'},
            {'qualified_name':'ConfigurationLibrary::BaseSystem::sensor', 'owner':'ConfigurationLibrary::BaseSystem', 'type':'ConfigurationLibrary::Sensor'},
            {'qualified_name':'ConfigurationLibrary::SelectedSystem::accessory', 'owner':'ConfigurationLibrary::SelectedSystem', 'type':'ConfigurationLibrary::Accessory'}]}
    for row in facts['parts']:row['multiplicity']={'status':'default','lower':1,'upper':1}
    return facts


class SelectionTests(unittest.TestCase):
    def test_selected_context_and_inherited_role(self):
        result = reconcile(SCOPE, inventory())
        self.assertEqual(result['status'], 'pass', result)
        self.assertIn('Current context: ConfigurationContext::current', render_text(result))

    def test_existing_role_from_unselected_context_is_rejected(self):
        facts = inventory(); facts['parts'][2]['owner'] = 'ConfigurationLibrary::AlternativeSystem'
        self.assertEqual(reconcile(SCOPE, facts)['status'], 'fail')

    def test_wrong_root_type_cannot_be_satisfied_by_library(self):
        facts = inventory(); facts['parts'][0]['type'] = 'ConfigurationLibrary::AlternativeSystem'
        self.assertEqual(reconcile(SCOPE, facts)['status'], 'fail')

    def test_missing_accessory_and_wrong_selection(self):
        for mutate in (lambda f:f['parts'].pop(), lambda f:f['parts'][2].update(type='ConfigurationLibrary::HistoricalSensor')):
            facts=inventory(); mutate(facts); self.assertEqual(reconcile(SCOPE, facts)['status'], 'fail')

    def test_duplicate_exact_identity_is_not_first_match(self):
        facts=inventory(); facts['parts'].append(dict(facts['parts'][2]))
        self.assertEqual(reconcile(SCOPE, facts)['status'], 'fail')

    def test_redefined_inherited_placeholder_cannot_satisfy_selection(self):
        facts=inventory(); facts['parts'].append({'qualified_name':'ConfigurationLibrary::SelectedSystem::sensor', 'owner':'ConfigurationLibrary::SelectedSystem', 'type':'ConfigurationLibrary::HistoricalSensor', 'redefines':['ConfigurationLibrary::BaseSystem::sensor']})
        result=reconcile(SCOPE,facts)
        self.assertIn('role_redefined', {f['rule'] for f in result['findings']})

    def test_open_alternatives_do_not_select_historical_equipment(self):
        result=reconcile(SCOPE,inventory()); self.assertEqual(result['status'],'pass')
        self.assertNotIn('ConfigurationLibrary::HistoricalSensor', [r['type'] for r in result['view']['selected_roles'].values()])

    def test_explicitly_open_exact_type_cannot_also_be_selected(self):
        scope=deepcopy(SCOPE);scope['open_alternatives'].append('ConfigurationLibrary::Sensor')
        self.assertEqual(reconcile(scope,inventory())['status'],'fail')

    def test_connections_and_unknown_inheritance_cannot_pass(self):
        scope=deepcopy(SCOPE);scope['connections']=[{'from':'ConfigurationContext::current::a','to':'ConfigurationContext::current::b'}]
        self.assertEqual(reconcile(scope,inventory())['status'],'unsupported')
        facts=inventory(); facts['part_definitions'][5].pop('supertypes')
        self.assertEqual(reconcile(SCOPE,facts)['status'],'unsupported')

    def test_suppressed_optional_and_unknown_multiplicity_cannot_pass(self):
        for bound, status in [({'status':'literal','lower':0,'upper':0},'fail'), ({'status':'literal','lower':0,'upper':1},'unknown'), ({'status':'inherited'},'unsupported')]:
            facts=inventory();facts['parts'][2]['multiplicity']=bound
            self.assertEqual(reconcile(SCOPE,facts)['status'],status)

    def test_use_case_subject_cannot_be_current_root(self):
        facts=inventory();facts['parts'][0]['owner_kind']='UseCaseDefinition'
        self.assertEqual(reconcile(SCOPE,facts)['status'],'fail')

    def test_parent_cycle_and_duplicate_selected_identity_refused(self):
        scope=deepcopy(SCOPE);scope['selected_roles']['Sensor']['parent']='Accessory';scope['selected_roles']['Accessory']['parent']='Sensor'
        with self.assertRaises(ValueError):schema(scope)
        scope=deepcopy(SCOPE);scope['selected_roles']['Duplicate']=dict(scope['selected_roles']['Sensor'])
        with self.assertRaises(ValueError):schema(scope)


@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(), 'Pinned SysML parser required')
class NativeSelectionTests(unittest.TestCase):
    def test_unresolved_native_variant_cannot_count_as_selected_presence(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);model=directory/'variant.sysml';scope_path=directory/'scope.json'
            model.write_text('package VariantContext { part def Sensor; part def Accessory; variation part def Choice { variant part alpha : Sensor; variant part beta : Accessory; } part current : Choice; }')
            scope={'version':'configuration-1.0','root':{'native_name':'VariantContext::current','type':'VariantContext::Choice'},'selected_roles':{'Sensor':{'parent':'$root','native_name':'VariantContext::Choice::alpha','type':'VariantContext::Sensor'}},'open_alternatives':[],'connections':[]}
            scope_path.write_text(json.dumps(scope))
            native=check_sysml(model,syntax_only=True)
            self.assertEqual(native['status'],'pass',native)
            self.assertEqual(native.get('parser_issues'),[])
            self.assertTrue(next(r for r in native['inventory']['part_definitions'] if r['qualified_name']=='VariantContext::Choice')['is_variation'])
            self.assertTrue(next(r for r in native['inventory']['parts'] if r['qualified_name']=='VariantContext::Choice::alpha')['is_variant'])
            result=inspect_configuration(model,scope_path,sha256(scope_path.read_bytes()).hexdigest())
            self.assertEqual(result['status'],'unsupported',result)
            self.assertNotIn('Sensor',result['checked'])

    def test_usage_specialization_cannot_hide_inherited_member_override(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);model=directory/'chain.sysml';scope_path=directory/'scope.json'
            model.write_text('package ChainContext { part def Sensor; part def Replacement :> Sensor; part def Assembly { part sensor : Sensor; } part def BaseSystem { part assembly : Assembly { part sensor : Replacement [1] redefines Assembly::sensor; } } part def SelectedSystem :> BaseSystem { part assembly : Assembly [1] redefines BaseSystem::assembly; } part current : SelectedSystem; }')
            scope={'version':'configuration-1.0','root':{'native_name':'ChainContext::current','type':'ChainContext::SelectedSystem'},'selected_roles':{'Assembly':{'parent':'$root','native_name':'ChainContext::SelectedSystem::assembly','type':'ChainContext::Assembly'},'Sensor':{'parent':'Assembly','native_name':'ChainContext::Assembly::sensor','type':'ChainContext::Sensor'}},'open_alternatives':[],'connections':[]}
            scope_path.write_text(json.dumps(scope))
            result=inspect_configuration(model,scope_path,sha256(scope_path.read_bytes()).hexdigest())
            self.assertEqual(result['native']['status'],'pass',result)
            self.assertEqual(result['native']['parser_issues'],[])
            self.assertEqual(result['status'],'unsupported',result)
            self.assertTrue(any(f['rule']=='parent_context' and f['id']=='Sensor' for f in result['findings']))

    def test_usage_owned_overrides_require_current_declaration(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);library=directory/'library.sysml';current=directory/'current.sysml';scope_path=directory/'scope.json'
            library.write_text(MODELS[0].read_text()+'\npackage ReplacementLibrary { private import ConfigurationLibrary::*; part def ReplacementSensor :> Sensor; }\n')
            current.write_text('package ConfigurationContext { private import ConfigurationLibrary::*; private import ReplacementLibrary::*; part current : SelectedSystem { part sensor : ReplacementSensor [1] redefines BaseSystem::sensor; } }')
            scope=deepcopy(SCOPE)
            def inspect():
                scope_path.write_text(json.dumps(scope));return inspect_configuration([library,current],scope_path,sha256(scope_path.read_bytes()).hexdigest())
            result=inspect()
            self.assertEqual(result['status'],'fail',result)
            self.assertTrue(any(f['rule']=='role_redefined' and f['id']=='Sensor' for f in result['findings']))
            self.assertEqual(result['native']['parser_issues'],[])
            scope['selected_roles']['Sensor'].update(native_name='ConfigurationContext::current::sensor',type='ReplacementLibrary::ReplacementSensor')
            self.assertEqual(inspect()['status'],'pass')
            # An override inside a selected parent usage must receive the same
            # treatment as one directly inside the current root usage.
            library.write_text('package NestedConfiguration { part def Sensor; part def Replacement :> Sensor; part def Module { part sensor : Sensor; } part def System { part module : Module { part sensor : Replacement [1] redefines Module::sensor; } } }')
            current.write_text('package ConfigurationContext { private import NestedConfiguration::*; part current : System; }')
            scope={'version':'configuration-1.0','root':{'native_name':'ConfigurationContext::current','type':'NestedConfiguration::System'},'selected_roles':{'Module':{'parent':'$root','native_name':'NestedConfiguration::System::module','type':'NestedConfiguration::Module'},'Sensor':{'parent':'Module','native_name':'NestedConfiguration::Module::sensor','type':'NestedConfiguration::Sensor'}},'open_alternatives':[],'connections':[]}
            result=inspect();self.assertEqual(result['status'],'fail',result)
            self.assertTrue(any(f['rule']=='role_redefined' and f['id']=='Sensor' for f in result['findings']))
            scope['selected_roles']['Sensor'].update(native_name='NestedConfiguration::System::module::sensor',type='NestedConfiguration::Replacement')
            self.assertEqual(inspect()['status'],'pass')

    def test_real_parser_bundle_and_cli(self):
        digest=sha256((BASE/'scope.json').read_bytes()).hexdigest()
        result=inspect_configuration(MODELS,BASE/'scope.json',digest)
        self.assertEqual(result['status'],'pass',result)
        self.assertEqual(len(result['model_files']),2)
        run=subprocess.run([sys.executable,str(ROOT/'scripts/configuration.py'),'check',*map(str,MODELS),'--scope',str(BASE/'scope.json'),'--scope-sha256',digest,'--json'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(json.loads(run.stdout)['view'],result['view'])

    def test_stale_scope_and_bundle_fingerprints(self):
        digest=sha256((BASE/'scope.json').read_bytes()).hexdigest()
        self.assertEqual(inspect_configuration(MODELS,BASE/'scope.json','0'*64)['status'],'error')
        self.assertEqual(inspect_configuration(MODELS,BASE/'scope.json',digest,expected_model_sha256='0'*64)['status'],'error')

    def test_actual_removal_and_historical_root_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);library=directory/'library.sysml';current=directory/'current.sysml'
            library.write_text(MODELS[0].read_text().replace('part accessory : Accessory;',''))
            current.write_text(MODELS[1].read_text())
            digest=sha256((BASE/'scope.json').read_bytes()).hexdigest()
            result=inspect_configuration([library,current],BASE/'scope.json',digest)
            self.assertEqual(result['status'],'fail',result)
            library.write_text(MODELS[0].read_text());current.write_text(MODELS[1].read_text().replace('part current : SelectedSystem;','part current : AlternativeSystem;'))
            self.assertEqual(inspect_configuration([library,current],BASE/'scope.json',digest)['status'],'fail')
            library.write_text(MODELS[0].read_text().replace('part accessory : Accessory;', 'part accessory : Accessory [0..0];'))
            current.write_text(MODELS[1].read_text())
            result=inspect_configuration([library,current],BASE/'scope.json',digest)
            self.assertEqual(result['status'],'fail',result)

    def test_input_drift_during_parser_cannot_leave_successful_view(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            models=[]
            for path in MODELS:
                target=Path(directory)/path.name;target.write_bytes(path.read_bytes());models.append(target)
            def mutate(paths,**kwargs):
                result=check_sysml(paths,**kwargs);models[0].write_text(models[0].read_text()+'\n');return result
            with patch('verifier.configuration.check_sysml',side_effect=mutate):
                result=inspect_configuration(models,BASE/'scope.json',sha256((BASE/'scope.json').read_bytes()).hexdigest())
            self.assertEqual(result['status'],'error');self.assertNotIn('view',result)

    def test_native_action_parameter_is_not_a_design_context(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);current=directory/'context.sysml';scope_path=directory/'scope.json'
            current.write_text('package ConfigurationContext { private import ConfigurationLibrary::*; action def Review { in part current : SelectedSystem; } }')
            scope=deepcopy(SCOPE);scope['root']['native_name']='ConfigurationContext::Review::current'
            scope_path.write_text(json.dumps(scope))
            result=inspect_configuration([MODELS[0],current],scope_path,sha256(scope_path.read_bytes()).hexdigest())
            self.assertEqual(result['native']['status'],'pass',result)
            self.assertEqual(result['status'],'fail',result)
            self.assertTrue(any(f['rule']=='root_context' for f in result['findings']))


@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(), 'Pinned SysML parser required')
class ConnectedNativeSelectionTests(unittest.TestCase):
    def inspect(self, current=None, mutate_scope=None, library=None):
        base=BASE/'connected'
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            directory=Path(directory);lib=directory/'library.sysml';model=directory/'current.sysml';scope_path=directory/'scope.json'
            lib.write_text((base/'library.sysml').read_text() if library is None else library)
            model.write_text((base/'current.sysml').read_text() if current is None else current)
            scope=json.loads((base/'scope.json').read_text())
            if mutate_scope: mutate_scope(scope)
            scope_path.write_text(json.dumps(scope))
            result=inspect_configuration([lib,model],scope_path,sha256(scope_path.read_bytes()).hexdigest())
            self.assertEqual(result['native']['status'],'pass',result)
            return result

    def test_connected_current_context_and_native_view(self):
        result=self.inspect();self.assertEqual(result['status'],'pass',result)
        graph=result['system_view'];self.assertEqual(set(graph['nodes']),{'$root','Sensor','Enterprise'})
        self.assertEqual(graph['edges']['DataLink']['from']['path'],['LinkContext::current','LinkLibrary::System::sensor','LinkLibrary::Sensor::output'])
        self.assertFalse(graph['edges']['DataLink']['directed'])
        self.assertIn('Native adjacency DataLink',render_text(result))
        self.assertEqual(result['connectivity_claim'],'selected_binary_adjacencies')

    def test_missing_historical_and_wrong_external_connections_fail(self):
        text=(BASE/'connected/current.sysml').read_text()
        cases=[text.replace('    connection dataLink connect current.sensor.output to enterprise.input;',''),
               text.replace('current.sensor.output to enterprise.input','historical.sensor.output to enterprise.input'),
               text.replace('current.sensor.output to enterprise.input','current.sensor.output to secondReceiver.input')]
        for source in cases:
            result=self.inspect(current=source);self.assertEqual(result['status'],'fail',result)
            self.assertEqual(result['system_view']['edges'],{})

    def test_external_same_typed_peer_in_another_package_fails(self):
        text=(BASE/'connected/current.sysml').read_text()+'\npackage OtherContext { private import LinkLibrary::*; ref part enterprise : Receiver; }\n'
        result=self.inspect(current=text,mutate_scope=lambda s:s['external_roles']['Enterprise'].update(native_name='OtherContext::enterprise'))
        self.assertEqual(result['status'],'fail',result)
        self.assertTrue(any(f['rule']=='external_context' for f in result['findings']))

    def test_endpoint_reversal_and_usage_owned_external_connection(self):
        text=(BASE/'connected/current.sysml').read_text()
        result=self.inspect(current=text.replace('current.sensor.output to enterprise.input','enterprise.input to current.sensor.output'))
        self.assertEqual(result['status'],'pass',result)
        local=text.replace('part current : System;', 'part current : System { connection localLink connect sensor.output to enterprise.input; }').replace('    connection dataLink connect current.sensor.output to enterprise.input;','')
        def select(s):s['connections'][0].update(owner='LinkContext::current',native_name='LinkContext::current::localLink')
        result=self.inspect(current=local,mutate_scope=select)
        self.assertEqual(result['status'],'pass',result)
        self.assertEqual(result['system_view']['edges']['DataLink']['to']['path'],['LinkContext::enterprise','LinkLibrary::Receiver::input'])

    def test_anonymous_connection_requires_unique_native_endpoint_pair(self):
        text=(BASE/'connected/current.sysml').read_text().replace('connection dataLink connect','connect')
        result=self.inspect(current=text,mutate_scope=lambda s:s['connections'][0].update(native_name=None))
        self.assertEqual(result['status'],'pass',result)
        duplicate=text.replace('connect current.sensor.output to enterprise.input;','connect current.sensor.output to enterprise.input; connect current.sensor.output to enterprise.input;')
        result=self.inspect(current=duplicate,mutate_scope=lambda s:s['connections'][0].update(native_name=None))
        self.assertEqual(result['status'],'fail',result)
        self.assertEqual(result['system_view']['edges'],{})

    def test_binding_is_not_ordinary_native_adjacency(self):
        text=(BASE/'connected/current.sysml').read_text().replace('connection dataLink connect current.sensor.output to enterprise.input;', 'binding dataLink bind current.sensor.output = enterprise.input;')
        result=self.inspect(current=text)
        self.assertEqual(result['status'],'unsupported',result)
        self.assertEqual(result['system_view']['edges'],{})

    def test_inherited_port_and_port_override_are_distinct(self):
        library=(BASE/'connected/library.sysml').read_text().replace('part sensor : Sensor;', 'part sensor : InheritedSensor;')
        result=self.inspect(library=library,mutate_scope=lambda s:s['selected_roles']['Sensor'].update(type='LinkLibrary::InheritedSensor'))
        self.assertEqual(result['status'],'pass',result)
        library=(BASE/'connected/library.sysml').read_text().replace('part def System {','part def UpdatedSensor :> Sensor { port output : Data [1] redefines Sensor::output; }\n    part def System {').replace('part sensor : Sensor;','part sensor : UpdatedSensor;')
        def select(s):s['selected_roles']['Sensor']['type']='LinkLibrary::UpdatedSensor'
        result=self.inspect(library=library,mutate_scope=select)
        self.assertEqual(result['status'],'fail',result)
        self.assertTrue(any(f['rule']=='port_redefined' for f in result['findings']))
        self.assertEqual(result['system_view']['edges'],{})
        def updated(s):select(s);s['connections'][0]['from']['port']='LinkLibrary::UpdatedSensor::output'
        result=self.inspect(library=library,mutate_scope=updated)
        self.assertEqual(result['status'],'unsupported',result)

    def test_type_owned_connection_is_unsupported_and_disclosed(self):
        library=(BASE/'connected/library.sysml').read_text().replace('part sensor : Sensor;', 'part sensor : Sensor; connection internal connect sensor.output to sensor.output;')
        def select(s):s['connections'][0].update(owner='LinkLibrary::System',native_name='LinkLibrary::System::internal',to=dict(s['connections'][0]['from']))
        result=self.inspect(library=library,mutate_scope=select)
        self.assertEqual(result['status'],'unsupported',result)
        self.assertTrue(any(o['id']=='native:LinkLibrary::System::internal' for o in result['system_view']['omissions']))

    def test_every_selected_parent_is_part_of_native_endpoint_identity(self):
        library=(BASE/'connected/library.sysml').read_text().replace('part def System {\n        part sensor : Sensor;\n    }', 'part def Module { part sensor : Sensor; } part def System { part module : Module; part otherModule : Module; }')
        current=(BASE/'connected/current.sysml').read_text().replace('current.sensor.output','current.module.sensor.output')
        def select(s):
            s['selected_roles']={'Module':{'parent':'$root','native_name':'LinkLibrary::System::module','type':'LinkLibrary::Module'},'Sensor':{'parent':'Module','native_name':'LinkLibrary::Module::sensor','type':'LinkLibrary::Sensor'}}
        result=self.inspect(library=library,current=current,mutate_scope=select)
        self.assertEqual(result['status'],'pass',result)
        self.assertEqual(result['system_view']['edges']['DataLink']['from']['path'],['LinkContext::current','LinkLibrary::System::module','LinkLibrary::Module::sensor','LinkLibrary::Sensor::output'])
        result=self.inspect(library=library,current=current.replace('current.module.sensor.output','current.otherModule.sensor.output'),mutate_scope=select)
        self.assertEqual(result['status'],'fail',result)

    def test_variable_port_types_cannot_supply_selected_endpoint_proof(self):
        library=(BASE/'connected/library.sysml').read_text()
        variants=[library.replace('port def Data;', 'variation port def Data;'),
                  library.replace('port def Data;', 'variation port def VariableData; port def Data :> VariableData;'),
                  library.replace('port def Data;', 'variation port def Data;').replace('port output : Data;', 'port output : ~Data;')]
        for source in variants:
            # Keep the peer ordinary so it cannot mask a missed variation on
            # the selected sensor's direct, inherited or conjugated port type.
            source=source.replace('part def Sensor {','port def OtherData; part def Sensor {').replace('port input : Data;','port input : OtherData;')
            result=self.inspect(library=source)
            self.assertEqual(result['status'],'unsupported',result)
            self.assertEqual(result['native']['parser_issues'],[])
            self.assertEqual(result['system_view']['edges'],{})
            self.assertTrue(any(f['rule']=='port_type' for f in result['findings']))
        ordinary=self.inspect(library=library.replace('port output : Data;', 'port output : ~Data;'))
        self.assertEqual(ordinary['status'],'pass',ordinary)

    def test_empty_connection_scope_discloses_native_omission(self):
        result=self.inspect(mutate_scope=lambda s:s.update(connections=[]))
        self.assertEqual(result['status'],'pass',result)
        self.assertEqual(result['connectivity_claim'],'empty_scope_no_connectivity_claim')
        self.assertEqual(result['system_view']['edges'],{})
        self.assertTrue(any(o['id']=='native:LinkContext::dataLink' and o['status']=='not_selected' for o in result['system_view']['omissions']))


if __name__ == '__main__': unittest.main()
