"""Rejection/provenance and analytic-expression checks; zero PDE solves."""
import ast
import copy
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contract import ROOT, Rejected, load_plan, select
from physics import flat_exact, mixed_mms, scalar_mms, topology_counts


class StaticPreparation(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "prepare.py"), *args],
                              capture_output=True, text=True, timeout=10)

    def test_bound_whitelist_and_default(self):
        plans = load_plan()
        self.assertEqual(len(plans), 18)
        self.assertEqual(sum(p["role"] == "base" for p in plans.values()), 12)
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertFalse(d["solver_called"])
        self.assertIsNone(d["actual_run_id"])

    def test_no_execution_or_unknown_modes(self):
        for args in [("--execute",), ("--mode", "solve"), ("--mode", "steady"),
                     ("--exec",), ("--planned-id", "G02"), ("--mode", "stage"),
                     ("--prep-id", "misleading_default"), ("--mode", "stage", "--prep-id", "../bad")]:
            self.assertNotEqual(self.cli(*args).returncode, 0, args)

    def test_source_binding_mismatch_rejected(self):
        # Inject a mismatched hash without touching original protected inputs.
        with patch("contract.sha256", return_value="0" * 64):
            with self.assertRaises(Rejected):
                load_plan()

    def test_altered_config_rejected(self):
        plan = select()[0]
        variants = []
        for k, value in [("execution_authorized", True), ("actual_run_id", "fake"),
                         ("true_relative_residual_target", 1e-4), ("extra", 1),
                         ("quadrature_degree", True), ("quadrature_degree", float("nan"))]:
            d = copy.deepcopy(plan); d[k] = value; variants.append(d)
        d = copy.deepcopy(plan); d["geometry"]["d_nm"] = 25; variants.append(d)
        for d in variants:
            with self.assertRaises(Rejected): select(supplied=d)
        with tempfile.TemporaryDirectory(prefix="d4-input-") as t:
            p = Path(t) / "input.json"
            for text in ["null", "[]", '{"planned_id":"x","planned_id":"y"}']:
                p.write_text(text)
                self.assertEqual(self.cli("--config", str(p)).returncode, 64)

    def test_unique_preparation_records_and_no_result(self):
        # A temporary direct child name tests the actual public path without
        # retaining synthetic fixtures as project progress evidence.
        parent = ROOT / "prepared_records"
        parent.mkdir(exist_ok=True)
        name = "static_test_" + uuid.uuid4().hex
        target = parent / name
        try:
            r = self.cli("--mode", "stage", "--prep-id", name)
            self.assertEqual(r.returncode, 0, r.stderr)
            manifest = json.loads((target / "PREPARATION.json").read_text())
            self.assertEqual(manifest["inputs_before"], manifest["inputs_after"])
            self.assertEqual(manifest["problem_count"], 18)
            self.assertFalse(manifest["solver_called"])
            self.assertEqual(len(list(target.glob("*/input.json"))), 18)
            self.assertEqual(len(list(target.glob("*/future_record_template.json"))), 18)
            self.assertFalse(list(target.rglob("result.json")))
            before = (target / "PREPARATION.json").read_bytes()
            r = self.cli("--mode", "stage", "--prep-id", name)
            self.assertEqual(r.returncode, 64)
            self.assertEqual(before, (target / "PREPARATION.json").read_bytes())
            for p in target.glob("*/future_record_template.json"):
                record = json.loads(p.read_text())
                self.assertEqual(record["record_kind"], "TEMPLATE_NOT_A_RESULT")
                self.assertFalse(record["RESULT_PASS"])
                self.assertTrue(all(v is None for v in record["measurements"].values()))
        finally:
            if target.is_dir(): shutil.rmtree(target)

    def test_output_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory(prefix="d4-output-") as t:
            r = self.cli("--mode", "stage", "--prep-id", "escape", "--output-parent", t)
            self.assertEqual(r.returncode, 64)
            self.assertEqual(list(Path(t).iterdir()), [])
        (ROOT / "prepared_records").mkdir(exist_ok=True)
        link = ROOT / "prepared_records" / ("static_link_" + uuid.uuid4().hex)
        link.symlink_to(ROOT)
        try:
            self.assertEqual(self.cli("--mode", "stage", "--prep-id", link.name).returncode, 64)
        finally:
            link.unlink()

    def test_geometry_units_and_counts(self):
        self.assertEqual(topology_counts(192, 60, True)["raw_dofs"], 104943)
        self.assertEqual(topology_counts(192, 60, True)["free_P2_trace_pairs_per_component"], 119)
        e = flat_exact()
        self.assertAlmostEqual(e["K_m3"] / (75e-9)**3, 1/12)
        self.assertAlmostEqual(e["R_Pa_s_m3"] * e["K_m3"], 0.001)

    def test_manufactured_boundaries_periodic_and_sources(self):
        # Independent central differences check explicit forcing signs; this
        # tests analytic functions, NOT FEM residuals or numerical convergence.
        step = 0.0002
        for x, z in [(0.17, 0.21), (0.83, 0.61), (1.73, 0.81)]:
            s = scalar_mms(x, z)
            lap = ((scalar_mms(x+step,z)["value"] - 2*s["value"] + scalar_mms(x-step,z)["value"])
                   + (scalar_mms(x,z+step)["value"] - 2*s["value"] + scalar_mms(x,z-step)["value"])) / step**2
            self.assertAlmostEqual(-lap, s["forcing"], delta=2e-6)
            m = mixed_mms(x,z)
            for j in (0,1):
                lap = sum((mixed_mms(x+dx,z+dz)["velocity"][j] - 2*m["velocity"][j]
                           + mixed_mms(x-dx,z-dz)["velocity"][j]) / step**2
                          for dx,dz in [(step,0),(0,step)])
                dx,dz = [(step,0),(0,step)][j]
                gradp = (mixed_mms(x+dx,z+dz)["pressure"] - mixed_mms(x-dx,z-dz)["pressure"]) / (2*step)
                self.assertAlmostEqual(-lap+gradp,m["forcing"][j],delta=3e-6)
        for z in [0,.19,.71,1]:
            self.assertAlmostEqual(scalar_mms(0,z)["value"],scalar_mms(2,z)["value"])
            for k in ["velocity","pressure"]:
                if k == "pressure":
                    self.assertEqual(mixed_mms(0,z)[k], mixed_mms(2,z)[k])
                else:
                    for a,b in zip(mixed_mms(0,z)[k], mixed_mms(2,z)[k]):
                        self.assertAlmostEqual(a,b,delta=1e-14)
        for z in [0,1]:
            self.assertEqual(scalar_mms(.31,z)["value"],0)
            self.assertTrue(all(abs(a)<1e-14 for a in mixed_mms(.31,z)["velocity"]))

    def test_syntax_and_no_solve_calls_in_package(self):
        forbidden = {"solve", "collideAndStream", "assemble_matrix", "assemble_vector",
                     "create_rectangle", "create_unit_square", "LinearProblem", "NonlinearProblem"}
        files = [ROOT/"prepare.py", *(ROOT/"src").glob("*.py"), ROOT/"environment/probe_backend.py"]
        for p in files:
            tree = ast.parse(p.read_text(), filename=str(p))
            compile(tree, str(p), "exec")
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func,"id","")
                    self.assertNotIn(name,forbidden,str(p))


if __name__ == "__main__":
    unittest.main(verbosity=2)
