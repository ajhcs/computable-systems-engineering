"""Read-only context slices and conservative changes for parsed SysML models."""

from .sysml import check_sysml

IDENTIFIED = ("concerns", "use_cases", "requirements")
ELEMENTS = ("part_definitions", "parts", "concerns", "use_cases", "actions", "states",
            "requirements", "constraints", "attributes", "events", "event_attributes")


def view_sysml(paths, short_id):
    """Retrieve one reviewed element plus the local records it depends on."""
    parsed = check_sysml(paths, syntax_only=True)
    if parsed["status"] != "pass":
        return {"status": parsed["status"], "findings": parsed["findings"],
                "parser_issues": parsed.get("parser_issues", [])}
    inventory = parsed["inventory"]
    matches = [(group, item) for group in IDENTIFIED for item in inventory[group]
               if item.get("id") == short_id]
    if len(matches) != 1:
        return {"status": "error", "detail": f"Expected one element with short ID {short_id}"}
    group, element = matches[0]
    qualified = element["qualified_name"]
    constraints = [item for item in inventory["constraints"] if item.get("requirement") == qualified]
    owners = {qualified} | {item["qualified_name"] for item in constraints}
    parts = [part for part in inventory["parts"]
             if any(subject.get("target") == part.get("qualified_name")
                    for subject in element.get("subjects", []))]
    participants = [part for part in inventory["parts"]
                    if (part.get("qualified_name") or "").startswith(qualified + "::")]
    types = {part.get("type") for part in parts}
    attributes = [item for item in inventory["attributes"] if item.get("part_definition") in types]
    events = [item for item in inventory["events"] if item.get("part_definition") in types]
    owners.update(item["qualified_name"] for item in attributes)
    owners.update(item["qualified_name"] for item in events)
    event_names = {item["qualified_name"] for item in events}
    return {"status": "pass", "claim_scope": "parsed_context_view",
            "model_sha256": parsed["model_sha256"], "selected_id": short_id,
            "selected_kind": group, "element": element,
            "constraints": constraints, "documents": [item for item in inventory["documents"]
                                                   if item.get("owner") in owners or
                                                   (item.get("owner") or "").startswith(qualified + "::")],
            "subject_parts": parts, "participants": participants,
            "subject_attributes": attributes,
            "subject_events": events,
            "event_attributes": [item for item in inventory["event_attributes"]
                                 if item.get("event") in event_names]}


def _records(inventory):
    records = {}
    for group in ELEMENTS:
        for item in inventory[group]:
            identity = item.get("id") if group in IDENTIFIED else None
            identity = identity or (item.get("event", "") + "::" + item.get("name", "")
                                    if group == "event_attributes" else item.get("qualified_name", ""))
            key = f"{group}:{identity}"
            records[key] = {name: value for name, value in item.items()
                            if name not in ("line", "source")}
    document_counts = {}
    for item in inventory["documents"]:
        base = f"documents:{item.get('owner')}:{item.get('name')}"
        ordinal = document_counts.get(base, 0)
        document_counts[base] = ordinal + 1
        records[f"{base}:{ordinal}"] = {name: value for name, value in item.items()
                                         if name not in ("line", "source")}
    return records


def _affected(changed, inventory):
    """Conservative direct dependency closure, not semantic-change proof."""
    records = _records(inventory)
    changed_set = set(changed)
    impacted = set(changed_set)
    part_definitions = {records[key].get("qualified_name") for key in changed_set
                        if key.startswith("part_definitions:") and key in records}
    for key in changed_set:
        item = records.get(key, {})
        if key.startswith(("attributes:", "events:")):
            part_definitions.add(item.get("part_definition"))
        elif key.startswith("event_attributes:"):
            event = item.get("event")
            part_definitions.update(row.get("part_definition") for row in inventory["events"]
                                    if row.get("qualified_name") == event)
    for part in inventory["parts"]:
        if part.get("type") in part_definitions or f"parts:{part.get('qualified_name')}" in changed_set:
            impacted.add(f"parts:{part['qualified_name']}")
    part_names = {key.split(":", 1)[1] for key in impacted if key.startswith("parts:")}
    for requirement in inventory["requirements"]:
        if any(subject.get("target") in part_names for subject in requirement.get("subjects", [])):
            impacted.add(f"requirements:{requirement.get('id') or requirement['qualified_name']}")
    requirement_names = {requirement["qualified_name"] for requirement in inventory["requirements"]
                         if f"requirements:{requirement.get('id') or requirement['qualified_name']}" in impacted}
    for constraint in inventory["constraints"]:
        if constraint.get("requirement") in requirement_names:
            impacted.add(f"constraints:{constraint['qualified_name']}")
    for key in changed_set:
        if key.startswith("documents:"):
            owner = records.get(key, {}).get("owner")
            for group in ("part_definitions", "attributes", "events", "requirements", "constraints",
                          "use_cases", "concerns", "actions", "states"):
                for item in inventory[group]:
                    if item.get("qualified_name") == owner:
                        impacted.add(f"{group}:{item.get('id') or owner}")
                        if group == "part_definitions":
                            for part in inventory["parts"]:
                                if part.get("type") == owner:
                                    impacted.add(f"parts:{part['qualified_name']}")
                        elif group in ("attributes", "events"):
                            for part in inventory["parts"]:
                                if part.get("type") == item.get("part_definition"):
                                    impacted.add(f"parts:{part['qualified_name']}")
    part_names = {key.split(":", 1)[1] for key in impacted if key.startswith("parts:")}
    for requirement in inventory["requirements"]:
        if any(subject.get("target") in part_names for subject in requirement.get("subjects", [])):
            impacted.add(f"requirements:{requirement.get('id') or requirement['qualified_name']}")
    impacted_requirements = {item["qualified_name"] for item in inventory["requirements"]
                             if f"requirements:{item.get('id') or item['qualified_name']}" in impacted}
    for constraint in inventory["constraints"]:
        if constraint.get("requirement") in impacted_requirements:
            impacted.add(f"constraints:{constraint['qualified_name']}")
    for constraint in inventory["constraints"]:
        if f"constraints:{constraint['qualified_name']}" in impacted:
            for requirement in inventory["requirements"]:
                if requirement["qualified_name"] == constraint.get("requirement"):
                    impacted.add(f"requirements:{requirement.get('id') or requirement['qualified_name']}")
    return sorted(impacted)


def diff_sysml(before_paths, after_paths):
    """Compare parsed record structure and text; does not decide engineering meaning."""
    before = check_sysml(before_paths, syntax_only=True)
    after = check_sysml(after_paths, syntax_only=True)
    if before["status"] != "pass" or after["status"] != "pass":
        return {"status": "error", "claim_scope": "structural_and_documentation_diff",
                "before": {"status": before["status"], "findings": before["findings"],
                           "parser_issues": before.get("parser_issues", [])},
                "after": {"status": after["status"], "findings": after["findings"],
                          "parser_issues": after.get("parser_issues", [])}}
    old, new = _records(before["inventory"]), _records(after["inventory"])
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(key for key in set(old) & set(new) if old[key] != new[key])
    if max(len(old), len(new)) > 10000 or (len(added) + len(removed) + len(changed)) * max(len(old), len(new)) > 1_000_000:
        return {"status": "unknown", "claim_scope": "structural_and_documentation_diff",
                "before_sha256": before["model_sha256"], "after_sha256": after["model_sha256"],
                "reason": "Diff impact work cap exceeded"}
    return {"status": "pass", "claim_scope": "structural_and_documentation_diff",
            "before_sha256": before["model_sha256"], "after_sha256": after["model_sha256"],
            "added": added, "removed": removed, "changed": changed,
            "potentially_affected": _affected(added + changed, after["inventory"]),
            "removed_impact": _affected(removed, before["inventory"])}
