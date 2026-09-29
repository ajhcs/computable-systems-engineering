"""Behavioral checks of the local checker, not a benchmark of LLM obedience."""
import copy
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/develop-conops"
SCRIPT = SKILL / "scripts/conops.py"
spec = importlib.util.spec_from_file_location("conops", SCRIPT)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
EXAMPLE = ROOT / "examples/workshop/conops.json"


class ConopsTests(unittest.TestCase):
    def setUp(self):
        self.doc = c.read(EXAMPLE)

    def observations(self, value=1.5, unit="s"):
        return {"model_sha256": c.fingerprint(self.doc), "results": {"C1": {
            "value": value, "unit": unit, "evidence": "Synthetic fixture, not measured",
            "context": "Illustrative normal scenario"}}}

    def test_complete_record_does_not_claim_semantics_or_implementation(self):
        report = c.check(self.doc)
        self.assertEqual(report["structure"], "pass")
        self.assertEqual(report["review_gaps"], [])
        self.assertEqual(report["semantic_validation"], "not_evaluated")
        self.assertEqual(report["implementation"], "not_evaluated")
        self.assertTrue(report["open_questions"])

    def test_draft_allowed_without_claiming_review_complete(self):
        result = c.check({"version": 1})
        self.assertEqual(result["structure"], "pass")
        self.assertTrue(result["review_gaps"])

    def test_broken_reference(self):
        self.doc["scenarios"]["S1"]["steps"][0]["from"] = "missing"
        self.assertTrue(c.structural_errors(self.doc))

    def test_duplicate_id_across_groups(self):
        self.doc["actors"]["S1"] = "bad collision"
        self.assertTrue(c.structural_errors(self.doc))

    def test_reserved_id(self):
        self.doc["actors"]["system"] = "not an external actor"
        self.assertTrue(c.structural_errors(self.doc))

    def test_boundary_is_explicit(self):
        self.doc["scenarios"]["S1"]["steps"][0]["to"] = "register"
        self.assertTrue(c.structural_errors(self.doc))

    def test_missing_test_environment_is_a_review_gap(self):
        del self.doc["scenarios"]["S1"]["evaluation"]["environment"]
        self.assertFalse(c.structural_errors(self.doc))
        self.assertTrue(any("environment" in x for x in c.review_gaps(self.doc)))

    def test_absent_need_coverage(self):
        self.doc["needs"]["N2"] = copy.deepcopy(self.doc["needs"]["N1"])
        self.assertIn("N2: no linked scenario", c.review_gaps(self.doc))

    def test_deferred_coverage_is_allowed_with_reason(self):
        self.assertFalse(c.review_gaps(self.doc))
        del self.doc["review_notes"]["off_normal"]
        self.assertTrue(any("off_normal" in x for x in c.review_gaps(self.doc)))

    def test_blocking_question(self):
        self.doc["questions"][0]["blocking"] = True
        self.assertTrue(any("blocking" in x for x in c.review_gaps(self.doc)))

    def test_unknown_keys_rejected_but_extensions_allowed(self):
        self.doc["criteria"]["C1"]["targte"] = 3
        self.assertTrue(c.structural_errors(self.doc))
        del self.doc["criteria"]["C1"]["targte"]
        self.doc["criteria"]["C1"]["extra"] = {"rationale": "A local extension"}
        self.assertFalse(c.structural_errors(self.doc))

    def test_numeric_pass_fail_and_boundary(self):
        for value, status in [(1.5, "pass"), (2, "pass"), (2.01, "fail")]:
            self.assertEqual(c.evaluate(self.doc, self.observations(value))["overall"], status)

    def test_all_comparisons(self):
        for op, good, bad in [("<", 1, 2), ("<=", 2, 3), (">", 3, 2),
                              (">=", 2, 1), ("==", 2, 1), ("!=", 1, 2)]:
            self.doc["criteria"]["C1"]["op"] = op
            self.assertEqual(c.evaluate(self.doc, self.observations(good))["overall"], "pass")
            self.assertEqual(c.evaluate(self.doc, self.observations(bad))["overall"], "fail")

    def test_wrong_units_rejected(self):
        self.assertEqual(c.evaluate(self.doc, self.observations(1, "ms"))["overall"], "invalid")

    def test_missing_observation_unknown(self):
        obs = self.observations()
        obs["results"] = {}
        self.assertEqual(c.evaluate(self.doc, obs)["overall"], "unknown")

    def test_empty_criteria_do_not_pass_vacuously(self):
        self.doc["criteria"] = {}
        self.doc["questions"] = []
        obs = {"model_sha256": c.fingerprint(self.doc), "results": {}}
        self.assertEqual(c.evaluate(self.doc, obs)["overall"], "unknown")

    def test_no_boolean_or_nonfinite_measurements(self):
        for value in (True, False, float("nan"), float("inf"), "1.5"):
            self.assertEqual(c.evaluate(self.doc, self.observations(value))["overall"], "invalid")

    def test_stale_evidence(self):
        obs = self.observations()
        self.doc["criteria"]["C1"]["value"] = 5
        self.assertEqual(c.evaluate(self.doc, obs)["overall"], "stale")

    def test_formatting_does_not_stale_evidence(self):
        changed = json.loads(json.dumps(self.doc, sort_keys=True, indent=4))
        self.assertEqual(c.fingerprint(changed), c.fingerprint(self.doc))

    def test_provenance_and_context_required(self):
        for field in ("evidence", "context"):
            obs = self.observations()
            obs["results"]["C1"][field] = ""
            self.assertEqual(c.evaluate(self.doc, obs)["overall"], "invalid")

    def test_focused_view_keeps_criteria_dependencies_and_questions(self):
        self.doc["actors"]["unrelated"] = "Actor outside the requested slice"
        result = c.view(self.doc, ["S1"])
        self.assertEqual(set(result["records"]), {"S1", "C1", "N1", "member", "register", "system"})
        self.assertTrue(result["questions"])

    def test_dependency_impact_is_transitive(self):
        changed = copy.deepcopy(self.doc)
        changed["actors"]["member"] = "Updated actor"
        result = c.diff(self.doc, changed)
        self.assertEqual(result["changed"], ["member"])
        self.assertEqual(result["reconsider"], ["C1", "N1", "S1"])

    def test_removal_uses_old_dependencies(self):
        changed = copy.deepcopy(self.doc)
        del changed["criteria"]["C1"]
        changed["questions"] = []
        result = c.diff(self.doc, changed)
        self.assertEqual(result["changed"], ["C1"])
        self.assertEqual(result["evidence_status"], "recheck")

    def test_nonrecord_changes_are_reported(self):
        changed = copy.deepcopy(self.doc)
        changed["review_notes"]["lifecycle"] = "Updated scope"
        self.assertEqual(c.diff(self.doc, changed)["other_changes"], ["review_notes"])

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            for bad in ('{"version":1,"version":1}', '{"version":NaN}', '{"version":Infinity}'):
                path.write_text(bad, encoding="utf-8")
                with self.assertRaises(ValueError):
                    c.read(path)

    def test_malformed_inputs_do_not_raise(self):
        rng = random.Random(928)
        atoms = [None, True, False, 0, 1, "", "text", [], {}, [1], {"wrong": 3}]
        for value in atoms:
            c.check(value)
        for _ in range(350):
            record = copy.deepcopy(self.doc)
            target = rng.choice([record, record["system"], record["needs"]["N1"],
                                 record["scenarios"]["S1"], record["criteria"]["C1"]])
            key = rng.choice(list(target))
            target[key] = rng.choice(atoms)
            c.check(record)

    def test_cli_draft_review_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "record.json")
            for command, expected in [(["init", path], 0), (["init", path], 2),
                                      (["check", path], 0), (["check", path, "--review"], 1)]:
                result = subprocess.run([sys.executable, str(SCRIPT), *command], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
