"""Fail-closed accounting for newly produced trial events and independent oracles."""
import json
import re

ACCOUNTING_VERSION = "cse-accounting-2"
EVENT_TYPES = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
               "item.started", "item.updated", "item.completed"}


def payload_size(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return {"utf8_bytes": len(text.encode()), "regex_wordpunct_v2": len(re.findall(r"\w+|[^\w\s]", text))}


def summarize_events(raw):
    events, errors = [], []
    seen_completed = set()
    open_items = set()
    open_turn = False

    def reject(value):
        raise ValueError(f"Nonfinite JSON: {value}")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate event field")
            result[key] = value
        return result

    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for number, line in enumerate(lines, 1):
        try:
            event = json.loads(line, parse_constant=reject, object_pairs_hook=unique)
            json.dumps(event, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if not isinstance(event, dict) or event.get("type") not in EVENT_TYPES:
                raise ValueError("Unknown or malformed event")
            if event["type"].startswith("item."):
                item = event.get("item")
                if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k] for k in ("id", "type")):
                    raise ValueError("Malformed item event")
                if event["type"] == "item.completed":
                    if item["id"] in seen_completed:
                        raise ValueError("Duplicate completed item")
                    seen_completed.add(item["id"])
                    open_items.discard(item["id"])
                elif event["type"] == "item.started":
                    if item["id"] in open_items or item["id"] in seen_completed:
                        raise ValueError("Repeated item start")
                    open_items.add(item["id"])
            if event["type"] == "turn.completed" and event.get("usage") is not None:
                usage = event["usage"]
                if not isinstance(usage, dict) or not usage or any(type(v) is not int or v < 0 for v in usage.values()):
                    raise ValueError("Malformed usage")
            if event["type"] == "turn.started":
                if open_turn:
                    raise ValueError("Repeated turn start without completion")
                open_turn = True
            elif event["type"] in ("turn.completed", "turn.failed"):
                open_turn = False
            events.append(event)
        except (ValueError, TypeError, RecursionError) as exc:
            errors.append({"line": number, "code": "invalid_event", "detail": str(exc)[:200]})
    completed = [e for e in events if e.get("type") == "turn.completed"]
    failures = [e for e in events if e.get("type") in ("error", "turn.failed")]
    transcript_status = ("invalid" if errors else "complete"
                         if completed and not failures and not open_items and not open_turn
                         else "incomplete")
    items = [e["item"] for e in events if e.get("type") == "item.completed" and isinstance(e.get("item"), dict)]
    tools = [x for x in items if x.get("type") not in ("agent_message", "reasoning", "todo_list")]
    usage = None
    if transcript_status == "complete" and all(isinstance(x.get("usage"), dict) for x in completed):
        keys = set.intersection(*(set(x["usage"]) for x in completed))
        usage = {k: sum(x["usage"][k] for x in completed) for k in sorted(keys) if all(type(x["usage"][k]) is int for x in completed)}
    payloads = []
    for item in tools:
        command = item.get("command") if item["type"] == "command_execution" else None
        if not isinstance(command, str):
            command = None
        output = item.get("aggregated_output")
        payloads.append({"id": item["id"], "type": item["type"], "command": command,
                         "input": payload_size(command) if command is not None else None,
                         "input_scope": "logged_command_text" if command is not None else "unavailable_in_cli_event",
                         "result": payload_size(output if isinstance(output, str) else item),
                         "result_scope": "logged_aggregated_output" if isinstance(output, str) else "logged_completion_event"})
    known = [item["input"] for item in payloads if item["input"] is not None]
    missing = len(payloads) - len(known)
    costs = {"scope": "Logged command text only, not complete tool arguments or billed tokens",
             "known_tool_inputs": len(known), "unknown_tool_inputs": missing}
    for metric in ("utf8_bytes", "regex_wordpunct_v2"):
        subtotal = sum(item[metric] for item in known)
        costs["known_" + metric] = subtotal
        costs["all_tools_" + metric] = subtotal if not missing and transcript_status == "complete" else None
    return {"accounting_version": ACCOUNTING_VERSION,
            "transcript_status": transcript_status,
            "transcript_errors": errors,
            "completed_turns": len(completed), "provider_usage": usage,
            "tool_calls": len(tools) if not errors else None, "observed_tool_calls": len(tools),
            "tool_payloads": payloads, "logged_command_input_cost": costs,
            "failure_events": failures, "invalid_event_lines": len(errors),
            "domain_question_count": None, "needless_question_count": None, "provider_confirmation_count": None,
            "question_count_note": "Independent transcript classification required; absence of a count is not zero."}


def score_completion(trial, oracle):
    if (trial.get("transcript_status") != "complete" or type(trial.get("invalid_event_lines")) is not int
            or trial["invalid_event_lines"] != 0 or trial.get("returncode") != 0
            or trial.get("timed_out") or not trial.get("completed_turns") or trial.get("failure_events")):
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
