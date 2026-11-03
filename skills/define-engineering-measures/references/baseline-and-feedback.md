# Baseline and feedback

Read this when revising a definition or using an observed discrepancy to guide
design. Keep the old record immutable and write a proposed revision to another
file. Run the definition checker on both, then compare them. Preserve the
observations' original definition ID, revision and meaning digest.

Treat these changes as meaning changes: quantity/scale, an input definition,
formula, unit, population/boundary, aggregation/weighting, exclusions,
window/inclusion, sampling, context/conditions or uncertainty method. Even an
apparently editorial edit inside those fields breaks exact declared equivalence.
This conservative result requests engineering review; it does not prove that
the natural-language meanings differ. No algebraic normalization, unit conversion
or inferred synonymy is applied. Renaming an input also changes the definition.

Label, source/provenance and trace-link changes are listed separately as
metadata. Review them for authority or lineage changes even when the meaning
digest stays equal. Changed content needs a new revision. A digest is evidence
of bytes or content, not evidence of accepted meaning.

Equal definitions still require a collection review before comparing observed
results: population changes, case mix, missingness, device/calibration changes,
timing, sampling bias and uncertain conditions can invalidate a comparison.
Keep those unresolved rather than declaring comparability from two matching
records. If a meaning field changed, identify whether observations can be
reprocessed under one definition, require an explicit bridging study, or keep
separate baselines. Do not invent the bridging result.

When using feedback, retain the discrepancy and evidence, the design question it
raises, the proposed corrective action and the follow-up measure definition.
Ask who owns the response, what evidence would justify changing course, and
what engineer-selected stopping condition applies. Neither a changed metric nor
a subsequent improvement establishes that the action caused the improvement.
Use [engineering evidence planning](../../plan-engineering-evidence/SKILL.md)
when a broader comparison or evaluation plan is needed. Queue analysis and
statistical inference remain separate capabilities.
