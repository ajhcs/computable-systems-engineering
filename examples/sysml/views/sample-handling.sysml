package SampleHandling {
    doc /* Entirely synthetic view-check example. No engineering acceptance claimed. */
    part def Operator;
    part def Station;
    part def Archive;
    part operator : Operator;
    part station : Station;
    part archive : Archive;

    action def ProcessSample;
    action def CaptureSample;
    action def StoreSample;
    action def ValidateSample;

    doc cseViews /*
    CSE-VIEWS/1.0
    {"views": [
        {"id": "FT", "kind": "function_tree", "nodes": [
            {"id": "F0", "element": "SampleHandling::ProcessSample", "level": 0, "parent": null},
            {"id": "F1", "element": "SampleHandling::CaptureSample", "level": 1, "parent": "F0"},
            {"id": "F2", "element": "SampleHandling::StoreSample", "level": 1, "parent": "F0"},
            {"id": "F3", "element": "SampleHandling::ValidateSample", "level": 2, "parent": "F1"}
        ]},
        {"id": "SQ", "kind": "sequence", "participants": [
            {"id": "OP", "element": "SampleHandling::operator"},
            {"id": "ST", "element": "SampleHandling::station"},
            {"id": "AR", "element": "SampleHandling::archive"}
        ], "exchanges": [
            {"id": "E1", "from": "OP", "to": "ST", "message": "Submit sample for capture",
             "timing": {"min": 0, "max": 2, "unit": "seconds", "basis": "Elapsed after synthetic scenario trigger"}},
            {"id": "E2", "from": "ST", "to": "AR", "message": "Send validated sample record",
             "timing": {"min": 1, "max": 4, "unit": "seconds", "basis": "Elapsed after E1 completes"}}
        ]}
    ]}
    */
}
