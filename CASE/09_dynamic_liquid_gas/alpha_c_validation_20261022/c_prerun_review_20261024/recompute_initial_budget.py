"""Read existing zero-step C fields and compute scalar budget predictions only.

No solver import, collision, streaming, field evolution or subprocess invocation.
The predictions use the exact global CH moment identity, not an evolved state.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

A=Path(__file__).resolve().parent
B=A.parent
V=np.array([[0,0,0],[-1,0,0],[0,-1,0],[0,0,-1],[-1,-1,0],[-1,1,0],[-1,0,-1],[-1,0,1],[0,-1,-1],[0,-1,1],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,-1,0],[1,0,1],[1,0,-1],[0,1,1],[0,1,-1]])
W=np.array([1/3]+[1/18]*3+[1/36]*6+[1/18]*3+[1/36]*6)
N=64;COUNT=N**3
inputs={}

def read(path):
    inputs[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    return path.read_bytes()

def jread(path):return json.loads(read(path))
def total(a):return np.sum(a,dtype=np.longdouble)
def maximum(a):return float(np.max(np.abs(a)))
def grad(p):
    g=np.zeros((3,)+p.shape)
    for c,w in zip(V,W):
        for k in range(3):
            if c[k]:g[k]+=3*w*c[k]*np.roll(p,tuple(-c),axis=(0,1,2))
    return g
def lap(p):
    ans=np.zeros_like(p)
    for c,w in zip(V,W):ans+=6*w*(np.roll(p,tuple(-c),axis=(0,1,2))-p)
    return ans

def main():
    protocol=jread(B/'protocol.json');old=jread(B/'evidence/c_initial_budget_forecast.json')
    reference={x['case_id']:x for x in old};out=[]
    for case in protocol['stages']['c']:
        ev=B/'evidence'/('init_'+case['id']+'_v1');base=ev/'data'
        cfg=jread(base/'config.json');res=jread(base/'result.json');schema=jread(base/'frame_schema.json');manifest=jread(ev/'manifest.json')
        assert int(read(ev/'exit_code.txt'))==manifest['independent_exit_code']==0
        assert manifest['case_id']==case['id'] and manifest['command'][-1]=='--initialize-only'
        assert all(res[k]==0 for k in ('completed_steps','requested_steps','NS_collide_calls','CH_collide_calls'))
        assert cfg['case_id']==case['id'] and cfg['N']==N and cfg['nominal_steps']==64 and cfg['steps']==0
        assert cfg['rhos']==case['rhos'] and cfg['taus']==case['taus'] and cfg['alpha']==cfg['tau_CH']==1 and cfg['MPI_ranks']==1
        assert schema['shape']==[N,N,N,16] and schema['dtype']=='<f8' and schema['order']=='C'
        raw=gzip.decompress(read(base/'frames/step_0.bin.gz'));assert len(raw)==COUNT*16*8
        cube=np.frombuffer(raw,dtype='<f8').reshape(N,N,N,16);assert np.isfinite(cube).all()
        f={name:cube[...,k] for k,name in enumerate(schema['columns'])}
        p=f['phi'];rho=f['rho'];mu=f['mu'];u=np.array([f['u'+axis] for axis in 'xyz']);force=np.array([f['F'+axis] for axis in 'xyz']);rawj=np.array([f['j'+axis] for axis in 'xyz'])
        gp=grad(p);gm=grad(mu);div=sum(grad(u[k])[k] for k in range(3));S=np.sum(u*gp,axis=0)
        mu_exact=np.zeros_like(p) if cfg['constant_mu_zero'] else 4*cfg['beta']*p*(p-1)*(p-.5)-cfg['kappa']*lap(p)
        x,y,z=np.indices((N,)*3);half=cfg['a0_nm']/2.5+(np.sin(2*np.pi*y/N+.37)*np.cos(2*np.pi*z/N+.19)+.25*np.cos(4*np.pi*y/N+.23))/2.5
        prescribed=.5*(1+np.tanh(2*(abs(x-N/2)-half)/4))
        errors={'profile':maximum(p-prescribed),'mean_phi':float(abs(total(p)/COUNT-.5)),
                'rho':maximum(rho-(1+(cfg['rhos'][1]-1)*p)),'tau':maximum(f['tau']-(1+.25*p)),
                'mu':maximum(mu-mu_exact),'force':maximum(force+p*gm),
                'source':maximum(f['source']-S),'source_old':maximum(f['source_old']-S),
                'startup_AB':maximum(f['source']-f['source_old']),
                'raw_j':maximum(rawj),'half_force_velocity':maximum(u-force/(2*rho)),
                'periodic_gradient_sum':max(float(abs(total(gp[k]))/COUNT) for k in range(3)),
                'summation_by_parts_per_node':float(abs(total(S)+total(p*div))/COUNT)}
        Q=total(p);mass=total(rho);source_sum=total(S)
        # Scalar predictions only, no phi1/rho1 or populations are constructed.
        dq=-source_sum;dm=(cfg['rhos'][1]-1)*dq
        forecast=float(dq/Q);massrel=float(dm/mass)
        history=list(csv.DictReader(read(base/'history.csv').decode().splitlines()));assert len(history)==1 and int(history[0]['step'])==0
        errors['history_Q_per_node']=float(abs(Q-np.longdouble(history[0]['phase_sum']))/COUNT)
        errors['history_mass_per_node']=float(abs(mass-np.longdouble(history[0]['mass_sum']))/COUNT)
        assert all(v<=1e-12 for v in errors.values()),(case['id'],errors)
        assert abs(forecast-reference[case['id']]['predicted_first_step_phase_relative_change'])<1e-15
        row={'case_id':case['id'],'Q0':float(Q),'M0':float(mass),'source_sum':float(source_sum),'phi_div_u_sum':float(total(p*div)),
             'predicted_delta_Q':float(dq),'predicted_delta_Q_over_Q0':forecast,
             'predicted_delta_mass':float(dm),'predicted_delta_mass_over_M0':massrel,
             'predicted_Q_budget_ratio':abs(forecast)/protocol['thresholds']['phase_relative_drift'],
             'predicted_mass_budget_ratio':abs(massrel)/protocol['thresholds']['mass_relative_drift'],
             'predicted_liquid_relative_change':float(-dq/total(1-p)),
             'phase_within_budget_prediction':bool(abs(forecast)<=protocol['thresholds']['phase_relative_drift']),
             'mass_within_budget_prediction':bool(abs(massrel)<=protocol['thresholds']['mass_relative_drift']),
             'initial_Mach':maximum(np.sqrt(np.sum(u*u,axis=0))*np.sqrt(3)),
             'initial_div_u_max':maximum(div),'initial_rho_min':float(rho.min()),'initial_rho_max':float(rho.max()),
             'initial_phi_min':float(p.min()),'initial_phi_max':float(p.max()),'initial_pressure_abs_max':maximum(f['p_h']),
             'initial_grad_mu_max':maximum(np.sqrt(np.sum(gm*gm,axis=0))),
             'initial_force_sum':[float(total(force[k])) for k in range(3)],
             'initial_capillary_power':float(total(np.sum(u*force,axis=0))),
             'initial_CH_dissipation':float(-total(mu*lap(mu))/6),
             'initial_source_integration_absolute_sum':float(total(abs(S))),
             'independent_errors':errors,'initialization_collide_calls':0,'actual_first_step_measured':False}
        out.append(row);print(case['id'],forecast,massrel,'Mach',row['initial_Mach'],flush=True)
    result={'scope':'Existing four zero-step fields only; scalar exact-moment forecasts, not a simulation',
            'cases':out,'source_coefficient_zeroth_moment':float(np.dot(W,-2.5+1.5*np.sum(V*V,axis=1))),
            'field_rows':COUNT*len(out),'all_initial_field_checks_pass':True,'first_step_evolved':False,
            'predicted_joint_physical_budget_pass':all(r['phase_within_budget_prediction'] and r['mass_within_budget_prediction'] for r in out)}
    (A/'initial_budget_recomputed.json').write_text(json.dumps(result,indent=2)+'\n')
    (A/'inputs_sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
    with (A/'initial_budget_summary.csv').open('w') as f:
        fields=['case_id','source_sum','predicted_delta_Q_over_Q0','predicted_delta_mass_over_M0','predicted_Q_budget_ratio','predicted_mass_budget_ratio','initial_Mach','initial_div_u_max','initial_rho_min']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(out)
if __name__=='__main__':main()
