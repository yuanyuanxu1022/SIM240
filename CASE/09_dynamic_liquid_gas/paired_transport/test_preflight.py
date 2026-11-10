"""Regression checks for blocking unsupported GHY runs and mismatched directions."""
import copy
import json
import unittest
from pathlib import Path
import preflight

ROOT = Path(__file__).resolve().parent


class PreparationGuards(unittest.TestCase):
    def setUp(self):
        self.shared = json.loads((ROOT / "shared_case.json").read_text())
        self.xcase = json.loads((ROOT / "Kxx/case.json").read_text())
        self.ycase = json.loads((ROOT / "Kyy/case.json").read_text())
        self.material = json.loads((ROOT / self.shared["material_profile"]).read_text())

    def test_current_GHY_is_blocked_without_simulation(self):
        report = preflight.audit(ROOT)
        self.assertTrue(report["pair_structure_consistent"])
        self.assertFalse(report["preparation_complete"])
        self.assertFalse(report["simulation_started"])
        self.assertTrue(any("liquid_density" in m for m in report["missing_preparation_evidence"]))
        self.assertTrue(any("water_presence" in m for m in report["missing_preparation_evidence"]))

    def test_material_overrides_cannot_silently_differ(self):
        altered = copy.deepcopy(self.ycase)
        altered["viscosity_Pa_s"] = 0.015
        self.assertTrue(preflight.pair_issues(self.shared, self.xcase, altered))

    def test_wrong_axis_or_checkpoint_override_rejected(self):
        altered = copy.deepcopy(self.ycase)
        altered["drive_unit_vector"] = [1, 0, 0]
        self.assertTrue(preflight.pair_issues(self.shared, self.xcase, altered))
        altered = copy.deepcopy(self.ycase)
        altered["initial_checkpoint"] = "different_state"
        self.assertTrue(preflight.pair_issues(self.shared, self.xcase, altered))

    def test_candidate_and_nonfinite_values_do_not_become_verified(self):
        self.assertTrue(any("liquid_dynamic_viscosity" in m for m in preflight.material_issues(self.material)))
        for value in (float("nan"), float("inf"), -1.0, 0, True):
            self.assertFalse(preflight.positive(value))
        altered = copy.deepcopy(self.material)
        altered["liquid_density"].update(value=float("nan"), status="verified", source="test_only")
        self.assertTrue(any("liquid_density" in m for m in preflight.material_issues(altered)))

    def test_angle_units_and_BGK_mapping_are_checked(self):
        altered = copy.deepcopy(self.material)
        altered["mold"]["contact_angle_through_liquid"].update(value=90, unit="rad", status="verified", source="test_only")
        self.assertTrue(any("mold.contact_angle" in m for m in preflight.material_issues(altered)))
        self.assertTrue(preflight.mapping_issues(self.shared, self.material))
        # Synthetic arithmetic fixture, not GHY data or a physical validation.
        fixture_material = copy.deepcopy(self.material)
        for name, value in {"liquid_density": 1000, "liquid_dynamic_viscosity": .012,
                            "gas_density": 1, "gas_dynamic_viscosity": 1.8e-5,
                            "liquid_gas_surface_tension": .03}.items():
            fixture_material[name]["value"] = value
        fixture_shared = copy.deepcopy(self.shared)
        fixture_shared["numerics"].update(dx_m=5e-9, dt_s=1e-13, tau_liquid=.644,
                                          tau_gas=.716, surface_tension_lattice=2.4e-6)
        self.assertEqual(preflight.mapping_issues(fixture_shared, fixture_material), [])
        fixture_shared["numerics"]["surface_tension_lattice"] *= 10
        self.assertTrue(preflight.mapping_issues(fixture_shared, fixture_material))


if __name__ == "__main__":
    unittest.main()
