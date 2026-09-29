"""Public-source candidate slices with wholly synthetic observations."""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR, check_sysml

PUBLIC = ROOT / "examples/sysml/public"


def record(name):
    return (PUBLIC / f"{name}-candidate.sysml",
            json.loads((PUBLIC / f"{name}-manifest.json").read_text()),
            json.loads((PUBLIC / f"{name}-evidence.json").read_text()))


@unittest.skipUnless(JAR.is_file() and (CLASSES / "SysmlBridge.class").is_file(),
                     "Run python3 scripts/install_sysml_parser.py to enable parser integration tests")
class PublicSysmlTests(unittest.TestCase):
    def test_fhwa_correlated_deadline_slice(self):
        model, manifest, evidence = record("fhwa-response")
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=evidence, review=True)["status"], "pass")
        wrong_id = copy.deepcopy(evidence)
        wrong_id["events"][-1]["requestId"] = "C"
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=wrong_id, review=True)["status"], "fail")
        late = copy.deepcopy(evidence)
        late["events"][-1]["time"] = "60.001"
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=late, review=True)["status"], "fail")
        prefix = copy.deepcopy(evidence)
        prefix["events"].pop()
        prefix["observed_until"] = {"time": "59", "unit": "seconds"}
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=prefix, review=True)["status"], "unknown")

    def test_nasa_partial_until_slice_and_known_gap(self):
        model, manifest, evidence = record("nasa-low-power")
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=evidence, review=True)["status"], "pass")
        early_loss = copy.deepcopy(evidence)
        early_loss["observations"][2]["NASALowPowerCandidate::element::lowPowerConfiguration"] = False
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=early_loss, review=True)["status"], "fail")
        no_release = copy.deepcopy(evidence)
        no_release["observations"] = no_release["observations"][:3]
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=no_release, review=True)["status"], "unknown")
        early_power = copy.deepcopy(evidence)
        early_power["observations"][0]["NASALowPowerCandidate::element::supplementaryPowerAvailable"] = True
        self.assertEqual(check_sysml(model, manifest=manifest, evidence=early_power, review=True)["status"], "pass")

    def test_public_candidate_test_generation_scope(self):
        nasa, nasa_manifest, _ = record("nasa-low-power")
        generated = check_sysml(nasa, manifest=nasa_manifest, generate_tests=True)
        self.assertEqual(generated["test_generation"]["status"], "pass")
        clause = generated["test_generation"]["results"]["R_NASA_LOW__holdUntilPower"]
        self.assertEqual(clause["coverage"], {"referenced": 3, "witnessed": 3})
        fhwa, fhwa_manifest, _ = record("fhwa-response")
        unsupported = check_sysml(fhwa, manifest=fhwa_manifest, generate_tests=True)
        self.assertEqual(unsupported["test_generation"]["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
