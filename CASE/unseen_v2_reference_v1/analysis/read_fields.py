#!/usr/bin/env pvpython
"""Read VTK payloads, hash their complete reference closure, integrate core fluid."""
from pathlib import Path
import argparse
import csv
import gc
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from evidence import need,kv,rows,sha,save,exact_parameters

def payloads(path, root, hashes):
    path=Path(path).resolve()
    need(path.is_relative_to(root), 'VTK reference escapes run directory')
    if str(path) in hashes: return
    hashes[str(path)]=sha(path)
    if path.suffix in ('.pvd','.vtm'):
        for node in ET.parse(path).getroot().iter('DataSet'):
            if 'file' in node.attrib: payloads(path.parent/node.attrib['file'],root,hashes)

def leaves(data):
    iterator=data.NewIterator();iterator.SkipEmptyNodesOn();iterator.InitTraversal()
    while not iterator.IsDoneWithTraversal():
        obj=iterator.GetCurrentDataObject()
        if obj is not None and obj.IsA('vtkImageData'): yield obj
        iterator.GoToNextItem()

def audit(run):
    run=Path(run).resolve();cfg=kv(run/'run_config.txt');result=kv(run/'result.txt')
    p=exact_parameters(cfg);dx=p['dx'];nx=p['nx'];ny=p['ny']
    index=rows(run/'frame_index.csv')
    need(len(index)>0, 'no actual saved frames')
    readers=list((run/'vtkData').glob('*.pvd'))
    need(len(readers)==1, 'expected one VTK master reader')
    readerpath=readers[0];hashes={};payloads(readerpath,run,hashes)
    datasets=list(ET.parse(readerpath).getroot().iter('DataSet'))
    need(len(datasets)==len(index), 'VTK frame-index disagreement')
    diagnostics={} if cfg['mode']=='initialize' else {int(r['step']):r for r in rows(run/'diagnostics.csv')}
    checked=[]
    for ds,frame in zip(datasets,index):
        step=int(frame['step'])
        need(int(float(ds.attrib['timestep']))==step, 'wrong VTK time selection')
        path=readerpath.parent/ds.attrib['file']
        reader=vtk.vtkXMLMultiBlockDataReader();reader.SetFileName(str(path));reader.Update()
        need(reader.GetErrorCode()==0, 'VTK reader error')
        totals=np.zeros(3);bounds=np.zeros(3);ids=[];umax=0.;pressure_min=math.inf;pressure_max=-math.inf
        for image in leaves(reader.GetOutput()):
            dims=image.GetDimensions();ext=image.GetExtent();origin=image.GetOrigin();spacing=image.GetSpacing()
            need(all(abs(s/dx-1)<1e-10 for s in spacing), 'wrong VTK length units/spacing')
            data=image.GetPointData()
            names=['material','velocity_m_s','pressure_Pa','dissipation_m2_s3']
            need(all(data.GetArray(name) is not None for name in names), 'missing physical VTK array')
            material=vtk_to_numpy(data.GetArray('material')).reshape(dims[2],dims[1],dims[0])
            xs=origin[0]+np.arange(ext[0],ext[1]+1)*spacing[0]
            ys=origin[1]+np.arange(ext[2],ext[3]+1)*spacing[1]
            zs=origin[2]+np.arange(ext[4],ext[5]+1)*spacing[2]
            core=((xs>=0)&(xs<p['P']))[None,None,:]&((ys>=0)&(ys<p['Ly']))[None,:,None]
            mask=(material==1)&core&((zs>=0)&(zs<p['h']+p['d']))[:,None,None]
            iz,iy,ix=np.nonzero(mask)
            if not len(ix): continue
            xx,yy,zz=xs[ix],ys[iy],zs[iz]
            ijk=[np.rint(v/dx-.5).astype(np.int64) for v in [xx,yy,zz]]
            need(all(np.max(np.abs(v/dx-.5-i))<1e-8 for v,i in zip([xx,yy,zz],ijk)), 'non-centered VTK lattice')
            groove=(xx>=(p['P']-p['w'])/2)&(xx<(p['P']+p['w'])/2)
            need(np.all(zz<p['h']+p['d']*groove), 'fluid in an analytical solid')
            ids.append(ijk[0]+nx*(ijk[1]+ny*ijk[2]))
            vel=vtk_to_numpy(data.GetArray('velocity_m_s'))[mask.ravel()]
            pressure=vtk_to_numpy(data.GetArray('pressure_Pa'))[mask.ravel()]
            dissipation=vtk_to_numpy(data.GetArray('dissipation_m2_s3'))[mask.ravel()]
            need(vel.dtype==np.float32 and vel.shape[1]==3, 'unexpected velocity export representation')
            need(all(np.isfinite(a).all() for a in [vel,pressure,dissipation]), 'nonfinite VTK field')
            need(np.all(dissipation>=0), 'negative kinematic dissipation')
            totals+=vel.astype(float).sum(axis=0)
            gamma=len(vel)*np.finfo(float).eps/(1-len(vel)*np.finfo(float).eps)
            bounds+=(np.abs(np.spacing(vel)).astype(float)*.5).sum(axis=0)+gamma*np.abs(vel.astype(float)).sum(axis=0)
            umax=max(umax,float(np.linalg.norm(vel.astype(float),axis=1).max()))
            pressure_min=min(pressure_min,float(pressure.min()));pressure_max=max(pressure_max,float(pressure.max()))
        ids=np.concatenate(ids)
        need(len(ids)==p['nodes'] and len(np.unique(ids))==p['nodes'], 'missing or duplicated core fluid')
        factor=dx**3/(p['P']*p['Ly']);J=totals*factor;error=bounds*factor
        target=np.array([float(v) for v in result['J_vector_m2_s'].split(',')]) if cfg['mode']=='initialize' else np.array([float(diagnostics[step]['J'+axis]) for axis in 'xyz'])
        error+=2*np.finfo(float).eps*np.abs(target)
        need(np.all(np.abs(J-target)<=error), 'VTK and diagnostic flux disagree beyond export roundoff')
        if cfg['mode']=='initialize':
            expected=np.zeros(3);expected[1 if cfg['direction']=='P' else 0]=p['a']*p['dt']/2
            need(np.allclose(J,p['H']*expected,rtol=1e-6,atol=1e-30), 'initial force half-step velocity')
            need(pressure_min==pressure_max==0, 'initial pressure is not equilibrium perturbation')
        checked.append(dict(step=step,unique_fluid_nodes=len(ids),J_m2_s=J.tolist(),
            diagnostic_J_m2_s=target.tolist(),roundoff_bound_m2_s=error.tolist(),
            max_speed_m_s=umax,pressure_range_Pa=[pressure_min,pressure_max],
            material='core fluid only; periodic overlap excluded',arrays=names))
        del reader,ids;gc.collect()
    need(all(sha(p)==s for p,s in hashes.items()), 'VTK payload changed during read')
    return dict(PASS=True,actual_reader=True,VTK_version=vtk.vtkVersion.GetVTKVersion(),
        frames=checked,payload_sha256=hashes,velocity_units='m/s',
        pressure_units='Pa_periodic_perturbation',dissipation_units='m2/s3',solver_executed=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    try:
        receipt=audit(args.run);save(args.out,receipt)
    except Exception as e:
        save(args.out,dict(PASS=False,error=type(e).__name__+': '+str(e),solver_executed=False));raise
    print(json.dumps(dict(field_readback_PASS=True,frames=len(receipt['frames']))))
