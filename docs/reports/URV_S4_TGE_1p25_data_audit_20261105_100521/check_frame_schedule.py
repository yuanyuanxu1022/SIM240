"""Check existing frame schedule; no field or solver execution."""
from pathlib import Path
from fractions import Fraction
import csv
import json
import math

R=Path(__file__).resolve().parent
ROOT=R.parents[2]/'outputs/URV_S4_1p25_data_20261104_234955/01_raw_server/steady'
def kv(p):
    return dict(x.split('=',1) for x in p.read_text().splitlines() if x and not x.startswith('#'))
def rows(p):
    with p.open() as f:return list(csv.DictReader(f))
cfg=kv(ROOT/'run_config.txt');result=kv(ROOT/'result.txt')
stop=int(result['steps_completed']);schedule=rows(ROOT/'frame_schedule.csv');frames=rows(ROOT/'frame_index.csv')
requests=[float(v) for v in cfg['frame_tstar'].split(',')]
assert len(schedule)==len(requests)==11
expected={0,stop}
for request,item in zip(requests,schedule):
    target=math.ceil(Fraction(str(request))*6*(Fraction(cfg['h_nm'])/Fraction(cfg['dx_nm']))**2)
    assert float(item['requested_tstar'])==request and int(item['target_step'])==target
    assert int(item['reached'])==int(target<=stop)
    if target<=stop:expected.add(target)
assert [int(f['step']) for f in frames]==sorted(expected)
assert len(frames)==int(result['frames_written'])==10
dt=float(result['dt_s']);h=float(cfg['h_nm'])*1e-9;nu=float(cfg['nu_m2_s'])
for frame in frames:
    step=int(frame['step'])
    assert math.isclose(float(frame['time_s']),step*dt,rel_tol=1e-12,abs_tol=1e-24)
    assert math.isclose(float(frame['tstar']),nu*step*dt/h**2,rel_tol=1e-12,abs_tol=1e-14)
out=dict(PASS=True,scheduled_requests=11,actual_saved_frames=10,saved_steps=sorted(expected),
         stopped_before_future_scheduled_frames=True,final_physical_time_s=stop*dt,
         PVD_timestep_unit='lattice step, not seconds',solver_calls=0)
(R/'frame_schedule_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
