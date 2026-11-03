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
  "decisions": {
    "D_CHECKOUT": {
      "affects": [
        "K_SERVICE",
        "F_ISSUE",
        "R_APP",
        "S_NORMAL"
      ],
      "basis": "STUDY",
      "by": "",
      "status": "superseded",
      "text": "Superseded as the proposed first priority in this authored case: E_SYN_FINDING locates the unresolved decisions in fault handoff and release, while routine checkout proceeds. Preserve the original hypothesis in the before revision; this does not prove checkout quality in a real service."
    },
    "D_RECOVERY": {
      "affects": [
        "N_ACCESS",
        "SYS",
        "K_SERVICE",
        "F_ISSUE",
        "F_WITHDRAW",
        "F_RESTORE",
        "F_QUALIFY",
        "R_APP",
        "R_PROC",
        "R_TECH",
        "S_NORMAL",
        "S_FAULT",
        "S_MAINT"
      ],
      "basis": "STUDY",
      "by": "",
      "status": "proposed",
      "text": "Propose clarifying the fault next-action owner, maintenance handoff and evidence/authority for release before prioritizing checkout-screen changes. Reason: the supplied synthetic finding affects the explanation, functions, responsibilities, scenarios and evaluation method. Keep N_ACCESS, SYS and all retained obligations; the engineer must decide any actual responsibility or criteria."
    }
  },
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
      "basis": "STUDY",
      "description": "Produce readiness observations and identify the proposed release-decision route; actual tool-specific criteria, competence and authorization remain unresolved.",
      "kind": "function",
      "label": "Evaluate readiness",
      "native_name": "LendingExample::EvaluateReadiness",
      "status": "proposed"
    },
    "F_RESTORE": {
      "basis": "STUDY",
      "description": "Perform proposed maintenance with the provider, procedure and service bench; supply a completion record and the next readiness decision while release authority remains unresolved.",
      "kind": "function",
      "label": "Maintain the tool",
      "native_name": "LendingExample::MaintainTool",
      "status": "proposed"
    },
    "F_WITHDRAW": {
      "basis": "STUDY",
      "description": "Proposed clarification: transform a fault report into withdrawal status and a work record with an explicit next-action owner and handoff acknowledgement; actual responsibility needs engineer direction.",
      "kind": "function",
      "label": "Withdraw a faulted tool",
      "native_name": "LendingExample::WithdrawFaultedTool",
      "status": "proposed"
    },
    "K_SERVICE": {
      "basis": "STUDY",
      "description": "Revised proposal: investigate unclear fault handoff and return-to-service decisions first. The supplied synthetic case favors this explanation over routine checkout interaction delay. Preserve N_ACCESS, SYS and every retained support/evaluation expectation; no operational cause or acceptance is established.",
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
      "basis": "STUDY",
      "description": "Proposed instructions cover fault handoff, completion records and the route to a release decision; substantive technical criteria and authority still need domain evidence.",
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
      "basis": "STUDY",
      "description": "Trigger: borrower reports a fault. Walk F_WITHDRAW; inspect the proposed next-action owner and acknowledgement. Outcome: withdrawal and a work record for maintenance; actual responsibility remains unresolved.",
      "kind": "scenario",
      "label": "Reported fault",
      "native_name": "LendingExample::FaultReport",
      "status": "proposed"
    },
    "S_MAINT": {
      "basis": "STUDY",
      "description": "Trigger: withdrawn tool and work record. Walk F_RESTORE then F_QUALIFY; inspect completion information and the missing release basis. Outcome: evaluation record and unresolved release decision, with no automatic return to service.",
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
    "E_DIFFERENTIATE": {
      "basis": "STUDY",
      "environment": "Proposed nonoperational walkthrough using the same service boundary, sample tool records and the normal case as a comparison.",
      "limitations": "Unexecuted qualitative plan. No actual participants, observations, timing threshold, capability result or release decision are supplied.",
      "method": "Compare S_NORMAL, S_FAULT and S_MAINT with a desk operator and maintenance provider. Follow tool records; record the stopping point, missing information and next-action decision owner. Routine checkout stops would support D_CHECKOUT; fault/release ambiguity with a clear normal path would prompt reconsideration.",
      "mode": "plan",
      "purpose": "analysis",
      "result": "not_run",
      "target": "K_SERVICE"
    },
    "E_FAULT": {
      "basis": "STUDY",
      "environment": "Nonoperational fault-report rehearsal with sample records.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Walk a reported fault through withdrawal and maintenance handoff; inspect the proposed next-action owner, missing work information and acknowledgement.",
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
      "basis": "STUDY",
      "environment": "Nonoperational service bench, maintenance provider and readiness test kit; no actual tool release.",
      "limitations": "Plan only. No observed performance, technical adequacy or release authorization.",
      "method": "Collect proposed readiness observations with the test kit; ask the responsible engineer to define the tool-specific release criteria, authority and required records.",
      "mode": "plan",
      "purpose": "qualification",
      "result": "not_run",
      "target": "F_QUALIFY"
    },
    "E_SYN_FINDING": {
      "basis": "STUDY",
      "environment": "Synthetic teaching case supplied in reframing-study.md; no execution or operational setting was observed.",
      "limitations": "Declared interpretation of synthetic input only. E_DIFFERENTIATE and all original evaluations remain unexecuted plans. No real cause, frequency, competence, feasibility, validation or acceptance is established.",
      "method": "Qualitatively interpret only the supplied authored case in STUDY: normal checkout proceeds; the fault record lacks a next-action owner and the maintenance record lacks release authority/criteria. This supports reconsidering D_CHECKOUT within the example.",
      "mode": "assessment",
      "purpose": "analysis",
      "result": "supported",
      "target": "K_SERVICE"
    }
  },
  "question": {
    "basis": "STUDY",
    "text": "Which explanation should guide the next lending-service proposal: routine checkout interactions or unclear fault and return-to-service decisions?"
  },
  "questions": {
    "Q_CAUSE": {
      "affects": [
        "K_SERVICE",
        "F_ISSUE",
        "F_WITHDRAW",
        "F_RESTORE",
        "F_QUALIFY",
        "R_APP",
        "R_PROC",
        "R_TECH",
        "S_NORMAL",
        "S_FAULT",
        "S_MAINT"
      ],
      "blocking": false,
      "text": "E_SYN_FINDING favors the fault/recovery explanation within the supplied synthetic case and sends D_CHECKOUT back to K_SERVICE, F_WITHDRAW, F_RESTORE and F_QUALIFY. Does real evidence support that explanation, and what contrary routine-checkout finding would justify reopening D_CHECKOUT? No operational cause is established."
    },
    "Q_CRITERIA": {
      "affects": [
        "F_QUALIFY"
      ],
      "blocking": false,
      "text": "Which role may authorize return to service, using which tool-specific criteria, competence and records? Clarify with the engineer; a maintenance allocation alone does not supply release authority."
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
      "basis": "STUDY",
      "from": "R_APP",
      "kind": "information_to",
      "label": "proposed fault record, next-action owner and acknowledgement",
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
    "STUDY": {
      "excerpt": "Supplied synthetic result: routine checkout proceeds, while fault handoff and return-to-service decisions stop on unclear responsibility and release criteria.",
      "kind": "provided",
      "sha256": "a014ea8b3e1810019219acc4665958147e9fa85979f2816452ed980b175844e7"
    },
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
      "conditions": "Supplied qualitative synthetic case only; operational observation and all retained evaluations remain not_run.",
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
      "next_decision": "Engineer to review the proposed fault owner and release-decision route and decide what real evidence is needed; no responsibility, threshold or release is accepted here.",
      "outcome": "D_CHECKOUT retained as superseded; D_RECOVERY proposed; affected functions, handoff, scenarios and evaluation methods reconsidered.",
      "summary": "Return to the access-problem explanation and propose fault/recovery clarification first, preserving the same boundary and obligations."
    },
    "concept": {
      "conditions": "Supplied qualitative synthetic case only; operational observation and all retained evaluations remain not_run.",
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
      "next_decision": "Engineer to review the proposed fault owner and release-decision route and decide what real evidence is needed; no responsibility, threshold or release is accepted here.",
      "outcome": "D_CHECKOUT retained as superseded; D_RECOVERY proposed; affected functions, handoff, scenarios and evaluation methods reconsidered.",
      "summary": "Return to the access-problem explanation and propose fault/recovery clarification first, preserving the same boundary and obligations."
    },
    "scenarios": {
      "conditions": "Supplied qualitative synthetic case only; operational observation and all retained evaluations remain not_run.",
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
      "next_decision": "Engineer to review the proposed fault owner and release-decision route and decide what real evidence is needed; no responsibility, threshold or release is accepted here.",
      "outcome": "D_CHECKOUT retained as superseded; D_RECOVERY proposed; affected functions, handoff, scenarios and evaluation methods reconsidered.",
      "summary": "Return to the access-problem explanation and propose fault/recovery clarification first, preserving the same boundary and obligations."
    }
  }
}
    */
  }
}
