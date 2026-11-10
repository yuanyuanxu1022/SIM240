"""Geometry and case-selection regression tests; no flow solver is launched."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import test_checker as baseline


class GeometryReleaseTests(unittest.TestCase):
    def test_roundoff_faces_accepted_without_data_change(self):
        data=baseline.fixture();face=data[2][0];face['Sz_m2']=abs(face['Sx_m2'])*5.44e-14
        before=face.copy();report,_=baseline.checker.evaluate(*data)
        self.assertTrue(report['interface_checks_satisfied']);self.assertEqual(face,before)

    def test_real_tilt_rejected(self):
        data=baseline.fixture();face=data[2][0];face['Sz_m2']=abs(face['Sx_m2'])*1e-5
        with self.assertRaises(ValueError):baseline.checker.evaluate(*data)

    def test_unprepared_case_rejected(self):
        with tempfile.TemporaryDirectory(prefix='sdi_checker_fixture_') as tmp:
            root=Path(tmp);(root/'run_manifest.json').write_text(json.dumps(dict(case_id='C03',protocol_id='SDI-v1')))
            with self.assertRaisesRegex(ValueError,'Not a supported'):baseline.checker.check_run(root)

    def test_C02_manifest_cannot_accept_C01_input(self):
        with tempfile.TemporaryDirectory(prefix='sdi_checker_fixture_') as tmp:
            root=Path(tmp);(root/'common').mkdir()
            (root/'run_manifest.json').write_text(json.dumps(dict(case_id='C02',protocol_id='SDI-v1',files=[])))
            # Explicitly synthetic bookkeeping to exercise the case-id guard only.
            (root/'execution.json').write_text(json.dumps(dict(status='completed',steps=[dict(label='two_dimensional',exit_code=0),dict(label='openfoam',exit_code=0)])))
            cfg=json.loads((baseline.ROOT/'common/C02.json').read_text());cfg['case_id']='C01'
            (root/'common/C02.json').write_text(json.dumps(cfg))
            shutil.copy2(baseline.ROOT/'common/protocol.json',root/'common/protocol.json')
            with self.assertRaisesRegex(ValueError,'Unsupported configuration'):baseline.checker.check_run(root)


if __name__=='__main__':unittest.main()
