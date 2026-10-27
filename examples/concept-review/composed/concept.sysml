package 'Composed' {
  part def 'WorkflowElement';
  part 'A_BORROWER' : 'WorkflowElement';
  action 'F_ASSESS';
  action 'F_DETAIL_0';
  action 'F_DETAIL_1';
  action 'F_DETAIL_10';
  action 'F_DETAIL_11';
  action 'F_DETAIL_12';
  action 'F_DETAIL_13';
  action 'F_DETAIL_14';
  action 'F_DETAIL_15';
  action 'F_DETAIL_16';
  action 'F_DETAIL_17';
  action 'F_DETAIL_18';
  action 'F_DETAIL_19';
  action 'F_DETAIL_2';
  action 'F_DETAIL_20';
  action 'F_DETAIL_21';
  action 'F_DETAIL_22';
  action 'F_DETAIL_23';
  action 'F_DETAIL_24';
  action 'F_DETAIL_25';
  action 'F_DETAIL_26';
  action 'F_DETAIL_27';
  action 'F_DETAIL_28';
  action 'F_DETAIL_29';
  action 'F_DETAIL_3';
  action 'F_DETAIL_30';
  action 'F_DETAIL_31';
  action 'F_DETAIL_32';
  action 'F_DETAIL_33';
  action 'F_DETAIL_34';
  action 'F_DETAIL_35';
  action 'F_DETAIL_36';
  action 'F_DETAIL_37';
  action 'F_DETAIL_38';
  action 'F_DETAIL_39';
  action 'F_DETAIL_4';
  action 'F_DETAIL_40';
  action 'F_DETAIL_41';
  action 'F_DETAIL_42';
  action 'F_DETAIL_43';
  action 'F_DETAIL_44';
  action 'F_DETAIL_45';
  action 'F_DETAIL_46';
  action 'F_DETAIL_47';
  action 'F_DETAIL_48';
  action 'F_DETAIL_49';
  action 'F_DETAIL_5';
  action 'F_DETAIL_50';
  action 'F_DETAIL_6';
  action 'F_DETAIL_7';
  action 'F_DETAIL_8';
  action 'F_DETAIL_9';
  action 'F_ISSUE';
  action 'F_QUALIFY';
  action 'F_RESTORE';
  action 'F_WITHDRAW';
  concern 'K_SERVICE';
  concern 'N_ACCESS';
  part 'R_APP' : 'WorkflowElement';
  part 'R_BENCH' : 'WorkflowElement';
  part 'R_DESK' : 'WorkflowElement';
  part 'R_KIT' : 'WorkflowElement';
  part 'R_PROC' : 'WorkflowElement';
  part 'R_STORE' : 'WorkflowElement';
  part 'R_TECH' : 'WorkflowElement';
  part 'SYS' : 'WorkflowElement';
  action 'S_FAULT';
  action 'S_MAINT';
  action 'S_NORMAL';
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.1
{
  "decisions": {},
  "elements": {
    "A_BORROWER": {
      "basis": "SYN",
      "description": "External requester and reporter of tool faults.",
      "kind": "actor",
      "label": "Borrower",
      "native_name": "Composed::A_BORROWER",
      "status": "proposed"
    },
    "F_ASSESS": {
      "basis": "SYN",
      "description": "Transform a request and tool status into an availability decision.",
      "kind": "function",
      "label": "Assess availability",
      "native_name": "Composed::F_ASSESS",
      "status": "proposed"
    },
    "F_DETAIL_0": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 0",
      "native_name": "Composed::F_DETAIL_0",
      "status": "proposed"
    },
    "F_DETAIL_1": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 1",
      "native_name": "Composed::F_DETAIL_1",
      "status": "proposed"
    },
    "F_DETAIL_10": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 10",
      "native_name": "Composed::F_DETAIL_10",
      "status": "proposed"
    },
    "F_DETAIL_11": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 11",
      "native_name": "Composed::F_DETAIL_11",
      "status": "proposed"
    },
    "F_DETAIL_12": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 12",
      "native_name": "Composed::F_DETAIL_12",
      "status": "proposed"
    },
    "F_DETAIL_13": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 13",
      "native_name": "Composed::F_DETAIL_13",
      "status": "proposed"
    },
    "F_DETAIL_14": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 14",
      "native_name": "Composed::F_DETAIL_14",
      "status": "proposed"
    },
    "F_DETAIL_15": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 15",
      "native_name": "Composed::F_DETAIL_15",
      "status": "proposed"
    },
    "F_DETAIL_16": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 16",
      "native_name": "Composed::F_DETAIL_16",
      "status": "proposed"
    },
    "F_DETAIL_17": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 17",
      "native_name": "Composed::F_DETAIL_17",
      "status": "proposed"
    },
    "F_DETAIL_18": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 18",
      "native_name": "Composed::F_DETAIL_18",
      "status": "proposed"
    },
    "F_DETAIL_19": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 19",
      "native_name": "Composed::F_DETAIL_19",
      "status": "proposed"
    },
    "F_DETAIL_2": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 2",
      "native_name": "Composed::F_DETAIL_2",
      "status": "proposed"
    },
    "F_DETAIL_20": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 20",
      "native_name": "Composed::F_DETAIL_20",
      "status": "proposed"
    },
    "F_DETAIL_21": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 21",
      "native_name": "Composed::F_DETAIL_21",
      "status": "proposed"
    },
    "F_DETAIL_22": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 22",
      "native_name": "Composed::F_DETAIL_22",
      "status": "proposed"
    },
    "F_DETAIL_23": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 23",
      "native_name": "Composed::F_DETAIL_23",
      "status": "proposed"
    },
    "F_DETAIL_24": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 24",
      "native_name": "Composed::F_DETAIL_24",
      "status": "proposed"
    },
    "F_DETAIL_25": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 25",
      "native_name": "Composed::F_DETAIL_25",
      "status": "proposed"
    },
    "F_DETAIL_26": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 26",
      "native_name": "Composed::F_DETAIL_26",
      "status": "proposed"
    },
    "F_DETAIL_27": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 27",
      "native_name": "Composed::F_DETAIL_27",
      "status": "proposed"
    },
    "F_DETAIL_28": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 28",
      "native_name": "Composed::F_DETAIL_28",
      "status": "proposed"
    },
    "F_DETAIL_29": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 29",
      "native_name": "Composed::F_DETAIL_29",
      "status": "proposed"
    },
    "F_DETAIL_3": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 3",
      "native_name": "Composed::F_DETAIL_3",
      "status": "proposed"
    },
    "F_DETAIL_30": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 30",
      "native_name": "Composed::F_DETAIL_30",
      "status": "proposed"
    },
    "F_DETAIL_31": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 31",
      "native_name": "Composed::F_DETAIL_31",
      "status": "proposed"
    },
    "F_DETAIL_32": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 32",
      "native_name": "Composed::F_DETAIL_32",
      "status": "proposed"
    },
    "F_DETAIL_33": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 33",
      "native_name": "Composed::F_DETAIL_33",
      "status": "proposed"
    },
    "F_DETAIL_34": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 34",
      "native_name": "Composed::F_DETAIL_34",
      "status": "proposed"
    },
    "F_DETAIL_35": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 35",
      "native_name": "Composed::F_DETAIL_35",
      "status": "proposed"
    },
    "F_DETAIL_36": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 36",
      "native_name": "Composed::F_DETAIL_36",
      "status": "proposed"
    },
    "F_DETAIL_37": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 37",
      "native_name": "Composed::F_DETAIL_37",
      "status": "proposed"
    },
    "F_DETAIL_38": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 38",
      "native_name": "Composed::F_DETAIL_38",
      "status": "proposed"
    },
    "F_DETAIL_39": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 39",
      "native_name": "Composed::F_DETAIL_39",
      "status": "proposed"
    },
    "F_DETAIL_4": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 4",
      "native_name": "Composed::F_DETAIL_4",
      "status": "proposed"
    },
    "F_DETAIL_40": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 40",
      "native_name": "Composed::F_DETAIL_40",
      "status": "proposed"
    },
    "F_DETAIL_41": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 41",
      "native_name": "Composed::F_DETAIL_41",
      "status": "proposed"
    },
    "F_DETAIL_42": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 42",
      "native_name": "Composed::F_DETAIL_42",
      "status": "proposed"
    },
    "F_DETAIL_43": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 43",
      "native_name": "Composed::F_DETAIL_43",
      "status": "proposed"
    },
    "F_DETAIL_44": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 44",
      "native_name": "Composed::F_DETAIL_44",
      "status": "proposed"
    },
    "F_DETAIL_45": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 45",
      "native_name": "Composed::F_DETAIL_45",
      "status": "proposed"
    },
    "F_DETAIL_46": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 46",
      "native_name": "Composed::F_DETAIL_46",
      "status": "proposed"
    },
    "F_DETAIL_47": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 47",
      "native_name": "Composed::F_DETAIL_47",
      "status": "proposed"
    },
    "F_DETAIL_48": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 48",
      "native_name": "Composed::F_DETAIL_48",
      "status": "proposed"
    },
    "F_DETAIL_49": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 49",
      "native_name": "Composed::F_DETAIL_49",
      "status": "proposed"
    },
    "F_DETAIL_5": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 5",
      "native_name": "Composed::F_DETAIL_5",
      "status": "proposed"
    },
    "F_DETAIL_50": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 50",
      "native_name": "Composed::F_DETAIL_50",
      "status": "proposed"
    },
    "F_DETAIL_6": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 6",
      "native_name": "Composed::F_DETAIL_6",
      "status": "proposed"
    },
    "F_DETAIL_7": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 7",
      "native_name": "Composed::F_DETAIL_7",
      "status": "proposed"
    },
    "F_DETAIL_8": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 8",
      "native_name": "Composed::F_DETAIL_8",
      "status": "proposed"
    },
    "F_DETAIL_9": {
      "basis": "SYN",
      "description": "Proposed synthetic decomposition for bounded composition testing.",
      "kind": "function",
      "label": "Detailed support activity 9",
      "native_name": "Composed::F_DETAIL_9",
      "status": "proposed"
    },
    "F_ISSUE": {
      "basis": "SYN",
      "description": "Transform an agreed checkout into a handover record and return instructions.",
      "kind": "function",
      "label": "Record handover",
      "native_name": "Composed::F_ISSUE",
      "status": "proposed"
    },
    "F_QUALIFY": {
      "basis": "SYN",
      "description": "Produce readiness observations using the proposed kit; actual acceptance criteria are unresolved.",
      "kind": "function",
      "label": "Evaluate readiness",
      "native_name": "Composed::F_QUALIFY",
      "status": "proposed"
    },
    "F_RESTORE": {
      "basis": "SYN",
      "description": "Perform proposed maintenance using a provider, procedure and service bench.",
      "kind": "function",
      "label": "Maintain the tool",
      "native_name": "Composed::F_RESTORE",
      "status": "proposed"
    },
    "F_WITHDRAW": {
      "basis": "SYN",
      "description": "Transform a fault report into a withdrawal status and maintenance work record.",
      "kind": "function",
      "label": "Withdraw a faulted tool",
      "native_name": "Composed::F_WITHDRAW",
      "status": "proposed"
    },
    "K_SERVICE": {
      "basis": "SYN",
      "description": "One candidate; no selection or operational acceptance is asserted.",
      "kind": "concept",
      "label": "Supported lending service",
      "native_name": "Composed::K_SERVICE",
      "status": "proposed"
    },
    "N_ACCESS": {
      "basis": "SYN",
      "description": "Proposed need: obtain tools and handle reported faults explicitly.",
      "kind": "need",
      "label": "Dependable access to shared tools",
      "native_name": "Composed::N_ACCESS",
      "status": "proposed"
    },
    "R_APP": {
      "basis": "SYN",
      "description": "Technology for checkout and fault records; implementation not demonstrated.",
      "kind": "element",
      "label": "Checkout application",
      "native_name": "Composed::R_APP",
      "status": "proposed"
    },
    "R_BENCH": {
      "basis": "SYN",
      "description": "Proposed support infrastructure; suitability not established.",
      "kind": "element",
      "label": "Service bench",
      "native_name": "Composed::R_BENCH",
      "status": "proposed"
    },
    "R_DESK": {
      "basis": "SYN",
      "description": "Person role; actual competence, availability and staffing are unmeasured.",
      "kind": "element",
      "label": "Desk operator",
      "native_name": "Composed::R_DESK",
      "status": "proposed"
    },
    "R_KIT": {
      "basis": "SYN",
      "description": "Proposed qualification resource; calibration and fitness are unresolved.",
      "kind": "element",
      "label": "Readiness test kit",
      "native_name": "Composed::R_KIT",
      "status": "proposed"
    },
    "R_PROC": {
      "basis": "SYN",
      "description": "Support instructions; substantive technical content needs domain evidence.",
      "kind": "element",
      "label": "Maintenance procedure",
      "native_name": "Composed::R_PROC",
      "status": "proposed"
    },
    "R_STORE": {
      "basis": "SYN",
      "description": "Storage/status operation; facility capacity and inventory are unresolved.",
      "kind": "element",
      "label": "Tool store",
      "native_name": "Composed::R_STORE",
      "status": "proposed"
    },
    "R_TECH": {
      "basis": "SYN",
      "description": "External support role responsible for the proposed maintenance and readiness activities.",
      "kind": "element",
      "label": "Maintenance provider",
      "native_name": "Composed::R_TECH",
      "status": "proposed"
    },
    "SYS": {
      "basis": "SYN",
      "description": "Boundary: assessment, checkout recording, withdrawal, maintenance coordination and readiness evaluation.",
      "kind": "system",
      "label": "Tool lending service",
      "native_name": "Composed::SYS",
      "status": "proposed"
    },
    "S_FAULT": {
      "basis": "SYN",
      "description": "Trigger: borrower reports a fault. Walk F_WITHDRAW. Outcome: tool withdrawn and fault record available for maintenance.",
      "kind": "scenario",
      "label": "Reported fault",
      "native_name": "Composed::S_FAULT",
      "status": "proposed"
    },
    "S_MAINT": {
      "basis": "SYN",
      "description": "Trigger: withdrawn tool and work record. Walk F_RESTORE then F_QUALIFY. Outcome: evaluation record; authorization to release remains unresolved.",
      "kind": "scenario",
      "label": "Maintenance and readiness evaluation",
      "native_name": "Composed::S_MAINT",
      "status": "proposed"
    },
    "S_NORMAL": {
      "basis": "SYN",
      "description": "Trigger: borrower requests a tool. Walk F_ASSESS then F_ISSUE. Outcome: handover record and instructions, or explicit unavailability.",
      "kind": "scenario",
      "label": "Normal checkout",
      "native_name": "Composed::S_NORMAL",
      "status": "proposed"
    }
  },
  "evidence": {
    "E_FAULT": {
      "basis": "SYN",
      "environment": "Nonoperational fault-report rehearsal with sample records.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Walk a reported fault through withdrawal and maintenance handoff.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "S_FAULT"
    },
    "E_MAINT": {
      "basis": "SYN",
      "environment": "Service bench with maintenance provider and procedure; suitability unresolved.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Compare performed maintenance with a domain-reviewed maintenance procedure.",
      "mode": "plan",
      "purpose": "verification",
      "result": "not_run",
      "target": "F_RESTORE"
    },
    "E_NORMAL": {
      "basis": "SYN",
      "environment": "Nonoperational desk rehearsal with desk operator and sample records.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Observe a checkout walkthrough against borrower intent.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "S_NORMAL"
    },
    "E_READY": {
      "basis": "SYN",
      "environment": "Nonoperational service bench, maintenance provider and readiness test kit; no actual tool release.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Collect readiness observations with the test kit; define release criteria with the responsible engineer.",
      "mode": "plan",
      "purpose": "qualification",
      "result": "not_run",
      "target": "F_QUALIFY"
    }
  },
  "question": {
    "basis": "SYN",
    "text": "Does this illustrative lending-service concept retain its declared operational and lifecycle support?"
  },
  "questions": {
    "Q_CRITERIA": {
      "affects": [
        "F_QUALIFY"
      ],
      "blocking": false,
      "text": "What tool-specific criteria, competence and records authorize release?"
    },
    "Q_SCOPE": {
      "affects": [
        "K_SERVICE"
      ],
      "blocking": false,
      "text": "Are procurement/disposal and other enabling systems relevant to the next real use case?"
    }
  },
  "relations": {
    "CROSS_ALLOC": {
      "basis": "SYN",
      "from": "F_DETAIL_50",
      "kind": "allocated_to",
      "label": "Shared maintainer duty",
      "to": "R_TECH"
    },
    "DETAIL_0": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_0"
    },
    "DETAIL_1": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_1"
    },
    "DETAIL_10": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_10"
    },
    "DETAIL_11": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_11"
    },
    "DETAIL_12": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_12"
    },
    "DETAIL_13": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_13"
    },
    "DETAIL_14": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_14"
    },
    "DETAIL_15": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_15"
    },
    "DETAIL_16": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_16"
    },
    "DETAIL_17": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_17"
    },
    "DETAIL_18": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_18"
    },
    "DETAIL_19": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_19"
    },
    "DETAIL_2": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_2"
    },
    "DETAIL_20": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_20"
    },
    "DETAIL_21": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_21"
    },
    "DETAIL_22": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_22"
    },
    "DETAIL_23": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_23"
    },
    "DETAIL_24": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_24"
    },
    "DETAIL_25": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_25"
    },
    "DETAIL_26": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_26"
    },
    "DETAIL_27": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_27"
    },
    "DETAIL_28": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_28"
    },
    "DETAIL_29": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_29"
    },
    "DETAIL_3": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_3"
    },
    "DETAIL_30": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_30"
    },
    "DETAIL_31": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_31"
    },
    "DETAIL_32": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_32"
    },
    "DETAIL_33": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_33"
    },
    "DETAIL_34": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_34"
    },
    "DETAIL_35": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_35"
    },
    "DETAIL_36": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_36"
    },
    "DETAIL_37": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_37"
    },
    "DETAIL_38": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_38"
    },
    "DETAIL_39": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_39"
    },
    "DETAIL_4": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_4"
    },
    "DETAIL_40": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_40"
    },
    "DETAIL_41": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_41"
    },
    "DETAIL_42": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_42"
    },
    "DETAIL_43": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_43"
    },
    "DETAIL_44": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_44"
    },
    "DETAIL_45": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_45"
    },
    "DETAIL_46": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_46"
    },
    "DETAIL_47": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_47"
    },
    "DETAIL_48": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_48"
    },
    "DETAIL_49": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_49"
    },
    "DETAIL_5": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_5"
    },
    "DETAIL_50": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_50"
    },
    "DETAIL_6": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_6"
    },
    "DETAIL_7": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_7"
    },
    "DETAIL_8": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_8"
    },
    "DETAIL_9": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "decomposes",
      "label": "Support refinement",
      "to": "F_DETAIL_9"
    },
    "L01": {
      "basis": "SYN",
      "from": "S_NORMAL",
      "kind": "scenario_of",
      "label": "normal operation",
      "to": "K_SERVICE"
    },
    "L02": {
      "basis": "SYN",
      "from": "S_FAULT",
      "kind": "scenario_of",
      "label": "reported fault",
      "to": "K_SERVICE"
    },
    "L03": {
      "basis": "SYN",
      "from": "S_MAINT",
      "kind": "scenario_of",
      "label": "lifecycle support",
      "to": "K_SERVICE"
    },
    "L04": {
      "basis": "SYN",
      "from": "F_ASSESS",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_ACCESS"
    },
    "L05": {
      "basis": "SYN",
      "from": "F_ISSUE",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_ACCESS"
    },
    "L06": {
      "basis": "SYN",
      "from": "F_WITHDRAW",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_ACCESS"
    },
    "L07": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_ACCESS"
    },
    "L08": {
      "basis": "SYN",
      "from": "F_QUALIFY",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_ACCESS"
    },
    "L09": {
      "basis": "SYN",
      "from": "F_ASSESS",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_DESK"
    },
    "L10": {
      "basis": "SYN",
      "from": "F_ASSESS",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_STORE"
    },
    "L11": {
      "basis": "SYN",
      "from": "F_ISSUE",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_DESK"
    },
    "L12": {
      "basis": "SYN",
      "from": "F_ISSUE",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_APP"
    },
    "L13": {
      "basis": "SYN",
      "from": "F_WITHDRAW",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_DESK"
    },
    "L14": {
      "basis": "SYN",
      "from": "F_WITHDRAW",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_APP"
    },
    "L15": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_TECH"
    },
    "L16": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_PROC"
    },
    "L17": {
      "basis": "SYN",
      "from": "F_RESTORE",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_BENCH"
    },
    "L18": {
      "basis": "SYN",
      "from": "F_QUALIFY",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_TECH"
    },
    "L19": {
      "basis": "SYN",
      "from": "F_QUALIFY",
      "kind": "allocated_to",
      "label": "proposed means; capability unqualified",
      "to": "R_KIT"
    },
    "L20": {
      "basis": "SYN",
      "from": "R_APP",
      "kind": "interfaces_with",
      "label": "availability and fault records",
      "to": "R_STORE"
    },
    "L21": {
      "basis": "SYN",
      "from": "R_APP",
      "kind": "information_to",
      "label": "fault and maintenance work record",
      "to": "R_TECH"
    },
    "L22": {
      "basis": "SYN",
      "from": "A_BORROWER",
      "kind": "participates_in",
      "label": "request and handover",
      "to": "S_NORMAL"
    },
    "L23": {
      "basis": "SYN",
      "from": "A_BORROWER",
      "kind": "participates_in",
      "label": "fault report",
      "to": "S_FAULT"
    },
    "L24": {
      "basis": "SYN",
      "from": "R_TECH",
      "kind": "participates_in",
      "label": "maintenance and evaluation",
      "to": "S_MAINT"
    }
  },
  "sources": {
    "SYN": {
      "excerpt": "Synthetic shared-tool lending service, proposed solely for a CSE method test.",
      "kind": "proposal",
      "sha256": "18d0befaff84e2acb1597b11ff2b2021c3827796c78edba0ec19a5b39d93e6e8"
    }
  },
  "trade_studies": {},
  "version": "workflow-1.1",
  "views": {
    "OPERATIONS": {
      "elements": [
        "A_BORROWER",
        "F_ASSESS",
        "F_ISSUE",
        "F_QUALIFY",
        "F_RESTORE",
        "F_WITHDRAW",
        "K_SERVICE",
        "N_ACCESS",
        "R_APP",
        "R_BENCH",
        "R_DESK",
        "R_KIT",
        "R_PROC",
        "R_STORE",
        "R_TECH",
        "SYS",
        "S_FAULT",
        "S_MAINT",
        "S_NORMAL",
        "F_DETAIL_0",
        "F_DETAIL_1",
        "F_DETAIL_2",
        "F_DETAIL_3",
        "F_DETAIL_4",
        "F_DETAIL_5",
        "F_DETAIL_6",
        "F_DETAIL_7",
        "F_DETAIL_8",
        "F_DETAIL_9",
        "F_DETAIL_10",
        "F_DETAIL_11",
        "F_DETAIL_12",
        "F_DETAIL_13",
        "F_DETAIL_14",
        "F_DETAIL_15",
        "F_DETAIL_16",
        "F_DETAIL_17",
        "F_DETAIL_18",
        "F_DETAIL_19",
        "F_DETAIL_20",
        "F_DETAIL_21",
        "F_DETAIL_22",
        "F_DETAIL_23",
        "F_DETAIL_24",
        "F_DETAIL_25",
        "F_DETAIL_26",
        "F_DETAIL_27",
        "F_DETAIL_28",
        "F_DETAIL_29",
        "F_DETAIL_30",
        "F_DETAIL_31",
        "F_DETAIL_32",
        "F_DETAIL_33",
        "F_DETAIL_34",
        "F_DETAIL_35",
        "F_DETAIL_36",
        "F_DETAIL_37",
        "F_DETAIL_38",
        "F_DETAIL_39",
        "F_DETAIL_40"
      ],
      "label": "Operations"
    },
    "SUPPORT": {
      "elements": [
        "F_DETAIL_41",
        "F_DETAIL_42",
        "F_DETAIL_43",
        "F_DETAIL_44",
        "F_DETAIL_45",
        "F_DETAIL_46",
        "F_DETAIL_47",
        "F_DETAIL_48",
        "F_DETAIL_49",
        "F_DETAIL_50",
        "R_TECH"
      ],
      "label": "Detailed support"
    }
  },
  "workflows": {
    "architecture": {
      "conditions": "Synthetic method test; no rates, thresholds or measured competence.",
      "focus": [
        "N_ACCESS",
        "K_SERVICE",
        "SYS",
        "A_BORROWER",
        "S_NORMAL",
        "S_FAULT",
        "S_MAINT",
        "F_ASSESS",
        "F_ISSUE",
        "F_WITHDRAW",
        "F_RESTORE",
        "F_QUALIFY",
        "R_DESK",
        "R_APP",
        "R_STORE",
        "R_TECH",
        "R_PROC",
        "R_BENCH",
        "R_KIT"
      ],
      "next_decision": "Review applicability and readiness criteria before any operational or staffing claim.",
      "outcome": "A connected draft with visible evidence plans and unresolved operational claims.",
      "summary": "One source-linked, illustrative lending-service candidate."
    },
    "concept": {
      "conditions": "Synthetic method test; no rates, thresholds or measured competence.",
      "focus": [
        "N_ACCESS",
        "K_SERVICE",
        "SYS",
        "A_BORROWER",
        "S_NORMAL",
        "S_FAULT",
        "S_MAINT",
        "F_ASSESS",
        "F_ISSUE",
        "F_WITHDRAW",
        "F_RESTORE",
        "F_QUALIFY",
        "R_DESK",
        "R_APP",
        "R_STORE",
        "R_TECH",
        "R_PROC",
        "R_BENCH",
        "R_KIT"
      ],
      "next_decision": "Review applicability and readiness criteria before any operational or staffing claim.",
      "outcome": "A connected draft with visible evidence plans and unresolved operational claims.",
      "summary": "One source-linked, illustrative lending-service candidate."
    },
    "scenarios": {
      "conditions": "Synthetic method test; no rates, thresholds or measured competence.",
      "focus": [
        "N_ACCESS",
        "K_SERVICE",
        "SYS",
        "A_BORROWER",
        "S_NORMAL",
        "S_FAULT",
        "S_MAINT",
        "F_ASSESS",
        "F_ISSUE",
        "F_WITHDRAW",
        "F_RESTORE",
        "F_QUALIFY",
        "R_DESK",
        "R_APP",
        "R_STORE",
        "R_TECH",
        "R_PROC",
        "R_BENCH",
        "R_KIT"
      ],
      "next_decision": "Review applicability and readiness criteria before any operational or staffing claim.",
      "outcome": "A connected draft with visible evidence plans and unresolved operational claims.",
      "summary": "One source-linked, illustrative lending-service candidate."
    }
  }
}
    */
  }
}
