"""Software-only tests: synthetic records, fake clocks/processes; no native call."""
from pathlib import Path
import copy
import csv
import hashlib
import io
import json
import math
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CASE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(CASE/'analysis'),str(CASE/'scripts')]
import perf_contract as contract
import check_perf as checker
import run_perf as runner


def config(direction='P'):
    return dict(mode='steady',run_id='TEST_ONLY_PERF',output_directory='/test_only',
        direction=direction,dx_nm='1.25',h_nm='60.0',d_nm='80.0',w_nm='120',
        period_nm='240',Ly_nm='240',nu_m2_s='1e-06',acceleration_m_s2='100000',
        window_tstar='0.75',max_time_H_diffusion='8',
        frame_tstar='0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8')


def line(step,direction='P',**changes):
    p=contract.frozen_helpers()[1].exact_parameters(config(direction))
    mass=1000*p['nodes']*p['dx']**3
    r=dict.fromkeys(checker.HEADER,0.)
    r.update(step=step,J=1e-14,rho=1.,Mach=1e-10,mass=mass,time_s=step*p['dt'],
        corrected_mass=mass,finite=1.,window_rel_std=-1.,window_rel_span=-1.,window_cross_abs_max=-1.)
    r['Jy' if direction=='P' else 'Jx']=r['J'];r.update(changes)
    return (','.join(str(r[k]) for k in checker.HEADER)+'\n').encode()


def diagnostic(last=2100,direction='P'):
    d=checker.Diagnostics(config(direction))
    d.feed((','.join(checker.HEADER)+'\n').encode())
    for step in range(last+1):d.feed(line(step,direction))
    return d


def samples_for(diag,steps=(0,300,900,1100,1700,2100)):
    result=[]
    by_step={v[0]:(k,v[1]) for k,v in diag.endpoints.items()}
    for i,step in enumerate(steps):
        offset,digest=by_step[step]
        result.append(dict(sample=i,monotonic=float(i),alive=1,last_complete_step=step,
            complete_bytes=offset,complete_prefix_sha256=digest,RSS_bytes=1024,
            MemAvailable_bytes=16*1024**3,output_bytes=1000,disk_free_bytes=200*1024**3))
    return result


def receipt(samples):
    end=float(samples[-1]['monotonic'])
    return dict(inputs_before_sha256={'input':'same'},inputs_after_sha256={'input':'same'},
        process_start_monotonic=0.,stop_decision_monotonic=end,process_exit_monotonic=end+.01,
        stop_reason='target_observed',independent_process_exit_code=-15,
        unexpected_native_final_output=False,signals_sent=[dict(signal='SIGTERM',monotonic=end)],
        timed_out=False,solver_wall_cap_seconds=1800,observed_target_step=2048,SIGTERM_grace_seconds=10)


class Clock:
    def __init__(self):self.t=0.
    def __call__(self):return self.t
    def sleep(self,n):self.t+=n


class Child:
    pid=12345
    def __init__(self,clock,term_ignored=False,exit_at=None):
        self.clock=clock;self.returncode=None;self.term_ignored=term_ignored;self.exit_at=exit_at;self.sent=[]
    def poll(self):
        if self.exit_at is not None and self.clock.t>=self.exit_at:self.returncode=0
        return self.returncode
    def wait(self,timeout=None):
        if self.returncode is None:
            self.clock.t+=timeout or 0
            raise subprocess.TimeoutExpired('FAKE_CHILD_ONLY',timeout)
        return self.returncode
    def killpg(self,pid,sig):
        self.sent.append(sig)
        if sig==signal.SIGKILL or not self.term_ignored:self.returncode=-sig


class FakeDiagnostic:
    def __init__(self,clock,speed=512,error_at=None):
        self.clock=clock;self.speed=speed;self.error_at=error_at
        self.last=-1;self.complete_bytes=0;self.digest=hashlib.sha256()
    def read_new(self,path):
        if self.error_at is not None and self.clock.t>=self.error_at:raise ValueError('injected bad row')
        self.last=int(self.clock.t*self.speed);self.complete_bytes=self.last


METRICS=dict(RSS_bytes=1024,MemAvailable_bytes=16*1024**3,output_bytes=0,disk_free_bytes=200*1024**3)


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.d=checker.Diagnostics(config())
        self.d.feed((','.join(checker.HEADER)+'\n').encode())
    def test_partial_line_preserved_until_newline(self):
        row=line(0);self.d.feed(row[:-1]);self.assertEqual(self.d.last,-1)
        self.assertEqual(self.d.summary()['incomplete_tail_bytes'],len(row)-1)
        self.d.feed(b'\n');self.assertEqual(self.d.last,0)
    def test_missing_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError,'step'):self.d.feed(line(1))
    def test_skipped_or_duplicate_step_rejected(self):
        self.d.feed(line(0))
        for n in (0,2):
            with self.assertRaises(ValueError):self.d.feed(line(n))
    def test_nonfinite_and_flag_rejected(self):
        for changes in [dict(rho=float('nan')),dict(finite=0),dict(Mach=float('inf'))]:
            d=checker.Diagnostics(config());d.feed((','.join(checker.HEADER)+'\n').encode())
            with self.assertRaises(ValueError):d.feed(line(0,**changes))
    def test_mass_units_rejected(self):
        with self.assertRaisesRegex(ValueError,'mass units'):self.d.feed(line(0,corrected_mass=1.))
    def test_ledger_corruption_rejected(self):
        self.d.feed(line(0))
        with self.assertRaisesRegex(ValueError,'recomputation'):self.d.feed(line(1,delta_mass_error=1e-5))
    def test_density_guard_cannot_be_erased_by_later_good_row(self):
        self.d.feed(line(0))
        with self.assertRaisesRegex(ValueError,'density'):self.d.feed(line(1,max_density_deviation=1e-5))
        self.assertEqual(self.d.last,0)
    def test_Mach_and_Re_guards(self):
        for value in (.05, .001):
            d=checker.Diagnostics(config());d.feed((','.join(checker.HEADER)+'\n').encode())
            with self.assertRaises(ValueError):d.feed(line(0,Mach=value))
    def test_corrected_mass_guard(self):
        self.d.feed(line(0));mass=self.d.first['corrected_mass']
        new=mass*(1+1e-9);error=(new-mass)/mass
        with self.assertRaisesRegex(ValueError,'corrected mass safety'):
            self.d.feed(line(1,corrected_mass=new,corrected_mass_error=error,
                             density_delta=self.d.p['nodes']*error,delta_mass_error=error,mass_ledger_agreement=0))
    def test_direction_projection(self):
        with self.assertRaisesRegex(ValueError,'directional'):self.d.feed(line(0,Jx=1e-14,Jy=0))
        t=diagnostic(2,'T');self.assertEqual(t.last,2)
    def test_window_sentinels_valid(self):
        self.d.feed(line(0));self.assertEqual(self.d.last,0)
    def test_premature_window_metrics_rejected(self):
        with self.assertRaisesRegex(ValueError,'premature'):self.d.feed(line(0,window_rel_std=0))
    def test_diagnostic_truncation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'diagnostics.csv';p.write_bytes((','.join(checker.HEADER)+'\n').encode()+line(0))
            self.d.read_new(p);p.write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'truncated'):self.d.read_new(p)


class IntervalAndOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.diag=diagnostic()
    def setUp(self):self.samples=samples_for(self.diag);self.receipt=receipt(self.samples)
    def test_sufficient_not_scientific_pass(self):
        r=checker.outcome(self.receipt,self.samples,self.diag)
        self.assertEqual(r['PERF_OUTCOME'],checker.SUFFICIENT)
        self.assertFalse(r['RESULT_PASS']);self.assertEqual(r['NUMERICAL_GATE'],'NOT_EVALUATED')
        self.assertEqual(r['throughput_intervals'][0]['start_step'],300)
        self.assertEqual(r['throughput_intervals'][0]['delta_steps'],600)
    def test_actual_start_plus_512_not_nominal_end(self):
        s=[dict(sample=i,monotonic=float(i),last_complete_step=v) for i,v in enumerate([700,800,1024,1400,1600,2100])]
        w=checker.intervals(s);self.assertEqual(w[0]['end_step'],1400)
    def test_overlap_allowed(self):
        s=[dict(sample=i,monotonic=float(i),last_complete_step=v) for i,v in enumerate([1100,1700])]
        w=checker.intervals(s);self.assertEqual(w[0]['start_sample'],w[1]['start_sample'])
    def test_burst_at_stop_insufficient(self):
        s=samples_for(self.diag,[0,2100]);r=checker.outcome(receipt(s),s,self.diag)
        self.assertEqual(r['PERF_OUTCOME'],checker.INSUFFICIENT)
    def test_post_exit_rows_cannot_create_intervals(self):
        s=samples_for(self.diag,[0,300]);r=receipt(s);r.update(stop_reason='wall_timeout',timed_out=True,stop_decision_monotonic=1800.)
        r.update(signals_sent=[dict(signal='SIGTERM',monotonic=1800.)],process_exit_monotonic=1800.01)
        self.assertEqual(checker.outcome(r,s,self.diag)['PERF_OUTCOME'],checker.INSUFFICIENT)
    def test_changed_prefix_rejected(self):
        self.samples[1]['complete_prefix_sha256']='0'*64
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_excessive_sample_rate_rejected(self):
        self.samples[1]['monotonic']=.5
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_resource_violation_rejected(self):
        for key,value in [('MemAvailable_bytes',1),('RSS_bytes',9*1024**3),('output_bytes',5*1024**3),('disk_free_bytes',1)]:
            s=copy.deepcopy(self.samples);s[1][key]=value
            self.assertEqual(checker.outcome(self.receipt,s,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_normal_exit_is_HOLD(self):
        self.receipt['independent_process_exit_code']=0
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_native_final_output_is_HOLD(self):
        self.receipt['unexpected_native_final_output']=True
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_source_drift_rejected(self):
        self.receipt['inputs_after_sha256']={'input':'changed'}
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_target_delayed_or_wall_flag_erased_rejected(self):
        self.receipt['timed_out']=True
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_faked_KILL_without_grace_is_rejected(self):
        self.receipt['signals_sent'].append(dict(signal='SIGKILL',monotonic=6.))
        self.receipt['process_exit_monotonic']=6.01
        self.receipt['independent_process_exit_code']=-9
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_backward_progress_is_rejected(self):
        self.samples[2],self.samples[3]=self.samples[3],self.samples[2]
        for i,s in enumerate(self.samples):s.update(sample=i,monotonic=float(i))
        self.assertEqual(checker.outcome(self.receipt,self.samples,self.diag)['PERF_OUTCOME'],checker.ABORTED)
    def test_no_rows_at_wall_is_insufficient(self):
        d=checker.Diagnostics(config());s=[dict(sample=0,monotonic=0.,alive=1,last_complete_step=-1,
            complete_bytes=0,complete_prefix_sha256=hashlib.sha256(b'').hexdigest(),**METRICS)]
        r=receipt(s);r.update(stop_reason='wall_timeout',timed_out=True,stop_decision_monotonic=1800.,
            process_exit_monotonic=1800.01,signals_sent=[dict(signal='SIGTERM',monotonic=1800.)])
        self.assertEqual(checker.outcome(r,s,d)['PERF_OUTCOME'],checker.INSUFFICIENT)


class MonitorTests(unittest.TestCase):
    def observe(self,speed=512,ignored=False,exit_at=None,error_at=None,cancel_time=None,bad_resource=None):
        clock=Clock();child=Child(clock,ignored,exit_at);diag=FakeDiagnostic(clock,speed,error_at)
        out=io.StringIO();writer=csv.DictWriter(out,fieldnames=checker.SAMPLE_HEADER);writer.writeheader()
        def metrics(*args):return dict(METRICS,**(bad_resource or {}))
        result,samples=runner.monitor(child,Path('/FAKE_TEST_ONLY'),diag,writer,
            lambda:cancel_time is not None and clock.t>=cancel_time,clock,clock.sleep,metrics,child.killpg)
        return result,samples,child
    def test_target_stop(self):
        r,s,c=self.observe();self.assertEqual(r['stop_reason'],'target_observed')
        self.assertEqual(r['independent_process_exit_code'],-15);self.assertEqual(s[-1]['last_complete_step'],2048)
    def test_wall_stop_without_new_rows(self):
        r,s,c=self.observe(speed=0);self.assertEqual(r['stop_reason'],'wall_timeout')
        self.assertEqual(r['stop_decision_monotonic'],1800);self.assertTrue(r['timed_out'])
    def test_TERM_KILL_grace(self):
        r,s,c=self.observe(ignored=True);self.assertEqual(c.sent,[signal.SIGTERM,signal.SIGKILL])
        self.assertEqual(r['signals_sent'][1]['monotonic']-r['signals_sent'][0]['monotonic'],10)
        self.assertEqual(r['independent_process_exit_code'],-9)
    def test_user_stop(self):
        r,s,c=self.observe(cancel_time=2);self.assertEqual(r['stop_reason'],'user_stop')
    def test_unexpected_exit(self):
        r,s,c=self.observe(exit_at=2);self.assertEqual(r['stop_reason'],'unexpected_exit');self.assertEqual(c.sent,[])
    def test_bad_row_stops(self):
        r,s,c=self.observe(error_at=2);self.assertEqual(r['stop_reason'],'safety_or_resource_error')
    def test_bad_resource_stops(self):
        r,s,c=self.observe(bad_resource={'MemAvailable_bytes':1});self.assertEqual(r['stop_reason'],'safety_or_resource_error')
    def test_fixed_resource_boundaries(self):
        runner.resource_guard(METRICS,True)
        for key,value in [('disk_free_bytes',99*1024**3),('MemAvailable_bytes',11*1024**3)]:
            with self.assertRaises(ValueError):runner.resource_guard(dict(METRICS,**{key:value}),True)


class AuthorityAndIsolationTests(unittest.TestCase):
    def test_preparation_rejected_before_Popen_or_marker(self):
        data=dict(kind=contract.PREP,performance_time_stepping_authorized=False)
        with patch.object(runner,'verify',return_value=data),patch.object(runner.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(ValueError,'cannot launch'):runner.execute('FAKE','0'*64,data)
            popen.assert_not_called()
        self.assertFalse((CASE/'performance_attempt.json').exists())
    def test_formal_or_zero_authority_rejected(self):
        for kind in ['AUTHORIZED_EXECUTION_LAUNCH_RELEASE','AUTHORIZED_ZERO_STEP_RELEASE',contract.PREP]:
            with self.assertRaises(ValueError):contract.authorize(dict(kind=kind,performance_time_stepping_authorized=True))
    def test_external_hash_required(self):
        with self.assertRaises(ValueError):contract.verify(CASE/'README.md','0'*64)
    def test_pristine_and_symlink_ancestors(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);run=root/'run';run.mkdir();(run/'run_config.txt').touch();(run/'run_manifest.txt').touch()
            contract.pristine([dict(output_directory=str(run))]);(run/'old.log').touch()
            with self.assertRaises(ValueError):contract.pristine([dict(output_directory=str(run))])
            (root/'alias').symlink_to(run,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink'):contract.no_symlinks(root/'alias'/'file')
    def test_raw_hash_detects_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'run.log';p.write_text('first');old=checker.raw_hashes(Path(td));p.write_text('changed')
            self.assertNotEqual(old,checker.raw_hashes(Path(td)))
    def test_independent_checker_has_no_controller_import(self):
        import ast
        tree=ast.parse((CASE/'analysis/check_perf.py').read_text())
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertNotIn('run_perf',modules)
    def test_frozen_B_live_readonly(self):
        b=contract.verify_B();self.assertEqual(len(b['inputs_sha256']),1816)
        self.assertEqual(contract.sha(b['provenance']['native_binary']),contract.ELF_SHA)
    def test_materialized_pair_config_whitelist(self):
        b=contract.verify_B();plan=contract.load(CASE/'evidence/identity_plan.json')
        data=dict(prepared_benchmark_runs=copy.deepcopy(plan['prepared_benchmark_runs']),inputs_sha256={})
        for r in data['prepared_benchmark_runs']:
            for p in [Path(r['run_config_path']),Path(r['output_directory'])/'run_manifest.txt']:
                data['inputs_sha256'][str(p)]=contract.sha(p)
        contract.records_check(data,b)
        for field,value in [('source_planned_case_id','URV1_U_REG_P_dx5_a100000'),
                            ('output_directory',str(contract.OLD/'runs/forbidden')),
                            ('run_id','URV_S2_P_dx1p25_reuse_v1_20261102_01')]:
            wrong=copy.deepcopy(data);wrong['prepared_benchmark_runs'][0][field]=value
            with self.assertRaises(ValueError):contract.records_check(wrong,b)
        extra=copy.deepcopy(data);extra['prepared_benchmark_runs'].append(extra['prepared_benchmark_runs'][0])
        with self.assertRaises(ValueError):contract.records_check(extra,b)
        # No real config is edited: compare a mocked parsed mapping instead.
        original=contract.kv
        def altered(p):
            d=original(p)
            if str(p)==data['prepared_benchmark_runs'][0]['run_config_path']:d['window_tstar']='0.5'
            return d
        with patch.object(contract,'kv',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'config changed'):contract.records_check(data,b)
    def test_both_prepared_dirs_pristine(self):
        plan=contract.load(CASE/'evidence/identity_plan.json')
        contract.pristine(plan['prepared_benchmark_runs'])
    def test_default_main_is_readonly(self):
        doc=dict(kind=contract.PREP,performance_time_stepping_authorized=False,prepared_benchmark_run_ids=contract.IDS)
        with (patch.object(runner,'inspect',return_value=doc),patch.object(runner,'execute') as execute,
             patch.object(sys,'argv',['run_perf.py','--release','FAKE','--expected-sha256','0'*64]),
             patch('sys.stdout',new_callable=io.StringIO)):
            self.assertEqual(runner.main(),0);execute.assert_not_called()
    def test_failed_P_blocks_T_and_consumes_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);records=[]
            for d in ('P','T'):
                run=root/d;run.mkdir();cfg=config(d)
                (run/'run_config.txt').write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
                (run/'run_manifest.txt').touch()
                records.append(dict(run_id='TEST_ONLY_PERF_'+d,output_directory=str(run),run_config_path=str(run/'run_config.txt')))
            src=root/'input';src.write_text('source')
            data=dict(prepared_benchmark_runs=records,inputs_sha256={str(src):contract.sha(src)},native_binary='/NEVER_EXECUTED')
            clock=Clock();child=Child(clock);child.returncode=-15
            fake_process=dict(stop_reason='target_observed')
            with patch.object(runner,'CASE',root),patch.object(runner,'verify',return_value=data),\
                 patch.object(runner,'authorize',return_value=data),patch.object(runner,'environment',return_value={k:'1' for k in
                     ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']}),\
                 patch.object(runner,'resources',return_value=METRICS),patch.object(runner.subprocess,'Popen',return_value=child) as popen,\
                 patch.object(runner,'monitor',return_value=(fake_process,[])),\
                 patch.object(runner,'check',return_value={'PERF_OUTCOME':checker.INSUFFICIENT}):
                result=runner.execute('TEST_ONLY','0'*64,data)
                self.assertEqual(len(result),1);self.assertEqual(popen.call_count,1)
                self.assertEqual(sorted(p.name for p in Path(records[1]['output_directory']).iterdir()),
                                 ['run_config.txt','run_manifest.txt'])
                with self.assertRaises(ValueError):runner.execute('TEST_ONLY','0'*64,data)
    def test_wrong_stage_and_extra_formal_authority_rejected(self):
        for doc in [dict(protocol_id='URV-v1',stage='S2_REG_GRID',purpose=contract.PURPOSE),
                    dict(protocol_id='S2-MIP-v1-PERF',stage='S2_REG_GRID',purpose=contract.PURPOSE)]:
            with self.assertRaisesRegex(ValueError,'performance-only'):contract.validate_document(doc,{})
    def test_checker_end_to_end_synthetic_raw_and_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td);cfg=config()
            (run/'run_config.txt').write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
            raw=(','.join(checker.HEADER)+'\n').encode()+b''.join(line(n) for n in range(2101))+b'2101,PARTIAL'
            (run/'diagnostics.csv').write_bytes(raw)
            d=checker.Diagnostics(cfg);d.read_new(run/'diagnostics.csv');samples=samples_for(d)
            with (run/'performance_observations.csv').open('w') as f:
                writer=csv.DictWriter(f,fieldnames=checker.SAMPLE_HEADER);writer.writeheader();writer.writerows(samples)
            r=receipt(samples);r.update(run_id='TEST_ONLY_PERF',release_sha256='0'*64,purpose=contract.PURPOSE,
                formal_simulation_authorized=False,inputs_before_sha256={},inputs_after_sha256={},
                raw_output_sha256=checker.raw_hashes(run),diagnostics_after_exit=d.summary(),
                exact_collide_and_stream_calls=None,missing_native_outputs=['result.txt','execution_audit.txt','frame_index.csv'])
            contract.save(run/'performance_receipt.json',r)
            result=checker.check({'inputs_sha256':{}},dict(output_directory=str(run),run_id='TEST_ONLY_PERF',
                run_config_path=str(run/'run_config.txt')),'0'*64)
            self.assertEqual(result['PERF_OUTCOME'],checker.SUFFICIENT)
            self.assertEqual(result['diagnostics']['incomplete_tail_bytes'],len(b'2101,PARTIAL'))
            self.assertIsNone(result['exact_collide_and_stream_calls'])
            (run/'diagnostics.csv').write_bytes(raw+b'CHANGED')
            with self.assertRaisesRegex(ValueError,'output drift'):checker.check({'inputs_sha256':{}},
                dict(output_directory=str(run),run_id='TEST_ONLY_PERF',run_config_path=str(run/'run_config.txt')),'0'*64)


if __name__=='__main__':
    # A real Popen is forbidden throughout this software-only suite.
    with patch('subprocess.Popen',side_effect=AssertionError('NATIVE/EXTERNAL PROCESS FORBIDDEN')):
        unittest.main(verbosity=2)
