"""Read only named, previously accepted development end states; no solver.

2D high-precision derivatives are allowed only after checking full 3D y
invariance and matching its central slice. All energy mismatches are retained.
"""
from pathlib import Path
import base64, csv, hashlib, json, math, struct, zlib
import xml.etree.ElementTree as ET
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
REP=ROOT/'docs/reports'
protected={}
def bind(p):
    p=Path(p).resolve()
    assert '/results/prediction' not in str(p) and '/held' not in str(p)
    d=hashlib.sha256(p.read_bytes()).hexdigest()
    if str(p) in protected: assert protected[str(p)]==d
    protected[str(p)]=d
    return p
def kv(p): return dict(x.split('=',1) for x in bind(p).read_text().splitlines() if '=' in x)
def rows(p):
    with bind(p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def dump(n,o): (OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(n,rr):
    with (OUT/n).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def decode(node,n):
    assert node.attrib['type']=='Float32' and node.attrib['format']=='binary'
    s=''.join(node.text.split());nb=struct.unpack('<I',base64.b64decode(s[:8])[:4])[0]
    hc=4*math.ceil(4*(3+nb)/3)
    hd=struct.unpack('<'+'I'*(3+nb),base64.b64decode(s[:hc]))
    compressed=base64.b64decode(s[hc:]);assert len(compressed)==sum(hd[3:])
    blocks=[];offset=0
    for size in hd[3:]:
        blocks.append(zlib.decompress(compressed[offset:offset+size]));offset+=size
    data=b''.join(blocks);nc=int(node.attrib['NumberOfComponents'])
    assert len(data)==hd[1]*(nb-1)+hd[2]==n*nc*4
    return np.frombuffer(data,dtype='<f4').reshape(n,nc)

def deriv(v,mask,axis,dx,scheme):
    """v[z,x,component]; wall at half a cell; x periodic only."""
    prev=np.roll(v,1,axis=axis);nxt=np.roll(v,-1,axis=axis)
    mp=np.roll(mask,1,axis=axis);mn=np.roll(mask,-1,axis=axis)
    if axis==0:mp[0]=False;mn[-1]=False
    both=mask&mp&mn;lo=mask&~mp&mn;hi=mask&mp&~mn
    assert np.all((both|lo|hi)[mask]),'isolated stencil: no silent fallback'
    result=np.zeros_like(v)
    result[both]=(nxt[both]-prev[both])/(2*dx)
    if scheme=='wall_quadratic':
        result[lo]=(v[lo]+nxt[lo]/3)/dx
        result[hi]=-(v[hi]+prev[hi]/3)/dx
    else:
        assert scheme=='odd_extension'
        result[lo]=(nxt[lo]+v[lo])/(2*dx)
        result[hi]=-(v[hi]+prev[hi])/(2*dx)
    return result,both

def components(v,mask,dx,mu,scheme):
    gx,ix=deriv(v,mask,1,dx,scheme);gz,iz=deriv(v,mask,0,dx,scheme)
    # y derivative has been checked separately from the complete saved field.
    c={'normal_x':2*mu*gx[:,:,0]**2,'normal_y':np.zeros(mask.shape),
       'normal_z':2*mu*gz[:,:,2]**2,'shear_xy':mu*gx[:,:,1]**2,
       'shear_yz':mu*gz[:,:,1]**2,'shear_xz':mu*(gz[:,:,0]+gx[:,:,2])**2}
    phi=sum(c.values());grad=mu*(np.sum(gx*gx,axis=2)+np.sum(gz*gz,axis=2))
    return c,phi,grad,gx,gz,ix&iz

def test_operators():
    # Manufactured parallel plate profile: exact derivatives for quadratic
    # near-wall stencils and central interior, no Stokes solver invocation.
    dx=.25;nx=12;nz=20;H=nz*dx
    z=(np.arange(nz)+.5)*dx;mask=np.ones((nz,nx),bool)
    v=np.zeros((nz,nx,3));v[:,:,1]=(z*(H-z))[:,None]
    gz,_=deriv(v,mask,0,dx,'wall_quadratic');gx,_=deriv(v,mask,1,dx,'wall_quadratic')
    e=float(np.max(np.abs(gz[:,:,1]-(H-2*z)[:,None])))
    assert e<1e-12 and np.max(np.abs(gx))==0
    c,phi,grad,*_=components(v,mask,dx,.001,'wall_quadratic')
    assert np.allclose(phi,grad,rtol=1e-14,atol=0)
    assert np.allclose(c['shear_yz'],.001*(H-2*z[:,None])**2)
    # Six-term algebra against explicit 3x3 symmetrisation, arbitrary gradients.
    g=np.random.default_rng(901).normal(size=(300,3,3));D=(g+g.swapaxes(1,2))/2
    explicit=2*np.sum(D*D,axis=(1,2))
    expanded=2*np.sum(np.diagonal(g,axis1=1,axis2=2)**2,axis=1)
    for i,j in [(0,1),(0,2),(1,2)]:expanded+=(g[:,i,j]+g[:,j,i])**2
    algebra=float(np.max(np.abs(explicit-expanded)));assert algebra<3e-14
    return {'manufactured_quadratic_derivative_max_abs':e,'six_term_algebra_max_abs':algebra,
            'tests_are_postprocessor_checks_not_simulation_acceptance':True}

def region_masks(x,z,H,h,d,w,P,r):
    a=(P-w)/2;b=(P+w)/2
    dist_corner=np.minimum.reduce([np.hypot(x-xx,z-zz) for xx in (a,b) for zz in (h,h+d)])
    zdist=np.maximum(np.maximum(h-z,0),z-(h+d))
    dist_vertical=np.minimum(np.hypot(x-a,zdist),np.hypot(x-b,zdist))
    corner=dist_corner<=r
    vertical=(dist_vertical<=r)&~corner
    horizontal=(np.minimum(z,np.abs(H-z))<=r)&~corner&~vertical
    bulk=~(corner|vertical|horizontal)
    return {'corner_neighborhood':corner,'vertical_wall_band':vertical,
            'horizontal_wall_band':horizontal,'remaining_interior':bulk}

tests=test_operators();dump('operator_checks.json',tests)
bind(Path(__file__))
plan=bind(OUT/'DIAGNOSTIC_PLAN.md')
for p in [REP/'SIM240_中文稿_导师审阅版_20261022.md',REP/'SIM240_First_Paper_English_20261028.md',
          ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/src/variable_groove_transport.cpp',
          Path('/home/dell/openlb/src/functors/lattice/latticePhysDissipation3D.hh')]:bind(p)
old=json.loads(bind(REP/'PAPER1_scale_failure_audit_20261108/source_manifest.json').read_text())
certs=[REP/'D4_remaining14_acceptance_20261024/scalar_acceptance/flow_files_sha256.json',
       REP/'D4_prediction_readiness_20261024/screen_acceptance/flow_files_sha256.json',
       REP/'D4_grid_mid6_acceptance_20261024/independent/analysis/flow_files_sha256.json',
       REP/'D4_grid_narrow_fine4_acceptance_20261025/independent/analysis/flow_files_sha256.json',
       REP/'D4_foundation_acceptance_20261023/complete/flow_files_sha256.json']
expected_fields={}
for p in certs:expected_fields.update(json.loads(bind(p).read_text()))
selection=[r for r in rows(REP/'PAPER1_scale_failure_audit_20261108/scalar_records.csv')
           if r['role'].startswith('D4') and (float(r['d_nm'])==120 or r['role']=='D4_smooth_control')]
assert len(selection)==12 and sum(float(r['d_nm'])==120 for r in selection)==10
power=[];parts=[];regions=[];identities=[];field_checks=[]
for item in selection:
    run=(ROOT/item['source']).parent;r=kv(run/'result.txt');manifest=kv(run/'run_manifest.txt')
    assert int(bind(run/'exit_code.txt').read_text())==0
    dx,h,d,w,P,Ly,mu,rho,a,J=[float(r[k]) for k in ['dx_m','mesa_gap_m','groove_depth_m','groove_width_m','Lx_m','Ly_m','mu_phys_Pa_s','rho_phys_kg_m3','acceleration_m_s2','J_main_m2_s']]
    nx,ny,nz=round(P/dx),round(Ly/dx),round((h+d)/dx)
    masters=list((run/'vtkData').glob('*.pvd'));assert len(masters)==1
    master=bind(masters[0]);entries=list(ET.parse(master).getroot().iter('DataSet'))
    last=entries[-1];assert int(last.attrib['timestep'])==int(r['steps_completed'])
    vtm=bind(master.parent/last.attrib['file']);children=list(ET.parse(vtm).getroot().iter('DataSet'));assert len(children)==1
    vti=bind(vtm.parent/children[0].attrib['file'])
    for p in (vtm,vti):assert str(p) in expected_fields and protected[str(p)]==expected_fields[str(p)],str(p)
    tree=ET.parse(vti).getroot();assert tree.attrib['compressor']=='vtkZLibDataCompressor' and tree.attrib['byte_order']=='LittleEndian'
    img=tree.find('ImageData');piece=img.find('Piece');ex=list(map(int,piece.attrib['Extent'].split()))
    dims=[ex[2*i+1]-ex[2*i]+1 for i in range(3)];origin=np.array(list(map(float,img.attrib['Origin'].split())))
    spacing=np.array(list(map(float,img.attrib['Spacing'].split())));assert np.allclose(spacing,dx,rtol=1e-12,atol=0)
    coords=[origin[i]+np.arange(ex[2*i],ex[2*i+1]+1)*dx for i in range(3)]
    lengths=[P,Ly,h+d];ids=[np.flatnonzero((v>=0)&(v<lengths[i])) for i,v in enumerate(coords)]
    assert [len(v) for v in ids]==[nx,ny,nz]
    nodes=math.prod(dims);data={n.attrib['Name']:decode(n,nodes) for n in piece.find('PointData')}
    pick=np.ix_(ids[2],ids[1],ids[0])
    mat=data['material'][:,0].reshape(dims[::-1])[pick]
    vv=data['velocity_m_s'].reshape((*dims[::-1],3))[pick]
    pp=data['pressure_Pa'][:,0].reshape(dims[::-1])[pick]
    ee=data['dissipation_m2_s3'][:,0].reshape(dims[::-1])[pick]
    x=(np.arange(nx)+.5)*dx;z=(np.arange(nz)+.5)*dx
    height=h+d*((x>=(P-w)/2)&(x<(P+w)/2))
    mask=z[:,None]<height[None,:];m3=np.broadcast_to(mask[:,None,:],mat.shape)
    assert np.array_equal(mat==1,m3) and int(m3.sum())==int(r['fluid_nodes'])
    assert np.all(np.isfinite(vv[m3])) and np.all(np.isfinite(pp[m3])) and np.all(np.isfinite(ee[m3])) and np.min(ee[m3])>=0
    flux=vv[m3].astype(float).sum(axis=0)*dx**3/(P*Ly)
    target=np.array([float(v) for v in r['J_vector_m2_s'].split(',')])
    vel=vv[m3]; ulp=np.maximum(np.nextafter(vel,np.float32(np.inf)).astype(float)-vel.astype(float),vel.astype(float)-np.nextafter(vel,np.float32(-np.inf)).astype(float))
    bound=.5*ulp.sum(axis=0)*dx**3/(P*Ly)+1e-13*np.abs(target)+1e-30
    assert np.all(np.abs(flux-target)<=bound)
    cut=rows(run/'field_slice.csv');assert len(cut)==int(mask.sum())
    v=np.zeros((nz,nx,3));saved=np.zeros((nz,nx));seen=np.zeros_like(mask)
    for line in cut:
        ix,iz=round(float(line['x'])/dx-.5),round(float(line['z'])/dx-.5)
        assert mask[iz,ix] and not seen[iz,ix];seen[iz,ix]=True
        v[iz,ix]=[float(line[k]) for k in ['ux','uy','uz']];saved[iz,ix]=float(line['Phi'])
    assert np.array_equal(seen,mask)
    assert np.array_equal(v[mask].astype(np.float32),vv[:,ny//2,:,:][mask])
    vmax=float(np.max(np.linalg.norm(v[mask],axis=1)))
    yrange=np.ptp(vv.astype(float),axis=1);yvariation=float(np.max(np.abs(yrange[mask])))/vmax
    dy=(np.roll(vv.astype(float),-1,axis=1)-np.roll(vv.astype(float),1,axis=1))/(2*dx)
    ygrad_power=mu*float(np.sum(dy[m3]**2))*dx**3
    pin=rho*a*J*P*Ly;ypower_ratio=ygrad_power/pin
    # These are disclosed reduction checks, not new scientific Gate criteria.
    assert yvariation<1e-6 and ypower_ratio<1e-10,(yvariation,ypower_ratio)
    saved_vtk=rho*float(ee[m3].astype(float).sum())*dx**3
    saved_cut=float(saved[mask].sum())*dx**2*Ly
    sbound=rho*.5*np.abs(np.spacing(ee[m3]).astype(float)).sum()*dx**3+1e-13*saved_cut
    assert abs(saved_vtk-saved_cut)<=sbound
    lcp=(h**3+(h+d)**3)/24;lct=h**3*(h+d)**3/(6*(h**3+(h+d)**3));lc=lcp if item['direction']=='P' else lct
    rlc=mu/lc;rdrive=rho*a/J;vol=dx**2*Ly
    q_profile=v[:,:,0].sum(axis=0)*dx/J
    fbase=dict(run_id=item['run_id'],direction=item['direction'],h_nm=h*1e9,d_nm=d*1e9,w_nm=w*1e9,dx_nm=dx*1e9)
    field_checks.append(dict(**fbase,step=int(r['steps_completed']),fluid_nodes=int(m3.sum()),
        VTM_and_payload_match_prior_acceptance=True,field_J_max_absolute_difference=float(np.max(np.abs(flux-target))),
        CSV_slice_matches_Float32_field=True,y_variation_relative_to_umax=yvariation,y_gradient_power_over_input=ypower_ratio,
        saved_Phi_cut_vs_3D_relative_difference=saved_cut/saved_vtk-1,
        transverse_q_over_J_min=float(q_profile.min()) if item['direction']=='T' else None,
        transverse_q_over_J_max=float(q_profile.max()) if item['direction']=='T' else None,
        source_vtm=str(vtm.relative_to(ROOT))))
    for scheme in ('wall_quadratic','odd_extension'):
        c,phi,grad,gx,gz,interior=components(v,mask,dx,mu,scheme)
        pg=float(phi[mask].sum())*vol;gg=float(grad[mask].sum())*vol
        div=gx[:,:,0]+gz[:,:,2]
        divnorm=float(np.sqrt(np.sum(div[mask]**2)/(np.sum(gx[mask]**2)+np.sum(gz[mask]**2))))
        power.append(dict(**fbase,scheme=scheme,input_W=pin,saved_moment_W=saved_cut,strain_W=pg,gradient_W=gg,
            strain_input_residual_percent=100*(pg/pin-1),strain_saved_residual_percent=100*(pg/saved_cut-1),
            grad_strain_relative_difference_percent=100*(gg/pg-1),normalized_divergence_L2=divnorm,
            R_drive_over_R_LC=rdrive/rlc,R_strain_over_R_LC=pg/(P*Ly*J**2*rlc),
            saved_moment_input_residual_percent=100*(saved_cut/pin-1)))
        for name,arr in c.items():
            pi=float(arr[mask].sum())*vol
            parts.append(dict(**fbase,scheme=scheme,component=name,power_W=pi,fraction_of_strain=pi/pg,
                              R_component_over_R_LC=pi/(P*Ly*J**2*rlc)))
        xx,zz=np.meshgrid(x,z);HH=np.broadcast_to(height,mask.shape)
        # Same-J local parabolic reference; discontinuous across steps in x.
        if item['direction']=='P':bder=(HH-2*zz)/(2*lc)
        else:bder=6*(HH-2*zz)/HH**3
        main=1 if item['direction']=='P' else 0
        deformation=mu*(gz[:,:,main]/J-bder)**2
        if item['direction']=='P':extra={'transverse_gradient':mu*(gx[:,:,1]/J)**2}
        else:extra={'axial_gradient':mu*(gx[:,:,0]/J)**2,'vertical_velocity_gradient':mu*((gx[:,:,2]/J)**2+(gz[:,:,2]/J)**2)}
        excess_parts={'profile_departure':deformation,**extra}
        vals={name:float(ar[mask].sum())*dx**2/P/rlc for name,ar in excess_parts.items()}
        identity_sum=sum(vals.values());excess_drive=rdrive/rlc-1;excess_grad=gg/(P*Ly*J**2*rlc)-1
        for name,value in vals.items():
            identities.append(dict(**fbase,scheme=scheme,term=name,R_excess_term_over_R_LC=value,
                term_fraction_of_positive_sum=value/identity_sum if identity_sum else 0,
                sum_terms_over_R_LC=identity_sum,drive_excess_over_R_LC=excess_drive,
                grad_excess_over_R_LC=excess_grad,identity_sum_minus_grad_excess=identity_sum-excess_grad))
        for frac in ((1/8,1/4,1/2) if d>0 else ()):
            masks=region_masks(xx,zz,HH,h,d,w,P,frac*h)
            assert np.all(sum((ar&mask).astype(int) for ar in masks.values())[mask]==1)
            for name,ar in masks.items():
                sel=ar&mask;pi=float(phi[sel].sum())*vol;ps=float(saved[sel].sum())*vol
                regions.append(dict(**fbase,scheme=scheme,r_over_h=frac,region=name,
                    fluid_volume_fraction=float(sel.sum()/mask.sum()),strain_power_fraction=pi/pg,
                    saved_power_fraction=ps/saved_cut,R_region_over_R_LC=pi/(P*Ly*J**2*rlc)))
    # Store only small analysis products, never an altered field.
    print(json.dumps({'run_id':item['run_id'],'w_nm':w*1e9,'dx_nm':dx*1e9,'direction':item['direction'],
                      'yvariation':yvariation,'ypower_ratio':ypower_ratio}),flush=True)
    del data,mat,vv,pp,ee,dy,vel,ulp

table('field_checks.csv',field_checks);table('power_checks.csv',power);table('strain_components.csv',parts)
table('spatial_regions.csv',regions);table('positive_excess_diagnostic.csv',identities)
dump('source_manifest.json',protected)
changed=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
assert not changed,changed
old_drift=[p for p,h in old.items() if p in protected and protected[p]!=h]
assert not old_drift,old_drift
dump('verification.json',{'source_count':len(protected),'changed_inputs':changed,'overlap_with_previous_manifest_unchanged':True,
                         'full_fields_read':len(field_checks),'formal_gate_changed':False,'solver_calls':0,'fit_calls':0,
                         'reserved_prediction_results_read':False,'new_run_id':None,'human_final_approval':False})
print(json.dumps({'completed':True,'frames':len(field_checks),'source_count':len(protected)},ensure_ascii=False),flush=True)
