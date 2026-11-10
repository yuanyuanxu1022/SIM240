#!/usr/bin/env python3
"""Closed-form expectations for proposed cases, not a PDE solver or flow run."""
import csv
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path

OUT=Path(__file__).resolve().parent
L=24e-6; W=48e-6; AREA=L*W; MU=.001; DEPTH=100e-9


def coefficients(h):
    # Independent scalar evaluation of the published rounded V2, no fitted code import.
    a,b=h**3,(h+DEPTH)**3
    kp=(a+b)/24/(1+1.7685*(100/120)**1.6331)
    kt=(a*b)/(6*(a+b))/(1+.4900*(100/120)**.6990)
    return kp,kt


def high_precision_kt(h):
    with localcontext() as ctx:
        ctx.prec=60
        g=Decimal(str(h));d=Decimal('1e-7');a=g**3;b=(g+d)**3
        return float(a*b/(6*(a+b))/(1+Decimal('.4900')*(Decimal(5)/6)**Decimal('.6990')))


def case(case_id,h,previous,dt,nx,ny):
    H=h+50e-9; oldH=previous+50e-9
    rate=(h-previous)/dt; closing=-rate
    kp,k=coefficients(h);assert math.isclose(k,high_precision_kt(h),rel_tol=2e-14)
    j_pressure=k*24/(MU*L)
    q_pressure=W*j_pressure
    q_low=-q_pressure+closing*AREA/2
    q_high=q_pressure+closing*AREA/2
    q_net=closing*AREA;storage=rate*AREA
    volume_new=H*AREA;volume_old=oldH*AREA
    def p(x):return 24*(1-x/L)+MU*closing*x*(L-x)/(2*k)
    def j(x):return j_pressure+closing*(x-L/2)
    # Verify endpoints and differential identities by analytic coefficients.
    assert p(0)==24 and p(L)==0
    assert math.isclose(q_low+q_high,q_net,rel_tol=1e-13,abs_tol=1e-32)
    assert math.isclose(volume_new-volume_old,dt*storage,rel_tol=1e-13,abs_tol=1e-32)
    peak_x=L/2-24*k/(MU*closing*L) if closing else 0
    peak_x=max(0,min(L,peak_x))
    # This is a CONTINUUM target and a boundary sampling diagnostic, not a prediction
    # of the current trace-split discrete solution or its convergence outcome.
    per_edge_sampling_error=W*closing*(L/nx)/2
    result={'input_id':case_id,'status':'ANALYTIC_EXPECTATION_NOT_RUN',
      'h_current_m':h,'h_previous_m':previous,'gapDeltaT_s':dt,'H_current_m':H,
      'H_previous_m':oldH,'Hdot_m_s':rate,'closing_speed_m_s':closing,
      'Nx':nx,'Ny':ny,'Nz':1,'cells':nx*ny,'b0_m':125e-9,
      'K_parallel_m3':kp,'K_xx_perpendicular_m3':k,'Q_pressure_m3_s':q_pressure,
      'Q_xLow_outward_m3_s':q_low,'Q_xHigh_outward_m3_s':q_high,
      'Q_net_outward_m3_s':q_net,'storage_rate_m3_s':storage,
      'volume_previous_m3':volume_old,'volume_current_m3':volume_new,
      'volume_change_m3':volume_new-volume_old,'center_pressure_Pa':p(L/2),
      'peak_pressure_Pa':p(peak_x),'peak_x_m':peak_x,
      'normalization_pressure_Pa':max(24,abs(p(peak_x))),
      'normalization_J_m2_s':max(abs(j(0)),abs(j(L))),
      'normalization_Q_m3_s':max(q_pressure,abs(q_net),abs(q_low),abs(q_high)),
      'zeroGradient_exact_field_edge_flux_sampling_difference_abs_m3_s':abs(per_edge_sampling_error),
      'zeroGradient_exact_field_boundary_only_difference_over_abs_boundary_Q':
         (2*abs(per_edge_sampling_error)/(abs(q_low)+abs(q_high))) if closing else 0,
      'formal_solver_calls':0}
    profile=[{'input_id':case_id,'i':i,'x_m':(i+.5)*L/nx,
              'pressure_continuum_Pa':p((i+.5)*L/nx),
              'Jx_continuum_m2_s':j((i+.5)*L/nx),
              'Ux_continuum_m_s':j((i+.5)*L/nx)/H} for i in range(nx)]
    return result,profile


def main():
    specs=[('GAP_ACCEPT_A',75e-9,75e-9,.25,16,32),
           ('GAP_ACCEPT_B',50e-9,50e-9,.25,16,32),
           ('GAP_ACCEPT_C',75e-9,77e-9,.25,32,64)]
    cases=[];profiles=[]
    for args in specs:
        c,p=case(*args);cases.append(c);profiles+=p
    (OUT/'analytic_expected.json').write_text(json.dumps({'status':'PROPOSED_INPUTS_ANALYTIC_ONLY_NOT_SIMULATION',
        'formula':'p=24*(1-x/L)+mu*V*x*(L-x)/(2*Kxx); Jx=Kxx*24/(mu*L)+V*(x-L/2)',
        'cases':cases,'solver_calls':0,'model_accuracy_claim':False},indent=2)+'\n')
    for filename,rows in [('CASE_INPUTS_AND_TARGETS.csv',cases),('ANALYTIC_PROFILES.csv',profiles)]:
        with (OUT/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps([{k:c[k] for k in ('input_id','cells','H_current_m','center_pressure_Pa',
          'Q_xLow_outward_m3_s','Q_xHigh_outward_m3_s','Q_net_outward_m3_s',
          'zeroGradient_exact_field_boundary_only_difference_over_abs_boundary_Q')} for c in cases],indent=2))


if __name__=='__main__': main()
