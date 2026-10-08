"""One source of truth for discovery, schemas and strict argument validation."""
from pathlib import Path
import math
import re

ROOT = Path(__file__).resolve().parents[1]


class InterfaceError(ValueError):
    def __init__(self, code, message, recovery):
        super().__init__(message)
        self.code, self.recovery = code, recovery

    def report(self):
        return {"status": "error", "code": self.code, "message": str(self), "recovery": self.recovery}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


TEXT = {"type": "string", "minLength": 1, "maxLength": 4096}
PATHS = {"type": "array", "items": TEXT, "minItems": 1, "maxItems": 128, "uniqueItems": True}
BOOL = {"type": "boolean"}
OPERATIONS = {
    "inspect": {"summary": "Read one parsed element and its dependencies.", "schema": obj({"models": PATHS, "id": TEXT}, ("models", "id")), "script": "sysml_view.py", "guide": "docs/interface/inspect.md"},
    "validate": {"summary": "Check syntax, compile clauses, or review supplied evidence.", "schema": obj({"models": PATHS, "mode": {"enum": ["syntax", "compile", "review"]}, "kind": {"enum": ["concept", "conops", "scenario"]}, "manifest": TEXT, "evidence": TEXT}, ("models", "mode")), "script": "sysml.py", "guide": "docs/interface/validate.md"},
    "testgen": {"summary": "Generate bounded synthetic tests, not observed evidence.", "schema": obj({"models": PATHS, "manifest": TEXT, "max_rows": {"type": "integer", "minimum": 1, "maximum": 256}, "evaluation_cap": {"type": "integer", "minimum": 1, "maximum": 100000}}, ("models",)), "script": "sysml_testgen.py", "guide": "docs/interface/validate.md"},
    "diff": {"summary": "Compare structure and documentation in two model bundles.", "schema": obj({"before": PATHS, "after": PATHS}, ("before", "after")), "script": "sysml_diff.py", "guide": "docs/interface/inspect.md"},
}


def validate(value, schema, path="arguments"):
    """Validate the deliberately small JSON Schema subset used by this adapter."""
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "boolean": type(value) is bool,
             "integer": type(value) is int, "number": type(value) in (int, float)}
    if kind and not valid.get(kind, False):
        raise InterfaceError("invalid_type", f"{path}: expected {kind}", "Use the schema from describe.")
    if "enum" in schema and not any(type(value) is type(x) and value == x for x in schema["enum"]):
        raise InterfaceError("invalid_choice", f"{path}: unsupported value", f"Choose one of {schema['enum']}.")
    if kind == "object":
        extra = set(value) - set(schema["properties"])
        missing = set(schema["required"]) - set(value)
        if extra or missing:
            raise InterfaceError("invalid_fields", f"{path}: missing={sorted(missing)}, unknown={sorted(extra)}", "Use only the requested operation's fields.")
        for key, item in value.items():
            validate(item, schema["properties"][key], f"{path}.{key}")
    elif kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100000):
            raise InterfaceError("invalid_size", f"{path}: invalid item count", "Use a bounded, nonempty model bundle.")
        if schema.get("uniqueItems") and len({repr(x) for x in value}) != len(value):
            raise InterfaceError("duplicate_input", f"{path}: repeated item", "Supply each item once.")
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{i}]")
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value.strip()) <= schema.get("maxLength", 4096) or "\0" in value:
            raise InterfaceError("invalid_text", f"{path}: empty, oversized or NUL text", "Supply concise nonempty text.")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise InterfaceError("invalid_format", f"{path}: invalid format", "Use the format from describe.")
    elif kind in ("integer", "number"):
        if isinstance(value, float) and not math.isfinite(value):
            raise InterfaceError("invalid_number", f"{path}: nonfinite number", "Supply a finite value.")
        if not schema.get("minimum", float("-inf")) <= value <= schema.get("maximum", float("inf")):
            raise InterfaceError("invalid_range", f"{path}: value out of range", "Respect the declared bounds.")


def discover():
    return {"version": "cse-interface-1", "operations": {name: op["summary"] for name, op in OPERATIONS.items()},
            "next": "describe OPERATION", "elicitation": "elicit --state FILE; domain questions only"}


def describe(name):
    if name not in OPERATIONS:
        raise InterfaceError("unknown_operation", f"Unknown operation: {name}", "Run discover.")
    op = OPERATIONS[name]
    return {"operation": name, "description": op["summary"], "inputSchema": op["schema"],
            "guide": str(ROOT / op["guide"]), "readOnly": True}


def command(name, arguments):
    describe(name)
    validate(arguments, OPERATIONS[name]["schema"])
    # File suffix is admission, not syntax validation. The native parser is authoritative.
    groups = ("before", "after") if name == "diff" else ("models",)
    normalized = dict(arguments)
    for group in groups:
        paths = [Path(p).resolve() for p in arguments[group]]
        if len(paths) != len(set(paths)):
            raise InterfaceError("duplicate_input", "Model paths resolve to the same file", "Supply each source once.")
        for path in paths:
            if path.suffix.lower() != ".sysml":
                raise InterfaceError("unsupported_format", f"Unsupported input format: {path.suffix or '(none)'}", "Use native tooling for this format; provide an explicit SysML v2 export for CSE. Migration requires a fidelity review.")
            if not path.is_file():
                raise InterfaceError("missing_file", f"Model not found: {path}", "Correct the path or supply the missing bundle member.")
        normalized[group] = [str(p) for p in paths]
    a = normalized
    argv = [str(ROOT / "scripts" / OPERATIONS[name]["script"])]
    if name == "diff":
        for group in groups:
            for path in a[group]:
                argv += ["--" + group, path]
    else:
        argv += a["models"]
        if name == "inspect":
            argv += ["--id", a["id"]]
        else:
            argv += ["--json"]
            if name == "validate":
                if a["mode"] == "review" and not all(a.get(x) for x in ("manifest", "evidence")):
                    raise InterfaceError("review_inputs_missing", "Review requires independent manifest and supplied evidence", "Supply both inputs or use syntax/compile; neither establishes a behavior review.")
                if a["mode"] != "review" and any(x in a for x in ("manifest", "evidence")):
                    raise InterfaceError("unused_evidence", "Evidence inputs would not be reviewed in this mode", "Use mode=review to evaluate supplied evidence.")
                if a["mode"] == "syntax":
                    argv += ["--syntax-only"]
                elif a["mode"] == "review":
                    argv += ["--review"]
            for key in ("kind", "manifest", "evidence", "max_rows", "evaluation_cap"):
                if key in a:
                    if key in ("manifest", "evidence"):
                        path = Path(a[key]).resolve()
                        if not path.is_file():
                            raise InterfaceError("missing_file", f"Missing {key}: {path}", "Provide the existing independent input; do not fabricate evidence.")
                        value = str(path)
                    else:
                        value = str(a[key])
                    argv += ["--" + key.replace("_", "-"), value]
    return argv
