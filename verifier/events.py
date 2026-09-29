"""Exact, correlated event-response obligations over a finite observation window."""

from decimal import Decimal, InvalidOperation
from fractions import Fraction
import re

NAME = r"[A-Za-z][A-Za-z0-9_]*"
NUMBER = r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
CLAUSE = re.compile(
    rf"Each (?P<subject>{NAME})\.(?P<trigger>{NAME}) shall within (?P<duration>{NUMBER}) "
    rf"(?P<unit>milliseconds?|seconds?|minutes?) have (?P<response_subject>{NAME})\."
    rf"(?P<response>{NAME}) with matching (?P<correlation>{NAME})\.\Z"
)
MILLIS = {"millisecond": 1, "second": 1000, "minute": 60000}


class EventError(ValueError):
    pass


def _quantity(raw, unit):
    if not isinstance(raw, str) or len(raw) > 64 or not re.fullmatch(NUMBER, raw):
        raise EventError("Time must be a nonnegative exact decimal string")
    if not isinstance(unit, str) or (unit[:-1] if unit.endswith("s") else unit) not in MILLIS:
        raise EventError("Unsupported time unit")
    base_unit = unit[:-1] if unit.endswith("s") else unit
    try:
        value = Fraction(Decimal(raw)) * MILLIS[base_unit]
    except InvalidOperation as exc:
        raise EventError("Invalid time value") from exc
    if value.numerator.bit_length() > 1024:
        raise EventError("Time value exceeds computation bound")
    return value


def parse_event_clause(sentence):
    if not isinstance(sentence, str):
        raise EventError("Event clause must be text")
    match = CLAUSE.fullmatch(sentence)
    if not match:
        raise EventError("Event clause does not match CSE-EVENT/2.0 grammar")
    result = match.groupdict()
    if result["subject"] != result["response_subject"]:
        raise EventError("Trigger and response must name the same bound subject")
    result["duration_ms"] = _quantity(result["duration"], result["unit"])
    if result["duration_ms"] <= 0:
        raise EventError("Deadline must be positive")
    return result


def check_event_trace(clause, evidence, *, trigger_path, response_path,
                      event_cap=10000, diagnostic_cap=8):
    """One distinct correlation ID per trigger; one later response per ID."""
    records = evidence.get("events")
    horizon = evidence.get("observed_until")
    if not isinstance(records, list) or not isinstance(horizon, dict) or set(horizon) != {"time", "unit"}:
        raise EventError("Event evidence needs events and observed_until")
    if type(event_cap) is not int or event_cap < 1 or type(diagnostic_cap) is not int or diagnostic_cap < 1:
        raise EventError("Event limits must be positive integers")
    if len(records) > event_cap:
        return {"status": "unknown", "reason": "Event count cap exceeded", "coverage": {"triggers": 0}}
    observed_until = _quantity(horizon["time"], horizon["unit"])
    complete = evidence["complete"]
    correlation = clause["correlation"]
    pending = {}
    seen = set()
    matched = 0
    unmatched_responses = 0
    prior_time = None
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not {"event", "time", "unit", correlation} <= set(record):
            raise EventError(f"Event {index} is missing required fields")
        name = record["event"]
        identity = record[correlation]
        if not isinstance(name, str) or name not in (trigger_path, response_path):
            raise EventError(f"Event {index} does not bind to this requirement")
        if not isinstance(identity, str) or not identity or len(identity) > 128:
            raise EventError(f"Event {index} needs a bounded nonempty correlation ID")
        time = _quantity(record["time"], record["unit"])
        if prior_time is not None and time < prior_time:
            raise EventError("Events must be ordered by nondecreasing time")
        if time > observed_until:
            raise EventError("Event occurs after observed_until")
        prior_time = time
        if name == trigger_path:
            if identity in seen:
                raise EventError(f"Repeated trigger correlation ID: {identity}")
            seen.add(identity)
            pending[identity] = (index, time)
        elif identity in pending:
            start_index, start_time = pending[identity]
            if time <= start_time + clause["duration_ms"]:
                del pending[identity]
                matched += 1
            else:
                unmatched_responses += 1
        else:
            unmatched_responses += 1
    coverage = {"triggers": len(seen), "matched": matched,
                "unmatched_responses": unmatched_responses}
    if not seen:
        return {"status": "unknown", "coverage": coverage, "reason": "No trigger event observed"}
    failures, unresolved = [], []
    for identity, (index, start) in pending.items():
        item = {"trigger_index": index, "correlation_id": identity}
        if complete and observed_until >= start + clause["duration_ms"]:
            failures.append(item)
        else:
            unresolved.append(item)
    if failures:
        return {"status": "fail", "coverage": coverage, "counterexample": failures[0],
                "failure_count": len(failures), "failure_examples": failures[:diagnostic_cap]}
    if unresolved or not complete:
        return {"status": "unknown", "coverage": coverage,
                "reason": "Pending event obligations or incomplete observation window",
                "pending_count": len(unresolved), "pending": unresolved[:diagnostic_cap]}
    return {"status": "pass", "coverage": coverage}
