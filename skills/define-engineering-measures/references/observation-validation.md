# Computing a defined measure from observations

Read this reference when the engineer has supplied aligned observation values
or prediction bounds and asks for interval scores, weighted summaries, or a
conditional Bernoulli probability. Defining a measure alone does not require
an observation run.

Use the versioned [observation contract](../../../docs/observation-validation.md)
and its synthetic example. Retain the existing measure ID/revision and record
the dataset's population, boundary, window, sampling, role and source basis.
Keep training, calibration, held-out and simulation roles explicit. Do not
infer that a dataset is independent, representative or held out from its name.

Run `python3 /absolute/checkout/scripts/validate_observations.py RECORD.json`
with repeated `--required CHECK_ID` when an expected set is already selected.
Repair schema and draft-data errors within the engineer's stated meaning;
surface changed exclusions, weights, applicability or acceptance thresholds as
proposals. Keep the JSON result beside its exact input revision.

A successful run means the bounded computation completed. Report realized
coverage together with width and score. Weight effective size describes weight
concentration, not independent information. Binomial tails are conditional on
the selected model assumptions. Unknown applicability prevents required
success; assumption text and hashes do not verify source truth, future
coverage, physical fidelity or engineering acceptance.
