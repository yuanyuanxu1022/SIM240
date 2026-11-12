#!/usr/bin/env python3
"""Offline reader and fail-closed acceptance; never invokes a solver.

K = nu/a * sum(u_i V) / Aplan. The volume average is a diagnostic only.
No independent reference is accepted without a bound runtime receipt.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def metrics(meta: dict, rows: list[dict], faces: list[dict]) -> dict:
    if len(rows) != meta['expected_cells']:
        raise ValueError('cell count differs from frozen mesh plan')
    if not rows or any(not math.isfinite(v) for r in rows for v in r.values()):
        raise ValueError('missing or nonfinite cell values')
    if any(r['V_m3'] <= 0 for r in rows):
        raise ValueError('nonpositive cell volume')
    V = math.fsum(r['V_m3'] for r in rows)
    expected = meta['expected_V_m3']
    if abs(V/expected-1) > 1e-10:
        raise ValueError('fluid volume differs from exact groove geometry')
    period, depth, height = [meta[k]*1e-9 for k in ('P_nm','d_nm','h_nm')]
    width, ly = meta['w_nm']*1e-9, meta['Ly_nm']*1e-9
    tol = 1e-7*meta['dx_nm']*1e-9
    for r in rows:
        x,y,z = (r[k] for k in ('x_m','y_m','z_m'))
        if not (0-tol < x < period+tol and -tol < y < ly+tol and -tol < z < depth+height+tol):
            raise ValueError('cell outside frozen bounding box')
        if depth and z < depth-tol and x > width+tol:
            raise ValueError('cell occupies the solid ridge')
    comp = 'Uy_m_s' if meta['direction']=='P' else 'Ux_m_s'
    integral = math.fsum(r[comp]*r['V_m3'] for r in rows)
    J = integral/meta['Aplan_m2']
    K = meta['nu_m2_s']/meta['acceleration_m_s2']*J
    if K <= 0 or not math.isfinite(K):
        raise ValueError('nonpositive or invalid main conductance')
    umean = integral/V
    kappa = meta['nu_m2_s']/meta['acceleration_m_s2']*umean
    href = V/meta['Aplan_m2']
    if abs(K/(href*kappa)-1) > 1e-12:
        raise ValueError('K vs Href*kappa normalization mismatch')
    power = meta['rho_kg_m3']*meta['acceleration_m_s2']*integral
    diss = meta['rho_kg_m3']*math.fsum(r['diss_per_mass_m2_s3']*r['V_m3'] for r in rows)
    if diss <= 0 or not math.isfinite(diss):
        raise ValueError('invalid dissipation')
    result = dict(K_m3=K,J_m2_s=J,kappa_m2=kappa,Href_m=href,
                  fluid_volume_m3=V,drive_power_W=power,viscous_dissipation_W=diss,
                  power_balance_percent=abs(diss/power-1)*100)
    if meta['direction']=='T':
        if not faces:
            raise ValueError('missing complete transverse section fluxes')
        groups: dict[int, list[float]] = {}
        areas: dict[int, list[float]] = {}
        # block coordinates are exact integer multiples of dx; use nearest face index.
        dx = meta['dx_nm']*1e-9
        for f in faces:
            if any(not math.isfinite(v) for v in f.values()) or f['area_m2']<=0:
                raise ValueError('invalid face record')
            idx=round(f['x_m']/dx)
            if abs(f['x_m']-idx*dx)>dx*1e-6:
                raise ValueError('face off the prepared structured x planes')
            groups.setdefault(idx,[]).append(f['flux_positive_x_m3_s'])
            areas.setdefault(idx,[]).append(f['area_m2'])
        count=round(period/dx)
        if set(groups)!=set(range(count+1)):
            raise ValueError('missing x section, including periodic ends')
        for i, values in areas.items():
            # At a step plane the full open section is only h; the vertical wall
            # contributes a zero-flux face, but its area is excluded here below.
            area=math.fsum(values)
            target=(height+depth if 0 < i*dx < width else height)*ly
            # Export includes solid step faces too; validate against full mesh
            # x-face area, and use zero-wall flux in the complete flux sum.
            if i in (0,round(width/dx)):
                target=(height+depth)*ly
            if abs(area/target-1)>1e-8:
                raise ValueError('section area incomplete or duplicated')
        qs=[math.fsum(groups[i]) for i in range(count+1)]
        qmean=math.fsum(qs)/len(qs)
        if qmean<=0:
            raise ValueError('invalid transverse section flux sign')
        result.update(section_flux_spread_percent=(max(qs)-min(qs))/qmean*100,
                      section_flux_mean_m3_s=qmean,
                      section_vs_volume_percent=abs(qmean/(J*ly)-1)*100,
                      section_evidence='corrected finite-volume face flux')
    else:
        result.update(section_flux_spread_percent=0.0,
                      section_evidence='exact y invariance of scalar model; not an independent mass test')
    if meta['d_nm']==0:
        exact=height**3/12
        exact_velocity=[meta['acceleration_m_s2']*r['z_m']*(height-r['z_m'])/(2*meta['nu_m2_s']) for r in rows]
        num=math.fsum((r[comp]-u)**2*r['V_m3'] for r,u in zip(rows,exact_velocity))
        den=math.fsum(u*u*r['V_m3'] for r,u in zip(rows,exact_velocity))
        result.update(flat_K_error_percent=abs(K/exact-1)*100,
                      flat_profile_L2_percent=math.sqrt(num/den)*100)
    return result


def csv_float(path: Path) -> list[dict]:
    with path.open() as stream:
        return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(stream)]


def completion_status(records: dict, comparisons: list[dict]) -> dict:
    """Execution closure, reference qualification and comparison are distinct."""
    states=[r['status'] for r in records.values()]
    all_finished=all(s not in ('NOT_EXECUTED','RUN_INCOMPLETE') for s in states)
    comparable=all(d['status'] in ('PASS','FAIL') for d in comparisons)
    failed=any(s in ('REFERENCE_CHECK_FAIL','INVALID_EVIDENCE','EXECUTION_FAILED_OR_NO_EVIDENCE') for s in states)
    failed=failed or any(d.get('reference_accepted') is False for d in comparisons)
    if all(s=='NOT_EXECUTED' for s in states):
        status='INCOMPLETE';execution='NOT_STARTED'
    elif all_finished:
        status='COMPLETE' if comparable else 'COMPLETE_WITH_REFERENCE_FAILURE'
        execution='FIXED_SET_FINISHED'
    elif failed:
        status='STOPPED_ON_FAILURE';execution='STOPPED_ON_FAILURE'
    else:
        status='INCOMPLETE';execution='PARTIAL'
    return dict(status=status,execution_status=execution,all_planned_records_finished=all_finished,
                execution_closed=all_finished or failed,comparison_evaluable=comparable,
                automatic_followup_authorized=False)


def read_case(case: Path, release_sha: str | None=None, executable_sha: str | None=None) -> dict:
    meta=json.loads((case/'case.json').read_text())
    evidence=case/'referenceEvidence'
    if not (evidence/'cells.csv').exists():
        runtime_receipt=case/'runtime/receipt.json'
        if runtime_receipt.exists():
            record=json.loads(runtime_receipt.read_text())
            return dict(case_id=meta['case_id'],status='EXECUTION_FAILED_OR_NO_EVIDENCE',
                        independent_exit_code=record.get('independent_exit_code'),run_id=record.get('run_id'))
        if (case/'runtime/started.json').exists():
            return dict(case_id=meta['case_id'],status='RUN_INCOMPLETE')
        return dict(case_id=meta['case_id'],status='NOT_EXECUTED')
    values=metrics(meta,csv_float(evidence/'cells.csv'),
                   csv_float(evidence/'x_faces.csv') if meta['direction']=='T' else [])
    # A CSV and a normal solver End are insufficient runtime provenance.
    receipt_path=evidence/'receipt.json'
    problems=[]
    if not receipt_path.exists():
        problems.append('independent runtime receipt missing')
    else:
        receipt=json.loads(receipt_path.read_text())
        if not receipt.get('run_id') or receipt.get('independent_exit_code')!=0:
            problems.append('run identity/independent exit code invalid')
        if receipt.get('case_id')!=meta['case_id']:
            problems.append('receipt case identity mismatch')
        if not receipt.get('solver_converged',False):
            problems.append('steady stopping criterion not reached')
        expected_files=['cells.csv']+(['x_faces.csv'] if meta['direction']=='T' else [])
        for fn in expected_files:
            digest=hashlib.sha256((evidence/fn).read_bytes()).hexdigest()
            if receipt.get('evidence_sha256',{}).get(fn)!=digest:
                problems.append('runtime evidence hash mismatch: '+fn)
        if not receipt.get('source_manifest_sha256') or not receipt.get('executable_sha256'):
            problems.append('source/executable runtime binding missing')
        if receipt.get('source_manifest_sha256')!=release_sha or receipt.get('executable_sha256')!=executable_sha:
            problems.append('receipt does not match the frozen release and executable')
        if not receipt.get('release_unchanged') or not receipt.get('disk_budget_met'):
            problems.append('runtime release/disk checks not satisfied')
        for fn in ('log.blockMesh','log.checkMesh','log.solver','resource.txt','exit_code.txt','release_snapshot.json'):
            path=case/'runtime'/fn
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=receipt.get('runtime_logs_sha256',{}).get(fn):
                problems.append('missing or changed runtime record: '+fn)
        snapshot=case/'runtime/release_snapshot.json'
        if not snapshot.is_file() or hashlib.sha256(snapshot.read_bytes()).hexdigest()!=receipt.get('source_manifest_sha256'):
            problems.append('runtime release snapshot does not match source manifest')
        exitfile=case/'runtime/exit_code.txt'
        if not exitfile.is_file() or exitfile.read_text().strip()!='0':
            problems.append('independent exit-code file missing or nonzero')
        native=receipt.get('native_field_sha256',{})
        names=('v',) if meta['direction']=='P' else ('U','p','phi')
        if len(native)!=len(names) or {Path(p).name for p in native}!=set(names):
            problems.append('complete final native field set is missing')
        if len({str(Path(p).parent) for p in native})!=1:
            problems.append('native fields do not share a final time directory')
        for rel,expected in native.items():
            path=case/rel
            if not path.resolve().is_relative_to(case.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                problems.append('missing or changed native field: '+rel)
        meshhash=receipt.get('mesh_sha256',{})
        if set(meshhash)!=set(('points','faces','owner','neighbour','boundary')):
            problems.append('complete native mesh binding missing')
        for fn,expected in meshhash.items():
            path=case/'constant/polyMesh'/fn
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                problems.append('missing or changed native mesh: '+fn)
        meshlog=case/'runtime/log.checkMesh'
        solverlog=case/'runtime/log.solver'
        if not meshlog.is_file() or 'Mesh OK.' not in meshlog.read_text():
            problems.append('mesh was not independently accepted')
        if not solverlog.is_file() or 'solution converged' not in solverlog.read_text().lower():
            problems.append('steady convergence not verified in actual log')
    finest=meta['level'] in ('fine','tight','flat')
    if finest and values['power_balance_percent']>0.1:
        problems.append('power vs dissipation exceeds 0.1 percent')
    if finest and values['section_flux_spread_percent']>0.1:
        problems.append('section spread exceeds 0.1 percent')
    if finest and values.get('section_vs_volume_percent',0)>0.1:
        problems.append('corrected face flux vs volume transport exceeds 0.1 percent')
    if meta['d_nm']==0:
        if values['flat_K_error_percent']>0.1 or values['flat_profile_L2_percent']>0.1:
            problems.append('flat analytic comparison exceeds 0.1 percent')
    return dict(case_id=meta['case_id'],status='REFERENCE_CHECK_FAIL' if problems else 'LOCAL_CHECKS_PASS',
                issues=problems,metrics=values)


def assess(root: Path=ROOT) -> dict:
    manifest=json.loads((root/'prepared_manifest.json').read_text())
    drift=[fn for fn,digest in manifest['sha256'].items()
           if not (root/fn).is_file() or hashlib.sha256((root/fn).read_bytes()).hexdigest()!=digest]
    if drift:
        return dict(status='INPUT_DRIFT',paths=drift)
    release=root/'release_manifest.json'
    if release.is_file():
        release_data=json.loads(release.read_text())
        bad=[fn for fn,dg in release_data['sha256'].items()
             if not (root/fn).is_file() or hashlib.sha256((root/fn).read_bytes()).hexdigest()!=dg]
        bad += [fn for fn,dg in release_data.get('external_sha256',{}).items()
                if not Path(fn).is_file() or hashlib.sha256(Path(fn).read_bytes()).hexdigest()!=dg]
        if bad:return dict(status='RELEASE_DRIFT',paths=bad)
    release_sha=hashlib.sha256(release.read_bytes()).hexdigest() if release.is_file() else None
    executable_sha=json.loads(release.read_text())['sha256'].get('bin/paper1StokesReference') if release.is_file() else None
    records={}
    for meta in manifest['cases']:
        cid=meta['case_id']
        try:
            records[cid]=read_case(root/'prepared'/cid,release_sha,executable_sha)
        except (ValueError,KeyError,OSError) as error:
            records[cid]=dict(case_id=cid,status='INVALID_EVIDENCE',issues=[str(error)])
    flat_ok=all(records[f'h75_d0_{di}_flat']['status']=='LOCAL_CHECKS_PASS' for di in ('P','T'))
    anchors=json.loads((root/'comparison_inputs.json').read_text())
    decisions=[]
    for anchor in anchors:
        stem=f"h{anchor['h_nm']}_d{anchor['d_nm']}_{anchor['direction']}"
        group=[records[stem+'_'+lev] for lev in ('coarse','mid','fine','tight')]
        decision=dict(point=stem,status='NOT_ASSESSABLE')
        if flat_ok and all(r['status']=='LOCAL_CHECKS_PASS' for r in group):
            k1,k2,k3,kt=[r['metrics']['K_m3'] for r in group]
            d21=abs(k2/k1-1)*100;d32=abs(k3/k2-1)*100;alg=abs(kt/k3-1)*100
            reference_ok=d21<=1 and d32<=.5 and (d32<=d21 or max(d21,d32)<=.05) and alg<=.05
            decision.update(grid_mid_coarse_percent=d21,grid_fine_mid_percent=d32,
                            algebraic_change_percent=alg,reference_accepted=reference_ok)
            if reference_ok:
                delta=(anchor['K5_m3']/k3-1)*100
                decision.update(status='PASS' if abs(delta)<=2 else 'FAIL',delta_K_percent=delta,Kref_m3=k3)
                h,d=[anchor[k]*1e-9 for k in ('h_nm','d_nm')]
                aa,bb=h**3,(h+d)**3
                klc=(aa+bb)/24 if anchor['direction']=='P' else aa*bb/(6*(aa+bb))
                factor=1/(1+(1.7685*(d/120e-9)**1.6331 if anchor['direction']=='P' else .49*(d/120e-9)**.699))
                e0=(klc/k3-1)*100;e2=(factor*klc/k3-1)*100
                decision.update(LC_error_percent=e0,V2_error_percent=e2,V2_improved=abs(e2)<abs(e0))
        decisions.append(decision)
    baseline=[d for d in decisions if d['point'].startswith('h75_d100_')]
    output=dict(**completion_status(records,decisions),
                scientific_gate='NOT_A_GLOBAL_REFERENCE_QUALIFICATION',cases=records,comparisons=decisions,
                selected_six_all_pass=all(d['status']=='PASS' for d in decisions))
    if all('Kref_m3' in d for d in baseline):
        pp=next(d for d in baseline if d['point'].endswith('_P'));tt=next(d for d in baseline if d['point'].endswith('_T'))
        Aref=pp['Kref_m3']/tt['Kref_m3']
        a5=next(a for a in anchors if a['direction']=='P' and a['h_nm']==75)['K5_m3']/next(a for a in anchors if a['direction']=='T' and a['h_nm']==75)['K5_m3']
        da=(a5/Aref-1)*100
        b5,bref=[math.degrees(math.atan(1/a)) for a in (a5,Aref)]
        h,d=75e-9,100e-9
        aa,bb=h**3,(h+d)**3
        alc=((aa+bb)/24)/(aa*bb/(6*(aa+bb)))
        blc=math.degrees(math.atan(1/alc))
        output['baseline']=dict(Aref=Aref,A5=a5,A_difference_percent=da,beta_ref_deg=bref,
                                beta5_deg=b5,beta_difference_deg=b5-bref,
                                A_pass=abs(da)<=2,beta_pass=abs(b5-bref)<=.40,
                                ALC=alc,ALC_vs_reference_percent=(alc/Aref-1)*100,
                                betaLC_deg=blc,betaLC_minus_reference_deg=blc-bref,
                                evidence_role='derived from the same two main conductances')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite an assessment')
    result=assess()
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(result['status'])
