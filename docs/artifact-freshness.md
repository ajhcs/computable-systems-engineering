# Artifact freshness

Use `scripts/artifacts.py` when a calculation, drawing or document depends on
several files. This helper checks that the declared sources and delivered files
still match one captured run. It does not judge the model, execute a generator,
interpret a result, or approve a design. A fresh report can contain a failed
engineering check.

Keep the engineering claims in their existing model and evidence records. The
artifact plan is a file dependency list, not a competing engineering schema.

## Plan and generate

Select every input that can change the result: model, parameters, equations,
solver/renderer code, configuration, and external data or tool-version receipt.
Select all required outputs, including calculation reports, SVG, PDF and render
inspection records. Give outputs a new run directory. Output files must be
absent at `begin`; this prevents an old successful export from qualifying a
generator that produced nothing. The helper does not delete or replace files.

An `artifact-bundle-1.0` plan has exactly these fields:

```json
{
  "version": "artifact-bundle-1.0",
  "id": "DriveStudy",
  "revision": "1",
  "inputs": {"Model": "model.sysml", "Parameters": "inputs.json", "Builder": "build.py"},
  "outputs": {"Results": "run-02/results.json", "Drawing": "run-02/diagram.svg", "Document": "run-02/brief.pdf"}
}
```

Paths are relative to the supplied project root. IDs and paths must be unique
across both maps. Empty maps, empty files, symlinks, parent traversal, absolute
paths and unknown fields are refused. Limits are 128 files, 32 MiB per file,
128 MiB total, 512 characters per path, and 256 KiB per JSON record.

```text
python3 <runtime>/scripts/artifacts.py begin --root PROJECT --plan PLAN.json --out STARTED.json
```

Retain the returned `plan_sha256` as `DIGEST`. Run the selected generator and
engineering checks. Then bind the new outputs:

```text
python3 <runtime>/scripts/artifacts.py finish --root PROJECT --plan PLAN.json --plan-sha256 DIGEST --receipt STARTED.json --out COMPLETE.json
python3 <runtime>/scripts/artifacts.py check --root PROJECT --plan PLAN.json --plan-sha256 DIGEST --receipt COMPLETE.json
```

`finish` refuses changed sources, missing outputs and incomplete receipts.
`check` is read-only and refuses altered sources, outputs or file scope. Receipt
paths must be separate from the artifacts and must not already exist. Exit 0
means the named freshness operation passed; exit 2 means it could not complete.
All failures remain non-success, including file errors and resource limits.

The Python API is `verifier.artifacts.begin`, `finish` and `check`; `load` returns
a parsed record and its raw-byte digest. API callers retain and compare the
actual plan digest just as the CLI does. Files are never executable expressions.

## Review the meaning separately

Inspect the actual exported pages and compare the model's endpoints, quantities,
directions and units with the figure. A figure key must cover every displayed
quantity, including torque when a connection carries N m. Bind the inspection
record to the inspected files. A successful exporter or a matching digest cannot
establish diagram fidelity or visual quality.

The scope and receipts are local caller-supplied records. They are not signatures
or protected execution. Replacing both a file and its receipt is outside this
freshness check. Dependencies omitted from the plan remain untracked. Retain the
plan digest separately; do not narrow scope or regenerate receipts to erase a
failed check. Regenerate affected outputs in a new run and keep the failed run.
