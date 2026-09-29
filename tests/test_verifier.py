"""Executable examples for the version-2 finite semantics."""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import focused_view, load_json, verify

VALID = json.loads((ROOT / "examples/verifier/valid.json").read_text())


def check(change=None, **kwargs):
    model = copy.deepcopy(VALID)
    if change:
        change(model)
    return verify(model, review=True, **kwargs)


def rules(report):
    return {item["rule"] for item in report["findings"]}


class VerifierTests(unittest.TestCase):
    def test_valid_and_focused(self):
        whole = check()
        focused = check(selected=["S1"])
        self.assertEqual(whole["status"], "pass")
        self.assertEqual(focused["status"], "pass")
        self.assertEqual(whole["completed_obligations"], focused["completed_obligations"])
        self.assertEqual(whole["artifact_sha256"], focused["artifact_sha256"])

    def test_undefined_entity(self):
        report = check(lambda m: m["exchanges"]["GapNotice"].update({"from": "Unknown"}))
        self.assertEqual(report["status"], "fail")
        self.assertIn("undeclared", rules(report))

    def test_type_and_unit(self):
        report = check(lambda m: m["exchanges"]["GapNotice"]["fields"]["gap"].update({"type": "int"}))
        self.assertIn("type", rules(report))
        report = check(lambda m: m["statements"]["R1"]["predicate"].update({"unit": "km/h"}))
        self.assertIn("unit", rules(report))
        report = check(lambda m: m["properties"]["speed"].update({"scale": "0"}))
        self.assertEqual(report["status"], "error")
        def wrong_exchange_field(m):
            m["data"]["other"] = {"type": "bool"}
            m["scenarios"]["S1"]["steps"]["T1"]["produces"] = ["other"]
        self.assertIn("type", rules(check(wrong_exchange_field)))

    def test_broken_trace_and_review_coverage(self):
        report = check(lambda m: m["traces"][0].update({"to": "Missing"}))
        self.assertIn("trace", rules(report))
        report = check(lambda m: m["traces"].pop())
        self.assertIn("coverage", rules(report))

    def test_overlap_conflict(self):
        report = check(lambda m: m["statements"]["R2"].update({"when": {"ref": "mode", "op": "==", "value": "merge"}}))
        self.assertIn("consistency", rules(report))
        conflict = next(x for x in report["findings"] if x["rule"] == "consistency")
        self.assertEqual(conflict["evidence"]["conflict"], ["R1", "R2"])

    def test_three_way_conflict(self):
        def change(m):
            m["statements"] = {"N1": m["statements"]["N1"]}
            m["traces"] = [{"from": "S1", "to": "R3", "kind": "addresses"}]
            for index in range(3):
                key = f"R{index + 3}"
                m["statements"][key] = {"category": "requirement", "subject": "System", "modality": "shall",
                                        "when": {"ref": "mode", "op": "==", "value": "merge"},
                                        "predicate": {"ref": "speed", "op": "!=", "value": index, "unit": "m/s"}}
                m["traces"].append({"from": key, "to": "N1", "kind": "justifies"})
        report = check(change)
        conflicts = [x["evidence"]["conflict"] for x in report["findings"] if x["rule"] == "consistency"]
        self.assertIn(["R3", "R4", "R5"], conflicts)

    def test_missing_data_and_disabled_path(self):
        report = check(lambda m: m["scenarios"]["S1"]["steps"]["T1"].pop("produces"))
        self.assertIn("step-reachability", rules(report))
        self.assertIn("progress", rules(report))
        report = check(lambda m: m["scenarios"]["S1"]["steps"]["T2"].update(
            {"guard": {"ref": "speed", "op": "==", "value": 2, "unit": "m/s"}}))
        self.assertIn("step-reachability", rules(report))

    def test_nonterminal_dead_end(self):
        def change(m):
            m["scenarios"]["S1"]["external_at"] = ["idle"]
            m["scenarios"]["S1"]["steps"].pop("T2")
        report = check(change)
        self.assertIn("dead-end", rules(report))

    def test_permitted_loop_and_intentional_abort(self):
        def loop(m):
            m["scenarios"]["S1"]["steps"]["T3"] = {"from": "waiting", "to": "waiting"}
        self.assertEqual(check(loop)["status"], "pass")
        def abort(m):
            s = m["scenarios"]["S1"]
            s["steps"]["T2"]["to"] = "aborted"
            s["terminal"] = {"aborted": "operator canceled"}
            s["completion"] = []
            s["require_completion"] = False
        self.assertEqual(check(abort)["status"], "pass")

    def test_unsupported_malformed_stale_and_limits(self):
        self.assertEqual(check(lambda m: m["statements"]["R1"]["predicate"].update({"op": "~"}))["status"], "unsupported")
        self.assertEqual(verify({"version": 1}, review=True)["status"], "unsupported")
        self.assertEqual(check(lambda m: m["actors"].update({"Bad": []}))["status"], "error")
        self.assertEqual(check(evidence={"model_sha256": "old", "items": []})["status"], "unknown")
        self.assertEqual(check(evidence={"model_sha256": "old"})["status"], "error")
        self.assertEqual(check(lambda m: m["scenarios"]["S1"].update({"start": []}))["status"], "error")
        self.assertEqual(check(assignment_cap=1)["status"], "unknown")
        self.assertEqual(check(state_cap=1)["status"], "unknown")

    def test_focused_keeps_global_conflicts(self):
        report = check(lambda m: m["statements"]["R2"].update({"when": {"ref": "mode", "op": "==", "value": "merge"}}), selected=["S1"])
        self.assertIn("consistency", rules(report))

    def test_vacuous_and_missing_obligations(self):
        report = check(lambda m: m["statements"]["R1"].update(
            {"when": {"all": [{"ref": "mode", "op": "==", "value": "merge"},
                              {"ref": "mode", "op": "==", "value": "cruise"}]}}))
        self.assertEqual(report["status"], "unknown")
        self.assertIn("applicability", rules(report))
        empty = verify({"version": 2}, review=True)
        self.assertEqual(empty["status"], "unknown")
        self.assertNotEqual(empty["completed_obligations"], empty["expected_obligations"])

    def test_invalid_modality_and_applicability(self):
        report = check(lambda m: m["statements"]["N1"].update({"modality": "shall"}))
        self.assertEqual(report["status"], "fail")
        report = check(lambda m: m["statements"]["R1"].update(
            {"when": {"ref": "speed", "op": "==", "value": 1, "unit": "m/s"}}))
        self.assertEqual(report["status"], "unsupported")
        deep = {"ref": "speed", "op": "==", "value": 1, "unit": "m/s"}
        for _ in range(34):
            deep = {"not": deep}
        report = check(lambda m: m["statements"]["R1"].update({"predicate": deep}))
        self.assertEqual(report["status"], "unsupported")

    def test_semantic_digest_and_view(self):
        model = copy.deepcopy(VALID)
        reordered = json.loads(json.dumps(model, sort_keys=True))
        self.assertEqual(verify(model)["artifact_sha256"], verify(reordered)["artifact_sha256"])
        view = focused_view(model, ["S1"])
        self.assertEqual(view["artifact_sha256"], verify(model)["artifact_sha256"])
        self.assertEqual(set(view["scenarios"]), {"S1"})
        self.assertEqual(set(view["global"]["statements"]), set(model["statements"]))

    def test_fhwa_proposal_checks_as_proposal(self):
        model = load_json(ROOT / "examples/verifier/fhwa-merge-proposal.json")
        self.assertEqual(verify(model, review=True)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
