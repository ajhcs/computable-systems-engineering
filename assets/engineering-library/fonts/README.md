# Engineering palette fonts

These four unmodified DejaVu TrueType files were copied from the installed
Debian `fonts-dejavu-core` / `fonts-dejavu-mono` packages, version `2.37-8`.
The exact common distribution copyright and license notice is retained in
`DejaVu-COPYRIGHT.txt`. The manifest pins each font, notice and metrics file.

`metrics.json` contains the real `hmtx` advance for printable ASCII and middle
dot, selected through each font's Unicode `cmap`, with units from `head` and
metric counts from `hhea`. All four faces use 2048 font units. Widths are advance
sums with kerning and ligatures disabled; they are not ink bounding boxes.

`verifier/kit_fonts.py` validates the pinned manifest and assets and provides
embedded CSS, width and wrapping helpers. SVG callers must keep the shared
renderer settings `font-kerning:none`, `font-variant-ligatures:none`,
`text-rendering:geometricPrecision` and `white-space:pre`. In particular, default
browser hinting can round monospace advances to whole pixels when geometric
precision is omitted.

The qualified faces are DejaVu Sans regular/bold and DejaVu Sans Mono
regular/bold. The font binaries support additional characters, but this runtime
qualifies only printable ASCII plus middle dot. A calculated advance is not a
clipping or readability verdict; inspect actual loaded-font glyph bounds.
