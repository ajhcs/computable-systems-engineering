"""SysML v2 pilot adapter for the bounded CSE controlled-text profile.

The SysML file remains authoritative. The dictionaries assembled here are temporary
compiler inputs for the existing deterministic language checker.
"""

from hashlib import sha256
import fcntl
import json
import math
from pathlib import Path
import re
import subprocess
import time

from .language import LanguageError, _clock, check_document
from .events import EventError, _quantity, check_event_trace, parse_event_clause
from .influence import generate_influence_tests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "sysml"
JAR = CACHE / "pilot-2025-09" / "sysml" / "jupyter-sysml-kernel-0.52.0-all.jar"
LIBRARY = CACHE / "pilot-2025-09" / "sysml" / "sysml.library"
CLASSES = CACHE / "classes"
BRIDGE_SOURCE = ROOT / "tools" / "sysml" / "SysmlBridge.java"
BRIDGE_STAMP = CLASSES / "SysmlBridge.source.sha256"
PARSER = "OMG SysML v2 Pilot 2025-09 / kernel 0.52.0"
VERSION = "sysml-2.0-alpha.2"
ID = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
SOURCE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
CLOCK = re.compile(r"period ([0-9]+(?:\.[0-9]+)?) (millisecond|second|minute)s?\Z")
INTEGER_TYPE = re.compile(
    r"range (?P<min>-?(?:0|[1-9][0-9]*)) (?P<max>-?(?:0|[1-9][0-9]*)) "
    r"scale (?P<scale>(?:0|[1-9][0-9]*)(?:\.[0-9]+)?) "
    r"unit (?P<unit>[A-Za-z][A-Za-z0-9_]*)\Z"
)
QUANTITY_UNITS = {
    "ISQBase::DurationValue": {"millisecond", "milliseconds", "second", "seconds", "minute", "minutes"},
    "ISQBase::LengthValue": {"millimeter", "millimeters", "meter", "meters", "kilometer", "kilometers"},
}


class UnsupportedFeature(ValueError):
    """Valid SysML content outside the executable CSE profile."""


def _problem(report, code, detail, *, status="error", line=None, source=None, owner=None):
    item = {"code": code, "detail": detail}
    if line is not None:
        item["line"] = line
    if source is not None:
        item["source"] = source
    if owner is not None:
        item["owner"] = owner
    report["findings"].append(item)
    if {"pass": 0, "unsupported": 1, "unknown": 2, "fail": 3, "error": 4}[status] > {"pass": 0, "unsupported": 1, "unknown": 2, "fail": 3, "error": 4}[report["status"]]:
        report["status"] = status


def _block(document, marker):
    lines = document["body"].strip().splitlines()
    if not lines or lines[0].strip() != marker:
        raise ValueError(f"Expected {marker} header")
    content = " ".join(line.strip() for line in lines[1:] if line.strip())
    if not content:
        raise ValueError("Controlled documentation body is empty")
    return content


def _model_input(paths):
    """Build one parse unit and bind evidence to every contributing source byte."""
    if isinstance(paths, (str, Path)):
        paths = [Path(paths)]
    else:
        paths = [Path(path) for path in paths]
    if not paths or len(paths) > 128:
        raise ValueError("Supply between 1 and 128 SysML model files")
    canonical = [str(path.resolve()) for path in paths]
    if len(canonical) != len(set(canonical)):
        raise ValueError("Duplicate SysML model file")
    paths.sort(key=lambda path: str(path.resolve()))
    sources = []
    files = []
    line_ranges = []
    next_line = 1
    total_bytes = 0
    for path in paths:
        resolved = path.resolve()
        try:
            label = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            label = resolved.as_posix()
        raw = path.read_bytes()
        total_bytes += len(raw)
        if total_bytes > 5_000_000:
            raise ValueError("Combined SysML model exceeds 5 MB")
        source = raw.decode("utf-8")
        if not source.endswith("\n"):
            source += "\n"
        lines = source.count("\n")
        line_ranges.append((next_line, next_line + lines, label))
        next_line += lines + 1
        sources.append(source)
        files.append({"path": label, "sha256": sha256(raw).hexdigest()})
    if len(files) == 1:
        digest = files[0]["sha256"]
    else:
        digest = sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "\n".join(sources), files, line_ranges, digest


def _locate(line, line_ranges):
    if type(line) is not int or line < 1:
        return None, line
    for start, end, path in line_ranges:
        if start <= line < end:
            return path, line - start + 1
    return None, line


def _parser_output(source, timeout):
    if not JAR.is_file() or not LIBRARY.is_dir() or not (CLASSES / "SysmlBridge.class").is_file():
        raise RuntimeError("SysML pilot not installed; run python3 scripts/install_sysml_parser.py")
    if (not BRIDGE_STAMP.is_file() or
            BRIDGE_STAMP.read_text().strip() != sha256(BRIDGE_SOURCE.read_bytes()).hexdigest()):
        raise RuntimeError("SysML bridge source changed; rerun python3 scripts/install_sysml_parser.py")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0 or timeout > 600:
        raise ValueError("Parser timeout must be between 0 and 600 seconds")
    command = ["java", "-Xmx1200m", "-cp", f"{CLASSES}:{JAR}", "SysmlBridge",
               str(LIBRARY), "-"]
    CACHE.mkdir(parents=True, exist_ok=True)
    # The pilot may refresh a shared library index; serialize local parser runs.
    with (CACHE / "parser.lock").open("w") as lock:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        remaining = max(0.001, deadline - time.monotonic())
        completed = subprocess.run(command, input=source, capture_output=True, text=True, timeout=remaining,
                                   check=False)
    if completed.returncode:
        raise RuntimeError(f"SysML parser exited {completed.returncode}: {completed.stderr[-500:]}")
    try:
        data = json.loads(completed.stdout)
    except ValueError as exc:
        raise RuntimeError("SysML parser did not return a JSON result") from exc
    if not isinstance(data, dict):
        raise RuntimeError("SysML parser returned an invalid result")
    return data


def _manifest(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"version", "source_revision", "expected"} or type(value["version"]) is not int or value["version"] != 1 or not isinstance(value["source_revision"], str) or not value["source_revision"] or not isinstance(value["expected"], list):
        raise ValueError("Manifest needs version 1, source_revision, and expected entries")
    seen = set()
    labels = set()
    for entry in value["expected"]:
        if (not isinstance(entry, dict) or set(entry) != {"id", "constraint", "source"}
                or any(not isinstance(entry[key], str) or not (SOURCE_ID if key == "source" else ID).fullmatch(entry[key]) for key in entry)):
            raise ValueError("Each expected entry needs id, constraint, and source IDs")
        key = (entry["id"], entry["constraint"])
        label = entry["id"] + "__" + entry["constraint"]
        if key in seen or label in labels:
            raise ValueError("Duplicate or ambiguous expected obligation")
        seen.add(key)
        labels.add(label)
    return {(entry["id"], entry["constraint"]): entry for entry in value["expected"]}


def _evidence(value, model_digest):
    if value is None:
        return None
    allowed = {"model_sha256", "complete", "observations", "events", "observed_until"}
    if (not isinstance(value, dict) or set(value) - allowed or not {"model_sha256", "complete"} <= set(value)
            or value["model_sha256"] != model_digest or type(value["complete"]) is not bool
            or ("observations" in value and not isinstance(value["observations"], list))
            or ("events" in value and not isinstance(value["events"], list))
            or ("events" in value and "observed_until" not in value)):
        raise ValueError("Evidence is malformed or stale for this SysML model")
    return value


def check_sysml(path, *, manifest=None, evidence=None, review=False, syntax_only=False,
                kind=None, generate_tests=False, test_max_rows=16, test_evaluation_cap=2000,
                parser_timeout=60, observation_cap=10000, work_cap=1000000):
    """Parse one SysML file with the pinned pilot, then check supported clauses."""
    report = {"status": "pass", "checker_version": VERSION, "parser": PARSER, "claim_scope": "sysml_syntax_and_validation" if syntax_only else "supplied_behavior_evidence" if review else "sysml_and_controlled_text_compilation",
              "findings": [], "results": {}, "coverage": {"expected": [], "compiled": [], "unsupported": []}}
    report["limits"] = {"parser_timeout_seconds": parser_timeout, "observation_cap": observation_cap,
                        "per_clause_work_cap": work_cap}
    if generate_tests:
        report["test_generation"] = {"status": "unknown", "claim_scope": "synthetic_clause_local_influence_tests",
                                     "synthetic": True, "results": {}}
    try:
        if kind not in (None, "concept", "conops", "scenario"):
            raise ValueError("Unknown model kind")
        source, files, line_ranges, digest = _model_input(path)
        report["model_sha256"] = digest
        report["model_files"] = files
        expected = _manifest(manifest)
        if manifest is not None:
            report["source_revision"] = manifest["source_revision"]
            report["manifest_sha256"] = sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if review and syntax_only:
            raise ValueError("Syntax-only mode cannot be a required behavior review")
        if generate_tests and syntax_only:
            raise ValueError("Test generation needs controlled-clause compilation")
        if review and expected is None:
            _problem(report, "scope_missing", "Required review needs an independent manifest", status="unknown")
            return report
        observations = _evidence(evidence, report["model_sha256"])
        if evidence is not None:
            report["evidence_sha256"] = sha256(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        parsed = _parser_output(source, parser_timeout)
    except (OSError, UnicodeError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        _problem(report, "input_or_parser", str(exc))
        return report
    report["parser_issues"] = parsed.get("issues", [])
    for issue in report["parser_issues"]:
        issue["source"], issue["line"] = _locate(issue.get("line"), line_ranges)
    if parsed.get("error") or any(item.get("severity") == "ERROR" for item in report["parser_issues"]):
        _problem(report, "sysml_invalid", parsed.get("error") or "SysML parser or validator reported errors")
        return report
    record_groups = ("attributes", "events", "event_attributes", "parts", "part_definitions",
                     "concerns", "use_cases", "actions", "states", "requirements",
                     "constraints", "documents")
    if not all(isinstance(parsed.get(key), list) for key in record_groups):
        _problem(report, "parser_contract", "SysML adapter omitted required extracted records")
        return report
    for records in (parsed[key] for key in record_groups):
        for item in records:
            item["source"], item["line"] = _locate(item.get("line"), line_ranges)
    identified = {}
    for key in ("concerns", "use_cases", "requirements"):
        for item in parsed[key]:
            short_id = item.get("id")
            if not short_id:
                continue
            if not ID.fullmatch(short_id):
                _problem(report, "identity", f"Invalid short ID {short_id}", line=item.get("line"), source=item.get("source"))
            elif short_id in identified:
                _problem(report, "identity", f"Duplicate short ID {short_id}", line=item.get("line"), source=item.get("source"))
            else:
                identified[short_id] = item["qualified_name"]
    report["shape"] = {"part_definitions": len(parsed["part_definitions"]),
                       "concerns": len(parsed["concerns"]),
                       "use_cases": len(parsed["use_cases"]),
                       "actions": len(parsed["actions"]),
                       "states": len(parsed["states"])}
    if kind:
        report["shape"]["kind"] = kind
        needed = ("part_definitions", "concerns") if kind == "concept" else ("use_cases", "parts")
        for category in needed:
            count = len(parsed[category])
            report["shape"][category] = count
            if not count:
                _problem(report, "shape_gap", f"{kind} draft has no {category.replace('_', ' ')}", status="unknown")
        if syntax_only:
            report["claim_scope"] = f"sysml_syntax_and_{kind}_shape"
    if syntax_only:
        report["inventory"] = {key: parsed[key] for key in
                               ("part_definitions", "parts", "concerns", "use_cases", "actions", "states",
                                "requirements", "constraints", "attributes", "events",
                                "event_attributes", "documents")}
        return report

    documents = parsed["documents"]
    clock_docs = [item for item in documents if item.get("name") == "cseClock"]
    if len(clock_docs) != 1 or clock_docs[0].get("owner_kind") != "Package":
        _problem(report, "clock", "Exactly one package-owned cseClock block is required")
        return report
    try:
        period = _block(clock_docs[0], "CSE-CLOCK/2.0")
    except ValueError as exc:
        _problem(report, "clock", str(exc), line=clock_docs[0].get("line"), source=clock_docs[0].get("source"))
        return report
    clock_match = CLOCK.fullmatch(period)
    if not clock_match:
        _problem(report, "clock", "Clock must be 'period NUMBER UNIT'", line=clock_docs[0].get("line"), source=clock_docs[0].get("source"))
        return report
    clock = {"period": clock_match.group(1), "unit": clock_match.group(2)}
    try:
        _clock(clock)
    except LanguageError as exc:
        _problem(report, "clock", str(exc), line=clock_docs[0].get("line"), source=clock_docs[0].get("source"))
        return report

    reqs = {item["qualified_name"]: item for item in parsed["requirements"]
            if item.get("kind") == "RequirementUsage"}
    parts = {item["qualified_name"]: item for item in parsed["parts"]}
    part_definitions = {item["qualified_name"]: item for item in parsed["part_definitions"]}
    attributes = parsed["attributes"]
    events = parsed["events"]
    event_attributes = parsed["event_attributes"]
    constraints = {item["qualified_name"]: item for item in parsed["constraints"]}
    controlled_docs = {}
    source_docs = {}
    type_docs = {}
    for document in documents:
        name = document.get("name")
        if name == "cse":
            owner = document.get("owner")
            if document.get("owner_kind") != "ConstraintUsage" or owner in controlled_docs:
                _problem(report, "controlled_owner", "cse must uniquely belong to a constraint", line=document.get("line"), source=document.get("source"))
                return report
            controlled_docs[owner] = document
        elif name == "cseSource":
            owner = document.get("owner")
            if document.get("owner_kind") != "RequirementUsage" or owner in source_docs:
                _problem(report, "source_owner", "cseSource must uniquely belong to a requirement", line=document.get("line"), source=document.get("source"))
                return report
            try:
                source_docs[owner] = _block(document, "CSE-SOURCE/2.0")
            except ValueError as exc:
                _problem(report, "source", str(exc), line=document.get("line"), source=document.get("source"))
                return report
        elif name == "cseType":
            owner = document.get("owner")
            if document.get("owner_kind") != "AttributeUsage" or owner in type_docs:
                _problem(report, "type_owner", "cseType must uniquely belong to an attribute",
                         line=document.get("line"), source=document.get("source"))
                return report
            type_docs[owner] = document

    found = set()
    found_labels = set()
    known_evidence_fields = {
        part["qualified_name"] + "::" + attribute["name"]
        for part in parsed["parts"] for attribute in attributes
        if part.get("type") == attribute.get("part_definition") and attribute.get("name")
    }
    known_event_paths = {
        part["qualified_name"] + "::" + event["name"]
        for part in parsed["parts"] for event in events
        if part.get("type") == event.get("part_definition") and event.get("name")
    }
    event_fields = {
        part["qualified_name"] + "::" + event["name"]:
        {attribute["name"]: attribute.get("type") for attribute in event_attributes
         if attribute.get("event") == event.get("qualified_name")}
        for part in parsed["parts"] for event in events
        if part.get("type") == event.get("part_definition") and event.get("name")
    }
    for constraint in parsed["constraints"]:
        if constraint.get("membership_kind") == "AssumedConstraintMembership" and constraint.get("requirement") in reqs:
            _problem(report, "unsupported_assumption", "Assumed constraints are not yet included in trace semantics",
                     status="unsupported", owner=constraint.get("qualified_name"))
        elif constraint.get("membership_kind") != "RequirementConstraintMembership" and constraint.get("has_native_expression"):
            _problem(report, "unsupported_native_constraint", "Native SysML constraint computation is not implemented",
                     status="unsupported", owner=constraint.get("qualified_name"),
                     line=constraint.get("line"), source=constraint.get("source"))
    for constraint in parsed["constraints"]:
        if constraint.get("membership_kind") != "RequirementConstraintMembership":
            continue
        owner = constraint.get("requirement")
        if owner not in reqs:
            _problem(report, "requirement", "Required constraint has no owning requirement", owner=constraint.get("qualified_name"))
            continue
        requirement = reqs[owner]
        rid, cid = requirement.get("id"), constraint.get("name")
        if not rid or not cid or not ID.fullmatch(rid) or not ID.fullmatch(cid):
            _problem(report, "identity", "Requirement short ID and constraint name are required", owner=owner)
            continue
        identity = (rid, cid)
        key = rid + "__" + cid
        if identity in found or key in found_labels:
            _problem(report, "identity", f"Duplicate or ambiguous obligation {key}")
            continue
        found.add(identity)
        found_labels.add(key)
        document = controlled_docs.get(constraint["qualified_name"])
        if document is None:
            report["coverage"]["unsupported"].append(key)
            _problem(report, "unsupported_constraint", f"No supported CSE clause for {key}", status="unsupported")
            continue
        if constraint.get("has_native_expression"):
            _problem(report, "dual_authority", f"{key} has both a native expression and CSE text")
            continue
        if expected is not None and identity not in expected:
            _problem(report, "unclassified_obligation", f"{key} is absent from the independent manifest", status="unknown")
        try:
            header = document["body"].strip().splitlines()[0].strip()
            if header not in ("CSE-REQ/2.0", "CSE-EVENT/2.0"):
                raise ValueError(f"Unsupported controlled profile header: {header}")
            clause = _block(document, header)
            source = source_docs.get(owner)
            if not source or not SOURCE_ID.fullmatch(source):
                raise ValueError(f"{key} needs a valid cseSource ID")
            if expected is not None and identity in expected and source != expected[identity]["source"]:
                raise ValueError(f"{key} source ID does not match the independent manifest")
            subjects = requirement.get("subjects", [])
            if len(subjects) != 1 or not subjects[0].get("target"):
                raise ValueError(f"{key} needs exactly one bound subject")
            alias, target = subjects[0]["name"], subjects[0]["target"]
            part = parts.get(target)
            if part is None or not part.get("type"):
                raise ValueError(f"{key} subject does not resolve to a typed part")
            definition = part_definitions.get(part["type"], {})
            if (requirement.get("has_specialization") or definition.get("has_specialization") or
                    part.get("has_non_typing_specialization") or part.get("has_native_value")):
                raise UnsupportedFeature(f"{key} depends on inheritance, specialization, or a native subject value that is not computed")
            if header == "CSE-EVENT/2.0":
                event_clause = parse_event_clause(clause)
                if event_clause["subject"] != alias:
                    raise ValueError(f"{key} event subject does not match the bound SysML subject")
                selected = {item["name"]: item for item in events
                            if item.get("part_definition") == part["type"]}
                trigger = selected.get(event_clause["trigger"])
                response = selected.get(event_clause["response"])
                if not trigger or not response or trigger.get("direction") != "in" or response.get("direction") != "out":
                    raise ValueError(f"{key} needs declared in/out event occurrences")
                if trigger.get("has_non_typing_specialization") or response.get("has_non_typing_specialization"):
                    raise UnsupportedFeature(f"{key} uses specialized event declarations that are not computed")
                correlation = event_clause["correlation"]
                for event in (trigger, response):
                    fields = [item for item in event_attributes if item.get("event") == event["qualified_name"] and item.get("name") == correlation]
                    if len(fields) != 1:
                        raise ValueError(f"{key} needs one {correlation} attribute on both events")
                    if fields[0].get("type") != "ScalarValues::String":
                        raise UnsupportedFeature(f"{key} correlation type is not yet supported")
                    if fields[0].get("has_native_value") or fields[0].get("has_non_typing_specialization"):
                        raise UnsupportedFeature(f"{key} correlation field has a native value or specialization that is not computed")
                trigger_path = target + "::" + trigger["name"]
                response_path = target + "::" + response["name"]
                if not review:
                    checked = {"status": "pass", "claim_scope": "event_clause_compilation"}
                elif observations is None or "events" not in observations:
                    checked = {"status": "unknown", "reason": "No event evidence supplied"}
                else:
                    selected_evidence = dict(observations)
                    selected_evidence["events"] = [item for item in observations.get("events", [])
                                                   if isinstance(item, dict) and item.get("event") in (trigger_path, response_path)]
                    checked = check_event_trace(event_clause, selected_evidence,
                                                trigger_path=trigger_path, response_path=response_path,
                                                event_cap=observation_cap)
                    checked["claim_scope"] = "correlated_event_trace"
                report["results"][key] = {"source": source, "sysml_source": document.get("source"),
                                          "sysml_line": document.get("line"),
                                          "binding": {event_clause["subject"] + "." + trigger["name"]: trigger_path,
                                                      event_clause["subject"] + "." + response["name"]: response_path},
                                          "compiled_clause": clause, "deadline_ms": str(event_clause["duration_ms"]),
                                          "check": checked}
                if generate_tests:
                    report["test_generation"]["results"][key] = {
                        "status": "unsupported", "source": source,
                        "reason": "Correlated-event influence generation is not implemented"}
                report["coverage"]["compiled"].append(key)
                if checked["status"] == "fail":
                    _problem(report, "event_failure", f"{key} failed", status="fail", line=document.get("line"), source=document.get("source"))
                elif checked["status"] == "unknown":
                    _problem(report, "event_unknown", f"{key} could not be completed", status="unknown", line=document.get("line"), source=document.get("source"))
                continue
            properties = {}
            binding = {}
            for attribute in attributes:
                if attribute.get("part_definition") != part["type"]:
                    continue
                if attribute.get("direction") not in ("in", "out"):
                    continue
                local = alias + "." + attribute["name"]
                owner_kind = "input" if attribute["direction"] == "in" else "controlled"
                attribute_type = attribute.get("type")
                if attribute_type == "ScalarValues::Boolean":
                    properties[local] = {"type": "bool", "owner": owner_kind}
                elif attribute_type in QUANTITY_UNITS and attribute["qualified_name"] in type_docs:
                    content = _block(type_docs[attribute["qualified_name"]], "CSE-INT/2.0")
                    match = INTEGER_TYPE.fullmatch(content)
                    if not match:
                        raise ValueError(f"Invalid CSE-INT/2.0 declaration on {attribute['qualified_name']}")
                    fields = match.groupdict()
                    if fields["unit"] not in QUANTITY_UNITS[attribute_type]:
                        raise ValueError(f"Quantity unit does not match {attribute_type}: {fields['unit']}")
                    properties[local] = {"type": "int", "owner": owner_kind,
                                         "min": int(fields["min"]), "max": int(fields["max"]),
                                         "scale": fields["scale"], "unit": fields["unit"]}
                else:
                    continue
                binding[local] = target + "::" + attribute["name"]
            if not properties:
                raise UnsupportedFeature(f"{key} has no supported subject attributes")
            declared_names = {alias + "." + attribute["name"] for attribute in attributes
                              if attribute.get("part_definition") == part["type"] and attribute.get("name")}
            mentioned_names = set(re.findall(rf"\b{re.escape(alias)}\.[A-Za-z][A-Za-z0-9_]*\b", clause))
            unsupported_names = sorted((mentioned_names & declared_names) - set(properties))
            if unsupported_names:
                raise UnsupportedFeature(f"{key} references unsupported declared attributes: {', '.join(unsupported_names)}")
            modified_names = sorted(alias + "." + attribute["name"] for attribute in attributes
                                    if attribute.get("part_definition") == part["type"] and
                                    (attribute.get("has_native_value") or attribute.get("has_non_typing_specialization")) and
                                    alias + "." + attribute["name"] in mentioned_names)
            if modified_names:
                raise UnsupportedFeature(f"{key} references native values or specialized attributes that are not computed: {', '.join(modified_names)}")
            rows = None
            if observations is not None and "observations" in observations:
                rows = []
                for row in observations["observations"]:
                    if not isinstance(row, dict):
                        raise ValueError("Evidence row must be a map")
                    rows.append({local: row[physical] for local, physical in binding.items() if physical in row})
            candidate = {"language_version": 1, "clock": clock, "actors": {alias: {}},
                         "properties": properties, "requirements": {key: clause}}
            if rows is not None:
                candidate["observations"] = rows
                candidate["complete"] = observations["complete"]
            checked = check_document(candidate, review=review, observation_cap=observation_cap,
                                     work_cap=work_cap,
                                     expected={"version": 1, "required": [key]} if expected is not None else None)
            report["results"][key] = {"source": source, "sysml_source": document.get("source"),
                                      "sysml_line": document.get("line"),
                                      "binding": binding, "compiled_clause": clause,
                                      "check": checked}
            if checked["status"] == "error":
                _problem(report, "controlled_clause", f"{key}: {checked['error']['detail']}", line=document.get("line"), source=document.get("source"))
            else:
                report["coverage"]["compiled"].append(key)
                if generate_tests:
                    generated = generate_influence_tests(candidate, key, max_rows=test_max_rows,
                                                         evaluation_cap=test_evaluation_cap)
                    generated.update({"synthetic": True, "model_sha256": digest,
                                      "source": source, "sysml_source": document.get("source"),
                                      "sysml_line": document.get("line"), "binding": binding})
                    for entry in generated["variables"].values():
                        if entry["status"] == "witness":
                            for variant in ("pass_trace", "fail_trace"):
                                entry[variant] = [{binding[name]: value for name, value in row.items()}
                                                  for row in entry[variant]]
                    report["test_generation"]["results"][key] = generated
                if checked["status"] == "fail":
                    _problem(report, "trace_failure", f"{key} failed", status="fail", line=document.get("line"), source=document.get("source"))
                elif checked["status"] == "unknown":
                    _problem(report, "trace_unknown", f"{key} could not be completed", status="unknown", line=document.get("line"), source=document.get("source"))
        except UnsupportedFeature as exc:
            report["coverage"]["unsupported"].append(key)
            _problem(report, "unsupported_binding", str(exc), status="unsupported",
                     line=document.get("line"), source=document.get("source"))
        except (ValueError, EventError) as exc:
            _problem(report, "binding", str(exc), line=document.get("line"), source=document.get("source"))

    if expected is not None:
        report["coverage"]["expected"] = sorted(rid + "__" + cid for rid, cid in expected)
        for rid, cid in sorted(set(expected) - found):
            _problem(report, "missing_obligation", f"Expected {rid}__{cid} is absent from the model", status="unknown")
    else:
        report["coverage"]["expected"] = sorted(rid + "__" + cid for rid, cid in found)
    if not found:
        _problem(report, "empty", "No required constraints were found", status="unknown")
    for owner in sorted(set(controlled_docs) - {item["qualified_name"] for item in parsed["constraints"] if item.get("membership_kind") == "RequirementConstraintMembership"}):
        _problem(report, "unbound_controlled_text", f"Controlled text has no supported required-constraint owner: {owner}", status="unsupported")
    if observations is not None:
        if len(observations.get("observations", [])) > observation_cap or len(observations.get("events", [])) > observation_cap:
            _problem(report, "evidence_limit", "Evidence record cap exceeded", status="unknown")
        for index, row in enumerate(observations.get("observations", [])):
            if not isinstance(row, dict) or set(row) - known_evidence_fields:
                _problem(report, "evidence_fields", f"Observation {index} contains unknown fields")
                break
        prior_time = None
        horizon = observations.get("observed_until")
        try:
            if "events" in observations:
                if not isinstance(horizon, dict) or set(horizon) != {"time", "unit"}:
                    raise EventError("Event evidence needs observed_until")
                horizon_time = _quantity(horizon["time"], horizon["unit"])
            else:
                horizon_time = None
        except EventError as exc:
            _problem(report, "event_evidence", str(exc))
            horizon_time = None
        for index, item in enumerate(observations.get("events", [])):
            if not isinstance(item, dict) or item.get("event") not in known_event_paths:
                _problem(report, "event_binding", f"Event {index} has no declared event path")
                break
            path = item["event"]
            fields = event_fields[path]
            if not {"event", "time", "unit"} <= set(item) or set(item) - ({"event", "time", "unit"} | set(fields)):
                _problem(report, "event_evidence", f"Event {index} has missing or undeclared fields")
                break
            if any((typ == "ScalarValues::String" and not isinstance(item[name], str)) or
                   (typ == "ScalarValues::Boolean" and type(item[name]) is not bool)
                   for name, typ in fields.items() if name in item):
                _problem(report, "event_evidence", f"Event {index} payload has wrong type")
                break
            try:
                instant = _quantity(item["time"], item["unit"])
            except EventError as exc:
                _problem(report, "event_evidence", f"Event {index}: {exc}")
                break
            if (prior_time is not None and instant < prior_time) or (horizon_time is not None and instant > horizon_time):
                _problem(report, "event_evidence", f"Event {index} violates event time order or horizon")
                break
            prior_time = instant
    if generate_tests:
        results = report["test_generation"]["results"]
        states = [item["status"] for item in results.values()]
        report["test_generation"]["status"] = (
            "pass" if states and all(state == "pass" for state in states) and report["status"] == "pass"
            else "unsupported" if "unsupported" in states and report["status"] == "pass"
            else "unknown")
    return report
