# README artwork

`cse-overview.svg` is original explanatory artwork for CSE's ask/model/check
workflow. Its relationships are illustrative; it is not a SysML model,
product screenshot, or verification result.

`connected-overview.svg` is a simplified presentation derived from the checked
[synthetic connected fixture](../../examples/configuration-review/connected/README.md)
and its [native view ledger](../../examples/configuration-review/connected/generated/view.json).
It draws the selected current root, its sensor role, the explicit receiver peer,
and the retained `DataLink` ordinary undirected native adjacency. Selected
parentage is shown by containment. Labels are shortened and multiplicity is
omitted; exact identities, paths, diagnostics and omissions remain in the
native reader and ledger. The card and circular endpoint styling is explanatory
presentation, not a claim of formal SysML graphical interchange or behavior.

The SVGs retain editable text and geometry. They embed the repository's existing
Inter and Space Grotesk fonts with their original OFL notices; source files and
notices remain under [diagram-style/fonts](../diagram-style/fonts/). No fonts or
other third-party assets were added. Original project artwork is MIT licensed.

From the repository root, regenerate the SVGs or compare their exact sources:

```bash
python3 assets/readme/build.py
python3 assets/readme/build.py --check
```

The corresponding PNGs are actual browser rasterizations. To regenerate them
with an existing installed Chromium, pass its executable explicitly:

```bash
python3 assets/readme/render.py --browser /path/to/chromium
```

An optional `--library-path` selects an existing shared-library directory. The
script uses isolated temporary profiles under the repository's ignored `.tmp`
directory; it installs no browser or dependencies and leaves HOME unchanged.
`render-receipt.json` binds the exact sources, PNGs, renderer, illustration
generator and native view ledger. A changed native fixture needs a fresh native
view before these sources are rebuilt. Rasterization/source comparison and
visual inspection support their stated scopes; they do not authenticate source
truth, engineering acceptance, or audience preference.
