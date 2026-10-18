"""Documentary function-tree/sequence structure; never a behavioral or semantic proof."""

from collections import Counter
from hashlib import sha256
import json
import math
import re

VERSION = "cse-views-1.0"
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
UNITS = {"millisecond", "milliseconds", "second", "seconds", "minute", "minutes", "hour", "hours"}


def _object(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise ValueError(f"Expected fields {sorted(required)}; optional {sorted(optional)}")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _id(value):
    return isinstance(value, str) and bool(ID.fullmatch(value))


def _ids(value):
    return isinstance(value, list) and all(_id(item) for item in value) and len(set(value)) == len(value)


def _integer(value):
    return type(value) is int and value >= 0


def _bounds(value):
    _object(value, (), ("min", "max"))
    if not value or any(not _integer(n) for n in value.values()) or value.get("min", 0) > value.get("max", math.inf):
        raise ValueError("Counts need nonnegative integer min/max with min <= max")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key}")
        result[key] = value
    return result


def _profile(profile):
    if profile is None:
        return []
    _object(profile, ("version", "views"))
    if type(profile["version"]) is not int or profile["version"] != 1 or not isinstance(profile["views"], list):
        raise ValueError("View profile needs version 1 and views list")
    seen = set()
    for entry in profile["views"]:
        _object(entry, ("id", "kind"), ("required_levels", "required_ids", "level_counts", "child_counts", "require_timing", "exceptions"))
        if not _id(entry["id"]) or entry["id"] in seen or entry["kind"] not in ("function_tree", "sequence"):
            raise ValueError("Profile views need unique IDs and supported kinds")
        seen.add(entry["id"])
        if "required_ids" in entry and not _ids(entry["required_ids"]):
            raise ValueError("required_ids must contain unique IDs")
        if entry["kind"] == "function_tree":
            if "require_timing" in entry:
                raise ValueError("require_timing applies only to sequences")
            levels = entry.get("required_levels", [])
            if not isinstance(levels, list) or not all(_integer(n) for n in levels) or len(set(levels)) != len(levels):
                raise ValueError("required_levels needs unique nonnegative integers")
            for field in ("level_counts", "child_counts"):
                values = entry.get(field, {})
                if not isinstance(values, dict):
                    raise ValueError(f"{field} must be an object")
                for target, bounds in values.items():
                    if not isinstance(target, str) or not (re.fullmatch(r"0|[1-9][0-9]*", target) if field == "level_counts" else _id(target)):
                        raise ValueError(f"Invalid {field} target")
                    _bounds(bounds)
        else:
            if set(entry) & {"required_levels", "level_counts", "child_counts"}:
                raise ValueError("Hierarchy constraints apply only to function trees")
            if "require_timing" in entry and type(entry["require_timing"]) is not bool:
                raise ValueError("require_timing must be Boolean")
        exceptions = entry.get("exceptions", [])
        if not isinstance(exceptions, list):
            raise ValueError("exceptions must be a list")
        exception_keys = set()
        for exception in exceptions:
            _object(exception, ("rule", "target", "rationale"))
            rule, target = exception["rule"], exception["target"]
            allowed = {"required_level", "level_count", "child_count", "required_id"} if entry["kind"] == "function_tree" else {"timing", "required_id"}
            if not isinstance(rule, str) or rule not in allowed or not _text(target) or not _text(exception["rationale"]):
                raise ValueError("Exceptions need applicable rule, target, and nonempty rationale")
            key = (rule, target)
            if key in exception_keys:
                raise ValueError("Duplicate exception")
            exception_keys.add(key)
    return profile["views"]


def _workflow(inventory):
    """Read only the existing identity/hierarchy surface, not a workflow verdict."""
    docs = [doc for doc in inventory["documents"] if doc.get("name") == "cseWorkflow"]
    if not docs:
        return None
    if len(docs) != 1:
        raise ValueError("Reconciliation needs exactly one cseWorkflow block")
    lines = docs[0]["body"].strip().splitlines()
    if not lines or lines[0].strip() != "CSE-WORKFLOW/1.0":
        raise ValueError("Unsupported workflow documentation header for reconciliation")
    record = json.loads("\n".join(lines[1:]), object_pairs_hook=_unique_object,
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite {value}")))
    _object(record, ("version", "question", "sources", "elements", "relations", "workflows", "decisions", "questions", "trade_studies", "evidence"))
    if record["version"] != "workflow-1.0" or any(not isinstance(record[field], dict) for field in record if field != "version"):
        raise ValueError("Unsupported workflow version or container shape for reconciliation")
    for key, element in record["elements"].items():
        _object(element, ("kind", "native_name", "label", "description", "basis", "status"))
        if not _id(key) or not _text(element["kind"]) or not _text(element["native_name"]):
            raise ValueError("Malformed workflow element identity for reconciliation")
    for key, relation in record["relations"].items():
        _object(relation, ("kind", "from", "to", "basis", "label"))
        if not _id(key) or not _text(relation["kind"]) or any(not _id(relation[end]) or relation[end] not in record["elements"] for end in ("from", "to")):
            raise ValueError("Malformed workflow relation identity for reconciliation")
    return record


def _reconcile_tree(nodes, workflow):
    """Compare selected native identities and directed edges; permit scoped context."""
    functions = {}
    for key, element in workflow["elements"].items():
        if element["kind"] == "function":
            functions.setdefault(element["native_name"], []).append(key)
    for node in nodes.values():
        matches = functions.get(node["element"], [])
        if len(matches) != 1 or matches[0] != node["id"]:
            raise ValueError(f"{node['id']} must use the unique existing workflow function ID for {node['element']}")
    expected = {(node["parent"], node["id"]) for node in nodes.values() if node["parent"] is not None}
    edges = [(relation["from"], relation["to"]) for relation in workflow["relations"].values()
             if relation["kind"] == "decomposes" and relation["to"] in nodes
             and (nodes[relation["to"]]["parent"] is not None or relation["from"] in nodes)]
    if set(edges) != expected or len(edges) != len(set(edges)):
        raise ValueError("View parent links conflict with existing workflow decomposes edges in selected scope")
    return {"claim_scope": "selected_workflow_function_identities_and_decomposition_edges",
            "status": "pass", "omitted_children": sorted({relation["to"] for relation in workflow["relations"].values()
                if relation["kind"] == "decomposes" and relation["from"] in nodes and relation["to"] not in nodes})}


def check_views(inventory, profile=None):
    """Check package-owned cseViews docs against native bindings and optional task scope."""
    report = {"status": "pass", "checker_version": VERSION,
              "claim_scope": "documentary_view_structure", "findings": [], "views": [],
              "exceptions": [], "human_review": ["Functions express actions; verb-object names are recommended.",
                  "Assess decomposition adequacy and exchange meaning against the task and source.",
                  "Counts, text, bindings, and rationale do not establish completeness, approval, or behavior."]}
    def issue(code, detail, view=None, status="fail"):
        report["findings"].append({"code": code, "detail": detail, **({"view": view} if view else {})})
        rank = {"pass": 0, "unsupported": 1, "unknown": 2, "fail": 3, "error": 4}
        if rank[status] > rank[report["status"]]:
            report["status"] = status
    try:
        requirements = _profile(profile)
        if profile is not None:
            report["profile_sha256"] = sha256(json.dumps(profile, sort_keys=True, allow_nan=False).encode()).hexdigest()
        docs = [doc for doc in inventory["documents"] if doc.get("name") == "cseViews"]
        if not docs:
            if requirements:
                issue("view_missing", "No cseViews block for requested views", status="unknown")
            return report
        if len(docs) != 1 or docs[0].get("owner_kind") != "Package":
            raise ValueError("Exactly one package-owned cseViews block is supported per supplied model set")
        lines = docs[0]["body"].strip().splitlines()
        if not lines or lines[0].strip() != "CSE-VIEWS/1.0":
            raise ValueError("Expected CSE-VIEWS/1.0 header")
        data = json.loads("\n".join(lines[1:]), object_pairs_hook=_unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite {value}")))
        _object(data, ("views",))
        if not isinstance(data["views"], list):
            raise ValueError("views must be a list")
        workflow = _workflow(inventory)
        views = {}
        for view in data["views"]:
            if not isinstance(view, dict) or not _id(view.get("id")) or not _text(view.get("kind")):
                raise ValueError("Each view needs an ID and kind")
            key = view["id"]
            if key in views:
                issue("duplicate_id", f"Duplicate view ID {key}", key)
                continue
            views[key] = view
        # Native bindings must be unique and of the declared role. No surrogate elements.
        actions = Counter(item.get("qualified_name") for item in inventory["actions"])
        parts = Counter(item.get("qualified_name") for item in inventory["parts"])
        for key, view in views.items():
            kind = view["kind"]
            report["views"].append({"id": key, "kind": kind})
            if kind == "function_tree":
                _object(view, ("id", "kind", "nodes"))
                if not isinstance(view["nodes"], list):
                    raise ValueError("nodes must be a list")
                nodes, bindings = {}, set()
                for node in view["nodes"]:
                    _object(node, ("id", "element", "level", "parent"))
                    if not _id(node["id"]) or not _text(node["element"]) or not _integer(node["level"]) or not (node["parent"] is None or _id(node["parent"])):
                        raise ValueError("Node needs ID, native action element, nonnegative level, and parent ID/null")
                    if node["id"] in nodes:
                        issue("duplicate_id", f"Duplicate node ID {node['id']}", key)
                    nodes[node["id"]] = node
                    if actions[node["element"]] != 1:
                        issue("function_binding", f"{node['id']} must bind uniquely to a native action", key)
                    if node["element"] in bindings:
                        issue("duplicate_binding", f"Repeated function element {node['element']}", key)
                    bindings.add(node["element"])
                roots = [node for node in nodes.values() if node["parent"] is None]
                if len(roots) != 1 or roots[0]["level"] != 0:
                    issue("root", "Function tree needs exactly one explicit level-0 root", key)
                for node in nodes.values():
                    parent = nodes.get(node["parent"])
                    if node["parent"] is not None:
                        if parent is None:
                            issue("orphan", f"{node['id']} has missing parent {node['parent']}", key)
                        elif node["level"] != parent["level"] + 1:
                            issue("level", f"{node['id']} must be one level below its parent", key)
                # Iterative traversal also catches disconnected cycles without recursion limits.
                completed = set()
                for start in nodes:
                    path, current = set(), start
                    while current in nodes and current not in completed:
                        if current in path:
                            issue("cycle", f"Parent cycle includes {current}", key)
                            break
                        path.add(current)
                        current = nodes[current]["parent"]
                    completed.update(path)
                if workflow is not None:
                    try:
                        reconciliation = _reconcile_tree(nodes, workflow)
                        report["views"][-1]["workflow_reconciliation"] = reconciliation
                    except ValueError as exc:
                        issue("workflow_conflict", str(exc), key)
            elif kind == "sequence":
                _object(view, ("id", "kind", "participants", "exchanges"))
                if not isinstance(view["participants"], list) or not isinstance(view["exchanges"], list):
                    raise ValueError("participants and exchanges must be lists")
                participants, bindings = set(), set()
                for participant in view["participants"]:
                    _object(participant, ("id", "element"))
                    if not _id(participant["id"]) or not _text(participant["element"]):
                        raise ValueError("Participant needs ID and native part usage element")
                    if participant["id"] in participants:
                        issue("duplicate_id", f"Duplicate participant ID {participant['id']}", key)
                    participants.add(participant["id"])
                    if parts[participant["element"]] != 1:
                        issue("participant_binding", f"{participant['id']} must bind uniquely to a native part usage", key)
                    if participant["element"] in bindings:
                        issue("duplicate_binding", f"Repeated participant element {participant['element']}", key)
                    bindings.add(participant["element"])
                if not participants or not view["exchanges"]:
                    issue("sequence_empty", "Sequence needs participants and ordered exchanges", key)
                seen = set(participants)
                for exchange in view["exchanges"]:
                    _object(exchange, ("id", "from", "to", "message"), ("timing",))
                    if not _id(exchange["id"]):
                        raise ValueError("Exchange needs an ID")
                    if exchange["id"] in seen:
                        issue("duplicate_id", f"Duplicate sequence ID {exchange['id']}", key)
                    seen.add(exchange["id"])
                    for endpoint in ("from", "to"):
                        if not _id(exchange[endpoint]) or exchange[endpoint] not in participants:
                            issue("endpoint", f"{exchange['id']} has undeclared {endpoint} participant", key)
                    if not _text(exchange["message"]):
                        issue("exchange_text", f"{exchange['id']} needs a nonempty message; meaning needs human review", key)
                    if "timing" in exchange:
                        timing = exchange["timing"]
                        _object(timing, ("min", "max", "unit", "basis"))
                        if (any(type(timing[n]) not in (int, float) or not math.isfinite(timing[n]) or timing[n] < 0 for n in ("min", "max"))
                                or timing["min"] > timing["max"] or not isinstance(timing["unit"], str) or timing["unit"] not in UNITS or not _text(timing["basis"])):
                            issue("timing_range", f"{exchange['id']} needs finite 0 <= min <= max, duration unit, and timing basis", key)
            else:
                issue("view_kind", f"Unsupported view kind {kind}; activity flow is distinct from decomposition and sequence", key, "unsupported")
        for requirement in requirements:
            key = requirement["id"]
            view = views.get(key)
            if view is None:
                issue("view_missing", "Requested view is absent", key, "unknown")
                continue
            if view["kind"] != requirement["kind"]:
                issue("view_kind", "View does not match requested kind", key)
                continue
            exceptions = {(e["rule"], e["target"]): e for e in requirement.get("exceptions", [])}
            used = set()
            def gap(rule, target, detail):
                exception = exceptions.get((rule, str(target)))
                if exception:
                    used.add((rule, str(target)))
                    report["exceptions"].append({"view": key, **exception})
                else:
                    issue(rule, detail, key, "unknown")
            if view["kind"] == "function_tree":
                nodes = view["nodes"]
                ids = {node["id"] for node in nodes}
                levels = Counter(node["level"] for node in nodes)
                children = Counter(node["parent"] for node in nodes)
                for level in requirement.get("required_levels", []):
                    if level not in levels:
                        gap("required_level", level, f"Requested level {level} is absent")
                for field, counts, rule in (("level_counts", levels, "level_count"), ("child_counts", children, "child_count")):
                    for target, bounds in requirement.get(field, {}).items():
                        count = counts[int(target) if field == "level_counts" else target]
                        if field == "child_counts" and target not in ids:
                            gap("child_count", target, f"Requested parent {target} is absent")
                        elif not bounds.get("min", 0) <= count <= bounds.get("max", math.inf):
                            gap(rule, target, f"{field} target {target}: count {count} outside {bounds}")
            else:
                ids = {item["id"] for group in ("participants", "exchanges") for item in view[group]}
                if requirement.get("require_timing", False):
                    for exchange in view["exchanges"]:
                        if "timing" not in exchange:
                            gap("timing", exchange["id"], f"{exchange['id']} lacks requested timing")
            for expected in requirement.get("required_ids", []):
                if expected not in ids:
                    gap("required_id", expected, f"Requested ID {expected} is absent")
            for unused in sorted(set(exceptions) - used):
                issue("unused_exception", f"Exception {unused} did not justify an actual gap", key, "error")
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        issue("view_contract", str(exc), status="error")
    return report
