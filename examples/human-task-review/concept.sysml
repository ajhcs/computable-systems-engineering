package HumanTaskExample {
 part def Service; part def PersonRole; part def Software; part def Equipment; part def Procedure;
 part system : Service; part clerk : PersonRole; part backup : PersonRole;
 part application : Software; part terminal : Equipment; part instructions : Procedure;
 concern ReviewNeed; concern DeskConcept;
 action def ReviewRequest; action def RecoverReview;
 action def ScenarioNORMAL; action def ScenarioPEAK; action def ScenarioABSENCE; action def ScenarioRECOVERY;
 action def TaskNORMAL; action def TaskPEAK; action def TaskABSENCE; action def TaskRECOVERY;
 use case <UC_REVIEW> ReviewService { subject unit = system; actor operator = clerk;
 doc /* Narrative normal, peak, absence and recovery task contexts; no executable guards or schedule. */ }
}

package 'TaskWorkflow' {
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "decisions": {},
  "elements": {
    "F_RECOVER": {
      "basis": "CASE",
      "description": "Recover interrupted review; synthetic proposed context, not demonstrated performance.",
      "kind": "function",
      "label": "Recover interrupted review",
      "native_name": "HumanTaskExample::RecoverReview",
      "status": "proposed"
    },
    "F_REVIEW": {
      "basis": "CASE",
      "description": "Review a request; synthetic proposed context, not demonstrated performance.",
      "kind": "function",
      "label": "Review a request",
      "native_name": "HumanTaskExample::ReviewRequest",
      "status": "proposed"
    },
    "K_DESK": {
      "basis": "CASE",
      "description": "Supported request-review concept; synthetic proposed context, not demonstrated performance.",
      "kind": "concept",
      "label": "Supported request-review concept",
      "native_name": "HumanTaskExample::DeskConcept",
      "status": "proposed"
    },
    "N_REVIEW": {
      "basis": "CASE",
      "description": "Review requests with recoverable handoffs; synthetic proposed context, not demonstrated performance.",
      "kind": "need",
      "label": "Review requests with recoverable handoffs",
      "native_name": "HumanTaskExample::ReviewNeed",
      "status": "proposed"
    },
    "R_APP": {
      "basis": "CASE",
      "description": "Review application; synthetic proposed context, not demonstrated performance.",
      "kind": "element",
      "label": "Review application",
      "native_name": "HumanTaskExample::application",
      "status": "proposed"
    },
    "R_BACKUP": {
      "basis": "CASE",
      "description": "Backup clerk; synthetic proposed context, not demonstrated performance.",
      "kind": "element",
      "label": "Backup clerk",
      "native_name": "HumanTaskExample::backup",
      "status": "proposed"
    },
    "R_CLERK": {
      "basis": "CASE",
      "description": "Primary clerk; synthetic proposed context, not demonstrated performance.",
      "kind": "element",
      "label": "Primary clerk",
      "native_name": "HumanTaskExample::clerk",
      "status": "proposed"
    },
    "R_PROC": {
      "basis": "CASE",
      "description": "Review instructions; synthetic proposed context, not demonstrated performance.",
      "kind": "element",
      "label": "Review instructions",
      "native_name": "HumanTaskExample::instructions",
      "status": "proposed"
    },
    "R_TERMINAL": {
      "basis": "CASE",
      "description": "Review terminal; synthetic proposed context, not demonstrated performance.",
      "kind": "element",
      "label": "Review terminal",
      "native_name": "HumanTaskExample::terminal",
      "status": "proposed"
    },
    "SYS": {
      "basis": "CASE",
      "description": "Request-review service; synthetic proposed context, not demonstrated performance.",
      "kind": "system",
      "label": "Request-review service",
      "native_name": "HumanTaskExample::system",
      "status": "proposed"
    },
    "S_ABSENCE": {
      "basis": "CASE",
      "description": "Primary-clerk absence; synthetic proposed context, not demonstrated performance.",
      "kind": "scenario",
      "label": "Primary-clerk absence",
      "native_name": "HumanTaskExample::ScenarioABSENCE",
      "status": "proposed"
    },
    "S_NORMAL": {
      "basis": "CASE",
      "description": "Normal request review; synthetic proposed context, not demonstrated performance.",
      "kind": "scenario",
      "label": "Normal request review",
      "native_name": "HumanTaskExample::ScenarioNORMAL",
      "status": "proposed"
    },
    "S_PEAK": {
      "basis": "CASE",
      "description": "Peak-demand review; synthetic proposed context, not demonstrated performance.",
      "kind": "scenario",
      "label": "Peak-demand review",
      "native_name": "HumanTaskExample::ScenarioPEAK",
      "status": "proposed"
    },
    "S_RECOVERY": {
      "basis": "CASE",
      "description": "Interrupted-review recovery; synthetic proposed context, not demonstrated performance.",
      "kind": "scenario",
      "label": "Interrupted-review recovery",
      "native_name": "HumanTaskExample::ScenarioRECOVERY",
      "status": "proposed"
    },
    "T_ABSENCE": {
      "basis": "CASE",
      "description": "Primary-clerk absence task; synthetic proposed context, not demonstrated performance.",
      "kind": "step",
      "label": "Primary-clerk absence task",
      "native_name": "HumanTaskExample::TaskABSENCE",
      "status": "proposed"
    },
    "T_NORMAL": {
      "basis": "CASE",
      "description": "Normal request review task; synthetic proposed context, not demonstrated performance.",
      "kind": "step",
      "label": "Normal request review task",
      "native_name": "HumanTaskExample::TaskNORMAL",
      "status": "proposed"
    },
    "T_PEAK": {
      "basis": "CASE",
      "description": "Peak-demand review task; synthetic proposed context, not demonstrated performance.",
      "kind": "step",
      "label": "Peak-demand review task",
      "native_name": "HumanTaskExample::TaskPEAK",
      "status": "proposed"
    },
    "T_RECOVERY": {
      "basis": "CASE",
      "description": "Interrupted-review recovery task; synthetic proposed context, not demonstrated performance.",
      "kind": "step",
      "label": "Interrupted-review recovery task",
      "native_name": "HumanTaskExample::TaskRECOVERY",
      "status": "proposed"
    }
  },
  "evidence": {
    "E_ABSENCE": {
      "basis": "CASE",
      "environment": "Nonoperational service-desk rehearsal under the named scenario.",
      "limitations": "No operator observations, measured times, skill validation or staffing evidence supplied.",
      "method": "Observe the proposed task walkthrough with a representative operator and compare recorded conditions/outcome.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "T_ABSENCE"
    },
    "E_NORMAL": {
      "basis": "CASE",
      "environment": "Nonoperational service-desk rehearsal under the named scenario.",
      "limitations": "No operator observations, measured times, skill validation or staffing evidence supplied.",
      "method": "Observe the proposed task walkthrough with a representative operator and compare recorded conditions/outcome.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "T_NORMAL"
    },
    "E_PEAK": {
      "basis": "CASE",
      "environment": "Nonoperational service-desk rehearsal under the named scenario.",
      "limitations": "No operator observations, measured times, skill validation or staffing evidence supplied.",
      "method": "Observe the proposed task walkthrough with a representative operator and compare recorded conditions/outcome.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "T_PEAK"
    },
    "E_RECOVERY": {
      "basis": "CASE",
      "environment": "Nonoperational service-desk rehearsal under the named scenario.",
      "limitations": "No operator observations, measured times, skill validation or staffing evidence supplied.",
      "method": "Observe the proposed task walkthrough with a representative operator and compare recorded conditions/outcome.",
      "mode": "plan",
      "purpose": "validation",
      "result": "not_run",
      "target": "T_RECOVERY"
    }
  },
  "question": {
    "basis": "CASE",
    "text": "Are the selected human/automation responsibilities and task facts explicit for normal, peak, absence and recovery conditions?"
  },
  "questions": {},
  "relations": {
    "L_1": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "addresses",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "N_REVIEW"
    },
    "L_10": {
      "basis": "CASE",
      "from": "F_RECOVER",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_TERMINAL"
    },
    "L_11": {
      "basis": "CASE",
      "from": "F_RECOVER",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_PROC"
    },
    "L_12": {
      "basis": "CASE",
      "from": "S_NORMAL",
      "kind": "scenario_of",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "K_DESK"
    },
    "L_13": {
      "basis": "CASE",
      "from": "S_PEAK",
      "kind": "scenario_of",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "K_DESK"
    },
    "L_14": {
      "basis": "CASE",
      "from": "S_ABSENCE",
      "kind": "scenario_of",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "K_DESK"
    },
    "L_15": {
      "basis": "CASE",
      "from": "S_RECOVERY",
      "kind": "scenario_of",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "K_DESK"
    },
    "L_2": {
      "basis": "CASE",
      "from": "F_RECOVER",
      "kind": "addresses",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "N_REVIEW"
    },
    "L_3": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_CLERK"
    },
    "L_4": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_BACKUP"
    },
    "L_5": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_APP"
    },
    "L_6": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_TERMINAL"
    },
    "L_7": {
      "basis": "CASE",
      "from": "F_REVIEW",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_PROC"
    },
    "L_8": {
      "basis": "CASE",
      "from": "F_RECOVER",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_CLERK"
    },
    "L_9": {
      "basis": "CASE",
      "from": "F_RECOVER",
      "kind": "allocated_to",
      "label": "Proposed documentary relationship; no capability or execution established.",
      "to": "R_APP"
    }
  },
  "sources": {
    "CASE": {
      "excerpt": "Synthetic service-desk human-task study. All roles, durations, skills and training below are proposals, not field measurements.",
      "kind": "proposal",
      "sha256": "2ae435afbf456d5d70f34349a516ed4bbc7b94cd0cd6384ea158a3ac81a9ad9b"
    }
  },
  "trade_studies": {},
  "version": "workflow-1.0",
  "workflows": {
    "concept": {
      "conditions": "Normal, peak-demand, absence and recovery are illustrative proposed contexts.",
      "focus": [
        "N_REVIEW",
        "K_DESK",
        "SYS",
        "F_REVIEW",
        "F_RECOVER",
        "R_CLERK",
        "R_BACKUP",
        "R_APP",
        "R_TERMINAL",
        "R_PROC",
        "S_NORMAL",
        "T_NORMAL",
        "S_PEAK",
        "T_PEAK",
        "S_ABSENCE",
        "T_ABSENCE",
        "S_RECOVERY",
        "T_RECOVERY"
      ],
      "next_decision": "Check task conditions, training, skill and timing proposals with actual operators.",
      "outcome": "Explicit task facts and responsibility links, with unqualified performance.",
      "summary": "One shared concept/task register."
    }
  }
}
    */
  }
}
package TaskRegister { concern humanTaskContext { doc cseHumanTasks /*CSE-HUMAN-TASKS/1.0
{
  "version": "human-tasks-1.0",
  "tasks": {
    "T_NORMAL": {
      "function": "F_REVIEW",
      "scenario": "S_NORMAL",
      "performers": [
        {
          "element": "R_CLERK",
          "role": "execute",
          "allocation": "human"
        },
        {
          "element": "R_APP",
          "role": "assist",
          "allocation": "automation"
        }
      ],
      "facts": {
        "purpose": {
          "status": "proposed",
          "text": "Review the request or restore an interrupted review without losing its recorded state.",
          "basis": "CASE",
          "refs": []
        },
        "entry": {
          "status": "proposed",
          "text": "A request and its current record are available.",
          "basis": "CASE",
          "refs": []
        },
        "inputs": {
          "status": "proposed",
          "text": "Request contents, current record and outstanding questions are available.",
          "basis": "CASE",
          "refs": []
        },
        "completion": {
          "status": "proposed",
          "text": "Record a review outcome or an explicit unresolved exception; no silent success.",
          "basis": "CASE",
          "refs": []
        },
        "skills": {
          "status": "proposed",
          "text": "Proposed ability to interpret request records and identify unresolved exceptions; not assessed.",
          "basis": "CASE",
          "refs": []
        },
        "equipment": {
          "status": "proposed",
          "text": "Use the existing application and review terminal; suitability remains unqualified.",
          "basis": "CASE",
          "refs": [
            "R_APP",
            "R_TERMINAL"
          ]
        },
        "procedure": {
          "status": "proposed",
          "text": "Use the proposed review/recovery instructions.",
          "basis": "CASE",
          "refs": [
            "R_PROC"
          ]
        },
        "duration": {
          "status": "proposed",
          "text": "Illustrative active task duration, excluding queue delay; not measured.",
          "basis": "CASE",
          "refs": [],
          "value": "2",
          "unit": "minute"
        },
        "concurrency": {
          "status": "proposed",
          "text": "One active request per clerk; queued work is not asserted to be simultaneous capacity.",
          "basis": "CASE",
          "refs": []
        },
        "interruption": {
          "status": "proposed",
          "text": "Record the current request identity and unresolved action before a resumable interruption.",
          "basis": "CASE",
          "refs": []
        },
        "recovery": {
          "status": "proposed",
          "text": "Recheck record version and outstanding conditions before resuming; otherwise escalate.",
          "basis": "CASE",
          "refs": []
        },
        "training": {
          "status": "proposed",
          "text": "Proposed briefing plus observed practice on normal, peak, absence and recovery examples; no competency claim.",
          "basis": "CASE",
          "refs": []
        },
        "evaluation": {
          "status": "proposed",
          "text": "Rehearse the task and gather operator feedback, observed times and exceptions.",
          "basis": "CASE",
          "refs": [
            "E_NORMAL"
          ]
        }
      }
    },
    "T_PEAK": {
      "function": "F_REVIEW",
      "scenario": "S_PEAK",
      "performers": [
        {
          "element": "R_CLERK",
          "role": "execute",
          "allocation": "human"
        },
        {
          "element": "R_APP",
          "role": "assist",
          "allocation": "automation"
        }
      ],
      "facts": {
        "purpose": {
          "status": "proposed",
          "text": "Review the request or restore an interrupted review without losing its recorded state.",
          "basis": "CASE",
          "refs": []
        },
        "entry": {
          "status": "proposed",
          "text": "Requests are queued; one request is active per clerk.",
          "basis": "CASE",
          "refs": []
        },
        "inputs": {
          "status": "proposed",
          "text": "Request contents, current record and outstanding questions are available.",
          "basis": "CASE",
          "refs": []
        },
        "completion": {
          "status": "proposed",
          "text": "Record a review outcome or an explicit unresolved exception; no silent success.",
          "basis": "CASE",
          "refs": []
        },
        "skills": {
          "status": "proposed",
          "text": "Proposed ability to interpret request records and identify unresolved exceptions; not assessed.",
          "basis": "CASE",
          "refs": []
        },
        "equipment": {
          "status": "proposed",
          "text": "Use the existing application and review terminal; suitability remains unqualified.",
          "basis": "CASE",
          "refs": [
            "R_APP",
            "R_TERMINAL"
          ]
        },
        "procedure": {
          "status": "proposed",
          "text": "Use the proposed review/recovery instructions.",
          "basis": "CASE",
          "refs": [
            "R_PROC"
          ]
        },
        "duration": {
          "status": "proposed",
          "text": "Illustrative active task duration, excluding queue delay; not measured.",
          "basis": "CASE",
          "refs": [],
          "value": "2",
          "unit": "minute"
        },
        "concurrency": {
          "status": "proposed",
          "text": "One active request per clerk; queued work is not asserted to be simultaneous capacity.",
          "basis": "CASE",
          "refs": []
        },
        "interruption": {
          "status": "proposed",
          "text": "Record the current request identity and unresolved action before a resumable interruption.",
          "basis": "CASE",
          "refs": []
        },
        "recovery": {
          "status": "proposed",
          "text": "Recheck record version and outstanding conditions before resuming; otherwise escalate.",
          "basis": "CASE",
          "refs": []
        },
        "training": {
          "status": "proposed",
          "text": "Proposed briefing plus observed practice on normal, peak, absence and recovery examples; no competency claim.",
          "basis": "CASE",
          "refs": []
        },
        "evaluation": {
          "status": "proposed",
          "text": "Rehearse the task and gather operator feedback, observed times and exceptions.",
          "basis": "CASE",
          "refs": [
            "E_PEAK"
          ]
        }
      }
    },
    "T_ABSENCE": {
      "function": "F_REVIEW",
      "scenario": "S_ABSENCE",
      "performers": [
        {
          "element": "R_BACKUP",
          "role": "execute",
          "allocation": "human"
        },
        {
          "element": "R_APP",
          "role": "assist",
          "allocation": "automation"
        }
      ],
      "facts": {
        "purpose": {
          "status": "proposed",
          "text": "Review the request or restore an interrupted review without losing its recorded state.",
          "basis": "CASE",
          "refs": []
        },
        "entry": {
          "status": "proposed",
          "text": "Primary clerk is unavailable; backup availability and competence are proposed.",
          "basis": "CASE",
          "refs": []
        },
        "inputs": {
          "status": "proposed",
          "text": "Request contents, current record and outstanding questions are available.",
          "basis": "CASE",
          "refs": []
        },
        "completion": {
          "status": "proposed",
          "text": "Record a review outcome or an explicit unresolved exception; no silent success.",
          "basis": "CASE",
          "refs": []
        },
        "skills": {
          "status": "proposed",
          "text": "Proposed ability to interpret request records and identify unresolved exceptions; not assessed.",
          "basis": "CASE",
          "refs": []
        },
        "equipment": {
          "status": "proposed",
          "text": "Use the existing application and review terminal; suitability remains unqualified.",
          "basis": "CASE",
          "refs": [
            "R_APP",
            "R_TERMINAL"
          ]
        },
        "procedure": {
          "status": "proposed",
          "text": "Use the proposed review/recovery instructions.",
          "basis": "CASE",
          "refs": [
            "R_PROC"
          ]
        },
        "duration": {
          "status": "proposed",
          "text": "Illustrative active task duration, excluding queue delay; not measured.",
          "basis": "CASE",
          "refs": [],
          "value": "2",
          "unit": "minute"
        },
        "concurrency": {
          "status": "proposed",
          "text": "One active request per clerk; queued work is not asserted to be simultaneous capacity.",
          "basis": "CASE",
          "refs": []
        },
        "interruption": {
          "status": "proposed",
          "text": "Record the current request identity and unresolved action before a resumable interruption.",
          "basis": "CASE",
          "refs": []
        },
        "recovery": {
          "status": "proposed",
          "text": "Recheck record version and outstanding conditions before resuming; otherwise escalate.",
          "basis": "CASE",
          "refs": []
        },
        "training": {
          "status": "proposed",
          "text": "Proposed briefing plus observed practice on normal, peak, absence and recovery examples; no competency claim.",
          "basis": "CASE",
          "refs": []
        },
        "evaluation": {
          "status": "proposed",
          "text": "Rehearse the task and gather operator feedback, observed times and exceptions.",
          "basis": "CASE",
          "refs": [
            "E_ABSENCE"
          ]
        }
      }
    },
    "T_RECOVERY": {
      "function": "F_RECOVER",
      "scenario": "S_RECOVERY",
      "performers": [
        {
          "element": "R_CLERK",
          "role": "execute",
          "allocation": "human"
        },
        {
          "element": "R_APP",
          "role": "assist",
          "allocation": "automation"
        }
      ],
      "facts": {
        "purpose": {
          "status": "proposed",
          "text": "Review the request or restore an interrupted review without losing its recorded state.",
          "basis": "CASE",
          "refs": []
        },
        "entry": {
          "status": "proposed",
          "text": "An interruption has ended; the current record must be rechecked.",
          "basis": "CASE",
          "refs": []
        },
        "inputs": {
          "status": "proposed",
          "text": "Request contents, current record and outstanding questions are available.",
          "basis": "CASE",
          "refs": []
        },
        "completion": {
          "status": "proposed",
          "text": "Record a review outcome or an explicit unresolved exception; no silent success.",
          "basis": "CASE",
          "refs": []
        },
        "skills": {
          "status": "proposed",
          "text": "Proposed ability to interpret request records and identify unresolved exceptions; not assessed.",
          "basis": "CASE",
          "refs": []
        },
        "equipment": {
          "status": "proposed",
          "text": "Use the existing application and review terminal; suitability remains unqualified.",
          "basis": "CASE",
          "refs": [
            "R_APP",
            "R_TERMINAL"
          ]
        },
        "procedure": {
          "status": "proposed",
          "text": "Use the proposed review/recovery instructions.",
          "basis": "CASE",
          "refs": [
            "R_PROC"
          ]
        },
        "duration": {
          "status": "proposed",
          "text": "Illustrative active task duration, excluding queue delay; not measured.",
          "basis": "CASE",
          "refs": [],
          "value": "1",
          "unit": "minute"
        },
        "concurrency": {
          "status": "proposed",
          "text": "One active request per clerk; queued work is not asserted to be simultaneous capacity.",
          "basis": "CASE",
          "refs": []
        },
        "interruption": {
          "status": "proposed",
          "text": "Record the current request identity and unresolved action before a resumable interruption.",
          "basis": "CASE",
          "refs": []
        },
        "recovery": {
          "status": "proposed",
          "text": "Recheck record version and outstanding conditions before resuming; otherwise escalate.",
          "basis": "CASE",
          "refs": []
        },
        "training": {
          "status": "proposed",
          "text": "Proposed briefing plus observed practice on normal, peak, absence and recovery examples; no competency claim.",
          "basis": "CASE",
          "refs": []
        },
        "evaluation": {
          "status": "proposed",
          "text": "Rehearse the task and gather operator feedback, observed times and exceptions.",
          "basis": "CASE",
          "refs": [
            "E_RECOVERY"
          ]
        }
      }
    }
  }
}
*/ } }

package CapacityInquiry { concern capacityQuestion { doc cseInquiry /*
CSE-INQUIRY/1.0
{
  "version": "inquiry-1.0",
  "question": {
    "text": "If the primary clerk is unavailable, can the backup meet 12 requests/hour?",
    "basis": "CAP_CASE"
  },
  "sources": {
    "CAP_CASE": {
      "sha256": "779ea604bc48fd1ac45a77c36383388608ff014002d886dbcbd40cfbfb6b1946",
      "excerpt": "Synthetic capacity inquiry attached to the service-desk model; all inputs are hypothetical proposals.",
      "kind": "proposal"
    }
  },
  "functions": {
    "F_REVIEW": {
      "native_name": "HumanTaskExample::ReviewRequest",
      "label": "Review requests",
      "demand": {
        "value": "12",
        "unit": "requests_per_hour",
        "basis": "CAP_CASE"
      },
      "minimum_assignments": 1,
      "minimum_basis": "CAP_CASE"
    }
  },
  "resources": {
    "R_CLERK": {
      "native_name": "HumanTaskExample::clerk",
      "label": "Primary clerk"
    },
    "R_BACKUP": {
      "native_name": "HumanTaskExample::backup",
      "label": "Backup clerk"
    }
  },
  "alternatives": {
    "A_EXISTING": {
      "label": "Existing backup",
      "assignments": [
        {
          "function": "F_REVIEW",
          "resource": "R_CLERK",
          "capability": "capable",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "20",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        },
        {
          "function": "F_REVIEW",
          "resource": "R_BACKUP",
          "capability": "capable",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "8",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        }
      ],
      "composition": {
        "F_REVIEW": {
          "method": "sum",
          "basis": "CAP_CASE"
        }
      },
      "concurrency_basis": null
    },
    "A_LARGER": {
      "label": "Proposed larger backup capability",
      "assignments": [
        {
          "function": "F_REVIEW",
          "resource": "R_CLERK",
          "capability": "capable",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "20",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        },
        {
          "function": "F_REVIEW",
          "resource": "R_BACKUP",
          "capability": "capable",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "16",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        }
      ],
      "composition": {
        "F_REVIEW": {
          "method": "sum",
          "basis": "CAP_CASE"
        }
      },
      "concurrency_basis": null
    },
    "A_UNQUALIFIED": {
      "label": "Unqualified backup proposal",
      "assignments": [
        {
          "function": "F_REVIEW",
          "resource": "R_CLERK",
          "capability": "capable",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "20",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        },
        {
          "function": "F_REVIEW",
          "resource": "R_BACKUP",
          "capability": "unknown",
          "capability_basis": "CAP_CASE",
          "capacity": {
            "value": "16",
            "unit": "requests_per_hour",
            "basis": "CAP_CASE"
          },
          "rationale": "Hypothesized clerk rate with application and equipment available; not measured capability.",
          "rationale_basis": "CAP_CASE"
        }
      ],
      "composition": {
        "F_REVIEW": {
          "method": "sum",
          "basis": "CAP_CASE"
        }
      },
      "concurrency_basis": null
    }
  }
}
*/ } }
