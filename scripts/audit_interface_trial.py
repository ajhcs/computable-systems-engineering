#!/usr/bin/env python3
"""Check the frozen snapshot against Git and collect new conversation messages."""
import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial")
    args = parser.parse_args()
    if args.trial not in {f"{c}-{n}" for c in ("baseline", "optimized") for n in range(1, 11)}:
        raise ValueError("Unknown trial")
    folder = ROOT / ".cache/interface-benchmark/trials" / args.trial
    manifest = json.loads((folder / "run-manifest.json").read_text())
    archive = subprocess.check_output(["git", "archive", manifest["revision"]], cwd=ROOT)
    changed, count = [], 0
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for entry in bundle.getmembers():
            path = folder / entry.name
            if entry.isfile():
                count += 1
                expected = bundle.extractfile(entry).read()
                if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
                    changed.append(entry.name)
            elif entry.issym():
                count += 1
                if not path.is_symlink() or os.readlink(path) != entry.linkname:
                    changed.append(entry.name)
    events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
    messages = [event["item"]["text"] for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
    result = {"checked_frozen_files": count, "modified_frozen_files": changed, "runtime_and_source_snapshot_preserved": not changed,
              "event_types": sorted({event.get("type") for event in events}), "agent_messages": messages,
              "events_sha256": sha256((folder / "events.jsonl").read_bytes()).hexdigest()}
    (folder / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
