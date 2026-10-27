#!/usr/bin/env python3
"""Fail-closed preflight for future linked-v2 renderers. This is not a renderer/fidelity verdict."""
import re
REQUIRED={
 "ACTION":{"nodes","control_flows","object_flows","send_via","accept_payloads","fork_join","guards"},
 "STATE":{"states","hierarchy","initial","transitions","triggers","guards","effects","entry_exit"},
 "INTERCONNECTION":{"parts","ports","port_kinds","endpoint_chains","connectors","directions","visibility"},
 "SEQUENCE":{"participants","participant_types","messages","payload_types","endpoint_chains","event_order","timing_scope"}
}
TOPOLOGY={"ACTION":{"nodes","control_flows"},"STATE":{"states","transitions"},
          "INTERCONNECTION":{"parts","ports","connectors","endpoint_chains"},
          "SEQUENCE":{"participants","messages","endpoint_chains","event_order"}}
def preflight(family,record):
    if family not in REQUIRED:raise ValueError("Unsupported family")
    if record.get("origin")!="linked-native-v2":raise ValueError("Expected linked parsed-v2 facts; legacy views are not inputs")
    for name in ["parsed_model_sha256","tool_sha256"]:
        if not isinstance(record.get(name),str) or not re.fullmatch("[0-9a-f]{64}",record[name]):raise ValueError("Missing/invalid provenance: "+name)
    for name in ["id","kind","owner"]:
        if not isinstance(record.get(name),str) or not record[name]:raise ValueError("Missing selected identity: "+name)
    for name in ["unsupported","unresolved"]:
        if name not in record or not isinstance(record[name],list):raise ValueError("Missing explicit limitation inventory")
        if record[name]:raise ValueError("Unsupported or unresolved semantics")
    missing=REQUIRED[family]-record.keys()
    if missing:raise ValueError("Missing facts: "+", ".join(sorted(missing)))
    for field in REQUIRED[family]:
        audit=record[field]
        if not isinstance(audit,dict) or audit.get("status")!="resolved":raise ValueError("Unknown/unresolved fact: "+field)
        if not isinstance(audit.get("evidence"),list) or not audit["evidence"] or not all(isinstance(v,str) and v for v in audit["evidence"]):
            raise ValueError("Missing native-element evidence: "+field)
        if not isinstance(audit.get("value"),list):raise ValueError("Missing explicit fact inventory: "+field)
        if field in TOPOLOGY[family] and not audit["value"]:raise ValueError("Empty required topology: "+field)
    return {"status":"preflight-only","family":family,"rendered":False,"fidelity":"unassessed"}
