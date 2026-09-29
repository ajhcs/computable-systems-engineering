"""Parsed context slices and conservative change impact."""

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR
from verifier.views import diff_sysml, view_sysml


@unittest.skipUnless(JAR.is_file() and (CLASSES / "SysmlBridge.class").is_file(),
                     "Run python3 scripts/install_sysml_parser.py to enable parser integration tests")
class SysmlViewTests(unittest.TestCase):
    def test_requirement_view_includes_binding_and_quantity_declaration(self):
        report = view_sysml(ROOT / "examples/sysml/quantity.sysml", "R_DURATION")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["selected_kind"], "requirements")
        self.assertEqual(len(report["subject_parts"]), 1)
        self.assertTrue(any(item.get("name") == "cseType" for item in report["documents"]))
        self.assertEqual(view_sysml(ROOT / "examples/sysml/quantity.sysml", "MISSING")["status"], "error")
        conops = view_sysml(ROOT / "examples/sysml/conops.sysml", "UC_BORROW")
        self.assertEqual(conops["status"], "pass")
        self.assertEqual(conops["subject_parts"][0]["qualified_name"], "ToolLibraryConops::system")
        self.assertTrue(any(item.get("name") == "user" for item in conops["participants"]))
        self.assertTrue(any("receives an allocated tool" in item["body"] for item in conops["documents"]))

    def test_clause_change_impacts_requirement_without_source_reformat_noise(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            prior = ROOT / "examples/sysml/ack.sysml"
            revised = Path(directory) / "revised.sysml"
            revised.write_text(prior.read_text().replace("within 2 seconds", "within 3 seconds"))
            result = diff_sysml(prior, revised)
            self.assertEqual(result["status"], "pass")
            self.assertIn("documents:AckExample::TimelyAcknowledgment::responseTime:cse:0", result["changed"])
            self.assertIn("requirements:R_ACK", result["potentially_affected"])
            self.assertIn("constraints:AckExample::TimelyAcknowledgment::responseTime",
                          result["potentially_affected"])

            revised.write_text(prior.read_text() + "\n")
            formatting = diff_sysml(prior, revised)
            self.assertEqual(formatting["status"], "pass")
            self.assertEqual(formatting["changed"], [])
            self.assertEqual(formatting["added"], [])
            self.assertEqual(formatting["removed"], [])
            self.assertNotEqual(formatting["before_sha256"], formatting["after_sha256"])

    def test_quantity_declaration_change_impacts_bound_requirement(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            prior = ROOT / "examples/sysml/quantity.sysml"
            revised = Path(directory) / "quantity.sysml"
            revised.write_text(prior.read_text().replace("scale 1 unit second",
                                                       "scale 0.5 unit second"))
            report = diff_sysml(prior, revised)
            self.assertEqual(report["status"], "pass")
            self.assertIn("documents:AckExample::Controller::elapsed:cseType:0", report["changed"])
            self.assertIn("requirements:R_DURATION", report["potentially_affected"])


if __name__ == "__main__":
    unittest.main()
