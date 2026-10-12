# Selecting a real engineering reference

Start with [the original-source triples](../examples/engineering-reference/README.md), not a plausible invented diagram. TMT APS is actual development-project engineering; APE is a reverse-engineered/simplified reference based on real hardware. Preserve that distinction.

Choose one question: composite lifecycle/abort, English-to-constraint bindings, ownership/cardinality, or nested boundary/ports. Read the original native-model link, its matching English section and source diagram before the adaptation. Keep source version, pin, author and rights with the selection; a v1 source is not original v2.

Use the smallest matched slice that retains the relationships needed to answer the question. Record retained and omitted IDs and explain meaningful translation changes. Preserve state boundaries, trigger/effect identity, units, cardinality and connector kind. If English and formal constraints disagree, show both meanings instead of silently reconciling them.

Check whether values are defaults or fixed bindings: a v1 defaultValue must remain overridable in the v2 transcription. Put composition roles and cardinalities at association ends or in the owning block's parts compartment. Preserve original port stereotypes and visibility in the source trace; document any partial port translation, glyph omission or necessary visibility adaptation. Port arrow glyphs do not by themselves justify directional item flows.

New layouts and v2 transcriptions remain labelled derivatives. Edit model meaning before presentation. Run the pinned parser, bounded source/derivative checks and actual rendering review, reporting their limits separately from native-tool execution and engineer acceptance. Original figures/photos remain linkouts or private critical-review material unless their separate reuse rights are established.

The [rejected invented reference set](diagram-reference-draft-status.md) remains experimental history. Its pilot measurements are not evidence about this source-grounded set. These new local references await engineering review; they authorize no publication or rollout.
