"""Benchmark accounting invariants. These tests do not demonstrate model success."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_accounting import summarize_events, score_completion, require_equivalent


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
        trial = {"returncode": 0, "completed_turns": 1, "claimed_status": "pass"}
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


if __name__ == "__main__":
    unittest.main()
