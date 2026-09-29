"""Bounded finite semantics. No model-provided expression is executed as code."""

from collections import deque
from hashlib import sha256
from itertools import product
import json
import re

VERSION = "0.1.0"
OBLIGATIONS = ("declarations", "types", "traces", "consistency", "scenarios")
ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
OPS = {"==", "!=", "<", "<=", ">", ">="}


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def load_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_pairs,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite number: {value}")))


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")).hexdigest()


def focused_view(model, selected):
    """Make an LLM context view; verification must still use the complete model."""
    selected = sorted(set(selected))
    if not selected or any(key not in model.get("scenarios", {}) for key in selected):
        raise ValueError("Select existing scenario IDs for a focused view")
    return {"artifact_sha256": digest(model), "view_scope": selected,
            "global": {key: model.get(key, {}) for key in
                       ("actors", "properties", "data", "exchanges", "statements", "traces")},
            "scenarios": {key: model["scenarios"][key] for key in selected}}


def finding(rule, status, ids=(), explanation="", evidence=None):
    result = {"rule": rule, "status": status, "ids": sorted(set(str(x) for x in ids)),
              "explanation": explanation}
    if evidence is not None:
        result["evidence"] = evidence
    return result


def _map(value, name, issues):
    if not isinstance(value, dict):
        issues.append(finding("schema", "error", [name], "Expected an object"))
        return {}
    return value


def _keys(obj, allowed, name, issues):
    extra = set(obj) - set(allowed)
    if extra:
        issues.append(finding("schema", "error", [name], "Unknown fields: " + ", ".join(sorted(extra))))


def _domain(spec, name, issues, *, owner=False):
    if not isinstance(spec, dict):
        issues.append(finding("declaration", "error", [name], "Expected a declaration object"))
        return None
    _keys(spec, {"type", "values", "min", "max", "unit", "scale", "owner"} if owner else
          {"type", "values", "min", "max", "unit", "scale"}, name, issues)
    typ = spec.get("type")
    if owner and spec.get("owner") not in ("input", "controlled"):
        issues.append(finding("declaration", "error", [name], "Owner must be input or controlled"))
    if typ == "bool":
        if set(spec) & {"values", "min", "max", "unit", "scale"}:
            issues.append(finding("declaration", "error", [name], "Boolean has no values, range, unit, or scale"))
        return (False, True)
    if typ == "enum":
        values = spec.get("values")
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
            issues.append(finding("declaration", "error", [name], "Enum needs unique string values"))
            return None
        if set(spec) & {"min", "max", "unit", "scale"}:
            issues.append(finding("declaration", "error", [name], "Enum has no range, unit, or scale"))
        return tuple(values)
    if typ == "int":
        lo, hi = spec.get("min"), spec.get("max")
        if type(lo) is not int or type(hi) is not int or hi < lo or hi - lo > 100000:
            issues.append(finding("declaration", "error", [name], "Integer needs finite inclusive bounds, width <= 100000"))
            return None
        if not isinstance(spec.get("unit"), str):
            issues.append(finding("declaration", "error", [name], "Integer unit must be a string (empty for dimensionless)"))
        scale = spec.get("scale")
        if not isinstance(scale, str) or not re.fullmatch(r"(?:0*[1-9][0-9]*|0*\.[0-9]*[1-9][0-9]*|[1-9][0-9]*\.[0-9]+)", scale):
            issues.append(finding("declaration", "error", [name], "Integer scale must be a positive decimal string"))
        return range(lo, hi + 1)
    issues.append(finding("declaration", "unsupported", [name], "Unsupported property type"))
    return None


def _value(spec, value, unit, name, issues):
    typ = spec.get("type")
    okay = ((typ == "bool" and type(value) is bool) or
            (typ == "enum" and isinstance(value, str) and value in spec.get("values", [])) or
            (typ == "int" and type(value) is int and type(spec.get("min")) is int and
             type(spec.get("max")) is int and spec["min"] <= value <= spec["max"]))
    if not okay:
        issues.append(finding("type", "fail", [name], "Literal is outside declared type or domain"))
    expected = spec.get("unit", "") if typ == "int" else None
    if (expected is not None and unit != expected) or (expected is None and unit is not None):
        issues.append(finding("unit", "fail", [name], "Literal unit does not match declaration"))


def _predicate(expr, props, name, issues, depth=0):
    if depth > 32:
        issues.append(finding("predicate", "unsupported", [name], "Predicate nesting exceeds 32"))
        return
    if not isinstance(expr, dict):
        issues.append(finding("predicate", "error", [name], "Predicate must be an object"))
        return
    if "all" in expr or "any" in expr:
        key = "all" if "all" in expr else "any"
        if set(expr) != {key} or not isinstance(expr[key], list) or not expr[key]:
            issues.append(finding("predicate", "error", [name], "Boolean connective needs a nonempty list"))
            return
        for part in expr[key]:
            _predicate(part, props, name, issues, depth + 1)
    elif "not" in expr:
        if set(expr) != {"not"}:
            issues.append(finding("predicate", "error", [name], "Malformed negation"))
        _predicate(expr["not"], props, name, issues, depth + 1)
    elif "ref" in expr:
        _keys(expr, {"ref", "op", "value", "unit"}, name, issues)
        ref, op = expr.get("ref"), expr.get("op")
        if ref not in props:
            issues.append(finding("undeclared", "fail", [name, ref], "Predicate references undeclared property"))
            return
        if op not in OPS:
            issues.append(finding("predicate", "unsupported", [name], "Unsupported comparison operator"))
        elif op not in ("==", "!=") and props[ref].get("type") != "int":
            issues.append(finding("type", "fail", [name, ref], "Ordered comparison requires integer"))
        _value(props[ref], expr.get("value"), expr.get("unit"), name, issues)
    else:
        issues.append(finding("predicate", "unsupported", [name], "Unsupported predicate form"))


def _eval(expr, state):
    if "all" in expr:
        return all(_eval(x, state) for x in expr["all"])
    if "any" in expr:
        return any(_eval(x, state) for x in expr["any"])
    if "not" in expr:
        return not _eval(expr["not"], state)
    left, right, op = state[expr["ref"]], expr["value"], expr["op"]
    return {"==": lambda: left == right, "!=": lambda: left != right,
            "<": lambda: left < right, "<=": lambda: left <= right,
            ">": lambda: left > right, ">=": lambda: left >= right}[op]()


def _render(expr, props):
    if "all" in expr:
        return "(" + " AND ".join(_render(x, props) for x in expr["all"]) + ")"
    if "any" in expr:
        return "(" + " OR ".join(_render(x, props) for x in expr["any"]) + ")"
    if "not" in expr:
        return "NOT (" + _render(expr["not"], props) + ")"
    literal = json.dumps(expr["value"])
    ref = expr["ref"]
    if props[ref]["type"] == "int":
        scale, unit = props[ref]["scale"], props[ref]["unit"]
        literal += f" {unit}" if scale == "1" else f" ticks of {scale} {unit}"
    return f"{ref} {expr['op']} {literal}"


def _validate(model, selected):
    issues = []
    if not isinstance(model, dict) or model.get("version") != 2:
        return {}, [finding("schema", "unsupported", [], "Only version-2 verifier records are supported")]
    _keys(model, {"version", "actors", "properties", "data", "exchanges", "statements", "traces", "scenarios"}, "model", issues)
    groups = {key: _map(model.get(key, {}), key, issues) for key in
              ("actors", "properties", "data", "exchanges", "statements", "scenarios")}
    actors, props, data, exchanges, statements, scenarios = (groups[k] for k in groups)
    seen = {}
    for group, records in groups.items():
        for key in records:
            if not isinstance(key, str) or not ID.fullmatch(key):
                issues.append(finding("identifier", "error", [key], "Invalid identifier"))
            if key in seen:
                issues.append(finding("identifier", "fail", [key], f"Duplicate identifier in {seen[key]} and {group}"))
            seen[key] = group
    domains = {}
    for key, spec in list(props.items()) + list(data.items()):
        domains[key] = _domain(spec, key, issues, owner=key in props)
    for key, actor in actors.items():
        if not isinstance(actor, dict):
            issues.append(finding("schema", "error", [key], "Actor must be an object"))
        else:
            _keys(actor, {}, key, issues)
    for key, exchange in exchanges.items():
        exchange = _map(exchange, key, issues)
        _keys(exchange, {"from", "to", "fields"}, key, issues)
        for endpoint in ("from", "to"):
            if exchange.get(endpoint) not in actors:
                issues.append(finding("undeclared", "fail", [key, exchange.get(endpoint)], "Exchange endpoint is undeclared"))
        fields = _map(exchange.get("fields", {}), key, issues)
        for field, spec in fields.items():
            if field not in data:
                issues.append(finding("undeclared", "fail", [key, field], "Exchange field is undeclared data"))
            elif spec != data[field]:
                issues.append(finding("type", "fail", [key, field], "Exchange field type or unit differs from data declaration"))
    categories = {"need", "goal", "fact", "assumption", "observation", "requirement"}
    for key, statement in statements.items():
        statement = _map(statement, key, issues)
        _keys(statement, {"category", "subject", "text", "modality", "when", "predicate", "source"}, key, issues)
        if statement.get("category") not in categories:
            issues.append(finding("statement", "unsupported", [key], "Unsupported statement category"))
        if statement.get("subject") not in actors:
            issues.append(finding("undeclared", "fail", [key, statement.get("subject")], "Statement subject undeclared"))
        if statement.get("category") == "requirement":
            if statement.get("modality") != "shall":
                issues.append(finding("statement", "fail", [key], "Requirement must use shall"))
            for field in ("when", "predicate"):
                if field not in statement:
                    issues.append(finding("statement", "error", [key], f"Missing {field}"))
                else:
                    _predicate(statement[field], props, key, issues)
        elif not isinstance(statement.get("text"), str):
            issues.append(finding("statement", "error", [key], "Qualitative statement needs text"))
        elif "modality" in statement or "predicate" in statement or "when" in statement:
            issues.append(finding("statement", "fail", [key], "Only a requirement may carry normative predicate fields"))
    traces = model.get("traces", [])
    if not isinstance(traces, list):
        issues.append(finding("schema", "error", ["traces"], "Traces must be a list"))
        traces = []
    for trace in traces:
        if not isinstance(trace, dict):
            issues.append(finding("trace", "error", [], "Trace must be an object"))
            continue
        _keys(trace, {"from", "to", "kind"}, "trace", issues)
        source, target, kind = trace.get("from"), trace.get("to"), trace.get("kind")
        valid = ((kind == "justifies" and statements.get(source, {}).get("category") == "requirement" and
                  statements.get(target, {}).get("category") in ("need", "goal")) or
                 (kind == "addresses" and source in scenarios and statements.get(target, {}).get("category") == "requirement"))
        if not valid:
            issues.append(finding("trace", "fail", [source, target], "Broken or mistyped trace"))
    if selected:
        for key in selected:
            if key not in scenarios:
                issues.append(finding("scope", "fail", [key], "Selected scenario is undeclared"))
    for key, scenario in scenarios.items():
        scenario = _map(scenario, key, issues)
        _keys(scenario, {"start", "initial", "initial_data", "external_at", "terminal", "completion", "require_completion", "steps"}, key, issues)
        steps = _map(scenario.get("steps", {}), key, issues)
        initial = _map(scenario.get("initial", {}), key, issues)
        if not isinstance(scenario.get("start"), str) or not scenario["start"]:
            issues.append(finding("scenario", "error", [key], "Missing start node"))
        for prop in props:
            if props[prop].get("owner") == "controlled" and prop not in initial:
                issues.append(finding("scenario", "error", [key, prop], "Missing initial controlled value"))
        for prop, value in initial.items():
            if prop not in props or props[prop].get("owner") != "controlled":
                issues.append(finding("scenario", "fail", [key, prop], "Initial value must name controlled property"))
            else:
                _value(props[prop], value, props[prop].get("unit", "") if props[prop].get("type") == "int" else None, key, issues)
        for field in ("initial_data", "external_at", "completion"):
            if not isinstance(scenario.get(field, []), list) or any(not isinstance(v, str) for v in scenario.get(field, [])):
                issues.append(finding("scenario", "error", [key], f"{field} must be string list"))
        for item in scenario.get("initial_data", []):
            if item not in data:
                issues.append(finding("undeclared", "fail", [key, item], "Initial data undeclared"))
        terminal = _map(scenario.get("terminal", {}), key, issues)
        for node, reason in terminal.items():
            if not isinstance(reason, str) or not reason:
                issues.append(finding("scenario", "error", [key, node], "Terminal needs a reason"))
        for node in scenario.get("completion", []):
            if node not in terminal:
                issues.append(finding("scenario", "fail", [key, node], "Completion must be terminal"))
        if type(scenario.get("require_completion", False)) is not bool:
            issues.append(finding("scenario", "error", [key], "require_completion must be boolean"))
        nodes = {scenario.get("start")} | set(terminal)
        for step_id, step in steps.items():
            if not isinstance(step_id, str) or not ID.fullmatch(step_id):
                issues.append(finding("identifier", "error", [step_id], "Invalid step identifier"))
            if step_id in seen:
                issues.append(finding("identifier", "fail", [step_id], "Duplicate step identifier"))
            seen[step_id] = "steps"
            step = _map(step, step_id, issues)
            _keys(step, {"from", "to", "guard", "effects", "consumes", "produces", "exchange"}, step_id, issues)
            if not isinstance(step.get("from"), str) or not isinstance(step.get("to"), str):
                issues.append(finding("scenario", "error", [key, step_id], "Step needs from and to nodes"))
            nodes.update((step.get("from"), step.get("to")))
            if step.get("from") in terminal:
                issues.append(finding("scenario", "fail", [key, step_id], "Terminal has outgoing step"))
            if "guard" in step:
                _predicate(step["guard"], props, step_id, issues)
            for field in ("consumes", "produces"):
                values = step.get(field, [])
                if not isinstance(values, list):
                    issues.append(finding("scenario", "error", [step_id], f"{field} must be list"))
                    continue
                for item in values:
                    if item not in data:
                        issues.append(finding("undeclared", "fail", [step_id, item], "Step data undeclared"))
            effects = _map(step.get("effects", {}), step_id, issues)
            for prop, value in effects.items():
                if prop not in props or props[prop].get("owner") != "controlled":
                    issues.append(finding("scenario", "fail", [step_id, prop], "Effect must target controlled property"))
                else:
                    _value(props[prop], value, props[prop].get("unit", "") if props[prop].get("type") == "int" else None, step_id, issues)
            if "exchange" in step and step["exchange"] not in exchanges:
                issues.append(finding("undeclared", "fail", [step_id, step["exchange"]], "Step exchange undeclared"))
            elif "exchange" in step and isinstance(step.get("produces", []), list):
                fields = exchanges[step["exchange"]].get("fields", {})
                if isinstance(fields, dict):
                    for item in step.get("produces", []):
                        if item not in fields:
                            issues.append(finding("type", "fail", [step_id, item], "Produced data is not a field of the step exchange"))
        for node in scenario.get("external_at", []):
            if node not in nodes:
                issues.append(finding("scenario", "fail", [key, node], "External input point is not a scenario node"))
            if node in terminal:
                issues.append(finding("scenario", "fail", [key, node], "Terminal cannot be an external input point"))
    return groups, issues


def _assignments(names, domains, cap):
    count = 1
    for name in names:
        count *= len(domains[name])
    if count > cap:
        return None, count
    return product(*(domains[name] for name in names)), count


def _consistency(groups, domains, cap):
    props, statements = groups["properties"], groups["statements"]
    inputs = sorted(k for k, v in props.items() if v["owner"] == "input")
    controlled = sorted(k for k, v in props.items() if v["owner"] == "controlled")
    contexts, context_count = _assignments(inputs, domains, cap)
    controls, control_count = _assignments(controlled, domains, cap)
    if contexts is None or controls is None or context_count * control_count > cap:
        return [finding("consistency", "unknown", [], "Assignment limit exceeded", {"assignments": context_count * control_count, "cap": cap})]
    requirements = {k: v for k, v in statements.items() if v["category"] == "requirement"}
    results = []
    exercised = set()
    control_values = list(product(*(domains[name] for name in controlled)))
    for context in contexts:
        environment = dict(zip(inputs, context))
        applicable = sorted(k for k, req in requirements.items() if _eval(req["when"], environment | dict(zip(controlled, control_values[0]))))
        exercised.update(applicable)
        # Applicability is deliberately restricted to input properties below.
        if not applicable:
            continue
        if not any(all(_eval(requirements[k]["predicate"], environment | dict(zip(controlled, values))) for k in applicable)
                   for values in control_values):
            conflict = applicable[:]
            for key in applicable:
                smaller = [item for item in conflict if item != key]
                if smaller and not any(all(_eval(requirements[item]["predicate"], environment | dict(zip(controlled, values)))
                                       for item in smaller) for values in control_values):
                    conflict = smaller
            results.append(finding("consistency", "fail", conflict, "Applicable requirements cannot be jointly satisfied",
                                   {"input": environment, "applicable": applicable, "conflict": conflict}))
    for key in sorted(set(requirements) - exercised):
        results.append(finding("applicability", "unknown", [key], "Requirement has no applicable input context in declared domain"))
    return results


def _refs(expr):
    if "ref" in expr:
        return {expr["ref"]}
    if "not" in expr:
        return _refs(expr["not"])
    return set().union(*(_refs(x) for x in expr.get("all", expr.get("any", []))))


def _scenario(key, scenario, groups, domains, cap):
    props = groups["properties"]
    input_names = sorted(k for k, v in props.items() if v["owner"] == "input")
    control_names = sorted(k for k, v in props.items() if v["owner"] == "controlled")
    data_names = sorted(groups["data"])
    input_values, count = _assignments(input_names, domains, cap)
    if input_values is None:
        return [finding("scenario", "unknown", [key], "Initial input limit exceeded", {"contexts": count, "cap": cap})]
    starts = []
    for values in input_values:
        state = (scenario["start"], tuple(scenario["initial"][k] for k in control_names),
                 tuple(values), tuple(k in scenario.get("initial_data", []) for k in data_names))
        starts.append(state)
    seen = set(starts)
    queue = deque(starts)
    edges = {}
    paths = {state: [] for state in starts}
    enabled_steps = set()
    blocked_data = set()
    terminal = scenario.get("terminal", {})
    steps = scenario.get("steps", {})
    transitions = 0
    while queue:
        state = queue.popleft()
        node, control, inp, available = state
        successors = []
        values = dict(zip(control_names, control)) | dict(zip(input_names, inp))
        if node in scenario.get("external_at", []):
            for new_input in product(*(domains[k] for k in input_names)):
                if tuple(new_input) != inp:
                    successors.append(((node, control, tuple(new_input), available), "external"))
        if node not in terminal:
            for step_id, step in sorted(steps.items()):
                if step["from"] != node:
                    continue
                if "guard" in step and not _eval(step["guard"], values):
                    continue
                missing = set(step.get("consumes", [])) - {k for k, present in zip(data_names, available) if present}
                if missing:
                    blocked_data.update((step_id, k) for k in missing)
                    continue
                enabled_steps.add(step_id)
                new_control = dict(zip(control_names, control)) | step.get("effects", {})
                new_data = set(k for k, present in zip(data_names, available) if present) | set(step.get("produces", []))
                target = (step["to"], tuple(new_control[k] for k in control_names), inp,
                          tuple(k in new_data for k in data_names))
                successors.append((target, step_id))
        transitions += len(successors)
        if transitions > cap:
            return [finding("scenario", "unknown", [key], "Transition limit exceeded",
                            {"transitions": transitions, "cap": cap})]
        edges[state] = successors
        for target, label in successors:
            if target not in seen:
                seen.add(target)
                paths[target] = paths[state] + [label]
                queue.append(target)
                if len(seen) > cap:
                    return [finding("scenario", "unknown", [key], "State limit exceeded", {"states": len(seen), "cap": cap})]
    results = []
    for step_id in sorted(set(steps) - enabled_steps):
        if any(steps[step_id]["from"] == state[0] for state in seen):
            reason = "Required data unavailable" if any(pair[0] == step_id for pair in blocked_data) else "Guard never enabled"
        else:
            reason = "Source node unreachable"
        results.append(finding("step-reachability", "fail", [key, step_id], reason))
    for state in sorted(seen):
        if state[0] not in terminal and not edges[state]:
            results.append(finding("dead-end", "fail", [key], "Reachable nonterminal state has no transition",
                                   {"node": state[0], "path": paths[state]}))
            break
    if scenario.get("require_completion", False):
        reverse = {state: set() for state in seen}
        for state, successors in edges.items():
            for target, _ in successors:
                reverse[target].add(state)
        good = {state for state in seen if state[0] in scenario.get("completion", [])}
        back = deque(good)
        while back:
            for prior in reverse[back.popleft()] - good:
                good.add(prior)
                back.append(prior)
        bad = next((state for state in sorted(seen) if state not in good), None)
        if bad is not None:
            results.append(finding("progress", "fail", [key], "Reachable state has no path to completion",
                                   {"node": bad[0], "path": paths[bad]}))
    return results


def verify(model, *, review=False, selected=(), assignment_cap=100000, state_cap=100000, evidence=None):
    """Return a deterministic report. This is a local check, not an acceptance receipt."""
    selected = tuple(sorted(set(selected)))
    revision = digest(model)
    result = {"artifact_sha256": revision, "dependencies": {}, "checker_version": VERSION,
              "profile": "core-v2" if review else "draft-v2",
              "scope": {"scenarios": list(selected) if selected else "all", "review": review},
              "expected_obligations": list(OBLIGATIONS) if review else [],
              "completed_obligations": [], "limits": {"assignment_cap": assignment_cap, "state_cap": state_cap},
              "status": "unknown", "findings": []}
    issues = []
    try:
        groups, issues = _validate(model, selected)
    except (TypeError, ValueError, KeyError, AttributeError) as error:
        groups = {}
        issues = [finding("schema", "error", [], f"Malformed record: {type(error).__name__}")]
    if evidence is not None:
        result["dependencies"]["evidence_sha256"] = digest(evidence)
        if not isinstance(evidence, dict) or not isinstance(evidence.get("items"), list):
            issues.append(finding("evidence", "error", [], "Evidence must have an items list"))
        elif evidence.get("model_sha256") != revision:
            issues.append(finding("evidence", "unknown", [], "Evidence revision is stale or malformed"))
    by_obligation = {name: [] for name in OBLIGATIONS}
    for item in issues:
        rule = item["rule"]
        obligation = ("traces" if rule == "trace" else "scenarios" if rule in ("scenario", "scope") else
                      "types" if rule in ("type", "unit", "predicate") else "declarations")
        by_obligation[obligation].append(item)
    if not issues:
        props = groups["properties"]
        result["rendered_requirements"] = {
            key: f"When {_render(statement['when'], props)}, {statement['subject']} SHALL {_render(statement['predicate'], props)}."
            for key, statement in sorted(groups["statements"].items()) if statement["category"] == "requirement"}
        # Applicability depends only on environmental inputs in this increment.
        for key, statement in groups["statements"].items():
            if statement["category"] == "requirement" and (_refs(statement["when"]) -
                 {name for name, spec in props.items() if spec["owner"] == "input"}):
                by_obligation["consistency"].append(finding("applicability", "unsupported", [key],
                    "Applicability may reference only input properties"))
        if not by_obligation["consistency"]:
            domains = {key: _domain(spec, key, [], owner=key in props) for key, spec in
                       list(props.items()) + list(groups["data"].items())}
            by_obligation["consistency"] += _consistency(groups, domains, assignment_cap)
            scenarios = groups["scenarios"]
            for key in selected or sorted(scenarios):
                by_obligation["scenarios"] += _scenario(key, scenarios[key], groups, domains, state_cap)
        traces = model.get("traces", [])
        if review:
            if not any(s["category"] == "requirement" for s in groups["statements"].values()):
                by_obligation["traces"].append(finding("coverage", "unknown", [], "Required review has no requirements"))
            if not groups["scenarios"]:
                by_obligation["scenarios"].append(finding("coverage", "unknown", [], "Required review has no scenarios"))
            for key, statement in groups["statements"].items():
                if statement["category"] == "requirement" and not any(t["kind"] == "justifies" and t["from"] == key for t in traces):
                    by_obligation["traces"].append(finding("coverage", "fail", [key], "Requirement lacks justification trace"))
            for key in selected or sorted(groups["scenarios"]):
                if not any(t["kind"] == "addresses" and t["from"] == key for t in traces):
                    by_obligation["traces"].append(finding("coverage", "fail", [key], "Scenario lacks requirement trace"))
    if issues:
        by_obligation["consistency"].append(finding("consistency", "not_run", [], "Blocked by model validation"))
        by_obligation["scenarios"].append(finding("scenario", "not_run", [], "Blocked by model validation"))
    result["completed_obligations"] = [] if issues else [name for name in OBLIGATIONS if not by_obligation[name]]
    result["obligations"] = {name: ("not_run" if issues and not items else "pass" if not items else
                                    "error" if any(x["status"] == "error" for x in items) else
                                    "fail" if any(x["status"] == "fail" for x in items) else
                                    "unsupported" if any(x["status"] == "unsupported" for x in items) else
                                    "unknown" if any(x["status"] == "unknown" for x in items) else "not_run")
                             for name, items in by_obligation.items()}
    findings = [item for name in OBLIGATIONS for item in by_obligation[name]]
    findings.sort(key=lambda item: (item["rule"], item["ids"], item["status"], item["explanation"]))
    result["findings"] = findings
    statuses = {item["status"] for item in findings}
    result["status"] = ("error" if "error" in statuses else "fail" if "fail" in statuses else
                        "unsupported" if "unsupported" in statuses else "unknown" if "unknown" in statuses else
                        "pass" if not review or set(result["completed_obligations"]) == set(OBLIGATIONS) else "not_run")
    return result
