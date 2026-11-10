# Selected-profile document export

Use this helper for a **static local HTML document**, optional standalone SVGs,
selected local font files and native graphics. It does not implement a general
document editor, select the project's identity, or establish engineering acceptance.
Resolve the intended authority with [visual profiles](visual-profiles.md) first.

## Existing-tool preflight

Run from any project directory, using the installed runtime's absolute path:

```sh
node <runtime>/scripts/render_technical_document.cjs preflight \
  --root <project> --profile visual-profile.json --python <python>
```

`<python>` needs an **existing PyMuPDF** installation for PDF inspection. The
helper itself uses Python's standard library to read embedded TrueType/OpenType
name and OS/2 weight tables. It does not infer internal names from font filenames.
Node needs an existing Playwright installation. `CSE_NODE_MODULES` can identify
its parent `node_modules` directory; otherwise normal Node resolution is used.
`CSE_CHROMIUM` can name an existing compatible Chromium executable. Inherit any
required environment library paths from the selected toolchain. The helper
installs nothing, does not change execution permissions and does not add browser
flags that disable a sandbox. A missing dependency returns `unsupported`.

Preflight checks availability and selected resources, not browser launch permission.
A launch failure is an `error` with a retained receipt. Use an environment already
authorized for rendering, or report the unrun rendering/PDF checks.

## Prepare editable inputs

Create HTML with the chosen page geometry and semantic content. Select font
families, weights and sizes through the profile's `typography` selectors; profile
CSS is appended after source styles. Palette entries become `--cse-<token>` CSS
variables. Optional figure/table treatments apply only to their selected selectors.
Separate mathematical/formal glyph roles can select their own font files.

Place selected graphics explicitly:

```html
<div data-cse-asset="comp-process"></div>
<img data-cse-asset="cover-art" alt="Project-supplied illustration">
```

An empty SVG `<g data-cse-asset="comp-process"/>` also works when composing a
standalone vector figure. The selected SVG master is inserted as a nested SVG,
with occurrence IDs namespaced and ID references adjusted. Native geometry is
retained; the helper does not redraw formal model content. Raster assets are
embedded as exact-byte data URIs and keep separate image roles. Configure their
placement and dimensions in the source. Put meaningful descriptions/alt text in
the source and preserve applicable license/source attribution.

This bounded helper rejects script/iframe/object/embed content, untracked HTML
images, SVG foreign objects, canvas content, remote requests and SVG CSS ID
selectors requiring adaptation. It does not recursively package arbitrary local
stylesheets or image URLs; keep static source styles inline and use selected
asset placeholders. A formal-symbol master containing a raster image is rejected.
Selected SVG masters need native geometric primitives. More complex sources can
use another qualified renderer and retain equivalent evidence.

## Render and inspect

```sh
node <runtime>/scripts/render_technical_document.cjs render \
  --root <project> --profile visual-profile.json --html proposal.html \
  --svg flow.svg --output-dir output/review-01 --python <python>
```

The output directory must be new. Input files and the plugin remain unchanged.
Browser temporary data is created under the output directory with short relative
paths; it is removed after the run. Repeated `--svg` arguments produce numbered
editable SVG exports. HTML, font data and selected artwork remain editable.

The helper records actual glyph suppliers through Chromium's
`CSS.getPlatformFontsForNode`, source hashes, selected asset occurrences, geometry
preservation, visibility/bounds, image loading, browser failures and blocked
requests. The PDF check independently reads embedded font names/weights, page
text/bounds, image objects and vector drawings. A raster illustration is permitted;
formal vector content and editorial imagery have distinct checks.

`render-receipt.json` uses `cse.document-render/1`; `pdf-receipt.json` uses
`cse.document-pdf/1`. An incomplete, unavailable or failed required check cannot
produce `pass`. The selected-profile snapshot and output digests accompany the
receipts. Existing receipts are not overwritten.

Inspect final PNG/PDF pixels at reading size for label overlaps, contrast, notation,
line endings and composition. Geometry/font checks do not establish the intended
identity was chosen, client approval, source truth or native-editor round trips.
Use [artifact freshness](artifact-freshness.md) when later edits can stale exports.

The real-browser regression is opt-in with `CSE_RUN_DOCUMENT_BROWSER=1` using the
same existing toolchain and Python interpreter; the normal source suite exercises
deterministic identity/error behavior without installing optional render tools.
