"""Independent URV-MRP-v1 readers and binary64 arithmetic. No native calls."""
from pathlib import Path
from fractions import Fraction
import csv,json,math,struct
from evidence import need,sha,kv,save

CASE=Path(__file__).resolve().parents[1]
SCHEDULE=CASE/'revision/density_capture_schedule.json'
def bits(value): return struct.pack('>d',float(value)).hex()
def unbits(value):
    need(isinstance(value,str) and len(value)==16,'invalid binary64 encoding')
    number=struct.unpack('>d',bytes.fromhex(value))[0]
    need(math.isfinite(number),'nonfinite binary64 value')
    return number

def secure_file(root,name):
    need(isinstance(name,str) and name and not Path(name).is_absolute(),'invalid relative capture path')
    p=Path(root)/name
    need(not any(part=='..' for part in Path(name).parts),'capture path escapes root')
    need(not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(Path(root).resolve()),
         'missing/symlink/escaping capture file')
    return p

def expected_coordinates():
    # Geometry origin is (dx/2,dx/2,-dx/2); bottom fluid local index is 1.
    return [(0,x,y,z) for x in range(48) for y in range(48)
            for z in range(1,16+(20 if 12<=x<36 else 0))]

def check_map(path):
    with Path(path).open() as f:
        rows=list(csv.DictReader(f))
    expected=expected_coordinates()
    need(len(rows)==len(expected)==57600,'wrong capture core size')
    for i,(row,coordinate) in enumerate(zip(rows,expected)):
        need(set(row)=={'ordinal','cuboid','iX','iY','iZ','material'},'core map schema')
        need(int(row['ordinal'])==i and int(row['material'])==1,'core ordinal/material')
        need(tuple(int(row[k]) for k in ['cuboid','iX','iY','iZ'])==coordinate,
             'core coordinates out of order or wrong geometry')

def validate_index(index,root,run_id,direction,binary_sha,with_hashes=True):
    need(index['protocol_id']=='URV-MRP-v1' and index['run_id']==run_id and
         index['direction']==direction,'capture identity')
    mapfile=secure_file(root,index['map_file']);check_map(mapfile)
    if with_hashes:
        need(index['native_binary_sha256']==binary_sha and index['map_sha256']==sha(mapfile),
             'capture executable/map binding')
    schedule=json.loads(SCHEDULE.read_text())['directions'][direction]
    expected={('initial_reference',0)}|{('diagnostic',s) for s in schedule['diagnostic_steps']}
    seen=set();constants=None;environment=None;initial=None;zero=None
    need(isinstance(index['records'],list),'capture record container')
    for record in index['records']:
        key=(record['phase'],record['step'])
        need(key in expected and key not in seen,'duplicate/unplanned phase/step')
        seen.add(key)
        need(record['nodes']==57600 and record['dtype']=='<f8','capture shape/type')
        need(record['file']==f'{key[0]}_{key[1]}.rho64','capture phase/file mismatch')
        p=secure_file(root,record['file'])
        need(p.stat().st_size==460800,'truncated/excess rho payload')
        if with_hashes:
            need(record['sha256']==sha(p) and record['bytes']==460800 and
                 record['map_sha256']==index['map_sha256'],'capture SHA/size binding')
        need(bits(record['time_s'])==record['time_hex64'],'capture time bit mismatch')
        # Independently match native config order for dt, rather than Fraction->float.
        dx=unbits(record['dx_hex64']);rho=unbits(record['rho_phys_hex64'])
        need(bits(dx)==bits(5.*1e-9) and rho==1000.,'capture constants')
        dt=(1.-.5)*dx*dx/(3.*1e-6)
        need(bits(key[1]*dt)==record['time_hex64'],'capture step/time mismatch')
        current=(record['dx_hex64'],record['rho_phys_hex64'])
        env=(record['fe_round'],record['mxcsr_control'],record['double_bytes'],record['iec559'],record['cpu_fma'])
        need(env[0]==0 and env[2:]==(8,True,True) and (env[1]&0x6000)==0,
             'capture floating environment')
        if constants is None: constants=current;environment=env
        need(current==constants and env==environment,'capture constants/environment changed')
        for keyname in ['native_mass_hex64','native_corrected_mass_hex64',
                        'native_density_delta_hex64','native_volume_hex64']:
            unbits(record[keyname])
        if key==('initial_reference',0): initial=p
        if key==('diagnostic',0): zero=p
    need(seen==expected,'missing capture phases/steps')
    need(initial.read_bytes()==zero.read_bytes(),'initial reference differs from diagnostic zero')
    return index

def finalize_capture(run,binary):
    """Bind native raw records before completion.json; never repairs payloads."""
    run=Path(run);root=run/'mass_capture';cfg=kv(run/'run_config.txt')
    raw=secure_file(root,'rho_capture_raw.json')
    index=json.loads(raw.read_text())
    need(Path(index['native_executable']).resolve()==Path(binary).resolve(),'wrong native capture executable')
    validate_index(index,root,cfg['run_id'],cfg['direction'],sha(binary),False)
    index['native_binary_sha256']=sha(binary)
    index['raw_index_sha256']=sha(raw);index['map_sha256']=sha(root/index['map_file'])
    index['schema_version']='URV-MRP-CAPTURE-1'
    for record in index['records']:
        p=secure_file(root,record['file']);record.update(sha256=sha(p),bytes=p.stat().st_size,
                                                      map_sha256=index['map_sha256'])
    validate_index(index,root,cfg['run_id'],cfg['direction'],sha(binary))
    save(root/'rho_capture_index.json',index)
    return index

def neumaier_add(state,term):
    total,correction=state;following=total+term
    correction+=((total-following)+term) if abs(total)>=abs(term) else ((term-following)+total)
    return following,correction

def replay_values(values,rho_phys,dx):
    need(hasattr(math,'fma'),'Python math.fma required; no unfused fallback')
    fused=split=0.;mass=(0.,0.);delta=(0.,0.);first=None;count=0;max_ulp=0
    for ordinal,rho in enumerate(values):
        need(math.isfinite(rho) and rho>0,'nonpositive/nonfinite density')
        partial=((rho*rho_phys)*dx)*dx
        old_fused=fused;old_split=split
        fused=math.fma(partial,dx,fused)
        term=partial*dx;split=split+term
        mass=neumaier_add(mass,term);delta=neumaier_add(delta,rho-1.)
        if bits(fused)!=bits(split):
            count+=1
            distance=abs(int(bits(fused),16)-int(bits(split),16));max_ulp=max(max_ulp,distance)
            if first is None:
                first=dict(ordinal=ordinal,rho_hex64=bits(rho),partial_hex64=bits(partial),
                           fused_input_hex64=bits(old_fused),split_input_hex64=bits(old_split),
                           fused_output_hex64=bits(fused),split_output_hex64=bits(split))
    result=dict(fused_mass=fused,split_mass=split,corrected_mass=mass[0]+mass[1],
                density_delta=delta[0]+delta[1])
    return dict(**result,hex64={k:bits(v) for k,v in result.items()},
                spatial_prefix_differences=count,maximum_prefix_ULP=max_ulp,
                first_spatial_prefix_difference=first)

def replay_file(path,rho_phys,dx):
    data=Path(path).read_bytes();need(len(data)==460800,'rho payload size')
    return replay_values((v[0] for v in struct.iter_unpack('<d',data)),rho_phys,dx)

def arithmetic_self_check():
    rho=1.;dx=5e-9;partial=((rho*1000.)*dx)*dx;mass=3.5e-21
    exact=float(Fraction(partial)*Fraction(dx)+Fraction(mass))
    fused=math.fma(partial,dx,mass);split=partial*dx+mass
    need(bits(exact)==bits(fused) and int(bits(fused),16)-int(bits(split),16)==1,
         'FMA rational oracle/constructed counterexample failure')
    need(bits(float(Fraction(partial)*Fraction(dx)))==bits(partial*dx),'product rounding oracle')
    return {'constructed_not_historical':True,'fma_hex64':bits(fused),'split_hex64':bits(split)}
