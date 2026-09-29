# Public references and reuse status

These are source links and research leads. No third-party implementation or complete source document is distributed in this repository.

| Source | Intended use | Current status |
|---|---|---|
| [NASA requirements checklist](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/) | Distinguish normative requirements, goals, facts, consistency, and traceability. | Reviewed as method background. Only precisely encoded conditions become automatic checks. |
| [NASA FRET](https://github.com/NASA-SW-VnV/fret) | Study structured requirement semantics and analysis. | [Bounded reuse spike](fret-spike.md); no integration or copied code. |
| [FRET compiler](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/app/parser/FretSemantics.js) | Evaluate reusable parsing/formalization interfaces. | Interface inspected. Standalone extraction has not been built or tested. |
| [FRET CLI documentation](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/cli/cli.md) | Evaluate formalization and realizability workflows on Linux. | Packaging and solver integration remain untested here. Pin a tested upstream revision before reuse. |
| [FHWA CARMA Detailed Concept of Operations](https://www.fhwa.dot.gov/publications/research/operations/20064/index.cfm), FHWA-HRT-20-064 | A small highway-merge reference case with needs, requirements, and traces. | [Proposed formalization slice](fhwa-merge-slice.md), not engineer-accepted. [Published PDF](https://www.fhwa.dot.gov/publications/research/operations/20064/20064.pdf). |
| [NASA EHP Integrated Concept of Operations, Rev D](https://ntrs.nasa.gov/citations/20260000972) | A possible later case with operational interfaces and capabilities. | Catalogue inspected only; the full document has not been evaluated for use. |

The skill methods are an original synthesis informed by systems-engineering study, including Buede and Miller, *The Engineering Design of Systems: Models and Methods*, and the maintainer's requirements for engineer involvement and program feedback. Private annotations, course readers, and book attachments are excluded.

FRET's upstream license and any redistribution notices must be checked at the exact revision selected for reuse. This repository's future license does not replace third-party terms. The project is independent of NASA and FHWA.
