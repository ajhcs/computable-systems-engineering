#!/usr/bin/env python3
"""Measure actual repository payloads; regex counts are not billed model tokens."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cse_interface.contracts import describe, discover

BASE = "b01ef01698450e5a47cc20f957fe93a09e9744b4"
SKILLS = ("develop-system-concept", "develop-conops", "develop-operational-scenarios")


def measure(text):
    return {"utf8_bytes": len(text.encode("utf-8")), "unicode_characters": len(text),
            "regex_wordpunct_v2": len(re.findall(r"\w+|[^\w\s]", text))}


def read(path, baseline=False):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode() if baseline else (ROOT / path).read_text()


def catalog(baseline=False):
    entries = []
    for name in SKILLS if baseline else ("cse", *SKILLS):
        raw = read(f"skills/{name}/SKILL.md", baseline)
        entries.append(raw.split("---", 2)[1].strip())
    return "\n\n".join(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = {"method": "regex-wordpunct-v2: Unicode word runs or single nonspace punctuation over exact UTF-8 payload; no JSON wrapping. Not a model tokenizer.",
              "baseline": BASE, "scope": "Repository-controlled payloads only; host/system/catalog wrappers and provider caching excluded.", "activation": {}, "operations": {}}
    result["initial_catalog"] = {"baseline": measure(catalog(True)), "optimized": measure(catalog())}
    result["manifest"] = {"baseline": measure(read(".codex-plugin/plugin.json", True)), "optimized": measure(read(".codex-plugin/plugin.json"))}
    for name in SKILLS:
        result["activation"][name] = {"baseline": measure(read(f"skills/{name}/SKILL.md", True)), "optimized": measure(read(f"skills/{name}/SKILL.md"))}
    result["cse_entry"] = measure(read("skills/cse/SKILL.md"))
    result["discovery"] = measure(json.dumps(discover(), sort_keys=True, separators=(",", ":")))
    for op in ("inspect", "validate", "testgen", "diff"):
        description = describe(op)
        # Normalize installation prefix solely in static comparison; runtime outputs below are exact.
        description["guide"] = str(Path(description["guide"]).relative_to(ROOT))
        schema = json.dumps(description, sort_keys=True, separators=(",", ":"))
        guide = read(description["guide"])
        result["operations"][op] = {"schema": measure(schema), "guide": measure(guide),
            "optimized_cold_entry_discover_schema_guide": measure(read("skills/cse/SKILL.md") + json.dumps(discover(), sort_keys=True, separators=(",", ":")) + schema + guide),
            "baseline_concept_entry_and_sysml_guide": measure(read("skills/develop-system-concept/SKILL.md", True) + read("skills/develop-system-concept/references/sysml.md", True))}
    request = {"operation": "validate", "arguments": {"models": ["examples/sysml/ack.sysml"], "mode": "syntax"}}
    before = subprocess.run([sys.executable, "scripts/sysml.py", "examples/sysml/ack.sysml", "--syntax-only", "--json"], cwd=ROOT, text=True, capture_output=True)
    after = subprocess.run([sys.executable, "scripts/interface.py", "invoke"], input=json.dumps(request), cwd=ROOT, text=True, capture_output=True)
    left, right = json.loads(before.stdout), json.loads(after.stdout)
    if before.returncode or after.returncode or any(left.get(k) != right.get(k) for k in ("status", "model_sha256", "claim_scope", "coverage", "findings")):
        raise RuntimeError("Cannot measure savings without equivalent parser results")
    result["actual_syntax_operation"] = {"fixture": "examples/sysml/ack.sysml (synthetic, not an AI task)",
        "baseline_response": measure(before.stdout), "optimized_response": measure(after.stdout),
        "optimized_request": measure(json.dumps(request)), "status": right["status"], "model_sha256": right["model_sha256"],
        "missing_details": right.get("details_omitted", {}), "claim_scope": right["claim_scope"]}
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
