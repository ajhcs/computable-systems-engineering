"""Discoverable input contract and byte-bound adapter for the existing trace monitor."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from .language import VERSION as CHECKER_VERSION, check_document

VERSION = "sampled-trace-input-1.0"
MAX_INPUT_BYTES = 4 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def schema_document():
    """Return interface help, never a source definition or an executed verdict."""
    return {
        "status": "not_run", "claim_scope": "sampled_trace_input_contract",
        "input_adapter_version": VERSION, "checker_version": CHECKER_VERSION,
        "document_fields": {
            "language_version": "integer 1, not Boolean",
            "clock": {"period": "positive exact decimal string", "unit": "millisecond(s), second(s), or minute(s)"},
            "actors": "nonempty map from actor identifier to empty object",
            "properties": "nonempty map from property identifier to a declaration below",
            "requirements": "nonempty map from stable requirement ID to a supported controlled sentence; not an array",
            "observations": "optional array of successive property-value maps, sampled at the declared clock period",
            "complete": "optional Boolean; true only for a complete declared observation window",
        },
        "property_owner": "required, exactly input or controlled, selected from the authored system boundary; example choices below are not project allocations",
        "property_declarations": {
            "bool": {"type": "bool", "owner": "input"},
            "enum": {"type": "enum", "owner": "input", "values": ["LabelOne", "LabelTwo"]},
            "int": {"type": "int", "owner": "controlled", "min": 0, "max": 10, "scale": "1", "unit": "second"},
        },
        "example_document": {
            "language_version": 1,
            "clock": {"period": "1", "unit": "second"},
            "actors": {"ExampleUnit": {}},
            "properties": {
                "request": {"type": "bool", "owner": "input"},
                "response": {"type": "bool", "owner": "controlled"},
            },
            "requirements": {"R_EXAMPLE": "Whenever request = true, ExampleUnit shall always satisfy response = true."},
            "observations": [], "complete": False,
        },
        "example_scope": {"version": 1, "required": ["R_EXAMPLE"]},
        "scope_contract": "exactly version: integer 1 and required: array of unique stable IDs; use the independently retained obligation scope and its retained raw-byte SHA-256",
        "limits": {"input_bytes_per_file": MAX_INPUT_BYTES},
        "meaning": [
            "Examples describe syntax only. Replace them with existing authored meanings, declarations and actual observations; this command executes no check.",
            "No declaration, property owner, requirement, sample or complete flag is inferred or repaired.",
            "A required review needs every independent obligation. Missing obligations, missing samples, incomplete windows and no exercised trigger cannot yield a successful required review.",
            "The byte digest detects drift against a retained value; it does not authenticate acceptance or protect a scope controlled by the same caller.",
        ],
    }


def _error(code, detail):
    return {"status": "error", "results": {}, "review": True,
            "required_review": True, "claim_scope": "sampled_trace_input_binding",
            "checker_version": CHECKER_VERSION, "input_adapter_version": VERSION,
            "error": {"code": code, "detail": detail}}


def _unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate JSON object key")
        result[name] = value
    return result


def _reject_constant(_value):
    raise ValueError("Non-finite JSON number")


def _decode(raw):
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                       parse_constant=_reject_constant)
    # JSON escapes can decode to an unpaired surrogate, and an exponent can
    # overflow to infinity without using a NaN/Infinity literal. Reject those
    # input values before the monitor computes its canonical UTF-8 identity.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def check_trace_bytes(document_raw, scope_raw, *, scope_sha256, document_sha256=None):
    """Bind exact supplied bytes and preserve the existing language monitor's verdict.

    The independent scope pin is mandatory. Neither a narrowed view nor the trace
    supplies that pin. No parsing of arbitrary engineering prose is performed.
    """
    if not isinstance(document_raw, bytes) or not isinstance(scope_raw, bytes):
        return _error("input", "Document and scope must be UTF-8 JSON bytes")
    if len(document_raw) > MAX_INPUT_BYTES or len(scope_raw) > MAX_INPUT_BYTES:
        return _error("input_limit", "Document or scope exceeds the per-file input byte limit")
    for label, raw, expected in (("scope", scope_raw, scope_sha256),
                                 ("document", document_raw, document_sha256)):
        if expected is None and label == "document":
            continue
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            return _error(f"{label}_digest", f"Retained {label} SHA-256 must be 64 lowercase hexadecimal characters")
        if sha256(raw).hexdigest() != expected:
            return _error(f"{label}_digest", f"Supplied {label} bytes do not match the retained SHA-256")
    try:
        document, scope = _decode(document_raw), _decode(scope_raw)
    except (ValueError, UnicodeError, RecursionError) as exc:
        return _error("json", f"Invalid UTF-8 JSON: {str(exc)[:200]}")
    if not isinstance(scope, dict):
        # None is the monitor's sentinel for candidate-selected scope. A pinned
        # JSON null must never opt this required-review adapter into that mode.
        return _error("scope_schema", "Independent scope must be an explicit manifest object")
    report = check_document(document, review=True, expected=scope)
    report["input_adapter_version"] = VERSION
    report["input_binding"] = {
        "document_sha256": sha256(document_raw).hexdigest(),
        "scope_sha256": sha256(scope_raw).hexdigest(),
        "scope_source": "separately supplied scope matched to retained raw-byte digest",
        "document_pin_checked": document_sha256 is not None,
        "meaning": "Byte identity only; no authenticated decision or protected-runner claim.",
    }
    return report


def _read_bounded(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    commands.add_parser("schema", help="show exact input shapes and a non-executed generic example")
    trace = commands.add_parser("trace", help="check supplied sampled observations against an independent retained scope")
    trace.add_argument("document")
    trace.add_argument("--scope", required=True)
    trace.add_argument("--scope-sha256", required=True, help="previously retained SHA-256 of exact scope file bytes")
    trace.add_argument("--document-sha256", help="optional previously retained SHA-256 of exact trace bytes")
    args = parser.parse_args(argv)
    if args.mode == "schema":
        print(json.dumps(schema_document(), sort_keys=True, indent=2))
        return 0
    try:
        report = check_trace_bytes(_read_bounded(args.document), _read_bounded(args.scope),
                                   scope_sha256=args.scope_sha256,
                                   document_sha256=args.document_sha256)
    except OSError:
        report = _error("input_io", "Cannot read the supplied document or independent scope file")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "pass" else 1
