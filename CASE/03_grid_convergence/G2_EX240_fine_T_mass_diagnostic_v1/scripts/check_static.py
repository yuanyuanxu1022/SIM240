#!/usr/bin/env python3
"""Source/manifest checks only. Never build or invoke OpenLB."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[2]
BASE = ROOT / 'CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp'
BASE_SHA = '898cbe394a4528ae3ef925002ccb16eb33da433651276457e5913b128174281e'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1048576), b''):
            digest.update(chunk)
    return digest.hexdigest()


def tokens(source):
    # Preserve whitespace inside string/character literals; ignore layout only.
    return re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z0-9_]+|[^\s]', source)


def check():
    assert sha(BASE) == BASE_SHA, 'Frozen baseline changed'
    text = (CASE / 'src/fine_T_diagnostic.cpp').read_text()
    pattern = r'// FINE_T_DIAGNOSTIC_BEGIN (\w+)\n.*?// FINE_T_DIAGNOSTIC_END \1'
    matches = list(re.finditer(pattern, text, flags=re.S))
    names = [m.group(1) for m in matches]
    expected = ['include','observer_parameter','shape','material','density','restrict_target',
                'create_observer','begin_step','observe_step','record','diagnostic_cutoff','finish']
    assert names == expected, names
    restored = re.sub(pattern, '', text, flags=re.S)
    assert tokens(restored) == tokens(BASE.read_text()), 'Change outside diagnostic insertion blocks'
    assert text.count('lattice.collideAndStream();') == BASE.read_text().count('lattice.collideAndStream();') == 1
    assert text.count('setProcessingContext(') == BASE.read_text().count('setProcessingContext(')
    header = (CASE / 'src/mass_ledger.h').read_text()
    assert not re.search(r'\b(lattice|cell|geometry|setField|computeRho|collideAndStream|communicate)\s*\.', header)
    assert 'snapshotSteps{0,119,120,624,625,626,3732,3733,4000}' in header
    assert 'inline constexpr int lastStep = 4000;' in header
    assert 'LDBL_MANT_DIG' in header and 'Neumaier' in header and 'deltaLong' in header
    assert 'formal_reference_accepted=false' in header
    assert 'if (haveId && id <= lastId)' in header
    assert 'Refusing to overwrite diagnostic binary' in (CASE / 'src/Makefile').read_text()
    return {'source_insertions': names, 'baseline_restored_exact_except_whitespace': True,
            'collision_force_geometry_boundary_gates_unchanged_in_source': True,
            'snapshot_steps': [0,119,120,624,625,626,3732,3733,4000],
            'compilation_performed': False, 'solver_started': False,
            'runtime_equivalence_verified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-bound-inputs', action='store_true')
    args = parser.parse_args()
    output = check()
    if args.check_bound_inputs:
        binding = json.loads((CASE / 'reports/preparation_manifest.json').read_text())
        for path, digest in binding['protected_inputs'].items():
            assert Path(path).is_file() and sha(Path(path)) == digest, path
        for name, digest in binding['prepared_source_files'].items():
            assert sha(CASE/name) == digest, name
        for directory, names in binding['include_library_tree_file_sets'].items():
            assert sorted(str(p) for p in Path(directory).rglob('*') if p.is_file()) == names, directory
        head=subprocess.run(['git','-C','/home/dell/openlb','rev-parse','HEAD'],
                            text=True,capture_output=True,check=True).stdout.strip()
        assert head == binding['environment']['OpenLB_HEAD']
        output['bound_inputs_unchanged'] = True
        output['bound_files'] = len(binding['protected_inputs'])
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
