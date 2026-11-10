"""Synthetic fields only. Independent polynomial/analytic integral oracles.

No PDE discretization matrix is assembled or solved; one artificial CSR array
is used only to test the pressure-row extraction/sign/MPC bookkeeping.
"""
import ast
from copy import deepcopy
from fractions import Fraction
from itertools import permutations
import hashlib
import json
from math import factorial, pi
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from numerics import (Field,Rejected,nodes,evaluate,geometry,triangle_rule,analytic,
                      FIXTURE_ATOL,FIXTURE_RTOL)
from extractor import extract_arrays,extract_real_record,read_synthetic_bundle


def make_fixture(velocity,pressure=lambda x,z:0.,nx=4,nz=2,flip=False,shuffle=False,offset=0.):
    """Independent rectangular mesh and nodal samples, never a numerical solve."""
    xy=np.array([(2*i/nx,j/nz) for j in range(nz+1) for i in range(nx+1)])
    triangles=[]
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;c=a+nx+1;d=c+1
            triangles.extend(([a,b,c],[b,d,c]) if flip else ([a,b,d],[a,d,c]))
    triangles=np.array(triangles,dtype=int)
    coords=[];lookup={};cellnodes=[]
    for tri in triangles:
        v=xy[tri]
        # Independent vertex/edge list, not imported P2 shape functions.
        pts=[v[0],v[1],v[2],(v[0]+v[1])/2,(v[1]+v[2])/2,(v[2]+v[0])/2]
        ids=[]
        for pos in pts:
            key=tuple(pos)
            if key not in lookup:lookup[key]=len(coords);coords.append(pos)
            ids.append(lookup[key])
        cellnodes.append(ids)
    coords=np.array(coords);nv=2*len(coords);npres=len(xy);n=nv+npres
    vi=np.arange(nv);pidx=np.arange(nv,n);components=np.tile([0,1],len(coords))
    vcoords=np.repeat(coords,2,axis=0)
    vals=np.zeros(n)
    vals[vi]=np.array([velocity(x,z) for x,z in coords]).ravel()
    vals[pidx]=[pressure(x,z)+offset for x,z in xy]
    cv=np.array([[2*k+c for k in row for c in (0,1)] for row in cellnodes])
    cp=pidx[triangles];weights=np.zeros(npres)
    for tri in triangles:
        v=xy[tri];det=(v[1,0]-v[0,0])*(v[2,1]-v[0,1])-(v[1,1]-v[0,1])*(v[2,0]-v[0,0])
        weights[tri]+=abs(det)/6
    if shuffle:
        rng=np.random.default_rng(240)
        permutation=rng.permutation(n) # old ID -> new ID
        new=np.empty_like(vals);new[permutation]=vals;vals=new
        vi=permutation[vi];pidx=permutation[pidx];cv=permutation[cv];cp=permutation[cp]
        for row in cv:rng.shuffle(row)
        for row in cp:rng.shuffle(row)
        for row in triangles:rng.shuffle(row)
    # Synthetic fixture defaults have no constraints, to allow open/nonperiodic tests.
    solution=dict(mesh_coordinates_hat=xy,mesh_triangles=triangles,
                  reconstructed_solution=vals,algebraic_solution_before_backsub=vals.copy(),
                  velocity_dof_coordinates_hat=vcoords,velocity_dof_components=components,
                  velocity_reconstructed_dof_indices=vi,velocity_reconstructed_values=vals[vi],
                  pressure_coordinates_hat=xy.copy(),pressure_reconstructed_dof_indices=pidx,
                  pressure_raw_P1=vals[pidx],pressure_zero_mean_P1=vals[pidx]-weights@vals[pidx]/weights.sum(),
                  pressure_area_weights_hat2=weights,periodic_slave_dofs=np.array([],dtype=int),
                  periodic_master_dofs=np.array([],dtype=int),periodic_coefficients=np.array([],dtype=float),
                  wall_velocity_dof_indices=np.array([],dtype=int))
    system=dict(cell_velocity_mixed_dofs=cv,cell_pressure_mixed_dofs=cp)
    return solution,system


def bundle_write(root,s,a):
    m=dict(kind='SYNTHETIC_EXTRACTOR_FIXTURE_NOT_RESULT',run_id=None,groups={})
    for group,data in [('solution',s),('system',a)]:
        (root/group).mkdir();m['groups'][group]={}
        for name,array in data.items():
            p=root/group/(name+'.npy');np.save(p,array,allow_pickle=False)
            m['groups'][group][p.name]=dict(size_bytes=p.stat().st_size,
                 sha256=hashlib.sha256(p.read_bytes()).hexdigest(),shape=list(array.shape),dtype=array.dtype.str)
    (root/'fixture_manifest.json').write_text(json.dumps(m))


class Fixtures(unittest.TestCase):
    def near(self,a,b,atol=FIXTURE_ATOL,rtol=FIXTURE_RTOL):
        np.testing.assert_allclose(a,b,atol=atol,rtol=rtol)

    def test_p2_complete_polynomial_all_orientations_and_scales(self):
        coeff=np.array([[1,2,-3,4,5,-2],[-2,3,4,-1,2,6.]])
        def poly(x):
            a,b=x[:,0],x[:,1]
            return np.column_stack((np.ones(len(a)),a,b,a*a,a*b,b*b))@coeff.T
        for scale in (.001,1.,1000.):
            v=np.array([[.2,-.4],[1.3,.1],[-.1,1.6]])*scale
            q=np.array([[.2,.3,.5],[.6,.2,.2],[.1,.8,.1]])@v
            for perm in permutations(range(3)):
                vv=v[list(perm)];u,g,p,_=evaluate(vv,poly(nodes(vv)),np.array([3+2*x-z for x,z in vv]),q)
                self.near(u,poly(q),atol=1e-8)
                expected=np.empty_like(g)
                for c in range(2):
                    _,b,d,e,f,h=coeff[c];expected[:,c,0]=b+2*e*q[:,0]+f*q[:,1];expected[:,c,1]=d+f*q[:,0]+2*h*q[:,1]
                self.near(g,expected,atol=1e-8);self.near(p,3+2*q[:,0]-q[:,1])

    def test_triangle_monomials_through_degree_eight(self):
        v=np.array([[0.,0.],[1.,0.],[0.,1.]])
        x,w=triangle_rule(v,6)
        for i in range(9):
            for j in range(9-i):
                exact=Fraction(factorial(i)*factorial(j),factorial(i+j+2))
                self.near(w@(x[:,0]**i*x[:,1]**j),float(exact))

    def test_flat_parabola_full_pipeline_and_shared_edge_sections(self):
        s,a=make_fixture(lambda x,z:(z*(1-z)/2,0.))
        out=extract_arrays(s,a,'flat_mixed',include_algebra=False);m=out['high_rule']
        self.near([m['area'],m['J_hat'],m['D'],m['Dsym'],m['W']],[2,1/12,1/6,1/6,1/6])
        self.near(m['u_error2'],0);self.assertIsNone(m['p_L2_relative'])
        self.near(out['flux']['q'],np.full(7,1/12))
        for slab in out['flux']['slabs']:self.near(slab['theorem_defect'],0)
        self.assertTrue(out['quadrature']['within_candidate_change_target'])
        self.assertFalse(out['RESULT_PASS'])

    def test_global_and_local_dof_permutations(self):
        v=lambda x,z:(1+x+z+x*z,z*z-x)
        p=lambda x,z:2*x-3*z
        s,a=make_fixture(v,p);t,b=make_fixture(v,p,shuffle=True)
        m=Field(s,a).integrate();n=Field(t,b).integrate()
        for key in ('J_hat','D','W','Pdiv','div2','u_error2','p_error2'):
            self.near(m[key],n[key])
        self.near(Field(s,a).section(.5),Field(t,b).section(.5))

    def test_pressure_offset_invariance(self):
        v=lambda x,z:(z*(1-z),x*z)
        p=lambda x,z:x+2*z
        s,a=make_fixture(v,p);t,b=make_fixture(v,p,offset=17.)
        m=Field(s,a).integrate();n=Field(t,b).integrate()
        for key in ('p_error2','Pdiv','eta_energy_weak','J_hat'):
            self.near(m[key],n[key])
        self.near(n['pressure_mean_raw']-m['pressure_mean_raw'],17.)

    def test_rectangle_topology_flip_preserves_polynomial_integrals(self):
        v=lambda x,z:(x*x+z*z,x*z)
        p=lambda x,z:x-2*z
        s,a=make_fixture(v,p);t,b=make_fixture(v,p,flip=True)
        m=Field(s,a).integrate();n=Field(t,b).integrate()
        # Integrals independently known over [0,2]x[0,1].
        self.near(m['J_hat'],5/3)
        self.near(m['D'],50/3)
        self.near(m['div2'],24)
        for key in ('J_hat','D','Dsym','Pdiv','div2','u_error2','p_error2'):
            self.near(m[key],n[key])

    def test_complete_periodic_and_wall_trace_diagnostics(self):
        s,a=make_fixture(lambda x,z:(z*(1-z),0.))
        vi=s['velocity_reconstructed_dof_indices'];vc=s['velocity_dof_coordinates_hat'];comp=s['velocity_dof_components']
        pi=s['pressure_reconstructed_dof_indices'];pc=s['pressure_coordinates_hat']
        slave=[];master=[]
        for ids,coords,cs,is_velocity in ((vi,vc,comp,True),(pi,pc,np.full(len(pi),2),False)):
            for idx,pos,c in zip(ids,coords,cs):
                if pos[0]==2 and (not is_velocity or 0<pos[1]<1):
                    hit=np.flatnonzero((coords[:,0]==0)&(coords[:,1]==pos[1])&(cs==c))
                    self.assertEqual(len(hit),1);slave.append(idx);master.append(ids[hit[0]])
        s['periodic_slave_dofs']=np.array(slave);s['periodic_master_dofs']=np.array(master)
        s['periodic_coefficients']=np.ones(len(slave))
        s['wall_velocity_dof_indices']=vi[(vc[:,1]==0)|(vc[:,1]==1)]
        s['algebraic_solution_before_backsub'][slave]=0
        f=Field(s,a);report=f.trace_report()
        self.assertTrue(report['periodic_slave_indices_complete']);self.assertTrue(report['wall_indices_complete'])
        self.near(report['reconstruction_max_abs'],0);self.near(report['periodic_max_abs'],0)
        self.near(report['wall_max_abs'],0)
        s['periodic_master_dofs'][0]=s['pressure_reconstructed_dof_indices'][0]
        with self.assertRaisesRegex(Rejected,'PERIODIC_COMPONENT'):Field(s,a).trace_report()

    def test_strong_divergence_energy_identity_noslip_periodic(self):
        # Continuous piecewise linear x-dependent bubble, sampled exactly as P2.
        # Product z(1-z)*x would be cubic, so instead use an interior P2 hat.
        s,a=make_fixture(lambda x,z:(0.,0.),nx=4,nz=4)
        coords=s['velocity_dof_coordinates_hat'];comp=s['velocity_dof_components'];vi=s['velocity_reconstructed_dof_indices']
        hit=np.flatnonzero((np.max(np.abs(coords-[1.,.5]),axis=1)<1e-12)&(comp==0))
        s['reconstructed_solution'][vi[hit]]=1
        s['velocity_reconstructed_values']=s['reconstructed_solution'][vi].copy()
        f=Field(s,a);m=f.integrate()
        self.assertGreater(m['div2'],0)
        self.near(m['Dsym']-m['D'],m['div2'])
        self.near(m['eta_div']**2,m['div2']/m['D'])
        fl=f.flux_report(m['J_hat'])
        for slab in fl['slabs']:self.near(slab['theorem_defect'],0)

    def test_slab_identity_nonzero_wall_flux(self):
        s,a=make_fixture(lambda x,z:(x*z,z*z),nx=3,nz=3)
        f=Field(s,a);left,right=.17,1.71
        # div = z + 2z = 3z; top wall outward flux=1, bottom=0.
        self.near(f.slab_divergence(left,right),1.5*(right-left))
        self.near(f.slab_wall_flux(left,right),right-left)
        self.near(f.section(right)-f.section(left),.5*(right-left))
        self.near(f.section(right)-f.section(left)+f.slab_wall_flux(left,right)-f.slab_divergence(left,right),0)

    def test_mms_analytic_integrals_independent_closed_form(self):
        # Exact polynomial integrals g0^2=1/630, g1^2=2/105, g2^2=4/5
        # before multiplying the amplitude .1. No production physics imported.
        s,a=make_fixture(lambda x,z:(0.,0.))
        f=Field(s,a);uj=uu=pp=work=0.
        for c in f.cells:
            x,w=triangle_rule(c['v'],12);u,p,force=analytic('mms_mixed',x)
            uj+=w@u[:,0];uu+=w@np.sum(u*u,axis=1);pp+=w@(p*p);work+=w@np.sum(u*force,axis=1)
        self.near(uj/2,1/6)
        self.near(uu,1/15+.01*(2/105+pi*pi/630))
        self.near(pp,.005)
        self.near(work,2/3+.01*(4/5+2*pi*pi*(2/105)+pi**4/630))
        pts=np.array([[.13,.21],[.82,.47],[1.75,.83]])
        # Independent finite difference Laplacian and pressure gradient check.
        step=2e-4;u,p,force=analytic('mms_mixed',pts);lap=np.zeros_like(u);gp=np.zeros_like(u)
        for axis in (0,1):
            e=np.zeros_like(pts);e[:,axis]=step
            up,pp,_=analytic('mms_mixed',pts+e);um,pm,_=analytic('mms_mixed',pts-e)
            upp,_,_=analytic('mms_mixed',pts+2*e);umm,_,_=analytic('mms_mixed',pts-2*e)
            lap+=(-upp+16*up-30*u+16*um-umm)/(12*step*step)
            gp[:,axis]=(pp-pm)/(2*step)
        self.near(-lap+gp,force,atol=1e-7,rtol=1e-7)

    def test_mms_interpolation_quadrature_and_error_metrics(self):
        def v(x,z):return analytic('mms_mixed',np.array([[x,z]]))[0][0]
        def p(x,z):return analytic('mms_mixed',np.array([[x,z]]))[1][0]
        s,a=make_fixture(v,p,nx=4,nz=4)
        out=extract_arrays(s,a,include_algebra=False)
        self.assertGreater(out['high_rule']['u_L2_relative'],0)
        self.assertGreater(out['high_rule']['p_L2_relative'],0)
        self.assertTrue(out['quadrature']['within_candidate_change_target'])
        # This is nodal interpolation, explicitly NOT a manufactured PDE solution.
        self.assertEqual(out['status'],'OFFLINE_METRICS_UNACCEPTED')

    def test_zero_field_is_not_positive_driven_pass(self):
        s,a=make_fixture(lambda x,z:(0.,0.));m=Field(s,a).integrate()
        self.assertFalse(m['positive_driven_field']);self.assertIsNone(m['eta_div'])
        self.assertIsNone(m['eta_energy_direct']);self.near(m['u_L2_relative'],1)

    def test_weak_pressure_sign_and_periodic_aggregation_with_artificial_csr(self):
        s,a=make_fixture(lambda x,z:(x,0.),nx=2,nz=2)
        f=Field(s,a);m=f.integrate();n=len(s['reconstructed_solution'])
        pids=s['pressure_reconstructed_dof_indices'];pcoords=s['pressure_coordinates_hat']
        slave=pids[np.isclose(pcoords[:,0],2.)];master=pids[np.isclose(pcoords[:,0],0.)]
        s['periodic_slave_dofs']=slave;s['periodic_master_dofs']=master;s['periodic_coefficients']=np.ones(len(slave))
        # For div=1, integral of each pressure basis is its area weight.
        expected=np.zeros(n);expected[pids]=s['pressure_area_weights_hat2']
        for si,ma in zip(slave,master):expected[ma]+=expected[si];expected[si]=0
        pivot=int(np.flatnonzero(s['algebraic_solution_before_backsub'])[0]);value=s['algebraic_solution_before_backsub'][pivot]
        ptr=[0];col=[];data=[];rhs=np.zeros(n);rhs[pivot]=1
        for i in range(n):
            if expected[i]!=0:col.append(pivot);data.append(-expected[i]/value)
            ptr.append(len(col))
        a.update(csr_indptr=np.array(ptr),csr_indices=np.array(col),csr_values=np.array(data),rhs_after=rhs)
        result=f.weak_residual(m['weak_pressure_moments_unconstrained'])
        self.near(result['independent_c_vs_matrix_residual'],0)
        self.near(result['eta_c'],np.linalg.norm(expected))
        a['csr_values']=-a['csr_values']
        self.assertGreater(f.weak_residual(m['weak_pressure_moments_unconstrained'])['independent_c_vs_matrix_residual'],.1)
        a['rhs_after']=np.zeros(n)
        with self.assertRaisesRegex(Rejected,'ZERO_RHS'):f.weak_residual(m['weak_pressure_moments_unconstrained'])

    def test_bad_maps_nan_degenerate_duplicate_and_units_rejected(self):
        s,a=make_fixture(lambda x,z:(z*(1-z),0.))
        variants=[]
        t,b=deepcopy(s),deepcopy(a);t['reconstructed_solution'][0]=np.nan;variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);b['cell_velocity_mixed_dofs'][0,0]=b['cell_velocity_mixed_dofs'][0,1];variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);t['mesh_triangles'][0]=t['mesh_triangles'][1];variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);t['mesh_triangles'][0,1]=t['mesh_triangles'][0,0];variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);t['mesh_coordinates_hat']*=1e-9;variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);t['velocity_dof_coordinates_hat'][0,0]+=.03;variants.append((t,b))
        t,b=deepcopy(s),deepcopy(a);t['pressure_area_weights_hat2']*=2;variants.append((t,b))
        for t,b in variants:
            with self.assertRaises(Rejected):Field(t,b)

    def test_synthetic_archive_roundtrip_hash_tamper_and_kind_rejection(self):
        s,a=make_fixture(lambda x,z:(z*(1-z)/2,0.))
        with tempfile.TemporaryDirectory(prefix='sim240_synthetic_extractor_') as tmp:
            root=Path(tmp);bundle_write(root,s,a);t,b=read_synthetic_bundle(root)
            self.near(Field(t,b).integrate('flat_mixed')['J_hat'],1/12)
            p=root/'solution/mesh_coordinates_hat.npy';p.write_bytes(p.read_bytes()+b'x')
            with self.assertRaises(Rejected):read_synthetic_bundle(root)
            m=json.loads((root/'fixture_manifest.json').read_text());m['kind']='REAL_DIAGNOSTIC_UNVERIFIED'
            (root/'fixture_manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(Rejected,'SYNTHETIC_MARKER'):read_synthetic_bundle(root)

    def test_real_entry_rejects_before_path_access(self):
        class ExplodingPath:
            def __fspath__(self):raise AssertionError('REAL PATH WAS ACCESSED')
        with self.assertRaisesRegex(Rejected,'CLOSED'):extract_real_record(ExplodingPath())

    def test_no_backend_or_solver_imports(self):
        banned={'dolfinx','ufl','petsc4py','scipy','mpi4py','subprocess','solver','assembly','worker'}
        for name in ('numerics.py','extractor.py'):
            tree=ast.parse(Path(__file__).with_name(name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertFalse({a.name.split('.')[0] for a in node.names}&banned)
                if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],banned)
        self.assertFalse(banned & {x.split('.')[0] for x in sys.modules})


if __name__=='__main__':
    unittest.main(verbosity=2)
