"""Local CONOPS and focused scenario checks. Python 3.10+, standard library only."""
import argparse
import hashlib
import json
import math
import operator
import re
import sys
from pathlib import Path

GROUPS = ("actors", "needs", "scenarios", "criteria")
OPS = {"<": operator.lt, "<=": operator.le, "==": operator.eq,
       "!=": operator.ne, ">=": operator.ge, ">": operator.gt}
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_object, parse_constant=reject_constant)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def fingerprint(doc):
    encoded = json.dumps(doc, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def populated(value):
    return isinstance(value, str) and bool(value.strip())


def structural_errors(doc):
    errors = []

    def error(path, message):
        errors.append(f"{path}: {message}")

    def obj(value, path, fields=None):
        if not isinstance(value, dict):
            error(path, "expected object")
            return False
        if fields is not None:
            for key in sorted(set(value) - set(fields) - {"extra"}):
                error(path, f"unknown field {key}")
        if "extra" in value and not isinstance(value["extra"], dict):
            error(path + ".extra", "expected object")
        return True

    def text_fields(value, path, fields):
        for field in fields:
            if field in value and not isinstance(value[field], str):
                error(path + "." + field, "expected string")

    def text_list(value, path):
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            error(path, "expected list of strings")
            return False
        return True

    if not obj(doc, "record", {"version", "system", *GROUPS, "questions", "review_notes"}):
        return errors
    if type(doc.get("version")) is not int or doc.get("version") != 1:
        error("version", "expected integer 1")
    system = doc.get("system", {})
    if obj(system, "system", {"name", "purpose", "boundary"}):
        text_fields(system, "system", ("name", "purpose", "boundary"))
    containers = {}
    ids = {"system"}
    for group in GROUPS:
        values = doc.get(group, {})
        if not obj(values, group):
            values = {}
        containers[group] = values
        for key in values:
            if not IDENTIFIER.fullmatch(key):
                error(group, f"invalid ID {key!r}")
            if key in ids:
                error(group, f"duplicate or reserved ID {key}")
            ids.add(key)
    actors = containers["actors"]
    needs = containers["needs"]
    scenarios = containers["scenarios"]

    def reference(value, path, allowed):
        if not isinstance(value, str) or value not in allowed:
            error(path, f"unresolved reference {value!r}")

    for key, value in actors.items():
        if not populated(value):
            error("actors." + key, "expected nonempty actor description")
    for key, value in needs.items():
        path = "needs." + key
        if obj(value, path, {"text", "actor", "basis"}):
            text_fields(value, path, ("text", "actor", "basis"))
            if "actor" in value:
                reference(value["actor"], path + ".actor", actors)
    for key, value in scenarios.items():
        path = "scenarios." + key
        if not obj(value, path, {"need", "kind", "setting", "trigger", "steps",
                                "outcome", "assumptions", "evaluation"}):
            continue
        text_fields(value, path, ("need", "kind", "setting", "trigger", "outcome"))
        if "need" in value:
            reference(value["need"], path + ".need", needs)
        if "kind" in value and value["kind"] not in ("normal", "off_normal", "lifecycle"):
            error(path + ".kind", "expected normal, off_normal, or lifecycle")
        if "assumptions" in value:
            text_list(value["assumptions"], path + ".assumptions")
        evaluation = value.get("evaluation", {})
        if obj(evaluation, path + ".evaluation", {"method", "data", "environment"}):
            text_fields(evaluation, path + ".evaluation", ("method", "data", "environment"))
        steps = value.get("steps", [])
        if not isinstance(steps, list):
            error(path + ".steps", "expected list")
            continue
        for index, step in enumerate(steps):
            step_path = f"{path}.steps[{index}]"
            if not obj(step, step_path, {"from", "to", "exchange"}):
                continue
            text_fields(step, step_path, ("from", "to", "exchange"))
            for field in ("from", "to"):
                if field in step:
                    reference(step[field], step_path + "." + field, {"system", *actors})
            if "from" in step and "to" in step:
                if (step["from"] == "system") == (step["to"] == "system"):
                    error(step_path, "exchange must cross the system boundary; put context in setting")
    for key, value in containers["criteria"].items():
        path = "criteria." + key
        if not obj(value, path, {"scenario", "metric", "op", "value", "unit", "basis"}):
            continue
        text_fields(value, path, ("scenario", "metric", "op", "unit", "basis"))
        if "scenario" in value:
            reference(value["scenario"], path + ".scenario", scenarios)
        if "op" in value and (not isinstance(value["op"], str) or value["op"] not in OPS):
            error(path + ".op", "unsupported comparison")
        if "value" in value and not number(value["value"]):
            error(path + ".value", "expected finite number, not boolean")
    review_notes = doc.get("review_notes", {})
    if obj(review_notes, "review_notes", {"stakeholders", "off_normal", "lifecycle"}):
        text_fields(review_notes, "review_notes", ("stakeholders", "off_normal", "lifecycle"))
    questions = doc.get("questions", [])
    if not isinstance(questions, list):
        error("questions", "expected list")
    else:
        for index, value in enumerate(questions):
            path = f"questions[{index}]"
            if not obj(value, path, {"text", "affects", "blocking"}):
                continue
            text_fields(value, path, ("text",))
            if "blocking" in value and type(value["blocking"]) is not bool:
                error(path + ".blocking", "expected boolean")
            affected = value.get("affects", [])
            if text_list(affected, path + ".affects"):
                for ref in affected:
                    reference(ref, path + ".affects", ids)
    return errors


def scenario_record(doc, selected):
    """Select scenarios and dependencies without changing the original record."""
    if not selected:
        raise ValueError("Select at least one scenario")
    unknown = set(selected) - set(doc.get("scenarios", {}))
    if unknown:
        raise ValueError("Unknown scenario IDs: " + ", ".join(sorted(unknown)))
    focused = view(doc, selected)
    included = set(focused["records"])
    return {"version": doc["version"], "system": doc.get("system", {}),
            **{group: {key: value for key, value in doc.get(group, {}).items()
                       if key in included} for group in GROUPS},
            "questions": focused["questions"]}


def review_gaps(doc, selected=None):
    focused = selected is not None
    if focused:
        doc = scenario_record(doc, selected)
    gaps = []

    def required(value, path, fields):
        for field in fields:
            if not populated(value.get(field)):
                gaps.append(f"{path}.{field}: missing")

    required(doc.get("system", {}), "system", ("name", "purpose", "boundary"))
    for group in ("actors", "needs", "scenarios"):
        if not doc.get(group):
            gaps.append(f"{group}: no entries")
    needs = doc.get("needs", {})
    scenarios = doc.get("scenarios", {})
    kinds = {s.get("kind") for s in scenarios.values()}
    if not focused and "normal" not in kinds:
        gaps.append("scenarios: no normal-operation scenario")
    covered_needs = {s.get("need") for s in scenarios.values()}
    for key, value in needs.items():
        required(value, key, ("text", "actor", "basis"))
        if key not in covered_needs:
            gaps.append(f"{key}: no linked scenario")
    for key, value in scenarios.items():
        required(value, key, ("need", "kind", "setting", "trigger", "outcome"))
        steps = value.get("steps", [])
        if not any(s.get("to") == "system" for s in steps):
            gaps.append(f"{key}: no inbound exchange")
        if not any(s.get("from") == "system" for s in steps):
            gaps.append(f"{key}: no outbound exchange")
        for index, step in enumerate(steps):
            required(step, f"{key}.steps[{index}]", ("from", "to", "exchange"))
        required(value.get("evaluation", {}), key + ".evaluation", ("method", "data", "environment"))
    for key, value in doc.get("criteria", {}).items():
        required(value, key, ("scenario", "metric", "op", "unit", "basis"))
        if "value" not in value:
            gaps.append(f"{key}.value: missing")
    notes = doc.get("review_notes", {})
    if not focused and not populated(notes.get("stakeholders")):
        gaps.append("review_notes.stakeholders: coverage or scope rationale missing")
    for kind in ("off_normal", "lifecycle"):
        if not focused and kind not in kinds and not populated(notes.get(kind)):
            gaps.append(f"review_notes.{kind}: scenario or relevance rationale missing")
    for index, question in enumerate(doc.get("questions", [])):
        if not populated(question.get("text")):
            gaps.append(f"questions[{index}].text: missing")
        if question.get("blocking"):
            gaps.append(f"questions[{index}]: unresolved blocking question")
    return gaps


def check(doc, selected=None):
    errors = structural_errors(doc)
    result = {"structure": "fail" if errors else "pass", "errors": errors,
              "review_gaps": None if errors else review_gaps(doc, selected),
              "semantic_validation": "not_evaluated", "implementation": "not_evaluated"}
    if selected is not None:
        result["scope"] = {"structure": "whole_record",
                           "review": "selected_scenarios_and_dependencies",
                           "scenarios": sorted(set(selected)),
                           "overall_conops_coverage": "not_evaluated"}
    if not errors:
        result["model_sha256"] = fingerprint(doc)
        result["open_questions"] = doc.get("questions", [])
    return result


def records(doc):
    result = {"system": doc.get("system", {})}
    for group in GROUPS:
        result.update(doc.get(group, {}))
    return result


def dependencies(doc):
    deps = {key: set() for key in records(doc)}
    for key, value in doc.get("needs", {}).items():
        if value.get("actor"):
            deps[key].add(value["actor"])
        deps[key].add("system")
    for key, value in doc.get("scenarios", {}).items():
        deps[key].add("system")
        if value.get("need"):
            deps[key].add(value["need"])
        for step in value.get("steps", []):
            deps[key].update(step[field] for field in ("from", "to") if step.get(field))
    for key, value in doc.get("criteria", {}).items():
        if value.get("scenario"):
            deps[key].add(value["scenario"])
    return deps


def view(doc, selected):
    if not selected:
        return {"system": doc.get("system", {}),
                "ids": {g: list(doc.get(g, {})) for g in GROUPS},
                "open_questions": doc.get("questions", [])}
    all_records = records(doc)
    unknown = set(selected) - set(all_records)
    if unknown:
        raise ValueError("Unknown IDs: " + ", ".join(sorted(unknown)))
    deps = dependencies(doc)
    included = set(selected)
    included.update(key for key, value in doc.get("criteria", {}).items()
                    if value.get("scenario") in included)
    while True:
        expanded = included | set().union(*(deps[x] for x in included))
        if expanded == included:
            break
        included = expanded
    return {"records": {key: all_records[key] for key in sorted(included)},
            "questions": [q for q in doc.get("questions", [])
                          if not q.get("affects") or included.intersection(q["affects"])]}


def diff(old, new):
    before, after = records(old), records(new)
    changed = {key for key in before.keys() | after.keys()
               if key not in before or key not in after or before[key] != after[key]}
    deps = dependencies(old)
    for key, refs in dependencies(new).items():
        deps.setdefault(key, set()).update(refs)
    affected = set(changed)
    while True:
        expanded = affected | {key for key, refs in deps.items() if refs & affected}
        if expanded == affected:
            break
        affected = expanded
    return {"changed": sorted(changed), "reconsider": sorted(affected - changed),
            "other_changes": [key for key in ("version", "questions", "review_notes", "extra")
                              if old.get(key) != new.get(key)],
            "evidence_status": "recheck" if fingerprint(old) != fingerprint(new) else "unchanged"}


def evaluate(doc, observations):
    errors = structural_errors(doc)
    if errors:
        return {"overall": "invalid", "errors": errors}
    if not isinstance(observations, dict):
        return {"overall": "invalid", "errors": ["observations must be an object"]}
    if set(observations) - {"model_sha256", "results"}:
        return {"overall": "invalid", "errors": ["unknown observation field"]}
    if observations.get("model_sha256") != fingerprint(doc):
        return {"overall": "stale", "errors": ["observation model hash does not match"]}
    results = observations.get("results")
    if not isinstance(results, dict):
        return {"overall": "invalid", "errors": ["results must be an object"]}
    criteria = doc.get("criteria", {})
    if set(results) - set(criteria):
        return {"overall": "invalid", "errors": ["observations reference unknown criteria"]}
    evaluated = {}
    for key, criterion in criteria.items():
        if any(not populated(criterion.get(field)) for field in ("scenario", "metric", "op", "unit", "basis")) or "value" not in criterion:
            evaluated[key] = {"status": "unknown", "reason": "incomplete criterion"}
            continue
        observation = results.get(key)
        if observation is None:
            evaluated[key] = {"status": "unknown", "reason": "no observation"}
            continue
        if not isinstance(observation, dict) or set(observation) != {"value", "unit", "evidence", "context"}:
            evaluated[key] = {"status": "invalid", "reason": "expected value, unit, evidence, context"}
            continue
        if not number(observation["value"]):
            evaluated[key] = {"status": "invalid", "reason": "measurement must be a finite number"}
            continue
        if observation["unit"] != criterion["unit"]:
            evaluated[key] = {"status": "invalid", "reason": "unit mismatch; no implicit conversion"}
            continue
        if not populated(observation["evidence"]) or not populated(observation["context"]):
            evaluated[key] = {"status": "invalid", "reason": "evidence and context required"}
            continue
        passed = OPS[criterion["op"]](observation["value"], criterion["value"])
        evaluated[key] = {"status": "pass" if passed else "fail", "value": observation["value"],
                          "unit": observation["unit"], "evidence": observation["evidence"],
                          "context": observation["context"]}
    statuses = {x["status"] for x in evaluated.values()}
    overall = "unknown" if not statuses else next((s for s in ("invalid", "fail", "unknown") if s in statuses), "pass")
    return {"overall": overall, "results": evaluated,
            "scope": "declared numeric criteria on supplied observations only",
            "model_sha256": fingerprint(doc), "semantic_validation": "not_evaluated",
            "implementation": "not_independently_observed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "check", "view", "diff", "evaluate"):
        child = commands.add_parser(command)
        child.add_argument("record")
        if command == "check":
            child.add_argument("--review", action="store_true")
            child.add_argument("--scenario", action="append", dest="scenarios",
                               help="Review only this scenario and its dependencies; repeat for a set")
        if command == "view":
            child.add_argument("ids", nargs="*")
        if command in ("diff", "evaluate"):
            child.add_argument("other")
    args = parser.parse_args()
    try:
        if args.command == "init":
            draft = {"version": 1, "system": {"name": "", "purpose": "", "boundary": ""},
                     **{g: {} for g in GROUPS}, "questions": [], "review_notes": {}}
            with Path(args.record).open("x", encoding="utf-8") as handle:
                json.dump(draft, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
            print(compact({"created": str(Path(args.record)), "state": "incomplete_draft"}))
            return 0
        doc = read(args.record)
        report = check(doc, args.scenarios if args.command == "check" else None)
        if args.command == "check":
            print(compact(report))
            return int(bool(report["errors"] or (args.review and report["review_gaps"])))
        if report["errors"]:
            print(compact(report))
            return 1
        if args.command == "view":
            print(compact(view(doc, args.ids)))
            return 0
        other = read(args.other)
        if args.command == "evaluate":
            result = evaluate(doc, other)
            print(compact(result))
            return int(result["overall"] != "pass")
        other_report = check(other)
        if other_report["errors"]:
            print(compact(other_report))
            return 1
        print(compact(diff(doc, other)))
        return 0
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print(compact({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
