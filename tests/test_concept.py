import copy
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPT = WORKSPACE / "skills/develop-system-concept/scripts/concept.py"
spec = importlib.util.spec_from_file_location("concept", SCRIPT)
concept = importlib.util.module_from_spec(spec)
spec.loader.exec_module(concept)
DEFAULT = object()


def fixture():
    return {
        "version": 1,
        "framing": {
            "name": "Workshop reservation concept",
            "problem": "Members can arrive to find all shared tools reserved.",
            "current_state": "Reservations are kept on a paper board; this is a synthetic example.",
            "desired_outcome": "Members can learn availability before travelling.",
            "boundary": "Coordinate reservations; exclude tool control and maintenance.",
            "context": "A small shared workshop with intermittent connectivity.",
            "timeframe": "A pilot date remains an engineer decision.",
            "basis": "Synthetic test fixture, not a real stakeholder request.",
        },
        "needs": {"N1": {"text": "Know availability before travelling", "stakeholder": "Member", "basis": "Synthetic fixture"}},
        "functions": {"F1": {"text": "Report availability", "needs": ["N1"], "inputs": ["Tool and time query"], "outputs": ["Reservation status"]}},
        "criteria": {"R1": {"text": "Make current availability understandable", "kind": "goal", "needs": ["N1"], "basis": "Synthetic proposed goal", "measure": "Member explanation during a prototype walkthrough"}},
        "concepts": {"K1": {
            "summary": "A shared reservation board with a remotely readable mirror.",
            "functions": ["F1"],
            "allocations": [{"function": "F1", "element": "Availability view"}],
            "operations": [], "assumptions": ["Users can access the mirror before travelling."],
            "assessments": {"R1": {"finding": "unknown", "evidence": "unknown", "basis": "No user evaluation yet", "next_check": "Test a sketch with members"}},
            "evaluation": {"method": "Prototype walkthrough", "data": "Example reservations and member explanations", "environment": "Workshop or representative mockup"},
            "comparison": "An unstaffed mirror trades manual status effort for remote access; staffed telephone service remains unexplored.",
        }},
        "decisions": {"D1": {"text": "Explore the mirrored board", "status": "proposed", "basis": "Illustrative candidate for review", "affects": ["K1"]}},
        "questions": [{"text": "Which pilot date is useful?", "affects": [], "blocking": False}],
    }


class ConceptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.record = fixture()

    def check(self, record=DEFAULT, focused=(), review=True):
        return concept.check(self.record if record is DEFAULT else record, self.base, focused, review)

    def write(self, name, value):
        path = self.base / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def linked(self):
        linked = {"version": 1, "actors": {"A1": "Member"}, "needs": {"N1": {"text": "Availability", "actor": "A1", "basis": "Synthetic"}}, "scenarios": {"S1": {"need": "N1", "kind": "normal"}}}
        self.write("scenarios.json", linked)
        self.record["operations"] = {"O1": {"path": "scenarios.json", "ids": ["S1"], "sha256": concept.fingerprint(linked)}}
        self.record["concepts"]["K1"]["operations"] = ["O1"]
        return linked

    def test_complete_record_does_not_claim_feasibility_or_acceptance(self):
        report, code = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report["review_completeness"], "pass")
        self.assertEqual(report["feasibility"], "not_independently_evaluated")
        self.assertEqual(report["semantic_validation"], "not_evaluated")
        self.assertEqual(report["implementation"], "not_evaluated")
        self.assertEqual(report["decision_authenticity"], "not_evaluated")
        self.assertEqual(report["declared_findings"][0]["finding"], "unknown")

    def test_draft_is_valid_but_not_complete(self):
        report, code = self.check({"version": 1}, review=False)
        self.assertEqual(code, 0)
        self.assertTrue(report["review_gaps"])
        self.assertEqual(self.check({"version": 1})[1], 1)

    def test_strict_types_and_version(self):
        for bad in (None, [], True, 1, "record", {"version": True}, {"version": 2}):
            with self.subTest(bad=bad):
                self.assertEqual(self.check(bad)[1], 1)

    def test_unknown_fields_rejected_extensions_allowed(self):
        self.record["framing"]["boundry"] = "typo"
        self.assertEqual(self.check()[1], 1)
        del self.record["framing"]["boundry"]
        self.record["framing"]["extra"] = {"local_convention": "Allowed extension"}
        self.assertEqual(self.check()[1], 0)

    def test_ids_unique_valid_and_reserved(self):
        for key in ("framing", "K1", "bad key", "0bad"):
            record = fixture()
            record["needs"][key] = record["needs"].pop("N1")
            self.assertEqual(self.check(record)[1], 1)

    def test_broken_and_duplicate_references(self):
        for refs in (["N404"], ["N1", "N1"]):
            self.record["functions"]["F1"]["needs"] = refs
            self.assertEqual(self.check()[1], 1)

    def test_allocation_must_belong_to_candidate(self):
        self.record["functions"]["F2"] = copy.deepcopy(self.record["functions"]["F1"])
        self.record["concepts"]["K1"]["allocations"][0]["function"] = "F2"
        report, code = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any("allocations" in e for e in report["errors"]))

    def test_qualitative_goal_needs_no_numeric_threshold(self):
        self.assertEqual(self.check()[1], 0)
        self.assertNotIn("value", self.record["criteria"]["R1"])

    def test_one_candidate_no_selection_and_no_operations_are_allowed(self):
        del self.record["decisions"]
        self.assertEqual(self.check()[1], 0)

    def test_unknown_and_assumption_need_resolution_plan(self):
        assessment = self.record["concepts"]["K1"]["assessments"]["R1"]
        del assessment["next_check"]
        self.assertEqual(self.check()[1], 1)
        assessment.update(finding="supported", evidence="assumption")
        report, code = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(report["concerns"])
        assessment["next_check"] = "Measure with a prototype"
        self.assertEqual(self.check()[1], 0)

    def test_declared_contradiction_remains_visible_in_complete_review(self):
        self.record["criteria"]["R1"]["kind"] = "constraint"
        self.record["concepts"]["K1"]["assessments"]["R1"].update(finding="contradicted", evidence="analysis", basis="Synthetic analysis identifies a conflict")
        report, code = self.check()
        self.assertEqual(code, 0)
        self.assertTrue(any("contradiction" in s for s in report["concerns"]))
        self.assertEqual(report["feasibility"], "not_independently_evaluated")

    def test_accepted_decision_requires_recorded_author_and_basis(self):
        self.record["decisions"]["D1"].update(status="accepted", basis="")
        self.assertEqual(self.check()[1], 1)
        self.record["decisions"]["D1"].update(by="Synthetic engineer", basis="Synthetic user statement")
        report, code = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report["decision_authenticity"], "not_evaluated")

    def test_missing_evaluation_data_environment_detected(self):
        self.record["concepts"]["K1"]["evaluation"] = {"method": "Prototype"}
        report, code = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any("evaluation.data" in g for g in report["review_gaps"]))
        self.assertTrue(any("evaluation.environment" in g for g in report["review_gaps"]))

    def test_blank_input_or_output_entries_are_incomplete_only_on_review(self):
        for field in ("inputs", "outputs"):
            for values in ([""], ["   "], ["Known flow", ""]):
                record = fixture()
                record["functions"]["F1"][field] = values
                self.assertEqual(self.check(record, review=False)[1], 0)
                report, code = self.check(record, focused=("K1",))
                self.assertEqual(code, 1)
                self.assertTrue(any(f"functions.F1.{field}" in gap for gap in report["review_gaps"]))

    def test_focused_review_ignores_unrelated_incomplete_draft(self):
        self.record["needs"]["N2"] = {}
        self.record["functions"]["F2"] = {"needs": ["N2"]}
        self.record["criteria"]["R2"] = {"needs": ["N2"]}
        self.record["concepts"]["K2"] = {"functions": ["F2"]}
        self.assertEqual(self.check(focused=("K1",))[1], 0)
        self.assertEqual(self.check()[1], 1)

    def test_focused_review_catches_missing_applicable_criterion(self):
        self.record["criteria"]["R2"] = copy.deepcopy(self.record["criteria"]["R1"])
        report, code = self.check(focused=("K1",))
        self.assertEqual(code, 1)
        self.assertTrue(any("missing applicable criterion R2" in gap for gap in report["review_gaps"]))

    def test_focused_review_catches_unassessed_global_criterion(self):
        self.record["criteria"]["R2"] = {"text": "Global cost ceiling", "kind": "constraint", "basis": "Proposed", "measure": "Total cost estimate"}
        report, code = self.check(focused=("K1",))
        self.assertEqual(code, 1)
        self.assertTrue(any("missing applicable criterion R2" in gap for gap in report["review_gaps"]))

    def test_unrelated_structural_error_still_fails_focus(self):
        self.record["functions"]["F2"] = {"needs": ["N404"]}
        self.assertEqual(self.check(focused=("K1",))[1], 1)

    def test_unknown_selection_fails(self):
        self.assertEqual(self.check(focused=("K404",))[1], 1)
        with self.assertRaises(ValueError):
            concept.view(self.record, ["K404"])

    def test_relevant_blocking_questions_only(self):
        self.record["needs"]["N2"] = {}
        self.record["questions"] = [{"text": "Unrelated", "affects": ["N2"], "blocking": True}]
        self.assertEqual(self.check(focused=("K1",))[1], 0)
        self.record["questions"][0]["affects"] = ["N1"]
        self.assertEqual(self.check(focused=("K1",))[1], 1)

    def test_view_returns_dependencies_applicable_criteria_and_decisions(self):
        self.record["criteria"]["R2"] = copy.deepcopy(self.record["criteria"]["R1"])
        self.record["needs"]["N2"] = {"text": "Unrelated"}
        self.record["questions"].append({"text": "Unrelated question", "affects": ["N2"]})
        result = concept.view(self.record, ["K1"])
        self.assertIn("R2", result["record"]["criteria"])
        self.assertIn("N1", result["record"]["needs"])
        self.assertNotIn("N2", result["record"]["needs"])
        self.assertIn("D1", result["related_decisions"])
        self.assertEqual(len(result["record"]["questions"]), 1)

    def test_related_decisions_do_not_depend_on_insertion_order(self):
        decisions = {
            "D3": {"text": "Later consequence", "status": "proposed", "basis": "Synthetic", "affects": ["D2"]},
            "D2": {"text": "Dependent decision", "status": "proposed", "basis": "Synthetic", "affects": ["D1"]},
            "D1": self.record["decisions"]["D1"],
        }
        self.record["decisions"] = decisions
        first_selection = concept.selection(self.record, ["K1"])
        first_view = concept.view(self.record, ["K1"])
        self.record["decisions"] = dict(reversed(list(decisions.items())))
        self.assertEqual(first_selection, concept.selection(self.record, ["K1"]))
        self.assertEqual(first_view, concept.view(self.record, ["K1"]))
        self.assertTrue({"D1", "D2", "D3"}.issubset(first_selection))

    def test_cli_unicode_output_under_cp1252_environment(self):
        self.record["needs"]["N1"]["stakeholder"] = "工程师 / مهندس / Инженер"
        self.record["decisions"]["D1"]["text"] = "比較して判断する"
        path = self.write("unicode.json", self.record)
        environment = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "view", str(path), "K1"], capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        parsed = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(parsed["record"]["needs"]["N1"]["stakeholder"], self.record["needs"]["N1"]["stakeholder"])
        self.assertEqual(parsed["related_decisions"]["D1"]["text"], self.record["decisions"]["D1"]["text"])

    def test_link_hash_matches_and_formatting_does_not_make_it_stale(self):
        linked = self.linked()
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "current")
        (self.base / "scenarios.json").write_text(json.dumps(linked, indent=4, sort_keys=True), encoding="utf-8")
        self.assertEqual(self.check()[1], 0)

    def test_link_drift_missing_ids_and_missing_file_are_reported(self):
        linked = self.linked()
        linked["scenarios"]["S1"]["kind"] = "off_normal"
        self.write("scenarios.json", linked)
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "stale")
        self.assertEqual(self.check()[1], 1)
        self.record["operations"]["O1"]["ids"] = ["S404"]
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "missing_ids")
        (self.base / "scenarios.json").unlink()
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "unavailable")

    def test_unpinned_or_invalid_link_never_reports_current(self):
        self.linked()
        del self.record["operations"]["O1"]["sha256"]
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "unpinned")
        self.write("scenarios.json", {"version": True})
        self.assertEqual(self.check()[0]["operation_links"]["O1"]["status"], "invalid")

    def test_unrelated_link_is_not_read_in_focused_review(self):
        self.record["operations"] = {"O2": {"path": "missing.json"}}
        report, code = self.check(focused=("K1",))
        self.assertEqual(code, 0)
        self.assertEqual(report["operation_links"], {})

    def test_diff_propagates_from_needs_and_new_criteria(self):
        changed = copy.deepcopy(self.record)
        changed["needs"]["N1"]["text"] = "Different need"
        result = concept.diff(self.record, changed)
        self.assertEqual(result["changed"], ["N1"])
        self.assertTrue({"F1", "R1", "K1", "D1"}.issubset(result["affected_dependents"]))
        changed = copy.deepcopy(self.record)
        changed["criteria"]["R2"] = copy.deepcopy(changed["criteria"]["R1"])
        self.assertIn("K1", concept.diff(self.record, changed)["affected_dependents"])

    def test_diff_uses_old_edges_for_removed_records(self):
        changed = copy.deepcopy(self.record)
        del changed["criteria"]["R1"]
        del changed["concepts"]["K1"]["assessments"]["R1"]
        result = concept.diff(self.record, changed)
        self.assertEqual(result["removed"], ["R1"])
        self.assertIn("D1", result["affected_dependents"])

    def test_diff_detects_global_changes_and_preserves_equal_formatting(self):
        changed = copy.deepcopy(self.record)
        changed["framing"]["boundary"] = "Expanded boundary"
        self.assertIn("K1", concept.diff(self.record, changed)["affected_dependents"])
        changed = copy.deepcopy(self.record)
        changed["questions"][0]["text"] = "Revised question"
        self.assertEqual(concept.diff(self.record, changed)["other_changes"], ["questions"])
        self.assertFalse(concept.diff(self.record, json.loads(json.dumps(self.record, sort_keys=True)))["reconsider_evidence"])

    def test_parser_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for text in ('{"version":1,"version":1}', '{"version":1,"extra":{"x":NaN}}', '{"version":1,"extra":{"x":Infinity}}', '{"version":1,"extra":{"x":1e999}}'):
            path = self.base / "bad.json"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError):
                concept.read(path)

    def test_invalid_json_shapes_have_no_traceback(self):
        rng = random.Random(20260928)
        mutations = [None, True, False, 42, "text", [], {}, ["N1"]]
        for _ in range(250):
            record = fixture()
            location = rng.choice([record, record["framing"], record["needs"]["N1"], record["concepts"]["K1"], record["concepts"]["K1"]["assessments"]["R1"]])
            key = rng.choice(list(location))
            location[key] = copy.deepcopy(rng.choice(mutations))
            report, code = self.check(record)
            self.assertIn(code, (0, 1))
            self.assertIn(report["structural"], ("pass", "fail"))

    def test_cli_init_refuses_overwrite_and_draft_review_exit_differs(self):
        path = self.base / "draft.json"
        def run(*args):
            return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(run("init", path).returncode, 0)
        original = path.read_bytes()
        self.assertEqual(run("init", path).returncode, 2)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(run("check", path).returncode, 0)
        self.assertEqual(run("check", path, "--review").returncode, 1)
        path = self.write("complete.json", self.record)
        self.assertEqual(run("check", path, "--concept", "K1", "--review").returncode, 0)
        self.assertEqual(run("view", path, "K1").returncode, 0)
        self.assertEqual(run("diff", path, path).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
