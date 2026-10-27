"""Independent expected answers for original questions; no physical acceptance oracle."""
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
from verifier.inquiry import analyze,inspect_inquiry,draft_model,write_draft,render_text,decimal,VERSION,MARKER
from verifier.foundation import Invalid
from verifier.sysml import JAR
from fractions import Fraction


def record(domain='software'):
    text=(ROOT/'examples/inquiry'/(domain+'.sysml')).read_text()
    return json.loads(text.split(MARKER+'\n',1)[1].rsplit('        */',1)[0])


def native(r):return {'status':'pass','model_sha256':'a'*64,'inventory':{'actions':[{'qualified_name':f['native_name']} for f in r['functions'].values()],
                       'parts':[{'qualified_name':p['native_name']} for p in r['resources'].values()]}}
def evidence(r):return {k:{'status':'pass','detail':'Synthetic verified-source adapter for unit tests','actual_sha256':s['sha256'],'expected_sha256':s['sha256'],'kind':s['kind'],'excerpt':s['excerpt']} for k,s in r['sources'].items()}
def result(domain='software',alternative='A_EXISTING',lost=None,change=lambda r:None):
    r=record(domain);change(r);return analyze(r,native(r),evidence(r),alternative,[] if lost is None else lost)


class InquiryTests(unittest.TestCase):
    def test_software_assignment_survives_but_rate_fails(self):
        r=result(lost=['R_PRIMARY']);f=r['alternatives']['A_EXISTING']['functions'][0]
        self.assertEqual(r['status'],'fail');self.assertEqual(f['assignment_status'],'pass')
        self.assertEqual(f['capacity'],{'value':'8','unit':'jobs_per_minute'})
        self.assertEqual(r['operational_continuity'],'unknown');self.assertEqual(r['acceptance'],'not_evaluated')

    def test_software_larger_candidate_and_unqualified_rate_are_distinct(self):
        r=result(alternative='A_LARGER',lost=['R_PRIMARY']);self.assertEqual(r['status'],'pass')
        self.assertEqual(r['alternatives']['A_LARGER']['functions'][0]['capacity']['value'],'16')
        r=result(alternative='A_UNQUALIFIED');self.assertEqual(r['status'],'unknown')
        self.assertIsNone(r['alternatives']['A_UNQUALIFIED']['functions'][0]['capacity'])

    def test_question_context_and_no_loss_hypothesis_are_separate(self):
        r=result();text=render_text(r)
        self.assertIn('Recorded question:',text)
        self.assertIn('Hypothesis: no resources selected unavailable',text)
        self.assertIn('Conditions in the recorded question are not inferred',text)
        self.assertFalse(r['evaluated_hypothesis']['question_conditions_inferred'])
        self.assertEqual(r['evaluated_hypothesis']['unavailable'],[])
        self.assertEqual(r['alternatives']['A_EXISTING']['functions'][0]['capacity']['value'],'28')
        lost=result(lost=['R_PRIMARY']);self.assertEqual(lost['evaluated_hypothesis']['unavailable'],['R_PRIMARY'])
        self.assertEqual(lost['alternatives']['A_EXISTING']['functions'][0]['capacity']['value'],'8')

    def test_assignment_only_gap_has_its_own_next_decision(self):
        def change(r):
            r['sources']['MINIMUM']={'sha256':'c'*64,'excerpt':'New hypothetical proposal: at least two distinct assignments.','kind':'proposal'}
            r['functions']['F_PROCESS'].update(minimum_assignments=2,minimum_basis='MINIMUM')
        r=result(alternative='A_LARGER',lost=['R_PRIMARY'],change=change)
        f=r['alternatives']['A_LARGER']['functions'][0]
        self.assertEqual(f['assignment_status'],'fail');self.assertEqual(f['capacity_status'],'pass')
        self.assertEqual(f['assignment_gap'],1);self.assertEqual(f['minimum_assignments'],2)
        text=render_text(r);self.assertIn('needs 1 additional distinct assignments',text)
        self.assertIn('unchanged minimum 2',text);self.assertIn('Adequate rate does not close',text)
        both=result(lost=['R_PRIMARY','R_BACKUP']);self.assertIn('additional distinct assignments',render_text(both))
        self.assertIn('revise the workload',render_text(both))

    def test_hardware_channel_case_and_spare(self):
        r=result('hardware',lost=['R_FIRST']);self.assertEqual(r['status'],'fail')
        self.assertEqual(r['alternatives']['A_EXISTING']['functions'][0]['capacity']['value'],'2')
        self.assertEqual(result('hardware','A_SPARE',['R_FIRST'])['status'],'pass')
        self.assertEqual(result('hardware','A_UNQUALIFIED')['status'],'unknown')

    def test_physical_process_stage_shortfall_and_dedicated_candidate(self):
        r=result('physical-process');rows=r['alternatives']['A_EXISTING']['functions']
        self.assertEqual([(x['capacity']['value'],x['capacity_status']) for x in rows],[('4','fail'),('8','pass')])
        self.assertEqual(result('physical-process','A_FASTER')['status'],'pass')

    def test_shared_means_need_concurrent_budget_basis(self):
        r=result('physical-process','A_SHARED');self.assertEqual(r['status'],'unknown')
        self.assertTrue(all(x['capacity'] is None for x in r['alternatives']['A_SHARED']['functions']))
        self.assertIn('simultaneous per-function rates',render_text(r))
        def budget(r):
            r['sources']['BUDGET']={'sha256':'b'*64,'excerpt':'New hypothetical assumption: per-function shared rates are simultaneously attainable.','kind':'assumption'}
            r['alternatives']['A_SHARED']['concurrency_basis']='BUDGET'
        self.assertEqual(result('physical-process','A_SHARED',change=budget)['status'],'pass')

    def test_missing_assignment_criterion_does_not_erase_known_capacity(self):
        def change(r):r['functions']['F_PROCESS'].update(minimum_assignments=None,minimum_basis=None)
        r=result(lost=['R_PRIMARY'],change=change);f=r['alternatives']['A_EXISTING']['functions'][0]
        self.assertEqual(f['assignment_status'],'unknown');self.assertEqual(f['capacity']['value'],'8')
        self.assertEqual(f['capacity_status'],'fail');self.assertNotEqual(r['status'],'pass')

    def test_independent_composition_required_and_unsupported_not_run(self):
        def missing(r):r['alternatives']['A_EXISTING']['composition']={}
        self.assertEqual(result(change=missing)['status'],'unknown')
        def unsupported(r):r['alternatives']['A_EXISTING']['composition']['F_PROCESS']['method']='max'
        self.assertEqual(result(change=unsupported)['status'],'unsupported')
        self.assertEqual(result(lost=['R_PRIMARY'],change=unsupported)['status'],'unsupported')

    def test_units_never_convert_silently(self):
        def change(r):r['alternatives']['A_EXISTING']['assignments'][0]['capacity']['unit']='jobs_per_hour'
        r=result(change=change);self.assertEqual(r['status'],'unsupported')
        self.assertIsNone(r['alternatives']['A_EXISTING']['functions'][0]['capacity'])

    def test_native_timeout_and_unsupported_diagnostic_shapes_remain_unrun(self):
        model=ROOT/'examples/inquiry/software.sysml'
        for status,code,detail in [('error','native_check_error','Native parser timed out'),('unsupported','unsupported','Native operation unsupported'),('unknown','incomplete','Native check incomplete')]:
            diagnostic={'code':code,'detail':detail}
            with patch('verifier.inquiry.check_sysml',return_value={'status':status,'findings':[diagnostic]}):
                r=inspect_inquiry(model,{},'A_EXISTING',['R_PRIMARY'])
            self.assertEqual(r['status'],status);self.assertEqual(r['findings'],[diagnostic])
            self.assertEqual(r['request'],{'alternative':'A_EXISTING','unavailable':['R_PRIMARY']})
            self.assertEqual(r['evaluation'],'not_run');self.assertFalse(r['alternatives']);self.assertIsNone(r['evaluated_hypothesis'])
            for expert in (False,True):
                text=render_text(r,expert);self.assertIn(detail,text);self.assertIn('Hypothesis not evaluated',text)
                self.assertNotIn('Declared capacity',text)

    def test_exact_decimal_sum(self):
        def change(r):
            r['functions']['F_PROCESS']['demand']['value']='0.3'
            for p,v in zip(r['alternatives']['A_EXISTING']['assignments'],['0.1','0.2']):p['capacity']['value']=v
        r=result(change=change);self.assertEqual(r['status'],'pass')
        self.assertEqual(r['alternatives']['A_EXISTING']['functions'][0]['capacity']['value'],'0.3')
        self.assertEqual(decimal(Fraction(123456789012345678901234567890,1000)),'123456789012345678901234567.89')
        with self.assertRaises(Invalid):decimal(Fraction(1,3))

    def test_joint_loss_zero_capacity_and_unused_loss(self):
        r=result(lost=['R_PRIMARY','R_BACKUP']);f=r['alternatives']['A_EXISTING']['functions'][0]
        self.assertEqual(f['capacity']['value'],'0');self.assertEqual(f['assignment_status'],'fail')
        self.assertEqual(result(lost=['R_EXPERIMENTAL'])['status'],'pass')

    def test_declared_incapable_provider_is_not_counted_as_capacity(self):
        def change(r):r['alternatives']['A_EXISTING']['assignments'][1]['capability']='incapable'
        r=result(lost=['R_PRIMARY'],change=change);f=r['alternatives']['A_EXISTING']['functions'][0]
        self.assertEqual(f['assignment_status'],'pass');self.assertEqual(f['capacity']['value'],'0')
        self.assertEqual(f['declared_capable_remaining'],0)

    def test_missing_rate_and_missing_basis_are_unknown(self):
        self.assertEqual(result(change=lambda r:r['alternatives']['A_EXISTING']['assignments'][0].update(capacity=None))['status'],'unknown')
        self.assertEqual(result(change=lambda r:r['question'].update(basis=None))['status'],'unknown')

    def test_bad_sources_cannot_pass(self):
        r=record();e=evidence(r);e['SRC'].update(status='fail',detail='Stale source')
        self.assertEqual(analyze(r,native(r),e,'A_EXISTING',[])['status'],'fail')
        self.assertEqual(analyze(r,native(r),{},'A_EXISTING',[])['status'],'unknown')
        self.assertEqual(result(change=lambda r:r['functions']['F_PROCESS']['demand'].update(basis='MISSING'))['status'],'fail')

    def test_bad_selectors_and_identity_aliases_are_rejected(self):
        for alt,lost in [('ABSENT',[]),('A_EXISTING',['R_PRIMARY','R_PRIMARY']),('A_EXISTING',['UNKNOWN'])]:
            r=record();answer=analyze(r,native(r),evidence(r),alt,lost)
            self.assertEqual(answer['status'],'error');self.assertEqual(answer['alternatives'],{})
            self.assertEqual(answer['request']['unavailable'],lost)
        def alias(r):r['resources']['R_BACKUP']['native_name']=r['resources']['R_PRIMARY']['native_name']
        self.assertEqual(result(change=alias)['status'],'fail')

    def test_duplicate_pairs_negative_float_nonfinite_and_code_fields_rejected(self):
        changes=[lambda r:r['alternatives']['A_EXISTING']['assignments'].append(deepcopy(r['alternatives']['A_EXISTING']['assignments'][0])),
                 lambda r:r['functions']['F_PROCESS']['demand'].update(value='-1'),
                 lambda r:r['functions']['F_PROCESS']['demand'].update(value=0.3),
                 lambda r:r['functions']['F_PROCESS']['demand'].update(value='NaN'),
                 lambda r:r.update(executor='arbitrary-code')]
        for change in changes:self.assertEqual(result(change=change)['status'],'error')

    def test_input_and_criterion_values_are_unchanged(self):
        r=record();n=native(r);e=evidence(r);saved=deepcopy((r,n,e))
        analyze(r,n,e,'A_EXISTING',['R_PRIMARY']);self.assertEqual((r,n,e),saved)

    def test_bare_question_is_a_useful_draft_not_pass(self):
        r={'version':VERSION,'question':{'text':'Can we meet the workload?','basis':None},'sources':{},'functions':{},'resources':{},'alternatives':{}}
        a=analyze(r,native(r),{},None,[]);self.assertEqual(a['status'],'unknown')
        self.assertIn('workload/unit',render_text(a))

    def test_names_stay_unambiguous(self):
        def change(r):
            r['resources']['R_PRIMARY']['label']='Worker';r['resources']['R_BACKUP']['label']='Worker'
        a=result(lost=['R_PRIMARY'],change=change)
        self.assertIn('Hypothesis: BackupProcessing::primaryWorker unavailable.',render_text(a))
        self.assertIn('BackupProcessing::backupWorker',render_text(a))

    def test_input_change_after_calculation_refuses_all_rows(self):
        r=record();model=ROOT/'examples/inquiry/software.sysml';source=ROOT/'examples/inquiry/software-brief.md'
        m=model.read_bytes();raw=source.read_bytes();n=native(r);n['model_sha256']=sha256(m).hexdigest()
        n['inventory']['documents']=[{'name':'cseInquiry','body':MARKER+'\n'+json.dumps(r),'owner':'BackupProcessing::EngineeringQuestion'}]
        n['inventory']['concerns']=[{'qualified_name':'BackupProcessing::EngineeringQuestion'}]
        calls={}
        def read(path,cap):
            path=Path(path);calls[path]=calls.get(path,0)+1
            return m if path==model else (raw if calls[path]==1 else raw+b' changed')
        with patch('verifier.inquiry.check_sysml',return_value=n),patch('verifier.inquiry.read_regular',side_effect=read):
            report=inspect_inquiry(model,{'SRC':source},'A_LARGER',['R_PRIMARY'])
        self.assertEqual(report['status'],'error');self.assertEqual(report['evaluation'],'not_run')
        self.assertEqual(report['alternatives'],{});self.assertNotIn('summary',report)
        self.assertEqual(report['input_stability'],'error')

    def test_generation_is_exclusive_and_escapes_document_delimiter(self):
        r=record();r['question']['text']='Question containing */ literally'
        text=draft_model(r,'BackupProcessing');self.assertNotIn('*/ literally',text)
        body=text.split(MARKER+'\n',1)[1].rsplit('        */',1)[0];self.assertEqual(json.loads(body),r)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            p=Path(d)/'draft.sysml';write_draft(p,text)
            with self.assertRaises(FileExistsError):write_draft(p,'replacement')
            self.assertEqual(p.read_text(),text)
        r['resources']['R_PRIMARY']['native_name']='BackupProcessing::bad;statement'
        with self.assertRaises(Invalid):draft_model(r,'BackupProcessing')


@unittest.skipUnless(JAR.exists(),'pinned parser missing')
class NativeInquiryTests(unittest.TestCase):
    def test_original_domains_through_three_actual_launchers(self):
        for domain,skill,alternative,lost,expected in [('software','develop-system-concept','A_EXISTING','R_PRIMARY','fail'),
                ('hardware','develop-conops','A_SPARE','R_FIRST','pass'),('physical-process','develop-operational-scenarios','A_SHARED',None,'unknown')]:
            argv=[sys.executable,'-B',str(ROOT/'skills'/skill/'scripts/cse.py'),'question','answer',str(ROOT/'examples/inquiry'/(domain+'.sysml')),
                  '--source','SRC='+str(ROOT/'examples/inquiry'/(domain+'-brief.md')),'--alternative',alternative]
            if lost:argv+=['--unavailable',lost]
            done=subprocess.run(argv,capture_output=True,text=True,timeout=90);r=json.loads(done.stdout)
            self.assertEqual(r['status'],expected);self.assertEqual(done.returncode,0 if expected=='pass' else 1)
            self.assertEqual(r['native_status'],'pass');self.assertEqual(r['sources']['SRC']['status'],'pass')
            for audience in ('beginner','expert'):
                text=subprocess.run(argv+['--format','text','--audience',audience],capture_output=True,text=True,timeout=90)
                self.assertEqual(text.returncode,done.returncode);self.assertEqual(text.stdout.strip(),render_text(r,audience=='expert'))

    def test_actual_hypothesis_views_and_source_bound_assignment_only_gap(self):
        for domain,first,second in [('software','R_PRIMARY','R_BACKUP'),('hardware','R_FIRST','R_SECOND')]:
            for lost in ([],[first],[first,second]):
                argv=[sys.executable,'-B',str(ROOT/'skills/develop-system-concept/scripts/cse.py'),'question','answer',
                    str(ROOT/'examples/inquiry'/(domain+'.sysml')),'--source','SRC='+str(ROOT/'examples/inquiry'/(domain+'-brief.md'))]
                for resource in lost:argv+=['--unavailable',resource]
                raw=subprocess.run(argv,capture_output=True,text=True,timeout=90);r=json.loads(raw.stdout)
                self.assertEqual(r['evaluated_hypothesis']['unavailable'],sorted(lost))
                self.assertFalse(r['evaluated_hypothesis']['question_conditions_inferred'])
                for audience in ('beginner','expert'):
                    text=subprocess.run(argv+['--format','text','--audience',audience],capture_output=True,text=True,timeout=90)
                    self.assertEqual(text.returncode,raw.returncode);self.assertEqual(text.stdout.strip(),render_text(r,audience=='expert'))
                    self.assertIn('Recorded question:',text.stdout)
                    if not lost:self.assertIn('no resources selected unavailable',text.stdout)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            d=Path(d);source=d/'minimum.md';source.write_text('Original hypothetical proposal: at least two distinct assignments for processing jobs.\n')
            data=record();data['sources']['MINIMUM']={'sha256':sha256(source.read_bytes()).hexdigest(),'excerpt':source.read_text().strip(),'kind':'proposal'}
            data['functions']['F_PROCESS'].update(minimum_assignments=2,minimum_basis='MINIMUM')
            model=d/'gap.sysml';model.write_text(draft_model(data,'BackupProcessing'))
            argv=[sys.executable,'-B',str(ROOT/'scripts/question.py'),'answer',str(model),
                '--source','SRC='+str(ROOT/'examples/inquiry/software-brief.md'),'--source','MINIMUM='+str(source),
                '--alternative','A_LARGER','--unavailable','R_PRIMARY']
            raw=subprocess.run(argv,capture_output=True,text=True,timeout=90);r=json.loads(raw.stdout)
            f=r['alternatives']['A_LARGER']['functions'][0]
            self.assertEqual(r['status'],'fail');self.assertEqual(f['assignment_status'],'fail')
            self.assertEqual(f['capacity_status'],'pass');self.assertEqual(f['assignment_gap'],1)
            self.assertEqual(r['sources']['MINIMUM']['status'],'pass')
            for audience in ('beginner','expert'):
                text=subprocess.run(argv+['--format','text','--audience',audience],capture_output=True,text=True,timeout=90)
                self.assertEqual(text.returncode,1);self.assertEqual(text.stdout.strip(),render_text(r,audience=='expert'))
                self.assertIn('unchanged minimum 2',text.stdout);self.assertIn('additional distinct assignments',text.stdout)

    def test_public_native_error_retains_readable_unrun_views(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'invalid.sysml';model.write_text('package Broken { part invalid : MissingType; }\n')
            argv=[sys.executable,'-B',str(ROOT/'skills/develop-operational-scenarios/scripts/cse.py'),'question','answer',str(model)]
            raw=subprocess.run(argv,capture_output=True,text=True,timeout=90);r=json.loads(raw.stdout)
            self.assertEqual(raw.returncode,1);self.assertEqual(r['status'],'error')
            self.assertEqual(r['evaluation'],'not_run');self.assertFalse(r['alternatives']);self.assertIsNone(r['evaluated_hypothesis'])
            self.assertTrue(r['findings']);self.assertTrue(all('code' in f for f in r['findings']))
            for audience in ('beginner','expert'):
                text=subprocess.run(argv+['--format','text','--audience',audience],capture_output=True,text=True,timeout=90)
                self.assertEqual(text.returncode,1);self.assertNotIn('Traceback',text.stderr)
                self.assertEqual(text.stdout.strip(),render_text(r,audience=='expert'))
                self.assertIn('Hypothesis not evaluated',text.stdout)
                for finding in r['findings']:self.assertIn(finding['detail'],text.stdout)

    def test_minimal_start_fill_and_answer_without_overwriting(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            d=Path(d);starter=d/'starter.sysml';script=ROOT/'scripts/question.py'
            done=subprocess.run([sys.executable,'-B',str(script),'start',str(starter),'--text','Can the fallback meet the workload?'],capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr)
            r=inspect_inquiry(starter,{});self.assertEqual(r['native_status'],'pass');self.assertEqual(r['status'],'unknown')
            spec=d/'facts.json';spec.write_text(json.dumps(record()));model=d/'model.sysml'
            done=subprocess.run([sys.executable,'-B',str(script),'prepare',str(spec),str(model),'--package','BackupProcessing'],capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr)
            r=inspect_inquiry(model,{'SRC':ROOT/'examples/inquiry/software-brief.md'},'A_LARGER',['R_PRIMARY'])
            self.assertEqual(r['status'],'pass');self.assertEqual(r['behavior'],'not_run')
            done=subprocess.run([sys.executable,'-B',str(script),'prepare',str(spec),str(model),'--package','BackupProcessing'],capture_output=True,text=True)
            self.assertEqual(done.returncode,1)

    def test_actual_missing_stale_ambiguous_source_and_acquisition_errors(self):
        model=ROOT/'examples/inquiry/software.sysml'
        self.assertEqual(inspect_inquiry(model,{})['status'],'unknown')
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            d=Path(d);source=d/'source.md';source.write_text('A changed source.')
            r=inspect_inquiry(model,{'SRC':source});self.assertEqual(r['status'],'fail');self.assertEqual(r['evaluation'],'not_run')
            r=inspect_inquiry(model,{'SRC':d/'missing.md'});self.assertEqual(r['status'],'error')
            self.assertEqual(r['sources']['SRC']['actual_sha256'],None);self.assertEqual(r['input_paths']['sources']['SRC'],str(d/'missing.md'))
            self.assertIn('actual None',render_text(r,True))
            data=record();brief=(ROOT/'examples/inquiry/software-brief.md').read_text()
            duplicate=d/'duplicate.md';duplicate.write_text(brief+brief)
            data['sources']['SRC']['sha256']=sha256(duplicate.read_bytes()).hexdigest()
            duplicate_model=d/'duplicate.sysml';duplicate_model.write_text(draft_model(data,'BackupProcessing'))
            r=inspect_inquiry(duplicate_model,{'SRC':duplicate})
            self.assertEqual(r['status'],'fail');self.assertIn('exactly once',r['findings'][0]['detail'])
            r=inspect_inquiry(d/'missing.sysml',{});self.assertEqual(r['status'],'error');self.assertIsNone(r['model_sha256'])


if __name__=='__main__':unittest.main()
