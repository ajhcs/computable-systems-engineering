# Physical architecture

Use this method for the selected system's realizing elements and configuration.
Retain the system boundary and distinguish owned parts from external peers.
Components may include hardware, software, people, facilities or procedures when
relevant to the question; do not force every project into a fixed catalog.

Identify each part's native declaration, direct type, parent and multiplicity.
Separate available type definitions and historical options from selected roles.
A type's presence does not establish an installed instance or quantity. Keep
unknown selection and variability explicit rather than creating surrogate parts
to make the current context checkable.

Read [configuration reconciliation](../../../docs/configuration-review.md). Use
`configuration-1.0` for its supported declaration/selection claims, or explicitly
select `configuration-1.1` when native ordinary connections and external peers
are in scope. Retain the engineer's scope separately. Through the shared launcher:

```text
python3 <launcher> configuration-review fingerprint SCOPE.json
python3 <launcher> configuration-review check LIBRARY.sysml CURRENT.sysml --scope SCOPE.json --scope-sha256 RETAINED_DIGEST
```

Resolve `<launcher>` to this skill's sibling
`../develop-system-concept/scripts/cse.py`; use absolute input paths outside their
project directory. Keep the returned scope digest with the selected revision;
it identifies bytes, not engineer assent. The existing
`examples/configuration-review/connected/` bundle is a synthetic 1.1 example.
Review missing roles, overrides, omitted connectors and unsupported forms before
claiming that selected configuration facts reconcile. Changing selection is an
engineering proposal, not an automatic fingerprint refresh.

When a current-system view is requested, reuse [configuration views](../../../docs/configuration-system-view.md)
or the diagram skill. Reconciled ordinary connections establish scoped undirected
adjacency. Direction, payload compatibility, delivery, installation and physical
fit require their own representation and evidence.

Method basis: Buede and Miller, *The Engineering Design of Systems: Models and
Methods*, fourth edition, Chapter 8, pp. 210–211. The native selection and
reconciliation rules are CSE implementation choices, not a complete physical
design method.
