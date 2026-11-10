"""Marked artificial 48-file records; never uses actual N8 field arrays."""
from io import BytesIO
import json
from pathlib import Path
import numpy as np
from binding import SYNTHETIC,canonical,digest,blob_sha,snapshot
from test_fixtures import make_fixture


def code_hashes():
    here=Path(__file__).resolve().parent
    return {str(here/n):blob_sha((here/n).read_bytes()) for n in ('numerics.py','extractor.py','binding.py','analysis_record.py')}


def write_json(p,obj):p.write_bytes(canonical(obj)+b'\n')


def seal(case):
    root=case['root'];b=case['binding']
    inventory={name:blob_sha(blob) for name,blob in snapshot(root).items()}
    index={str(root/name):h for name,h in inventory.items()}
    write_json(Path(b['acceptance_inputs_path']),index)
    b['inventory']=inventory;b['inventory_sha256']=digest(inventory)
    b['acceptance_inputs_sha256']=blob_sha(Path(b['acceptance_inputs_path']).read_bytes())
    b['acceptance_sha256']=blob_sha(Path(b['acceptance_path']).read_bytes())
    b['code_sha256']=code_hashes();b['spec_sha256']=blob_sha(Path(b['spec_path']).read_bytes())
    trust={key:b[key] for key in ('acceptance_sha256','acceptance_inputs_sha256','inventory_sha256','code_sha256','spec_sha256')}
    trust['binding_sha256']=digest(b);case['trust']=trust
    return case


def make_case(base):
    base=Path(base).resolve();base.mkdir(exist_ok=True)
    root=base/'synthetic_record';root.mkdir()
    evidence=base/'synthetic_acceptance';evidence.mkdir()
    s,a=make_fixture(lambda x,z:(z*(1-z)/2,0.),nx=16,nz=8)
    vi=s['velocity_reconstructed_dof_indices'];vc=s['velocity_dof_coordinates_hat'];comp=s['velocity_dof_components']
    pi=s['pressure_reconstructed_dof_indices'];pc=s['pressure_coordinates_hat']
    slave=[];master=[]
    for ids,coords,cs,is_v in ((vi,vc,comp,True),(pi,pc,np.full(len(pi),2),False)):
        for idx,pos,c in zip(ids,coords,cs):
            if pos[0]==2 and (not is_v or 0<pos[1]<1):
                hit=np.flatnonzero((coords[:,0]==0)&(coords[:,1]==pos[1])&(cs==c))
                assert len(hit)==1;slave.append(int(idx));master.append(int(ids[hit[0]]))
    s['periodic_slave_dofs']=np.array(slave);s['periodic_master_dofs']=np.array(master);s['periodic_coefficients']=np.ones(len(slave))
    s['wall_velocity_dof_indices']=vi[(vc[:,1]==0)|(vc[:,1]==1)]
    s['algebraic_solution_before_backsub'][slave]=0
    n=len(s['reconstructed_solution']);pivot=int(np.flatnonzero(s['algebraic_solution_before_backsub'])[0])
    rhs=np.zeros(n);rhs[pivot]=s['algebraic_solution_before_backsub'][pivot]
    ptr=np.zeros(n+1,dtype=int);ptr[pivot+1:]=1
    null=np.zeros(n);null[pi]=1;null[np.array(slave)]=0
    a.update(csr_indptr=ptr,csr_indices=np.array([pivot]),csr_values=np.array([1.]),
             rhs_before=rhs.copy(),rhs_after=rhs.copy(),pressure_null_vector=null)
    run='SYNTHETIC_D4_N8_FORMAT_FIXTURE_NOT_RUN'
    contract=dict(run_id=run,planned_id='B0MIN_MMS_mixed_N8',record_dir=str(root),
                  solver_execution_authorized=False,kind=SYNTHETIC)
    csha=digest(contract)
    write_json(root/'contract.json',contract)
    write_json(root/'capture_manifest.json',dict(run_id=run,contract_sha256=csha,
        archive_status='ARCHIVE_COMPLETE',independent_exit_code=0,inputs_unchanged=True,children_stopped=True,kind=SYNTHETIC))
    (root/'archive').mkdir()
    write_json(root/'archive/worker_completion.json',dict(run_id=run,contract_sha256=csha,status='SOLVER_EXITED_UNVERIFIED',kind=SYNTHETIC))
    write_json(root/'synthetic_marker.json',dict(kind=SYNTHETIC,not_a_PDE_solution=True))
    for group,arrays in [('system',a),('solution',s)]:
        folder=root/'archive'/group;folder.mkdir();files={}
        for name,arr in arrays.items():
            buf=BytesIO();np.save(buf,arr,allow_pickle=False);blob=buf.getvalue();name=name+'.npy';(folder/name).write_bytes(blob)
            files[name]=dict(dtype=arr.dtype.str,shape=list(arr.shape),sha256=blob_sha(blob))
        write_json(folder/'manifest.json',dict(files=files,metadata=dict(contract_sha256=csha,
               record_kind='SYNTHETIC_DIAGNOSTIC_UNVERIFIED_NOT_RESULT'),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None))
    # Explicit synthetic auxiliary records reproduce the complete inventory count;
    # they carry no claim of solver/provenance evidence.
    for k in range(48-len(snapshot(root))):write_json(root/('synthetic_aux_%02d.json'%k),dict(kind=SYNTHETIC,not_real_evidence=True))
    certificate=evidence/'verdict.json';index=evidence/'input_sha256.json'
    write_json(certificate,dict(status='SYNTHETIC_DIAGNOSTIC_ACCEPTED_NOT_RESULT',kind=SYNTHETIC,run_id=run))
    here=Path(__file__).resolve().parent
    b=dict(schema_version=2,kind=SYNTHETIC,analysis_id='SYNTHETIC_ANALYSIS_N8_FORMAT_v2',
           source_run_id=run,planned_id='B0MIN_MMS_mixed_N8',source_contract_sha256=csha,
           record_root=str(root),acceptance_path=str(certificate),acceptance_inputs_path=str(index),
           spec_path=str(here/'ANALYSIS_SPEC.md'),analysis_output=str(base/'synthetic_analysis_output'),
           solver_authorized=False,real_extraction_authorized=False)
    return seal(dict(root=root,binding=b,base=base))
