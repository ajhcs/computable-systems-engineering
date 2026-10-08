"""Fail-closed accounting for newly produced trial events and independent oracles."""
import json
import re

ACCOUNTING_VERSION = "cse-accounting-3"
EVENT_TYPES = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
               "item.started", "item.updated", "item.completed"}


def payload_size(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return {"utf8_bytes": len(text.encode()), "regex_wordpunct_v2": len(re.findall(r"\w+|[^\w\s]", text))}


class TranscriptLifecycle:
    """One stream, sequential turns, immutable item identity and terminal states.

    The initial turn may omit its start, and items may omit their start. An
    update still opens an item. After a terminal turn event a new explicit start
    is required; terminal records can never implicitly create another turn.
    """

    def __init__(self):
        self.phase = "initial"
        self.turn = 0
        self.turn_id = None
        self.turn_ids = set()
        self.thread_seen = False
        self.items = {}
        self.open_items = set()

    def bind_turn(self, event):
        if "turn_id" not in event:
            return
        identity = event["turn_id"]
        if not isinstance(identity, str) or not identity:
            raise ValueError("Malformed turn identity")
        if self.turn_id is None:
            if identity in self.turn_ids:
                raise ValueError("Reused turn identity")
            self.turn_id = identity
            self.turn_ids.add(identity)
        elif identity != self.turn_id:
            raise ValueError("Event belongs to a different turn")

    def require_active(self, event):
        if self.phase == "closed":
            raise ValueError("Event after a terminal turn requires a new turn start")
        if self.phase == "initial":
            self.turn = 1
            self.phase = "active"
        self.bind_turn(event)

    def accept(self, event):
        kind = event["type"]
        if kind == "thread.started":
            if self.thread_seen or self.phase != "initial":
                raise ValueError("Repeated or late thread start; use one stream per transcript")
            if "thread_id" in event and (not isinstance(event["thread_id"], str) or not event["thread_id"]):
                raise ValueError("Malformed thread identity")
            self.thread_seen = True
        elif kind == "turn.started":
            if self.phase == "active":
                raise ValueError("Repeated turn start without completion")
            self.turn += 1
            self.phase, self.turn_id = "active", None
            self.bind_turn(event)
        elif kind in ("turn.completed", "turn.failed"):
            self.require_active(event)
            if self.open_items:
                raise ValueError("Turn terminated with unfinished items")
            self.phase = "closed"
        elif kind.startswith("item."):
            self.require_active(event)
            item = event["item"]
            self.bind_turn(item)
            identity = item["id"]
            previous = self.items.get(identity)
            if previous:
                item_type, turn, status = previous
                if turn != self.turn:
                    raise ValueError("Item identity reused across turns")
                if item_type != item["type"]:
                    raise ValueError("Item type changed for the same identity")
                if status == "completed":
                    raise ValueError("Item event after its terminal completion")
                if kind == "item.started":
                    raise ValueError("Repeated or out-of-order item start")
            status = "completed" if kind == "item.completed" else "open"
            self.items[identity] = (item["type"], self.turn, status)
            if status == "completed":
                self.open_items.discard(identity)
            else:
                self.open_items.add(identity)


def summarize_events(raw):
    events, errors = [], []
    lifecycle = TranscriptLifecycle()

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
            if event["type"] == "turn.completed" and event.get("usage") is not None:
                usage = event["usage"]
                if not isinstance(usage, dict) or not usage or any(type(v) is not int or v < 0 for v in usage.values()):
                    raise ValueError("Malformed usage")
            lifecycle.accept(event)
            events.append(event)
        except (ValueError, TypeError, RecursionError) as exc:
            errors.append({"line": number, "code": "invalid_event", "detail": str(exc)[:200]})
    completed = [e for e in events if e.get("type") == "turn.completed"]
    failures = [e for e in events if e.get("type") in ("error", "turn.failed")]
    transcript_status = ("invalid" if errors else "complete"
                         if completed and not failures and lifecycle.phase == "closed"
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
            "tool_calls": len(tools) if transcript_status == "complete" else None, "observed_tool_calls": len(tools),
            "tool_payloads": payloads, "logged_command_input_cost": costs,
            "failure_events": failures, "invalid_event_lines": len(errors),
            "domain_question_count": None, "needless_question_count": None, "provider_confirmation_count": None,
            "question_count_note": "Independent transcript classification required; absence of a count is not zero."}


def score_completion(trial, oracle):
    if (trial.get("accounting_version") != ACCOUNTING_VERSION or trial.get("transcript_status") != "complete"
            or trial.get("transcript_errors") or type(trial.get("invalid_event_lines")) is not int
            or trial["invalid_event_lines"] != 0 or trial.get("returncode") != 0
            or trial.get("timed_out") or type(trial.get("completed_turns")) is not int
            or trial["completed_turns"] <= 0 or trial.get("failure_events")):
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
