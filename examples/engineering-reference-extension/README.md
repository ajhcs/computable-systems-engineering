# Selected Action and untimed Sequence derivatives

This extends the [four-reference pack](../engineering-reference/README.md) with
TMT APS exposure and message-order readings from the pinned February 2017 native
model and the linked 2017 paper. The [same notices](../engineering-reference/notices/README.md)
apply. No original XML, generic source projections, figures, photographs, opaque
implementations or complete native archives are bundled.

- [Take SH Exposure reading](tmt-exposure.md): [SVG](rendered/05-tmt-exposure.svg),
  [PNG](rendered/05-tmt-exposure.png), [draw.io](rendered/05-tmt-exposure.drawio),
  [v2](derived/tmt-exposure.sysml) and [curated facts](source/action-facts.json).
  The concurrent send/accept branches, six control flows and one object flow are
  retained; no Ack image field, receive port, unit or timeout is invented.
- [Untimed signal-order reading](tmt-sequence-order.md):
  [v2](derived/tmt-sequence-order.sysml), [curated facts](source/sequence-facts.json)
  and [partial actual native pilot PNG](rendered/pilot-tmt-sequence-order.png).
  Three exchanges and local participant order are retained. Original durations
  remain outside executable claims.

The earlier source-style Sequence image/editable/style pairs have an in-image
claim about retained source XML. Those original artifacts stay local; revised
presentation release awaits fresh supported rendering and pixel inspection. The
sequence renderer emits local candidates under ignored work/, never a validated
public picture by itself. This does not hold the untimed textual model or actual
partial native pilot, whose scope and labels are distinct.

`python3 scripts/check_exposure_reference.py` compares curated facts, saved native
inventories and existing selected views. `python3 scripts/check_sequence_reference.py`
checks the untimed derivative contract and saved native endpoint/order/payload
inventory; source-style rendering is explicitly not distributed. Neither command
validates the original archive or XML independently. Optional local reserialized-source-slice
identity checks are documented in the base pack. Curated facts are reviewed
interpretations, not an independent original-source oracle.

Portable parser/native/evaluator reports under validation/ are retained historical
receipts, not newly executed results. Their exact model hashes remain meaningful;
local source-duration receipts and private failure logs remain local. Native
STATE/ACTION/INTERCONNECTION pilots are partial views and their omissions remain
listed in [native-view assessment](validation/native-view-assessment.json).
No native editor round-trip, behavioral execution, full equivalence or engineering
acceptance is claimed. A3/browser/style receipts for the held presentations are
not part of this public release.
