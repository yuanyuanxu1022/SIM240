"""R1/R2 regressions: artificial declarations/captures, no native execution."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from evidence import EvidenceError, sha
from contracts import release_inputs, time_stepping_defines
import check_results as checker
from fixtures_contract import CASE, ContractFixture


class ResidualTests(unittest.TestCase):
    def cli(self, root, release, out, batch=False):
        raw = root / 'raw'
        raw.mkdir(exist_ok=True)
        cmd = [sys.executable, '-B', str(CASE / 'analysis/check_results.py')]
        if batch:
            paths = []
            for i in range(24):
                p = root / f'raw_{i}'
                p.mkdir(exist_ok=True)
                paths.append(str(p))
            index = root / 'index.json'
            index.write_text(json.dumps(paths))
            cmd += ['--batch-index', str(index)]
        else:
            cmd += ['--run', str(raw)]
        cmd += ['--release', str(release), '--release-sha256', sha(release), '--out', str(out)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1'))

    def test_R1_malformed_other_run_does_not_write_inside_valid_baseline(self):
        for batch in (False, True):
            with self.subTest(batch=batch), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); baseline = root / 'baseline'; baseline.mkdir()
                marker = baseline / 'marker'; marker.write_text('SYNTHETIC protected bytes\n')
                release = root / 'SYNTHETIC_NOT_AN_EXECUTION_RELEASE.json'
                release.write_text(json.dumps(dict(inputs_sha256={}, approved_runs=[{}],
                    h75_regression_references={'P': {'directory': str(baseline)}})))
                out = baseline / 'analysis_malformed'
                proc = self.cli(root, release, out, batch)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn('incomplete run output declaration', proc.stderr)
                self.assertFalse(out.exists())
                self.assertEqual(list(baseline.iterdir()), [marker])
                self.assertEqual(marker.read_text(), 'SYNTHETIC protected bytes\n')

    def test_R1_malformed_reference_rejected_before_even_safe_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); release = root / 'SYNTHETIC.json'
            release.write_text(json.dumps(dict(inputs_sha256={},
                approved_runs=[{'output_directory': str(root / 'other')}],
                h75_regression_references={'P': {'directory': str(root / 'old')}, 'T': {}})))
            out = root / 'otherwise_safe_output'
            proc = self.cli(root, release, out)
            self.assertEqual(proc.returncode, 2)
            self.assertIn('incomplete reference directory declaration', proc.stderr)
            self.assertFalse(out.exists())

    def test_R1_invalid_documents_never_become_empty_protection(self):
        invalid = ['{', '[]', 'null', '{"inputs_sha256": []}',
                   '{"approved_runs": {}}', '{"approved_runs": [null]}',
                   '{"approved_runs": [{"output_directory": null}]}',
                   '{"h75_regression_references": []}',
                   '{"h75_regression_references": {"P": {"directory": ""}}}']
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'SYNTHETIC.json'
            for text in invalid:
                with self.subTest(text=text):
                    p.write_text(text)
                    with self.assertRaises(EvidenceError):
                        release_inputs(p)
            with self.assertRaises(EvidenceError):
                release_inputs(Path(tmp) / 'missing.json')

    def test_R1_complete_declarations_preserve_all_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / 'SYNTHETIC.json'
            paths = [str(root / name) for name in ['input', 'run', 'baseline']]
            p.write_text(json.dumps(dict(inputs_sha256={paths[0]: 'synthetic'},
                approved_runs=[{'output_directory': paths[1]}],
                h75_regression_references={'P': {'directory': paths[2]}})))
            self.assertEqual(release_inputs(p), paths)

    def test_R2_complete_binding_accepts_joined_and_split_single_zero(self):
        for option in ['-DURV_PREPARATION_ONLY=0', '-D URV_PREPARATION_ONLY=0']:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as tmp:
                f = ContractFixture(tmp)
                f.env['compile_command'] = 'compiler ' + option + ' -c urv_reference.cpp'
                f.refresh()
                checker.binding(f.path, sha(f.path))

    def test_R2_complete_binding_rejects_ambiguous_definitions(self):
        invalid = ['-DURV_PREPARATION_ONLY=0 -D URV_PREPARATION_ONLY=1',
                   '-DURV_PREPARATION_ONLY=0 -U URV_PREPARATION_ONLY',
                   '-D URV_PREPARATION_ONLY=0 -DURV_PREPARATION_ONLY=0',
                   '-DURV_PREPARATION_ONLY=0 -D URV_PREPARATION_ONLY=0',
                   '-DURV_PREPARATION_ONLY=0 -UURV_PREPARATION_ONLY',
                   '-DURV_PREPARATION_ONLY=1', '-D URV_PREPARATION_ONLY=1',
                   '-DURV_PREPARATION_ONLY', '-D URV_PREPARATION_ONLY',
                   '-DURV_PREPARATION_ONLY_OTHER=0',
                   '-DURV_PREPARATION_ONLY=0 -D',
                   '-DURV_PREPARATION_ONLY=0 -U -c',
                   '-DURV_PREPARATION_ONLY=0 -D "URV_PREPARATION_ONLY(x)=0"']
        for option in invalid:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as tmp:
                f = ContractFixture(tmp)
                f.env['compile_command'] = 'compiler ' + option + ' -c urv_reference.cpp'
                f.refresh()
                with self.assertRaises(EvidenceError):
                    checker.binding(f.path, sha(f.path))

    def test_R2_other_macro_names_are_not_target_macro(self):
        self.assertEqual(time_stepping_defines(
            'compiler -DURV_PREPARATION_ONLY_OTHER=1 -D URV_PREPARATION_ONLY=0'),
            [('-D', 'URV_PREPARATION_ONLY=0')])


if __name__ == '__main__':
    unittest.main()
