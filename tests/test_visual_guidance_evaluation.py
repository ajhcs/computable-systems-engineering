"""Synthetic evidence tests; no model is invoked and no fresh-session claim is made."""
import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("visual_eval", ROOT / "scripts/evaluate_visual_guidance.py")
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class VisualGuidanceEvaluationTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / ".tmp")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def prepare(self, case="indirect-profile"):
        project = self.work / case
        E.prepare(case, project, ROOT)
        return project

    def trace(self, commands=(), complete=True):
        path = self.work / "trace.jsonl"
        records = [{"type": "item.completed", "item": {"type": "command_execution",
                    "command": command, "exit_code": 0}} for command in commands]
        if complete:
            records.append({"type": "turn.completed", "usage": {}})
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
        return path

    def renderer_fixture(self, project):
        """Fabricated local receipt to exercise rejection paths, never a live trial."""
        out = project / "output"
        out.mkdir()
        (out / "document.html").write_text((project / "input.html").read_text())
        (out / "figure-1.svg").write_bytes((ROOT / "assets/engineering-library/components/comp-process.svg").read_bytes())
        (out / "document.pdf").write_bytes(b"%PDF-1.7\nsynthetic invalid PDF fixture\n")
        receipt = {"schema": "cse.document-render/1", "status": "unsupported", "font_probes": [],
                   "assets": [], "outputs": []}
        (out / "render-receipt.json").write_text(json.dumps(receipt))
        return receipt

    def missing_failure(self, project):
        from verifier import visual_profile as v
        path = project / "project-visual-profile.json"
        profile, digest = v.load(path)
        receipt = v.preflight(profile, project, ROOT)
        receipt.update(profile_sha256=digest, profile_path=str(path.resolve()), selection="explicit")
        return receipt

    def test_inventory_includes_routing_override_failure_artwork_and_negative(self):
        self.assertEqual(set(E.cases()), {"direct-profile", "indirect-profile", "client-override",
                                         "missing-font", "artwork-preservation", "text-only-negative"})

    def test_prepare_uses_only_declared_runtime_resources_and_preserves_inputs(self):
        project = self.prepare()
        profile = json.loads((project / "project-visual-profile.json").read_text())
        self.assertTrue(all(font["path"].startswith("runtime:") for font in profile["fonts"]))
        from verifier import visual_profile as v
        self.assertEqual(v.preflight(profile, project, ROOT)["status"], "pass")
        self.assertEqual((project / "artwork.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        manifest = json.loads((project / "evaluation-inputs.json").read_text())
        for name, expected in manifest["inputs"].items():
            self.assertEqual(sha256((project / name).read_bytes()).hexdigest(), expected)
        with self.assertRaisesRegex(ValueError, "refusing"):
            E.prepare("direct-profile", project, ROOT)

    def test_client_case_selects_independent_client_profile(self):
        project = self.prepare("client-override")
        manifest = json.loads((project / "evaluation-inputs.json").read_text())
        client = json.loads((project / manifest["profile"]).read_text())
        self.assertEqual(client["authority"]["kind"], "client")
        self.assertEqual({font["family"] for font in client["fonts"]}, {"IBM Plex Mono"})

    def test_missing_font_case_is_blocked_without_silent_fallback(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        with trace.open("a") as stream:
            stream.write(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "exit_code": 1,
                "command": "python3 " + str(ROOT / "scripts/visual_profile.py") + " preflight",
                "aggregated_output": json.dumps(self.missing_failure(project))}}) + "\n")
        result = E.evaluate("missing-font", project, ROOT, trace)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["session_freshness"], "not_inferred_from_trace")
        (project / "output").mkdir()
        (project / "output/document.pdf").write_bytes(b"fallback output")
        self.assertEqual(E.evaluate("missing-font", project, ROOT, trace)["status"], "fail")

    def test_missing_font_without_observed_failure_does_not_complete_review(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        result = E.evaluate("missing-font", project, ROOT, trace)
        self.assertIn({"id": "required_resource_failure_recorded_and_rechecked", "status": "fail"}, result["checks"])

    def test_missing_font_accepts_profile_bound_sidecar_and_explicit_path(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        (project / "output").mkdir()
        receipt = self.missing_failure(project)
        (project / "output/profile-preflight.json").write_text(json.dumps(receipt))
        self.assertEqual(E.evaluate("missing-font", project, ROOT, trace)["status"], "pass")
        (project / "output/profile-preflight.json").rename(project / "output/required-font.json")
        self.assertEqual(E.evaluate("missing-font", project, ROOT, trace, failure_receipt="output/required-font.json")["status"], "pass")

    def test_missing_font_rejects_generic_help_and_argument_errors(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        with trace.open("a") as stream:
            stream.write(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "exit_code": 1,
                "command": "node " + str(ROOT / "scripts/render_technical_document.cjs") + " --help",
                "aggregated_output": json.dumps({"schema": "cse.document-render/1", "status": "error", "findings": ["Mode, --root and --profile are required"]})}}) + "\n")
        result = E.evaluate("missing-font", project, ROOT, trace)
        self.assertIn({"id": "required_resource_failure_recorded_and_rechecked", "status": "fail"}, result["checks"])

    def test_missing_font_rejects_wrong_incomplete_or_stale_recorded_profile(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        (project / "output").mkdir()
        good = self.missing_failure(project)
        variants = {}
        for name in ("no-profile", "wrong-profile", "stale-hash", "wrong-path", "no-findings", "wrong-resource", "stale-font-source", "error"):
            variants[name] = copy.deepcopy(good)
        variants["no-profile"].pop("profile")
        variants["wrong-profile"]["profile"]["id"] = "another-project"
        variants["stale-hash"]["profile_sha256"] = "0" * 64
        variants["wrong-path"]["profile_path"] = str(project / "another-profile.json")
        variants["no-findings"]["findings"] = []
        variants["wrong-resource"]["findings"][0]["id"] = "unselected-font"
        variants["stale-font-source"]["fonts"][0]["sha256"] = "0" * 64
        variants["error"]["status"] = "error"
        for name, receipt in variants.items():
            with self.subTest(name=name):
                (project / "output/profile-preflight.json").write_text(json.dumps(receipt))
                result = E.evaluate("missing-font", project, ROOT, trace)
                self.assertIn({"id": "required_resource_failure_recorded_and_rechecked", "status": "fail"}, result["checks"])

    def test_recorded_missing_font_failure_is_stale_when_font_is_now_present(self):
        project = self.prepare("missing-font")
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")])
        (project / "output").mkdir()
        (project / "output/profile-preflight.json").write_text(json.dumps(self.missing_failure(project)))
        (project / "required-font-not-supplied.woff2").write_bytes((ROOT / "examples/ecosystem-diagram-reference/fonts/IBMPlexSans-Regular.woff2").read_bytes())
        result = E.evaluate("missing-font", project, ROOT, trace)
        self.assertIn({"id": "required_font_unavailable", "status": "fail"}, result["checks"])
        self.assertIn({"id": "required_resource_failure_recorded_and_rechecked", "status": "fail"}, result["checks"])

    def test_text_only_case_checks_absence_without_claiming_answer_correctness(self):
        project = self.prepare("text-only-negative")
        result = E.evaluate("text-only-negative", project, ROOT, self.trace())
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["claim_scope"], "bounded_observable_artifacts_and_recorded_commands")
        (project / "unasked.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.assertEqual(E.evaluate("text-only-negative", project, ROOT, self.trace())["status"], "fail")

    def test_reasoning_and_failed_commands_do_not_prove_activation(self):
        path = self.work / "trace.jsonl"
        command = "cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md")
        path.write_text("\n".join(json.dumps(record) for record in [
            {"type": "item.completed", "item": {"type": "reasoning", "text": command}},
            {"type": "item.completed", "item": {"type": "command_execution", "command": command, "exit_code": 1}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "I used the skill"}}]))
        self.assertEqual(E.commands_from_trace(path), [])

    def test_absent_observable_events_cannot_pass_negative(self):
        project = self.prepare("text-only-negative")
        path = self.work / "trace.json"
        path.write_text("{}")
        self.assertEqual(E.evaluate("text-only-negative", project, ROOT, path)["status"], "fail")

    def test_svg_comparison_preserves_native_geometry_while_allowing_ids_and_paint(self):
        first, second = self.work / "first.svg", self.work / "second.svg"
        first.write_text('<svg xmlns="http://www.w3.org/2000/svg"><g><rect id="source" x="1" y="2" width="3" height="4" fill="#123"/></g></svg>')
        second.write_text('<svg xmlns="http://www.w3.org/2000/svg"><g transform="translate(30 40)"><rect id="occurrence" x="1" y="2" width="3" height="4" fill="#456"/></g></svg>')
        self.assertEqual(E.svg_geometry(first), E.svg_geometry(second))
        second.write_text(second.read_text().replace('width="3"', 'width="9"'))
        self.assertNotEqual(E.svg_geometry(first), E.svg_geometry(second))

    def placement_fixture(self):
        master = self.work / "master.svg"
        first = '<rect x="1" y="2" width="3" height="4" fill="#123"/>'
        second = '<path d="M1 2 L3 4" stroke="#123"/>'
        master.write_text('<svg xmlns="http://www.w3.org/2000/svg">' + first + second + '</svg>')
        selected = '<svg xmlns="http://www.w3.org/2000/svg" data-cse-source="comp-process">'
        return master, first, second, selected

    def test_selected_illustration_may_be_separate_from_standalone_flow(self):
        master, first, second, selected = self.placement_fixture()
        html, flow = self.work / "document.html", self.work / "figure.svg"
        html.write_text('<html><body><figure id="flow">Documentary flow</figure><aside>' + selected + first + second + '</svg></aside></body></html>')
        flow.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect x="20" y="30" width="50" height="60"/></svg>')
        self.assertEqual(E.selected_svg_geometry((html, flow), "comp-process", master),
                         {"retained": True, "occurrences": 1, "complete_occurrences": 1})

    def test_changed_geometry_in_any_identified_occurrence_fails(self):
        master, first, second, selected = self.placement_fixture()
        html, flow = self.work / "document.html", self.work / "figure.svg"
        html.write_text('<html><body>' + selected + first + second + '</svg></body></html>')
        flow.write_text(selected + first.replace('width="3"', 'width="9"') + second + '</svg>')
        self.assertEqual(E.selected_svg_geometry((html, flow), "comp-process", master),
                         {"retained": False, "occurrences": 2, "complete_occurrences": 1})

    def test_master_cannot_be_split_across_incomplete_occurrences(self):
        master, first, second, selected = self.placement_fixture()
        html, flow = self.work / "document.html", self.work / "figure.svg"
        html.write_text('<html><body>' + selected + first + '</svg></body></html>')
        flow.write_text(selected + second + '</svg>')
        self.assertEqual(E.selected_svg_geometry((html, flow), "comp-process", master),
                         {"retained": False, "occurrences": 2, "complete_occurrences": 0})

    def test_unrelated_master_does_not_satisfy_selected_occurrence(self):
        master, first, second, selected = self.placement_fixture()
        html, flow = self.work / "document.html", self.work / "figure.svg"
        html.write_text('<html><body><svg>' + first + second + '</svg>' + selected + first + '</svg></body></html>')
        flow.write_text('<svg xmlns="http://www.w3.org/2000/svg" data-cse-source="another-component">' + first + second + '</svg>')
        self.assertEqual(E.selected_svg_geometry((html, flow), "comp-process", master),
                         {"retained": False, "occurrences": 1, "complete_occurrences": 0})
        html.write_text('<html><body><svg>' + first + second + '</svg></body></html>')
        self.assertEqual(E.selected_svg_geometry((html, flow), "comp-process", master),
                         {"retained": False, "occurrences": 0, "complete_occurrences": 0})

    def test_preservation_compares_region_wording_and_amounts(self):
        first, second = self.work / "first.html", self.work / "second.html"
        first.write_text('<main id="accepted-body">A <b>$400</b> fee.</main>')
        second.write_text('<header>New artwork</header><main id="accepted-body">A <b>$400</b> fee.</main>')
        self.assertEqual(E.region_text(first, "accepted-body"), E.region_text(second, "accepted-body"))
        second.write_text(second.read_text().replace("$400", "$500"))
        self.assertNotEqual(E.region_text(first, "accepted-body"), E.region_text(second, "accepted-body"))

    def test_preserved_html_does_not_cover_missing_or_changed_pdf_body(self):
        original = self.work / "input.html"
        original.write_text('<main id="accepted-body"><h1>Review scope</h1><p>Four hours for $400.</p></main>')
        self.assertTrue(E.pdf_contains_region(original, [{"text": "Header\nReview scope\nFour hours for $400.\nFooter"}]))
        self.assertFalse(E.pdf_contains_region(original, [{"text": "Header\nDifferent visible content.\nFooter"}]))
        self.assertFalse(E.pdf_contains_region(original, [{"text": "Review scope\nFour hours for $500."}]))

    def test_unsupported_receipt_and_empty_evidence_cannot_pass(self):
        project = self.prepare()
        self.renderer_fixture(project)
        trace = self.trace(["cat " + str(ROOT / "skills/generate-engineering-diagrams/SKILL.md"),
                            "node " + str(ROOT / "scripts/render_technical_document.cjs")])
        result = E.evaluate("indirect-profile", project, ROOT, trace)
        self.assertEqual(result["status"], "fail")
        failures = {item["id"] for item in result["checks"] if item["status"] == "fail"}
        self.assertTrue({"renderer_completed", "actual_glyph_fonts_match_selection", "output_hash_inventory_present"} <= failures)

    def test_changed_input_is_reported_even_if_receipt_claims_pass(self):
        project = self.prepare()
        receipt = self.renderer_fixture(project)
        receipt["status"] = "pass"
        (project / "output/render-receipt.json").write_text(json.dumps(receipt))
        (project / "brief.txt").write_text("Weaken the brief")
        result = E.evaluate("indirect-profile", project, ROOT, self.trace())
        self.assertIn({"id": "input_preserved:brief.txt", "status": "fail"}, result["checks"])

    def test_current_hashes_are_bound_to_each_delivered_artifact(self):
        project = self.prepare()
        receipt = self.renderer_fixture(project)
        receipt["outputs"] = [{"path": "document.html", "sha256": E.digest(project / "output/document.html")},
                              {"path": "document.pdf", "sha256": E.digest(project / "output/document.pdf")},
                              {"path": "figure-1.svg", "sha256": E.digest(project / "output/figure-1.svg")}]
        path = project / "output/render-receipt.json"
        path.write_text(json.dumps(receipt))
        result = E.evaluate("indirect-profile", project, ROOT, self.trace())
        self.assertIn({"id": "delivered_artifacts_hash_bound", "status": "pass"}, result["checks"])
        (project / "output/document.pdf").write_bytes(b"Changed PDF")
        result = E.evaluate("indirect-profile", project, ROOT, self.trace())
        self.assertIn({"id": "current_output:document.pdf", "status": "fail"}, result["checks"])
        receipt["outputs"].pop()
        path.write_text(json.dumps(receipt))
        result = E.evaluate("indirect-profile", project, ROOT, self.trace())
        self.assertIn({"id": "delivered_artifacts_hash_bound", "status": "fail"}, result["checks"])

    def test_claimed_pdf_success_is_not_a_substitute_for_actual_pdf_inspection(self):
        project = self.prepare()
        receipt = self.renderer_fixture(project)
        from verifier import visual_profile as v
        selected = project / "project-visual-profile.json"
        preflight = v.preflight(v.load(selected)[0], project, ROOT)
        preflight["profile_sha256"] = E.digest(selected)
        receipt["profile_preflight"] = preflight
        receipt["pdf"] = {"schema": "cse.document-pdf/1", "status": "pass", "checks": {"fonts_embedded_and_readable": True},
                          "sha256": E.digest(project / "output/document.pdf"), "postscript_names": ["IBMPlexSans", "IBMPlexSans-SmBld"], "weights": [400, 600]}
        (project / "output/profile-preflight.json").write_text(json.dumps(preflight))
        (project / "output/render-receipt.json").write_text(json.dumps(receipt))
        result = E.evaluate("indirect-profile", project, ROOT, self.trace())
        self.assertIn({"id": "independent_pdf_inspection", "status": "fail"}, result["checks"])

    def test_cli_malformed_receipt_returns_error(self):
        project = self.prepare()
        self.renderer_fixture(project)
        (project / "output/render-receipt.json").write_text("not JSON")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_visual_guidance.py"), "check", "--case", "indirect-profile",
                                 "--project", str(project), "--runtime", str(ROOT), "--trace", str(self.trace())], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "error")


if __name__ == "__main__":
    unittest.main()
