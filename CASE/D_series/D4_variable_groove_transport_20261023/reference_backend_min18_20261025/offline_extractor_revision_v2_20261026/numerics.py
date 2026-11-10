"""Independent P2/P1 postprocessing primitives. NumPy only; no PDE backend.

No file access, assembly or equation solve. All coordinates are dimensionless.
"""
from math import fsum
import numpy as np


class Rejected(ValueError):
    pass


COORD_ATOL = 2e-12
FIXTURE_ATOL = 2e-11
FIXTURE_RTOL = 2e-11
QUADRATURE_CHANGE_TARGET = 1e-8


def require(ok, reason):
    if not ok:
        raise Rejected(reason)


def finite(a, shape=None):
    a = np.asarray(a)
    require(a.dtype.kind in 'fiu' and np.all(np.isfinite(a)), 'NONFINITE_OR_NONNUMERIC')
    if shape is not None:
        require(a.shape == shape, 'SHAPE_MISMATCH')
    return a


def indices(a, shape=None):
    a = finite(a, shape)
    require(a.dtype.kind in 'iu', 'INTEGER_INDICES_REQUIRED')
    return a.astype(np.int64, copy=False)


def geometry(vertices):
    v = finite(vertices, (3, 2)).astype(float)
    j = (v[1:] - v[0]).T
    det = j[0, 0]*j[1, 1] - j[0, 1]*j[1, 0]
    require(abs(det) > 64*np.finfo(float).eps*np.max(np.abs(j))**2, 'DEGENERATE_CELL')
    inv = np.array([[j[1, 1], -j[0, 1]], [-j[1, 0], j[0, 0]]])/det
    grads = np.vstack((-inv.sum(axis=0), inv))
    return v, abs(det), inv, grads


def nodes(vertices):
    v = np.asarray(vertices)
    return np.vstack((v, (v[0]+v[1])/2, (v[1]+v[2])/2, (v[2]+v[0])/2))


def barycentric(vertices, points):
    v, _, inv, _ = geometry(vertices)
    ab = (np.asarray(points)-v[0]) @ inv.T
    return np.column_stack((1-ab.sum(axis=1), ab))


def basis(lam, grad_lam):
    pairs = ((0, 1), (1, 2), (2, 0))
    phi = np.column_stack([lam[:, i]*(2*lam[:, i]-1) for i in range(3)] +
                          [4*lam[:, i]*lam[:, j] for i, j in pairs])
    grad = np.stack([(4*lam[:, i]-1)[:, None]*grad_lam[i] for i in range(3)] +
                    [4*(lam[:, i, None]*grad_lam[j]+lam[:, j, None]*grad_lam[i])
                     for i, j in pairs], axis=1)
    return phi, grad


def triangle_rule(vertices, n=8):
    require(isinstance(n, int) and 3 <= n <= 32, 'QUADRATURE_ORDER_OUT_OF_SCOPE')
    v, det, _, _ = geometry(vertices)
    x, w = np.polynomial.legendre.leggauss(n)
    x, w = (x+1)/2, w/2
    a, b = np.meshgrid(x, x, indexing='ij')
    wa, wb = np.meshgrid(w, w, indexing='ij')
    a, b = a.ravel(), b.ravel()
    lam = np.column_stack(((1-a)*(1-b), a, (1-a)*b))
    return lam @ v, (wa*wb).ravel()*(1-a)*det


def evaluate(vertices, velocity_nodes, pressure_nodes, points):
    _, _, _, grads = geometry(vertices)
    lam = barycentric(vertices, points)
    phi, grad = basis(lam, grads)
    return (phi @ velocity_nodes, np.einsum('qnd,nc->qcd', grad, velocity_nodes),
            lam @ pressure_nodes, lam)


def analytic(kind, points):
    """Independent streamfunction polynomial differentiation, no source import."""
    points = np.asarray(points)
    x, z = points[:, 0], points[:, 1]
    u = np.zeros((len(x), 2)); f = np.zeros_like(u); p = np.zeros(len(x))
    if kind == 'flat_mixed':
        u[:, 0] = z*(1-z)/2
        f[:, 0] = 1
        return u, p, f
    require(kind == 'mms_mixed', 'MIXED_RECTANGLE_ANALYTIC_KIND_REQUIRED')
    poly = np.polynomial.polynomial
    # psi = integral(z-z^2) + sin(pi*x) * g(z); g=.1*z^2*(1-z)^2
    g = np.array([0., 0., .1, -.2, .1])
    g0, g1, g2, g3 = [poly.polyval(z, poly.polyder(g, k)) for k in range(4)]
    s, c = np.sin(np.pi*x), np.cos(np.pi*x)
    u[:, 0] = z-z*z+s*g1
    u[:, 1] = -np.pi*c*g0
    p = .1*c*np.cos(np.pi*z)
    lap_x = -2+s*(g3-np.pi**2*g1)
    lap_z = -np.pi*c*(g2-np.pi**2*g0)
    f[:, 0] = -lap_x-.1*np.pi*s*np.cos(np.pi*z)
    f[:, 1] = -lap_z-.1*np.pi*c*np.sin(np.pi*z)
    return u, p, f


class Field:
    """Mixed rectangle field reconstructed by coordinate/component matching."""
    def __init__(self, solution, system, period=2., height=1.):
        require(period == 2. and height == 1., 'ONLY_NONDIMENSIONAL_2_BY_1_RECTANGLE_SUPPORTED')
        self.period, self.height = period, height
        self.s, self.sys = solution, system
        xy = finite(solution['mesh_coordinates_hat'])
        require(xy.ndim == 2 and xy.shape[1] == 2, 'MESH_COORDINATE_SHAPE')
        tri = indices(solution['mesh_triangles'])
        require(tri.ndim == 2 and tri.shape[1] == 3 and len(tri)>0, 'TRIANGLE_SHAPE')
        require(tri.min() >= 0 and tri.max() < len(xy), 'TRIANGLE_INDEX_RANGE')
        require(len({tuple(sorted(t)) for t in tri}) == len(tri), 'DUPLICATE_CELL')
        self.xy, self.tri = xy, tri
        require(len({tuple(p) for p in xy})==len(xy), 'DUPLICATE_MESH_VERTEX')
        require(np.max(np.abs(xy.min(axis=0))) <= COORD_ATOL and
                np.max(np.abs(xy.max(axis=0)-[period, height])) <= COORD_ATOL, 'RECTANGLE_BOUNDS')
        values = finite(solution['reconstructed_solution'])
        require(values.ndim == 1, 'SOLUTION_VECTOR_SHAPE')
        vi = indices(solution['velocity_reconstructed_dof_indices'])
        pi = indices(solution['pressure_reconstructed_dof_indices'])
        require(vi.ndim == pi.ndim == 1 and len(set(vi)) == len(vi) and len(set(pi)) == len(pi)
                and not set(vi)&set(pi) and set(vi)|set(pi) == set(range(len(values))), 'DOF_PARTITION')
        vc = finite(solution['velocity_dof_coordinates_hat'], (len(vi), 2))
        comp = indices(solution['velocity_dof_components'], (len(vi),))
        require(set(comp) == {0, 1}, 'VELOCITY_COMPONENTS')
        pc = finite(solution['pressure_coordinates_hat'], (len(pi), 2))
        require(np.array_equal(values[vi], finite(solution['velocity_reconstructed_values'], (len(vi),))), 'VELOCITY_COPY_MISMATCH')
        require(np.array_equal(values[pi], finite(solution['pressure_raw_P1'], (len(pi),))), 'PRESSURE_COPY_MISMATCH')
        cv = indices(system['cell_velocity_mixed_dofs'], (len(tri), 12))
        cp = indices(system['cell_pressure_mixed_dofs'], (len(tri), 3))
        vlookup = {int(i):(vc[k], int(comp[k])) for k,i in enumerate(vi)}
        plookup = {int(i):pc[k] for k,i in enumerate(pi)}
        self.cells = []
        edges = {}; pweights = np.zeros(len(values)); usedv=set(); usedp=set()
        for ci, t in enumerate(tri):
            v, det, _, _ = geometry(xy[t]); expected=nodes(v)
            require(len(set(cv[ci])) == 12 and len(set(cp[ci])) == 3, 'REPEATED_LOCAL_DOF')
            vn = np.full((6, 2), -1, dtype=int); pn = np.full(3, -1, dtype=int)
            for idx in cv[ci]:
                require(int(idx) in vlookup, 'CELL_VELOCITY_INDEX_KIND')
                pos, c = vlookup[int(idx)]
                matches = np.flatnonzero(np.max(np.abs(expected-pos), axis=1) <= COORD_ATOL)
                require(len(matches)==1 and vn[matches[0], c] == -1, 'P2_COORDINATE_MATCH')
                vn[matches[0], c] = idx
            for idx in cp[ci]:
                require(int(idx) in plookup, 'CELL_PRESSURE_INDEX_KIND')
                matches = np.flatnonzero(np.max(np.abs(v-plookup[int(idx)]), axis=1) <= COORD_ATOL)
                require(len(matches)==1 and pn[matches[0]] == -1, 'P1_COORDINATE_MATCH')
                pn[matches[0]] = idx
            require(np.all(vn>=0) and np.all(pn>=0), 'INCOMPLETE_CELL_MAP')
            usedv.update(vn.ravel());usedp.update(pn)
            pweights[pn] += det/6
            self.cells.append(dict(v=v, ids=vn, pids=pn, u=values[vn], p=values[pn]))
            for a,b in ((0,1),(1,2),(2,0)):
                key=tuple(sorted((int(t[a]),int(t[b]))))
                edges.setdefault(key,[]).append(ci)
        require(usedv==set(vi) and usedp==set(pi), 'UNUSED_DOF')
        require(all(len(e)<=2 for e in edges.values()), 'NONMANIFOLD_EDGE')
        self.boundaries=[]
        for (a,b), attached in edges.items():
            if len(attached)==1:
                v=xy[[a,b]]
                require(any(np.all(np.abs(v[:,axis]-value)<=COORD_ATOL)
                            for axis,value in ((0,0),(0,period),(1,0),(1,height))), 'INTERNAL_HOLE_OR_BAD_BOUNDARY')
                self.boundaries.append((v, attached[0]))
        # Each shared geometric P2 node must use the same scalar mixed DOF.
        seen={}; seen_pressure={}
        for cell in self.cells:
            for pos, ids in zip(nodes(cell['v']),cell['ids']):
                key=tuple(np.round(pos,12))
                require(key not in seen or np.array_equal(seen[key],ids), 'DISCONTINUOUS_SHARED_NODE')
                seen[key]=ids
            for pos, idx in zip(cell['v'],cell['pids']):
                key=tuple(np.round(pos,12))
                require(key not in seen_pressure or seen_pressure[key]==idx, 'DISCONTINUOUS_PRESSURE_NODE')
                seen_pressure[key]=idx
        self.area=fsum(geometry(c['v'])[1]/2 for c in self.cells)
        require(abs(self.area-period*height)<=2e-11, 'RECTANGLE_AREA')
        self.pressure_weights = pweights
        self.pmean=float(pweights@values/self.area)
        for c in self.cells:c['p0']=c['p']-self.pmean
        saved_weights=finite(solution['pressure_area_weights_hat2'],(len(pi),))
        require(np.allclose(saved_weights,pweights[pi],atol=FIXTURE_ATOL,rtol=FIXTURE_RTOL), 'PRESSURE_WEIGHT_MISMATCH')
        require(np.allclose(solution['pressure_zero_mean_P1'],values[pi]-self.pmean,
                            atol=FIXTURE_ATOL,rtol=FIXTURE_RTOL), 'PRESSURE_GAUGE_MISMATCH')

    def trace_report(self):
        """Check saved reconstruction/trace data without issuing geometry PASS."""
        s=self.s; value=finite(s['reconstructed_solution']);n=len(value)
        algebra=finite(s['algebraic_solution_before_backsub'],(n,))
        slave=indices(s['periodic_slave_dofs']);master=indices(s['periodic_master_dofs'],slave.shape)
        co=finite(s['periodic_coefficients'],slave.shape)
        require(slave.ndim==1 and len(set(slave))==len(slave) and not set(slave)&set(master),'CHAINED_OR_DUPLICATE_MPC')
        require(all(0<=i<n for i in list(slave)+list(master)) and np.all(co==1),'MPC_INDEX_OR_COEFFICIENT')
        expected=algebra.copy();expected[slave]=co*algebra[master]
        vi=indices(s['velocity_reconstructed_dof_indices']);vc=s['velocity_dof_coordinates_hat']
        pi=indices(s['pressure_reconstructed_dof_indices']);pc=s['pressure_coordinates_hat']
        comp=indices(s['velocity_dof_components']);coords={int(i):p for i,p in zip(vi,vc)}
        coords.update({int(i):p for i,p in zip(pi,pc)})
        kinds={int(i):int(c) for i,c in zip(vi,comp)};kinds.update({int(i):2 for i in pi})
        for si,ma in zip(slave,master):
            require(kinds[int(si)]==kinds[int(ma)],'PERIODIC_COMPONENT_MISMATCH')
            require(np.max(np.abs(coords[int(si)]-coords[int(ma)]-[self.period,0]))<=COORD_ATOL,'PERIODIC_COORDINATE_MISMATCH')
        wall=indices(s['wall_velocity_dof_indices'])
        require(wall.ndim==1 and set(wall)<=set(vi) and len(set(wall))==len(wall),'WALL_INDEX_KIND')
        expectedwall=set(vi[(np.abs(vc[:,1])<=COORD_ATOL)|(np.abs(vc[:,1]-1)<=COORD_ATOL)])
        expectedslave=set(vi[(np.abs(vc[:,0]-2)<=COORD_ATOL)&(vc[:,1]>COORD_ATOL)&(vc[:,1]<1-COORD_ATOL)])
        expectedslave.update(pi[np.abs(pc[:,0]-2)<=COORD_ATOL])
        uscale=float(np.max(np.abs(value[vi])));pscale=float(np.max(np.abs(value[pi])))
        return dict(reconstruction_max_abs=float(np.max(np.abs(value-expected))),
                    periodic_max_abs=float(np.max(np.abs(value[slave]-co*value[master]))) if len(slave) else None,
                    wall_max_abs=float(np.max(np.abs(value[wall]))) if len(wall) else None,
                    velocity_scale=uscale,pressure_scale=pscale,
                    wall_indices_complete=set(wall)==expectedwall,
                    periodic_slave_indices_complete=set(slave)==expectedslave,
                    recorded_wall_count=len(wall),expected_wall_count=len(expectedwall),
                    recorded_periodic_count=len(slave),expected_periodic_count=len(expectedslave),
                    classification='TRACE_DIAGNOSTIC_NOT_GEOMETRY_PASS')

    def integrate(self, kind='mms_mixed', order=8):
        packed=[]
        for c in self.cells:
            x,w=triangle_rule(c['v'],order)
            u,g,p,lam=evaluate(c['v'],c['u'],c['p0'],x)
            ue,pe,f=analytic(kind,x)
            packed.append((c,x,w,u,g,p,lam,ue,pe,f))
        exmean=fsum(float(w@pe) for _,_,w,_,_,_,_,_,pe,_ in packed)/self.area
        terms={k:[] for k in ('J_integral','D','Dsym','W','Pdiv','div_integral','div2','u_error2','u_exact2','p_error2','p_exact2')}
        weak=np.zeros(len(self.s['reconstructed_solution'])); cell_diag=[]
        for c,x,w,u,g,p,lam,ue,pe,f in packed:
            div=g[:,0,0]+g[:,1,1]; eps=(g+g.transpose(0,2,1))/2
            vals=dict(J_integral=u[:,0],D=np.sum(g*g,axis=(1,2)),Dsym=2*np.sum(eps*eps,axis=(1,2)),
                      W=np.sum(f*u,axis=1),Pdiv=p*div,div_integral=div,div2=div*div,
                      u_error2=np.sum((u-ue)**2,axis=1),u_exact2=np.sum(ue*ue,axis=1),
                      p_error2=(p-(pe-exmean))**2,p_exact2=(pe-exmean)**2)
            local={k:float(w@v) for k,v in vals.items()}
            for k,v in local.items():terms[k].append(v)
            weak[c['pids']] += lam.T@(w*div)
            cell_diag.append({k:local[k] for k in ('D','div_integral','div2')})
        out={k:fsum(v) for k,v in terms.items()}
        out.update(J_hat=out['J_integral']/self.period,pressure_mean_raw=self.pmean,
                   pressure_exact_mean=exmean,area=self.area,quadrature_points_per_duffy_axis=order,
                   u_L2_relative=np.sqrt(out['u_error2']/out['u_exact2']),
                   p_L2_relative=(np.sqrt(out['p_error2']/out['p_exact2']) if out['p_exact2']>0 else None))
        S=max(out['D'],abs(out['W']))
        valid=out['D']>0 and out['W']>0 and out['J_hat']>0
        out.update(positive_driven_field=valid,eta_div=np.sqrt(out['div2']/out['D']) if out['D']>0 else None,
                   eta_energy_weak=abs(out['D']-out['Pdiv']-out['W'])/S if S>0 else None,
                   eta_pressure_work=abs(out['Pdiv'])/S if S>0 else None,
                   eta_energy_direct=abs(out['D']-out['W'])/S if S>0 else None,
                   symmetric_gradient_identity_defect=out['Dsym']-out['D']-out['div2'],
                   J_exact=1/12 if kind=='flat_mixed' else 1/6,
                   J_absolute_error=abs(out['J_hat']-(1/12 if kind=='flat_mixed' else 1/6)),
                   weak_pressure_moments_unconstrained=weak.tolist(),cell_diagnostics=cell_diag,
                   classification='METRICS_ONLY_NO_PHYSICAL_PASS',reference_qualified=False)
        return out

    def section(self, x):
        require(0 < x < self.period, 'SECTION_OUTSIDE_INTERIOR')
        intervals=[]
        for i,c in enumerate(self.cells):
            v=c['v']; zs=[]
            for a,b in ((0,1),(1,2),(2,0)):
                va,vb=v[a],v[b]
                if abs(va[0]-x)<=COORD_ATOL:zs.append(float(va[1]))
                if (va[0]-x)*(vb[0]-x)<0:
                    zs.append(float(va[1]+(x-va[0])*(vb[1]-va[1])/(vb[0]-va[0])))
            if len(zs)>1 and max(zs)-min(zs)>COORD_ATOL:
                intervals.append((min(zs),max(zs),i))
        knots=sorted({round(z,14) for a,b,_ in intervals for z in (a,b)})
        require(knots and abs(knots[0])<=COORD_ATOL and abs(knots[-1]-self.height)<=COORD_ATOL,'SECTION_COVERAGE')
        g,w=np.polynomial.legendre.leggauss(3);parts=[]
        for a,b in zip(knots[:-1],knots[1:]):
            if b-a<=COORD_ATOL:continue
            mid=(a+b)/2; candidates=[i for lo,hi,i in intervals if lo-COORD_ATOL<mid<hi+COORD_ATOL]
            require(1<=len(candidates)<=2,'SECTION_OVERLAP_OR_GAP')
            pos=np.column_stack((np.full(3,x),mid+(b-a)*g/2))
            samples=[]
            for i in candidates:
                c=self.cells[i];lam=barycentric(c['v'],pos)
                require(np.min(lam)>=-COORD_ATOL,'SECTION_CELL_MISMATCH')
                if len(candidates)>1:require(np.all(np.min(np.abs(lam),axis=1)<COORD_ATOL),'OVERLAPPING_CELL_INTERIORS')
                samples.append(evaluate(c['v'],c['u'],c['p0'],pos)[0][:,0])
            require(all(np.allclose(samples[0],q,atol=FIXTURE_ATOL,rtol=FIXTURE_RTOL) for q in samples),'DISCONTINUOUS_SECTION_TRACE')
            parts.append(float(w@samples[0]*(b-a)/2))
        return fsum(parts)

    def slab_divergence(self, left, right):
        require(0<=left<right<=self.period,'SLAB_INTERVAL')
        values=[]
        for c in self.cells:
            polygon=[p.copy() for p in c['v']]
            for wall,sign in ((left,1),(right,-1)):
                clipped=[]
                for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                    ina=sign*(a[0]-wall)>=0;inb=sign*(b[0]-wall)>=0
                    if ina:clipped.append(a)
                    if ina!=inb:
                        clipped.append(a+(b-a)*(wall-a[0])/(b[0]-a[0]))
                polygon=clipped
                if len(polygon)<3:break
            for k in range(1,len(polygon)-1):
                v=np.array([polygon[0],polygon[k],polygon[k+1]])
                va,vb=v[1]-v[0],v[2]-v[0]
                if abs(va[0]*vb[1]-va[1]*vb[0])<1e-15:continue
                x,w=triangle_rule(v,3);_,g,_,_=evaluate(c['v'],c['u'],c['p0'],x)
                values.append(float(w@(g[:,0,0]+g[:,1,1])))
        return fsum(values)

    def slab_wall_flux(self,left,right):
        values=[];g,w=np.polynomial.legendre.leggauss(3)
        for edge,i in self.boundaries:
            if abs(edge[0,1]-edge[1,1])>COORD_ATOL:continue
            z=float(edge[0,1]);sign=-1 if abs(z)<COORD_ATOL else 1
            a=max(left,min(edge[:,0]));b=min(right,max(edge[:,0]))
            if b<=a:continue
            pos=np.column_stack(((a+b)/2+(b-a)*g/2,np.full(3,z)))
            c=self.cells[i];u=evaluate(c['v'],c['u'],c['p0'],pos)[0]
            values.append(float(w@u[:,1]*(b-a)/2*sign))
        return fsum(values)

    def flux_report(self,J):
        xs=[self.period*k/8 for k in range(1,8)];qs=[self.section(x) for x in xs]
        slabs=[]
        for a,b,qa,qb in zip(xs[:-1],xs[1:],qs[:-1],qs[1:]):
            div=self.slab_divergence(a,b);wall=self.slab_wall_flux(a,b)
            slabs.append(dict(left=a,right=b,div_integral=div,wall_flux=wall,
                              theorem_defect=qb-qa+wall-div))
        return dict(x=xs,q=qs,eta_q=max(abs(q-J) for q in qs)/abs(J) if J>0 else None,
                    sampled_sections_only=True,slabs=slabs)

    def weak_residual(self,moments):
        s,a=self.s,self.sys
        x=finite(s['algebraic_solution_before_backsub']);n=len(x)
        b=finite(a['rhs_after'],(n,));ptr=indices(a['csr_indptr'],(n+1,))
        col=indices(a['csr_indices']);val=finite(a['csr_values'],col.shape)
        require(ptr[0]==0 and ptr[-1]==len(col) and np.all(np.diff(ptr)>=0) and
                (len(col)==0 or (col.min()>=0 and col.max()<n)), 'CSR_INVALID')
        require(np.linalg.norm(b)>0,'ZERO_RHS_DENOMINATOR')
        r=np.array([b[i]-fsum(float(val[k]*x[col[k]]) for k in range(ptr[i],ptr[i+1])) for i in range(n)])
        slave=indices(s['periodic_slave_dofs']);master=indices(s['periodic_master_dofs'],slave.shape)
        coeff=finite(s['periodic_coefficients'],slave.shape)
        require(len(set(slave))==len(slave) and not set(slave)&set(master),'CHAINED_OR_DUPLICATE_MPC')
        require(np.all(coeff==1),'ONLY_UNIT_PERIODIC_COEFFICIENT_SUPPORTED')
        require(all(0<=i<n for i in list(slave)+list(master)),'MPC_INDEX_RANGE')
        ps=set(indices(s['pressure_reconstructed_dof_indices'])); c=finite(moments,(n,)).copy()
        for si,ma,co in zip(slave,master,coeff):
            require((int(si) in ps)==(int(ma) in ps),'MPC_COMPONENT_KIND_MISMATCH')
            if int(si) in ps:c[ma]+=co*c[si];c[si]=0
        rows=np.array(sorted(ps-set(slave)),dtype=int)
        require(np.max(np.abs(b[rows]))<=1e-14,'NONZERO_CONTINUITY_RHS')
        norm=float(np.linalg.norm(b))
        return dict(eta_all=float(np.linalg.norm(r)/norm),eta_c=float(np.linalg.norm(r[rows])/norm),
                    independent_c_vs_matrix_residual=float(np.linalg.norm(c[rows]-r[rows])/norm),
                    pressure_rows=rows.tolist(),pressure_moments_aggregated=c[rows].tolist(),
                    rhs_norm=norm,classification='ALGEBRAIC_DIAGNOSTIC_NOT_ACCURACY_BOUND')
