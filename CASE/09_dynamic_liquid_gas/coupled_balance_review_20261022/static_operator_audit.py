#!/usr/bin/env python3
"""Read-only source binding + finite-array algebra. No OpenLB/time integrator.

The arrays below are synthetic algebra fixtures, not physical CFD results.
Output is a new review artifact, never an old CASE output.
"""
from pathlib import Path
import hashlib
import json
import re
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLB = Path('/home/dell/openlb')
source = (OLB/'src/descriptor/definition/common.h').read_text()
def descriptor_array(name):
    block = re.search(r'\b'+name+r'<3,19>\[[^;]+?=\s*\{(.*?)\n\};', source, re.S).group(1)
    return [[int(v) for v in row.split(',')] for row in re.findall(r'\{([^{}]+)\}', block)]
c = np.array(descriptor_array('c'))
w = np.array([a/b for a,b in descriptor_array('t')])
assert c.shape == (19,3) and w.shape == (19,)
cs2 = 1/3
a = 2*w/cs2
b = w*(-2.5+np.sum(c*c,axis=1)/(2*cs2))
def shift(f, ci):
    return np.roll(f, tuple(-int(v) for v in ci), axis=(0,1,2))
def lap(f):
    return sum(ai*(shift(f,ci)-f) for ai,ci in zip(a,c))
def grad(f):
    return np.array([sum(wi*ci[j]*shift(f,ci)/cs2 for wi,ci in zip(w,c)) for j in range(3)])
def div(v):
    return sum(grad(v[j])[j] for j in range(3))
def total(v):
    return float(np.sum(v,dtype=np.longdouble))
def inner(f,g):
    return total(f*g)
def symbol(k):
    return float(np.sum(a*(1-np.cos(c@k))))

N=16
x,y,z=np.indices((N,)*3)*2*np.pi/N
phi=.35+.13*np.cos(x+.31)+.07*np.sin(2*x+.2)+.06*np.cos(y+.4)+.04*np.sin(x+y+.7)+.03*np.cos(z-.3)
psi=np.sin(x+.2)*np.sin(y+.6)+.17*np.cos(y+z+.5)
gp=grad(psi)
u=np.array([gp[1],-gp[0],np.zeros_like(phi)])
beta=.03; kappa=.02; M=1/6
mu=4*beta*phi*(phi-1)*(phi-.5)-kappa*lap(phi)
Gphi=grad(phi); Gmu=grad(mu)
S=np.sum(u*Gphi,axis=0)
def energy(p):
    return total(beta*p*p*(p-1)**2)-kappa/2*inner(p,lap(p))
eta=np.cos(2*x-y+.7)+.2*np.sin(z+x)
h=1e-5
energy_fd=(energy(phi+h*eta)-energy(phi-h*eta))/(2*h)
energy_derivative=inner(mu,eta)
link_diss=M/2*sum(ai*total((shift(mu,ci)-mu)**2) for ai,ci in zip(a,c))
gradient_diss=M*total(Gmu*Gmu)
cap_force=-phi*Gmu
source_old=.7*S+.01*np.cos(x)
source_AB=1.5*S-.5*source_old
# Evaluate one-step FORMULA on arrays; no dynamics or trajectory is executed.
source_stream=sum(bi*shift(source_AB,-ci) for bi,ci in zip(b,c))
delta_phi=M*lap(mu)+source_stream
compressible_u=Gphi
Sc=np.sum(compressible_u*Gphi,axis=0)

checks={
 'weights_sum_error':abs(float(w.sum())-1),
 'source_zeroth_plus_one':abs(float(b.sum())+1),
 'source_first_max':float(np.max(np.abs(b@c))),
 'source_second_max':float(np.max(np.abs(np.einsum('i,ij,ik->jk',b,c,c)))),
 'laplacian_sum':total(lap(mu)),
 'gradient_adjoint_residual':total(S)+inner(phi,div(u)),
 'solenoidal_fixture_divergence_max':float(np.max(np.abs(div(u)))),
 'CH_tau1_global_budget_residual':total(delta_phi)+total(source_AB),
 'energy_variation_absolute_error':abs(energy_fd-energy_derivative),
 'energy_variation_relative_error':abs(energy_fd-energy_derivative)/max(abs(energy_derivative),1e-30),
 'link_dissipation_identity_residual':link_diss+M*inner(mu,lap(mu)),
 'compressible_source_identity_residual':total(Sc)+inner(phi,div(compressible_u)),
}
observations={
 'fixture_phi_range':[float(phi.min()),float(phi.max())],
 'source_sum_solenoidal':total(S),
 'source_sum_non_solenoidal':total(Sc),
 'link_dissipation':link_diss,
 'central_gradient_squared_dissipation':gradient_diss,
 'relative_dissipation_definition_difference':(gradient_diss-link_diss)/link_diss,
 'capillary_net_force':[total(v) for v in cap_force],
 'capillary_net_force_to_sum_local_magnitudes':float(np.linalg.norm([total(v) for v in cap_force]))/total(np.sqrt(np.sum(cap_force**2,axis=0))),
 'advection_plus_capillary_work':-inner(mu,S)+total(np.sum(u*cap_force,axis=0)),
 'laplacian_minus_div_grad_L2':float(np.linalg.norm(lap(phi)-div(grad(phi)))),
 'note':'Synthetic periodic-array counterexamples; not measured target residual flow.',
}
sigma=1.4467592592592595e-5; W=4.; R=16.; rhoL=1.; rhoG=.0012
target_beta=12*sigma/W; target_kappa=1.5*sigma*W
spectra=[]
for n in [16,32,64]:
    for mode in [(1,0,0),(1,1,0),(1,1,1),(3,0,0),(2,2,1)]:
        k=2*np.pi*np.array(mode)/n; lam=symbol(k)
        growth=1-M*lam*(2*target_beta+target_kappa*lam)
        spectra.append(dict(N=n,mode=mode,Lambda=lam,k_squared=float(k@k),
           target_bulk_endpoint_amplification=growth,
           target_bulk_endpoint_efold_steps=-1/float(np.log(growth))))

binding=ROOT/'CASE/09_dynamic_liquid_gas/source3d_validation_20261022/evidence/build_binding.json'
hashes=json.loads(binding.read_text())['sha256']
mismatches=[p for p,hsh in hashes.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=hsh]
assert not mismatches, mismatches
assert max(abs(checks[k]) for k in ['source_zeroth_plus_one','source_first_max','source_second_max','laplacian_sum','gradient_adjoint_residual','solenoidal_fixture_divergence_max','CH_tau1_global_budget_residual','link_dissipation_identity_residual','compressible_source_identity_residual'])<1e-10
assert checks['energy_variation_relative_error']<1e-6
payload={
 'kind':'static algebra and current source binding only',
 'new_OpenLB_run':False,'time_integration':False,
 'descriptor_read_from':str(OLB/'src/descriptor/definition/common.h'),
 'checks':checks,'counterexamples':observations,'spectra':spectra,
 'target_scales':dict(beta=target_beta,kappa=target_kappa,M=M,
    density_positive_phi_upper_bound=rhoL/(rhoL-rhoG),
    curved_thin_interface_shift_estimate=-W/(12*R),
    conditional_gas_density_SI=(rhoG+(rhoG-rhoL)*(-W/(12*R)))*1000,
    note='thin-interface fixed-radius estimate only, not a solved equilibrium'),
 'physical_refinement_at_fixed_NS_tau':dict(dx_ratio=.5,dt_ratio=.25,
    sigma_lu_ratio=.5,W_lu_ratio=2,beta_lu_ratio=.25,kappa_lu_ratio=1,
    M_lu_ratio_required_for_fixed_M_SI=4,tau_CH_coarse=1,tau_CH_fine=2.5),
 'previous_bound_files_rechecked':len(hashes),'hash_mismatches':mismatches,
}
(HERE/'static_operator_audit.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps(payload,indent=2))
