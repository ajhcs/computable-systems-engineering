"""Boundary tests for interface contracts and elicitation, not AI task evidence."""
import copy
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cse_interface.contracts import command, describe, discover, InterfaceError, validate, OPERATIONS
from cse_interface.elicitation import transition
from cse_interface.limits import ANSWER_LIMIT_BYTES, RESOLUTION_RESERVE_BYTES, json_bytes

spec = importlib.util.spec_from_file_location("interface_cli", ROOT / "scripts/interface.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class Contracts(unittest.TestCase):
    def test_discovery_schemas_and_real_commands(self):
        self.assertEqual(set(discover()["operations"]), set(OPERATIONS))
        for name in OPERATIONS:
            self.assertTrue(Path(describe(name)["guide"]).is_file())
        argv = command("validate", {"models": [str(ROOT / "examples/sysml/ack.sysml")], "mode": "syntax"})
        self.assertIn("--syntax-only", argv)
        self.assertIn("--json", argv)

    def test_strict_types_unknown_fields_and_review_invariants(self):
        base = {"models": [str(ROOT / "examples/sysml/ack.sysml")], "mode": "syntax"}
        cases = [{**base, "review": True}, {**base, "models": "file"}, {**base, "mode": "approved"},
                 {**base, "mode": "review"}, {**base, "evidence": "missing"}]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(InterfaceError):
                command("validate", arguments)
        with self.assertRaises(InterfaceError):
            command("testgen", {"models": base["models"], "max_rows": True})

    def test_unsupported_format_and_missing_file_are_actionable(self):
        for path, code in (("NASA.mdl", "unsupported_format"), ("missing.sysml", "missing_file")):
            with self.assertRaises(InterfaceError) as caught:
                command("inspect", {"models": [path], "id": "R1"})
            self.assertEqual(caught.exception.code, code)
            self.assertTrue(caught.exception.recovery)

    def test_duplicate_resolved_paths(self):
        path = ROOT / "examples/sysml/ack.sysml"
        with self.assertRaises(InterfaceError):
            command("inspect", {"models": [str(path), str(path.parent / "." / path.name)], "id": "R1"})

    def test_compaction_preserves_status_and_reports_omission(self):
        for status in ("pass", "fail", "unknown", "unsupported", "error", "not_run"):
            report = {"status": status, "claim_scope": "test", "findings": list(range(20)), "inventory": {"parts": [1, 2]}, "coverage": {"required": 2, "complete": 1}}
            result = cli.compact(report)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["coverage"], report["coverage"])
            self.assertEqual(result["details_omitted"]["findings"], 12)
            self.assertEqual(len(report["findings"]), 20)

    def test_checker_exit_cannot_be_upgraded_to_success(self):
        request = {"operation": "validate", "arguments": {"models": [str(ROOT / "examples/sysml/ack.sysml")], "mode": "syntax"}}
        with patch.object(cli.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, '{"status":"pass"}', "")):
            with self.assertRaises(InterfaceError) as caught:
                cli.invoke(request)
            self.assertEqual(caught.exception.code, "contradictory_report")

    def test_nonfinite_and_duplicate_json_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                cli.read_json(io.StringIO(raw))

    def test_request_limit_counts_utf8_bytes_at_exact_boundary(self):
        raw = json.dumps({"text": "é" * 20}, ensure_ascii=False)
        boundary = len(raw.encode("utf-8"))
        self.assertEqual(cli.read_json(io.StringIO(raw), limit=boundary)["text"], "é" * 20)
        with self.assertRaises(InterfaceError):
            cli.read_json(io.StringIO(raw), limit=boundary - 1)

    def test_new_slash_entry_and_independent_launchers(self):
        for name in ("cse", "develop-system-concept", "develop-conops", "develop-operational-scenarios"):
            self.assertEqual((ROOT / ".agents/skills" / name).resolve(), ROOT / "skills" / name)
            run = subprocess.run([sys.executable, str(ROOT / "skills" / name / "scripts/cse.py"), "describe", "inspect"], cwd="/", text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["operation"], "inspect")

    def test_invoke_real_parser_equivalence(self):
        from verifier.sysml import JAR, CLASSES, check_sysml
        if not JAR.is_file() or not (CLASSES / "SysmlBridge.class").is_file():
            self.skipTest("Pinned parser unavailable")
        paths = [str(ROOT / "examples/sysml/ack.sysml")]
        baseline = check_sysml(paths, syntax_only=True)
        optimized = cli.invoke({"operation": "validate", "arguments": {"models": paths, "mode": "syntax"}})
        for key in ("status", "claim_scope", "model_sha256", "coverage", "findings"):
            self.assertEqual(baseline[key], optimized[key], key)


class Elicitation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.model = Path(self.tmp.name) / "candidate.sysml"
        self.model.write_text("package Example {}")
        self.context = {"operation": "edit", "models": [str(self.model)], "known": {}}
        self.question = {"key": "threshold", "question": "Which response limit applies?", "reason": "The requested threshold edit needs a value.", "needed_for": "edit", "type": "number"}
        self.request = {"action": "prepare", "context": self.context, "question": self.question}
        self.initial = {"format": "cse-questions-1", "questions": []}

    def prepare(self):
        return transition(self.initial, self.request)

    def reply(self, result, **extra):
        return {"action": "answer", "id": result["id"], "revision": result["revision"], "outcome": "accept", "content": 5, **extra}

    def test_valid_answer_has_no_model_mutation_or_acceptance(self):
        before = self.model.read_bytes()
        state, result = self.prepare()
        state, answer = transition(state, self.reply(result))
        self.assertEqual(answer["value"], 5)
        self.assertFalse(answer["applied"])
        self.assertEqual(self.model.read_bytes(), before)
        self.assertEqual(answer["authority"], "domain_clarification_only")

    def test_invalid_answer_does_not_consume_pending_question(self):
        state, result = self.prepare()
        original = copy.deepcopy(state)
        for value in (True, "5", [], None, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(InterfaceError):
                transition(state, self.reply(result, content=value))
        self.assertEqual(state, original)
        self.assertEqual(transition(state, self.reply(result))[1]["status"], "answered")

    def test_cancel_and_decline_do_not_supply_defaults(self):
        for outcome in ("cancel", "decline"):
            state, result = self.prepare()
            response = self.reply(result, outcome=outcome)
            response.pop("content")
            state, answer = transition(state, response)
            self.assertNotIn("value", answer)
            self.assertFalse(answer["applied"])
            self.assertEqual(transition(state, self.request)[1]["status"], "not_needed")

    def test_stale_source_revision_and_wrong_revision_are_rejected(self):
        state, result = self.prepare()
        with self.assertRaises(InterfaceError):
            transition(state, self.reply(result, revision="wrong"))
        self.model.write_text("package Changed {}")
        with self.assertRaises(InterfaceError) as caught:
            transition(state, self.reply(result))
        self.assertEqual(caught.exception.code, "stale_question")
        new, fresh = transition(state, self.request)
        self.assertNotEqual(fresh["revision"], result["revision"])
        self.assertEqual(new["questions"][0]["status"], "stale")

    def test_known_readonly_and_unrelated_questions_suppressed(self):
        for op in ("inspect", "validate", "explain", "compare"):
            request = copy.deepcopy(self.request)
            request["context"]["operation"] = op
            self.assertEqual(transition(self.initial, request)[1]["status"], "not_needed")
        self.context["known"]["threshold"] = 3
        self.assertEqual(self.prepare()[1]["status"], "not_needed")

    def test_new_known_fact_invalidates_an_older_pending_question(self):
        state, result = self.prepare()
        self.context["known"]["threshold"] = 3
        state, answer = transition(state, self.request)
        self.assertEqual(answer["status"], "not_needed")
        with self.assertRaises(InterfaceError):
            transition(state, self.reply(result))

    def test_replay_reworded_question_and_multiple_pending(self):
        state, result = self.prepare()
        second = copy.deepcopy(self.request)
        second["question"]["key"] = "units"
        with self.assertRaises(InterfaceError):
            transition(state, second)
        state, _ = transition(state, self.reply(result))
        with self.assertRaises(InterfaceError):
            transition(state, self.reply(result))
        self.question["question"] = "Please provide the same limit again?"
        self.assertEqual(transition(state, self.request)[1]["status"], "not_needed")

    def test_choices_missing_answers_and_provider_permissions(self):
        self.question.update(type="choice", choices=["seconds", "minutes"])
        state, result = self.prepare()
        with self.assertRaises(InterfaceError):
            transition(state, self.reply(result, content="hours"))
        request = self.reply(result)
        request.pop("content")
        with self.assertRaises(InterfaceError):
            transition(state, request)
        self.question["permission"] = "execute"
        with self.assertRaises(InterfaceError):
            self.prepare()

    def test_persistent_ledger_rejects_replay_across_calls(self):
        path = Path(self.tmp.name) / "draft.cse-questions.json"
        result = cli.elicit(path, self.request)
        answer = cli.elicit(path, self.reply(result))
        self.assertEqual(answer["status"], "answered")
        with self.assertRaises(InterfaceError):
            cli.elicit(path, self.reply(result))

    def test_ledger_will_not_overwrite_existing_foreign_json_or_symlink(self):
        path = Path(self.tmp.name) / "foreign.cse-questions.json"
        path.write_text('{"accepted":true}')
        with self.assertRaises(InterfaceError):
            cli.elicit(path, self.request)
        self.assertEqual(path.read_text(), '{"accepted":true}')
        alias = path.parent / "link.cse-questions.json"
        alias.symlink_to(path)
        with self.assertRaises(InterfaceError):
            cli.elicit(alias, self.request)

    def actual_cli(self, path, request):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/interface.py"), "elicit", "--state", str(path)],
                             input=json.dumps(request), text=True, capture_output=True, timeout=20)
        self.assertEqual(run.stderr, "", run.stderr)
        return run.returncode, json.loads(run.stdout)

    def test_independent_two_large_prepares_can_both_be_resolved(self):
        self.context["known"] = {"reference": "k" * 550000}
        ledger = Path(self.tmp.name) / "large.cse-questions.json"
        self.question["key"] = "first"
        code, first = self.actual_cli(ledger, self.request)
        self.assertEqual((code, first["status"]), (0, "pending"))
        self.assertEqual(self.actual_cli(ledger, self.reply(first))[1]["status"], "answered")
        self.question["key"] = "second"
        code, second = self.actual_cli(ledger, self.request)
        self.assertEqual((code, second["status"]), (0, "pending"))
        self.assertGreater(ledger.stat().st_size, 1000000)
        pending = ledger.read_bytes()
        for outcome in ("accept", "cancel", "decline"):
            branch = ledger.parent / (outcome + ".cse-questions.json")
            branch.write_bytes(pending)
            request = self.reply(second, outcome=outcome)
            if outcome != "accept":
                request.pop("content")
            code, result = self.actual_cli(branch, request)
            self.assertEqual((code, result["status"]), (0, "answered" if outcome == "accept" else outcome))
            self.assertFalse(result["applied"])
        self.assertEqual(self.model.read_text(), "package Example {}")

    def test_legacy_serialization_over_request_limit_remains_readable(self):
        self.context["known"] = {"reference": "k" * 550000}
        state, first = self.prepare()
        state, _ = transition(state, self.reply(first))
        self.question["key"] = "second"
        state, second = transition(state, self.request)
        ledger = Path(self.tmp.name) / "legacy.cse-questions.json"
        ledger.write_text(json.dumps(state, sort_keys=True) + "\n")
        self.assertGreater(ledger.stat().st_size, 1000000)
        self.assertEqual(self.actual_cli(ledger, self.reply(second))[1]["status"], "answered")

    def test_pending_admission_reserves_largest_valid_answer(self):
        self.question["type"] = "text"
        projected, _ = self.prepare()
        limit = len(json_bytes(projected)) + RESOLUTION_RESERVE_BYTES
        ledger = Path(self.tmp.name) / "boundary.cse-questions.json"
        answer = " " * (ANSWER_LIMIT_BYTES - 4) + "x"
        self.assertEqual(len(json_bytes(answer)), ANSWER_LIMIT_BYTES)
        with patch.object(cli, "LEDGER_LIMIT_BYTES", limit):
            pending = cli.elicit(ledger, self.request)
            result = cli.elicit(ledger, self.reply(pending, content=answer))
            self.assertEqual(result["status"], "answered")
            self.assertLessEqual(ledger.stat().st_size, limit)
            self.assertEqual(json.loads(ledger.read_text())["questions"][0]["answer"], answer)

    def test_capacity_rejection_is_atomic_and_existing_cancel_still_works(self):
        ledger = Path(self.tmp.name) / "capacity.cse-questions.json"
        pending = cli.elicit(ledger, self.request)
        before = ledger.read_bytes()
        enlarged = copy.deepcopy(self.request)
        enlarged["context"]["known"] = {"new_fact": "z" * 1000}
        with patch.object(cli, "LEDGER_LIMIT_BYTES", len(before) + RESOLUTION_RESERVE_BYTES):
            with self.assertRaises(InterfaceError) as caught:
                cli.elicit(ledger, enlarged)
            self.assertEqual(caught.exception.code, "ledger_capacity")
            self.assertEqual(ledger.read_bytes(), before)
            cancel = self.reply(pending, outcome="cancel")
            cancel.pop("content")
            self.assertEqual(cli.elicit(ledger, cancel)["status"], "cancel")

    def test_one_byte_below_reservation_rejects_before_pending_is_persisted(self):
        projected, _ = self.prepare()
        ledger = Path(self.tmp.name) / "too-small.cse-questions.json"
        with patch.object(cli, "LEDGER_LIMIT_BYTES", len(json_bytes(projected)) + RESOLUTION_RESERVE_BYTES - 1):
            with self.assertRaises(InterfaceError) as caught:
                cli.elicit(ledger, self.request)
            self.assertEqual(caught.exception.code, "ledger_capacity")
            self.assertFalse(ledger.exists())

    def test_oversize_answer_or_choice_never_consumes_pending_state(self):
        self.question["type"] = "text"
        ledger = Path(self.tmp.name) / "answer-limit.cse-questions.json"
        pending = cli.elicit(ledger, self.request)
        before = ledger.read_bytes()
        value = " " * ANSWER_LIMIT_BYTES + "x"
        with self.assertRaises(InterfaceError) as caught:
            cli.elicit(ledger, self.reply(pending, content=value))
        self.assertEqual(caught.exception.code, "answer_limit")
        self.assertEqual(ledger.read_bytes(), before)
        self.question.update(type="choice", choices=[value, "small"])
        with self.assertRaises(InterfaceError) as caught:
            self.prepare()
        self.assertEqual(caught.exception.code, "answer_limit")

    def test_cancel_and_decline_work_after_source_change_or_deletion(self):
        for change in ("edit", "delete"):
            for outcome in ("cancel", "decline"):
                self.model.write_text("package Example {}")
                ledger = Path(self.tmp.name) / (change + outcome + ".cse-questions.json")
                pending = cli.elicit(ledger, self.request)
                if change == "delete":
                    self.model.unlink()
                else:
                    self.model.write_text("package Changed {}")
                with self.assertRaises(InterfaceError):
                    cli.elicit(ledger, self.reply(pending))
                request = self.reply(pending, outcome=outcome)
                request.pop("content")
                code, result = self.actual_cli(ledger, request)
                self.assertEqual((code, result["status"]), (0, outcome))
                self.assertFalse(result["applied"])

    def test_record_count_bound_never_blocks_last_cancellation(self):
        state = self.initial
        for i in range(127):
            self.question["key"] = f"q{i}"
            state, pending = transition(state, self.request)
            state, _ = transition(state, self.reply(pending))
        ledger = Path(self.tmp.name) / "count-boundary.cse-questions.json"
        ledger.write_bytes(json_bytes(state))
        self.question["key"] = "last"
        pending = cli.elicit(ledger, self.request)
        cancel = self.reply(pending, outcome="cancel")
        cancel.pop("content")
        self.assertEqual(cli.elicit(ledger, cancel)["status"], "cancel")
        before = ledger.read_bytes()
        self.question["key"] = "too_many"
        with self.assertRaises(InterfaceError) as caught:
            cli.elicit(ledger, self.request)
        self.assertEqual(caught.exception.code, "ledger_limit")
        self.assertEqual(ledger.read_bytes(), before)
        self.assertEqual(len(json.loads(before)["questions"]), 128)

    def concurrent_requests(self, ledger, requests):
        barrier = threading.Barrier(len(requests))
        def run(request):
            barrier.wait(timeout=10)
            return self.actual_cli(ledger, request)
        with ThreadPoolExecutor(max_workers=len(requests)) as pool:
            return list(pool.map(run, requests))

    def test_concurrent_prepare_returns_one_persisted_question(self):
        ledger = Path(self.tmp.name) / "concurrent-prepare.cse-questions.json"
        results = self.concurrent_requests(ledger, [self.request, self.request])
        self.assertTrue(all(code == 0 for code, _ in results), results)
        self.assertEqual(results[0][1]["id"], results[1][1]["id"])
        self.assertEqual(len(json.loads(ledger.read_text())["questions"]), 1)

    def test_concurrent_answer_cancel_has_exactly_one_winner(self):
        ledger = Path(self.tmp.name) / "concurrent-resolve.cse-questions.json"
        pending = cli.elicit(ledger, self.request)
        cancel = self.reply(pending, outcome="cancel")
        cancel.pop("content")
        results = self.concurrent_requests(ledger, [self.reply(pending), cancel])
        self.assertEqual(sorted(code for code, _ in results), [0, 2], results)
        self.assertEqual(next(result for code, result in results if code == 2)["code"], "inactive_question")
        self.assertIn(json.loads(ledger.read_text())["questions"][0]["status"], ("answered", "cancel"))


if __name__ == "__main__":
    unittest.main()
