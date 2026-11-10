#!/usr/bin/env pvpython
"""Read initial VTM/payloads, field units and core-fluid counts; no flow advancement."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy

ROOT=Path(__file__).resolve().parents[1]
kv=lambda p:dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((ROOT/'evidence/preflight.json').read_text());records=[]
for item in pre['initial_output_sets']:
    out=ROOT/item['output'];row=item['row'];cfg=kv(out/'effective_config.txt')
    inputs=list((out/'vtkData').rglob('*iT0000000.vtm'));assert len(inputs)==1
    root=inputs[0];payloads={}
    def walk(file):
        file=file.resolve();assert out.resolve() in file.parents
        payloads[str(file.relative_to(out))]=sha(file)
        if file.suffix in ['.vtm','.pvd']:
            for entry in ET.parse(file).getroot().iter():
                if 'file' in entry.attrib:walk(file.parent/entry.attrib['file'])
    walk(root)
    reader=vtkXMLMultiBlockDataReader();reader.SetFileName(str(root));reader.Update()
    output=reader.GetOutput();it=output.NewIterator();it.SkipEmptyNodesOn();it.InitTraversal()
    total=0;maximum_velocity_error=0.;arrays_seen=set()
    while not it.IsDoneWithTraversal():
        data=it.GetCurrentDataObject();it.GoToNextItem()
        if not data.IsA('vtkImageData'):continue
        pd=data.GetPointData();names=['material','velocity_m_s','pressure_Pa','dissipation_m2_s3']
        assert all(pd.GetArray(name) is not None for name in names)
        arrays={name:vtk_to_numpy(pd.GetArray(name)) for name in names};arrays_seen.update(names)
        n=data.GetNumberOfPoints();extent=data.GetExtent();shape=[extent[2*i+1]-extent[2*i]+1 for i in range(3)]
        index=np.arange(n);ijk=[index%shape[0],(index//shape[0])%shape[1],index//(shape[0]*shape[1])]
        position=[data.GetOrigin()[i]+(extent[2*i]+ijk[i])*data.GetSpacing()[i] for i in range(3)]
        mask=arrays['material']==1
        for i,length in enumerate([float(cfg['Lx_m']),float(cfg['Ly_m']),float(cfg['h_m'])+float(cfg['d_m'])]):
            mask&=(position[i]>=0)&(position[i]<length)
        total+=int(mask.sum())
        for name in names:assert np.isfinite(arrays[name][mask]).all()
        expected=np.zeros(3);expected[1 if row['direction']=='P' else 0]=.5*float(row['acceleration_m_s2'])*float(cfg['dt_s'])
        err=float(np.max(np.abs(arrays['velocity_m_s'][mask]-expected)))
        maximum_velocity_error=max(maximum_velocity_error,err)
        assert err<max(1e-15,float(np.max(expected))*1e-8)
    assert total==int(row['fluid_nodes_expected'])
    assert set(arrays_seen)==set(['material','velocity_m_s','pressure_Pa','dissipation_m2_s3'])
    assert len((out/'frame_index.csv').read_text().splitlines())==2
    records.append({'run_id':kv(out/'result.txt')['run_id'],'core_fluid_points':total,
                    'initial_half_force_velocity_max_abs_error_m_s':maximum_velocity_error,
                    'arrays':sorted(arrays_seen),'files_sha256':payloads,
                    'vtk_bytes':sum((out/name).stat().st_size for name in payloads)})
assert len(records)==6
result={'ok':True,'initial_output_sets':6,'reader':'vtkXMLMultiBlockDataReader',
        'vtk_version':__import__('vtkmodules.vtkCommonCore',fromlist=['vtkVersion']).vtkVersion.GetVTKVersion(),
        'records':records,'collide_and_stream_calls':0,'intermediate_time_frames_verified':False,
        'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False}
(ROOT/'evidence/initial_fields.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
