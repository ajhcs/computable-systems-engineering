package FieldServiceDemo {
    doc /* Original synthetic station-maintenance decomposition for presentation testing.
        Documentary parentage only: no requirements, acceptance status, or execution order. */
    action def MaintainStation;
    action def PrepareServiceVisit;
    action def ReviewServiceRequest;
    action def ConfirmAccessReadiness;
    action def GatherServiceResources;
    action def InspectAndRestoreStation;
    action def InspectStationCondition;
    action def InvestigateReportedIssue;
    action def RestoreAffectedComponents;
    action def ReturnStationAndReport;
    action def ReviewPostServiceCondition;
    action def ReturnStationToCustodian;
    action def DocumentServiceFindings;

    doc cseViews /*
    CSE-VIEWS/1.0
{
    "views": [
        {
            "id": "FT_DEMO",
            "kind": "function_tree",
            "nodes": [
                {
                    "id": "F0",
                    "element": "FieldServiceDemo::MaintainStation",
                    "level": 0,
                    "parent": null
                },
                {
                    "id": "F1",
                    "element": "FieldServiceDemo::PrepareServiceVisit",
                    "level": 1,
                    "parent": "F0"
                },
                {
                    "id": "F11",
                    "element": "FieldServiceDemo::ReviewServiceRequest",
                    "level": 2,
                    "parent": "F1"
                },
                {
                    "id": "F12",
                    "element": "FieldServiceDemo::ConfirmAccessReadiness",
                    "level": 2,
                    "parent": "F1"
                },
                {
                    "id": "F13",
                    "element": "FieldServiceDemo::GatherServiceResources",
                    "level": 2,
                    "parent": "F1"
                },
                {
                    "id": "F2",
                    "element": "FieldServiceDemo::InspectAndRestoreStation",
                    "level": 1,
                    "parent": "F0"
                },
                {
                    "id": "F21",
                    "element": "FieldServiceDemo::InspectStationCondition",
                    "level": 2,
                    "parent": "F2"
                },
                {
                    "id": "F22",
                    "element": "FieldServiceDemo::InvestigateReportedIssue",
                    "level": 2,
                    "parent": "F2"
                },
                {
                    "id": "F23",
                    "element": "FieldServiceDemo::RestoreAffectedComponents",
                    "level": 2,
                    "parent": "F2"
                },
                {
                    "id": "F3",
                    "element": "FieldServiceDemo::ReturnStationAndReport",
                    "level": 1,
                    "parent": "F0"
                },
                {
                    "id": "F31",
                    "element": "FieldServiceDemo::ReviewPostServiceCondition",
                    "level": 2,
                    "parent": "F3"
                },
                {
                    "id": "F32",
                    "element": "FieldServiceDemo::ReturnStationToCustodian",
                    "level": 2,
                    "parent": "F3"
                },
                {
                    "id": "F33",
                    "element": "FieldServiceDemo::DocumentServiceFindings",
                    "level": 2,
                    "parent": "F3"
                }
            ]
        }
    ]
}
    */
}
