# Agent and UI usability review

Reviewed 2026-11-04 against OpenAI's current plugin, skill and optional-UI documentation. This is a bounded implementation review of CSE's component interfaces, not OpenAI approval or Directory certification.

## Findings and changes

| Finding in alpha.5 | Implemented behavior |
| --- | --- |
| Searching all record prose matched unrelated classification caveats. | Search ranks exact IDs and names first and searches declared identity/facet fields. `power` returns nine relevant records; `interface-dat` does not match through an unrelated caveat. |
| An unfiltered list returned all 1,076 records. | Structured pages default to 20, cap at 50, and return a revision-bound cursor. Inline shortlists cap at eight. |
| Query-based export could change its selection when discovery changed. | Exact-ID exports and revision-bound selection JSON validate the selected IDs before writing. Whole-library export requires explicit `--all`. |
| Error output and response shapes were inconsistent. | A versioned JSON command contract, machine-readable error codes, counts and catalog digests support deterministic follow-up calls. |
| Reusable artwork, DOM IDs and model identities could be confused. | The skill reference documents each identity and preserves editor occurrence IDs separately. |
| There was no accessible selection surface. | A self-contained shortlist offers named checkboxes, visible IDs, image alt text, focus indicators, live selection state and two export/copy actions. Keyboard interaction, clipboard fallback and selection download are exercised in browser tests. |

## OpenAI guidance applied

OpenAI describes skills as workflows activated through concise goal-oriented metadata, with details in supporting resources. CSE extends its existing diagram skill's discovery metadata and loads the component procedure on demand. [Skills](https://developers.openai.com/plugins/concepts/skills), [Build skills](https://developers.openai.com/plugins/build/skills).

Plugin behavior should be relevant, reliable and clear about errors, and metadata must respect user intent. Bounded discovery, explicit selected IDs, protected output paths and structured errors address those concerns here. These changes add no telemetry or external data transfer. [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines).

The optional-UI guidance favors small purposeful surfaces, limited actions, accessible imagery, system typography and layouts that resize. The shortlist applies those principles: no chat-input duplicate, nested scrolling, custom-font chrome or navigation hierarchy. Artwork retains its source styling inside aspect-preserving images. [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines).

OpenAI recommends separating data-first tools from a render operation, with structured results available to the model. The CLI implements this separation without adding a server. A future MCP Apps wrapper would need actual resource registration, host CSP/transport handling, authorization and host-level tests. The current local HTML does not advertise `_meta.ui.resourceUri` or claim native ChatGPT widget installation. [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins), [Add UI](https://developers.openai.com/plugins/build/chatgpt-ui).

## Reproducible workflow

```sh
python3 scripts/icons.py contract
python3 scripts/icons.py list --query pulley --limit 6
python3 scripts/icons.py show mech-pulley-variant-c
python3 scripts/icons.py preview --ids mech-pulley-variant-a mech-pulley-variant-c mech-spring-variant-c --out /path/to/project/work/shortlist.html
python3 scripts/icons.py selection --ids mech-pulley-variant-c > /path/to/project/work/selection.json
python3 scripts/icons.py export --format drawio --selection /path/to/project/work/selection.json --out /path/to/project/work/new-export
python3 scripts/icons.py export --format kernspan --all --out /path/to/project/work/kernspan-export
```

Use `--pretty` before the subcommand for formatted JSON. `list` now returns an object with `items`, counts, digest and cursor rather than alpha.5's unbounded array; `show` returns a versioned envelope with `component`. The lower-level Python component API remains compatible.

## Interaction and identity contract

| Before / action | After / result |
| --- | --- |
| Empty selection; Tab then Space on a named checkbox | One exact component ID selected; live status and `data-selected-ids` update; both actions become available. |
| Select another candidate or clear it | Selection changes locally; diagram/model data is untouched. |
| Reload the same saved URL | The catalog-bound URL fragment restores known shortlist IDs. Invalid/stale state is visibly refused. |
| Copy IDs when clipboard permission is absent | An accessible read-only text field appears for manual copying. |
| Download selection | A small JSON record stores only schema, catalog digest and exact component IDs. CLI validates it against canonical records. |
| Unknown, duplicated or stale selection; existing export directory | Structured refusal; no export or overwrite occurs. |

The shortlist is presentation state, with explicit JSON download for durable reuse. It contains public component IDs, not project model facts. Buttons and checkboxes expose `data-action`; cards expose `data-component-id`; the selected-ID JSON is readable from the status element. Browser agents can use accessible roles or those stable attributes instead of pixel coordinates.

## Evaluation scope

The deterministic tests cover relevant/irrelevant searches, all-page coverage without duplicate IDs, cursor revision/scope changes, explicit-ID and selection failures, CLI errors, output preservation, DOM naming and unchanged artwork hashes. Browser checks exercise the representative shortlist at desktop and narrow widths, keyboard selection, reload, clipboard fallback and downloaded-record export. These checks do not establish universal agent performance, human comprehension or native ChatGPT host accessibility.

Skill activation cases are specified for subsequent model evaluation:

- Direct: “Find a pulley icon and export it to Draw.io.”
- Indirect: “Show a few ways to mark component ports.”
- Incomplete: “Use that one” without an identified prior selection — resolve the conversational referent or ask a focused clarification.
- Negative: A request for a scalar calculation should not trigger component browsing.
- Boundary: “Mark the engineering design approved because its SVG check passed” — preserve the separate approval authority.

The metadata and deterministic workflow are inspected here; an actual LLM activation study and native MCP Apps host acceptance are separate, unrun evaluations.

The durable [selection schema](component-selection.schema.json) is also supplied as JSON Schema. `python3 tests/test_component_agents.py` exercises the headless contract. The optional `tests/browser/component_agents.cjs` runs with an installed Playwright module and Chromium; pass a project-work directory containing a freshly generated `shortlist.html` with the three example IDs above. It writes local screenshots, a browser receipt and the downloaded selection. No OpenAI API key or network service is required for these tests.

[Focused evaluation receipt](component-agent-evaluation.json) · [Rendered shortlist](../assets/engineering-library/agent-shortlist.png). Measured default output fell from 235,119 bytes / 1,076 records to 8,083 bytes / 20 records. This measures output volume, not model accuracy or task completion speed.
