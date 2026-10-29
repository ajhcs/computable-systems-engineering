# Current-system views and reconciliation

The optional `configuration-review view` route derives a current-system reader
from a fresh native `configuration-1.1` review. It produces `system.svg`, a
standalone `index.html` reader, and `view.json` with the semantic ledger. The SVG
is an editable simplified model-derived presentation, not native graphical SysML
interchange or an executable architecture.

The graph retains the scoped current root, selected logical roles, explicit
external peers and reconciled binary connection endpoints. Every displayed node
has its native identity, direct type and selected parent. Connection aliases
`C1`, `C2`, and so on map to exact retained connection IDs in the reader and
ledger. Endpoint tables retain the complete linked native feature paths. An
anonymous connection is identified honestly by its scoped owner and endpoint
pair; no unstable parser UUID or source-line identity is invented.

Ordinary connections are undirected adjacency. Lines have no arrowheads and do
not claim item-flow direction, vendor protocol compatibility, timing, execution,
installation or complete system adequacy. Blue cards identify selected roles;
purple cards identify external peers. Position alone expresses no engineering
relation. Selected parent identities remain explicit in the card and table.
Open alternatives are listed separately and do not become current graph nodes.

Only reconciled facts are drawn. A failed or unsupported required check remains
visible in the result, findings and omission list. The reader also lists native
current-context connections outside the retained scope; an empty connection
scope cannot masquerade as complete topology coverage. A partial view can be
saved for investigation, but its command and subsequent check remain
unsuccessful. A native input error with no graph produces a view error instead
of an apparent successful diagram.

Native parser diagnostics retain their severity, source and line in a dedicated
reader section. The SVG shows their count and warning count; the ledger retains
the full native records. A warning in an unselected historical declaration does
not automatically fail a valid retained-scope review, but it remains visible.

From the complete checkout or an installed drafting launcher:

```text
python3 skills/develop-system-concept/scripts/cse.py configuration-review fingerprint examples/configuration-review/connected/scope.json
python3 skills/develop-system-concept/scripts/cse.py configuration-review view examples/configuration-review/connected/library.sysml examples/configuration-review/connected/current.sysml --scope examples/configuration-review/connected/scope.json --scope-sha256 RETAINED_DIGEST --output work/current-system-view
python3 skills/develop-system-concept/scripts/cse.py configuration-review check-view examples/configuration-review/connected/library.sysml examples/configuration-review/connected/current.sysml --scope examples/configuration-review/connected/scope.json --scope-sha256 RETAINED_DIGEST --view work/current-system-view
```

The standalone CLI is `python3 scripts/configuration.py`. All three drafting
launchers expose the route. Existing `check` and `fingerprint` uses remain
available. The version-1.0 declaration-only contract does not manufacture a
connected view; select the explicit 1.1 scope when connected obligations apply.
The output parent must exist and the destination directory must be new. No
existing artifact is overwritten. Keep screenshots or independent review notes
outside this three-file generated directory.

`check-view` reruns native reconciliation from the explicit model file set and
retained scope. It regenerates the three artifacts deterministically in memory
and compares their bytes with the saved files. It never adopts facts or success
labels from the saved ledger. Missing, extra, symlinked, modified, stale or
retargeted artifacts cannot pass. An added unselected native connection changes
the omission ledger and invalidates the old view even when the retained required
connections still reconcile. A scope change requires its new retained digest;
the old digest cannot qualify a view for that changed scope.

The ledger binds the actual model files and aggregate model digest, scope digest,
configuration module digest, native parser result, the complete configuration
report digest, and renderer source digest. These identify the supplied bytes and
tool output; they do not authenticate engineer assent or provide a protected
runner. Exact artifact comparison deliberately flags presentation edits as well
as topology edits. A changed editable SVG requires regeneration or a separately
reviewed presentation route; arbitrary edits are not silently accepted as source
truth. `view_status` reports artifact fidelity, while overall status also retains
the actual configuration result. Consistent artifacts for a failed configuration
do not produce an overall pass.

Each artifact is bounded to 32 MB. The graph is bounded by the configuration
contract to 513 nodes and 256 edges. Narrow screens scroll the SVG at readable
size rather than shrinking its labels; tables provide the exact text alternative.
XML/source checks and fresh native comparisons establish their declared scopes.
Actual pixel inspection, useful interaction, native-tool edit/save/reopen,
behavior and engineering acceptance are separate observations.
