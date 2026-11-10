#!/usr/bin/env python3
"""Analyze only a completed frozen matrix; never launch solver or alter thresholds."""
import cmath
import csv
import json
import math
from pathlib import Path
import sys
from run_translation_suite import BASE, BATCH_ID, cases, sha

def unwrap(phases):
    result = [phases[0]]
    for previous, current in zip(phases, phases[1:]):
        difference = (current-previous+math.pi) % (2*math.pi)-math.pi
        if abs(difference) > .1:
            raise ValueError('phase increment too large; possible alias or corrupted series')
        result.append(result[-1]+difference)
    return result

def slope(values):
    center = (len(values)-1)/2
    mean = sum(values)/len(values)
    return sum((i-center)*(v-mean) for i,v in enumerate(values))/sum((i-center)**2 for i in range(len(values)))

def evaluate(rows, n, direction, variant):
    steps = round(n/(4*.008))
    if len(rows) != steps+1 or [int(r['step']) for r in rows] != list(range(steps+1)):
        raise ValueError('incomplete history')
    if any(not math.isfinite(float(v)) for r in rows for v in r.values()):
        raise ValueError('nonfinite history')
    if any(int(r['nodes']) != n**3 or int(r['finite']) != 1 for r in rows):
        raise ValueError('bad nodes or finite flags')
    sums = [float(r['phase_sum']) for r in rows]
    drifts = [(s-sums[0])/sums[0] for s in sums]
    if max(abs(d-float(r['relative_drift'])) for d,r in zip(drifts, rows)) > 1e-12:
        raise ValueError('stored versus recomputed drift mismatch')
    tests = {'conservation': max(map(abs,drifts)) <= 1e-9}
    components = {}
    for axis in 'xyz':
        z = [complex(float(r['re_'+axis]),float(r['im_'+axis])) for r in rows]
        if abs(z[0]) < 1e-4:
            raise ValueError('missing initial Fourier mode')
        angles = unwrap([cmath.phase(v) for v in z])
        moving = direction != 'zero' and axis in direction
        amplitude_error = abs(abs(z[-1])/abs(z[0])-1)
        item = dict(amplitude_relative_error=amplitude_error, phase_change=angles[-1]-angles[0])
        if moving:
            velocity = -.008 if direction.endswith('-') else .008
            measured = -slope(angles)*n/(2*math.pi)
            ratio = measured/velocity
            item.update(speed=measured, speed_ratio=ratio, speed_relative_error=abs(ratio-1))
            if variant == 'new':
                tests['speed_'+axis] = abs(ratio-1) <= (.05 if n==16 else .02)
                tests['amplitude_'+axis] = amplitude_error <= (.02 if n==16 else .01)
            else:
                tests['defect_reproduced_'+axis] = .45 <= ratio <= .55
        else:
            tests['stationary_'+axis] = abs(item['phase_change']) <= 1e-6
        components[axis] = item
    endpoint_l2 = float(rows[-1]['fluctuation_L2'])
    if direction == 'zero':
        tests['zero_velocity_L2'] = max(float(r['fluctuation_L2']) for r in rows) <= 1e-10
    elif variant == 'new':
        tests['endpoint_L2'] = endpoint_l2 <= (.10 if n==16 else .04)
    return dict(N=n,direction=direction,variant=variant,components=components,tests=tests,
                max_abs_phase_drift=max(map(abs,drifts)), final_L2=endpoint_l2,
                contract_pass=all(tests.values()),
                interpretation='corrected operator test' if variant=='new' else 'negative control; not physical advection PASS')

def main():
    evidence=BASE/'evidence'/BATCH_ID
    if (evidence/'exit_code.txt').read_text().strip() != '0':
        raise ValueError('batch independent exit is not zero')
    manifest=json.loads((evidence/'manifest.json').read_text())
    if not manifest.get('finished_utc') or len(manifest['cases'])!=36 or not manifest['source_hashes_unchanged']:
        raise ValueError('batch completion evidence missing')
    hashes=manifest['source_binding']['sha256']
    if any(not Path(p).is_file() or sha(p)!=h for p,h in hashes.items()):
        raise ValueError('source hash mismatch')
    results=[]
    for run_id,variant,n,direction in cases():
        if (evidence/run_id/'exit_code.txt').read_text().strip()!='0':
            raise ValueError(run_id+' nonzero independent exit')
        out=BASE/'output'/BATCH_ID/run_id
        cfg=json.loads((out/'config.json').read_text()); result=json.loads((out/'result.json').read_text())
        if (cfg['variant'],cfg['N'],cfg['direction']) != (variant,n,direction):
            raise ValueError('config mismatch')
        if not result['safe'] or result['completed_steps']!=round(n/(4*.008)):
            raise ValueError('run did not complete safely')
        rows=list(csv.DictReader((out/'history.csv').open()))
        # Verify 3D endpoint field count, coordinates, finite data and independent L2.
        for name,step in [('initial.csv',0),('final.csv',result['completed_steps'])]:
            field=list(csv.DictReader((out/name).open()))
            if len(field)!=n**3 or len({(r['x'],r['y'],r['z']) for r in field})!=n**3:
                raise ValueError('incomplete field')
            numerator=denominator=total=0.
            for r in field:
                values=[float(v) for v in r.values()]
                if not all(map(math.isfinite,values)):raise ValueError('nonfinite field')
                exact=.5+(.05/3)*sum(math.cos(2*math.pi*(float(r[a])-cfg['u'][i]*step)/n) for i,a in enumerate('xyz'))
                if abs(exact-float(r['exact_phi']))>1e-12:raise ValueError('exact field mismatch')
                val=float(r['phi']);total+=val;numerator+=(val-exact)**2;denominator+=(exact-.5)**2
            row=rows[step]
            if abs(total-float(row['phase_sum']))>1e-7 or abs(math.sqrt(numerator/denominator)-float(row['fluctuation_L2']))>1e-10:
                raise ValueError('field versus history mismatch')
        results.append(evaluate(rows,n,direction,variant))
    indexed={(r['variant'],r['N'],r['direction']):r for r in results}
    matrix_tests={}
    for n in (16,32):
        for sign in '+-':
            ratios=[indexed['new',n,a+sign]['components'][a]['speed_ratio'] for a in 'xyz']
            matrix_tests[f'axis_spread_n{n}_{sign}']=max(ratios)-min(ratios)<=.002
    for direction in ('x+','x-','y+','y-','z+','z-','xyz+','xyz-'):
        for axis in direction[:-1]:
            coarse=indexed['new',16,direction]['components'][axis]['speed_relative_error']
            fine=indexed['new',32,direction]['components'][axis]['speed_relative_error']
            matrix_tests[f'refinement_{direction}_{axis}']=fine<coarse or max(fine,coarse)<=1e-6
    passed=all(r['contract_pass'] for r in results) and all(matrix_tests.values())
    print(json.dumps(dict(batch_id=BATCH_ID,operator_contract_pass=passed,cases=results,
                         matrix_tests=matrix_tests,NUMERICAL_GATE='NOT_EVALUATED',
                         RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED'),indent=2))
    return 0 if passed else 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('ANALYSIS_BLOCKED: '+str(exc),file=sys.stderr);sys.exit(3)
