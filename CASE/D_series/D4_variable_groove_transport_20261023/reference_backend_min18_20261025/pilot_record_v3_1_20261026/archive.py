"""Copy stopped-process output to a durable, independently verifiable archive."""
import json
import os
from pathlib import Path
import shutil
from common import digest, sha


def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def durable_json(path,value):
    path=Path(path)
    temp=path.with_name(path.name+'.writing')
    with temp.open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
        f.flush();os.fsync(f.fileno())
    if path.exists():raise FileExistsError(path)
    os.rename(temp,path);sync_dir(path.parent)


def strict_inventory(root):
    root=Path(root);result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('ARCHIVE_SYMLINK_REJECTED:'+str(p))
        if p.is_dir():continue
        if not p.is_file():raise ValueError('ARCHIVE_SPECIAL_FILE_REJECTED:'+str(p))
        result[str(p.relative_to(root))]={'sha256':sha(p),'bytes':p.stat().st_size}
    return result


def archive_stopped_work(work,record,contract,*,children_stopped,independent_exit_code):
    """Never deletes source; partial copy/failed publication stays visibly incomplete."""
    work,record=Path(work),Path(record)
    if not children_stopped:raise ValueError('ARCHIVE_REQUIRES_STOPPED_WRITERS')
    stage,final=record/'archive.incomplete',record/'archive'
    if any(p.exists() for p in (stage,final,record/'archive_manifest.json',record/'archive_failure.json')):
        raise FileExistsError('ARCHIVE_NO_OVERWRITE')
    try:
        stage.mkdir()
        before=strict_inventory(work)
        for source in sorted(work.rglob('*')):
            dest=stage/source.relative_to(work)
            if source.is_symlink():raise ValueError('ARCHIVE_SYMLINK_REJECTED')
            if source.is_dir():dest.mkdir(exist_ok=True);continue
            with source.open('rb') as src,dest.open('xb') as dst:
                shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
        if strict_inventory(stage)!=before or strict_inventory(work)!=before:
            raise ValueError('ARCHIVE_COPY_OR_SOURCE_CHANGED')
        for p in sorted((p for p in stage.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(p)
        sync_dir(stage);os.rename(stage,final);sync_dir(record)
        result={'status':'ARCHIVE_COMPLETE','run_id':contract['run_id'],
            'contract_sha256':digest(contract),'source_work_dir':str(work),
            'archive_dir':str(final),'independent_exit_code':independent_exit_code,
            'work_files':before,'source_deleted':False,'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False}
        durable_json(record/'archive_manifest.json',result)
        return result
    except Exception as exc:
        # Preserve original work and any partial target. No success marker.
        marker=record/'archive_manifest.json'
        if marker.exists():
            try:marker.unlink();sync_dir(record)
            except OSError:pass  # Capture still reports INCOMPLETE, never success.
        try: durable_json(record/'archive_failure.json',{'status':'ARCHIVE_INCOMPLETE',
            'run_id':contract['run_id'],'contract_sha256':digest(contract),
            'source_work_dir':str(work),'original_archive_exception':repr(exc),
            'independent_exit_code':independent_exit_code,'source_deleted':False})
        except Exception as log_exc:
            raise RuntimeError('ARCHIVE_AND_FAILURE_RECORD_FAILED; original='+repr(exc)+'; record='+repr(log_exc)) from exc
        raise
