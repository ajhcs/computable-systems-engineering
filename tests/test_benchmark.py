"""Benchmark accounting invariants. These tests do not demonstrate model success."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_accounting import summarize_events, score_completion, require_equivalent
import compare_interface_pilots as comparison


class BenchmarkContract(unittest.TestCase):
    def test_no_usage_or_approval_counts_are_invented(self):
        report = summarize_events('{"type":"turn.started"}\n')
        self.assertIsNone(report["provider_usage"])
        self.assertIsNone(report["provider_confirmation_count"])
        self.assertEqual(report["completed_turns"], 0)

    def test_started_and_completed_tool_events_count_once(self):
        raw = '\n'.join(json.dumps(x) for x in [
            {"type": "item.started", "item": {"id": "1", "type": "command_execution"}},
            {"type": "item.completed", "item": {"id": "1", "type": "command_execution", "command": "python check.py", "aggregated_output": "pass"}},
            {"type": "turn.completed", "usage": {"input_tokens": 123, "output_tokens": 45}}])
        result = summarize_events(raw)
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["provider_usage"]["input_tokens"], 123)

    def test_deterministic_or_self_reported_success_is_not_agentic_success(self):
        trial = {"returncode": 0, "completed_turns": 1, "claimed_status": "pass", "invalid_event_lines": 0, "transcript_status": "complete"}
        self.assertEqual(score_completion(trial, {"artifact_check": True}), "unreviewed")
        trial["timed_out"] = True
        self.assertEqual(score_completion(trial, {"artifact_check": True, "semantic_fidelity": True, "independent_review": True}), "incomplete")

    def test_model_task_budget_and_tier_mismatch_refuse_comparison(self):
        baseline = {"model": "model", "effort": "medium", "service_tier": "default", "task_sha256": "a", "source_sha256": "b", "timeout_seconds": 60, "sandbox": "workspace-write", "cli_version": "1", "parser_sha256": "c"}
        self.assertTrue(require_equivalent(baseline, dict(baseline)))
        for key in baseline:
            candidate = dict(baseline, **{key: "different"})
            with self.subTest(key=key), self.assertRaises(ValueError):
                require_equivalent(baseline, candidate)

    def test_measured_context_does_not_claim_model_tokens(self):
        path = ROOT / "docs/interface-context-results.json"
        if not path.exists():
            self.skipTest("Run measurement before auditing results")
        result = json.loads(path.read_text())
        self.assertIn("Not a model tokenizer", result["method"])
        self.assertEqual(result["actual_syntax_operation"]["status"], "pass")
        self.assertEqual(result["actual_syntax_operation"]["claim_scope"], "sysml_syntax_and_validation")
        self.assertIn("synthetic", result["actual_syntax_operation"]["fixture"])

    def test_independent_malformed_line_probe_cannot_pass_or_supply_complete_usage(self):
        raw = 'malformed dropped event\n' + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1}}) + '\n'
        report = summarize_events(raw)
        report.update(returncode=0, timed_out=False)
        self.assertEqual(report["invalid_event_lines"], 1)
        self.assertEqual(report["transcript_status"], "invalid")
        self.assertIsNone(report["provider_usage"])
        self.assertIsNone(report["tool_calls"])
        self.assertEqual(score_completion(report, {"artifact_check": True, "semantic_fidelity": True, "independent_review": True}), "incomplete")

    def test_malformed_shapes_duplicate_fields_truncated_and_nonfinite_events_fail_closed(self):
        good = json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1}})
        cases = ['null', '[]', '1', '{}', '{"type":[]}', ' ', '{"type":"item.completed"}',
                 '{"type":"item.completed","item":null}', '{"type":"future.unknown"}',
                 '{"type":"turn.completed","type":"turn.failed"}', '{"type":',
                 '{"type":"turn.completed","usage":{"input_tokens":NaN}}',
                 '{"type":"turn.completed","usage":{"input_tokens":1e999}}',
                 '{"type":"turn.completed","usage":{"input_tokens":true}}',
                 '{"type":"turn.completed","usage":{"input_tokens":-1}}',
                 '{"type":"item.completed","item":{"id":"1","type":"command_execution","command":"\\ud800"}}']
        for broken in cases:
            for raw in (broken + '\n' + good, good + '\n' + broken):
                with self.subTest(broken=broken):
                    report = summarize_events(raw)
                    self.assertEqual(report["transcript_status"], "invalid")
                    self.assertEqual(report["invalid_event_lines"], 1)
                    self.assertIsNone(report["provider_usage"])

    def test_duplicate_completion_does_not_double_count_or_pass(self):
        item = json.dumps({"type": "item.completed", "item": {"id": "1", "type": "file_change"}})
        report = summarize_events(item + '\n' + item + '\n' + '{"type":"turn.completed"}')
        self.assertEqual(report["observed_tool_calls"], 1)
        self.assertEqual(report["transcript_status"], "invalid")
        self.assertIsNone(report["tool_calls"])

    def test_unfinished_turn_or_tool_is_incomplete(self):
        for tail in ('{"type":"turn.started"}', '{"type":"item.started","item":{"id":"2","type":"command_execution"}}'):
            report = summarize_events('{"type":"turn.completed","usage":{"input_tokens":1}}\n' + tail)
            self.assertEqual(report["transcript_status"], "incomplete")
            self.assertIsNone(report["provider_usage"])

    def test_repeated_turn_start_is_invalid_even_with_later_completion(self):
        report = summarize_events('{"type":"turn.started"}\n{"type":"turn.started"}\n{"type":"turn.completed"}')
        self.assertEqual(report["transcript_status"], "invalid")
        self.assertIsNone(report["provider_usage"])

    def test_missing_log_validity_never_defaults_to_pass(self):
        trial = {"returncode": 0, "completed_turns": 1, "invalid_event_lines": 0}
        oracle = {"artifact_check": True, "semantic_fidelity": True, "independent_review": True}
        self.assertEqual(score_completion(trial, oracle), "incomplete")
        trial["transcript_status"] = "complete"
        trial["invalid_event_lines"] = False
        self.assertEqual(score_completion(trial, oracle), "incomplete")
        trial["invalid_event_lines"] = 0
        self.assertEqual(score_completion(trial, oracle), "pass")

    def test_unavailable_edit_arguments_are_unknown_and_totals_remain_partial(self):
        events = [{"type": "item.completed", "item": {"id": "cmd", "type": "command_execution", "command": "python check.py", "aggregated_output": "pass"}},
                  {"type": "item.completed", "item": {"id": "edit", "type": "file_change", "changes": [{"path": "report.md", "kind": "update"}]}},
                  {"type": "turn.completed", "usage": {"input_tokens": 10}}]
        report = summarize_events('\n'.join(json.dumps(x) for x in events))
        self.assertEqual(report["tool_calls"], 2)
        self.assertIsNone(report["tool_payloads"][1]["input"])
        self.assertEqual(report["tool_payloads"][1]["input_scope"], "unavailable_in_cli_event")
        self.assertEqual(report["tool_payloads"][1]["result_scope"], "logged_completion_event")
        costs = report["logged_command_input_cost"]
        self.assertEqual((costs["known_tool_inputs"], costs["unknown_tool_inputs"]), (1, 1))
        self.assertIsNone(costs["all_tools_utf8_bytes"])
        self.assertGreater(costs["known_utf8_bytes"], 0)
        self.assertEqual(report["provider_usage"]["input_tokens"], 10)

    def test_empty_logged_command_is_distinct_from_absent_arguments(self):
        events = [{"type": "item.completed", "item": {"id": "1", "type": "command_execution", "command": ""}},
                  {"type": "item.completed", "item": {"id": "2", "type": "command_execution"}},
                  {"type": "turn.completed"}]
        report = summarize_events('\n'.join(json.dumps(x) for x in events))
        self.assertEqual(report["tool_payloads"][0]["input"]["utf8_bytes"], 0)
        self.assertIsNone(report["tool_payloads"][1]["input"])
        self.assertIsNone(report["provider_usage"])

    def test_valid_unicode_line_separator_inside_event_is_not_a_dropped_line(self):
        raw = json.dumps({"type": "item.completed", "item": {"id": "1", "type": "agent_message", "text": "first\u2028second"}}, ensure_ascii=False)
        report = summarize_events(raw + '\n{"type":"turn.completed"}\n')
        self.assertEqual(report["transcript_status"], "complete")
        self.assertEqual(report["invalid_event_lines"], 0)


class ComparisonEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.trials = self.root / "preserved"
        self.output = self.root / "corrected.json"
        manifest = {"model": "model", "effort": "medium", "service_tier": "default", "task_sha256": "a", "source_sha256": "b", "timeout_seconds": 60, "sandbox": "workspace-write", "cli_version": "1", "parser_sha256": "c"}
        legacy = {"returncode": 0, "timed_out": False, "elapsed_seconds": 1,
                  "completion": "pass", "provider_usage": {"input_tokens": 999},
                  "tool_payloads": [{"id": "edit", "input": {"utf8_bytes": 0}}]}
        events = [{"type": "item.completed", "item": {"id": "cmd", "type": "command_execution", "command": "echo observed"}},
                  {"type": "item.completed", "item": {"id": "edit", "type": "file_change"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 10}}]
        for name in ("baseline-1", "optimized-1"):
            folder = self.trials / name
            folder.mkdir(parents=True)
            for filename, value in (("run-manifest.json", manifest), ("result.json", legacy)):
                (folder / filename).write_text(json.dumps(value), encoding="utf-8")
            (folder / "events.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
            (folder / "task.txt").write_text("synthetic accounting fixture", encoding="utf-8")

    def preserved_bytes(self):
        return {str(path.relative_to(self.trials)): path.read_bytes() for path in self.trials.rglob("*") if path.is_file()}

    def run_comparison(self, output=None):
        with patch.object(sys, "argv", ["compare_interface_pilots.py", "--trials-root", str(self.trials), "--output", str(output or self.output)]), redirect_stdout(io.StringIO()):
            comparison.main()

    def test_comparison_recomputes_legacy_unknowns_without_rewriting_trials(self):
        before = self.preserved_bytes()
        self.run_comparison()
        report = json.loads(self.output.read_text())
        for condition in ("baseline", "optimized"):
            result = report[condition]["result"]
            self.assertTrue(result["accounting_recomputed_from_events"])
            self.assertEqual(result["completion"], "unreviewed")
            self.assertEqual(result["provider_usage"], {"input_tokens": 10})
            self.assertIsNone(result["tool_payloads"][1]["input"])
            self.assertIsNone(result["tool_payloads"][1]["command_sha256"])
            self.assertNotIn("command", result["tool_payloads"][0])
            self.assertIsNone(result["logged_command_input_cost"]["all_tools_utf8_bytes"])
        self.assertEqual(self.preserved_bytes(), before)

    def test_comparison_rejects_corrupt_events_even_if_saved_metadata_claims_pass(self):
        events = self.trials / "optimized-1/events.jsonl"
        events.write_text("malformed dropped event\n" + events.read_text(), encoding="utf-8")
        before = self.preserved_bytes()
        with self.assertRaisesRegex(ValueError, "invalid or unfinished"):
            self.run_comparison()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.preserved_bytes(), before)

    def test_comparison_refuses_output_inside_preserved_evidence(self):
        before = self.preserved_bytes()
        with self.assertRaisesRegex(ValueError, "cannot be overwritten"):
            self.run_comparison(self.trials / "baseline-1/result.json")
        self.assertEqual(self.preserved_bytes(), before)


if __name__ == "__main__":
    unittest.main()
