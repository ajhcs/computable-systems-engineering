# Electrical and scientific icon review set

This is a local, editable candidate set: **44 electrical** and **22 scientific/mathematical** standalone SVGs. [index.json](index.json) is the searchable inventory, including each symbol's intended meaning, limitations, treatment, file and source keys. Each SVG is independently editable vector geometry with native text, an accessible title and description, and no external images. The standalone art has no caption or card. The labeled 300 dpi proofs are [sheet 1](proofs/contact-01.png), [sheet 2](proofs/contact-02.png) and [sheet 3](proofs/contact-03.png).

The physical illustrations are examples of forms, not dimensioned or identified products. Schematic candidates are simplified locally authored marks, not transcriptions of standard artwork or certified symbols. Terminal rings at their outer edges make connectivity visible for this review; a conventional inversion bubble remains at the output of NOT and NAND. A control rung shows an open switch and coil only; it does not supply the source or return. Earth, motor and generator types remain bounded by their record descriptions. A protective-earth mark does not establish protective bonding. Explicit variants include an NPN transistor, unpolarized capacitor, rectifier diode, two-cell battery, two-winding transformer, generic two-contact connector, AC-to-DC power supply block and DC-to-AC inverter block. These choices do not specify a real circuit or device.

Equations and graph shapes are illustrations, not measured values, calibration results or simulation outputs. The standard-error expression describes sampling uncertainty under the independent, identically distributed observations stated in its record; it excludes other sources and does not specify a confidence interval. The quantity, unit, reference and assumptions for an actual use remain the engineer's responsibility. Native SVG text is editable and depends on available fonts; DejaVu Sans was used for the proof.

## Provenance and conventions

The accepted local [line specification](../../palette/sections/orthographic-illustrations/line-spec.json) uses a 35 mm square, a 160-unit viewBox, contour/feature/annotation weights of 2.4/1.4/0.8 units, and appropriate center or hidden-line patterns. Schematic strokes use a uniform heavy mark where helpful; their external terminal rings are review aids. A dashed line in the relay denotes mechanical association; dashed portions of the DC sign are part of that sign. All artwork is locally drawn and no manufacturer figure or standards graphic was copied.

Source keys in `index.json` resolve as follows:

| Key | Primary source and bounded use |
| --- | --- |
| `local-palette` | The accepted local line specification above; its drawing guidance cites [NASA Engineering Drawing Standards Manual, X-673-64-1F Rev. 001, §3.2.2–3.2.3](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/NASA%20GSFC-X-673-64-1F.pdf). |
| `iec-scope` | [IEC 60617 graphical symbols database](https://webstore.iec.ch/en/publication/2723), for the scope of electrotechnical schematic symbolism. The full controlled database was not evaluated for these marks. |
| `ti-logic` | [Texas Instruments Logic Pocket Data Book](https://www.ti.com/lit/ug/scyd013b/scyd013b.pdf) and [SN74HC00 NAND gate data sheet](https://www.ti.com/lit/ds/symlink/sn74hc00.pdf), for familiar logic-gate examples. These icons are locally constructed, not product representations. |
| `nist-math` | [NIST Guide to the SI, chapter 10](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-10-more-printing-and-using-symbols-and-numbers) and [NIST DLMF notation index](https://dlmf.nist.gov/not/), for mathematical and quantity notation. |
| `bipm-si` | [BIPM SI Brochure](https://www.bipm.org/en/publications/si-brochure/) and [SI base units](https://www.bipm.org/en/measurement-units/si-base-units), for SI quantity and unit context. |
| `nist-statistics` | [NIST/SEMATECH Engineering Statistics Handbook](https://www.nist.gov/programs-projects/nistsematech-engineering-statistics-handbook), for probability and statistical context. |
| `nist-uncertainty` | [NIST Statistical Concepts in Metrology](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nbsspecialpublication747.pdf), for the sample mean and estimated standard error. |
| `nist-calibration` | [NIST handbook on linear calibration](https://itl.nist.gov/div898/handbook/mpc/section3/mpc3672.htm), for calibration-graph context, not the graphic's synthetic positions. |
| `nist-signal` | [NIST, Properties of Signal Sources and Measurement Methods, section 10](https://tf.nist.gov/phase/Properties/ten.htm), for continuous and discrete signal context. |

These sources provide scope and notation context; citing them is not an assertion of symbol-by-symbol IEC, IEEE, ANSI or SI graphic conformity. Use the relevant controlled standard and the actual device documentation before preparing a formal schematic or interpreting a real installation.

## Rebuild and verification

```sh
python3 generate.py
python3 render_proofs.py
python3 check_rendered_joins.py
python3 check.py
```

`render_proofs.py` uses Pillow and `rsvg-convert` from the retained engineering-tools environment; override the paths with `RSVG_CONVERT` and `PROOF_FONT` if necessary. It rasterizes every SVG to 414 × 414 px (within one pixel of 35 mm at 300 dpi), checks the rendered ink has at least a 3-pixel edge margin, and writes SHA-256-bound pixel bounds and contact sheets. `check.py` checks required coverage, unique names and IDs, indexed files and sources, XML/frame/accessibility/monochrome constraints, stroke weights, each schematic's expected terminal count and a lead touching each terminal, as well as proof freshness and bounds. `check_rendered_joins.py` examines actual 300 dpi black pixels for 102 port-to-mark joins across the 44 electrical artworks, 10 intentionally separated component gaps and a clear patch within the breaker contact gap. Five pictograms or physical faces have no visible external lead to test. These tests do not prove electrical conduction, all interior connectivity, standards conformity, visual recognition, editor interoperability or correctness in an actual circuit.

Self-review inspected all three rendered sheets. Initial raster review exposed a missing protective-earth stem, unjoined socket and circuit-breaker leads, and notation overlap; the current source and proofs include corrections. Physical print, recognition testing, and editor edit/save/reopen were not performed. The review set does not create an engineering decision, accepted model fact, compliance finding, or device rating.
