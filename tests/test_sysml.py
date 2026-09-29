"""Integration tests against the pinned upstream SysML v2 pilot parser."""

import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR, check_sysml
import verifier.sysml as sysml_module

MODEL = ROOT / "examples/sysml/ack.sysml"
MANIFEST = json.loads((ROOT / "examples/sysml/ack-manifest.json").read_text())
EVIDENCE = json.loads((ROOT / "examples/sysml/ack-evidence.json").read_text())
EVENT_MODEL = ROOT / "examples/sysml/correlated-events.sysml"
EVENT_MANIFEST = json.loads((ROOT / "examples/sysml/correlated-events-manifest.json").read_text())
EVENT_EVIDENCE = json.loads((ROOT / "examples/sysml/correlated-events-evidence.json").read_text())
COMPOSED = [ROOT / "examples/sysml/composed-parts.sysml",
            ROOT / "examples/sysml/composed-requirement.sysml"]
COMPOSED_MANIFEST = json.loads((ROOT / "examples/sysml/composed-manifest.json").read_text())
COMPOSED_EVIDENCE = json.loads((ROOT / "examples/sysml/composed-evidence.json").read_text())
QUANTITY_MODEL = ROOT / "examples/sysml/quantity.sysml"
QUANTITY_MANIFEST = json.loads((ROOT / "examples/sysml/quantity-manifest.json").read_text())
QUANTITY_EVIDENCE = json.loads((ROOT / "examples/sysml/quantity-evidence.json").read_text())


@unittest.skipUnless(JAR.is_file() and (CLASSES / "SysmlBridge.class").is_file(),
                     "Run python3 scripts/install_sysml_parser.py to enable parser integration tests")
class SysmlTests(unittest.TestCase):
    def test_real_parser_and_trace_boundaries(self):
        report = check_sysml(MODEL, manifest=MANIFEST, evidence=EVIDENCE, review=True)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["parser_issues"], [])
        self.assertEqual(report["results"]["R_ACK__responseTime"]["check"]["claim_scope"], "required_sampled_trace")
        self.assertEqual(report["coverage"]["compiled"], ["R_ACK__responseTime"])

        late = copy.deepcopy(EVIDENCE)
        late["observations"][3]["AckExample::controller::acknowledged"] = False
        self.assertEqual(check_sysml(MODEL, manifest=MANIFEST, evidence=late, review=True)["status"], "fail")
        prefix = copy.deepcopy(EVIDENCE)
        prefix["observations"] = prefix["observations"][:3]
        self.assertEqual(check_sysml(MODEL, manifest=MANIFEST, evidence=prefix, review=True)["status"], "unknown")
        stale = copy.deepcopy(EVIDENCE)
        stale["model_sha256"] = "0" * 64
        self.assertEqual(check_sysml(MODEL, manifest=MANIFEST, evidence=stale, review=True)["status"], "error")

    def test_independent_scope_and_source_binding(self):
        missing_scope = check_sysml(MODEL, evidence=EVIDENCE, review=True)
        self.assertEqual(missing_scope["status"], "unknown")
        omitted = copy.deepcopy(MANIFEST)
        omitted["expected"].append({"id": "R_OTHER", "constraint": "required", "source": "SYN-02"})
        report = check_sysml(MODEL, manifest=omitted, evidence=EVIDENCE, review=True)
        self.assertEqual(report["status"], "unknown")
        self.assertTrue(any(item["code"] == "missing_obligation" for item in report["findings"]))
        wrong_source = copy.deepcopy(MANIFEST)
        wrong_source["expected"][0]["source"] = "SYN-02"
        self.assertEqual(check_sysml(MODEL, manifest=wrong_source, evidence=EVIDENCE, review=True)["status"], "error")

    def test_bad_sysml_and_unsupported_narrative(self):
        original = MODEL.read_text()
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "case.sysml"
            path.write_text(original.replace("part def Controller {", "part def Controller ??? {"))
            report = check_sysml(path)
            self.assertEqual(report["status"], "error")
            self.assertTrue(report["parser_issues"])

            path.write_text(original.replace("doc cse /*", "doc narrative /*"))
            report = check_sysml(path)
            self.assertEqual(report["status"], "unsupported")
            self.assertEqual(report["coverage"]["unsupported"], ["R_ACK__responseTime"])

            path.write_text(original.replace("unit.acknowledged = true", "unit.missing = true"))
            report = check_sysml(path)
            self.assertEqual(report["status"], "error")
            self.assertTrue(any(item["code"] == "controlled_clause" for item in report["findings"]))

    def test_cli_and_work_budget(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/sysml.py"), str(MODEL),
                                 "--manifest", str(ROOT / "examples/sysml/ack-manifest.json"),
                                 "--evidence", str(ROOT / "examples/sysml/ack-evidence.json"),
                                 "--review", "--json"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")
        limited = check_sysml(MODEL, manifest=MANIFEST, evidence=EVIDENCE, review=True, work_cap=1)
        self.assertEqual(limited["status"], "unknown")

    def test_all_skill_model_shapes_validate(self):
        for name in ("concept", "conops", "scenario"):
            with self.subTest(name=name):
                report = check_sysml(ROOT / "examples/sysml" / f"{name}.sysml", syntax_only=True)
                self.assertEqual(report["status"], "pass", report.get("parser_issues"))

    def test_correlated_sysml_events(self):
        report = check_sysml(EVENT_MODEL, manifest=EVENT_MANIFEST, evidence=EVENT_EVIDENCE, review=True)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["results"]["R_EVENT__responseTime"]["check"]["coverage"]["matched"], 2)
        wrong = copy.deepcopy(EVENT_EVIDENCE)
        wrong["events"][3]["correlationId"] = "C"
        self.assertEqual(check_sysml(EVENT_MODEL, manifest=EVENT_MANIFEST, evidence=wrong, review=True)["status"], "fail")
        early = copy.deepcopy(EVENT_EVIDENCE)
        early["events"] = early["events"][:2]
        early["observed_until"] = {"time": "1", "unit": "seconds"}
        self.assertEqual(check_sysml(EVENT_MODEL, manifest=EVENT_MANIFEST, evidence=early, review=True)["status"], "unknown")
        missing_event = {"model_sha256": EVENT_EVIDENCE["model_sha256"], "complete": True}
        self.assertEqual(check_sysml(EVENT_MODEL, manifest=EVENT_MANIFEST,
                                     evidence=missing_event, review=True)["status"], "unknown")

    def test_cross_file_import_and_stable_bundle(self):
        report = check_sysml(COMPOSED, manifest=COMPOSED_MANIFEST,
                             evidence=COMPOSED_EVIDENCE, review=True)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["results"]["R_COMPOSED__responseTime"]["sysml_source"],
                         "examples/sysml/composed-requirement.sysml")
        self.assertEqual(report["results"]["R_COMPOSED__responseTime"]["sysml_line"], 16)
        reverse = check_sysml(COMPOSED[::-1], syntax_only=True)
        self.assertEqual(reverse["model_sha256"], report["model_sha256"])
        self.assertEqual(reverse["status"], "pass")
        missing = check_sysml(COMPOSED[1], syntax_only=True)
        self.assertEqual(missing["status"], "error")

    def test_unrelated_declared_fields_and_events_do_not_block_slice(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "wide.sysml"
            source = EVENT_MODEL.read_text().replace(
                "out event occurrence ackSent {",
                "in event occurrence health { attribute code : String; }\n"
                "        out event occurrence ackSent {")
            source = source.replace("attribute correlationId : String;",
                                    "attribute correlationId : String; attribute detail : String;")
            path.write_text(source)
            evidence = copy.deepcopy(EVENT_EVIDENCE)
            evidence["model_sha256"] = sha256(path.read_bytes()).hexdigest()
            for item in evidence["events"]:
                item["detail"] = "synthetic"
            evidence["events"].insert(2, {"event": "EventExample::controller::health", "time": "0.75",
                                           "unit": "seconds", "code": "nominal"})
            report = check_sysml(path, manifest=EVENT_MANIFEST, evidence=evidence, review=True)
            self.assertEqual(report["status"], "pass", report["findings"])

            evidence["events"][2]["event"] = "EventExample::controller::undeclared"
            self.assertEqual(check_sysml(path, manifest=EVENT_MANIFEST, evidence=evidence, review=True)["status"], "error")

    def test_extra_unrelated_attribute_and_shape_gate(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "wide.sysml"
            path.write_text(MODEL.read_text().replace("ScalarValues::Boolean;", "ScalarValues::*;").replace(
                "out attribute acknowledged : Boolean;",
                "out attribute acknowledged : Boolean;\n        in attribute note : String;"))
            evidence = copy.deepcopy(EVIDENCE)
            evidence["model_sha256"] = sha256(path.read_bytes()).hexdigest()
            evidence["observations"][0]["AckExample::controller::note"] = "synthetic"
            report = check_sysml(path, manifest=MANIFEST, evidence=evidence, review=True)
            self.assertEqual(report["status"], "pass", report["findings"])

        self.assertEqual(check_sysml(ROOT / "examples/sysml/concept.sysml", kind="concept", syntax_only=True)["status"], "pass")
        self.assertEqual(check_sysml(MODEL, kind="concept", syntax_only=True)["status"], "unknown")

    def test_native_and_controlled_dual_authority_rejected(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "dual.sysml"
            path.write_text(MODEL.read_text().replace("            */\n        }",
                                                      "            */\n            true\n        }"))
            syntax = check_sysml(path, syntax_only=True)
            self.assertEqual(syntax["status"], "pass", syntax["parser_issues"])
            self.assertTrue(syntax["inventory"]["constraints"][0]["has_native_expression"])
            report = check_sysml(path)
            self.assertEqual(report["status"], "error")
            self.assertTrue(any(item["code"] == "dual_authority" for item in report["findings"]))

    def test_short_ids_unique_across_model_files(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "duplicate.sysml"
            path.write_text((ROOT / "examples/sysml/concept.sysml").read_text().replace(
                "ToolLibraryConcept", "AnotherConcept"))
            report = check_sysml([ROOT / "examples/sysml/concept.sysml", path], syntax_only=True)
            self.assertEqual(report["status"], "error")
            self.assertTrue(any(item["code"] == "identity" and "Duplicate" in item["detail"]
                                for item in report["findings"]))

    def test_exact_bounded_quantity_and_unit(self):
        report = check_sysml(QUANTITY_MODEL, manifest=QUANTITY_MANIFEST,
                             evidence=QUANTITY_EVIDENCE, review=True)
        self.assertEqual(report["status"], "pass", report["findings"])
        invalid_value = copy.deepcopy(QUANTITY_EVIDENCE)
        invalid_value["observations"][3]["AckExample::controller::elapsed"] = 101
        self.assertEqual(check_sysml(QUANTITY_MODEL, manifest=QUANTITY_MANIFEST,
                                     evidence=invalid_value, review=True)["status"], "error")

        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "wrong-unit.sysml"
            path.write_text(QUANTITY_MODEL.read_text().replace("unit.elapsed <= 2 second",
                                                               "unit.elapsed <= 2 meter"))
            report = check_sysml(path)
            self.assertEqual(report["status"], "error")
            self.assertTrue(any(item["code"] == "controlled_clause" for item in report["findings"]))

            path.write_text(QUANTITY_MODEL.read_text().replace("doc cseType", "doc notes"))
            report = check_sysml(path)
            self.assertEqual(report["status"], "unsupported")
            self.assertEqual(report["coverage"]["unsupported"], ["R_DURATION__responseTime"])

    def test_synthetic_influence_export_is_separate_from_evidence(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            output = Path(directory) / "generated.json"
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/sysml_testgen.py"),
                                     str(MODEL), "--manifest", str(ROOT / "examples/sysml/ack-manifest.json"),
                                     "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            artifact = json.loads(output.read_text())
            self.assertTrue(artifact["synthetic"])
            self.assertEqual(artifact["status"], "pass")
            clause = artifact["generation"]["results"]["R_ACK__responseTime"]
            self.assertEqual(clause["coverage"], {"referenced": 2, "witnessed": 2})
            for variable, item in clause["variables"].items():
                self.assertEqual(item["status"], "witness")
                self.assertEqual(item["pass_result"]["status"], "pass")
                self.assertEqual(item["fail_result"]["status"], "fail")
                changed = [(index, name) for index, (left, right) in enumerate(
                    zip(item["pass_trace"], item["fail_trace"]))
                           for name in left if left[name] != right[name]]
                self.assertEqual(changed, [(item["changed_index"], clause["binding"][variable])])
                for trace, expected in ((item["pass_trace"], "pass"),
                                        (item["fail_trace"], "fail")):
                    evidence = {"model_sha256": artifact["model_sha256"],
                                "complete": True, "observations": trace}
                    checked = check_sysml(MODEL, manifest=MANIFEST, evidence=evidence, review=True)
                    self.assertEqual(checked["status"], expected)
            self.assertEqual(check_sysml(MODEL, manifest=MANIFEST, evidence=artifact,
                                         review=True)["status"], "error")

    def test_event_generation_reports_unsupported(self):
        report = check_sysml(EVENT_MODEL, manifest=EVENT_MANIFEST, generate_tests=True)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["test_generation"]["status"], "unsupported")

    def test_nested_attributes_are_not_fabricated_as_direct_bindings(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "nested.sysml"
            path.write_text(MODEL.read_text().replace(
                "in attribute request : Boolean;\n        out attribute acknowledged : Boolean;",
                "part inner {\n            in attribute request : Boolean;\n"
                "            out attribute acknowledged : Boolean;\n        }"))
            syntax = check_sysml(path, syntax_only=True)
            self.assertEqual(syntax["status"], "pass", syntax["parser_issues"])
            self.assertEqual(syntax["inventory"]["attributes"], [])
            compiled = check_sysml(path, generate_tests=True)
            self.assertNotEqual(compiled["status"], "pass")
            self.assertEqual(compiled["test_generation"]["status"], "unknown")

    def test_manifest_component_identity_cannot_alias(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "ambiguous.sysml"
            path.write_text(MODEL.read_text().replace(
                "require constraint responseTime", "require constraint foo__responseTime"))
            wrong = copy.deepcopy(MANIFEST)
            wrong["expected"][0]["id"] = "R_ACK__foo"
            report = check_sysml(path, manifest=wrong)
            self.assertEqual(report["status"], "unknown")
            self.assertTrue(any(item["code"] == "unclassified_obligation" for item in report["findings"]))
            self.assertTrue(any(item["code"] == "missing_obligation" for item in report["findings"]))

    def test_stale_compiled_bridge_is_rejected(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            stale = Path(directory) / "old.source.sha256"
            stale.write_text("0" * 64)
            with patch.object(sysml_module, "BRIDGE_STAMP", stale):
                report = check_sysml(MODEL, syntax_only=True)
            self.assertEqual(report["status"], "error")
            self.assertIn("source changed", report["findings"][0]["detail"])

    def test_uncomputed_native_constraints_and_inheritance_cannot_pass_review(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        cases = {
            "native-constraint": MODEL.read_text().replace(
                "out attribute acknowledged : Boolean;",
                "out attribute acknowledged : Boolean;\n"
                "        assert constraint fixedResponse { acknowledged == false }"),
            "native-value": MODEL.read_text().replace(
                "out attribute acknowledged : Boolean;",
                "out attribute acknowledged : Boolean = false;"),
            "inheritance": MODEL.read_text().replace(
                "part def Controller {", "part def ParentController;\n    part def Controller :> ParentController {"),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            for name, source in cases.items():
                with self.subTest(name=name):
                    path = Path(directory) / f"{name}.sysml"
                    path.write_text(source)
                    syntax = check_sysml(path, syntax_only=True)
                    self.assertEqual(syntax["status"], "pass", syntax.get("parser_issues"))
                    evidence = copy.deepcopy(EVIDENCE)
                    evidence["model_sha256"] = sha256(path.read_bytes()).hexdigest()
                    report = check_sysml(path, manifest=MANIFEST, evidence=evidence, review=True)
                    self.assertEqual(report["status"], "unsupported", report["findings"])
                    generated = check_sysml(path, generate_tests=True)
                    self.assertNotEqual(generated["test_generation"]["status"], "pass")

    def test_native_correlation_value_cannot_be_ignored(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            path = Path(directory) / "event.sysml"
            path.write_text(EVENT_MODEL.read_text().replace(
                "attribute correlationId : String;", 'attribute correlationId : String = "A";'))
            syntax = check_sysml(path, syntax_only=True)
            self.assertEqual(syntax["status"], "pass", syntax.get("parser_issues"))
            evidence = copy.deepcopy(EVENT_EVIDENCE)
            evidence["model_sha256"] = sha256(path.read_bytes()).hexdigest()
            report = check_sysml(path, manifest=EVENT_MANIFEST, evidence=evidence, review=True)
            self.assertEqual(report["status"], "unsupported", report["findings"])


if __name__ == "__main__":
    unittest.main()
