package FlowExample {
    part def Resource;
    part station : Resource;
    concern <Q> EngineeringQuestion {
        doc cseInquiry /*
CSE-INQUIRY/1.0
{
  "version": "inquiry-1.1",
  "question": {
    "text": "Are the declared mean-flow values conditionally consistent?",
    "basis": "FLOW_SRC"
  },
  "sources": {
    "FLOW_SRC": {
      "sha256": "3753bdbf40acc8b6c947919f7e36490ad55cde00824e0e98f47d745f40810a25",
      "excerpt": "Synthetic mean-flow consistency case, not observations or staffing evidence.",
      "kind": "proposal"
    }
  },
  "functions": {},
  "resources": {
    "R_STATION": {
      "native_name": "FlowExample::station",
      "label": "Illustrative request station"
    }
  },
  "alternatives": {},
  "flow_checks": {
    "FLOW": {
      "label": "Declared request means",
      "subject": "R_STATION",
      "boundary": "Entry to exit of the illustrative station.",
      "population": "Requests inside this same station.",
      "averaging_context": "Hypothesized compatible stationary means, not a finite observed sample.",
      "units": {
        "population": "requests",
        "time": "minute"
      },
      "conditions": {
        "finite_means": {
          "value": true,
          "basis": "FLOW_SRC"
        },
        "strict_stationarity": {
          "value": true,
          "basis": "FLOW_SRC"
        },
        "metrically_transitive_arrivals": {
          "value": true,
          "basis": "FLOW_SRC"
        },
        "matched_boundary_population": {
          "value": true,
          "basis": "FLOW_SRC"
        },
        "compatible_averaging": {
          "value": true,
          "basis": "FLOW_SRC"
        }
      },
      "L": {
        "value": "2",
        "unit": "requests",
        "basis": "FLOW_SRC"
      },
      "arrival_rate": {
        "value": "1",
        "unit": "requests_per_minute",
        "basis": "FLOW_SRC"
      },
      "W": {
        "value": "2",
        "unit": "minute",
        "basis": "FLOW_SRC"
      },
      "tolerance": {
        "value": "0",
        "unit": "requests",
        "basis": "FLOW_SRC"
      }
    }
  }
}
        */
    }
}
