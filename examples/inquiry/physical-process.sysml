package KitWorkshop {
    part def Resource;
    part assemblyBench : Resource;
    part packingBench : Resource;
    part fasterBench : Resource;
    part sharedWorker : Resource;
    action def AssembleKits;
    action def PackKits;
    concern <Q> EngineeringQuestion {
        doc cseInquiry /*
CSE-INQUIRY/1.0
{
  "version": "inquiry-1.0",
  "question": {
    "text": "Can assembly and packing each support six kits/hour?",
    "basis": "SRC"
  },
  "sources": {
    "SRC": {
      "sha256": "860cd3401b5a29319518d6ec57397c63209ea3a4f38c6d2e20ac1141c4d59558",
      "excerpt": "# Original hypothetical kit-workshop brief\nQuestion: Can assembly and packing each support six kits/hour?\nWork sequence: Assemble kits, then pack kits. The proposed workload is six kits/hour for each function. Each function needs at least one assignment.\nExisting arrangement: Assembly bench supports four kits/hour; Packing bench supports eight kits/hour.\nCandidate arrangement: Faster assembly bench and Packing bench each support eight kits/hour, using dedicated means.\nShared-worker arrangement: Shared worker is proposed to perform either function at ten kits/hour separately; no simultaneous workload budget is provided.\nAssume the benches can perform their assigned functions and the dedicated per-function rates are applicable under the same conditions.\nAll figures and minima are original hypothetical inputs, not measurements or accepted requirements.\nThe shared worker's concurrent rates, material supply, queues, sequencing delays, quality, safety and actual process continuity are unresolved. The narrative sequence is not an executable simulation.",
      "kind": "proposal"
    }
  },
  "functions": {
    "F_ASSEMBLE": {
      "native_name": "KitWorkshop::AssembleKits",
      "label": "Assemble kits",
      "demand": {
        "value": "6",
        "unit": "kits_per_hour",
        "basis": "SRC"
      },
      "minimum_assignments": 1,
      "minimum_basis": "SRC"
    },
    "F_PACK": {
      "native_name": "KitWorkshop::PackKits",
      "label": "Pack kits",
      "demand": {
        "value": "6",
        "unit": "kits_per_hour",
        "basis": "SRC"
      },
      "minimum_assignments": 1,
      "minimum_basis": "SRC"
    }
  },
  "resources": {
    "R_ASSEMBLY": {
      "native_name": "KitWorkshop::assemblyBench",
      "label": "Assembly bench"
    },
    "R_PACKING": {
      "native_name": "KitWorkshop::packingBench",
      "label": "Packing bench"
    },
    "R_FASTER": {
      "native_name": "KitWorkshop::fasterBench",
      "label": "Faster assembly bench"
    },
    "R_SHARED": {
      "native_name": "KitWorkshop::sharedWorker",
      "label": "Shared worker"
    }
  },
  "alternatives": {
    "A_EXISTING": {
      "label": "Existing workshop",
      "assignments": [
        {
          "function": "F_ASSEMBLE",
          "resource": "R_ASSEMBLY",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "4",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Dedicated assembly under the stated assumptions.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_PACK",
          "resource": "R_PACKING",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "8",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Dedicated packing under the stated assumptions.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ASSEMBLE": {
          "method": "sum",
          "basis": "SRC"
        },
        "F_PACK": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_FASTER": {
      "label": "Faster assembly candidate",
      "assignments": [
        {
          "function": "F_ASSEMBLE",
          "resource": "R_FASTER",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "8",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Proposed faster dedicated assembly.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_PACK",
          "resource": "R_PACKING",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "8",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Dedicated packing under the stated assumptions.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ASSEMBLE": {
          "method": "sum",
          "basis": "SRC"
        },
        "F_PACK": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_SHARED": {
      "label": "Shared worker candidate",
      "assignments": [
        {
          "function": "F_ASSEMBLE",
          "resource": "R_SHARED",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "10",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Separate-function proposal; no simultaneous budget supplied.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_PACK",
          "resource": "R_SHARED",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "10",
            "unit": "kits_per_hour",
            "basis": "SRC"
          },
          "rationale": "Separate-function proposal; no simultaneous budget supplied.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ASSEMBLE": {
          "method": "sum",
          "basis": "SRC"
        },
        "F_PACK": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    }
  }
}
        */
    }
}
