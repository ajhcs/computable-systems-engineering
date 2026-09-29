#!/usr/bin/env python3
"""Small, dependency-free checks and views for a version-1 concept record."""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path


GROUPS = ("needs", "functions", "criteria", "concepts", "operations", "decisions")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")
FINDINGS = ("supported", "contradicted", "unknown", "deferred")
EVIDENCE = ("assumption", "analysis", "test", "observation", "source", "unknown")
DECISIONS = ("proposed", "accepted", "deferred", "superseded")
FRAME = dict.fromkeys(("name", "problem", "current_state", "desired_outcome", "boundary", "context", "timeframe", "basis"), str)
EVALUATION = dict.fromkeys(("method", "data", "environment"), str)
ASSESSMENT = {"finding": ("enum", FINDINGS), "evidence": ("enum", EVIDENCE), "basis": str, "next_check": str}
SCHEMA = {
    "version": int,
    "framing": FRAME,
    "needs": ("map", {"text": str, "stakeholder": str, "basis": str}),
    "functions": ("map", {"text": str, "needs": [str], "inputs": [str], "outputs": [str]}),
    "criteria": ("map", {"text": str, "kind": ("enum", ("constraint", "goal")), "needs": [str], "basis": str, "measure": str}),
    "concepts": ("map", {
        "summary": str, "functions": [str], "allocations": [{"function": str, "element": str}],
        "operations": [str], "assumptions": [str], "assessments": ("map", ASSESSMENT),
        "evaluation": EVALUATION, "comparison": str,
    }),
    "operations": ("map", {"path": str, "ids": [str], "sha256": str}),
    "decisions": ("map", {"text": str, "status": ("enum", DECISIONS), "by": str, "basis": str, "affects": [str]}),
    "questions": [{"text": str, "affects": [str], "blocking": bool}],
}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"nonfinite JSON number: {value}")


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        reject_constant(value)
    return number


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=pairs, parse_constant=reject_constant, parse_float=finite_float)


def fingerprint(record):
    raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def shape(value, schema, path, errors):
    if isinstance(schema, type):
        if type(value) is not schema:
            errors.append(f"{path}: expected {schema.__name__}")
    elif isinstance(schema, dict):
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return
        for key, child in value.items():
            if key == "extra":
                if not isinstance(child, dict):
                    errors.append(f"{path}.extra: expected object")
            elif key not in schema:
                errors.append(f"{path}.{key}: unexpected field")
            else:
                shape(child, schema[key], f"{path}.{key}", errors)
    elif isinstance(schema, list):
        if not isinstance(value, list):
            errors.append(f"{path}: expected list")
            return
        for index, child in enumerate(value):
            shape(child, schema[0], f"{path}[{index}]", errors)
    elif schema[0] == "map":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected ID map")
            return
        for key, child in value.items():
            shape(child, schema[1], f"{path}.{key}", errors)
    elif type(value) is not str or value not in schema[1]:
        errors.append(f"{path}: expected one of {', '.join(schema[1])}")


def structural(record):
    errors = []
    shape(record, SCHEMA, "record", errors)
    if errors:
        return errors
    if record.get("version") != 1:
        errors.append("record.version: expected 1")
    ids = {"framing"}
    for group in GROUPS:
        for key in record.get(group, {}):
            if not ID.fullmatch(key):
                errors.append(f"{group}.{key}: invalid ID")
            if key in ids:
                errors.append(f"{group}.{key}: duplicate or reserved ID")
            ids.add(key)

    def refs(values, valid, path):
        for value in values:
            if value not in valid:
                errors.append(f"{path}: unknown reference {value!r}")
        if len(values) != len(set(values)):
            errors.append(f"{path}: duplicate references")

    for group in ("functions", "criteria"):
        for key, item in record.get(group, {}).items():
            refs(item.get("needs", []), record.get("needs", {}), f"{group}.{key}.needs")
    for key, item in record.get("concepts", {}).items():
        refs(item.get("functions", []), record.get("functions", {}), f"concepts.{key}.functions")
        refs(item.get("operations", []), record.get("operations", {}), f"concepts.{key}.operations")
        refs(list(item.get("assessments", {})), record.get("criteria", {}), f"concepts.{key}.assessments")
        for index, allocation in enumerate(item.get("allocations", [])):
            if "function" in allocation:
                refs([allocation["function"]], item.get("functions", []), f"concepts.{key}.allocations[{index}]")
    for key, item in record.get("decisions", {}).items():
        refs(item.get("affects", []), ids, f"decisions.{key}.affects")
    for index, item in enumerate(record.get("questions", [])):
        refs(item.get("affects", []), ids, f"questions[{index}].affects")
    for key, item in record.get("operations", {}).items():
        if item.get("sha256") and not HEX.fullmatch(item["sha256"]):
            errors.append(f"operations.{key}.sha256: expected lowercase SHA-256")
        if len(item.get("ids", [])) != len(set(item.get("ids", []))):
            errors.append(f"operations.{key}.ids: duplicate references")
    return errors


def index(record):
    return {key: (group, item) for group in GROUPS for key, item in record.get(group, {}).items()}


def applicable_criteria(record, concept):
    needs = {need for ref in concept.get("functions", []) for need in record.get("functions", {}).get(ref, {}).get("needs", [])}
    return {key for key, item in record.get("criteria", {}).items() if not item.get("needs") or needs.intersection(item["needs"])}


def graph(record):
    result = {"framing": set()}
    for key, (group, item) in index(record).items():
        refs = set()
        if group in ("functions", "criteria"):
            refs.update(item.get("needs", []))
        elif group == "concepts":
            refs.update(item.get("functions", []))
            refs.update(item.get("operations", []))
            refs.update(item.get("assessments", {}))
            refs.update(applicable_criteria(record, item))
        elif group == "decisions":
            refs.update(item.get("affects", []))
        result[key] = refs | {"framing"}
    return result


def closure(selected, edges):
    result = set(selected)
    pending = list(selected)
    while pending:
        for ref in edges.get(pending.pop(), set()) - result:
            result.add(ref)
            pending.append(ref)
    return result


def relevant(affects, selected):
    return not affects or "framing" in affects or bool(set(affects) & selected)


def selection(record, requested):
    selected = closure(requested, graph(record)) if requested else set(index(record)) | {"framing"}
    while True:
        more = {key for key, item in record.get("decisions", {}).items() if relevant(item.get("affects", []), selected)} - selected
        if not more:
            break
        selected.update(more)
    return selected


def operation_status(item, base):
    if not item.get("path"):
        return {"status": "unknown", "detail": "missing path"}
    try:
        linked = read(base / item["path"])
        if not isinstance(linked, dict) or type(linked.get("version")) is not int or linked["version"] != 1:
            return {"status": "invalid", "detail": "expected a version-1 operational record"}
        linked_ids = set()
        for group in ("actors", "needs", "scenarios", "criteria"):
            records = linked.get(group, {})
            if not isinstance(records, dict):
                return {"status": "invalid", "detail": f"{group} is not an ID map"}
            linked_ids.update(records)
        missing = sorted(set(item.get("ids", [])) - linked_ids)
        actual = fingerprint(linked)
        if missing:
            return {"status": "missing_ids", "ids": missing, "actual_sha256": actual}
        if not item.get("sha256"):
            return {"status": "unpinned", "actual_sha256": actual}
        return {"status": "current" if item["sha256"] == actual else "stale", "actual_sha256": actual}
    except (OSError, ValueError, RecursionError) as exc:
        return {"status": "unavailable", "detail": str(exc)}


def review(record, selected, focused, base):
    gaps, findings, concerns = [], [], []

    def need(item, fields, path):
        for field in fields:
            value = item.get(field)
            blank_list = isinstance(value, list) and (not value or any(isinstance(entry, str) and not entry.strip() for entry in value))
            if value is None or (isinstance(value, str) and not value.strip()) or blank_list:
                gaps.append(f"{path}.{field}: missing or empty")

    need(record.get("framing", {}), FRAME, "framing")
    records = index(record)
    for key in sorted(selected - {"framing"}):
        group, item = records[key]
        path = f"{group}.{key}"
        if group == "needs":
            need(item, ("text", "stakeholder", "basis"), path)
        elif group == "functions":
            need(item, ("text", "needs", "inputs", "outputs"), path)
        elif group == "criteria":
            need(item, ("text", "kind", "basis", "measure"), path)
        elif group == "concepts":
            need(item, ("summary", "functions", "comparison"), path)
            need(item.get("evaluation", {}), EVALUATION, f"{path}.evaluation")
            for number, allocation in enumerate(item.get("allocations", [])):
                need(allocation, ("function", "element"), f"{path}.allocations[{number}]")
            assessments = item.get("assessments", {})
            if not assessments:
                gaps.append(f"{path}.assessments: no criterion assessment recorded")
            expected = applicable_criteria(record, item) if focused else set(record.get("criteria", {}))
            for criterion in sorted(expected - set(assessments)):
                gaps.append(f"{path}.assessments: missing applicable criterion {criterion}")
            for criterion, assessment in assessments.items():
                need(assessment, ("finding", "evidence", "basis"), f"{path}.assessments.{criterion}")
                finding, evidence = assessment.get("finding"), assessment.get("evidence")
                findings.append({"concept": key, "criterion": criterion, "finding": finding, "evidence": evidence})
                if finding in ("unknown", "deferred") or evidence in ("assumption", "unknown"):
                    need(assessment, ("next_check",), f"{path}.assessments.{criterion}")
                if finding == "contradicted" and record["criteria"][criterion].get("kind") == "constraint":
                    concerns.append(f"{key}: declared contradiction of constraint {criterion}")
                if finding == "supported" and evidence in ("assumption", "unknown"):
                    concerns.append(f"{key}/{criterion}: support rests on {evidence}, not independently established evidence")
        elif group == "decisions":
            need(item, ("text", "status", "basis"), path)
            if item.get("status") == "accepted":
                need(item, ("by",), path)
    for number, question in enumerate(record.get("questions", [])):
        if relevant(question.get("affects", []), selected):
            need(question, ("text",), f"questions[{number}]")
            if question.get("blocking"):
                gaps.append(f"questions[{number}]: blocking question: {question.get('text', '')}")
    if not focused:
        for group in ("needs", "functions", "criteria", "concepts"):
            if not record.get(group):
                gaps.append(f"{group}: no records")
        used_needs = {ref for item in record.get("functions", {}).values() for ref in item.get("needs", [])}
        for key in sorted(set(record.get("needs", {})) - used_needs):
            gaps.append(f"needs.{key}: no linked function")
    links = {}
    for key in sorted(selected & set(record.get("operations", {}))):
        links[key] = operation_status(record["operations"][key], base)
        if links[key]["status"] != "current":
            gaps.append(f"operations.{key}: {links[key]['status']}")
    return gaps, findings, concerns, links


def check(record, base, requested=(), require_review=False):
    errors = structural(record)
    if not errors:
        errors.extend(f"concepts: unknown requested concept {key!r}" for key in requested if key not in record.get("concepts", {}))
    gaps, findings, concerns, links = [], [], [], {}
    if not errors:
        selected = selection(record, requested)
        gaps, findings, concerns, links = review(record, selected, bool(requested), base)
    report = {
        "structural": "fail" if errors else "pass",
        "review_scope": {"concepts": list(requested)} if requested else "whole_record",
        "review_gaps": gaps, "errors": errors, "declared_findings": findings,
        "concerns": concerns, "operation_links": links,
        "feasibility": "not_independently_evaluated", "semantic_validation": "not_evaluated",
        "implementation": "not_evaluated", "decision_authenticity": "not_evaluated",
    }
    if not errors:
        report["model_sha256"] = fingerprint(record)
    if require_review:
        report["review_completeness"] = "fail" if gaps or errors else "pass"
    return report, 1 if errors or (require_review and gaps) else 0


def view(record, requested):
    records = index(record)
    if not requested:
        return {"framing": record.get("framing", {}), "inventory": {group: list(record.get(group, {})) for group in GROUPS}}
    unknown = set(requested) - set(records) - {"framing"}
    if unknown:
        raise ValueError(f"unknown IDs: {', '.join(sorted(unknown))}")
    selected = closure(requested, graph(record))
    result = {"version": 1, "framing": record.get("framing", {})}
    for group in GROUPS:
        items = {key: item for key, item in record.get(group, {}).items() if key in selected}
        if items:
            result[group] = items
    expanded = selection(record, requested)
    related = {key: item for key, item in record.get("decisions", {}).items() if key not in selected and key in expanded}
    selected.update(related)
    result["questions"] = [q for q in record.get("questions", []) if relevant(q.get("affects", []), selected)]
    return {"requested": list(requested), "record": result, "related_decisions": related}


def diff(old, new):
    def flatten(record):
        return {"framing": record.get("framing", {}), **{key: {"group": group, "record": item} for key, (group, item) in index(record).items()}}

    before, after = flatten(old), flatten(new)
    added, removed = set(after) - set(before), set(before) - set(after)
    changed = {key for key in set(before) & set(after) if before[key] != after[key]}
    affected = changed | added | removed
    edges = graph(old)
    for key, refs in graph(new).items():
        edges.setdefault(key, set()).update(refs)
    while True:
        more = {key for key, refs in edges.items() if refs & affected} - affected
        if not more:
            break
        affected.update(more)
    other = [key for key in ("version", "questions", "extra") if old.get(key) != new.get(key)]
    return {"added": sorted(added), "removed": sorted(removed), "changed": sorted(changed),
            "affected_dependents": sorted(affected - changed - added - removed), "other_changes": other,
            "external_artifacts": "not_compared; run check for linked content drift",
            "reconsider_evidence": fingerprint(old) != fingerprint(new)}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "check", "view"):
        sub = commands.add_parser(command)
        sub.add_argument("record", type=Path)
        if command == "check":
            sub.add_argument("--concept", action="append", default=[])
            sub.add_argument("--review", action="store_true")
        elif command == "view":
            sub.add_argument("ids", nargs="*")
    sub = commands.add_parser("diff")
    sub.add_argument("old", type=Path)
    sub.add_argument("new", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            with args.record.open("x", encoding="utf-8") as target:
                json.dump({"version": 1, "framing": {key: "" for key in FRAME}}, target, indent=2)
                target.write("\n")
            result, code = {"created": str(args.record), "state": "incomplete_draft"}, 0
        elif args.command == "diff":
            old, new = read(args.old), read(args.new)
            errors = structural(old) + structural(new)
            result, code = ({"errors": errors}, 1) if errors else (diff(old, new), 0)
        else:
            record = read(args.record)
            if args.command == "check":
                result, code = check(record, args.record.parent, args.concept, args.review)
            else:
                errors = structural(record)
                result, code = ({"errors": errors}, 1) if errors else (view(record, args.ids), 0)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
        return code
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
