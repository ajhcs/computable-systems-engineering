# xPPU Scenario15: what belongs to the unit?

The selected native PPU Block directly owns seven modules: stack, crane, stamp, large sorting conveyor, PicAlpha conveyor, small sorting conveyor and refill conveyor. All seven source properties are composite and have multiplicity1. This is ownership, not workpiece order or a new equipment allocation.

The chapter describes a laboratory production plant that manipulates and sorts workpieces. Its ISA88 discussion distinguishes unit, equipment and control modules. The author’s Scenario15 Overview depicts the selected seven compositions; its Boolean flags, module internals, operations and state machines carry additional meaning that this structural projection excludes. Fig12.11 and chapter4 §4.3/Fig4.17 provide English/use-case context and have broader, different scopes.

Use the containment reading to answer “what does PPU own?” Use the relationship reading to recover role/type/multiplicity and composition without implying process direction. The original UML, notation and empty DI remain byte-preserved. The v2 file is a bounded structural transcription, not an executable xPPU controller.

Sources: [model](https://github.com/x-PPU/Models/tree/c3aedf66f3e9695e6a7751ae62d17c64b1bc373c), [Bougouffa et al.2019 chapter12](https://doi.org/10.1007/978-3-030-13499-0_12), [chapter4](https://doi.org/10.1007/978-3-030-13499-0_4). Research demonstrator; no commercial deployment claim.
