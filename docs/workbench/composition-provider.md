# Physical-composition application providers

The local editor and the MCP client adapter use one controller, native reader
and typed engineering operations. The provider supplies requests, temporary
intent storage and artifact transfer. It supplies no model or engineering
verdict. Hosted persistence, the complete MCP data-tool contract and actual
Codex/ChatGPT acceptance remain open in the [parity ledger](parity.json).

Before a saved model exists, [initial authoring](composition-initial-project.md)
uses a separate prospective controller and `cse-initial-host-1` provider. It has
no revision-zero engineering projection. Its checked first request and receipt
explicitly hand off to this saved-model controller, using the same SDK client
and stable project/root/view grant. Local reference-protocol checks do not
establish production data tools or actual application acceptance.

## Requests and provider selection

An ordinary local page uses the existing authenticated loopback transport,
cookie/CSRF boundary and tab session storage. A trusted application bundle can
install `globalThis.cseCompositionHost` before loading the controller:

| Field | Contract |
|---|---|
| `version` | `cse-composition-host-1` |
| `kind` | Nonempty transport identifier for context and diagnostics. |
| `request({operation, payload})` | Asynchronously return `{status, body}`; retain native errors and definitive-refusal fields. |
| `intentStorage` | `getItem`, `setItem`, `removeItem`, synchronous or asynchronous. Read returns the exact string or null; failures throw. |
| `openArtifact` | Null when unavailable, otherwise accept `{kind, commit, revision}` and return `{isError: boolean}`. |

Only an absent provider selects loopback. Present null, undefined, incomplete or
unsupported providers refuse initialization before session, storage or polling
side effects. The provider is captured at startup. It is application code,
never a value supplied inside SysML, linked records or model metadata.

The operation names are `state`, `head`, `inspection`, `preview`, `apply` and
`receipt`. The default local provider also handles `session`; the MCP adapter
refuses that local bootstrap operation. Existing schemas, expected revisions,
source identities, configuration findings and receipts keep their meaning.

## Exact intent and acknowledgement

Initialization awaits the pending-intent read before assigning reader HTML or
enabling edits. Recovered request IDs, payloads, raw form values, original target
UUID/occurrence and base revision remain bound together.

Save awaits storage of that exact intent before dispatching apply. A preparation
or storage failure returns `not_sent` for this attempt and retains any earlier
unconfirmed outcome. It does not claim that an earlier or concurrent publication
is absent.

An apply response must match project UUID, request ID, operation, expected next
revision, commit format and the native canonical request digest. The checked
preview supplies that digest; it is retained with the request. Older entries
obtain it through existing read-only exact-request receipt lookup. The browser
does not recreate Python's JSON number encoding. Receipt lookup also checks
project and exact request digest before returning a receipt as committed.

A mismatched or missing acknowledgement retains the original unknown request.
A matching durable receipt remains committed even if temporary-state cleanup or
the following refresh fails. Failed cleanup is disclosed; reload can recover
and retry the same request without adding a revision. These client checks bind
a response to an operation. Server authorization and durable publication remain
separate enforcement obligations.

## Shared context

`globalThis.cseWorkbench.context()` returns a detached snapshot of saved
identities, revision/commit/bundle, selected native/role occurrence, fixed draft
target, form values, exact pending request, last acknowledged receipt, viewport,
history and separately retained complete configuration findings. `ready` is
false while the saved reader is loading or its original fonts are unavailable.
A new revision in a loading snapshot does not qualify its selection for action.

`subscribe(listener)` publishes snapshots after selection, navigation, form,
preview, notice/refusal, save, unknown-outcome and restoration changes. It returns
an unsubscribe function. Listeners receive separate copies; throwing or rejected
listeners cannot mutate findings, clear intent or revoke acknowledgement. The
Codex site adapter uses this same snapshot and its existing exact UI guards.

`web/composition-mcp-host.js` delegates through a supplied MCP Apps client's
`callServerTool`. Inspection input cannot replace its fixed project/view. Each
app instance namespaces intent storage without replacing global fetch/storage
APIs. The wrapper supplies the SDK client and render-resource bootstrap;
server-side authorization remains required for private calls.

The context publisher includes selected occurrence, fixed target,
creation/restoration draft, exact pending-request identity and retained scope
identities/statuses. This is selected UI context, not the complete engineering
review. Delivery is serialized and acknowledged after bridge success; an
unchanged failed delivery retries without another event. Disposal stops
subscriptions and future retries.

## Drawing and artifacts

The shared controller keeps the saved reader hidden while the four original
DejaVu Sans/Mono faces load. Expected families/weights must be present. Failure
or font timeout exposes an unsupported drawing message and inspection tables.
Completion is bound to document, srcdoc, view generation, commit and revision,
so an old font failure cannot hide a newer view. Saved SVG, masters, metrics,
textures and notation remain unchanged.

Local SVG/source-binding links retain commit-bound downloads. A configured host
uses its artifact handler or marks transfer unavailable. The MCP adapter
currently has no transfer handler. Candidate/export font gates, full host
frame/navigation compatibility and actual-host glyph coverage remain open;
saved-reader checks cannot close them.

## Qualification

`tests/test_composition_host.py` checks client project binding, storage isolation,
refusal preservation and delivery lifecycle. The browser driver
`tests/browser/composition_provider.mjs` uses the real native Git project to
check invalid providers, async intent restoration/persistence, storage failure,
acknowledged cleanup failure, exact retry, subscriber isolation, superseded
font failure and wrong-project/wrong-payload receipt rejection.

The assembled local suite also reruns existing role, navigation, multiplicity,
native-name and creation journeys. A separate official SDK reference sandbox
tests the explicit provider with real MCP calls, strict font policy, manual/agent
edits, reload/retry, restoration and raw SVG/native-file equality. These remain
local evidence; they do not establish OAuth, cloud durability or actual-product
acceptance.
