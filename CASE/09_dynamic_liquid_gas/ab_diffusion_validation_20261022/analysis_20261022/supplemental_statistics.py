"""Additional completed-history statistics and endpoint energy audit, no simulation."""
from pathlib import Path
import json
import re
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
P=json.loads((BASE/'protocol.json').read_text());batch=P['batch_id'];root=BASE/'output'/batch
text=Path('/home/dell/openlb/src/descriptor/definition/common.h').read_text()
def arr(name):
    b=re.search(r'\b'+name+r'<3,19>\[[^;]+?=\s*\{(.*?)\n\};',text,re.S).group(1)
    return np.array([[int(x) for x in r.split(',')] for r in re.findall(r'\{([^{}]+)\}',b)])
C=arr('c');w=arr('t');W=w[:,0]/w[:,1]
def lap(f):return sum(6*w*(np.roll(f,tuple(-c),axis=(0,1,2))-f) for c,w in zip(C,W))
def read(path,dtype=np.longdouble):
    names=Path(path).open().readline().strip().split(',');a=np.loadtxt(path,delimiter=',',skiprows=1,ndmin=2,dtype=dtype)
    return dict(zip(names,a.T))
allstats=[];endpoint=[]
for case in P['B_cases']:
    name=case['id'];d=root/f'{batch}_b_{name}';h=read(d/'history.csv');size=case['N']**3
    r=dict(id=name,kind=case['kind'],tau=case['tau'],N=case['N'],phi_min=float(min(h['phi_min'])),phi_max=float(max(h['phi_max'])),max_observed_energy_balance_per_node=float(max(abs(h['energy_balance_residual']))/size),max_observed_tau1_step_error=float(max(h['one_step_max_error'])))
    if case['tau']==1:assert r['max_observed_energy_balance_per_node']<=1e-12
    allstats.append(r)
    for field,t in [('initial',0),('final',case['steps'])]:
        f=read(d/(field+'.csv'),np.float64);n=case['N'];indices=((f['x'].astype(int)*n+f['y'].astype(int))*n+f['z'].astype(int));order=np.argsort(indices)
        phi=f['phi'][order].reshape((n,)*3);mu=f['mu'][order].reshape((n,)*3)
        if case['kind']=='linear':
            f0=.5*case['a']*(phi-case['center'])**2;expected_mu=case['a']*(phi-case['center'])-case['kappa']*lap(phi)
        else:
            f0=case['beta']*phi**2*(phi-1)**2;expected_mu=4*case['beta']*phi*(phi-1)*(phi-.5)-case['kappa']*lap(phi)
        energy=np.sum(f0-case['kappa']/2*phi*lap(phi),dtype=np.longdouble);diss=-(case['tau']-.5)/3*np.sum(mu*lap(mu),dtype=np.longdouble)
        r=dict(id=name,field=field,mu_constitutive_max_error=float(np.max(abs(mu-expected_mu))),energy_definition_per_node=float(abs(energy-h['free_energy'][t])/size),dissipation_definition_per_node=float(abs(diss-h['link_dissipation'][t])/size))
        assert max(r[k] for k in ['mu_constitutive_max_error','energy_definition_per_node','dissipation_definition_per_node'])<=1e-12
        endpoint.append(r)
summary=dict(all_B_history=allstats,all_B_endpoint_energy_checks=endpoint,max_tau1_observed_energy_balance_per_node=max(r['max_observed_energy_balance_per_node'] for r in allstats if r['tau']==1),max_endpoint_energy_definition_per_node=max(r['energy_definition_per_node'] for r in endpoint),max_endpoint_dissipation_definition_per_node=max(r['dissipation_definition_per_node'] for r in endpoint),limitation='B1 energy history is observed; full-field independent energy audit is at endpoints. B2 full fields are audited every step by independent_review.py.')
(HERE/'supplemental_statistics.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['all_B_history','all_B_endpoint_energy_checks']},indent=2))
