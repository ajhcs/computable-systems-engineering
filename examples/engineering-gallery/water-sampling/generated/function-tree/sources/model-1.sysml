package WaterSampling {
    private import ScalarValues::Boolean;
    private import ScalarValues::String;
    private import ISQBase::DurationValue;
    doc /* SYNTHETIC DEMONSTRATION ONLY. Original fictional water-quality sample
      logistics station, not a water treatment or public-health decision system.
      Every need, obligation, threshold, component, allocation and operation is a
      fictional demonstration choice, not real accepted engineering intent.
      Boundary: container intake records, identification holds and custody handoff.
      Excludes collection chemistry, analytical validity, refrigeration, contamination,
      equipment reliability, physical security, clinical and public-health suitability.
      Candidate A: staffed local register; candidate B: offline station with local
      receipts and later synchronization. B is the demonstrated concept, not a
      real engineering selection. Offline synchronization remains qualitative.
      Open questions: real custody policy, label reconciliation authority, storage
      duration, power budget and environmental limits require stakeholder work. */
    doc cseClock /* CSE-CLOCK/2.0
    period 1 second */
    part def IntakePanel;
    part def ReceiptRegister;
    part def HoldingRack;
    part def Station {
        doc /* Fictional candidate components: panel accepts requests; register
          preserves provisional or reconciled receipts; rack holds containers.
          These declarations establish composition only, not connector topology,
          implementation or physical capacity. A provisional receipt may state
          HELD with identity unresolved; it never authorizes pickup. */
        part intakePanel : IntakePanel;
        part receiptRegister : ReceiptRegister;
        part holdingRack : HoldingRack;
        in attribute intakeRequested : Boolean;
        out attribute receiptRecorded : Boolean;
        out attribute processingElapsed : DurationValue {
            doc cseType /* CSE-INT/2.0
            range 0 20 scale 1 unit second */
        }
        in event occurrence containerPresented { attribute correlationId : String; }
        out event occurrence receiptIssued { attribute correlationId : String; }
    }
    part def Operator;
    part def Courier;
    part def Custodian;
    part operator : Operator;
    part station : Station;
    part courier : Courier;
    part custodian : Custodian;
    concern <N_IDENTITY> PreserveIdentity { doc /* Fictional stakeholder need: The operator needs sample identity preserved through custody transfer. */ }
    concern <N_ACCOUNT> AccountForContainers { doc /* Fictional stakeholder need: The courier needs a reconciled record of containers accepted for pickup. */ }
    concern <N_SERVICE> RecoverService { doc /* Fictional stakeholder need: The custodian needs a declared intake pause and controlled restoration. */ }
    action def ManageSampleHandoff;
    action def ReceiveSample;
    action def IdentifyContainer;
    action def RecordReceipt;
    action def PreserveHandoffRecord;
    action def HoldUnidentifiedContainer;
    action def ReconcileLabel;
    action def ReleaseSample;
    action def MatchCourierManifest;
    action def RecordCustodyTransfer;
    action def MaintainStation;
    action def SuspendIntake;
    action def InspectAndRestore;
    use case <UC_NOMINAL> TransferLabeledSample { subject unit = station; actor user = operator; doc /* Nominal: present labeled container; record receipt; match pickup manifest; record custody transfer. Success means a documentary transfer record, not analytical sample validity. These are documentary exchanges, not executable SysML guards/effects. */ }
    use case <UC_RECOVERY> RecoverUnidentifiedSample { subject unit = station; actor user = operator; doc /* Exception and recovery: unreadable label leads to hold; operator supplies corrected identity; station records reconciliation before release. Reconciliation authority is fictional and requires real policy work. These are documentary exchanges, not executable SysML guards/effects. */ }
    use case <UC_MAINTENANCE> RecordStationInspection { subject unit = station; actor user = custodian; doc /* Lifecycle: declare pause; suspend intake; inspect and restore equipment; record inspection with return-to-service approval pending. Intake remains suspended at this demonstrated outcome. Operational release is a separate decision; no physical repair simulation or reliability claim. These are documentary exchanges, not executable SysML guards/effects. */ }
    requirement <R_RECORD> RecordReceiptObligation { doc cseSource /* CSE-SOURCE/2.0
    SYN-WATER-01 */ subject unit = station; require constraint receipt { doc cse /* CSE-REQ/2.0
    Upon unit.intakeRequested = true, unit shall within 2 seconds satisfy unit.receiptRecorded = true. */ } }
    requirement <R_ELAPSED> BoundProcessingObservation { doc cseSource /* CSE-SOURCE/2.0
    SYN-WATER-02 */ subject unit = station; require constraint duration { doc cse /* CSE-REQ/2.0
    Whenever unit.receiptRecorded = true, unit shall always satisfy unit.processingElapsed <= 4 second. */ } }
    requirement <R_CORRELATION> MatchEachReceipt { doc cseSource /* CSE-SOURCE/2.0
    SYN-WATER-03 */ subject unit = station; require constraint correlation { doc cse /* CSE-EVENT/2.0
    Each unit.containerPresented shall within 2 seconds have unit.receiptIssued with matching correlationId. */ } }
    doc cseViews /* CSE-VIEWS/1.0
{
  "views": [
    {
      "id": "FT_STATION",
      "kind": "function_tree",
      "nodes": [
        {
          "id": "F0",
          "element": "WaterSampling::ManageSampleHandoff",
          "level": 0,
          "parent": null
        },
        {
          "id": "F1",
          "element": "WaterSampling::ReceiveSample",
          "level": 1,
          "parent": "F0"
        },
        {
          "id": "F11",
          "element": "WaterSampling::IdentifyContainer",
          "level": 2,
          "parent": "F1"
        },
        {
          "id": "F12",
          "element": "WaterSampling::RecordReceipt",
          "level": 2,
          "parent": "F1"
        },
        {
          "id": "F2",
          "element": "WaterSampling::PreserveHandoffRecord",
          "level": 1,
          "parent": "F0"
        },
        {
          "id": "F21",
          "element": "WaterSampling::HoldUnidentifiedContainer",
          "level": 2,
          "parent": "F2"
        },
        {
          "id": "F22",
          "element": "WaterSampling::ReconcileLabel",
          "level": 2,
          "parent": "F2"
        },
        {
          "id": "F3",
          "element": "WaterSampling::ReleaseSample",
          "level": 1,
          "parent": "F0"
        },
        {
          "id": "F31",
          "element": "WaterSampling::MatchCourierManifest",
          "level": 2,
          "parent": "F3"
        },
        {
          "id": "F32",
          "element": "WaterSampling::RecordCustodyTransfer",
          "level": 2,
          "parent": "F3"
        },
        {
          "id": "F4",
          "element": "WaterSampling::MaintainStation",
          "level": 1,
          "parent": "F0"
        },
        {
          "id": "F41",
          "element": "WaterSampling::SuspendIntake",
          "level": 2,
          "parent": "F4"
        },
        {
          "id": "F42",
          "element": "WaterSampling::InspectAndRestore",
          "level": 2,
          "parent": "F4"
        }
      ]
    },
    {
      "id": "SQ_NOMINAL",
      "kind": "sequence",
      "participants": [
        {
          "id": "operator",
          "element": "WaterSampling::operator"
        },
        {
          "id": "station",
          "element": "WaterSampling::station"
        },
        {
          "id": "courier",
          "element": "WaterSampling::courier"
        }
      ],
      "exchanges": [
        {
          "id": "SQ_NOMINAL_E1",
          "from": "operator",
          "to": "station",
          "message": "Present labeled container and sample ID"
        },
        {
          "id": "SQ_NOMINAL_E2",
          "from": "station",
          "to": "operator",
          "message": "Return receipt with matching sample ID"
        },
        {
          "id": "SQ_NOMINAL_E3",
          "from": "courier",
          "to": "station",
          "message": "Present pickup manifest"
        },
        {
          "id": "SQ_NOMINAL_E4",
          "from": "station",
          "to": "courier",
          "message": "Return custody transfer record"
        }
      ]
    },
    {
      "id": "SQ_RECOVERY",
      "kind": "sequence",
      "participants": [
        {
          "id": "operator",
          "element": "WaterSampling::operator"
        },
        {
          "id": "station",
          "element": "WaterSampling::station"
        }
      ],
      "exchanges": [
        {
          "id": "SQ_RECOVERY_E1",
          "from": "operator",
          "to": "station",
          "message": "Present container with unreadable label"
        },
        {
          "id": "SQ_RECOVERY_E2",
          "from": "station",
          "to": "operator",
          "message": "Issue hold notice; container remains unreleased"
        },
        {
          "id": "SQ_RECOVERY_E3",
          "from": "operator",
          "to": "station",
          "message": "Supply corrected identification"
        },
        {
          "id": "SQ_RECOVERY_E4",
          "from": "station",
          "to": "operator",
          "message": "Confirm reconciliation and receipt"
        }
      ]
    },
    {
      "id": "SQ_MAINTENANCE",
      "kind": "sequence",
      "participants": [
        {
          "id": "custodian",
          "element": "WaterSampling::custodian"
        },
        {
          "id": "station",
          "element": "WaterSampling::station"
        },
        {
          "id": "operator",
          "element": "WaterSampling::operator"
        }
      ],
      "exchanges": [
        {
          "id": "SQ_MAINTENANCE_E1",
          "from": "custodian",
          "to": "station",
          "message": "Request maintenance window"
        },
        {
          "id": "SQ_MAINTENANCE_E2",
          "from": "station",
          "to": "operator",
          "message": "Announce intake suspended"
        },
        {
          "id": "SQ_MAINTENANCE_E3",
          "from": "custodian",
          "to": "station",
          "message": "Record inspection and restoration"
        },
        {
          "id": "SQ_MAINTENANCE_E4",
          "from": "station",
          "to": "operator",
          "message": "Inspection recorded; return-to-service approval pending"
        }
      ]
    }
  ]
}
    */
}
