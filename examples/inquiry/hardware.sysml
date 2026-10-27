package AcquisitionCoverage {
    part def Resource;
    part firstModule : Resource;
    part secondModule : Resource;
    part fourChannelSpare : Resource;
    part prototypeModule : Resource;
    action def AcquireChannels;
    concern <Q> EngineeringQuestion {
        doc cseInquiry /*
CSE-INQUIRY/1.0
{
  "version": "inquiry-1.0",
  "question": {
    "text": "Can acquisition cover four channels with the first module unavailable?",
    "basis": "SRC"
  },
  "sources": {
    "SRC": {
      "sha256": "46de4eeaecec5d3b3d5219959f579f30e1d745dd2e9b9f788a536eba9baecf06",
      "excerpt": "# Original hypothetical channel-acquisition brief\nQuestion: Can acquisition cover four channels with the first module unavailable?\nWork: Acquire channels. Proposed demand: four channels. At least one assignment is required.\nExisting arrangement: First module and Second module each cover two channels.\nCandidate arrangement: Four-channel spare covers four channels.\nUnqualified arrangement: Prototype module has a proposed four-channel figure; signal compatibility is unknown.\nAssume the existing modules and spare can acquire the specified signals, and their channel counts are independently additive for this static inquiry.\nThese are original hypothetical design inputs, not vendor specifications, measurements or accepted requirements.\nSampling simultaneity, signal ranges, bandwidth, bus integration, replacement timing and operational continuity are not qualified.",
      "kind": "proposal"
    }
  },
  "functions": {
    "F_ACQUIRE": {
      "native_name": "AcquisitionCoverage::AcquireChannels",
      "label": "Acquire channels",
      "demand": {
        "value": "4",
        "unit": "channel",
        "basis": "SRC"
      },
      "minimum_assignments": 1,
      "minimum_basis": "SRC"
    }
  },
  "resources": {
    "R_FIRST": {
      "native_name": "AcquisitionCoverage::firstModule",
      "label": "First module"
    },
    "R_SECOND": {
      "native_name": "AcquisitionCoverage::secondModule",
      "label": "Second module"
    },
    "R_SPARE": {
      "native_name": "AcquisitionCoverage::fourChannelSpare",
      "label": "Four-channel spare"
    },
    "R_PROTOTYPE": {
      "native_name": "AcquisitionCoverage::prototypeModule",
      "label": "Prototype module"
    }
  },
  "alternatives": {
    "A_EXISTING": {
      "label": "Existing acquisition modules",
      "assignments": [
        {
          "function": "F_ACQUIRE",
          "resource": "R_FIRST",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "2",
            "unit": "channel",
            "basis": "SRC"
          },
          "rationale": "Two-channel contribution under the stated assumptions.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_ACQUIRE",
          "resource": "R_SECOND",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "2",
            "unit": "channel",
            "basis": "SRC"
          },
          "rationale": "Two-channel contribution under the stated assumptions.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ACQUIRE": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_SPARE": {
      "label": "Spare module candidate",
      "assignments": [
        {
          "function": "F_ACQUIRE",
          "resource": "R_SPARE",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "4",
            "unit": "channel",
            "basis": "SRC"
          },
          "rationale": "Proposed spare contribution; physical qualification remains open.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ACQUIRE": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_UNQUALIFIED": {
      "label": "Prototype candidate",
      "assignments": [
        {
          "function": "F_ACQUIRE",
          "resource": "R_PROTOTYPE",
          "capability": "unknown",
          "capability_basis": "SRC",
          "capacity": {
            "value": "4",
            "unit": "channel",
            "basis": "SRC"
          },
          "rationale": "Channel count is proposed; signal compatibility has not been established.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_ACQUIRE": {
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
