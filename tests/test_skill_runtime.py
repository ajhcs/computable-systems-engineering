"""Real repo skill discovery paths and CLI use from another working directory."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR, check_sysml

SKILLS = ("develop-system-concept", "develop-conops", "develop-operational-scenarios")
PARSER_AVAILABLE = JAR.is_file() and (CLASSES / "SysmlBridge.class").is_file()


class RuntimeTests(unittest.TestCase):
    def test_installer_explains_unsupported_java_before_download_or_compile(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            java = Path(directory) / "java"
            java.write_text("#!/bin/sh\nprintf 'openjdk 17.0.9\\n'\n")
            java.chmod(0o755)
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/install_sysml_parser.py")],
                                    env=dict(os.environ, PATH=directory), text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("requires Java 21+ and javac 21+", result.stderr)
            self.assertNotIn("bad class file", result.stderr)

    def test_repo_skill_links_resolve_to_complete_skills(self):
        for name in SKILLS:
            skill = ROOT / ".agents/skills" / name
            self.assertTrue(skill.is_symlink())
            self.assertEqual(skill.resolve(), ROOT / "skills" / name)
            self.assertTrue((skill / "SKILL.md").is_file())

    def test_each_independent_launcher_finds_the_same_engine_from_another_directory(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            for name in SKILLS:
                result = subprocess.run([sys.executable, "-B", str(ROOT / ".agents/skills" / name / "scripts/cse.py"),
                                         "runtime"], cwd=directory, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["runtime_root"], str(ROOT))

    @unittest.skipUnless(PARSER_AVAILABLE, "Install the pinned SysML parser")
    def test_joint_concept_scenario_uses_one_model_and_exports_supported_tests(self):
        model = ROOT / "examples/sysml/joint-concept-scenario.sysml"
        for kind in ("concept", "scenario"):
            report = check_sysml(model, syntax_only=True, kind=kind)
            self.assertEqual(report["status"], "pass", report.get("parser_issues"))
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            local_model = Path(directory) / "user-model.sysml"
            local_model.write_bytes(model.read_bytes())
            launcher = ROOT / ".agents/skills/develop-operational-scenarios/scripts/cse.py"
            result = subprocess.run([sys.executable, "-B", str(launcher), "testgen", "user-model.sysml",
                                     "--output", "synthetic-tests.json"], cwd=directory,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            artifact = json.loads((Path(directory) / "synthetic-tests.json").read_text())
            self.assertTrue(artifact["synthetic"])
            generated = artifact["generation"]["results"]["R_RECORD__responseTime"]
            self.assertEqual(generated["coverage"], {"referenced": 2, "witnessed": 2})
            reviewed = check_sysml(local_model, review=True)
            self.assertEqual(reviewed["status"], "unknown")
            self.assertEqual(reviewed["findings"][0]["code"], "scope_missing")

    @unittest.skipUnless(PARSER_AVAILABLE, "Install the pinned SysML parser")
    def test_plain_output_distinguishes_compilation_and_behavior_and_reports_parser_errors(self):
        launcher = ROOT / ".agents/skills/develop-system-concept/scripts/cse.py"
        result = subprocess.run([sys.executable, "-B", str(launcher), "check",
                                 str(ROOT / "examples/sysml/ack.sysml")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no behavior evaluated", result.stdout)
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            model = Path(directory) / "invalid.sysml"
            model.write_text("package Broken { part def ???; }")
            invalid = subprocess.run([sys.executable, "-B", str(launcher), "check", str(model),
                                      "--syntax-only"], text=True, capture_output=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("ERROR", invalid.stdout)
            self.assertIn("invalid.sysml", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
