"""Behavioral boundary tests for the opt-in controlled language profile."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.language import LanguageError, check_document, parse_requirement, render_requirement

VALID = json.loads((ROOT / "examples/language/valid.json").read_text())


def model_with(requirement="R_ack"):
    model = copy.deepcopy(VALID)
    model["requirements"] = {requirement: model["requirements"][requirement]}
    return model


def one_result(model, requirement="R_ack"):
    return check_document(model, review=True)["results"][requirement]


def ack_trace(response_at=None, *, length=7):
    model = model_with()
    rows = model["observations"]
    while len(rows) < length:
        rows.append(copy.deepcopy(rows[-1]))
    rows = rows[:length]
    for tick, row in enumerate(rows):
        row["request"] = tick >= 1
        row["acknowledged"] = response_at is not None and tick >= response_at
    model["observations"] = rows
    return model


class LanguageTests(unittest.TestCase):
    def test_valid_fixture_and_round_trip(self):
        report = check_document(VALID, review=True)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["results"]), set(VALID["requirements"]))
        self.assertEqual(report["results"]["R_ack"]["deadline_ticks"], 4)
        for text in VALID["requirements"].values():
            parsed = parse_requirement(text, VALID["actors"], VALID["properties"], VALID["clock"])
            rendered = render_requirement(parsed, VALID["properties"])
            self.assertEqual(parse_requirement(rendered, VALID["actors"], VALID["properties"], VALID["clock"]), parsed)

    def test_initial_invariant_violation_is_detected(self):
        model = model_with("R_inhibit")
        model["observations"][0]["inhibited"] = True
        self.assertEqual(one_result(model, "R_inhibit")["status"], "fail")
        self.assertEqual(one_result(model, "R_inhibit")["counterexample"]["index"], 0)

    def test_within_inclusive_deadline_and_late_response(self):
        self.assertEqual(one_result(ack_trace(1))["status"], "pass")
        self.assertEqual(one_result(ack_trace(5))["status"], "pass")
        late = one_result(ack_trace(6))
        self.assertEqual(late["status"], "fail")
        self.assertEqual(late["counterexample"]["deadline_index"], 5)
        self.assertEqual(one_result(ack_trace(None, length=5))["status"], "unknown")
        self.assertEqual(one_result(ack_trace(None))["status"], "fail")

    def test_scope_exit_does_not_cancel_pending_deadline(self):
        model = ack_trace(None)
        for row in model["observations"][3:]:
            row["mode"] = "inactive"
        self.assertEqual(one_result(model)["status"], "fail")

    def test_trigger_at_scope_entry_and_vacuous_coverage(self):
        model = ack_trace(4)
        model["observations"][0]["request"] = True
        self.assertEqual(one_result(model)["status"], "pass")
        never = ack_trace(None)
        for row in never["observations"]:
            row["request"] = False
        self.assertEqual(one_result(never)["status"], "unknown")
        self.assertEqual(one_result(never)["coverage"]["triggers"], 0)

    def test_until_release_boundary_and_unresolved_prefix(self):
        model = model_with("R_retain")
        model["observations"][2]["retained"] = False
        failure = one_result(model, "R_retain")
        self.assertEqual(failure["status"], "fail")
        self.assertEqual(failure["counterexample"]["index"], 2)
        released_at_trigger = model_with("R_retain")
        released_at_trigger["observations"][1]["released"] = True
        released_at_trigger["observations"][1]["retained"] = False
        early_release = one_result(released_at_trigger, "R_retain")
        self.assertEqual(early_release["status"], "fail")
        self.assertEqual(early_release["counterexample"]["index"], 1)
        later_release = model_with("R_retain")
        later_release["observations"][1]["released"] = True
        later_release["observations"][2]["released"] = True
        later_release["observations"][2]["retained"] = False
        self.assertEqual(one_result(later_release, "R_retain")["status"], "pass")
        no_release = model_with("R_retain")
        for row in no_release["observations"]:
            row["released"] = False
        no_release["observations"][-1]["retained"] = True
        self.assertEqual(one_result(no_release, "R_retain")["status"], "unknown")

    def test_incomplete_and_missing_evidence_cannot_pass_review(self):
        missing_trace = copy.deepcopy(VALID)
        missing_trace.pop("observations")
        self.assertNotEqual(check_document(missing_trace, review=True)["status"], "pass")
        prefix = copy.deepcopy(VALID)
        prefix["complete"] = False
        self.assertEqual(check_document(prefix, review=True)["status"], "unknown")
        missing_value = ack_trace(5)
        missing_value["observations"][2].pop("acknowledged")
        # A known response within the deadline discharges the obligation even
        # when an earlier sample of that response is missing.
        self.assertEqual(one_result(missing_value)["status"], "pass")
        capped = check_document(VALID, review=True, observation_cap=1)
        self.assertEqual(capped["status"], "unknown")

    def test_missing_event_or_release_cannot_create_false_failure(self):
        uncertain_start = ack_trace(None)
        uncertain_start["observations"][0].pop("request")
        uncertain_start["observations"][1]["request"] = True
        self.assertEqual(one_result(uncertain_start)["status"], "unknown")
        uncertain_release = model_with("R_retain")
        uncertain_release["observations"][2].pop("released")
        uncertain_release["observations"][2]["retained"] = False
        self.assertEqual(one_result(uncertain_release, "R_retain")["status"], "unknown")

    def test_grammar_names_types_and_ownership(self):
        source = VALID["requirements"]["R_inhibit"]
        changes = (
            (source[:-1], "grammar"),
            (source.replace("Controller", "Unknown"), "undeclared"),
            (source.replace("inhibited", "undeclared"), "undeclared"),
            (source.replace("inhibited = true", "inhibited = maybe"), "type"),
            (source.replace("output_enabled = false", "inhibited = false"), "owner"),
            (source.replace("output_enabled = false", "output_enabled > false"), "type"),
            (source + " __import__('os')", "grammar"),
        )
        for sentence, code in changes:
            with self.subTest(sentence=sentence):
                with self.assertRaises(LanguageError) as caught:
                    parse_requirement(sentence, VALID["actors"], VALID["properties"], VALID["clock"])
                self.assertEqual(caught.exception.code, code)

    def test_exact_numeric_units_and_clock(self):
        props = copy.deepcopy(VALID["properties"])
        props["rate"] = {"type": "int", "min": 0, "max": 200, "scale": "0.1", "unit": "MB", "owner": "controlled"}
        good = "Whenever inhibited = true, Controller shall always satisfy rate <= 10.0 MB."
        self.assertEqual(parse_requirement(good, VALID["actors"], props, VALID["clock"])["response"]["value"], 100)
        for text, code in ((good.replace("MB", "MiB"), "unit"),
                           (good.replace("10.0", "10.05"), "unit"),
                           (good.replace("10.0", "30"), "type")):
            with self.subTest(text=text):
                with self.assertRaises(LanguageError) as caught:
                    parse_requirement(text, VALID["actors"], props, VALID["clock"])
                self.assertEqual(caught.exception.code, code)
        with self.assertRaises(LanguageError) as caught:
            parse_requirement(VALID["requirements"]["R_ack"].replace("2 seconds", "0.75 seconds"),
                              VALID["actors"], VALID["properties"], VALID["clock"])
        self.assertEqual(caught.exception.code, "unit")
        signed = copy.deepcopy(VALID["properties"])
        signed["temperature"] = {"type": "int", "min": -100, "max": 100, "scale": "0.5", "unit": "C", "owner": "controlled"}
        cold = "Whenever inhibited = true, Controller shall always satisfy temperature >= -2.5 C."
        self.assertEqual(parse_requirement(cold, VALID["actors"], signed, VALID["clock"])["response"]["value"], -5)
        close_clock = {"period": "0.3333333333333333333333333333", "unit": "milliseconds"}
        near_multiple = VALID["requirements"]["R_ack"].replace("2 seconds", "1 millisecond")
        with self.assertRaises(LanguageError) as caught:
            parse_requirement(near_multiple, VALID["actors"], VALID["properties"], close_clock)
        self.assertEqual(caught.exception.code, "unit")

    def test_bad_trace_types_and_document_shape(self):
        model = copy.deepcopy(VALID)
        model["observations"][0]["inhibited"] = 1
        self.assertEqual(check_document(model, review=True)["status"], "error")
        empty = copy.deepcopy(VALID)
        empty["requirements"] = {}
        self.assertNotEqual(check_document(empty, review=True)["status"], "pass")
        bad_clock = copy.deepcopy(VALID)
        bad_clock["clock"]["period"] = "0"
        self.assertEqual(check_document(bad_clock, review=True)["status"], "error")
        bad_clock["clock"] = {"period": "1", "unit": 5}
        self.assertEqual(check_document(bad_clock, review=True)["status"], "error")
        malformed_enum = copy.deepcopy(VALID)
        malformed_enum["properties"]["mode"]["values"] = [{"x": 1}]
        self.assertEqual(check_document(malformed_enum, review=True)["status"], "error")

    def test_scope_budget_and_parser_boundaries(self):
        manifest = {"version": 1, "required": sorted(VALID["requirements"])}
        self.assertEqual(check_document(VALID, review=True, expected=manifest)["status"], "pass")
        reduced = copy.deepcopy(VALID)
        reduced["requirements"].pop("R_ack")
        report = check_document(reduced, review=True, expected=manifest)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["scope"]["missing"], ["R_ack"])
        self.assertEqual(check_document(VALID, review=True, work_cap=1)["status"], "unknown")

        wrong_version = copy.deepcopy(VALID)
        wrong_version["language_version"] = True
        self.assertEqual(check_document(wrong_version)["status"], "error")
        lower = VALID["requirements"]["R_ack"].replace("In mode = active, upon", "upon")
        with self.assertRaises(LanguageError):
            parse_requirement(lower, VALID["actors"], VALID["properties"], VALID["clock"])
        huge = VALID["requirements"]["R_ack"].replace("2 seconds", "9" * 64 + " minutes")
        with self.assertRaises(LanguageError):
            parse_requirement(huge, VALID["actors"], VALID["properties"], VALID["clock"])

    def test_bounded_pending_diagnostics_and_irrelevant_missing_scope(self):
        model = model_with("R_retain")
        rows = []
        for tick in range(500):
            rows.append({"mode": "active", "pending": tick % 2 == 1,
                         "released": False})
        model["observations"] = rows
        result = one_result(model, "R_retain")
        self.assertEqual(result["status"], "unknown")
        self.assertGreater(result["pending_count"], 8)
        self.assertEqual(len(result["pending"]), 8)
        self.assertTrue(result["diagnostics_truncated"])

        irrelevant = model_with("R_inhibit")
        irrelevant["observations"][0]["mode"] = "inactive"
        irrelevant["observations"][0].pop("inhibited")
        self.assertEqual(one_result(irrelevant, "R_inhibit")["status"], "pass")

    def test_cli_review(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/requirements.py"),
                                 str(ROOT / "examples/language/valid.json"), "--review", "--json",
                                 "--manifest", str(ROOT / "examples/language/valid-manifest.json")],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
