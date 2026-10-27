"""Exact conditional mean-flow consistency and its applicability refusals."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verifier.inquiry import analyze,inspect_inquiry,draft_model,schema,render_text,MARKER
from verifier.sysml import check_sysml,JAR,CLASSES

MODEL=ROOT/'examples/inquiry/flow-consistency.sysml'
SOURCE=ROOT/'examples/inquiry/flow-brief.md'
RECORD=json.loads(MODEL.read_text().split(MARKER+'\n',1)[1].rsplit('        */',1)[0])
PARSER=JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


def evaluate(change=lambda r:None):
    r=deepcopy(RECORD);change(r)
    native={'status':'pass','model_sha256':'a'*64,'inventory':{'actions':[],
        'parts':[{'qualified_name':'FlowExample::station'}]}}
    evidence={k:{'status':'pass','detail':'Synthetic source-binding unit control'} for k in r['sources']}
    return analyze(r,native,evidence)


class FlowControls(unittest.TestCase):
    def test_declared_means_agree_without_claiming_staffing_or_stationarity_proof(self):
        report=evaluate();flow=report['flow_checks']['FLOW']
        self.assertEqual(report['status'],'pass')
        self.assertEqual(flow['predicted_L'],{'value':'2','unit':'requests'})
        self.assertEqual(flow['staffing_adequacy'],'not_evaluated')
        self.assertEqual(flow['applicability_validation'],'not_evaluated')
        text=render_text(report)
        self.assertIn('mean-flow conditions',text);self.assertNotIn('Calculation was not completed',text)

    def test_difference_uses_an_explicit_tolerance_not_an_invented_one(self):
        def change(r):r['flow_checks']['FLOW']['L']['value']='3'
        self.assertEqual(evaluate(change)['status'],'fail')
        def tolerate(r):
            change(r);r['flow_checks']['FLOW']['tolerance']['value']='1'
        self.assertEqual(evaluate(tolerate)['status'],'pass')
        def absent(r):r['flow_checks']['FLOW']['tolerance']=None
        self.assertEqual(evaluate(absent)['status'],'unknown')

    def test_each_applicability_condition_is_required_and_not_inferred(self):
        for key in RECORD['flow_checks']['FLOW']['conditions']:
            for value,expected in [(None,'unknown'),(False,'unsupported')]:
                def change(r,key=key,value=value):r['flow_checks']['FLOW']['conditions'][key]['value']=value
                report=evaluate(change)
                self.assertEqual(report['status'],expected,(key,report))
                self.assertIsNone(report['flow_checks']['FLOW']['predicted_L'])

    def test_matching_population_rate_time_units_are_required_without_conversion(self):
        for field in ['L','W','arrival_rate','tolerance']:
            def change(r,field=field):r['flow_checks']['FLOW'][field]['unit']='other'
            self.assertEqual(evaluate(change)['status'],'unsupported')

    def test_zero_arrival_rate_is_outside_the_retained_1961_theorem_profile(self):
        def change(r):r['flow_checks']['FLOW']['arrival_rate']['value']='0'
        self.assertEqual(evaluate(change)['status'],'unsupported')

    def test_missing_means_context_or_basis_stays_unknown(self):
        for field in ['L','arrival_rate','W']:
            def change(r,field=field):r['flow_checks']['FLOW'][field]=None
            self.assertEqual(evaluate(change)['status'],'unknown')
        def context(r):r['flow_checks']['FLOW']['averaging_context']=''
        self.assertEqual(evaluate(context)['status'],'unknown')
        def basis(r):r['flow_checks']['FLOW']['W']['basis']=None
        self.assertEqual(evaluate(basis)['status'],'unknown')

    def test_non_object_bad_types_negative_values_and_old_version_extension_refused(self):
        self.assertEqual(analyze([],{'status':'pass'}, {})['status'],'error')
        for change in [lambda r:r.update(version='inquiry-1.0'),
                       lambda r:r['flow_checks']['FLOW']['W'].update(value=-1),
                       lambda r:r['flow_checks']['FLOW']['W'].update(value='-1'),
                       lambda r:r['flow_checks']['FLOW']['conditions']['finite_means'].update(value='yes')]:
            r=deepcopy(RECORD);change(r);self.assertRaises(ValueError,schema,r)

    def test_missing_source_binding_prevents_any_flow_arithmetic(self):
        report=analyze(RECORD,{'status':'pass','model_sha256':'a'*64,
            'inventory':{'parts':[{'qualified_name':'FlowExample::station'}],'actions':[]}}, {})
        self.assertEqual(report['status'],'unknown');self.assertNotIn('flow_checks',report)

    def test_exact_small_decimals_and_unrounded_precision_limit(self):
        def exact(r):
            f=r['flow_checks']['FLOW'];f['arrival_rate']['value']='0.1';f['W']['value']='0.2';f['L']['value']='0.02'
        report=evaluate(exact);self.assertEqual(report['status'],'pass')
        self.assertEqual(report['flow_checks']['FLOW']['predicted_L']['value'],'0.02')
        def too_precise(r):
            f=r['flow_checks']['FLOW'];f['arrival_rate']['value']='0.'+'0'*31+'1';f['W']['value']='0.'+'0'*31+'1'
        self.assertEqual(evaluate(too_precise)['status'],'unsupported')


@unittest.skipUnless(PARSER,'Install the pinned SysML parser')
class NativeFlowControls(unittest.TestCase):
    def test_native_model_and_actual_skill_launcher(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            p=subprocess.run([sys.executable,'-B',str(ROOT/'.agents/skills/develop-system-concept/scripts/cse.py'),
                'question','answer',str(MODEL),'--source','FLOW_SRC='+str(SOURCE),'--format','text'],
                cwd=directory,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('Predicted mean count 2 requests',p.stdout)
            self.assertIn('staffing adequacy is not evaluated',p.stdout)

    def test_native_nonstationary_case_and_stale_source_refuse_success(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            d=Path(directory);r=deepcopy(RECORD);r['flow_checks']['FLOW']['conditions']['strict_stationarity']['value']=False
            model=d/'case.sysml';model.write_text(draft_model(r,'FlowExample'))
            self.assertEqual(inspect_inquiry(model,{'FLOW_SRC':SOURCE})['status'],'unsupported')
            source=d/'changed.md';source.write_text(SOURCE.read_text()+'Unreviewed change.\n')
            report=inspect_inquiry(MODEL,{'FLOW_SRC':source})
            self.assertEqual(report['status'],'fail');self.assertNotIn('flow_checks',report)

    def test_changed_model_clears_computed_flow_results(self):
        native=check_sysml(MODEL,syntax_only=True,kind='concept')
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            model=Path(directory)/'case.sysml';model.write_bytes(MODEL.read_bytes())
            def mutate(*args,**kwargs):
                model.write_text(model.read_text()+'\n// changed during native checking\n')
                return deepcopy(native)
            with patch('verifier.inquiry.check_sysml',side_effect=mutate):
                report=inspect_inquiry(model,{'FLOW_SRC':SOURCE})
            self.assertEqual(report['status'],'error');self.assertEqual(report['evaluation'],'not_run')
            self.assertNotIn('flow_checks',report)

    def test_shared_human_task_model_has_conditional_rate_results_without_new_authority(self):
        model=ROOT/'examples/human-task-review/concept.sysml'
        sources={'CAP_CASE':ROOT/'examples/human-task-review/capacity-brief.md'}
        existing=inspect_inquiry(model,sources,'A_EXISTING',['R_CLERK'])
        self.assertEqual(existing['status'],'fail')
        row=existing['alternatives']['A_EXISTING']['functions'][0]
        self.assertEqual(row['assignment_status'],'pass')
        self.assertEqual(row['capacity'],{'value':'8','unit':'requests_per_hour'})
        improved=inspect_inquiry(model,sources,'A_LARGER',['R_CLERK'])
        self.assertEqual(improved['status'],'pass');self.assertEqual(improved['operational_continuity'],'unknown')
        self.assertEqual(inspect_inquiry(model,sources,'A_UNQUALIFIED',['R_CLERK'])['status'],'unknown')
        # An application-loss query is not admitted by this deliberately scoped
        # clerk-rate model; it must not silently reuse the backup rate.
        self.assertEqual(inspect_inquiry(model,sources,'A_LARGER',['R_APP'])['status'],'error')


if __name__=='__main__':unittest.main()
