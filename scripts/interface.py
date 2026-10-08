#!/usr/bin/env python3
"""Progressive local interface. Read JSON requests on stdin; emit one JSON result."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cse_interface.contracts import InterfaceError, command, describe, discover, obj, TEXT, validate
from cse_interface.elicitation import transition, QUESTION
from cse_interface.limits import (REQUEST_LIMIT_BYTES, LEDGER_LIMIT_BYTES,
                                  ANSWER_LIMIT_BYTES, RESOLUTION_RESERVE_BYTES, json_bytes)


def read_json(stream, *, limit=REQUEST_LIMIT_BYTES, kind="request"):
    raw = stream.read(limit + 1)
    size = len(raw) if isinstance(raw, bytes) else len(raw.encode("utf-8"))
    if size > limit:
        raise InterfaceError("input_limit" if kind == "request" else "ledger_limit",
                             f"{kind.capitalize()} exceeds {limit} UTF-8 bytes",
                             "Supply only the operation arguments." if kind == "request" else
                             "Retain the existing ledger; no state has been changed.")
    def reject(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result
    return json.loads(raw, parse_constant=reject, object_pairs_hook=unique)


def compact(report):
    """Keep verdict/limits and provide explicit retrieval for omitted detail."""
    result = dict(report)
    omitted = {}
    if "inventory" in result:
        inventory = result.pop("inventory")
        result["inventory_counts"] = {k: len(v) for k, v in inventory.items() if isinstance(v, list)}
        omitted["inventory"] = True
    for key in ("findings", "parser_issues"):
        if isinstance(result.get(key), list) and len(result[key]) > 8:
            omitted[key] = len(result[key]) - 8
            result[key] = result[key][:8]
    if omitted:
        result["details_omitted"] = omitted
        result["recovery"] = "Repeat the same invoke request with --detail for complete evidence."
    return result


def invoke(request, detail=False):
    validate(request, obj({"operation": TEXT, "arguments": {}}, ("operation", "arguments")), "request")
    argv = command(request["operation"], request["arguments"])
    try:
        run = subprocess.run([sys.executable, "-B", *argv], text=True, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise InterfaceError("checker_timeout", "Checker exceeded 120 seconds; no successful verdict", "Reduce the explicit model scope or investigate parser/runtime performance.")
    try:
        report = json.loads(run.stdout)
    except ValueError:
        raise InterfaceError("checker_error", (run.stderr or run.stdout or "Checker produced no JSON")[:1500], "Check runtime and input files; retry the documented command.")
    if not isinstance(report, dict) or report.get("status") not in ("pass", "fail", "unknown", "unsupported", "not_run", "error"):
        raise InterfaceError("invalid_report", "Checker did not return a recognized status", "Inspect the complete checker output; do not infer success.")
    if run.returncode and report["status"] == "pass":
        raise InterfaceError("contradictory_report", "Checker exited unsuccessfully with a pass report", "Investigate the checker before claiming success.")
    return report if detail else compact(report)


def elicit(path, request):
    path = Path(path).absolute()
    if not path.name.endswith(".cse-questions.json") or not path.parent.is_dir():
        raise InterfaceError("ledger_path", "Use an existing private directory and *.cse-questions.json", "Example: work/draft.cse-questions.json")
    if path.exists() and path.is_symlink():
        raise InterfaceError("ledger_path", "Ledger cannot be a symlink", "Choose a new regular file.")
    protected = request.get("context", {}).get("models", []) if isinstance(request, dict) else []
    if path in {Path(x).resolve() for x in protected}:
        raise InterfaceError("ledger_collision", "Ledger cannot overwrite a source model", "Choose a separate ledger path.")
    # Single-process/user concurrency protection; not an acceptance authority boundary.
    with open(str(path) + ".lock", "a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            with path.open("rb") as stream:
                state = read_json(stream, limit=LEDGER_LIMIT_BYTES, kind="ledger")
            if not isinstance(state, dict) or state.get("format") != "cse-questions-1" or not isinstance(state.get("questions"), list):
                raise InterfaceError("invalid_ledger", "File is not a CSE question ledger", "Choose a new ledger; retain the existing file.")
        else:
            state = {"format": "cse-questions-1", "questions": []}
        new_state, result = transition(state, request)
        serialized = json_bytes(new_state)
        reserve = RESOLUTION_RESERVE_BYTES if any(item["status"] == "pending" for item in new_state["questions"]) else 0
        if len(serialized) + reserve > LEDGER_LIMIT_BYTES:
            raise InterfaceError("ledger_capacity", "No question admitted: ledger capacity would be exceeded",
                                 "Resolve or cancel any existing question; retain this ledger and use a new scoped ledger for further questions.")
        if new_state != state:
            with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as tmp:
                temporary = Path(tmp.name)
                tmp.write(serialized)
                tmp.flush()
                os.fsync(tmp.fileno())
            try:
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "describe", "invoke", "elicit", "elicit-help"))
    parser.add_argument("operation", nargs="?")
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--state")
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover()
        elif args.command == "describe":
            result = describe(args.operation)
        elif args.command == "invoke":
            result = invoke(read_json(sys.stdin), args.detail)
        elif args.command == "elicit-help":
            result = {"prepare": {"action": "prepare", "context": {"operation": "edit|decompose|migrate|compare", "models": ["existing file"], "known": {"field": "already supplied value"}}, "question": QUESTION},
                      "answer": {"action": "answer", "id": "returned id", "revision": "returned revision", "outcome": "accept|cancel|decline", "content": "typed answer; accept only"},
                      "scope": "Domain clarification only; provider safety/permission confirmations remain with the host. No model writes or acceptance.",
                      "limits": {"request_utf8_bytes": REQUEST_LIMIT_BYTES, "ledger_bytes": LEDGER_LIMIT_BYTES,
                                 "answer_serialized_json_bytes": ANSWER_LIMIT_BYTES}}
        else:
            if not args.state:
                raise InterfaceError("ledger_required", "Elicitation requires --state", "Use a private *.cse-questions.json ledger.")
            result = elicit(args.state, read_json(sys.stdin))
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 1 if result.get("status") in ("fail", "unknown", "unsupported", "not_run", "error") else 0
    except InterfaceError as exc:
        print(json.dumps(exc.report(), sort_keys=True))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"status": "error", "code": "invalid_input", "message": str(exc)[:1000], "recovery": "Correct the JSON or file input; run describe or elicit-help."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
