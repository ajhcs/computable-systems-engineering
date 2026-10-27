# Independent holds: bounded local contract

Application 1.3 stores holds by `(record_id, hold_id)` in schema 2. Releasing one
hold changes only that row. Disposition is blocked while any hold on the target
record is active. The captured aggregate flag is computed from those rows,
rather than stored separately.

This is a dummy application, not enforcement of actual issuer authority or
retention obligations. Notice basis, applicability, completeness and stakeholder
acceptance remain unestablished. All policies and local identities are fixtures.

## Operations and bounds

- `hold_id` is a case-sensitive 1..64 character ASCII identity using letters,
  digits and `_.:-`, starting with a letter or digit. It is scoped to one record.
- Calls without `hold_id` address the single `fixture-default` hold. This retains
  the simple fixture API and never means all holds. The initially held fixture
  records have that named hold.
- On an active record, reapplying an active ID or releasing an already released
  ID returns no change.
  An unknown ID is denied; releasing an ID on another record does not affect the
  original record. A released ID cannot be reused; a new notice needs a new ID.
- There are at most 64 hold rows per record, including released history. This is
  a prototype capture bound, not a record-management policy. Reaching the bound
  refuses a new ID without deleting history.
- Fixture permission and session checks still apply. SQL transactions serialize
  local changes; an SQL audit failure rolls back both the release and its capture.
  These checks do not prove physical crash safety or distributed behavior.
- Holds cannot be applied to an already disposed record. Setting a flag or
  denying restore does not recover removed content or missing audit evidence.

## Reproduce normal and faulty behavior

With the pinned parser available, run from the repository root:

```sh
python3 skills/develop-system-concept/scripts/cse.py prototype-demo --output work/named-holds-normal
python3 skills/develop-system-concept/scripts/cse.py prototype-demo --output work/named-holds-fault --fault release_all_holds
```

Both output directories must be new. The normal run executes 33 captured dummy
transactions and passes the twelve-obligation selection. Transactions 27–33
apply A and B, release A, demonstrate that B blocks disposition, then release B
and dispose. The explicit fault clears every hold on the target record during
A's release. It is expected to exit nonzero and fail `R_D_HOLD_PRESERVE`.

[hold-manifest.json](hold-manifest.json) retains the original eleven expected
obligations and adds [the new requirement](independent-holds.sysml). The original
[strict manifest](strict-manifest.json) remains unchanged and separately usable;
its Boolean-hold requirement checks disposition gating, not preservation of
other hold identities during release. No general execution engine was added.

The registered `repair_reuse_sqlite_v4` observer independently compares typed
before/after rows for the target record, excluding only the requested ID. A
validly captured release-all fault is a monitor failure. Missing or malformed
identity/rows, duplicate or foreign IDs, unknown flags and contradictory
aggregates are capture errors before monitoring. The per-record capture does
not establish that every real-world notice was supplied or provide a global
multi-record snapshot proof. Unit tests separately check record isolation.

Fresh databases and captures are required. Older schemas and v1/v2/v3 captures
are not migrated or relabeled. Hashes identify supplied bytes, not authorized
decisions or protected execution. `recorded_boolean_signals_v1` remains a
separate, narrower correspondence profile.

## Verification and limits

The synthetic [hold tests](../../tests/test_independent_holds.py) cover multiple
holds, default-ID compatibility, retries, wrong-record/unknown/unauthorized
release, persistence, SQL rollback, one concurrent release/addition pair, bounds,
old-schema refusal and adversarial capture fields. The
[prototype review tests](../../tests/test_prototype_review.py) exercise the new
native obligation with actual normal/faulty captures and reject incomplete hold
evidence. The [walkthrough](walkthrough/README.md) retains the existing eleven
checks and the unresolved copy/audit recovery examples.

Real authority, intended-use validation, participant competence, acceptance and
ISO conformity remain unresolved or unassessed. No full project evaluation plan
is completed merely by running these local tests.
