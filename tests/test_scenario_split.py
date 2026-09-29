"""Exercise focused review and reuse the original checker regression suite."""
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
import test_develop_conops as regression

ROOT = Path(__file__).resolve().parents[1]
REVISION = ROOT / "skills"
SCRIPT = REVISION / "develop-operational-scenarios/scripts/conops.py"
spec = importlib.util.spec_from_file_location("focused_conops", SCRIPT)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
regression.c = c
regression.SCRIPT = SCRIPT


class FocusedReviewTests(unittest.TestCase):
    def setUp(self):
        self.doc = c.read(regression.EXAMPLE)
        self.doc.pop("review_notes")

    def test_one_scenario_needs_no_overall_coverage_notes(self):
        self.assertTrue(c.check(self.doc)["review_gaps"])
        result = c.check(self.doc, ["S1"])
        self.assertEqual(result["review_gaps"], [])
        self.assertEqual(result["scope"]["overall_conops_coverage"], "not_evaluated")
        self.assertEqual(result["semantic_validation"], "not_evaluated")

    def test_uncovered_unrelated_need_does_not_block_selected_work(self):
        self.doc["needs"]["N2"] = copy.deepcopy(self.doc["needs"]["N1"])
        self.assertEqual(c.check(self.doc, ["S1"])["review_gaps"], [])
        self.assertIn("N2: no linked scenario", c.check(self.doc)["review_gaps"])

    def test_incomplete_other_scenario_does_not_block(self):
        self.doc["scenarios"]["S2"] = {}
        self.assertEqual(c.check(self.doc, ["S1"])["review_gaps"], [])
        self.assertTrue(c.check(self.doc, ["S1", "S2"])["review_gaps"])

    def test_exception_can_be_reviewed_without_a_normal_scenario(self):
        self.doc["scenarios"]["S1"]["kind"] = "off_normal"
        self.assertEqual(c.check(self.doc, ["S1"])["review_gaps"], [])
        self.assertIn("scenarios: no normal-operation scenario", c.check(self.doc)["review_gaps"])

    def test_selected_evaluation_gap_remains_visible(self):
        self.doc["scenarios"]["S1"]["evaluation"]["environment"] = ""
        self.assertIn("S1.evaluation.environment: missing", c.check(self.doc, ["S1"])["review_gaps"])

    def test_related_criterion_and_need_are_reviewed(self):
        self.doc["criteria"]["C1"]["basis"] = ""
        self.doc["needs"]["N1"]["basis"] = ""
        gaps = c.check(self.doc, ["S1"])["review_gaps"]
        self.assertIn("C1.basis: missing", gaps)
        self.assertIn("N1.basis: missing", gaps)

    def test_global_and_dependency_questions_remain_blocking(self):
        for affects in ([], ["system"], ["N1"], ["C1"]):
            self.doc["questions"] = [{"text": "Engineer decision needed", "affects": affects, "blocking": True}]
            self.assertTrue(any("blocking" in x for x in c.check(self.doc, ["S1"])["review_gaps"]))

    def test_unrelated_question_does_not_block(self):
        self.doc["scenarios"]["S2"] = {}
        self.doc["questions"] = [{"text": "A separate decision", "affects": ["S2"], "blocking": True}]
        self.assertEqual(c.check(self.doc, ["S1"])["review_gaps"], [])

    def test_malformed_data_elsewhere_is_not_silently_accepted(self):
        self.doc["scenarios"]["S2"] = {"need": "missing"}
        result = c.check(self.doc, ["S1"])
        self.assertEqual(result["structure"], "fail")
        self.assertEqual(result["scope"]["structure"], "whole_record")

    def test_selection_rejects_other_record_types_and_unknown_ids(self):
        for selected in ([], ["N1"], ["missing"]):
            with self.assertRaises(ValueError):
                c.check(self.doc, selected)

    def test_review_preserves_record_and_whole_record_fingerprint(self):
        before = copy.deepcopy(self.doc)
        result = c.check(self.doc, ["S1"])
        self.assertEqual(self.doc, before)
        self.assertEqual(result["model_sha256"], c.fingerprint(self.doc))

    def test_standalone_package_cli_review_and_repeated_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            shutil.copytree(SCRIPT.parents[1], folder / "standalone")
            script = folder / "standalone/scripts/conops.py"
            self.doc["scenarios"]["S2"] = {}
            record = folder / "scenarios.json"
            record.write_text(json.dumps(self.doc), encoding="utf-8")
            cases = [(["--scenario", "S1", "--review"], 0),
                     (["--review"], 1),
                     (["--scenario", "S1", "--scenario", "S2", "--review"], 1),
                     (["--scenario", "missing", "--review"], 2)]
            for args, expected in cases:
                run = subprocess.run([sys.executable, "-B", str(script), "check", str(record), *args],
                                     capture_output=True, text=True, cwd=folder)
                self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
                self.assertIsInstance(json.loads(run.stdout), dict)


def suite():
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromModule(regression),
                               loader.loadTestsFromTestCase(FocusedReviewTests)])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    raise SystemExit(not result.wasSuccessful())
