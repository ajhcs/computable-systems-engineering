package BackupProcessing {
    part def Resource;
    part primaryWorker : Resource;
    part backupWorker : Resource;
    part largerBackup : Resource;
    part experimentalWorker : Resource;
    action def ProcessJobs;
    concern <Q> EngineeringQuestion {
        doc cseInquiry /*
CSE-INQUIRY/1.0
{
  "version": "inquiry-1.0",
  "question": {
    "text": "Can fallback processing meet 12 jobs/minute if the primary worker is unavailable?",
    "basis": "SRC"
  },
  "sources": {
    "SRC": {
      "sha256": "9125d24bcf74b8c72b3f13a8cec644f430165423a6699c38c63f47591aea5d2b",
      "excerpt": "# Original hypothetical backup-processing brief\nQuestion: Can fallback processing meet 12 jobs/minute if the primary worker is unavailable?\nWork: Process jobs. Proposed workload: 12 jobs/minute. At least one assignment is required.\nExisting arrangement: Primary worker (20 jobs/minute) and Backup worker (8 jobs/minute).\nCandidate arrangement: Primary worker plus Larger backup worker (16 jobs/minute).\nUnqualified arrangement: Experimental worker has a proposed rate of 24 jobs/minute; whether it can process these jobs is unknown.\nFor the first two arrangements, assume the named workers can perform this function, have independent additive rates, and meet the same operating conditions.\nAll rates, capability assertions, minima and the workload are invented design inputs, not measured service performance or accepted requirements.\nNo recovery timing, job correctness, queueing, failover mechanism or continuity has been demonstrated.",
      "kind": "proposal"
    }
  },
  "functions": {
    "F_PROCESS": {
      "native_name": "BackupProcessing::ProcessJobs",
      "label": "Process jobs",
      "demand": {
        "value": "12",
        "unit": "jobs_per_minute",
        "basis": "SRC"
      },
      "minimum_assignments": 1,
      "minimum_basis": "SRC"
    }
  },
  "resources": {
    "R_PRIMARY": {
      "native_name": "BackupProcessing::primaryWorker",
      "label": "Primary worker"
    },
    "R_BACKUP": {
      "native_name": "BackupProcessing::backupWorker",
      "label": "Backup worker"
    },
    "R_LARGER": {
      "native_name": "BackupProcessing::largerBackup",
      "label": "Larger backup worker"
    },
    "R_EXPERIMENTAL": {
      "native_name": "BackupProcessing::experimentalWorker",
      "label": "Experimental worker"
    }
  },
  "alternatives": {
    "A_EXISTING": {
      "label": "Existing workers",
      "assignments": [
        {
          "function": "F_PROCESS",
          "resource": "R_PRIMARY",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "20",
            "unit": "jobs_per_minute",
            "basis": "SRC"
          },
          "rationale": "Primary processing under the stated assumptions.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_PROCESS",
          "resource": "R_BACKUP",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "8",
            "unit": "jobs_per_minute",
            "basis": "SRC"
          },
          "rationale": "Fallback processing under the stated assumptions.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_PROCESS": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_LARGER": {
      "label": "Larger backup candidate",
      "assignments": [
        {
          "function": "F_PROCESS",
          "resource": "R_PRIMARY",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "20",
            "unit": "jobs_per_minute",
            "basis": "SRC"
          },
          "rationale": "Primary processing under the stated assumptions.",
          "rationale_basis": "SRC"
        },
        {
          "function": "F_PROCESS",
          "resource": "R_LARGER",
          "capability": "capable",
          "capability_basis": "SRC",
          "capacity": {
            "value": "16",
            "unit": "jobs_per_minute",
            "basis": "SRC"
          },
          "rationale": "Proposed larger fallback; qualification remains an engineering task.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_PROCESS": {
          "method": "sum",
          "basis": "SRC"
        }
      },
      "concurrency_basis": null
    },
    "A_UNQUALIFIED": {
      "label": "Unqualified candidate",
      "assignments": [
        {
          "function": "F_PROCESS",
          "resource": "R_EXPERIMENTAL",
          "capability": "unknown",
          "capability_basis": "SRC",
          "capacity": {
            "value": "24",
            "unit": "jobs_per_minute",
            "basis": "SRC"
          },
          "rationale": "Rate is proposed; capability for these jobs has not been established.",
          "rationale_basis": "SRC"
        }
      ],
      "composition": {
        "F_PROCESS": {
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
