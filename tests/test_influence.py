"""Generated single-variable witnesses are concrete, nonvacuous trace pairs."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.influence import generate_influence_tests
from verifier.language import check_document

VALID = json.loads((ROOT / "examples/language/valid.json").read_text())


def changed_cells(left, right):
    return [(index, name) for index, (a, b) in enumerate(zip(left, right))
            for name in a if a[name] != b[name]]


class InfluenceTests(unittest.TestCase):
    def test_all_existing_temporal_forms_have_replayable_witnesses(self):
        for requirement in VALID["requirements"]:
            with self.subTest(requirement=requirement):
                generated = generate_influence_tests(VALID, requirement)
                self.assertEqual(generated["status"], "pass", generated)
                self.assertEqual(generated["coverage"]["referenced"],
                                 generated["coverage"]["witnessed"])
                for variable, item in generated["variables"].items():
                    self.assertEqual(item["status"], "witness")
                    passing, failing = item["pass_trace"], item["fail_trace"]
                    self.assertEqual(len(passing), len(failing))
                    self.assertEqual(changed_cells(passing, failing),
                                     [(item["changed_index"], variable)])
                    for rows, expected in ((passing, "pass"), (failing, "fail")):
                        model = deepcopy(VALID)
                        model["requirements"] = {requirement: VALID["requirements"][requirement]}
                        model["observations"] = rows
                        model["complete"] = True
                        checked = check_document(model, review=True)
                        self.assertEqual(checked["status"], expected, (requirement, variable))
                        self.assertGreater(checked["results"][requirement]["coverage"]["triggers"], 0)

    def test_repeated_property_is_changed_as_one_real_value(self):
        model = {"clock": {"period": "1", "unit": "second"}, "actors": {"C": {}},
                 "properties": {"x": {"type": "bool", "owner": "input"},
                                "y": {"type": "bool", "owner": "controlled"}},
                 "requirements": {"R": "In x = true, upon x = true, C shall within 2 seconds satisfy y = true."}}
        generated = generate_influence_tests(model, "R")
        self.assertEqual(generated["status"], "pass", generated)
        self.assertEqual(generated["variables"]["x"]["roles"], ["scope", "trigger"])
        item = generated["variables"]["x"]
        self.assertEqual(changed_cells(item["pass_trace"], item["fail_trace"]),
                         [(item["changed_index"], "x")])

    def test_short_exhaustive_fallback_handles_trigger_used_as_release(self):
        model = {"clock": {"period": "1", "unit": "second"}, "actors": {"C": {}},
                 "properties": {"trigger": {"type": "bool", "owner": "input"},
                                "response": {"type": "bool", "owner": "controlled"}},
                 "requirements": {"R": "Upon trigger = true, C shall until trigger = true satisfy response = true."}}
        generated = generate_influence_tests(model, "R")
        self.assertEqual(generated["status"], "pass", generated)
        self.assertEqual(generated["variables"]["trigger"]["roles"], ["trigger", "release"])
        self.assertEqual(generated["variables"]["trigger"]["witness_role"], "short_exhaustive")

    def test_quantity_and_enum_domains_are_generated_from_declarations(self):
        model = {"clock": {"period": "1", "unit": "second"}, "actors": {"C": {}},
                 "properties": {"temperature": {"type": "int", "min": -20, "max": 20,
                                                "scale": "0.5", "unit": "C", "owner": "input"},
                                "alarm": {"type": "bool", "owner": "controlled"},
                                "mode": {"type": "enum", "values": ["idle", "hot", "cool"],
                                         "owner": "input"}},
                 "requirements": {"R1": "Whenever temperature >= 5 C, C shall always satisfy alarm = true.",
                                  "R2": "In mode = hot, whenever temperature >= 5 C, C shall always satisfy alarm = true."}}
        for requirement in model["requirements"]:
            with self.subTest(requirement=requirement):
                generated = generate_influence_tests(model, requirement)
                self.assertEqual(generated["status"], "pass", generated)
                self.assertEqual(generated["coverage"]["referenced"],
                                 generated["coverage"]["witnessed"])
                self.assertTrue(all(-20 <= row["temperature"] <= 20
                                    for item in generated["variables"].values()
                                    for row in item["pass_trace"]))

    def test_no_witness_does_not_claim_redundancy(self):
        model = {"clock": {"period": "1", "unit": "second"}, "actors": {"C": {}},
                 "properties": {"x": {"type": "bool", "owner": "controlled"}},
                 "requirements": {"R": "Whenever x = true, C shall always satisfy x = true."}}
        generated = generate_influence_tests(model, "R")
        self.assertEqual(generated["status"], "unknown")
        self.assertEqual(generated["coverage"], {"referenced": 1, "witnessed": 0})
        self.assertEqual(generated["variables"]["x"]["status"], "not_found_within_search")
        self.assertFalse(generated["search"]["complete_for_all_traces"])

    def test_row_and_evaluation_limits_cannot_be_coverage(self):
        row_limited = generate_influence_tests(VALID, "R_ack", max_rows=2)
        self.assertEqual(row_limited["status"], "unknown")
        self.assertEqual(row_limited["coverage"]["witnessed"], 0)
        work_limited = generate_influence_tests(VALID, "R_ack", evaluation_cap=1)
        self.assertEqual(work_limited["status"], "unknown")
        self.assertEqual(work_limited["coverage"]["witnessed"], 0)
        huge = deepcopy(VALID)
        huge["clock"] = {"period": "1", "unit": "millisecond"}
        huge["requirements"]["R_ack"] = huge["requirements"]["R_ack"].replace(
            "2 seconds", "9" * 60 + " milliseconds")
        huge_limited = generate_influence_tests(huge, "R_ack")
        self.assertEqual(huge_limited["status"], "unknown")
        self.assertEqual(huge_limited["search"]["evaluations"], 0)


if __name__ == "__main__":
    unittest.main()
