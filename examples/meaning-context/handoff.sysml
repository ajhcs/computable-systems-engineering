package HandoffStudy {
    private import ScalarValues::Boolean;
    doc cseClock /*CSE-CLOCK/2.0
    period 1 second
    */
    part def SendingDesk {
        in attribute active : Boolean;
        in attribute complete : Boolean;
        out attribute acknowledged : Boolean;
    }
    part def Clinic;
    part desk : SendingDesk;
    part clinic : Clinic {
        doc description /*The clinic acknowledges the selected referral.*/
    }
    action def Handoff {
        doc description /*A handoff is complete only after the sending service receives acknowledgement for the same referral from the selected receiving clinic. Sending alone does not complete the handoff.*/
    }
    action def CustomsHandoff {
        doc description /*A handoff transfers customs custody in this separate synthetic namespace.*/
    }
    action def SendReferral {
        doc description /*Send the referral.*/
    }
    action def AcknowledgeReferral {
        doc description /*Acknowledge the referral.*/
    }
    use case <UC_TRANSFER> Transfer;
    concern <N_DELAY> ReduceDelay {
        doc description /*Reduce handoff delay without an adopted numeric threshold.*/
    }
    requirement <R_COMPLETE> CompletionRequiresAcknowledgement {
        doc cseSource /*CSE-SOURCE/2.0
        SYN-HANDOFF-1
        */
        subject unit = desk;
        require constraint completionMeaning {
            doc cse /*CSE-REQ/2.0
            In unit.active = true, whenever unit.complete = true,
            unit shall always satisfy unit.acknowledged = true.
            */
        }
    }
}

package 'MeaningContext' {
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "decisions": {
    "D_COMPLETION": {
      "affects": [
        "S_HANDOFF",
        "R_COMPLETE"
      ],
      "basis": "SYN_HANDOFF",
      "by": "Synthetic study author",
      "status": "proposed",
      "text": "Use the stated acknowledgement-based completion definition for this synthetic candidate."
    }
  },
  "elements": {
    "A_CLINIC": {
      "basis": "SYN_HANDOFF",
      "description": "The clinic as an external acknowledgement performer; this is a role, not another instance.",
      "kind": "actor",
      "label": "receiver",
      "native_name": "HandoffStudy::clinic",
      "status": "proposed"
    },
    "F_ACK": {
      "basis": "SYN_HANDOFF",
      "description": "The receiving clinic acknowledges the selected referral.",
      "kind": "function",
      "label": "acknowledge referral",
      "native_name": "HandoffStudy::AcknowledgeReferral",
      "status": "proposed"
    },
    "F_SEND": {
      "basis": "SYN_HANDOFF",
      "description": "Send a referral without asserting completion.",
      "kind": "function",
      "label": "send referral",
      "native_name": "HandoffStudy::SendReferral",
      "status": "proposed"
    },
    "N_DELAY": {
      "basis": "SYN_HANDOFF",
      "description": "A direction for investigation, without an adopted threshold.",
      "kind": "goal",
      "label": "reduce handoff delay",
      "native_name": "HandoffStudy::ReduceDelay",
      "status": "proposed"
    },
    "R_CLINIC": {
      "basis": "SYN_HANDOFF",
      "description": "The selected receiving clinic.",
      "kind": "element",
      "label": "clinic",
      "native_name": "HandoffStudy::clinic",
      "status": "proposed"
    },
    "R_COMPLETE": {
      "basis": "SYN_HANDOFF",
      "description": "For active handoffs, a complete result requires a matched receiving-clinic acknowledgement.",
      "kind": "requirement",
      "label": "completion invariant",
      "native_name": "HandoffStudy::CompletionRequiresAcknowledgement",
      "status": "proposed"
    },
    "R_DESK": {
      "basis": "SYN_HANDOFF",
      "description": "Sending service for the selected handoff.",
      "kind": "system",
      "label": "sending desk",
      "native_name": "HandoffStudy::desk",
      "status": "proposed"
    },
    "S_CUSTOMS": {
      "basis": "SYN_HANDOFF",
      "description": "Separate customs custody concept; no clinical equivalence is declared.",
      "kind": "scenario",
      "label": "customs handoff",
      "native_name": "HandoffStudy::CustomsHandoff",
      "status": "proposed"
    },
    "S_HANDOFF": {
      "basis": "SYN_HANDOFF",
      "description": "Completion requires receipt of acknowledgement for the same referral from the selected clinic; sending alone is insufficient.",
      "kind": "scenario",
      "label": "handoff",
      "native_name": "HandoffStudy::Handoff",
      "status": "proposed"
    }
  },
  "evidence": {
    "E_PLAN": {
      "basis": "SYN_HANDOFF",
      "environment": "Synthetic unit fixture only.",
      "limitations": "Planning is not execution or clinical evidence.",
      "method": "Exercise sending, waiting, matching and unrelated acknowledgements.",
      "mode": "plan",
      "purpose": "verification",
      "result": "not_run",
      "target": "S_HANDOFF"
    },
    "E_REPORTED": {
      "basis": "SYN_HANDOFF",
      "environment": "Authored example.",
      "limitations": "A supplied assessment; no execution or operational observation is claimed.",
      "method": "Illustrative reported review.",
      "mode": "assessment",
      "purpose": "analysis",
      "result": "supported",
      "target": "F_ACK"
    }
  },
  "question": {
    "basis": "SYN_HANDOFF",
    "text": "Explain and implement handoff completion without changing its definition."
  },
  "questions": {
    "Q_MAPPING": {
      "affects": [
        "S_HANDOFF",
        "F_ACK"
      ],
      "blocking": false,
      "text": "Which real acknowledgement transport and observation boundary would implement this candidate?"
    }
  },
  "relations": {
    "REL_ACK_ALLOCATION": {
      "basis": "SYN_HANDOFF",
      "from": "F_ACK",
      "kind": "allocated_to",
      "label": "selected acknowledgement performer",
      "to": "R_CLINIC"
    },
    "REL_COMPLETION": {
      "basis": "SYN_HANDOFF",
      "from": "R_COMPLETE",
      "kind": "controls",
      "label": "sending does not satisfy completion",
      "to": "F_SEND"
    },
    "REL_DESK": {
      "basis": "SYN_HANDOFF",
      "from": "R_DESK",
      "kind": "participates_in",
      "label": "sending service",
      "to": "S_HANDOFF"
    },
    "REL_GOAL": {
      "basis": "SYN_HANDOFF",
      "from": "N_DELAY",
      "kind": "controls",
      "label": "goal guides investigation; no mandatory threshold",
      "to": "F_SEND"
    },
    "REL_PARTICIPANT": {
      "basis": "SYN_HANDOFF",
      "from": "A_CLINIC",
      "kind": "participates_in",
      "label": "external acknowledgement performer",
      "to": "S_HANDOFF"
    },
    "REL_REFERRAL": {
      "basis": "SYN_HANDOFF",
      "from": "F_SEND",
      "kind": "information_to",
      "label": "referral identity and selected clinic",
      "to": "F_ACK"
    },
    "REL_SEND_ALLOCATION": {
      "basis": "SYN_HANDOFF",
      "from": "F_SEND",
      "kind": "allocated_to",
      "label": "selected sending function performer",
      "to": "R_DESK"
    }
  },
  "sources": {
    "SYN_HANDOFF": {
      "excerpt": "Synthetic handoff study, revision 1. No clinical or operational acceptance is claimed.\n\nA handoff is complete when the sending service receives an acknowledgement for the same referral from the selected receiving clinic. Sending the referral alone does not complete the handoff. The completion invariant applies to active handoffs. Waiting without acknowledgement is allowed; no completion deadline is specified.\n\nReduce handoff delay is a goal, without a mandatory numeric threshold. The clinic is the selected external acknowledgement performer; the sending desk sends referrals. Customs handoff is a separate concept in a separate namespace.\n\nE_PLAN is a plan to test the handoff and has not run. E_REPORTED is an illustrative reported assessment, not an executed observation. The acknowledgement transport mapping remains an open question. These statements define only this synthetic study.",
      "kind": "proposal",
      "sha256": "ff438738230bb86617b9dffabc00492fb1b4cf8ecd89dfbb71bf4aee1777d874"
    }
  },
  "trade_studies": {},
  "version": "workflow-1.0",
  "workflows": {
    "concept": {
      "conditions": "Active handoffs only. Completion requires acknowledgement for the same referral from the selected receiving clinic. No deadline is specified.",
      "focus": [
        "S_HANDOFF"
      ],
      "next_decision": "Resolve the acknowledgement transport mapping without inventing behavior.",
      "outcome": "An explanation and implementation preserve the completion distinction.",
      "summary": "Review the defined handoff completion event and selected roles."
    }
  }
}
    */
  }
}
