"""Offline comparison preparation. No native core, model client, or network calls.

Source anchors check a small attributed reference fixture. They do not implement
SysML semantics or establish native semantic authority. All API bindings remain
unavailable until supplied by the native owner and independently reviewed.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

ARMS = ("semantic_query_replay", "duplicated_artifacts", "deduplicated_artifact")
LIMITS = ["source declarations only", "no execution observations supplied",
          "manual qualified labels are not native IDs", "native API and independent oracle review pending"]


def wire(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return sha256(wire(value)).hexdigest()


def size(raw):
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise ValueError("Measure exact recorded bytes")
    return {"utf8_bytes": len(raw), "regex_wordpunct_v2": len(re.findall(r"\w+|[^\w\s]", raw.decode("utf-8")))}


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("Nonfinite JSON")
    result = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=reject)
    wire(result)
    return result


def snapshot(source, fixture):
    expected = fixture["source"]
    if sha256(source).hexdigest() != expected["sha256"] or len(source) != expected["bytes"]:
        raise ValueError("Source bytes do not match the pinned public fixture")
    records = {}
    for definition in fixture["facts"]:
        key = definition["id"]
        if key in records:
            raise ValueError("Duplicate reference fact ID")
        quote = definition["quote"].encode("utf-8")
        if source.count(quote) != 1:
            raise ValueError("Source anchor is missing or ambiguous: " + key)
        value = definition["value"]
        # This is fixture integrity for literal annotations, not a language parser.
        if value["kind"] in ("quantity_literal", "decimal_literal"):
            match = re.search(r"=\s*([0-9]+(?:\.[0-9]+)?)(?:\[([^\]]+)\])?;", definition["quote"])
            if not match or match[1] != value["number"]:
                raise ValueError("Literal annotation disagrees with source")
            if value["kind"] == "quantity_literal" and (match[2] or "").strip("'") != value["unit"]:
                raise ValueError("Unit annotation disagrees with source")
        start = source.index(quote)
        record = deepcopy(definition)
        record.update(source_sha256=expected["sha256"], native_id=None,
                      locator={"byte_start": start, "byte_end": start + len(quote),
                               "line_start": source[:start].count(b"\n") + 1,
                               "quote_sha256": sha256(quote).hexdigest()})
        records[key] = record
    return {"source_sha256": expected["sha256"], "authority": fixture["authority"],
            "evidence_limits": deepcopy(LIMITS), "records": records}


def selected_records(reference, task):
    keys = task["facts"]
    if len(keys) != len(set(keys)) or not keys:
        raise ValueError("Task requires distinct reference fact IDs")
    if any(key not in reference["records"] for key in keys):
        raise ValueError("Unknown source fact ID")
    return [deepcopy(reference["records"][key]) for key in keys]


def response(reference, task, arm):
    if arm not in ARMS:
        raise ValueError("Unknown comparison arm")
    records = selected_records(reference, task)
    groups = [records]
    if arm == "duplicated_artifacts":
        if len(records) < 3:
            raise ValueError("Duplicated fixture needs unique facts in both views")
        # Two task packets share one fact; each also has needed unique facts.
        # Both are read in one batch. This deliberately controlled layout is
        # declared, not presented as observed native UI/artifact behavior.
        middle = (len(records) + 1) // 2
        groups = [records[:middle], [records[0], *records[middle:]]]
    return {"source_sha256": reference["source_sha256"], "authority": reference["authority"],
            "evidence_limits": deepcopy(reference["evidence_limits"]), "arm": arm,
            "containers": [{"id": str(i), "records": deepcopy(group)} for i, group in enumerate(groups)]}


def information(packet):
    if set(packet) != {"source_sha256", "authority", "evidence_limits", "arm", "containers"} or packet["arm"] not in ARMS:
        raise ValueError("Unknown packet fields or arm")
    records, container_ids = {}, set()
    if not isinstance(packet["containers"], list) or not packet["containers"]:
        raise ValueError("Missing evidence containers")
    count = 0
    for container in packet["containers"]:
        if set(container) != {"id", "records"} or container["id"] in container_ids:
            raise ValueError("Malformed or duplicate container")
        container_ids.add(container["id"])
        if not isinstance(container["records"], list):
            raise ValueError("Records must be a list")
        for record in container["records"]:
            if record.get("source_sha256") != packet["source_sha256"]:
                raise ValueError("Mixed or stale source revisions")
            key = record["id"]
            if key in records and wire(records[key]) != wire(record):
                raise ValueError("Conflicting copies of the same fact")
            records[key] = record
            count += 1
    normalized = {key: packet[key] for key in ("source_sha256", "authority", "evidence_limits")}
    normalized["records"] = {key: records[key] for key in sorted(records)}
    return normalized, count


def equal_information(reference, task, packets):
    expected, _ = information(response(reference, task, ARMS[0]))
    rows = []
    if len(packets) != len(ARMS) or {packet["arm"] for packet in packets} != set(ARMS):
        raise ValueError("All three distinct comparison arms are required")
    for packet in packets:
        observed, count = information(packet)
        if wire(observed) != wire(expected):
            raise ValueError("Unequal information: source, values, IDs, evidence or limits differ")
        rows.append({"arm": packet["arm"], "unique_facts": len(expected["records"]),
                     "delivered_records": count, "extra_copies": count - len(expected["records"]),
                     "normalized_information_sha256": digest(observed)})
    return rows


def answer_template(reference, task):
    fields = ("id", "subject_id", "subject_id_scheme", "native_id", "predicate", "value", "source_sha256", "locator")
    return {"claims": [{key: record[key] for key in fields} for record in selected_records(reference, task)],
            "evidence_conclusion": task["evidence_conclusion"]}


def check_answer(reference, task, answer):
    expected = answer_template(reference, task)
    if not isinstance(answer, dict) or set(answer) != set(expected) or not isinstance(answer["claims"], list):
        return {"reference_checks": "fail", "reason": "Answer shape mismatch", "agentic_success": None}
    def normalize(value):
        ids = [row["id"] for row in value["claims"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate answer identity")
        return {"claims": sorted(value["claims"], key=lambda row: row["id"]),
                "evidence_conclusion": value["evidence_conclusion"]}
    try:
        correct = wire(normalize(answer)) == wire(normalize(expected))
    except (KeyError, TypeError, ValueError):
        correct = False
    return {"reference_checks": "pass" if correct else "fail", "agentic_success": None,
            "meaning_review": "pending independent review; exact claim fidelity only"}


def patch_reference(source, reference, intent):
    if sha256(source).hexdigest() != reference["source_sha256"]:
        raise ValueError("Stale source for patch oracle")
    replacements, targets = [], set()
    for edit in intent["edits"]:
        if set(edit) != {"fact_id", "before", "after", "unit"} or edit["fact_id"] in targets:
            raise ValueError("Malformed or duplicate edit target")
        targets.add(edit["fact_id"])
        fact = reference["records"].get(edit["fact_id"])
        if not fact or fact["value"].get("kind") != "quantity_literal":
            raise ValueError("Unknown or unsupported oracle target")
        if (edit["before"], edit["unit"]) != (fact["value"]["number"], fact["value"]["unit"]):
            raise ValueError("Wrong original literal or unit")
        if not isinstance(edit["after"], str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", edit["after"]):
            raise ValueError("New literal must be an exact nonnegative decimal string")
        literal = re.search(rb"=\s*([0-9]+(?:\.[0-9]+)?)", fact["quote"].encode())[1]
        offset = re.search(rb"=\s*([0-9]+(?:\.[0-9]+)?)", fact["quote"].encode()).start(1)
        start = fact["locator"]["byte_start"] + offset
        replacements.append((start, start + len(literal), edit["after"].encode()))
    candidate = source
    for start, end, value in sorted(replacements, reverse=True):
        candidate = candidate[:start] + value + candidate[end:]
    return candidate


def review_reference(source, reference, intent):
    candidate = patch_reference(source, reference, intent)
    return {"base_revision": reference["source_sha256"], "intent_sha256": digest(intent),
            "candidate_sha256": sha256(candidate).hexdigest(), "generation": 1,
            "decision": "accept", "authority": "synthetic_oracle_only_not_human_consent"}


def check_patch(source, original_after, candidate, reference, intent, supplied_review, trusted_review):
    """Compare externally collected bytes; this function never edits any model."""
    errors = []
    expected_review = review_reference(source, reference, intent)
    if wire(trusted_review) != wire(expected_review):
        raise ValueError("Oracle review does not match this pinned fixture")
    if wire(supplied_review) != wire(trusted_review):
        errors.append("review_identity_mismatch")
    if original_after != source:
        errors.append("original_changed")
    if candidate != patch_reference(source, reference, intent):
        errors.append("candidate_not_exact_authorized_literal_delta")
    return {"reference_checks": "fail" if errors else "pass", "errors": errors,
            "human_authority_authenticated": False, "native_atomicity_proved": False, "agentic_success": None}


def cost_ledger(bootstrap, task, calls, model_context_frames=None):
    """Count recorded protocol bytes, including failed attempts; never infer model usage."""
    seen, total, retries, unknown = {}, {"utf8_bytes": 0, "regex_wordpunct_v2": 0}, 0, 0
    samples = [bootstrap, task]
    for call in calls:
        if (set(call) != {"id", "request", "result", "outcome", "retry_of"}
                or not isinstance(call["id"], str) or not call["id"] or call["id"] in seen):
            raise ValueError("Malformed or duplicated call record")
        if call["outcome"] not in ("ok", "error"):
            raise ValueError("Unknown call outcome")
        if call["retry_of"] is not None:
            if call["retry_of"] not in seen or seen[call["retry_of"]] != "error":
                raise ValueError("Retry lacks a prior failed call")
            retries += 1
        seen[call["id"]] = call["outcome"]
        samples.extend([call["request"], call["result"]])
    for sample in samples:
        measured = size(sample)
        if measured is None:
            unknown += 1
        else:
            for metric in total:
                total[metric] += measured[metric]
    frames = None
    if model_context_frames:
        measured = [size(frame) for frame in model_context_frames]
        if any(frame is None for frame in measured):
            raise ValueError("Model request context frames must be complete or unavailable")
        frames = {metric: sum(row[metric] for row in measured) for metric in total}
    return {"tool_calls": len(calls), "retry_calls": retries, "unknown_payloads": unknown,
            "known_protocol_subtotal": total, "complete_protocol_total": None if unknown else total,
            "recorded_model_context_total": frames, "provider_usage": None, "billed_cost": None}


def scripted_calls(packet, retry=False):
    successful = {"id": "read-2" if retry else "read-1", "request": wire({"read": "task_packet", "arm": packet["arm"]}),
                  "result": wire(packet), "outcome": "ok", "retry_of": "read-1" if retry else None}
    if not retry:
        return [successful]
    return [{"id": "read-1", "request": wire({"read": "missing_packet", "arm": packet["arm"]}),
             "result": wire({"status": "error", "code": "UNKNOWN_SELECTOR", "recovery": "Use a listed packet; no state changed"}),
             "outcome": "error", "retry_of": None}, successful]
