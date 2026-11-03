"""Hand-worked and independent time-grid expectations for the queue contract."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.queueing import analyze, LIMITS


def fixture():
    return json.loads((ROOT/'examples/queueing/service-pool.json').read_text())


def replay(record, details=True):
    return analyze(record, details=details)['checks']['Replay']


class QueueTests(unittest.TestCase):
    def test_hand_worked_serial_queue_and_idle_tail(self):
        result = analyze(fixture(), ['Replay','Stationary'], details=True)
        self.assertEqual(result['status'], 'pass', result)
        r = result['checks']['Replay']['result']
        self.assertEqual([x['start'] for x in r['trace']], ['0','3','5'])
        self.assertEqual(r['window_queue_area'], '5')
        self.assertEqual(r['window_busy_area'], '6')
        self.assertEqual(r['window_utilization'], '3/4')
        self.assertEqual(r['window_mean_queue'], '5/8')
        self.assertEqual(r['window_mean_in_system'], '11/8')
        self.assertEqual(r['supplied_cohort_mean_wait'], '5/3')
        self.assertEqual(result['observed_data_validation'], 'not_evaluated')
        self.assertEqual(result['acceptance'], 'not_evaluated')

    def test_pending_wait_is_integrated_through_horizon(self):
        r = fixture();q=r['checks']['Replay']
        q.update(window={'start':'0','end':'5'},jobs=[{'id':'A','arrival':'0','service':'10'}, {'id':'B','arrival':'1','service':'1'}])
        data=replay(r)['result']
        self.assertEqual((data['completed_jobs'],data['in_service_at_end'],data['waiting_at_end']), (0,1,1))
        self.assertEqual(data['window_mean_queue'],'4/5')
        self.assertEqual(data['window_utilization'],'1')
        self.assertIsNone(data['completed_jobs_mean_wait'])
        self.assertEqual(data['supplied_cohort_mean_wait'],'9/2')

    def test_nonzero_window_start_and_no_invented_initial_backlog(self):
        r=fixture();q=r['checks']['Replay']
        q.update(window={'start':'10','end':'20'},jobs=[{'id':'A','arrival':'12','service':'2'}])
        self.assertEqual(replay(r)['result']['window_utilization'],'1/5')
        q['assumptions']['empty_initial_system']['holds']=False
        self.assertEqual(replay(r)['status'],'unsupported')

    def test_two_servers_ties_and_zero_duration(self):
        r=fixture();q=r['checks']['Replay'];q['servers']=2
        q['jobs']=[{'id':name,'arrival':arrival,'service':service} for name,arrival,service in
                   [('A','0','3'),('B','0','2'),('C','1','1'),('D','2','2')]]
        data=replay(r)['result']
        self.assertEqual([x['start'] for x in data['trace']], ['0','0','2','3'])
        self.assertEqual(data['window_utilization'],'1/2')
        q.update(servers=1,jobs=[{'id':'Z','arrival':'0','service':'0'}, {'id':'A','arrival':'0','service':'1'}])
        data=replay(r)['result']
        self.assertEqual([x['id'] for x in data['trace']], ['Z','A'])
        self.assertEqual(data['peak_queue'],0)

    def test_horizon_boundary_completions_and_grants_are_explicit(self):
        r=fixture();q=r['checks']['Replay']
        q.update(window={'start':'0','end':'3'},jobs=[{'id':'A','arrival':'0','service':'3'}, {'id':'B','arrival':'1','service':'2'}])
        data=replay(r)['result']
        self.assertEqual((data['completed_jobs'],data['in_service_at_end'],data['waiting_at_end']), (1,1,0))
        self.assertEqual(data['window_queue_area'],'2')
        q['jobs'][1]['arrival']='3'
        self.assertEqual(replay(r)['status'],'error')

    def test_integer_replays_agree_with_independent_time_grid(self):
        for servers, durations in product((1,2), product((1,2,3),repeat=3)):
            arrivals=[0,0,1];pending=[];active=[];starts={};queue_area=busy_area=0
            for t in range(12):
                active=[x for x in active if x[1]>t]
                pending.extend(i for i,a in enumerate(arrivals) if a==t)
                while pending and len(active)<servers:
                    i=pending.pop(0); starts[i]=t;active.append((i,t+durations[i]))
                queue_area+=len(pending);busy_area+=len(active)
            r=fixture();q=r['checks']['Replay']
            q.update(servers=servers,window={'start':'0','end':'12'},jobs=[{'id':f'J{i}','arrival':str(a),'service':str(durations[i])} for i,a in enumerate(arrivals)])
            result=replay(r)['result']
            self.assertEqual([int(x['start']) for x in result['trace']], [starts[i] for i in range(3)])
            self.assertEqual(Fraction(result['window_queue_area']),queue_area)
            self.assertEqual(Fraction(result['window_busy_area']),busy_area)

    def test_mmc_matches_hand_derived_one_and_two_server_values(self):
        r=fixture();result=analyze(r)['checks']['Stationary']['result']
        self.assertEqual(result['probability_wait'],'1/3')
        self.assertEqual(result['probability_empty'],'1/3')
        self.assertEqual(result['mean_wait'],'1/6')
        self.assertEqual(result['mean_system_time'],'2/3')
        self.assertEqual(result['mean_in_system'],'4/3')
        r['checks']['Stationary'].update(servers=1,arrival_rate='2',service_rate='3')
        result=analyze(r)['checks']['Stationary']['result']
        self.assertEqual(result['mean_wait'],'2/3')
        self.assertEqual(result['mean_system_time'],'1')
        r['checks']['Stationary']['arrival_rate']='0'
        result=analyze(r)['checks']['Stationary']['result']
        self.assertEqual(result['probability_empty'],'1')
        self.assertEqual(result['mean_queue'],'0')

    def test_unstable_queue_and_false_or_unknown_assumptions_cannot_pass(self):
        r=fixture();r['checks']['Stationary']['arrival_rate']='4'
        self.assertEqual(analyze(r)['status'],'fail')
        for kind in ('Replay','Stationary'):
            for holds,basis,expected in ((False,'Explicit contrary fact','unsupported'),(None,'Unresolved','unknown'),(True,None,'unknown')):
                r=fixture();assumption=next(iter(r['checks'][kind]['assumptions'].values()))
                assumption.update(holds=holds,basis=basis)
                self.assertEqual(analyze(r)['checks'][kind]['status'],expected)

    def test_empty_and_missing_required_scope_never_pass(self):
        self.assertEqual(analyze(fixture(),[])['status'],'error')
        self.assertEqual(analyze(fixture(),['Replay','Replay'])['status'],'error')
        report=analyze(fixture(),['Removed'])
        self.assertEqual(report['status'],'fail')
        self.assertIn('Removed',report['checks'])
        r=fixture();r['checks']['Replay']['jobs']=[]
        self.assertEqual(analyze(r)['status'],'unknown')

    def test_compact_result_and_input_preservation(self):
        r=fixture();original=deepcopy(r)
        a=analyze(r);b=analyze(r,details=True)
        self.assertNotIn('trace',a['checks']['Replay']['result'])
        self.assertEqual(a['checks']['Replay']['result']['trace_sha256'],b['checks']['Replay']['result']['trace_sha256'])
        self.assertEqual(r,original)

    def test_schema_types_limits_and_unsupported_modes(self):
        changes=[lambda r:r['checks']['Replay'].update(servers=True),
                 lambda r:r['checks']['Replay']['jobs'][0].update(service=-1),
                 lambda r:r['checks']['Replay']['jobs'][0].update(service='-1'),
                 lambda r:r['checks']['Replay']['jobs'].append(deepcopy(r['checks']['Replay']['jobs'][0])),
                 lambda r:r['checks']['Replay'].update(servers=65),
                 lambda r:r['checks']['Replay'].update(jobs=[{'id':f'J{i}','arrival':'0','service':'1'} for i in range(513)]),
                 lambda r:r['checks']['Replay'].update(priority='not supported'),
                 lambda r:r['checks']['Stationary'].update(service_rate='0')]
        for change in changes:
            r=fixture();change(r);self.assertEqual(analyze(r)['status'],'error')
        r=fixture();r['checks']['Replay']['kind']='model_code'
        self.assertEqual(analyze(r)['status'],'unsupported')
        r=fixture();r['checks']['Stationary'].update(servers=64,arrival_rate='9'*79,service_rate='9'*80)
        self.assertEqual(analyze(r)['status'],'unknown')

    def test_cli_from_external_directory_strict_input_and_scope(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            p=Path(tmp)/'record.json';p.write_text(json.dumps(fixture()))
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/queueing.py'),str(p),*args],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(run('--required','Replay').returncode,0)
            self.assertEqual(run('--required','Missing').returncode,1)
            for value in ('{"version":1,"version":2}','{"value":NaN}','null','\udcff'):
                p.write_bytes(value.encode('utf-8',errors='surrogatepass'))
                self.assertEqual(run().returncode,2)
            p.write_bytes(b' '*(LIMITS['input_bytes']+1));self.assertEqual(run().returncode,2)


if __name__ == '__main__':
    unittest.main()
