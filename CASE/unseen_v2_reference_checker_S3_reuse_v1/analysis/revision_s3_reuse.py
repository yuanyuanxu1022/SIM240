"""Exact S1 ELF adoption for S3; no authority is granted by source reuse."""
from pathlib import Path
import json
from evidence import need,sha
from s3_baselines import S2_RELEASE,S2_SHA,verify_baselines

REVISION='URV-S3-S1-ELF-REUSE-v1'
ELF_SHA='5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'

def verify_s3_reuse(bound,observed,checker_case):
    from contracts import covered,verify_provenance
    from stage_s3 import validate_records,validate_formal_authority
    path=checker_case/'s3_revision/anchor.json';covered(str(path),bound['inputs_sha256']);anchor=json.loads(path.read_text())
    need(anchor['revision_id']==REVISION and anchor['simulation_authorized'] is False,'S3 source anchor is not authority')
    need(bound.get('source_revision')==dict(id=REVISION,anchor=str(path),sha256=sha(path)),'S3 anchor identity mismatch')
    need(bound.get('stage')=='S3_REG_LINEARITY','exact S3 source stage required');validate_records(bound,checker_case)
    need(observed==anchor['native_source_sha256'],'S3 exact native source mismatch')
    binary=covered(bound['provenance']['native_binary'],bound['inputs_sha256'])
    need(str(binary)==anchor['native_binary_path'] and sha(binary)==anchor['native_binary_sha256']==ELF_SHA,'S3 exact reused ELF required')
    need(anchor['S2_release_path']==str(S2_RELEASE) and anchor['S2_release_sha256']==S2_SHA and sha(covered(str(S2_RELEASE),bound['inputs_sha256']))==S2_SHA,'S3 predecessor release mismatch')
    prior=json.loads(S2_RELEASE.read_text());need(bound['provenance']==prior['provenance'],'S3 genuine build provenance changed')
    need(all(bound['inputs_sha256'].get(p)==h for p,h in prior['inputs_sha256'].items()),'S3 predecessor closure dropped')
    # Reuse genuine old S2 lineage with its own checker/stage, without pretending S3 is S2.
    verify_provenance(prior,checker_case.parent/'unseen_v2_reference_checker_S2_reuse_v1')
    audit=json.loads(covered(anchor['machine_audit_path'],bound['inputs_sha256']).read_text())
    need(audit['SOURCE_REVISION_AUDIT']=='PASS' and audit['binary_sha256']==ELF_SHA and
         anchor['instruction_audit_status']=='REUSED_EXACT_ELF_SCOPED_PASS','historical scoped instruction audit mismatch')
    verify_baselines(bound)
    if bound.get('simulation_authorized') is True:validate_formal_authority(bound)
