#!/usr/bin/env pvpython
"""Read existing VTK and integrate valid core-fluid points; no solver or rendering."""
from pathlib import Path
import csv
import gc
import hashlib
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

OUT=Path(__file__).resolve().parent
INPUTS={}
def sha(p):
    p=Path(p).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    INPUTS[str(p)]=h.hexdigest()
    return h.hexdigest()
def kv(p):
    sha(p);return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
def references(p):
    p=Path(p).resolve();sha(p)
    if p.suffix in ['.vtm','.pvd']:
        for node in ET.parse(p).getroot().iter('DataSet'):
            if 'file' in node.attrib:references(p.parent/node.attrib['file'])
def leaves(data):
    it=data.NewIterator();it.SkipEmptyNodesOn();it.InitTraversal()
    while not it.IsDoneWithTraversal():
        obj=it.GetCurrentDataObject()
        if obj is not None and obj.IsA('vtkImageData'):yield obj
        it.GoToNextItem()

def main():
    p=OUT/'field_readers.json';sha(p);readers=json.loads(p.read_text());records=[]
    for rec in readers:
        folder=Path(rec['result_directory']);r=kv(folder/'result.txt')
        dx=rec['dx_nm']*1e-9;nx=round(240e-9/dx);ny=nx
        pvd=Path(rec['reader']);sha(pvd);datasets=list(ET.parse(pvd).getroot().iter('DataSet'))
        selected=[node for node in datasets if int(float(node.attrib['timestep']))==rec['final_step']]
        if 'fine_t_C_' in str(folder):selected=[datasets[0]]+selected
        assert len(selected)==(2 if 'fine_t_C_' in str(folder) else 1)
        for ds in selected:
            step=int(float(ds.attrib['timestep']));vtm=pvd.parent/ds.attrib['file'];references(vtm)
            reader=vtk.vtkXMLMultiBlockDataReader();reader.SetFileName(str(vtm));reader.Update()
            assert reader.GetErrorCode()==0
            sums=np.zeros(3);bounds=np.zeros(3);allids=[];arrays=None;fluid_count=0
            for image in leaves(reader.GetOutput()):
                dims=image.GetDimensions();ext=image.GetExtent();origin=image.GetOrigin();spacing=image.GetSpacing()
                assert all(abs(abs(s)/dx-1)<1e-10 for s in spacing)
                point=image.GetPointData();arrays=[point.GetArrayName(i) for i in range(point.GetNumberOfArrays())]
                for name in ['material','velocity_m_s','pressure_Pa','dissipation_m2_s3']:assert name in arrays
                material=vtk_to_numpy(point.GetArray('material')).reshape(dims[2],dims[1],dims[0])
                xs=origin[0]+np.arange(ext[0],ext[1]+1)*spacing[0]
                ys=origin[1]+np.arange(ext[2],ext[3]+1)*spacing[1]
                zs=origin[2]+np.arange(ext[4],ext[5]+1)*spacing[2]
                mask=(material==1)&((zs>=0)&(zs<175e-9))[:,None,None]&((ys>=0)&(ys<240e-9))[None,:,None]&((xs>=0)&(xs<240e-9))[None,None,:]
                iz,iy,ix=np.nonzero(mask);fluid_count+=len(ix)
                xx=xs[ix];yy=ys[iy];zz=zs[iz]
                ijk=[np.rint(v/dx-.5).astype(np.int64) for v in [xx,yy,zz]]
                assert all(np.max(np.abs(v/dx-.5-i))<=1e-9 for v,i in zip([xx,yy,zz],ijk))
                slot=(xx>=60e-9)&(xx<180e-9)
                assert np.all(zz<75e-9+100e-9*slot)
                allids.append(ijk[0]+nx*(ijk[1]+ny*ijk[2]))
                valid=mask.ravel();vel=vtk_to_numpy(point.GetArray('velocity_m_s'))[valid]
                pressure=vtk_to_numpy(point.GetArray('pressure_Pa'))[valid]
                diss=vtk_to_numpy(point.GetArray('dissipation_m2_s3'))[valid]
                assert np.isfinite(vel).all() and np.isfinite(pressure).all() and np.isfinite(diss).all()
                assert np.all(diss>=0)
                assert vel.dtype==np.float32
                sums+=np.sum(vel.astype(np.float64),axis=0)
                half_ulp=np.abs(np.spacing(vel)).astype(np.float64)*.5
                gamma=len(vel)*np.finfo(float).eps/(1-len(vel)*np.finfo(float).eps)
                bounds+=np.sum(half_ulp,axis=0)+gamma*np.sum(np.abs(vel.astype(float)),axis=0)
            ids=np.concatenate(allids)
            assert fluid_count==rec['fluid_nodes'] and len(np.unique(ids))==fluid_count
            factor=dx**3/(240e-9)**2;J=sums*factor;roundoff=bounds*factor
            if step==rec['final_step']:target=np.array([float(v) for v in r['J_vector_m2_s'].split(',')])
            else:
                sha(folder/'diagnostics.csv')
                with (folder/'diagnostics.csv').open() as f:first=next(csv.DictReader(f))
                target=np.array([float(first['J'+k]) for k in 'xyz'])
            roundoff+=2*np.finfo(float).eps*np.abs(target)
            difference=np.abs(J-target)
            assert np.all(difference<=roundoff),(folder,step,difference.tolist(),roundoff.tolist())
            records.append(dict(case=rec['case'],dx_nm=rec['dx_nm'],step=step,reader=str(vtm),
                valid_unique_fluid_nodes=fluid_count,arrays=arrays,velocity_units='m/s',pressure_units='Pa_periodic_perturbation',
                dissipation_units='m2/s3',J_integrated_m2_s=J.tolist(),J_CSV_m2_s=target.tolist(),
                difference_m2_s=difference.tolist(),float32_export_and_float64_sum_bound_m2_s=roundoff.tolist(),
                matches_CSV_within_numeric_export_bounds=True))
            del reader,image,vel,pressure,diss,material,ids,allids;gc.collect()
    dest=OUT/'saved_field_review.json'
    if dest.exists():raise FileExistsError(dest)
    dest.write_text(json.dumps(dict(VTK_version=vtk.vtkVersion.GetVTKVersion(),frames=len(records),
        records=records,actual_readback=True,figures_generated=False,solver_started=False,
        note='Six final grooved fields plus Scheme C initial field; smooth profiles checked separately. Only saved instants are covered.'),indent=2)+'\n')
    (OUT/'field_read_inputs_sha256.json').write_text(json.dumps(INPUTS,indent=2)+'\n')
    print(json.dumps(dict(frames=len(records),all_saved_fields_reviewed_PASS=True,solver_started=False)))

if __name__=='__main__':main()
