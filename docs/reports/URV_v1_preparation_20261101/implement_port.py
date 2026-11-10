#!/usr/bin/env python3
"""One-time reproducible, reversible measurement-only port; never runs a solver."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DEST = ROOT/'CASE/unseen_v2_reference_v1'
BASE = ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/src'
C = ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1'
OLD = ROOT/'docs/reports/Unseen_V2_reference_protocol_20261101'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if DEST.exists():
        raise FileExistsError(DEST)
    protected = dict(json.loads((OLD/'preparation_bindings.json').read_text())['files'])
    for p in [*OLD.rglob('*'), *(ROOT/'docs/reports/C_h75_reference_review_20261101').rglob('*')]:
        if p.is_file(): protected[str(p)] = sha(p)
    assert all(sha(p)==s for p,s in protected.items())
    (OUT/'protected_inputs_before.json').write_text(json.dumps(protected,indent=2)+'\n')
    for d in ['src','scripts','analysis','tests','common','build','audits','evidence']:
        (DEST/d).mkdir(parents=True)
    for f in ['PROTOCOL.md','protocol.json','acceptance_spec.json','case_matrix.csv',
              'model_predictions_before_reference.csv','prediction_seal.json',
              'data_history_status.json','preparation_bindings.json']:
        shutil.copy2(OLD/f, DEST/'common'/f)
    (DEST/'common/adoption.json').write_text(json.dumps(dict(protocol_id='URV-v1',
        adopted_for='isolated implementation, compilation and zero-step audit only',
        user_instruction='按采用的 URV-v1 实现隔离参考程序和独立检查器，完成编译与零步审计，保持正式计算未启动。',
        formal_execution_authorized=False, actual_solver_run_ids=[],
        author_external_data_history_confirmation='PENDING',
        original_protocol_materials_preserved=True),ensure_ascii=False,indent=2)+'\n')
    for f in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        (OUT/'before').mkdir(exist_ok=True)
        shutil.copy2(ROOT/'docs/reports'/f, OUT/'before'/f)
    shutil.copy2(C/'src/mass_stats.h',DEST/'src/mass_stats.h')
    shutil.copy2(C/'scripts/test_mass_stats.cpp',DEST/'tests/test_mass_stats.cpp')
    original=(BASE/'variable_groove_transport.cpp').read_text()
    source=original
    edits=[]
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1, (old[:100],source.count(old))
        source=source.replace(old,new)
        edits.append(dict(old=old,new=new))
    replace('#include <olb.h>', '#include <olb.h>\n#include "mass_stats.h"\n\n#ifndef URV_PREPARATION_ONLY\n#define URV_PREPARATION_ONLY 1\n#endif')
    replace('using T = double;', 'using T = double;\nusing fine_t_stat::NeumaierSum;\nlong long actualCollideAndStreamCalls = 0;\nstruct ExecutionAudit {\n  std::filesystem::path directory;\n  ~ExecutionAudit() {\n    std::ofstream out(directory/"execution_audit.txt");\n    out << "protocol=URV-v1\\npreparation_only_build=" << URV_PREPARATION_ONLY\n        << "\\ncollide_and_stream_calls=" << actualCollideAndStreamCalls << "\\n";\n  }\n};')
    replace('  p.runId=c.at("run_id");', '#if URV_PREPARATION_ONLY\n  if (p.mode=="steady") throw std::runtime_error("URV-v1 preparation build: formal time stepping is disabled");\n#endif\n  p.runId=c.at("run_id");')
    replace('    effectiveConfig(p);', '    effectiveConfig(p);') if False else None
    replace('  if (p.mode=="describe") return 0;', '  ExecutionAudit executionAudit{p.outputDirectory};\n  if (p.mode=="describe") return 0;')
    replace('  T mass = 0.0;', '  T mass = 0.0; // Original sequential mass, retained verbatim.\n  T correctedMass = 0.0;\n  T densityDelta = 0.0;')
    replace('  Measurement value;','  Measurement value;\n  NeumaierSum correctedMass;\n  NeumaierSum densityDelta;')
    replace('      value.mass += rho * rhoPhys * dx * dx * dx;', '      value.mass += rho * rhoPhys * dx * dx * dx;\n      correctedMass.add(rho * rhoPhys * dx * dx * dx);\n      densityDelta.add(rho - 1.0);')
    replace('  for (int iD = 0; iD < 3; ++iD) {\n    value.meanVelocity', '  value.correctedMass = correctedMass.value();\n  value.densityDelta = densityDelta.value();\n  value.finite = value.finite && std::isfinite(value.correctedMass)\n    && std::isfinite(value.densityDelta);\n  for (int iD = 0; iD < 3; ++iD) {\n    value.meanVelocity')
    replace('      <<"frames_written="<<written.size()<<\'\\n\';', '''      <<"frames_written="<<written.size()<<'\\n'
      <<"mass="<<zero.mass<<'\\n'<<"corrected_mass="<<zero.correctedMass<<'\\n'
      <<"density_delta="<<zero.densityDelta<<'\\n'
      <<"J_vector_m2_s="<<zero.fluxJ[0]<<','<<zero.fluxJ[1]<<','<<zero.fluxJ[2]<<'\\n'
      <<"max_density_deviation="<<zero.maxDensityDeviation<<'\\n'
      <<"max_Mach="<<zero.maxLatticeSpeed/std::sqrt(T(1.0/3.0))<<'\\n'
      <<"exit_code="<<(zero.finite?0:3)<<'\\n';''')
    replace('       "window_cross_abs_max,finite\\n";', '       "window_cross_abs_max,finite,corrected_mass,corrected_mass_error,"\n       "delta_mass_error,mass_ledger_agreement,density_delta\\n";')
    replace('  T maxMassError = 0.0;', '  T maxMassError = 0.0; // Legacy ledger has its own unchanged denominator.\n  T maxCorrectedMassError = 0.0;\n  T maxDeltaMassError = 0.0;\n  T maxMassLedgerAgreement = 0.0;\n  bool allMeasurementsFinite = true;')
    replace('      lattice.collideAndStream();','      lattice.collideAndStream();\n      ++actualCollideAndStreamCalls;')
    replace('    const T massError = (state.mass - initial.mass) / initial.mass;', '''    const T massError = (state.mass - initial.mass) / initial.mass;
    const T correctedMassError =
      (state.correctedMass - initial.correctedMass) / initial.correctedMass;
    const T deltaMassError =
      (state.densityDelta - initial.densityDelta)
      / (initial.fluidNodes + initial.densityDelta);
    const T massLedgerAgreement = std::abs(correctedMassError - deltaMassError);''')
    replace('    maxMassError = std::max(maxMassError, std::abs(massError));', '''    maxMassError = std::max(maxMassError, std::abs(massError));
    maxCorrectedMassError = std::max(maxCorrectedMassError, std::abs(correctedMassError));
    maxDeltaMassError = std::max(maxDeltaMassError, std::abs(deltaMassError));
    maxMassLedgerAgreement = std::max(maxMassLedgerAgreement, massLedgerAgreement);
    allMeasurementsFinite = allMeasurementsFinite && state.finite
      && std::isfinite(massError) && std::isfinite(correctedMassError)
      && std::isfinite(deltaMassError) && std::isfinite(massLedgerAgreement);''')
    replace("                << state.finite << '\\n';", "                << state.finite << ',' << state.correctedMass << ','\n                << correctedMassError << ',' << deltaMassError << ','\n                << massLedgerAgreement << ',' << state.densityDelta << '\\n';")
    replace('    && maxMassError < massTolerance', '    && allMeasurementsFinite\n    && maxCorrectedMassError < massTolerance\n    && maxMassLedgerAgreement <= 1.0e-13')
    replace('          << "Case,direction,dx,tau,force,J,Keff,R_eff,Mach,mass_error\\n"', '          << "Case,direction,dx,tau,force,J,Keff,R_eff,Mach,mass_error,"\n             "legacy_mass_error,mass_ledger_agreement\\n"')
    replace("          << resistance << ',' << maxMach << ',' << maxMassError << '\\n';", "          << resistance << ',' << maxMach << ',' << maxCorrectedMassError\n          << ',' << maxMassError << ',' << maxMassLedgerAgreement << '\\n';")
    replace('         << "max_mass_abs_relative=" << maxMassError << \'\\n\'', '''         << "mass_gate_statistic=Neumaier_physical_mass\\n"
         << "max_mass_abs_relative=" << maxCorrectedMassError << '\\n'
         << "legacy_max_mass_abs_relative=" << maxMassError << '\\n'
         << "legacy_mass_gate_PASS=" << (maxMassError < massTolerance) << '\\n'
         << "max_delta_mass_abs_relative=" << maxDeltaMassError << '\\n'
         << "max_mass_ledger_agreement=" << maxMassLedgerAgreement << '\\n'
         << "all_measurements_finite=" << allMeasurementsFinite << '\\n' ''')
    (DEST/'src/urv_reference.cpp').write_text(source)
    # Reverse every edit to prove that no unlisted physical edits occurred.
    restored=source
    for edit in reversed(edits):
        assert restored.count(edit['new'])==1
        restored=restored.replace(edit['new'],edit['old'])
    assert restored==original
    (OUT/'source_port_edits.json').write_text(json.dumps(dict(edits=edits,
        base_source_sha256=sha(BASE/'variable_groove_transport.cpp'),
        port_source_sha256=sha(DEST/'src/urv_reference.cpp'),
        reverse_edits_restore_base_exactly=True),indent=2)+'\n')
    (OUT/'source_port.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),source.splitlines(True),fromfile='D4/original',tofile='URV/isolated')))
    make=(BASE/'Makefile').read_text().replace('variable_groove_transport','urv_reference')
    make=make.replace('-DPLATFORM_CPU_SISD','-DURV_PREPARATION_ONLY=1 -DPLATFORM_CPU_SISD')
    (DEST/'src/Makefile').write_text(make)
    (DEST/'.gitignore').write_text('/build/\n/audits/\n/results/\n__pycache__/\n*.pyc\n')
    print(json.dumps(dict(isolated_source_created=True,reversible_edits=len(edits),formal_execution_authorized=False)))

if __name__=='__main__': main()
