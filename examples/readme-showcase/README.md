# Engineering questions, readable outputs

[Open the full-size gallery](generated/index.html) to explore eight different questions. Each preview comes from existing synthetic models, ledgers, evidence and checker output. These are explanatory presentations, not native SysML graphical views or accepted engineering designs. All sample-station limits, responsibilities, operating policies and traces are fictional demonstration choices.

The PNGs are 800 pixels wide with 22-pixel main labels and supporting text at least 18 pixels. They are intended for desktop reading at their natural width. A dense PNG shrunk to 342 pixels is **not** claimed readable: the gallery keeps it 800 pixels wide inside a scrolling frame, with a plain-language caption, nearby source links and a complete text alternative. Use that reader on narrow screens. Its document is read-only engineering documentation, not a station operational UI.

## Normal handoffs

A container enters the station and is later picked up. Four recorded exchanges identify who sends what to whom, without inventing timing, screen fields or executable activity logic.

```text
Show the four normal sample handoffs, naming who sends what to whom. Use the existing station model and distinguish documentary exchanges from executable behavior.
```

![Four normal handoffs](generated/01-normal-handoffs.png)

[Full-size view and text alternative](generated/index.html#normal-handoffs) · [Editable SVG](generated/01-normal-handoffs.svg) · [Authoritative model: SQ_NOMINAL](../engineering-gallery/water-sampling/station.sysml). The wording is the source's four existing messages; presentation numbering adds no new relation.

## Label recovery

An unreadable label causes a hold. The container stays unreleased while the operator supplies corrected identification; the station then confirms reconciliation and a receipt. Actual reconciliation authority and policy remain unresolved.

```text
Walk through the unreadable-label hold and recovery. Show the four existing exchanges and make the unreleased hold explicit.
```

![Unidentified-container hold and recovery](generated/02-label-recovery.png)

[Full-size view and text alternative](generated/index.html#label-recovery) · [Editable SVG](generated/02-label-recovery.svg) · [Authoritative model: SQ_RECOVERY](../engineering-gallery/water-sampling/station.sysml). These are documentary manual/protocol exchanges, not a station screen design.

## Responsibilities

People, equipment and functions have different roles. Five existing documentary assignments show who identifies, records, reconciles and inspects; the courier participates in pickup but has no function allocation recorded. Seven other assignments are intentionally omitted from this scoped preview.

```text
Show the recorded responsibilities for identifying, recording, reconciling and inspecting samples. Keep participants distinct from functions and expose missing allocations.
```

![Selected documentary responsibilities](generated/03-responsibilities.png)

[Full-size view and text alternative](generated/index.html#responsibilities) · [Editable SVG](generated/03-responsibilities.svg) · [Documentary allocation ledger](../engineering-gallery/water-sampling/semantic-ledger.json) · [Native action and participant bindings](../engineering-gallery/water-sampling/generated/shape-concept.json). IDs: F11, F12, F22, F32, F42. These assignments are not native allocations, implementation ownership or proof of capability. The custodian's candidate `InspectAndRestore` function does not authorize automatic operational release.

## Need traces

Read all six recorded links, preserving their direction and relationship kind. Three requirements justify two stakeholder needs; two use cases address selected requirements. No scenario link to the duration requirement is recorded in this ledger.

```text
Read the existing need, requirement and scenario traces. Preserve link direction and kind, and show any missing scenario link without inventing one.
```

![Typed need, requirement and scenario relationships](generated/04-need-traces.png)

[Full-size view and text alternative](generated/index.html#need-traces) · [Editable SVG](generated/04-need-traces.svg) · [All six typed source traces](../engineering-gallery/water-sampling/semantic-ledger.json). IDs: N_IDENTITY, N_ACCOUNT, R_RECORD, R_ELAPSED, R_CORRELATION, UC_NOMINAL, UC_RECOVERY. A typed relationship is not a satisfaction proof; the diagram adds no missing links.

## Receipt deadlines

Two overlapping containers receive distinct matching receipts. W002 is presented later and answered first. W001 at exactly 2 seconds meets the inclusive deadline; its 2.1-second counterpart fails. Each deadline is relative to that container's own trigger.

```text
Compare the existing passing and late receipt traces. Show overlapping container IDs, the inclusive two-second deadline and the correctly reversed response order.
```

![Passing and late correlated receipt timelines](generated/05-receipt-deadlines.png)

[Full-size view and text alternative](generated/index.html#receipt-deadlines) · [Editable SVG](generated/05-receipt-deadlines.svg) · [Passing events](../engineering-gallery/water-sampling/evidence-pass.json) · [Late events](../engineering-gallery/water-sampling/evidence-late.json) · [Passing result](../engineering-gallery/water-sampling/generated/native-pass.json) · [Late result](../engineering-gallery/water-sampling/generated/native-late.json). ID: R_CORRELATION. These are actual supported monitor results against synthetic traces, not measured implementation latency or a performance distribution.

## Quantity bound

At the same recorded receipt, a four-second observation passes and a five-second observation fails the fictional four-second limit. Both are valid integer values in the 0 to 20 second declared domain. Receipt timing and event correlation still pass in both comparisons.

```text
Compare the recorded-receipt observations of four and five seconds against the fictional four-second limit. Show which check fails and retain the other passing controls.
```

![Four-second pass and five-second failure at recorded receipt](generated/06-quantity-bound.png)

[Full-size view and text alternative](generated/index.html#quantity-bound) · [Editable SVG](generated/06-quantity-bound.svg) · [Passing observations](../engineering-gallery/water-sampling/evidence-pass.json) · [Over-limit observations](../engineering-gallery/water-sampling/evidence-over-limit.json) · [Over-limit result](../engineering-gallery/water-sampling/generated/native-over-limit.json). ID: R_ELAPSED at sample 3, with `receiptRecorded=true`. The quantity is observed, not a clock inferred by the model. R_RECORD's separate two-second response window does not define the quantity's four-second bound.

## Blocked handoff

A deliberately broken copy of the finite scenario requires the label to be both readable and unreadable. The arrow from `recorded` to `done` exists, but its guard can never enable it. The actual verifier reports the disabled step and the missing completion path. The original finite fixture stays unchanged.

```text
Explain the existing blocked-handoff negative control. Show the contradictory guard and the actual finite verifier findings without implying a SysML-to-executable conversion.
```

![Actual findings for a deliberately blocked finite handoff](generated/07-blocked-handoff.png)

[Full-size view and text alternative](generated/index.html#blocked-handoff) · [Editable SVG](generated/07-blocked-handoff.svg) · [Exact reproduced mutated fixture](generated/blocked-handoff-fixture.json) · [Actual reproduced result](generated/blocked-handoff-result.json) · [Original finite model](../engineering-gallery/water-sampling/finite-scenarios.json) · [Existing negative-control construction](../engineering-gallery/water-sampling/build.py). IDs: FS_NOMINAL, FN_RECORD, FN_HANDOFF. The report and semantic digest must equal the pre-existing negative control. This is the separately authored finite engine, not an executable conversion of narrative SysML or a finding about real equipment.

## Tool library

Compare improved paper records with an offline laptop ledger. Both retain volunteer authorization; no final choice or measured speed advantage is recorded. The conditional arithmetic shows why the recalled peak offers no nominal spare capacity, while refusing to invent a waiting-time prediction.

```text
Compare the existing community tool-library paper and laptop concepts. Show the conditional capacity arithmetic and evidence gaps without selecting a winner or predicting wait time.
```

![Two community tool-library proposals and conditional workload arithmetic](generated/08-tool-library.png)

[Full-size view and text alternative](generated/index.html#tool-library) · [Editable SVG](generated/08-tool-library.svg) · [Synthetic request](../tool-library/input.md) · [Legacy concept record](../tool-library/result/concept.json) · [Existing concept brief](../tool-library/result/concept-brief.md) · [Capacity calculation](../tool-library/result/capacity_check.py) · [Arithmetic result](../tool-library/result/capacity-check.txt). IDs: K_PAPER, K_LAPTOP, C_WAIT, D_SELECTION. Ten arrivals times one transaction times three minutes equals 30 volunteer-minutes in 30 minutes, assuming one continuously available volunteer. These are fictional recollections and conditional arithmetic, not measurements, candidate feasibility, expected wait, accepted criterion weights or an accepted choice. Paper is recommended only as the next baseline exploration; final selection remains deferred.

## Meaning and reproduction

[The frozen selection ledger](semantic-ledger.json) records each question, prompt, selected IDs, source bindings, scope and omissions before geometry. [The generated meaning ledger](generated/meaning-ledger.json) binds the actual source facts and hashes. Native syntax/profile, sampled/event monitors, finite scenario review, legacy structural review and the original capacity calculation are actually rerun; their results must match the existing published example reports. A passing trace, declared assessment, structural check and stakeholder acceptance remain separate claims.

The builder uses the existing pinned parser and standard library. It never modifies the original model, evidence, concept or calculation report. The legacy capacity script is executed from an exact temporary copy on `/workspace` because it writes its report beside itself. The full existing sources remain the authority; the new previews change presentation only. No private reference-library figure is imported. See [the engineering gallery method](../../docs/gallery-method.md) for terminology and supported-computation limits.

From the repository root, with its pinned parser installed:

```sh
python3 examples/readme-showcase/build.py --output /workspace/path/to/fresh-showcase
python3 examples/readme-showcase/build.py --check
```

`--check` uses the tracked `generated/` directory. It checks source, generator, checker and font pins; exact output inventory and hashes; SVG-to-PNG receipt bindings; recorded browser bounds/narrow-scroll results; and a fresh deterministic SVG/content/facts/report regeneration. Changed, deleted, added or stale artifacts fail. It needs no browser. It does not silently normalize precision or relax byte comparisons. Python 3.10 and 3.12 are the supported reproduction targets; the renderer uses the already portable existing font-metric support.

PNG rendering is a separate optional operation requiring existing installed tools. It records renderer, browser and output hashes and uses an isolated profile and process-local temporary paths on `/workspace`, leaving `HOME` and `CODEX_HOME` unchanged. On the reviewed BuilderBob host:

```sh
python3 examples/readme-showcase/render.py \
  --output examples/readme-showcase/generated \
  --browser /workspace/cache/builderbob/global-tools/browsers/chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell \
  --playwright-module /workspace/cache/builderbob/npm/_npx/a4d0c66fe73b166b/node_modules/playwright \
  --library-path /workspace/cache/builderbob/global-tools/browser-deps/sysroot/usr/lib/x86_64-linux-gnu
```

Embedded font notices are included in [font-notices](generated/font-notices/manifest.json). Browser rasterization and author inspection are evidence about the supplied pixels, not independent engineering acceptance, native graphical conformance or an editor edit/save/reopen round trip. No source or model is sent to a hosted service. Publication, merge, deployment, real operating acceptance and private-source rights remain outside this artifact task.
