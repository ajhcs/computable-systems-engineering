# Current configuration reconciliation

The baseline contract below is `configuration-1.0`. The explicit connected-context
contract `configuration-1.1` is described at the end of this document.

`configuration-review` is an optional check of one explicitly selected design
context against a separately retained `configuration-1.0` scope. It checks native
identities, direct types and selected role membership. It does not select a design,
instantiate installed equipment, infer quantities, or approve a configuration.
Historical option definitions can remain in the same explicit model bundle.

Use the [synthetic example](../examples/configuration-review/scope.json) as the
contract. The scope has exactly `version`, `root`, `selected_roles`,
`open_alternatives`, and `connections`. `root` names one package-level native
part usage and its exact direct type. Each selected role names its exact native
declaration, exact direct type and parent (`$root` or another selected role ID).
This selected parent chain is checked against parsed ownership and explicit type
generalization, including declarations owned directly by the selected usage.
An override owned by that usage prevents selecting the historical declaration,
even when its parent type has not changed. Merely finding a role somewhere in an imported library is
insufficient. Parent cycles and duplicate selected native identities are refused.

An inherited declaration can be selected when linked explicit generalizations
prove membership. If a descendant redefines it, the historical declaration cannot
stand in for the overriding role: retain the overriding declaration explicitly.
This profile does not expand native instances or resolve arbitrary value-bound
contexts. Root usage specialization and selected role value bindings are
unsupported. A role with usage specialization can be reconciled as a leaf, but
selecting its children is unsupported because inherited usage-owned members are
not resolved. Direct types must match exactly; a compatible subtype is not silently
accepted as the retained type. Definitions and roles outside the selected chain
are not enumerated as selected equipment.

Each selected root/role must also have a supported positive lower multiplicity.
A zero upper bound fails as suppressed; an optional lower bound returns unknown.
Inherited and complex bounds return unsupported in this first profile. Authored
declaration presence alone cannot establish that the selected role is present.

Native variation contexts and variant declarations return `unsupported`, even
when their declarations have positive default multiplicity. This profile does
not resolve native variant selection. Explicit type ancestry must be available
so an inherited variation context cannot silently pass.

`open_alternatives` lists exact qualified part-definition identities that remain
available, with no automatic selection. An exact type cannot be both explicitly
open and selected. A base definition in this list does not exclude a distinct
selected subtype. This list is not proof of a complete alternative space or an
unresolved native variability condition. Connections are explicit `{from,to}`
requests; linked native endpoints are not extracted in this increment, so every
requested connection returns `unsupported` and prevents overall success. An empty
connection list makes no connectivity claim.

From a full checkout/plugin, the drafting launchers expose:

```text
python3 skills/develop-system-concept/scripts/cse.py configuration-review fingerprint examples/configuration-review/scope.json
python3 skills/develop-system-concept/scripts/cse.py configuration-review check examples/configuration-review/library.sysml examples/configuration-review/current.sysml --scope examples/configuration-review/scope.json --scope-sha256 RETAINED_DIGEST
```

The standalone equivalent is `python3 scripts/configuration.py`. `check` accepts
one or more explicit model files; no imports or other source paths are discovered
from model text. The native checker and shared bundle capture enforce up to 128
files and 5 MB combined. Scope JSON is bounded to 1 MB, 256 selected roles and 256
open alternatives/connections, rejects duplicate keys and unknown fields, and
never executes model text. The scope digest is required. It identifies retained
scope bytes, not authenticated engineer acceptance.

Every report binds the actual model file hashes, aggregate model digest, scope
digest, checker digest and native parser result. Optional
`--expected-model-sha256 DIGEST` refuses a stale model revision before reconciliation.
Without it, the new candidate is evaluated against the same retained selection
scope and its actual revision is reported. Changing a selection requires an
engineer-directed scope revision and new retained digest; the command never
rewrites scope. Inputs changed during checking invalidate the result and its
current view. Parser errors and unsupported requests cannot produce success.

The default readable view names the current root, reconciled selected roles,
parent chains, open library alternatives and findings. `--json` supplies the same
facts for a derived current view. Native connection checks, architecture
completeness, behavior, feasibility, installation, procurement and acceptance are
outside this profile. A passing result means only the retained configuration
claims supported by this contract match the supplied native bundle.

## Connected contexts — explicit configuration-1.1

The opt-in `configuration-1.1` scope adds `external_roles` and native connection
obligations. Version 1.0 remains unchanged: its string-valued connection requests
are unsupported and it makes no connected-context claim. No existing scope is
silently upgraded. See the [native connected example](../examples/configuration-review/connected/scope.json),
parsed together with its `library.sysml` and `current.sysml`.

An external role is `ID: {native_name,type}`. IDs are distinct from selected role
and connection IDs. Each names one explicitly declared package-level peer in the
same package as the current root, with its exact direct type and positive
supported multiplicity. This expresses an external dependency, not room/system
ownership. Bindings, usage specializations and unresolved variability remain
unsupported. A similarly typed peer in another package cannot satisfy the scope.

Each connection has exactly:

```json
{"id":"DataLink","native_name":"LinkContext::dataLink","owner":"LinkContext",
 "from":{"role":"Sensor","port":"LinkLibrary::Sensor::output"},
 "to":{"role":"Enterprise","port":"LinkLibrary::Receiver::input"}}
```

Endpoint roles are `$root`, retained selected-role IDs, or explicit external-peer
IDs. `port` is the exact native port declaration identity. The checker proves its
membership in the selected type/usage context, checks historical port overrides,
and compares the complete linked endpoint feature chain: actual current-root
usage, every selected child declaration, then the port. Matching terminal port
names or device types is insufficient. A same-typed historical root cannot
satisfy a current-root connection. Endpoint order is interchangeable for these
ordinary connections: the result proves undirected adjacency, not data-flow
direction, payload compatibility, delivery, protocols or executable behavior.
Specialized, bound or variable port declarations remain unsupported, including
an explicitly retained port redefinition; selecting the historical port instead
fails when the selected context overrides it. No effective port-specialization
interpreter is implied by ordinary endpoint support.
Every endpoint also needs one direct port-definition type with available,
non-variable ancestry. A variation port type, including one inherited through
an ordinary derived port definition or its linked conjugated definition, cannot
supply endpoint proof. Conjugated definitions are traced through the native
original-definition reference; an unavailable reference is unsupported.

Named connections match exact native identity and explicit owner. For an ordinary
anonymous `connect`, use `native_name: null`; its identity is the owner plus the
unordered exact linked endpoint pair. Exactly one native match is required;
ambiguous duplicates fail. Source lines are retained only as diagnostics, never
used as anonymous connection identity. One native connector cannot satisfy two
retained connection IDs.

Supported owners are the explicit current package or reconciled usage identities.
Usage-owned relative paths are anchored to that selected usage; explicit
package-level peers keep their actual anchor. Connections declared inside type
definitions, inherited connector semantics, bindings, flows, typed/specialized
connectors and unsupported endpoint expressions return unsupported when selected.
They are not silently converted to ordinary adjacency. No native source regex or
textual name matching supplies the linked endpoint proof.

A missing or retargeted ordinary connection fails; unsupported native constructs
prevent success. Failed required roles/edges are omitted from the reconciled
current graph with explicit findings. Every `1.1` reconciliation result has
`system_view` containing nodes, undirected edges with exact endpoint paths,
open alternatives and omissions. Nodes distinguish the root, owned selected
roles and external references. Unselected native connectors in the explicit
context and selected types are disclosed as omissions. The graph covers the
retained configuration obligations, rather than claiming whole-model completeness.
An empty connection list has `connectivity_claim: empty_scope_no_connectivity_claim`;
it does not establish that a connected system is adequately specified.

The report's model-file/aggregate fingerprints, scope fingerprint, checker digest
and input-stability checks bind this derived graph to the same native revision.
`render_text` and JSON expose the same reconciled adjacency facts. The optional
system-view commands derive their presentation from that graph and compare it
against a fresh reconciliation rather than trusting an editable drawing as the
engineering authority. Physical installation, signal compatibility, runtime
behavior and engineering acceptance remain separate evidence.
