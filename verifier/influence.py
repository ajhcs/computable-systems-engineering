"""Bounded synthetic witnesses that one sampled requirement property matters.

This is a property-influence criterion inspired by FLIP, not FLIP itself. A
witness is a pair of complete traces differing in exactly one property at one
sample, for which the selected requirement changes from pass to fail.
"""

from copy import deepcopy
from itertools import product

from .language import LanguageError, _clock, _compare, _evaluate, _fraction_decimal, parse_requirement

VERSION = "influence-1.0"
EXHAUSTIVE_CASE_CAP = 4096


def _roles(parsed):
    return {role: parsed[role] for role in ("scope", "trigger", "response", "release")
            if parsed.get(role) is not None}


def _domain(spec, comparisons):
    """One concrete representative for each attainable comparison truth vector."""
    if spec["type"] == "bool":
        candidates = [False, True]
    elif spec["type"] == "enum":
        mentioned = {item["value"] for item in comparisons}
        candidates = [value for value in spec["values"] if value in mentioned]
        other = next((value for value in spec["values"] if value not in mentioned), None)
        if other is not None:
            candidates.append(other)
    else:
        low, high = spec["min"], spec["max"]
        candidates = {low, high}
        for item in comparisons:
            boundary = item["value"]
            candidates.update(value for value in (boundary - 1, boundary, boundary + 1)
                              if low <= value <= high)
        candidates = sorted(candidates)
    representatives = []
    seen = set()
    for value in candidates:
        signature = tuple(_compare(item, {item["name"]: value}) for item in comparisons)
        if signature not in seen:
            seen.add(signature)
            representatives.append(value)
    return representatives


def _row(parsed, **changes):
    result = {"trigger": False, "response": False}
    if parsed["scope"] is not None:
        result["scope"] = True
    if parsed["timing"] == "until":
        result["release"] = False
    result.update(changes)
    return result


def _template(parsed, role):
    """Build pass/fail role sketches; concrete values and verdicts are checked later."""
    timing = parsed["timing"]
    if role == "scope" and parsed["scope"] is None:
        return None
    if timing == "always":
        if role == "response":
            passing = [_row(parsed, trigger=True, response=True)]
            failing = [_row(parsed, trigger=True, response=False)]
            return 0, passing, failing
        passing = [_row(parsed, trigger=True, response=True),
                   _row(parsed, trigger=role == "scope", response=False,
                        scope=role != "scope")]
        failing = deepcopy(passing)
        failing[1][role] = True
        return 1, passing, failing
    if timing == "within":
        deadline = parsed["deadline_ticks"]
        if role == "response":
            passing = [_row(parsed, trigger=True)] + [_row(parsed) for _ in range(deadline)]
            for row in passing[1:]:
                row["scope"] = False
            passing[deadline]["response"] = True
            failing = deepcopy(passing)
            failing[deadline]["response"] = False
            return deadline, passing, failing
        passing = [_row(parsed, trigger=True, response=True), _row(parsed, trigger=False)]
        passing += [_row(parsed) for _ in range(deadline + 1)]
        if role == "trigger":
            passing[2]["trigger"] = False
            passing[1]["scope"] = False
            for row in passing[3:]:
                row["scope"] = False
        else:
            passing[1]["scope"] = False
            passing[2]["scope"] = False
            passing[2]["trigger"] = True
            for row in passing[3:]:
                row["scope"] = False
        failing = deepcopy(passing)
        failing[2][role] = True
        return 2, passing, failing
    if role == "response":
        passing = [_row(parsed, trigger=True, response=True), _row(parsed, release=True)]
        failing = deepcopy(passing)
        failing[0]["response"] = False
        return 0, passing, failing
    if role == "release":
        passing = [_row(parsed, trigger=True, response=True),
                   _row(parsed, release=True), _row(parsed, release=True)]
        failing = deepcopy(passing)
        failing[1]["release"] = False
        return 1, passing, failing
    passing = [_row(parsed, trigger=True, response=True),
               _row(parsed, response=True, release=True),
               _row(parsed), _row(parsed, release=True)]
    if role == "scope":
        passing[1]["scope"] = False
        passing[2]["scope"] = False
        passing[2]["trigger"] = True
        passing[3]["scope"] = False
    else:
        passing[1]["scope"] = False
        passing[3]["scope"] = False
    failing = deepcopy(passing)
    failing[2][role] = True
    return 2, passing, failing


def _template_length(parsed, role):
    if parsed["timing"] == "within":
        return parsed["deadline_ticks"] + (1 if role == "response" else 3)
    if parsed["timing"] == "always":
        return 1 if role == "response" else 2
    return 2 if role == "response" else 3 if role == "release" else 4


def _materialize(roles, domains, variable, focus_role, index, passing, failing):
    pass_rows, fail_rows = [], []
    target_pairs = None
    for tick, (pass_demands, fail_demands) in enumerate(zip(passing, failing)):
        pass_row, fail_row = {}, {}
        for name, domain in domains.items():
            relevant = [(role, item) for role, item in roles.items() if item["name"] == name]

            def satisfies(value, demands, *, focused=False):
                return all(_compare(item, {name: value}) is demands[role]
                           for role, item in relevant if not focused or role == focus_role)

            if tick == index and name == variable:
                target_pairs = [(left, right) for left in domain for right in domain
                                if left != right and satisfies(left, pass_demands, focused=True) and
                                satisfies(right, fail_demands, focused=True)]
                if not target_pairs:
                    return None
                pass_row[name], fail_row[name] = target_pairs[0]
            else:
                common = next((value for value in domain if satisfies(value, pass_demands)
                               and satisfies(value, fail_demands)), None)
                if common is None:
                    return None
                pass_row[name] = fail_row[name] = common
        pass_rows.append(pass_row)
        fail_rows.append(fail_row)
    return (([dict(row) if tick != index else {**row, variable: left}
              for tick, row in enumerate(pass_rows)],
             [dict(row) if tick != index else {**row, variable: right}
              for tick, row in enumerate(fail_rows)])
            for left, right in target_pairs)


def _short_lengths(parsed):
    if parsed["timing"] == "always":
        return (1, 2)
    if parsed["timing"] == "until":
        return (2, 3, 4)
    deadline = parsed["deadline_ticks"]
    return (deadline + 1, deadline + 2, deadline + 3)


def _exhaustive_short_witness(parsed, domains, variable, max_rows, search):
    """Fallback for tiny concrete spaces; still no global redundancy claim."""
    names = list(domains)
    domain_vectors = [domains[name] for name in names]
    state_count = 1
    for domain in domain_vectors:
        state_count *= len(domain)
    if not state_count or state_count > EXHAUSTIVE_CASE_CAP:
        return None
    states = [dict(zip(names, values)) for values in product(*domain_vectors)]
    for length in _short_lengths(parsed):
        if length > max_rows:
            continue
        case_count = 1
        for _ in range(length):
            case_count *= state_count
            if case_count > EXHAUSTIVE_CASE_CAP:
                break
        if case_count > EXHAUSTIVE_CASE_CAP:
            continue
        for sequence in product(range(state_count), repeat=length):
            if search["evaluations"] >= search["evaluation_cap"]:
                return None
            rows = [states[index] for index in sequence]
            base = _evaluate(parsed, rows)
            search["evaluations"] += 1
            if base["status"] not in ("pass", "fail"):
                continue
            for tick in range(length):
                for alternate in domains[variable]:
                    if alternate == rows[tick][variable]:
                        continue
                    if search["evaluations"] >= search["evaluation_cap"]:
                        return None
                    changed = [dict(row) for row in rows]
                    changed[tick][variable] = alternate
                    result = _evaluate(parsed, changed)
                    search["evaluations"] += 1
                    if {base["status"], result["status"]} != {"pass", "fail"}:
                        continue
                    if base["status"] == "pass":
                        return tick, rows, changed, base, result
                    return tick, changed, rows, result, base
    return None


def generate_influence_tests(model, requirement_id, *, max_rows=16, evaluation_cap=2000):
    """Find non-vacuous, one-cell pass/fail witnesses for referenced properties.

    Search templates are intentionally incomplete. An uncovered result says
    nothing about global redundancy; generated traces are not physical evidence.
    """
    if (type(max_rows) is not int or not 1 <= max_rows <= 1000 or
            type(evaluation_cap) is not int or not 1 <= evaluation_cap <= 100000):
        raise LanguageError("schema", "Test-generation limits must be positive bounded integers")
    if not isinstance(model, dict) or not isinstance(model.get("requirements"), dict) or requirement_id not in model["requirements"]:
        raise LanguageError("schema", "Selected requirement is absent")
    properties = model["properties"]
    parsed = parse_requirement(model["requirements"][requirement_id], model["actors"],
                               properties, model["clock"])
    roles = _roles(parsed)
    by_name = {}
    for role, item in roles.items():
        by_name.setdefault(item["name"], []).append(role)
    domains = {name: _domain(properties[name], [roles[role] for role in used])
               for name, used in sorted(by_name.items())}
    report = {"version": VERSION, "criterion": "single_sample_property_influence",
              "claim_scope": "synthetic_tests_for_one_finite_sampled_requirement",
              "requirement_id": requirement_id,
              "clock_period_ms": _fraction_decimal(_clock(model["clock"])),
              "search": {"method": "bounded_role_templates_then_tiny_exhaustive_search", "max_rows": max_rows,
                         "evaluation_cap": evaluation_cap, "evaluations": 0,
                         "exhaustive_case_cap": EXHAUSTIVE_CASE_CAP,
                         "complete_for_all_traces": False},
              "variables": {}}
    for name, used in sorted(by_name.items()):
        item = {"roles": used, "status": "not_found_within_search"}
        if len(domains[name]) < 2:
            item["reason"] = "Declared domain has no distinct comparison behavior"
        else:
            for role in used:
                if _template_length(parsed, role) > max_rows:
                    item["reason"] = "Minimum template exceeds max_rows"
                    continue
                sketch = _template(parsed, role)
                if sketch is None:
                    continue
                index, passing, failing = sketch
                pairs = _materialize(roles, domains, name, role, index, passing, failing)
                if pairs is None:
                    continue
                for pass_rows, fail_rows in pairs:
                    if report["search"]["evaluations"] + 2 > evaluation_cap:
                        item["reason"] = "Evaluation cap exceeded"
                        break
                    pass_result = _evaluate(parsed, pass_rows)
                    fail_result = _evaluate(parsed, fail_rows)
                    report["search"]["evaluations"] += 2
                    if pass_result["status"] == "pass" and fail_result["status"] == "fail":
                        item = {"roles": used, "status": "witness", "witness_role": role,
                                "changed_index": index, "pass_value": pass_rows[index][name],
                                "fail_value": fail_rows[index][name],
                                "pass_trace": pass_rows, "fail_trace": fail_rows,
                                "pass_result": pass_result, "fail_result": fail_result}
                        break
                if item["status"] == "witness" or item.get("reason") == "Evaluation cap exceeded":
                    break
            if item["status"] != "witness" and report["search"]["evaluations"] < evaluation_cap:
                fallback = _exhaustive_short_witness(parsed, domains, name, max_rows, report["search"])
                if fallback is not None:
                    index, pass_rows, fail_rows, pass_result, fail_result = fallback
                    item = {"roles": used, "status": "witness", "witness_role": "short_exhaustive",
                            "changed_index": index, "pass_value": pass_rows[index][name],
                            "fail_value": fail_rows[index][name],
                            "pass_trace": pass_rows, "fail_trace": fail_rows,
                            "pass_result": pass_result, "fail_result": fail_result}
        report["variables"][name] = item
    report["coverage"] = {"referenced": len(by_name),
                          "witnessed": sum(item["status"] == "witness" for item in report["variables"].values())}
    report["status"] = "pass" if report["coverage"]["witnessed"] == report["coverage"]["referenced"] else "unknown"
    return report
