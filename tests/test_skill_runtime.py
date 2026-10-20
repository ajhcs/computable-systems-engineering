"""Real repo skill discovery paths and CLI use from another working directory."""

import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR, check_sysml

SKILLS = ("develop-system-concept", "develop-conops", "develop-operational-scenarios")
PARSER_AVAILABLE = JAR.is_file() and (CLASSES / "SysmlBridge.class").is_file()


def launcher(name):
    registered = ROOT / ".agents/skills" / name
    # Installed plugins carry real skill directories. Preserve a Windows Git
    # symlink-record checkout rather than rewriting its registration files.
    base = registered if registered.is_dir() else ROOT / "skills" / name
    return base / "scripts/cse.py"


class RuntimeTests(unittest.TestCase):
    def test_installer_explains_unsupported_java_before_download_or_compile(self):
        spec = importlib.util.spec_from_file_location("cse_test_installer", ROOT / "scripts/install_sysml_parser.py")
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        old_java = subprocess.CompletedProcess(["java", "--version"], 0, "openjdk 17.0.9", "")
        errors = io.StringIO()
        with patch.object(installer.subprocess, "run", return_value=old_java) as run, \
                patch.object(installer, "urlopen") as download, redirect_stderr(errors):
            self.assertEqual(installer.main(), 1)
        self.assertIn("requires Java 21+ and javac 21+", errors.getvalue())
        self.assertNotIn("bad class file", errors.getvalue())
        self.assertEqual(run.call_args.args[0], ["java", "--version"])
        self.assertEqual(run.call_count, 1)
        download.assert_not_called()

    def test_repo_skill_registrations_refer_to_complete_skills(self):
        for name in SKILLS:
            skill = ROOT / ".agents/skills" / name
            if skill.is_symlink():
                self.assertEqual(skill.resolve(), ROOT / "skills" / name)
                self.assertTrue((skill / "SKILL.md").is_file())
            else:
                # Windows Git may preserve a tracked link as its target text.
                # This checks metadata, not project discovery through that file.
                self.assertEqual(os.name, "nt")
                self.assertEqual(skill.read_text().strip(), "../../skills/" + name)
                self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file())

    def test_each_independent_launcher_finds_the_same_engine_from_another_directory(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            for name in SKILLS:
                result = subprocess.run([sys.executable, "-B", str(launcher(name)),
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
            entrypoint = launcher("develop-operational-scenarios")
            result = subprocess.run([sys.executable, "-B", str(entrypoint), "testgen", "user-model.sysml",
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
        entrypoint = launcher("develop-system-concept")
        result = subprocess.run([sys.executable, "-B", str(entrypoint), "check",
                                 str(ROOT / "examples/sysml/ack.sysml")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no behavior evaluated", result.stdout)
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            model = Path(directory) / "invalid.sysml"
            model.write_text("package Broken { part def ???; }")
            invalid = subprocess.run([sys.executable, "-B", str(entrypoint), "check", str(model),
                                      "--syntax-only"], text=True, capture_output=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("ERROR", invalid.stdout)
            self.assertIn("invalid.sysml", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
