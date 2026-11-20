# Component catalog in physical composition

The engineer can look up presentation assets beside the saved model. Search
uses the installed catalog's existing ranking, exact family and SysML-context
filters, and revision-bound cursor. An exact-ID inspection returns the same
treatment, source IDs, applicability and approval fields as `icons.py show`.
Inspecting an ID from a search also requires that page's catalog digest.

| Action | Native contract | Observable result |
| --- | --- | --- |
| Search for “pulley” | `catalog_search` with query, optional family and SysML context, page limit and cursor | The Pulley exact ID `mech-pulley` comes first. More reads the next page with the original filters. |
| Inspect “Pulley” | `catalog_inspect` with exact ID, catalog digest and optional artwork flag | View the pinned SVG and its source and modeling-context facts. |
| Use a stale cursor or digest | Existing cursor validation or an exact revision mismatch | Repeat discovery and inspect the returned ID against the new catalog. |
| Inspect an unknown ID | Existing exact-ID resolution | Show the refusal. Similar names do not resolve the request. |

The panel follows the existing [keyboard-accessible catalog shortlist](../component-agent-review.md).
The read interaction uses a search form, paged buttons and one details pane.
The saved diagram and its edit target stay visible in their existing places.
Artwork loads as an isolated image using the original SVG bytes. The catalog
digest, artwork ID, source element ID, native model UUID and diagram occurrence
retain their existing meanings.

## Keep an artwork selection

Open an exact entry and add it to the artwork selection. The selection lists
exact IDs and allows removal. Search can continue while the selection is open.
Download the existing `cse.component-selection/1` JSON format, or open a saved
record in an empty selection. A stale catalog, unknown ID, duplicate ID, or
malformed record leaves the current selection intact.

The site tools can read, validate, replace or clear the visible selection.
Replacing or clearing it requires the current project and view guard and
the artwork selection revision. A concurrent edit to the artwork selection
requires a fresh read before retrying.

The catalog digest binds the selection to the packaged artwork. The file holds
only the digest and selected IDs and works with the existing CLI export.
Applying a selected asset to a diagram remains a separate operation with its
own occurrence binding and review.

## Place a saved frame master

Select a physical frame, then inspect a saved rectangle master in the catalog.
Preview frame placement with the frame's view ID, occurrence ID, native UUID,
catalog digest and SVG digest. The frame editor starts with the saved fill,
boundary and text swatches and alignment. You can change these values using the
installed palette, or open the saved frame style directly. The preview tests
contrast and key clearance and presents the candidate SVG
before save. When creating the first appearance companion, supply the wording
for the local key. An explicit replacement key is also allowed.

The appearance and any required footer space are saved with Git history.
The renderer retains the source SVG master, frame bounds, connector geometry
and native properties. An illustration such as the Pulley, a stale master
digest, or a declaration row without a physical frame is refused for this
rectangle placement. Other artwork roles follow their own placement contracts.

The typed `set_frame_master` request accepts an optional `style` object with
`fill`, `stroke`, `text` and `align`. The three colors use exact saved swatch
IDs, and alignment accepts `left` or `center`. Earlier requests keep the saved
style. The renderer applies the chosen swatches to the presentation copy and
validates the resulting text, boundary and texture visibility.

## Style an ownership connector

Choose a saved connector in **Ownership connector appearance**, then edit its
swatch and preview. The control lists the exact route and its endpoint
occurrences. The typed `set_connector_style` request binds the view, connector,
both native endpoint UUIDs and the current palette digest. A first appearance
requires an authored local key. Existing appearance keeps its key when the
request supplies null.

Save records the swatch in the appearance companion. The existing unarrowed
ownership path, its endpoint geometry and the crossing-gap rules remain
authoritative. The over-route swatch also colors its crossing marker. The
renderer refuses a stroke with insufficient contrast.

## Edit the local key

Open **View local key** to inspect the saved entries. Edit one to five lines,
preview the original ruled legend, and save through the same history as the
other appearance edits. The `set_view_key` request binds the view and original
legend master digest. The renderer applies the project's original font and
footer clearance checks. It grows the canvas height when the authored key
requires it and rejects text too wide for the saved canvas. Existing frame and
connector swatches and all route points are preserved.

## Edit a display alias

Select a framed part and edit **Display alias in this view** beside its declared
name. Preview the drawing before saving. Clear the field to show the declared
name. The typed `set_display_alias` request takes the saved view ID, frame ID,
native element UUID and one line of alias text or null. It writes the view's
display-label companion. Other views, SysML, stable identities and retained
configuration scope stay intact.

The drawing uses the existing frame master, typeface and layout. The retained
label contract accepts printable ASCII and the middle dot. The renderer checks
fit in the saved frame. Use the layout operation if an alias needs a larger frame.

The [display-alias browser check](../../tests/browser/composition_display_alias.mjs)
accepts a fresh output directory, using the same parser cache and browser
settings as the [navigation checks](composition-navigation.md#repeat-the-browser-acceptance-checks).
Its receipt binds the rendered SVG to the saved Git transaction and verifies
restoration into a new revision.
