package SoftwareExample { part def Application; part application : Application; concern ExportNeed; action def ExportConfiguration; }

package 'SoftwareMetadata' {
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "decisions": {},
  "elements": {
    "F_EXPORT": {
      "basis": "BRIEF",
      "description": "Export configuration; illustrative and technically unqualified.",
      "kind": "function",
      "label": "Export configuration",
      "native_name": "SoftwareExample::ExportConfiguration",
      "status": "proposed"
    },
    "N_EXPORT": {
      "basis": "BRIEF",
      "description": "Retain exportable configuration; illustrative and technically unqualified.",
      "kind": "need",
      "label": "Retain exportable configuration",
      "native_name": "SoftwareExample::ExportNeed",
      "status": "proposed"
    },
    "R_APP": {
      "basis": "BRIEF",
      "description": "Existing application; illustrative and technically unqualified.",
      "kind": "element",
      "label": "Existing application",
      "native_name": "SoftwareExample::application",
      "status": "proposed"
    }
  },
  "evidence": {
    "E_EXPORT": {
      "basis": "CHECKS",
      "environment": "Nonproduction application test with synthetic configuration.",
      "limitations": "No implementation or observed result is supplied.",
      "method": "Compare an exported sample with a domain-reviewed source configuration.",
      "mode": "plan",
      "purpose": "verification",
      "result": "not_run",
      "target": "F_EXPORT"
    }
  },
  "question": {
    "basis": "BRIEF",
    "text": "Is the export concept connected to its selected purpose and evidence plan?"
  },
  "questions": {},
  "relations": {
    "L_ALLOC": {
      "basis": "CHECKS",
      "from": "F_EXPORT",
      "kind": "allocated_to",
      "label": "proposed implementation",
      "to": "R_APP"
    },
    "L_NEED": {
      "basis": "CHECKS",
      "from": "F_EXPORT",
      "kind": "addresses",
      "label": "proposed contribution",
      "to": "N_EXPORT"
    }
  },
  "sources": {
    "BRIEF": {
      "excerpt": "Synthetic software-only export concept: an operator requests a configuration export from an existing application.",
      "kind": "proposal",
      "sha256": "7f65ca373505543f9dd5a229c41a2581e066955541ced8dae93b8509df2d5e88"
    },
    "CHECKS": {
      "excerpt": "Synthetic review focus: retain the export function, application allocation and verification plan. No new physical facility is proposed.",
      "kind": "proposal",
      "sha256": "2032a0c1b9ac45be3cecc409d62741056bb4f44b09a639c8ce11f0ed19006a9b"
    }
  },
  "trade_studies": {},
  "version": "workflow-1.0",
  "workflows": {
    "concept": {
      "conditions": "Synthetic example; existing host environment is outside the change.",
      "focus": [
        "N_EXPORT",
        "F_EXPORT",
        "R_APP"
      ],
      "next_decision": "Specify actual export correctness and operating conditions.",
      "outcome": "Inspectable purpose, function, allocation and evaluation plan.",
      "summary": "One software-only concept slice."
    }
  }
}
    */
  }
}
