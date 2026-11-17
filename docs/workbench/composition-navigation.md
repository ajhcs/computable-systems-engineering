# Physical composition navigation

This increment completes the active capability's explicit overview/reading-size
obligation from the preserved revision G guidance. It uses the same saved SVG
and native bindings as the inspector and connected editor. There is no second
graph, thumbnail model, engineering parser or artwork collection.

The low-fidelity route is:

```text
Readable size (100%) → Overview (complete saved SVG)
                              ↓ select an exact occurrence
                      Readable size + native properties
```

The existing engineer feedback requires the original SVG/iconography kit.
This route applies that feedback to viewport controls; it introduces no ownership,
configuration or source-editing decision. Controls remain plain text buttons.
Full drawing identification, detail-sheet exports and remaining modeling
operations keep their separate open obligations.

## State and command mappings

| State/action | Visible result | Authority and side effect | Required evidence |
|---|---|---|---|
| PC-VIEW-READABLE | Saved SVG at 100%, with scrollable diagram pane | Exact saved geometry, labels, fonts and source UUIDs; ephemeral browser viewport | Real glyph suppliers, native dimensions and keyboard reveal |
| PC-VIEW-OVERVIEW | Complete saved SVG fits the available pane; fit percentage stays visible | Uniform CSS scale of that same SVG; no source/layout/Git transaction | Every frame and relationship remains present and within the viewport |
| Select from overview | Native selection opens at readable size | Exact occurrence/engineering UUID; required-review scope and edit target retained | Pointer and keyboard selection; definitions/usages; draft/pending cases |
| Previous/Next | Selected occurrence revealed at readable size, navigation focus retained | Existing native selection; independent inspection and editing identities | Navigate all occurrences without test-side diagram scrolling |
| Refresh while in overview | New saved view stays in overview | Refit the new saved SVG; retain exact pending request and form values | Actual CLI/GUI state and context agree; no camera command becomes an engineering edit |
| Active move/resize | View mode and native selection cannot change during that gesture | Existing fixed gesture target and SVG coordinate transform remain stable | Navigation/selection controls disabled; competing tool and keyboard selection refuse |

The reader's `cseDiagramNavigation` provides mode, reveal, restore, lock and
state methods. The controller and site tools call these same methods. Native
SVG attributes, viewBox, component/source bindings and exported `view.svg`
remain unchanged. Screen scale affects browser inspection, not the stored
layout or exported drawing. The initial screen mode is readable size.

Viewport state is explicitly transient: mode, scale, scroll offsets and client
dimensions in CSS pixels, plus a navigation revision. It is not a SysML element,
layout companion or Git revision. Refresh retains it within the open editor;
reopening starts at reading size. Source, identity, layout and history still have
their independent durable persistence obligations.

The site adapter exposes `cse_set_view_mode` and the same occurrence reveal
through `cse_select_element`. Its context includes current navigation state.
Guards include navigation revision, mode and scroll offsets, so an older command
cannot silently undo intervening manual navigation. Navigation retains human
drafts and checked/unknown requests. It cannot discard or save them. MCP and
actual Codex/ChatGPT host coverage remain open, as in the central parity matrix.

## Inspected precedent

Observed 2026-11-17: draw.io's official
[zoom documentation](https://www.drawio.com/docs/manual/editor/zoom/), including
its actual toolbar screenshot, shows a percentage menu with reset/100% and fit
actions. The page was inspected in Chromium, including loaded image dimensions;
the initial direct-image request returned HTTP 403 and was not treated as
screen evidence. The normal documentation page returned HTTP 200 and displayed
the screenshot. Research captures remain private.

The documented separation of screen zoom from exported drawing supports a
viewport-only CSE control. CSE's explicit overview/readable-size pair and
selection-to-reveal route are implementation proposals under the existing
readability requirement. This precedent establishes neither CSE usability nor
engineering acceptance.

Assembled checks must include desktop/mobile definitions/usages, resize/refit,
complete overview coverage, natural-size labels, native owner and retained-scope
identity, stale navigation guards, active gestures, preserved drafts/requests,
unchanged sources/layout/history/export SVG and the standalone saved reader.
Actual application tests and full-capability closure remain separate gates.

## Repeat the browser acceptance checks

The repository-owned runner is
[`tests/browser/composition_navigation.mjs`](../../tests/browser/composition_navigation.mjs),
with a synthetic native/Git fixture. It uses an existing configured Playwright
and Chromium installation; it adds no production runtime dependency and installs
nothing. Run from the checkout with the qualified native parser/cache and an
explicit workspace temporary directory. Select a fresh output directory:

```sh
mkdir -p .tmp
TMPDIR="$PWD/.tmp" CSE_SYSML_CACHE="$PWD/.cache/sysml" node tests/browser/composition_navigation.mjs work/navigation-check
```

When the configured browser is outside Node's normal module/browser locations,
set `CSE_BROWSER_MODULE` and `CSE_BROWSER_EXECUTABLE` to those existing paths;
retain any qualified browser-library environment. Missing dependencies or native
support fail the run. They do not produce a passing receipt. The Python
regression suite and this real-browser acceptance run are separate evidence.

The runner creates fresh synthetic projects, checks all four desktop/mobile
definition/usage cases and the standalone reader, and records source/driver/
fixture hashes, real font suppliers and screenshots. Fitting frames must be
fully contained in the padded viewport. Genuinely oversized frames must be
centered and remain inspectable through the available scroll range; extra-small
standalone viewports exercise both oversized axes. The host API is a declared
test double, so its callbacks do not establish actual Codex/ChatGPT execution.
