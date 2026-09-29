"""Small, deterministic, FRET-inspired language for sampled traces."""

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from hashlib import sha256
import json
import re

VERSION = "language-1.0"
NAME = r"[A-Za-z][A-Za-z0-9_]*"
PROPERTY_NAME = rf"{NAME}(?:\.{NAME})?"
NUMBER = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
COMPARISON = re.compile(rf"(?P<name>{PROPERTY_NAME}) (?P<op><=|>=|!=|=|<|>) (?P<value>{NAME}|{NUMBER})(?: (?P<unit>{NAME}))?\Z")
SENTENCE = re.compile(rf"(?:(?:In (?P<scope>[^,]+), )?(?P<condition>whenever|upon)|(?P<initial>Whenever|Upon)) (?P<trigger>[^,]+), (?P<actor>{NAME}) shall (?:(?P<always>always)|within (?P<duration>{NUMBER}) (?P<timeunit>milliseconds?|seconds?|minutes?)|until (?P<release>.+)) satisfy (?P<response>.+)\.\Z")
ID = re.compile(rf"{NAME}\Z")
PROPERTY_ID = re.compile(rf"{PROPERTY_NAME}\Z")
UNIT_MS = {"millisecond": 1, "second": 1000, "minute": 60000}


class LanguageError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(detail)


def _fraction_decimal(value):
    """Render an exact finite decimal; inputs arise from decimal literals."""
    numerator, denominator = value.numerator, value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise LanguageError("unit", "Quantity lacks a finite decimal representation")
    places = max(twos, fives)
    digits = str(abs(numerator) * 2 ** (places - twos) * 5 ** (places - fives))
    if places:
        digits = digits.zfill(places + 1)
        digits = digits[:-places] + "." + digits[-places:]
        digits = digits.rstrip("0").rstrip(".")
    return ("-" if numerator < 0 else "") + digits


def _decimal(value, label):
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(NUMBER, value):
        raise LanguageError("type", f"{label} must be an exact decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise LanguageError("type", f"Invalid {label}") from exc


def _time_unit(unit):
    if not isinstance(unit, str):
        raise LanguageError("unit", "Time unit must be a string")
    key = unit[:-1] if unit.endswith("s") else unit
    if key not in UNIT_MS:
        raise LanguageError("unit", f"Unsupported time unit: {unit}")
    return UNIT_MS[key]


def _clock(clock):
    if not isinstance(clock, dict) or set(clock) != {"period", "unit"}:
        raise LanguageError("schema", "Clock needs period and unit")
    period = Fraction(_decimal(clock["period"], "clock period")) * _time_unit(clock["unit"])
    if period <= 0:
        raise LanguageError("unit", "Clock period must be positive")
    return period


def _declarations(actors, properties):
    if not isinstance(actors, dict) or not actors or not isinstance(properties, dict) or not properties:
        raise LanguageError("schema", "Nonempty actors and properties maps required")
    for name, spec in actors.items():
        if not isinstance(name, str) or not ID.fullmatch(name) or not isinstance(spec, dict) or spec:
            raise LanguageError("schema", f"Invalid actor declaration: {name}")
    for name, spec in properties.items():
        if not isinstance(name, str) or not PROPERTY_ID.fullmatch(name) or not isinstance(spec, dict) or spec.get("owner") not in ("input", "controlled"):
            raise LanguageError("schema", f"Invalid property declaration: {name}")
        kind = spec.get("type")
        if kind == "bool":
            if set(spec) != {"type", "owner"}:
                raise LanguageError("schema", f"Invalid boolean declaration: {name}")
        elif kind == "enum":
            values = spec.get("values")
            if set(spec) != {"type", "owner", "values"} or not isinstance(values, list) or not values or any(not isinstance(v, str) or not ID.fullmatch(v) for v in values) or len(values) != len(set(values)):
                raise LanguageError("schema", f"Invalid enum declaration: {name}")
        elif kind == "int":
            lo, hi, unit = spec.get("min"), spec.get("max"), spec.get("unit")
            if set(spec) != {"type", "owner", "min", "max", "scale", "unit"} or type(lo) is not int or type(hi) is not int or lo > hi or hi - lo > 100000 or not isinstance(unit, str) or (unit and not ID.fullmatch(unit)):
                raise LanguageError("schema", f"Invalid integer declaration: {name}")
            if _decimal(spec["scale"], "scale") <= 0:
                raise LanguageError("schema", f"Invalid scale: {name}")
        else:
            raise LanguageError("unsupported", f"Unsupported property type: {name}")


def _comparison(source, properties):
    match = COMPARISON.fullmatch(source)
    if not match:
        raise LanguageError("grammar", f"Malformed comparison: {source}")
    name, op, raw, unit = match.group("name", "op", "value", "unit")
    if name not in properties:
        raise LanguageError("undeclared", f"Undeclared property: {name}")
    spec = properties[name]
    kind = spec["type"]
    if kind == "bool":
        if op not in ("=", "!=") or raw not in ("true", "false"):
            raise LanguageError("type", f"Invalid Boolean comparison: {source}")
        if unit:
            raise LanguageError("unit", f"Boolean has no unit: {name}")
        value = raw == "true"
    elif kind == "enum":
        if op not in ("=", "!=") or raw not in spec["values"]:
            raise LanguageError("type", f"Invalid enum comparison: {source}")
        if unit:
            raise LanguageError("unit", f"Enum has no unit: {name}")
        value = raw
    else:
        if unit != (spec["unit"] or None):
            raise LanguageError("unit", f"Quantity unit mismatch: {name}")
        physical = _decimal(raw, "quantity")
        ticks = Fraction(physical) / Fraction(Decimal(spec["scale"]))
        if ticks.denominator != 1:
            raise LanguageError("unit", f"Quantity cannot be represented exactly: {name}")
        value = int(ticks)
        if not spec["min"] <= value <= spec["max"]:
            raise LanguageError("type", f"Quantity outside declared bounds: {name}")
    return {"name": name, "op": op, "value": value}


def parse_requirement(source, actors, properties, clock):
    _declarations(actors, properties)
    period = _clock(clock)
    if not isinstance(source, str):
        raise LanguageError("grammar", "Requirement must be a sentence")
    match = SENTENCE.fullmatch(source)
    if not match:
        raise LanguageError("grammar", "Sentence does not match profile 1 grammar")
    fields = match.groupdict()
    if fields["scope"] is None and fields["condition"] is not None:
        raise LanguageError("grammar", "Unscoped sentence must begin with Whenever or Upon")
    if fields["actor"] not in actors:
        raise LanguageError("undeclared", f"Undeclared actor: {fields['actor']}")
    mode = fields["condition"] or fields["initial"].lower()
    timing = "always" if fields["always"] else "within" if fields["duration"] else "until"
    if (mode == "whenever") != (timing == "always"):
        raise LanguageError("grammar", "Whenever pairs with always; upon pairs with within or until")
    result = {"actor": fields["actor"], "condition": mode, "timing": timing,
              "scope": _comparison(fields["scope"], properties) if fields["scope"] else None,
              "trigger": _comparison(fields["trigger"], properties),
              "response": _comparison(fields["response"], properties)}
    if properties[result["response"]["name"]]["owner"] != "controlled":
        raise LanguageError("owner", "Response must be controlled")
    if timing == "within":
        duration = Fraction(_decimal(fields["duration"], "duration")) * _time_unit(fields["timeunit"])
        ticks = duration / period
        if duration <= 0 or ticks.denominator != 1:
            raise LanguageError("unit", "Duration must be a positive exact number of clock ticks")
        if len(_fraction_decimal(duration)) > 64:
            raise LanguageError("unit", "Normalized duration exceeds 64 digits")
        result["deadline_ticks"] = int(ticks)
        # Decimal input times an integer unit factor has a finite decimal form.
        result["duration_ms"] = _fraction_decimal(duration)
    if timing == "until":
        result["release"] = _comparison(fields["release"], properties)
    return result


def render_requirement(parsed, properties):
    def comp(item):
        value = item["value"]
        spec = properties[item["name"]]
        if spec["type"] == "bool":
            value = "true" if value else "false"
        elif spec["type"] == "int":
            value = _fraction_decimal(Fraction(value) * Fraction(Decimal(spec["scale"])))
        return f"{item['name']} {item['op']} {value}" + (f" {spec['unit']}" if spec.get("unit") else "")
    head = f"In {comp(parsed['scope'])}, " if parsed["scope"] else ""
    head += parsed["condition"] if parsed["scope"] else parsed["condition"].capitalize()
    head += f" {comp(parsed['trigger'])}, {parsed['actor']} shall "
    timing = parsed["timing"]
    if timing == "within":
        head += f"within {parsed['duration_ms']} milliseconds"
    else:
        head += "always" if timing == "always" else f"until {comp(parsed['release'])}"
    return head + f" satisfy {comp(parsed['response'])}."


def _compare(item, row):
    value = row.get(item["name"])
    if value is None:
        return None
    target = item["value"]
    return {"=": lambda: value == target, "!=": lambda: value != target,
            "<": lambda: value < target, "<=": lambda: value <= target,
            ">": lambda: value > target, ">=": lambda: value >= target}[item["op"]]()


def _trace_value(value, spec):
    typ = spec["type"]
    return (type(value) is bool if typ == "bool" else
            type(value) is str and value in spec["values"] if typ == "enum" else
            type(value) is int and spec["min"] <= value <= spec["max"])


def _next_index(values, wanted):
    """First index at or after each position with the specified tri-state value."""
    length = len(values)
    result = [length] * (length + 1)
    for index in range(length - 1, -1, -1):
        result[index] = index if values[index] is wanted else result[index + 1]
    return result


def _evaluate(parsed, rows, *, diagnostic_cap=8):
    """Linear in observations plus triggers, with bounded diagnostic output."""
    scope, trigger, response = parsed["scope"], parsed["trigger"], parsed["response"]
    timing = parsed["timing"]
    events, missing, prior_scope, prior_trigger = [], False, None, None
    for index, row in enumerate(rows):
        scoped = _compare(scope, row) if scope else True
        condition = _compare(trigger, row)
        if timing == "always":
            if scoped is True and condition is True:
                events.append(index)
            elif scoped is not False and condition is not False:
                missing = True
        elif scoped is True and condition is True:
            if index == 0 or prior_scope is False or prior_trigger is False:
                events.append(index)
            elif prior_scope is None or prior_trigger is None:
                missing = True
        elif scoped is not False and condition is not False:
            missing = True
        prior_scope, prior_trigger = scoped, condition
    coverage = {"triggers": len(events)}
    if not events:
        return {"status": "unknown", "coverage": coverage, "reason": "No exercised or unambiguously identified condition"}

    values = [_compare(response, row) for row in rows]
    next_true = _next_index(values, True)
    next_false = _next_index(values, False)
    next_missing = _next_index(values, None)
    pending_count, pending_examples = 0, []

    def note(start, reason, deadline=None):
        nonlocal pending_count
        pending_count += 1
        if len(pending_examples) < diagnostic_cap:
            item = {"trigger_index": start, "reason": reason}
            if deadline is not None:
                item["deadline_index"] = deadline
            pending_examples.append(item)

    if timing == "until":
        release = [_compare(parsed["release"], row) for row in rows]
        next_release = _next_index(release, True)
        next_uncertain_release = _next_index(release, None)

    for start in events:
        if timing == "always":
            if values[start] is False:
                return {"status": "fail", "coverage": coverage, "counterexample": {"index": start}}
            if values[start] is None:
                note(start, "response missing")
        elif timing == "within":
            deadline = start + parsed["deadline_ticks"]
            end = min(deadline, len(rows) - 1)
            if next_true[start] <= end:
                continue
            if next_missing[start] <= end:
                note(start, "response missing before deadline", deadline)
            elif deadline < len(rows):
                return {"status": "fail", "coverage": coverage,
                        "counterexample": {"index": start, "deadline_index": deadline}}
            else:
                note(start, "deadline not observed", deadline)
        else:
            stop = next_release[start + 1]
            failed = next_false[start]
            uncertain_release = next_uncertain_release[start + 1]
            if failed < stop and uncertain_release > failed:
                return {"status": "fail", "coverage": coverage, "counterexample": {"index": failed}}
            if failed < stop and uncertain_release <= failed:
                note(start, "release may precede response failure")
            elif next_missing[start] < stop:
                note(start, "held response missing")
            elif stop == len(rows):
                note(start, "release missing or unobserved")

    pending = bool(pending_count or missing)
    return {"status": "unknown" if pending else "pass", "coverage": coverage,
            **({"reason": "Incomplete or missing observation", "pending_count": pending_count,
                "pending": pending_examples, "diagnostics_truncated": pending_count > len(pending_examples)} if pending else {})}


def check_document(model, *, review=False, observation_cap=10000, work_cap=1000000,
                   expected=None, diagnostic_cap=8):
    report = {"checker_version": VERSION, "status": "error", "results": {}, "review": bool(review),
              "required_review": bool(review and expected is not None),
              "claim_scope": "required_sampled_trace" if review and expected is not None else "candidate_sampled_trace" if review else "grammar_and_types"}
    try:
        if not isinstance(model, dict) or set(model) - {"language_version", "clock", "actors", "properties", "requirements", "observations", "complete"} or type(model.get("language_version")) is not int or model.get("language_version") != 1:
            raise LanguageError("schema", "Expected language_version 1 and known fields")
        actors, properties, clock = model["actors"], model["properties"], model["clock"]
        _declarations(actors, properties)
        _clock(clock)
        requirements = model["requirements"]
        if not isinstance(requirements, dict) or not requirements or any(not ID.fullmatch(key) for key in requirements):
            raise LanguageError("schema", "Nonempty requirement IDs required")
        parsed = {key: parse_requirement(value, actors, properties, clock) for key, value in sorted(requirements.items())}
        if expected is not None:
            if not isinstance(expected, dict) or set(expected) != {"version", "required"} or type(expected["version"]) is not int or expected["version"] != 1 or not isinstance(expected["required"], list) or any(not isinstance(item, str) or not ID.fullmatch(item) for item in expected["required"]) or len(expected["required"]) != len(set(expected["required"])):
                raise LanguageError("scope", "Expected manifest needs version 1 and unique required IDs")
            missing_required = sorted(set(expected["required"]) - set(parsed))
            report["scope"] = {"source": "external_manifest", "required": expected["required"], "missing": missing_required}
        else:
            missing_required = []
            report["scope"] = {"source": "candidate", "required": list(parsed), "missing": []}
        rows = model.get("observations")
        if type(observation_cap) is not int or observation_cap < 1 or type(work_cap) is not int or work_cap < 1 or type(diagnostic_cap) is not int or diagnostic_cap < 1:
            raise LanguageError("schema", "Analysis limits must be positive integers")
        report["artifact_sha256"] = sha256(json.dumps(model, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        report["clock_period_ms"] = _fraction_decimal(_clock(clock))
        report["obligations"] = list(parsed)
        if rows is not None:
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise LanguageError("schema", "Observations must be an array of maps")
            if len(rows) > observation_cap:
                report["status"] = "unknown"
                report["limit"] = "observation_cap"
                report["results"] = {key: {"status": "unknown", "reason": "Observation cap exceeded",
                                           "coverage": {"triggers": 0}} for key in parsed}
                return report
            for index, row in enumerate(rows):
                for name, value in row.items():
                    if name not in properties or not _trace_value(value, properties[name]):
                        raise LanguageError("type", f"Invalid observation {index}: {name}")
        if "complete" in model and type(model["complete"]) is not bool:
            raise LanguageError("schema", "complete must be Boolean")
        work = (len(rows) if rows is not None else 0) * len(parsed) * 8
        report["work_units_bound"] = work
        for key, item in parsed.items():
            result = {"status": "pass"} if not review else _evaluate(item, rows or [], diagnostic_cap=diagnostic_cap) if rows is not None and work <= work_cap else {"status": "unknown", "reason": "Missing observations or work cap exceeded", "coverage": {"triggers": 0}}
            if "deadline_ticks" in item:
                result["deadline_ticks"] = item["deadline_ticks"]
            report["results"][key] = result
        statuses = [item["status"] for item in report["results"].values()]
        report["status"] = ("fail" if "fail" in statuses else "unknown" if "unknown" in statuses or missing_required or (review and not model.get("complete", False)) else "pass")
        return report
    except (LanguageError, KeyError, TypeError, InvalidOperation) as exc:
        report["error"] = {"code": exc.code if isinstance(exc, LanguageError) else "schema", "detail": str(exc)}
        return report
