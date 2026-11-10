import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import audit_existing as audit


class ExistingAuditTests(unittest.TestCase):
    def test_three_sources_are_mechanical_pinned_variants(self):
        for height in (50,75,125):
            actual = audit.G3 / "build/generated" / f"g3_ex240_h{height}.cpp"
            self.assertEqual(actual.read_text(), audit.expected_g3_source(height))

    def test_f2_shift_is_explicit_not_hidden(self):
        dest = audit.F2 / "results/f2_liquid_film_compression_h125_T_20260919T162951+0800"
        result = audit.frozen.parse_kv(dest / "result.txt")
        report = audit.diagnostics(dest / "diagnostics.csv", result, f2=True)
        self.assertFalse(report["schema_PASS"])
        self.assertLessEqual(report["window_std_recomputed"], 1e-6)

    def test_wrong_header_mapping_is_rejected(self):
        dest = audit.F2 / "results/f2_liquid_film_compression_h125_T_20260919T162951+0800"
        result = audit.frozen.parse_kv(dest / "result.txt")
        with self.assertRaises(RuntimeError):
            audit.diagnostics(dest / "diagnostics.csv", result, f2=False)

    def test_height_specific_field_coverage(self):
        dest = audit.G3 / "results/g3h_formal_h50_P_20260920T113426+0800"
        self.assertEqual(audit.height_field(dest / "field_slice.csv",50),3840)
        with self.assertRaises(RuntimeError):
            audit.height_field(dest / "field_slice.csv",75)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("sys.argv", ["audit_existing.py","--output-dir",tmp]):
                with self.assertRaises(RuntimeError):
                    audit.main()
            self.assertFalse(list(Path(tmp).iterdir()))


if __name__ == "__main__":
    unittest.main()
