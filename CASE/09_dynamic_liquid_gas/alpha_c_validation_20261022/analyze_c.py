"""Independent reconstruction from every C frame; no OpenLB or reference evolution."""
import gzip
import json
import math
import numpy as np
from numerical_reference import C,W,lap,grad
from analyze_alpha import require,rows,drift

FIELDS=['phi','mu','source','source_old','ux','uy','uz','jx','jy','jz','Fx','Fy','Fz','p_h','rho','tau']
LD=np.longdouble

def total(x):return np.sum(x,dtype=LD)
def vec(f,prefix):return np.array([f[prefix+a] for a in 'xyz'])
def maximum(x):return float(np.max(abs(x)))

def binary(path,n,nfields):
    with gzip.open(path,'rb') as f:raw=f.read()
    require(len(raw)==n**3*nfields*8,'binary size mismatch '+str(path))
    data=np.frombuffer(raw,dtype='<f8').reshape((n,n,n,nfields))
    require(np.isfinite(data).all(),'nonfinite binary '+str(path));return data

def frame(path,n):
    a=binary(path,n,16);return {name:a[...,i] for i,name in enumerate(FIELDS)}

def quantities(f,cfg):
    p=f['phi'];rho=f['rho'];mu=f['mu'];u=vec(f,'u');j=vec(f,'j');force=vec(f,'F')
    gp=grad(p);gm=grad(mu);lp=lap(p);lm=lap(mu)
    raw=j/rho;snapped=np.where(abs(raw)<1e-15,0.,raw);cut=rho*(snapped-raw)
    derivatives=np.array([grad(u[a]) for a in range(3)])
    div=sum(derivatives[a,a] for a in range(3));strain=.5*(derivatives+derivatives.swapaxes(0,1))
    actual_S=np.sum(u*gp,axis=0);mu_expected=np.zeros_like(p) if cfg['constant_mu_zero'] else 4*cfg['beta']*p*(p-1)*(p-.5)-cfg['kappa']*lp
    s=dict(phase_sum=total(p),liquid_sum=total(1-p),mass_sum=total(rho),source_sum=total(f['source']),
        S_sum=total(f['source_old']),phi_div_u_sum=total(p*div),
        free_energy=total(cfg['beta']*p*p*(p-1)**2-cfg['kappa']/2*p*lp),
        link_dissipation=-total(mu*lm)/6,kinetic_energy=total(.5*rho*np.sum(u*u,axis=0)),
        viscous_gradient_dissipation=total(2*rho*(f['tau']-.5)/3*np.sum(strain*strain,axis=(0,1))),
        capillary_power=total(np.sum(u*force,axis=0)),instant_advection_work=-total(mu*f['source_old']),
        AB_advection_work=-total(mu*f['source']),conditional_mass_diffusion_kinetic_term=-total(.5*np.sum(u*u,axis=0)*(cfg['rhos'][1]-1)/6*lm),
        mass_diffusion_flux_max=maximum((cfg['rhos'][1]-1)/6*np.sqrt(np.sum(gm*gm,axis=0))),
        Mach_max=maximum(np.sqrt(3*np.sum(u*u,axis=0))),grad_mu_max=maximum(np.sqrt(np.sum(gm*gm,axis=0))),
        div_u_max=maximum(div),div_u_square_sum=total(div*div),
        mu_constitutive_max_error=maximum(mu-mu_expected),S_local_max_error=maximum(f['source_old']-actual_S),
        force_local_max_error=maximum(force+p*gm),rho_mapping_max_error=maximum(rho-(1+(cfg['rhos'][1]-1)*p)),
        tau_mapping_max_error=maximum(f['tau']-(1+.25*p)),phi_min=float(p.min()),phi_max=float(p.max()),
        rho_min=float(rho.min()),rho_max=float(rho.max()),p_h_min=float(f['p_h'].min()),p_h_max=float(f['p_h'].max()),
        half_force_velocity_error=maximum(u-snapped-.5*force/rho))
    for a in range(3):
        s[f'raw_J{a}']=total(j[a]);s[f'physical_P{a}']=total(rho*u[a]);s[f'force_sum{a}']=total(force[a])
        s[f'raw_cut_sum{a}']=total(cut[a]);s[f'omega_cut_sum{a}']=total(cut[a]/f['tau'])
    s['gradient_integration_by_parts_residual_per_node']=(s['S_sum']+s['phi_div_u_sum'])/p.size
    s['semidiscrete_capillary_advection_exchange']=s['instant_advection_work']+s['capillary_power']
    return s

def population_step1(path,n,before,after,cfg):
    pre=binary(path/'step1_pre.bin.gz',n,38);post=binary(path/'step1_post_collision.bin.gz',n,38);stream=binary(path/'step1_post_stream.bin.gz',n,38)
    j=np.einsum('...q,qa->a...',pre[...,:19],C);rho=before['rho'];force=vec(before,'F')
    raw=j/rho;u=np.where(abs(raw)<1e-15,0.,raw)+force/(2*rho);u2=np.sum(u*u,axis=0)
    gr=(cfg['rhos'][1]-1)*grad(before['phi']);pressure=(np.sum(pre[...,1:19],axis=-1)+.5*np.sum(u*gr,axis=0)-.5*rho*u2)/2
    errors=dict(NS_collision=0.,CH_collision=0.,NS_stream=0.,CH_stream=0.,pressure_recovery=maximum(pressure-before['p_h']),
                pre_phi=maximum(1+np.sum(pre[...,19:],axis=-1)-before['phi']),post_phi=maximum(1+np.sum(stream[...,19:],axis=-1)-after['phi']),
                pre_raw_j=maximum(j-vec(before,'j')),post_raw_j=maximum(np.einsum('...q,qa->a...',stream[...,:19],C)-vec(after,'j')))
    for i,(c,w) in enumerate(zip(C,W)):
        cu=np.sum(c[:,None,None,None]*u,axis=0);cf=np.sum(c[:,None,None,None]*force/rho,axis=0);cg=np.sum(c[:,None,None,None]*gr,axis=0)
        eq=3*pressure*(w-1)-1.5*rho*w*u2 if i==0 else 3*w*(pressure+rho*(cu+1.5*cu*cu-.5*u2))
        om=1/before['tau'];expected=(1-om)*pre[...,i]+om*eq+(1-.5*om)*3*w*(rho*cf+cu*cg)
        hc=(before['phi']-(1-w)*before['mu'] if i==0 else w*before['mu'])-w+w*(-2.5+1.5*(c@c))*before['source']
        errors['NS_collision']=max(errors['NS_collision'],maximum(post[...,i]-expected))
        errors['CH_collision']=max(errors['CH_collision'],maximum(post[...,19+i]-hc))
        errors['NS_stream']=max(errors['NS_stream'],maximum(stream[...,i]-np.roll(post[...,i],tuple(c),axis=(0,1,2))))
        errors['CH_stream']=max(errors['CH_stream'],maximum(stream[...,19+i]-np.roll(post[...,19+i],tuple(c),axis=(0,1,2))))
    return errors

def analyze_case(case,path,thresholds,initialization=False):
    cfg=json.loads((path/'config.json').read_text());result=json.loads((path/'result.json').read_text());schema=json.loads((path/'frame_schema.json').read_text())
    n=case['N'];steps=0 if initialization else case['steps'];count=n**3
    require(cfg['case_id']==case['id'] and cfg['N']==n and cfg['steps']==steps and cfg['nominal_steps']==64,'C configuration length/ID mismatch')
    require(cfg['rhos']==case['rhos'] and cfg['taus']==case['taus'] and cfg['alpha']==1 and cfg['tau_CH']==1,'C parameter mismatch')
    require(cfg['constant_mu_zero']==(case['chemical']=='mu0') and cfg['MPI_ranks']==1,'C model mismatch')
    require(math.isclose(cfg['dt_SI'],1.0416666666666667e-13,rel_tol=1e-14),'C time mapping mismatch')
    for k,v in dict(sigma=2.0833333333333333e-5,width=4,beta=6.25e-5,kappa=1.25e-4).items():require(math.isclose(cfg[k],v,rel_tol=1e-14),'C '+k+' mismatch')
    require(schema['columns']==FIELDS and schema['shape']==[n,n,n,16] and schema['dtype']=='<f8' and schema['order']=='C','C schema mismatch')
    require(result['requested_steps']==steps and result['completed_steps']==steps and result['NS_collide_calls']==steps and result['CH_collide_calls']==steps and result['safe'],'C result incomplete')
    history=rows(path/'history.csv');require(len(history)==steps+1 and [int(r['step']) for r in history]==list(range(steps+1)),'C history missing steps')
    expected={f'step_{i}.bin.gz' for i in range(steps+1)};require({p.name for p in (path/'frames').iterdir()}==expected,'C frame set mismatch')
    maxima={};raw_values={'phase_sum':[],'liquid_sum':[],'mass_sum':[]};old=None;old_s=None;initial=None;first_quantities=None;pop_metrics=None
    self_report_keys=['NS_collision_population_max_error','CH_collision_population_max_error','NS_stream_population_max_error','CH_stream_population_max_error','CH_point_update_max_error','pressure_recovery_max_error','alpha_max_error']
    self_report_max={k:max(float(r[k]) for r in history) for k in self_report_keys}
    quantity_history_error=0.
    for t,row in enumerate(history):
        f=frame(path/'frames'/f'step_{t}.bin.gz',n)
        require(np.min(f['rho'])>0,'C nonpositive density in saved frame')
        s=quantities(f,cfg)
        require(int(row['finite'])==1 and int(row['nodes'])==count and s['rho_min']>0,'bad C finite/rho/nodes')
        for k,v in s.items():
            if k=='half_force_velocity_error':continue
            discrepancy=abs(LD(row[k])-v)
            if k.endswith('_sum') or k.startswith(('raw_J','physical_P','force_sum','raw_cut_sum','omega_cut_sum')) or k in ('free_energy','link_dissipation','kinetic_energy','viscous_gradient_dissipation','capillary_power','instant_advection_work','AB_advection_work','conditional_mass_diffusion_kinetic_term','semidiscrete_capillary_advection_exchange'):
                discrepancy/=count
            quantity_history_error=max(quantity_history_error,float(discrepancy))
        for key in ('mu_constitutive_max_error','S_local_max_error','force_local_max_error','rho_mapping_max_error','tau_mapping_max_error','half_force_velocity_error'):
            maxima[key]=max(maxima.get(key,0.),float(s[key]))
        for k in raw_values:raw_values[k].append(str(s[k]))
        if t==0:
            initial=f;first_quantities=s
            x,y,z=np.indices((n,)*3);a=cfg['a0_nm']/2.5+(np.sin(2*np.pi*y/n+.37)*np.cos(2*np.pi*z/n+.19)+.25*np.cos(4*np.pi*y/n+.23))/2.5
            prescribed=.5*(1+np.tanh(2*(abs(x-n/2)-a)/4))
            require(maximum(f['phi']-prescribed)<1e-12 and abs(total(f['phi'])/count-.5)<1e-12,'C initial profile/amount mismatch')
            maxima['startup_source_error']=maximum(f['source']-f['source_old'])
        else:
            source=sum(w*(-2.5+1.5*(c@c))*np.roll(old['source'],tuple(c),axis=(0,1,2)) for c,w in zip(C,W))
            phase_delta=f['phi']-old['phi'];error=maximum(phase_delta-lap(old['mu'])/6-source)
            maxima['CH_point_update_max_error']=max(maxima.get('CH_point_update_max_error',0.),error)
            qres=(s['phase_sum']-old_s['phase_sum']+old_s['source_sum'])/count
            maxima['phase_budget_residual_per_node']=max(maxima.get('phase_budget_residual_per_node',0.),float(abs(qres)))
            for a in range(3):
                raw=(s[f'raw_J{a}']-old_s[f'raw_J{a}']-old_s[f'force_sum{a}']-old_s[f'omega_cut_sum{a}'])/count
                phys=(s[f'physical_P{a}']-old_s[f'physical_P{a}']-.5*(s[f'force_sum{a}']+old_s[f'force_sum{a}'])-old_s[f'omega_cut_sum{a}']-s[f'raw_cut_sum{a}']+old_s[f'raw_cut_sum{a}'])/count
                for key,v in ((f'raw_momentum_residual_per_node_{a}',raw),(f'physical_momentum_residual_per_node_{a}',phys)):
                    maxima[key]=max(maxima.get(key,0.),float(abs(v)));require(abs(LD(row[key])-v)<1e-12,'C momentum ledger mismatch')
            ab=maximum(f['source']-(1.5*f['source_old']-.5*old['source_old']));maxima['AB_source_max_error']=max(maxima.get('AB_source_max_error',0.),ab)
            work=total(old['mu']*phase_delta);sourcework=total(old['mu']*source);remainder=s['free_energy']-old_s['free_energy']-work
            energy=(s['free_energy']-old_s['free_energy']+old_s['link_dissipation']-sourcework-remainder)/count
            maxima['energy_balance_residual_per_node']=max(maxima.get('energy_balance_residual_per_node',0.),float(abs(energy)))
            for key,value in dict(chemical_work_on_actual_delta_phi=work,source_migration_work=sourcework,energy_time_remainder=remainder,
                                  source_migration_correction_work=sourcework-old_s['AB_advection_work'],
                                  kinetic_diagnostic_remainder=s['kinetic_energy']-old_s['kinetic_energy']-old_s['capillary_power']+old_s['viscous_gradient_dissipation']).items():
                require(abs(LD(row[key])-value)/count<1e-12,'C work/remainder ledger mismatch '+key)
            if t==1:pop_metrics=population_step1(path,n,old,f,cfg)
        if cfg['constant_mu_zero']:
            maxima['control_phi_change']=max(maxima.get('control_phi_change',0.),maximum(f['phi']-initial['phi']))
            maxima['control_velocity']=max(maxima.get('control_velocity',0.),maximum(vec(f,'u')))
        for field,key in (('phase_sum','phase_relative_drift'),('mass_sum','mass_relative_drift'),('liquid_sum','liquid_relative_drift')):
            d=(s[field]-first_quantities[field])/first_quantities[field]
            require(abs(d-LD(row[key]))<1e-12,'C reported drift mismatch')
        old=f;old_s=s
    require(quantity_history_error<1e-12,'independent field/history quantity mismatch')
    amounts={k:drift(v) for k,v in raw_values.items()}
    implementation=all(v<=thresholds['local_absolute'] for v in maxima.values()) and all(v<=thresholds['local_absolute'] for v in self_report_max.values())
    if pop_metrics:implementation=implementation and all(v<=thresholds['local_absolute'] for v in pop_metrics.values())
    safety=max(float(r['Mach_max']) for r in history)<thresholds['Mach']
    amount_pass=amounts['phase_sum']['max_abs']<=thresholds['phase_relative_drift'] and amounts['mass_sum']['max_abs']<=thresholds['mass_relative_drift']
    return dict(id=case['id'],initialization_only=initialization,implementation_contract_pass=None if initialization else bool(implementation),
                physical_amount_drift_within_budget=None if initialization else bool(amount_pass),safety_pass=bool(safety),
                independent_maxima=maxima,reported_stage_maxima=self_report_max,step1_full_population_checks=pop_metrics,
                field_history_max_discrepancy=float(quantity_history_error),amounts=amounts,
                maximum_Mach=max(float(r['Mach_max']) for r in history),
                initial_rho_min=first_quantities['rho_min'],full_population_independent_steps=[] if initialization else [1],
                all_step_fields_reconstructed=True,energy_remainders_descriptive_not_zero_gates=True)
