package NativeHandoff {
    private import ScalarValues::Boolean;
    doc /* Synthetic explicit correspondence; native behavior is not executed. */
    part def Person;
    part def DeskData {
        in attribute request : Boolean;
        out attribute ready : Boolean;
        out attribute result : Boolean;
        out attribute enabled : Boolean;
    }
    part clerk : Person;
    part desk : DeskData;
    action def Prepare;
    action def Complete;
    action def Handle;
    action def Routine;
    action def PrepareStep;
    action def CompleteStep;
}

package NativeMapping {
    concern context {
        doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "version": "workflow-1.0",
  "question": {
    "text": "Synthetic explicit correspondence only; does not execute native behavior.",
    "basis": null
  },
  "sources": {},
  "elements": {
    "F_PREPARE": {
      "kind": "function",
      "native_name": "NativeHandoff::Prepare",
      "label": "Prepare",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "F_COMPLETE": {
      "kind": "function",
      "native_name": "NativeHandoff::Complete",
      "label": "Complete",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "F_HANDLE": {
      "kind": "function",
      "native_name": "NativeHandoff::Handle",
      "label": "Handle",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "R_CLERK": {
      "kind": "element",
      "native_name": "NativeHandoff::clerk",
      "label": "clerk",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "R_SYSTEM": {
      "kind": "system",
      "native_name": "NativeHandoff::desk",
      "label": "desk",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "S_ROUTINE": {
      "kind": "scenario",
      "native_name": "NativeHandoff::Routine",
      "label": "Routine",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "T_PREPARE": {
      "kind": "step",
      "native_name": "NativeHandoff::PrepareStep",
      "label": "PrepareStep",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    },
    "T_COMPLETE": {
      "kind": "step",
      "native_name": "NativeHandoff::CompleteStep",
      "label": "CompleteStep",
      "description": "Synthetic proposed correspondence role.",
      "basis": null,
      "status": "proposed"
    }
  },
  "relations": {
    "L_ALLOC": {
      "kind": "allocated_to",
      "from": "F_PREPARE",
      "to": "R_SYSTEM",
      "label": "Proposed assignment",
      "basis": null
    },
    "L_PARENT_PREPARE": {
      "kind": "decomposes",
      "from": "F_HANDLE",
      "to": "F_PREPARE",
      "label": "Proposed decomposition",
      "basis": null
    },
    "L_PARENT_COMPLETE": {
      "kind": "decomposes",
      "from": "F_HANDLE",
      "to": "F_COMPLETE",
      "label": "Proposed decomposition",
      "basis": null
    },
    "L_ORDER": {
      "kind": "precedes",
      "from": "T_PREPARE",
      "to": "T_COMPLETE",
      "label": "Documentary order only",
      "basis": null
    }
  },
  "workflows": {},
  "decisions": {},
  "questions": {},
  "trade_studies": {},
  "evidence": {}
}
        */
    }
}
