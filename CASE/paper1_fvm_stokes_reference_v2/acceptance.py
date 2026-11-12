"""v2.1 shared operational rule; no solver/tool execution, no continuous error bound.

Foundation13 criteriaSatisfied uses solvei=0 and cmptMax(initialResidual).
Our fixed solver prints no Time separator. nNonOrthogonalCorrectors=0 yields
one v solve, or one Ux/(Uy)/Uz solve followed by one p solve per outer cycle.
This parser validates that sequence, not arbitrary last occurrences.
"""
import math
import re

RULE = dict(version='v2.1_stopping_fix', name='full_fields_v2_1',
            declared_residuals=dict(normal=dict(p=1e-10,U=1e-10,v=1e-10),
                                    tight=dict(p=1e-11,U=1e-11,v=1e-11)),
            branches=dict(groove=dict(controls=dict(P=['v'],T=['Ux','Uz','p'])),
                          flat_P=dict(controls=['v']),
                          flat_T=dict(controls=['Ux','p'],negligible_ratio=1e-9,
                                      flat_K_percent=0.1,flat_profile_percent=0.1)),
            iteration_cap_acceptance=True, residual_comparison='strict_less_than',
            parser='fixed_solver_first_solve_per_outer_cycle',
            zero_exception_scope='d=0 and direction=T only')


def same_residual(a, b):
    if not isinstance(a,(int,float)) or not isinstance(b,(int,float)):
        return False
    if not math.isfinite(a) or not math.isfinite(b) or min(a,b)<0:
        return False
    if a==0 or b==0:
        return a==b
    return abs(a-b)/max(a,b)<=1e-9


def steady_stop(text, meta, rule, exit_code=0, amplitudes=None, analytic=None):
    """Receipt and reader call independently on bound raw log/CSV.

    A normal cap exit may be accepted; unknown/truncated/abnormal exit cannot.
    Empty-direction Uy, when printed, must also meet its residual criterion.
    """
    issues=[]; blocks=[]; current=[]; native=False; native_time=None; malformed=False
    direction=meta['direction']; lead='v' if direction=='P' else 'Ux'
    for line in text.splitlines():
        match=re.search(r'Solving for (\w+), Initial residual = (\S+),',line)
        if match:
            name,value=match.groups()
            if native: malformed=True  # no solves after final native report
            if name==lead and current:
                blocks.append(current);current=[]
            try: number=float(value)
            except ValueError: number=math.nan
            current.append((name,number))
        report=re.fullmatch(r'SIMPLE solution converged in ([0-9.eE+-]+) iterations\s*',line.strip())
        if report:
            native=True; native_time=float(report.group(1))
    if current: blocks.append(current)
    if not blocks: issues.append('no complete outer iteration')
    for block in blocks:
        names=[n for n,_ in block]
        allowed=[['v']] if direction=='P' else [['Ux','Uz','p'],['Ux','Uy','Uz','p']]
        if names not in allowed: malformed=True
        if any(not math.isfinite(v) or v<0 for _,v in block): malformed=True
    if malformed: issues.append('invalid residual sequence/nonfinite/negative residual')
    complete_end=bool(text.strip().splitlines() and text.strip().splitlines()[-1]=='End')
    if not complete_end: issues.append('missing final End')
    trace=dict(blocks[-1]) if blocks else {}
    threshold=rule['declared_residuals']['tight' if meta['level']=='tight' else 'normal']['v' if direction=='P' else 'U']
    flat=meta.get('flat_zero_component_exception',False)
    if flat and not (meta['d_nm']==0 and direction=='T' and meta['level']=='flat'):
        issues.append('flat exception outside T flat')
    required=['v'] if direction=='P' else ['Ux','Uz','p']+(['Uy'] if 'Uy' in trace else [])
    if flat: required=[n for n in required if n!='Uz']
    for name in required:
        if name not in trace or not math.isfinite(trace[name]) or not 0<=trace[name]<threshold:
            issues.append('residual not met: '+name)
    # Even excluded Uz must be present, finite and nonnegative in a complete cycle.
    if flat:
        amps=amplitudes or {};ax=amps.get('Ux',math.nan);az=amps.get('Uz',math.nan)
        if not all(math.isfinite(v) for v in (ax,az)) or ax<=0 or az<0 or az/ax>rule['branches']['flat_T']['negligible_ratio']:
            issues.append('flat vertical amplitude ratio not met')
        for key,limit in [('flat_K_error_percent',rule['branches']['flat_T']['flat_K_percent']),('flat_profile_L2_percent',rule['branches']['flat_T']['flat_profile_percent'])]:
            val=(analytic or {}).get(key,math.nan)
            if not math.isfinite(val) or not 0<=val<=limit:
                issues.append('flat analytic condition not met: '+key)
    # Time::running uses time < endTime - 0.5*deltaT; fixed deltaT=1.
    cap=math.ceil(meta['end_time_cap']-meta.get('start_time',0)-0.5)
    final_time=meta.get('start_time',0)+len(blocks)
    if native and native_time!=final_time:
        issues.append('native convergence report time disagrees with cycle count')
    if exit_code==124: reason='wall_clock'
    elif exit_code!=0: reason='abnormal_exit'
    elif native: reason='native_convergence'  # wins if convergence and cap coincide
    elif len(blocks)==cap: reason='iteration_cap'
    else: reason='unclassified_normal_exit'
    if reason in ('wall_clock','abnormal_exit','unclassified_normal_exit'):
        issues.append('unacceptable stop: '+reason)
    if len(blocks)>cap: issues.append('iteration count exceeds frozen cap')
    return dict(criterion=rule['name'],actual_stop_reason=reason,
                post_hoc_acceptance='rejected' if issues else 'accepted',reasons=issues,
                components=trace,outer_iterations=len(blocks),final_time=final_time,threshold=threshold,
                log_reports_converged=native,ends_with_End=complete_end,
                flat_exception_used=flat)
