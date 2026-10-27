"""Installed runtime cache selection and checking from a read-only package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CACHE, CLASSES, JAR, LIBRARY


class CacheTests(unittest.TestCase):
    def run_command(self, args, cache, cwd):
        return subprocess.run([sys.executable, "-B", *map(str, args)], cwd=cwd,
                              env=dict(os.environ, CSE_SYSML_CACHE=str(cache),
                                       PYTHONDONTWRITEBYTECODE="1"),
                              capture_output=True, text=True, timeout=40)

    def test_installer_checker_and_launcher_agree_on_external_cache(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temp:
            caller = Path(temp)
            cache = caller / "external cache"
            script = ("import runpy,json; from verifier.sysml import CACHE; "
                      "data=runpy.run_path('scripts/install_sysml_parser.py'); "
                      "print(json.dumps([str(CACHE),str(data['CACHE'])]))")
            result = self.run_command(["-c", script], cache, ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [str(cache), str(cache)])
            result = self.run_command([ROOT / "skills/develop-conops/scripts/cse.py", "runtime"], cache, caller)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["sysml_cache"], str(cache))
            self.assertFalse(cache.exists(), "Runtime discovery must not install or write a cache")

    def test_empty_selected_cache_does_not_fall_back_to_repository_parser(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temp:
            cache = Path(temp) / "empty"
            result = self.run_command([ROOT / "scripts/sysml.py", ROOT / "examples/sysml/concept.sysml",
                                       "--syntax-only", "--json"], cache, temp)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "error")
            self.assertIn("not installed", report["findings"][0]["detail"])
            result = self.run_command([ROOT / "scripts/check.py", "--require-sysml"], cache, temp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing or stale", result.stderr)
            self.assertFalse(cache.exists())

    @unittest.skipUnless(JAR.is_file() and LIBRARY.is_dir() and (CLASSES / "SysmlBridge.class").is_file(),
                         "Install the pinned parser for the read-only package integration check")
    def test_readonly_package_checks_with_external_writable_cache(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temp:
            temp = Path(temp)
            package, cache = temp / "package", temp / "cache"
            for name in ("scripts", "verifier", "tools"):
                shutil.copytree(ROOT / name, package / name, ignore=shutil.ignore_patterns("__pycache__"))
            for name in ("pilot-2025-09", "classes"):
                shutil.copytree(CACHE / name, cache / name)
            paths = list(package.rglob("*")) + [package]
            try:
                for path in paths:
                    path.chmod(0o555 if path.is_dir() else 0o444)
                result = self.run_command([package / "scripts/sysml.py", ROOT / "examples/sysml/concept.sysml",
                                           "--syntax-only", "--kind", "concept", "--json"], cache, temp)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "pass")
                self.assertTrue((cache / "parser.lock").is_file())
                self.assertFalse((package / ".cache").exists())
            finally:
                for path in paths:
                    path.chmod(0o755 if path.is_dir() else 0o644)


if __name__ == "__main__":
    (ROOT / ".tmp").mkdir(exist_ok=True)
    unittest.main()
