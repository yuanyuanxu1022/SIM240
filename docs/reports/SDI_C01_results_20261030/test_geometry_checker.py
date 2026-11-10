"""Checker repair tests on synthetic data; no simulation launch."""
import importlib.util
import json
import unittest
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


new=load('geometry_repaired_checker',OUT/'check_results_geometry_v1_1.py')
old_tests=load('original_checker_tests',ROOT/'CASE/interface_static_darcy_v1/tests/test_checker.py')
old_tests.checker=new


class GeometryRecognitionTests(unittest.TestCase):
    def test_accepts_observed_scale_roundoff_without_altering_raw_values(self):
        data=old_tests.fixture();face=data[2][0]
        face['Sz_m2']=abs(face['Sx_m2'])*5.44e-14
        original=face.copy();report,_=new.evaluate(*data)
        self.assertTrue(report['interface_checks_satisfied']);self.assertEqual(face,original)

    def test_rejects_genuinely_tilted_face(self):
        data=old_tests.fixture();face=data[2][0];face['Sz_m2']=abs(face['Sx_m2'])*1e-5
        with self.assertRaises(ValueError):new.evaluate(*data)


if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(old_tests.CheckerTests),
                             unittest.defaultTestLoader.loadTestsFromTestCase(GeometryRecognitionTests)])
    with (OUT/'checker_repair_tests.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report=dict(kind='SYNTHETIC_CHECKER_TESTS_ONLY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                all_satisfied=result.wasSuccessful(),solver_run=False,scientific_thresholds_changed=False)
    (OUT/'checker_repair_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
