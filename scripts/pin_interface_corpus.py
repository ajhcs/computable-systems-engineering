#!/usr/bin/env python3
"""Retrieve pinned public bytes into ignored cache; emit metadata, never raw models."""
from hashlib import sha256
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    {"id": "sysml-ev", "repository": "Systems-Modeling/SysML-v2-Release", "revision": "fb97b754f29588b8e9c7a35f370880cd15eb29e7", "family": "official-sysml-example", "format": "SysML v2", "split": "held-out", "path": "sysml/src/examples/State Space Representation Examples/EVSample.sysml", "license_path": "LICENSE", "native_dependency": "Pinned open SysML v2 parser; no behavior oracle supplied"},
    {"id": "nasa-jt9d", "repository": "nasa/T-MATS", "revision": "ad6e4d5d0d76c229db4eb72ca40ef58d5ddc4014", "family": "NASA-T-MATS", "format": "Simulink MDL", "split": "held-out", "path": "Trunk/TMATS_Examples/Example_JT9D/JT9D_Model_Dyn.mdl", "license_path": "LICENSE", "native_dependency": "MATLAB/Simulink and T-MATS; numerical oracle not generated"},
    {"id": "tmt", "repository": "Open-MBEE/TMT-SysML-Model", "revision": "b2a33b71c65678498b538195dcb947a7962ca75b", "family": "Thirty-Meter-Telescope", "format": "MagicDraw SysML v1 archive", "split": "reserved-not-run", "path": "TMT-2024x.mdzip", "license_path": "LICENSE", "native_dependency": "Compatible Cameo/MagicDraw; migration/semantic oracle unavailable"},
]


def retrieve(url, path):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=45) as response:
            raw = response.read(35000001)
        if len(raw) > 35000000:
            raise ValueError("Public input exceeds 35 MB cap")
        path.write_bytes(raw)
    raw = path.read_bytes()
    return {"url": url, "sha256": sha256(raw).hexdigest(), "bytes": len(raw), "cache_path": str(path.relative_to(ROOT))}


def main():
    records = []
    for source in SOURCES:
        directory = ROOT / ".cache/interface-benchmark/corpus" / source["id"]
        directory.mkdir(parents=True, exist_ok=True)
        base = "https://raw.githubusercontent.com/" + source["repository"] + "/" + source["revision"] + "/"
        record = dict(source)
        for key, path in (("model", source["path"]), ("license", source["license_path"]), ("readme", "README.md")):
            record[key] = retrieve(base + urllib.parse.quote(path), directory / Path(path).name)
        text = (directory / source["license_path"]).read_text(errors="replace")
        record["license_identifier"] = "Apache-2.0" if "Apache License" in text else "EPL-2.0" if text.startswith("Eclipse Public License - v 2.0") else "manual-review-required"
        record["oracle_boundary"] = "Upstream source bytes and native declarations; structural parser results when supported. No simulated performance or accepted engineering interpretation."
        records.append(record)
    destination = ROOT / "benchmarks/interface/corpus-lock.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"retrieved_utc_date": "2026-10-08", "sources": records}, indent=2) + "\n")
    print(json.dumps(records))


if __name__ == "__main__":
    main()
