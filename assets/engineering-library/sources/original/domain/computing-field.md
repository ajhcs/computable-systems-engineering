# Computing and field-equipment icon study

This independently authored, editable set contains 38 computing and 27 aerospace/field pictograms or schematic examples. Each uses the accepted 35 mm reference frame; physical subjects use front, side, or plan views and the accepted hierarchy of contour, feature, and supporting strokes. Icons have local meanings and limits in `index.json`. The labels are necessary context for abstract ideas and for processor or network-device roles that cannot be reliably inferred from appearance.

`field-*` artwork depicts generic equipment or operational relationships. It is **not** a military operational-symbol library and does not specify affiliation, echelon, a unit, weapon, or status. The [US Defense Logistics Agency's MIL-STD-2525 record](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=114934) describes a separate joint-military symbology standard; no conformance is claimed here.

Sources used for semantic scope, not as copied graphics:

- `nist-cloud`: [NIST SP 800-145](https://csrc.nist.gov/pubs/sp/800/145/final), cloud-computing characteristics and service/deployment concepts.
- `nist-authn`: [NIST authentication glossary](https://csrc.nist.gov/glossary/term/authentication), identity verification.
- `nist-authz`: [NIST authorization glossary](https://csrc.nist.gov/glossary/term/authorization), permission and access decision.
- `nist-encryption`: [NIST encryption glossary](https://csrc.nist.gov/glossary/term/encryption), transformation into ciphertext.
- `nist-digital-twin`: [NIST IR 8356](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957183), bounded discussion of digital representations and synchronization.
- `nasa-spacecraft`: [NASA spacecraft subsystem description](https://science.nasa.gov/asset/webb/webb-telescope-spacecraft-diagram/), equipment context; the simplified icons do not depict that spacecraft.
- `faa-rotorcraft`: [FAA Rotorcraft Flying Handbook](https://rotorcraft.arc.nasa.gov/faa-h-8083-21.pdf), helicopter component context; the figure is not a specific aircraft.
- `nasa-aircraft`: [NASA's beginner aeronautics material](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/), fixed-wing component context.
- `dla-symbology`: the separate military-standard record above, used to maintain the boundary rather than to copy symbols.

`generate.py` produces the individual icons; `preview.py` renders review sheets; run `python3 check.py`. The programmatic checks establish inventory, source metadata, unique rendered geometry, and bounds, not universal comprehension, component fit, cybersecurity, or real model behavior. Examples are synthetic and do not represent an actual aircraft, network deployment, or operational military system.
