// Synthetic physical-view and source-preservation fixture. No equipment claims.
package DiagramComposition {
    part def Device;
    part def Base { part inherited : Device; }
    part def Assembly :> Base;
    part current : Assembly {
        part <LEFT> left [2] : Device;
        part optional [0..1] : Device;
        part suppressed [0] : Device;
        part unbounded [1..*] : Device;
        ref part peer : Device;
    }
    part def Catalog { part def Module; }

    doc cseViews /* CSE-VIEWS/1.1
    {
      "views": [
        {
          "id": "PC_USAGE", "kind": "physical_composition", "mode": "usages",
          "nodes": [
            {"id": "Root", "element": "DiagramComposition::current", "parent": null, "level": 0, "edge": null},
            {"id": "Left", "element": "DiagramComposition::current::left", "parent": "Root", "level": 1, "edge": "OwnLeft"},
            {"id": "Optional", "element": "DiagramComposition::current::optional", "parent": "Root", "level": 1, "edge": "OwnOptional"},
            {"id": "Suppressed", "element": "DiagramComposition::current::suppressed", "parent": "Root", "level": 1, "edge": "OwnSuppressed"},
            {"id": "Unbounded", "element": "DiagramComposition::current::unbounded", "parent": "Root", "level": 1, "edge": "OwnUnbounded"}
          ]
        },
        {
          "id": "PC_DEFINITION", "kind": "physical_composition", "mode": "definitions",
          "nodes": [
            {"id": "Catalog", "element": "DiagramComposition::Catalog", "parent": null, "level": 0, "edge": null},
            {"id": "Module", "element": "DiagramComposition::Catalog::Module", "parent": "Catalog", "level": 1, "edge": "OwnModule"}
          ]
        }
      ]
    }
    */
}
