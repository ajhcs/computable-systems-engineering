package LendingExample {
    doc /* Synthetic method test. All allocations and resources are proposals.
           No operational performance or acceptance is established. */
    part def Service;
    part def PersonRole;
    part def Software;
    part def StorageOperation;
    part def Procedure;
    part def Facility;
    part def Equipment;
    part system : Service;
    part borrower : PersonRole;
    part deskOperator : PersonRole;
    part checkoutApp : Software;
    part toolStore : StorageOperation;
    part maintenanceProvider : PersonRole;
    part maintenanceProcedure : Procedure;
    part serviceBench : Facility;
    part readinessKit : Equipment;
    concern <N_ACCESS> AccessNeed;
    concern <K_SERVICE> ServiceConcept;
    action def AssessAvailability;
    action def RecordHandover;
    action def WithdrawFaultedTool;
    action def MaintainTool;
    action def EvaluateReadiness;
    action def NormalCheckout;
    action def FaultReport;
    action def MaintenanceReturn;
    use case <UC_LEND> OperateLendingService {
        subject unit = system;
        actor requester = borrower;
        doc /* Normal: request -> assess -> record handover or unavailability.
               Fault: report -> withdraw -> maintenance work record.
               Lifecycle: maintain -> evaluate readiness -> record observations.
               These are narrative paths, not executable SysML behavior. */
    }
}

package 'LendingMetadata' {
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "decisions": {},
  "elements": {
    "A_BORROWER": {
      "basis": "SYN",
      "description": "External requester and reporter of tool faults.",
      "kind": "actor",
      "label": "Borrower",
      "native_name": "LendingExample::borrower",
      "status": "proposed"
    },
    "F_ASSESS": {
      "basis": "SYN",
      "description": "Transform a request and tool status into an availability decision.",
      "kind": "function",
      "label": "Assess availability",
      "native_name": "LendingExample::AssessAvailability",
      "status": "proposed"
    },
    "F_ISSUE": {
      "basis": "SYN",
      "description": "Transform an agreed checkout into a handover record and return instructions.",
      "kind": "function",
      "label": "Record handover",
      "native_name": "LendingExample::RecordHandover",
      "status": "proposed"
    },
    "F_QUALIFY": {
      "basis": "SYN",
      "description": "Produce readiness observations using the proposed kit; actual acceptance criteria are unresolved.",
      "kind": "function",
      "label": "Evaluate readiness",
      "native_name": "LendingExample::EvaluateReadiness",
      "status": "proposed"
    },
    "F_RESTORE": {
      "basis": "SYN",
      "description": "Perform proposed maintenance using a provider, procedure and service bench.",
      "kind": "function",
      "label": "Maintain the tool",
      "native_name": "LendingExample::MaintainTool",
      "status": "proposed"
    },
    "F_WITHDRAW": {
      "basis": "SYN",
      "description": "Transform a fault report into a withdrawal status and maintenance work record.",
      "kind": "function",
      "label": "Withdraw a faulted tool",
      "native_name": "LendingExample::WithdrawFaultedTool",
      "status": "proposed"
    },
    "K_SERVICE": {
      "basis": "SYN",
      "description": "One candidate; no selection or operational acceptance is asserted.",
      "kind": "concept",
      "label": "Supported lending service",
      "native_name": "LendingExample::ServiceConcept",
      "status": "proposed"
    },
    "N_ACCESS": {
      "basis": "SYN",
      "description": "Proposed need: obtain tools and handle reported faults explicitly.",
      "kind": "need",
      "label": "Dependable access to shared tools",
      "native_name": "LendingExample::AccessNeed",
      "status": "proposed"
    },
    "R_APP": {
      "basis": "SYN",
      "description": "Technology for checkout and fault records; implementation not demonstrated.",
      "kind": "element",
      "label": "Checkout application",
      "native_name": "LendingExample::checkoutApp",
      "status": "proposed"
    },
    "R_BENCH": {
      "basis": "SYN",
      "description": "Proposed support infrastructure; suitability not established.",
      "kind": "element",
      "label": "Service bench",
      "native_name": "LendingExample::serviceBench",
      "status": "proposed"
    },
    "R_DESK": {
      "basis": "SYN",
      "description": "Person role; actual competence, availability and staffing are unmeasured.",
      "kind": "element",
      "label": "Desk operator",
      "native_name": "LendingExample::deskOperator",
      "status": "proposed"
    },
    "R_KIT": {
      "basis": "SYN",
      "description": "Proposed qualification resource; calibration and fitness are unresolved.",
      "kind": "element",
      "label": "Readiness test kit",
      "native_name": "LendingExample::readinessKit",
      "status": "proposed"
    },
    "R_PROC": {
      "basis": "SYN",
      "description": "Support instructions; substantive technical content needs domain evidence.",
      "kind": "element",
      "label": "Maintenance procedure",
      "native_name": "LendingExample::maintenanceProcedure",
      "status": "proposed"
    },
    "R_STORE": {
      "basis": "SYN",
      "description": "Storage/status operation; facility capacity and inventory are unresolved.",
      "kind": "element",
      "label": "Tool store",
      "native_name": "LendingExample::toolStore",
      "status": "proposed"
    },
    "R_TECH": {
      "basis": "SYN",
      "description": "External support role responsible for the proposed maintenance and readiness activities.",
      "kind": "element",
      "label": "Maintenance provider",
      "native_name": "LendingExample::maintenanceProvider",
      "status": "proposed"
    },
    "SYS": {
      "basis": "SYN",
      "description": "Boundary: assessment, checkout recording, withdrawal, maintenance coordination and readiness evaluation.",
      "kind": "system",
      "label": "Tool lending service",
      "native_name": "LendingExample::system",
      "status": "proposed"
    },
    "S_FAULT": {
      "basis": "SYN",
      "description": "Trigger: borrower reports a fault. Walk F_WITHDRAW. Outcome: tool withdrawn and fault record available for maintenance.",
      "kind": "scenario",
      "label": "Reported fault",
      "native_name": "LendingExample::FaultReport",
      "status": "proposed"
    },
    "S_MAINT": {
      "basis": "SYN",
      "description": "Trigger: withdrawn tool and work record. Walk F_RESTORE then F_QUALIFY. Outcome: evaluation record; authorization to release remains unresolved.",
      "kind": "scenario",
      "label": "Maintenance and readiness evaluation",
      "native_name": "LendingExample::MaintenanceReturn",
      "status": "proposed"
    },
    "S_NORMAL": {
      "basis": "SYN",
      "description": "Trigger: borrower requests a tool. Walk F_ASSESS then F_ISSUE. Outcome: handover record and instructions, or explicit unavailability.",
      "kind": "scenario",
      "label": "Normal checkout",
      "native_name": "LendingExample::NormalCheckout",
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
  "version": "workflow-1.0",
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
