"""Adversarial offline-harness tests; no native/model/engineering acceptance."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks/offline_matched"
sys.path.insert(0, str(HARNESS))
from harness import (ARMS, answer_template, check_answer, check_patch, cost_ledger, equal_information,
                     information, load_json, patch_reference, response, review_reference, scripted_calls, size, snapshot, wire)


class OfflineContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(HARNESS / "fixtures.json")
        cls.source_path = Path(os.environ.get("OFFLINE_EV_SOURCE", str(ROOT / ".cache/offline-matched/EVSample.sysml")))
        if not cls.source_path.is_file():
            raise RuntimeError("Pinned EV source unavailable; supply OFFLINE_EV_SOURCE. No synthetic substitute or auto-download.")
        cls.source = cls.source_path.read_bytes()
        cls.reference = snapshot(cls.source, cls.fixture)

    def test_all_six_task_triplets_have_identical_normalized_information(self):
        for task in self.fixture["tasks"]:
            rows = equal_information(self.reference, task, [response(self.reference, task, arm) for arm in ARMS])
            self.assertEqual(len({row["normalized_information_sha256"] for row in rows}), 1)
            self.assertEqual([row["extra_copies"] for row in rows], [0, 1, 0])

    def test_every_evidence_anchor_matches_original_utf8_source_and_hash(self):
        for fact in self.reference["records"].values():
            locator = fact["locator"]
            actual = self.source[locator["byte_start"]:locator["byte_end"]]
            self.assertEqual(actual.decode(), fact["quote"])
            self.assertEqual(sha256(actual).hexdigest(), locator["quote_sha256"])
            self.assertIsNone(fact["native_id"])
        self.assertEqual(self.reference["records"]["capacity"]["value"], {"kind": "quantity_literal", "number": "50", "unit": "A⋅h"})

    def test_changed_source_or_fabricated_scalar_annotations_fail_before_snapshot(self):
        with self.assertRaises(ValueError):
            snapshot(self.source + b"\n", self.fixture)
        for field, wrong in (("number", "999"), ("unit", "kg")):
            fixture = deepcopy(self.fixture)
            fact = next(row for row in fixture["facts"] if row["id"] == "capacity")
            fact["value"][field] = wrong
            with self.assertRaises(ValueError):
                snapshot(self.source, fixture)

    def test_missing_added_or_changed_information_refuses_comparison(self):
        task = self.fixture["tasks"][0]
        for mutation in ("missing", "added", "value", "identity", "source", "limits", "hint"):
            packets = [response(self.reference, task, arm) for arm in ARMS]
            packet = packets[1]
            if mutation == "missing":
                packet["containers"][-1]["records"].pop()
            elif mutation == "added":
                packet["containers"][0]["records"].append(self.reference["records"]["large_mass_prose"])
            elif mutation == "value":
                packet["containers"][-1]["records"][-1]["value"] = {"meaning": "extra assertion"}
            elif mutation == "identity":
                packet["containers"][-1]["records"][-1]["subject_id"] = "invented native ID"
            elif mutation == "source":
                packet["source_sha256"] = "stale"
            elif mutation == "limits":
                packet["evidence_limits"] = []
            else:
                packet["answer_hint"] = "Privileged extra information"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                equal_information(self.reference, task, packets)

    def test_consistent_duplicates_are_allowed_but_conflicting_duplicates_are_not(self):
        task = self.fixture["tasks"][0]
        packet = response(self.reference, task, ARMS[1])
        normalized, count = information(packet)
        self.assertEqual(count, len(normalized["records"]) + 1)
        packet["containers"][1]["records"][0]["predicate"] = "different relation"
        with self.assertRaises(ValueError):
            information(packet)

    def test_duplicate_or_missing_arm_cannot_satisfy_equality_gate(self):
        task = self.fixture["tasks"][0]
        packet = response(self.reference, task, ARMS[0])
        for packets in ([packet], [packet] * 3):
            with self.assertRaises(ValueError):
                equal_information(self.reference, task, packets)

    def test_packet_mutation_cannot_modify_reference_or_sibling_limits(self):
        task = self.fixture["tasks"][0]
        before = wire(self.reference)
        packets = [response(self.reference, task, arm) for arm in ARMS]
        packets[1]["evidence_limits"].append("extra decision information")
        self.assertEqual(wire(self.reference), before)
        self.assertNotEqual(packets[1]["evidence_limits"], packets[0]["evidence_limits"])
        with self.assertRaises(ValueError):
            equal_information(self.reference, task, packets)

    def test_correct_reference_answers_do_not_become_agent_success(self):
        for task in self.fixture["tasks"]:
            result = check_answer(self.reference, task, answer_template(self.reference, task))
            self.assertEqual(result["reference_checks"], "pass")
            self.assertIsNone(result["agentic_success"])
            self.assertIn("pending", result["meaning_review"])

    def test_duplicate_short_name_wrong_citation_or_unit_is_rejected(self):
        task = self.fixture["tasks"][2]
        for mutation in ("subject", "citation", "unit", "native", "duplicate"):
            answer = answer_template(self.reference, task)
            claim = next(row for row in answer["claims"] if row["id"] == "c1_range")
            if mutation == "subject":
                claim["subject_id"] = self.reference["records"]["l1_range"]["subject_id"]
            elif mutation == "citation":
                claim["locator"]["byte_start"] += 1
            elif mutation == "unit":
                claim["value"]["unit"] = "m"
            elif mutation == "native":
                claim["native_id"] = "made-up-id"
            else:
                answer["claims"].append(deepcopy(claim))
            self.assertEqual(check_answer(self.reference, task, answer)["reference_checks"], "fail")

    def test_declared_requirement_binding_cannot_be_reported_as_execution(self):
        task = self.fixture["tasks"][3]
        answer = answer_template(self.reference, task)
        answer["evidence_conclusion"] = "simulation_passed"
        self.assertEqual(check_answer(self.reference, task, answer)["reference_checks"], "fail")

    def test_prose_and_assumption_discrepancy_cannot_be_silently_resolved(self):
        task = self.fixture["tasks"][4]
        answer = answer_template(self.reference, task)
        answer["evidence_conclusion"] = "1200_kg_is_accepted_intent"
        self.assertEqual(check_answer(self.reference, task, answer)["reference_checks"], "fail")

    def test_malformed_answers_and_unknown_task_fact_fail_closed(self):
        task = self.fixture["tasks"][0]
        for answer in (None, [], {}, {"claims": None, "evidence_conclusion": "source_declarations_only"}):
            self.assertEqual(check_answer(self.reference, task, answer)["reference_checks"], "fail")
        with self.assertRaises(ValueError):
            response(self.reference, {**task, "facts": ["nonexistent"]}, ARMS[0])

    def test_patch_candidates_match_independent_literal_replacement_gold(self):
        for intent in self.fixture["patches"]:
            gold = self.source.replace(":>> capacity = 50['A⋅h'];".encode(), ":>> capacity = 60['A⋅h'];".encode())
            if intent["id"] == "P02":
                gold = gold.replace(b":>> baseVoltage = 300[V];", b":>> baseVoltage = 310[V];")
            self.assertEqual(patch_reference(self.source, self.reference, intent), gold)
            review = review_reference(self.source, self.reference, intent)
            result = check_patch(self.source, self.source, gold, self.reference, intent, review, review)
            self.assertEqual(result["reference_checks"], "pass")
            self.assertFalse(result["native_atomicity_proved"])
            self.assertFalse(result["human_authority_authenticated"])

    def test_patch_oracle_rejects_unrelated_changes_original_mutation_and_partial_apply(self):
        intent = self.fixture["patches"][1]
        good = patch_reference(self.source, self.reference, intent)
        review = review_reference(self.source, self.reference, intent)
        for original, candidate in ((self.source, good + b"\n"), (self.source + b"\n", good),
                                    (self.source, patch_reference(self.source, self.reference, self.fixture["patches"][0])),
                                    (self.source, good.replace(b"1100[kg]", b"1000[kg]"))):
            self.assertEqual(check_patch(self.source, original, candidate, self.reference, intent, review, review)["reference_checks"], "fail")

    def test_stale_cancelled_wrong_or_replaced_review_does_not_qualify_patch(self):
        intent = self.fixture["patches"][0]
        good = patch_reference(self.source, self.reference, intent)
        review = review_reference(self.source, self.reference, intent)
        for key, value in (("base_revision", "old"), ("intent_sha256", "other"), ("candidate_sha256", "wrong"),
                           ("generation", 0), ("decision", "cancel"), ("decision", "decline")):
            result = check_patch(self.source, self.source, good, self.reference, intent, {**review, key: value}, review)
            self.assertEqual(result["reference_checks"], "fail")
        with self.assertRaises(ValueError):
            check_patch(self.source, self.source, good, self.reference, intent, review, {**review, "generation": 0})

    def test_invalid_patch_id_literal_unit_or_type_is_not_admitted_by_oracle(self):
        for key, value in (("fact_id", "unknown"), ("before", "49"), ("after", True), ("after", "NaN"), ("unit", "kg")):
            intent = deepcopy(self.fixture["patches"][0])
            intent["edits"][0][key] = value
            with self.assertRaises(ValueError):
                patch_reference(self.source, self.reference, intent)
        with self.assertRaises(ValueError):
            patch_reference(self.source + b"\n", self.reference, self.fixture["patches"][0])

    def test_cost_ledger_counts_failed_attempt_and_retry_not_only_final_call(self):
        calls = [{"id": "1", "request": b"req", "result": b"no", "outcome": "error", "retry_of": None},
                 {"id": "2", "request": b"req2", "result": b"ok", "outcome": "ok", "retry_of": "1"}]
        result = cost_ledger(b"alpha beta", b"x", calls)
        self.assertEqual(result["complete_protocol_total"]["utf8_bytes"], 22)
        self.assertEqual((result["tool_calls"], result["retry_calls"]), (2, 1))
        self.assertIsNone(result["recorded_model_context_total"])
        self.assertIsNone(result["provider_usage"])

    def test_unknown_payload_is_not_zero_or_a_complete_total(self):
        calls = [{"id": "1", "request": None, "result": b"ok", "outcome": "ok", "retry_of": None}]
        result = cost_ledger(b"", b"", calls)
        self.assertIsNone(result["complete_protocol_total"])
        self.assertEqual(result["unknown_payloads"], 1)
        self.assertEqual(size(b""), {"utf8_bytes": 0, "regex_wordpunct_v2": 0})
        self.assertEqual(size("A⋅h".encode()), {"utf8_bytes": 5, "regex_wordpunct_v2": 3})

    def test_recorded_model_context_counts_repeated_prefix_on_every_request(self):
        result = cost_ledger(b"a", b"b", [], model_context_frames=[b"ab", b"abcd", b"abcdef"])
        self.assertEqual(result["recorded_model_context_total"]["utf8_bytes"], 12)
        self.assertIsNone(result["provider_usage"])
        with self.assertRaises(ValueError):
            cost_ledger(b"a", b"b", [], model_context_frames=[b"ab", None])

    def test_duplicate_calls_or_fake_retry_lineage_refused(self):
        call = {"id": "1", "request": b"req", "result": b"ok", "outcome": "ok", "retry_of": None}
        for calls in ([call, call], [{**call, "retry_of": "missing"}], [call, {**call, "id": "2", "retry_of": "1"}]):
            with self.assertRaises(ValueError):
                cost_ledger(b"", b"", calls)

    def test_every_arm_has_equal_call_count_and_explicit_retry_schedule(self):
        for task in self.fixture["tasks"]:
            for retry in (False, True):
                for arm in ARMS:
                    calls = scripted_calls(response(self.reference, task, arm), retry)
                    result = cost_ledger(b"", b"", calls)
                    self.assertEqual(result["tool_calls"], 2 if retry else 1)
                    self.assertEqual(result["retry_calls"], int(retry))

    def test_cli_refuses_existing_output_without_altering_source_or_sentinel(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "sentinel").write_bytes(b"retained")
            before = self.source_path.read_bytes()
            run = subprocess.run([sys.executable, "-B", str(HARNESS / "prepare.py"), "--source", str(self.source_path),
                                  "--license", str(self.source_path.with_name("LICENSE")), "--output", str(folder)], capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual((folder / "sentinel").read_bytes(), b"retained")
            self.assertEqual(self.source_path.read_bytes(), before)
            self.assertEqual(sorted(path.name for path in folder.iterdir()), ["sentinel"])

    def test_json_loader_rejects_ambiguous_and_nonfinite_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load_json(path)

    def test_preparation_keeps_oracles_outside_each_actor_allowlist_and_cannot_claim_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "fresh"
            run = subprocess.run([sys.executable, "-B", str(HARNESS / "prepare.py"), "--source", str(self.source_path),
                                  "--license", str(self.source_path.with_name("LICENSE")), "--output", str(folder)], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            roles = load_json(folder / "ROLE_SEPARATION.json")
            self.assertFalse(roles["agent_inputs_released"])
            self.assertEqual(len(roles["per_task_arm_allowlists"]), 18)
            for row in roles["per_task_arm_allowlists"]:
                self.assertEqual(row["files"], ["bootstrap.json", row["task"] + "-task.json", row["task"] + "-" + row["arm"] + ".json"])
                self.assertTrue(all((folder / name).is_file() for name in row["files"]))
                self.assertFalse(any("oracle" in name or "candidate" in name or "reference" in name for name in row["files"]))
            readiness = load_json(folder / "READINESS.json")
            self.assertEqual(readiness["native_human_ai_acceptance"], "blocked")
            self.assertFalse(readiness["model_dispatch_implemented"])
            self.assertEqual(readiness["ten_capabilities_accepted"], 0)
            report = load_json(folder / "REPORT.json")
            self.assertTrue(all(value is None for value in report["elicitation_observations"].values()))
            pins = load_json(folder / "MANIFEST.json")["sha256"]
            self.assertEqual(set(pins), {path.name for path in folder.iterdir() if path.name != "MANIFEST.json"})
            for name, expected in pins.items():
                self.assertEqual(sha256((folder / name).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
