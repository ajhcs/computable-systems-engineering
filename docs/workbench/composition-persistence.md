# Local composition transaction reference

This supporting work belongs to physical composition inspect, rename, finite
multiplicity and saved presentation operations. It addresses their save/restart, concurrent edit,
lost-response retry and history obligations. It is not an independent platform
milestone or closure of either operation's persistence cell.

`verifier/composition_project.py` stores exact multi-file composition bundles,
supported linked records and the stable element registry in a private bare Git
repository. `scripts/composition_project.py` exposes import, inspect, apply and
history against an explicitly selected local project directory. Model filenames
remain labels for supplied text; they never select server-side files to read.

From the checkout, with the isolated parser cache selected, import the
[explicit bundle](composition-bundle.md), inspect its element UUIDs, then apply
one of the typed request files below:

```sh
python3 scripts/composition_project.py import --project work/private-composition.git --bundle work/composition-bundle.json --project-id 42d0daa7-6464-40cc-b5c8-10f2717f3495 --request-id 0d538096-1d82-4419-822a-c167f46166b6
python3 scripts/composition_project.py inspect --project work/private-composition.git
python3 scripts/composition_project.py apply --project work/private-composition.git --request work/composition-request.json
python3 scripts/composition_project.py history --project work/private-composition.git
```

## Commit and retry

A successful operation writes the exact UTF-8 blobs, a manifest with SHA-256
bindings, the registry and its request receipt into a Git tree, then creates a
real parent-linked Git commit. It advances `refs/heads/main` with Git's atomic
compare-and-swap against the previous commit. Git runs with `core.fsync=all` and
`core.fsyncMethod=fsync`; the new project directory's parent is also synced.
The receipt is returned only after publication. Local process restart and
fresh-directory Git bundle restoration are tested separately from these sync
settings; power-loss survival and remote durability are not established here.

Each request has a canonical UUID and a digest of its exact typed JSON values.
Retrying the same request returns its original committed receipt even when later
revisions exist. Reusing the UUID with different values fails. A lost response
after publication therefore cannot duplicate a rename. A failure before rename
publication leaves the old head readable; unreachable objects are not successful
project state. The store does not delete those objects automatically.

A mutation must supply the expected monotonic project revision. Concurrent
different operations have one successful publication and one explicit conflict;
concurrent copies of one request converge on the same receipt. The source digest
and Git commit identity remain distinct from this monotonic revision.

## Supported operation requests

```json
{
  "operation": "rename",
  "request_id": "e9327d11-6521-4a2d-8c72-c6dc3d8440b2",
  "expected_revision": 1,
  "element_id": "a5ec26bf-4b3b-4ab6-ad4d-fb4d0f120822",
  "new_name": "detector"
}
```

The element UUID comes from inspect. Rename uses the same
[candidate boundary](composition-bundle.md), independent reparse and typed
binding adapters. Unsupported edits never advance the head. Retained
configuration bytes stay unchanged; reopen recomputes their findings against
the saved sources. Successful storage does not imply a successful required
engineering review.

```json
{
  "operation": "restore",
  "request_id": "e2cd0af5-592a-4f18-bfab-c9bc50eb7229",
  "expected_revision": 2,
  "target_revision": 1
}
```

Restore copies one published snapshot into a new monotonic revision and commit.
It preserves that snapshot's source bytes, supported companions and registry;
it never rewinds the branch. It provides the primitive for global undo/redo,
not selective per-user undo. Intervening changes require a fresh explicit
operation against the current head. Restoring earlier source bytes cannot make
an old request's expected revision current again.

## Current limits and open acceptance

- Trusted local filesystem and Unix authority only; no hosted account/project
  authorization, Cloudflare coordinator or R2 publication. The
  [loopback interaction adapter](composition-interaction.md) shares these operations.
- Inspect, native rename, finite multiplicity, saved layout and snapshot restoration;
  create/delete/reparent, other property and presentation changes still need their operations.
- Existing bundle limits apply, plus 2 MB of snapshot metadata and 10,000
  revisions. History currently scans the bounded chain. Scaling and migration
  remain open; these limits do not reduce the target capability.
- Normal import retry after successful publication is tested. Interrupted initial
  repository creation before its first published head still needs a recovery
  protocol; an incomplete directory is refused rather than silently replaced.
- The project is a storage container for the admitted records. Unknown companion
  roles still require adapters; source hashes do not authenticate engineer assent.
- Complete appearance/view-session behavior, revision-bound analysis jobs and
  both actual application journeys remain open. The SVG/iconography kit remains
  governed by the [saved design-kit workflow](../../skills/generate-engineering-diagrams/references/design-kit.md).

Run the native parser with an isolated project cache. Relevant test coverage is
in `tests/test_composition_project.py`: process restart, raw Git source bytes,
atomic linked updates, retained-scope findings, pre-publication failure,
lost response, different/identical request races, stale edits, monotonic restore,
portable Git history and corrupt-source rejection. This reference must still be
assembled with the diagram, adapters and remote persistence before any row closes.

The [physical diagram contract](composition-diagrams.md) adds `set_layout` to
this same transaction path. It also defines saved-artifact render/check commands
and the remaining connected-interaction gates.

`CompositionProject.preview()` now prepares the same candidate as publication
without writing project objects or reserving a revision. Apply rechecks its
original base; a preview can become stale. A committed request returns its durable
receipt even if a following redraw/read fails. That read failure is separate from
the successful transaction acknowledgement.
