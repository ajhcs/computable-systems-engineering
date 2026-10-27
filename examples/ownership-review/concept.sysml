package OwnershipExample {
 part def Platform; part def Organization;
 part integration : Platform; part alpha : Platform; part beta : Platform;
 part alphaOrg : Organization; part betaOrg : Organization; part coordinator : Organization;
 concern IntegrationNeed; concern IntegrationConcept; action def ExchangeData;
}

package 'OwnershipWorkflow' {
  concern workflowContext {
    doc cseWorkflow /*CSE-WORKFLOW/1.0
{
  "decisions": {},
  "elements": {
    "E_ALPHA": {
      "basis": "CASE",
      "description": "Alpha platform; synthetic proposed identity/responsibility only.",
      "kind": "element",
      "label": "Alpha platform",
      "native_name": "OwnershipExample::alpha",
      "status": "proposed"
    },
    "E_BETA": {
      "basis": "CASE",
      "description": "Beta platform; synthetic proposed identity/responsibility only.",
      "kind": "element",
      "label": "Beta platform",
      "native_name": "OwnershipExample::beta",
      "status": "proposed"
    },
    "F_EXCHANGE": {
      "basis": "CASE",
      "description": "Exchange selected information; synthetic proposed identity/responsibility only.",
      "kind": "function",
      "label": "Exchange selected information",
      "native_name": "OwnershipExample::ExchangeData",
      "status": "proposed"
    },
    "K_LINK": {
      "basis": "CASE",
      "description": "Two-provider integration; synthetic proposed identity/responsibility only.",
      "kind": "concept",
      "label": "Two-provider integration",
      "native_name": "OwnershipExample::IntegrationConcept",
      "status": "proposed"
    },
    "N_LINK": {
      "basis": "CASE",
      "description": "Coordinate provider information; synthetic proposed identity/responsibility only.",
      "kind": "need",
      "label": "Coordinate provider information",
      "native_name": "OwnershipExample::IntegrationNeed",
      "status": "proposed"
    },
    "ORG_ALPHA": {
      "basis": "CASE",
      "description": "Provider Alpha; synthetic proposed identity/responsibility only.",
      "kind": "actor",
      "label": "Provider Alpha",
      "native_name": "OwnershipExample::alphaOrg",
      "status": "proposed"
    },
    "ORG_BETA": {
      "basis": "CASE",
      "description": "Provider Beta; synthetic proposed identity/responsibility only.",
      "kind": "actor",
      "label": "Provider Beta",
      "native_name": "OwnershipExample::betaOrg",
      "status": "proposed"
    },
    "ORG_COORD": {
      "basis": "CASE",
      "description": "Integration coordinator; synthetic proposed identity/responsibility only.",
      "kind": "actor",
      "label": "Integration coordinator",
      "native_name": "OwnershipExample::coordinator",
      "status": "proposed"
    },
    "SYS": {
      "basis": "CASE",
      "description": "Integration service; synthetic proposed identity/responsibility only.",
      "kind": "system",
      "label": "Integration service",
      "native_name": "OwnershipExample::integration",
      "status": "proposed"
    }
  },
  "evidence": {},
  "question": {
    "basis": "CASE",
    "text": "Are constituent and interface responsibilities, agreements and withdrawal/change arrangements explicit?"
  },
  "questions": {},
  "relations": {
    "I_API": {
      "basis": "CASE",
      "from": "E_ALPHA",
      "kind": "interfaces_with",
      "label": "Shared information interface",
      "to": "E_BETA"
    },
    "L_ALPHA": {
      "basis": "CASE",
      "from": "F_EXCHANGE",
      "kind": "allocated_to",
      "label": "Alpha endpoint responsibility",
      "to": "E_ALPHA"
    },
    "L_BETA": {
      "basis": "CASE",
      "from": "F_EXCHANGE",
      "kind": "allocated_to",
      "label": "Beta endpoint responsibility",
      "to": "E_BETA"
    },
    "L_NEED": {
      "basis": "CASE",
      "from": "F_EXCHANGE",
      "kind": "addresses",
      "label": "Proposed contribution",
      "to": "N_LINK"
    }
  },
  "sources": {
    "CASE": {
      "excerpt": "Synthetic two-provider integration concept. All organizations, responsibilities and agreements are proposals.",
      "kind": "proposal",
      "sha256": "990328e315d5159b291683ca8928738d42b91121325b47f45c3f8a1b17da4f02"
    }
  },
  "trade_studies": {},
  "version": "workflow-1.0",
  "workflows": {
    "concept": {
      "conditions": "Illustrative proposed relationships, not actual agreements or implementation.",
      "focus": [
        "N_LINK",
        "K_LINK",
        "SYS",
        "E_ALPHA",
        "E_BETA",
        "ORG_ALPHA",
        "ORG_BETA",
        "ORG_COORD",
        "F_EXCHANGE"
      ],
      "next_decision": "Review roles, change impacts and withdrawal proposals with actual constituent owners.",
      "outcome": "Explicit responsibilities and unresolved commitment/continuity evidence.",
      "summary": "One jointly coordinated integration with independently controlled platforms."
    }
  }
}
    */
  }
}
package OwnershipRegister { concern ownershipContext { doc cseOwnership /*CSE-OWNERSHIP/1.0
{
  "version": "ownership-1.0",
  "items": {
    "E_ALPHA": {
      "target_kind": "element",
      "roles": {
        "own": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "operate": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "fund": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "change": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "support": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "accept": {
          "parties": [
            "ORG_ALPHA"
          ],
          "status": "proposed",
          "basis": "CASE"
        }
      },
      "facts": {
        "agreement": {
          "text": "Proposed participation arrangement; no signed agreement or authentic assent supplied.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "change_control": {
          "text": "Propose impact review and coordinate changes with the affected endpoint owners.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "withdrawal": {
          "text": "Notify affected participants and mark integration dependency unavailable pending explicit review.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        }
      }
    },
    "E_BETA": {
      "target_kind": "element",
      "roles": {
        "own": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "operate": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "fund": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "change": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "support": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "accept": {
          "parties": [
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        }
      },
      "facts": {
        "agreement": {
          "text": "Proposed participation arrangement; no signed agreement or authentic assent supplied.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "change_control": {
          "text": "Propose impact review and coordinate changes with the affected endpoint owners.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "withdrawal": {
          "text": "Notify affected participants and mark integration dependency unavailable pending explicit review.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        }
      }
    },
    "I_API": {
      "target_kind": "interface",
      "roles": {
        "own": {
          "parties": [
            "ORG_ALPHA",
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "operate": {
          "parties": [
            "ORG_COORD"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "fund": {
          "parties": [
            "ORG_COORD"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "change": {
          "parties": [
            "ORG_ALPHA",
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "support": {
          "parties": [
            "ORG_ALPHA",
            "ORG_BETA"
          ],
          "status": "proposed",
          "basis": "CASE"
        },
        "accept": {
          "parties": [
            "ORG_COORD"
          ],
          "status": "proposed",
          "basis": "CASE"
        }
      },
      "facts": {
        "agreement": {
          "text": "Proposed participation arrangement; no signed agreement or authentic assent supplied.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "change_control": {
          "text": "Propose impact review and coordinate changes with the affected endpoint owners.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        },
        "withdrawal": {
          "text": "Notify affected participants and mark integration dependency unavailable pending explicit review.",
          "status": "proposed",
          "basis": "CASE",
          "refs": [
            "ORG_ALPHA",
            "ORG_BETA",
            "I_API"
          ]
        }
      }
    }
  }
}
*/ } }
