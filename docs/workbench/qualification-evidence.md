# Physical composition development evidence

The [parity matrix](parity.json) records physical composition as active.
The tests below cover the frozen R37 checkpoint. Operation-level working
receipts are retained separately in the private qualification workspace.

| Check | Observed result and limits |
|---|---|
| Native build and smoke | The Linux amd64 image built with the declared non-root user. The smoke in the emulated guest reached the native parser timeout. The same unpacked image passed the offline smoke on a native CPU with networking isolated and the fixture read-only. Exact SysML and two SVG digests matched. |
| Full local regression | On the frozen R37 source, `python3 scripts/check.py --require-sysml` exited successfully. It reported 1,492 cases across 96 suites, including four skips across two suites. |
| Packaged cross-interface rehearsal | The packaged Worker and browser, Chromium, and the official MCP Apps reference bridge ran with a synthetic OAuth issuer and local Worker and R2 fixtures. One synthetic project advanced from import to a site-tool rename and then a manual frame drag. The drag preserved the renamed SysML. Both retained review scopes kept their bytes and outcomes, the native identity remained stable, and the final revision and SVG were read back. The journey passed at standard width and 520 px. |
| Private preview | The approved R37 release was deployed. DNS and TLS were verified and unauthenticated probes returned a generic unavailable response while project access was closed. The real compute restart and actual Codex desktop and ChatGPT journey await live tenant authorization. |

The baseline covered the pinned Python and Java SysML runtime. The local
host tests and [Astra walkthrough review](astra-review.md) provide scoped
software and visual evidence. Physical composition remains open until the
actual application and operation-level acceptance obligations pass.
