"""Fail-closed accounting for newly produced trial events and independent oracles."""
import json
import re


def payload_size(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return {"utf8_bytes": len(text.encode()), "regex_wordpunct_v2": len(re.findall(r"\w+|[^\w\s]", text))}


def summarize_events(raw):
    events, invalid_lines = [], 0
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            invalid_lines += 1
    completed = [e for e in events if e.get("type") == "turn.completed"]
    failures = [e for e in events if e.get("type") in ("error", "turn.failed")]
    items = [e["item"] for e in events if e.get("type") == "item.completed" and isinstance(e.get("item"), dict)]
    tools = [x for x in items if x.get("type") not in ("agent_message", "reasoning", "todo_list")]
    usage = None
    if completed and all(isinstance(x.get("usage"), dict) for x in completed):
        keys = set.intersection(*(set(x["usage"]) for x in completed))
        usage = {k: sum(x["usage"][k] for x in completed) for k in sorted(keys) if all(type(x["usage"][k]) is int for x in completed)}
    return {"completed_turns": len(completed), "provider_usage": usage, "tool_calls": len(tools),
            "tool_payloads": [{"id": x.get("id"), "type": x.get("type"), "command": x.get("command"),
                               "input": payload_size(x.get("command", "")), "result": payload_size(x.get("aggregated_output", x))} for x in tools],
            "failure_events": failures, "invalid_event_lines": invalid_lines,
            "domain_question_count": None, "needless_question_count": None, "provider_confirmation_count": None,
            "question_count_note": "Independent transcript classification required; absence of a count is not zero."}


def score_completion(trial, oracle):
    if trial.get("returncode") != 0 or trial.get("timed_out") or not trial.get("completed_turns") or trial.get("failure_events"):
        return "incomplete"
    if oracle.get("artifact_check") is False or oracle.get("semantic_fidelity") is False:
        return "fail"
    if oracle.get("artifact_check") is True and oracle.get("semantic_fidelity") is True and oracle.get("independent_review") is True:
        return "pass"
    return "unreviewed"


def require_equivalent(a, b):
    for key in ("model", "effort", "service_tier", "task_sha256", "source_sha256", "timeout_seconds", "sandbox", "cli_version", "parser_sha256"):
        if key not in a or a[key] is None or a[key] != b.get(key):
            raise ValueError(f"Non-equivalent or missing condition: {key}")
    if a["service_tier"] != "default":
        raise ValueError("Only Standard/default trials are authorized")
    return True
