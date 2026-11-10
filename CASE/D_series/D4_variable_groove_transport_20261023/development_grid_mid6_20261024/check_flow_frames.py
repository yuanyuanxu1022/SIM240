#!/usr/bin/env pvpython
"""Read every completed VTM frame, compare Float32 field integrals with raw CSV."""
from pathlib import Path
import argparse,csv,hashlib,json,re
import xml.etree.ElementTree as ET
import numpy as np
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--analysis',type=Path,required=True);a=ap.parse_args()
    cases=json.loads((a.analysis/'field_cases.json').read_text());records=[];hashes={}
    for case in cases:
        out=Path(case['output']);cfg=case['effective'];row=case['row'];dx=float(cfg['dx_m'])
        lengths=np.array([float(cfg['Lx_m']),float(cfg['Ly_m']),float(cfg['h_m'])+float(cfg['d_m'])])
        area=lengths[0]*lengths[1];factor=dx**3/area
        expected_nodes=round((lengths[0]*lengths[1]*float(cfg['h_m'])+float(cfg['w_m'])*lengths[1]*float(cfg['d_m']))/dx**3)
        frames=case['frames'];expected_steps=[int(r['step']) for r in frames]
        frame_steps_set=set(expected_steps)
        assert expected_nodes<=1990656,'this bounded reader is limited to the current MID6 maximum mesh'
        diagnostics={int(r['step']):r for r in csv.DictReader((out/'diagnostics.csv').open()) if int(r['step']) in frame_steps_set}
        roots={int(re.search(r'iT(\d+)\.vtm$',str(p)).group(1)):p for p in (out/'vtkData').rglob('*iT*.vtm')}
        assert set(roots)==set(expected_steps)
        # Traverse all XML roots too: no dangling PVD/master references.
        visited=set()
        def walk(file):
            file=file.resolve();assert out.resolve() in file.parents
            if file in visited:return
            visited.add(file);hashes[str(file)]=sha(file)
            if file.suffix in ['.vtm','.pvd']:
                for entry in ET.parse(file).getroot().iter():
                    if 'file' in entry.attrib:walk(file.parent/entry.attrib['file'])
        for p in (out/'vtkData').rglob('*'):
            if p.suffix in ['.vtm','.pvd']:walk(p)
        baseline_coordinates=None
        for step in expected_steps:
            reader=vtkXMLMultiBlockDataReader();reader.SetFileName(str(roots[step]));reader.Update()
            it=reader.GetOutput().NewIterator();it.SkipEmptyNodesOn();it.InitTraversal()
            coordinates=[];velocities=[];pressure=[];dissipation=[]
            while not it.IsDoneWithTraversal():
                data=it.GetCurrentDataObject();it.GoToNextItem()
                if not data.IsA('vtkImageData'):continue
                arrays={name:vtk_to_numpy(data.GetPointData().GetArray(name)) for name in ['material','velocity_m_s','pressure_Pa','dissipation_m2_s3']}
                assert all(v.dtype==np.dtype('float32') for v in arrays.values())
                n=data.GetNumberOfPoints();ex=data.GetExtent();shape=[ex[2*i+1]-ex[2*i]+1 for i in range(3)]
                ix=np.arange(n);ijk=[ix%shape[0],(ix//shape[0])%shape[1],ix//(shape[0]*shape[1])]
                xyz=np.array([data.GetOrigin()[i]+(ex[2*i]+ijk[i])*data.GetSpacing()[i] for i in range(3)]).T
                mask=arrays['material']==1
                for i in range(3):mask&=(xyz[:,i]>=0)&(xyz[:,i]<lengths[i])
                for v in arrays.values():assert np.isfinite(v[mask]).all()
                coordinates.append(np.rint(xyz[mask]/dx-.5).astype(np.int64))
                velocities.append(arrays['velocity_m_s'][mask]);pressure.append(arrays['pressure_Pa'][mask]);dissipation.append(arrays['dissipation_m2_s3'][mask])
            xyz=np.concatenate(coordinates);v=np.concatenate(velocities);p=np.concatenate(pressure);phi=np.concatenate(dissipation)
            assert len(xyz)==expected_nodes and len(np.unique(xyz,axis=0))==expected_nodes
            nx,ny,nh,nd=[round(float(cfg[k])/dx) for k in ['Lx_m','Ly_m','h_m','d_m']]
            edge=(float(cfg['Lx_m'])-float(cfg['w_m']))/(2*dx)
            assert np.all((xyz>=0)&(xyz<np.array([nx,ny,nh+nd])))
            height=nh+nd*((xyz[:,0]+.5>=edge)&(xyz[:,0]+.5<nx-edge))
            assert np.all(xyz[:,2]+.5<height)  # unique count then establishes complete intended fluid set
            order=np.lexsort(xyz.T[::-1]);xyz=xyz[order];v=v[order];p=p[order];phi=phi[order]
            if baseline_coordinates is None:baseline_coordinates=xyz
            else:assert np.array_equal(xyz,baseline_coordinates)
            assert phi.min()>=0
            field_flux=v.astype(np.float64).sum(axis=0)*factor
            csv_flux=np.array([float(diagnostics[step][k]) for k in ['Jx','Jy','Jz']])
            # Each serialized component rounded to nearest Float32. Bound half-ULP
            # plus conservative double summation error for both integrations.
            up=np.nextafter(v,np.float32(np.inf));down=np.nextafter(v,np.float32(-np.inf))
            rounding=.5*np.maximum(up.astype(float)-v.astype(float),v.astype(float)-down.astype(float)).sum(axis=0)*factor
            eps=np.finfo(float).eps;gamma=(2*expected_nodes*eps)/(1-2*expected_nodes*eps)
            arithmetic=gamma*np.abs(v.astype(float)).sum(axis=0)*factor
            bound=rounding+arithmetic+np.finfo(float).tiny
            diff=np.abs(field_flux-csv_flux);assert np.all(diff<=bound),(row['run_id'],step,diff.tolist(),bound.tolist())
            if step==expected_steps[-1]:
                slice_rows=list(csv.DictReader((out/'field_slice.csv').open()))
                y_index=round(lengths[1]/dx)//2
                sel=xyz[:,1]==y_index;sv=v[sel];sx=xyz[sel]
                mapping={(int(x),int(z)):k for k,(x,y,z) in enumerate(sx)}
                assert len(slice_rows)==len(mapping)
                ids=[mapping[(round(float(r['x'])/dx-.5),round(float(r['z'])/dx-.5))] for r in slice_rows]
                expected_v=np.array([[float(r[k]) for k in ['ux','uy','uz']] for r in slice_rows],dtype=np.float32)
                assert np.array_equal(sv[ids],expected_v)
            reader.SetFileName('')
            main=1 if row['direction']=='P' else 0
            records.append({'run_id':row['run_id'],'step':step,'fluid_points':expected_nodes,
                'field_flux_m2_s':field_flux.tolist(),'csv_flux_m2_s':csv_flux.tolist(),
                'main_relative_difference':float(diff[main]/abs(csv_flux[main])),
                'component_absolute_difference':diff.tolist(),'Float32_rounding_and_sum_bound':bound.tolist(),
                'pressure_min_Pa':float(p.min()),'pressure_max_Pa':float(p.max()),
                'dissipation_min_m2_s3':float(phi.min()),'dissipation_max_m2_s3':float(phi.max())})
    result={'ok':True,'cases':len(cases),'frames_read':len(records),'all_payloads_finite':True,
       'material_points_unchanged':True,'frame_flux_matches_csv_within_Float32_serialization_bound':True,
       'final_fields_match_double_csv_after_Float32_rounding':True,
       'max_main_relative_flux_difference':max(r['main_relative_difference'] for r in records),
       'unique_referenced_files':len(hashes),'referenced_bytes':sum(Path(p).stat().st_size for p in hashes),
       'vtk_version':__import__('vtkmodules.vtkCommonCore',fromlist=['vtkVersion']).vtkVersion.GetVTKVersion(),
       'pressure_definition':'periodic pressure perturbation, not imposed macroscopic pressure drop',
       'dissipation_definition':'kinematic dissipation m2/s3, not W/m3','records':records}
    (a.analysis/'flow_frames.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    (a.analysis/'flow_files_sha256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2))
    assert all(sha(Path(p))==h for p,h in hashes.items())
    print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
