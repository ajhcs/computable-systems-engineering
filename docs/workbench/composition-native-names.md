# Native names in physical-composition renames

The source CLI, local Git transaction, visible rename form and site callback use
one `CompositionDocument.rename` operation. A rename changes an element's native
name while preserving its engineering UUID, short ID and unrelated source bytes.
This completes an existing operation within the active physical capability.

A SysML alias is a native Membership. It is distinct from the presentation alias
in a `display_labels` companion. Neither is replaced merely because its spelling
matches the renamed element's old name.

| Source reference | Rename behavior |
|---|---|
| Declared/effective name | Change the exact native Name token when it binds the renamed element or an unnamed redefinition whose effective name follows it. |
| Short ID | Preserve its spelling, including when the old declared name equals that short ID. |
| Explicit alias name or alias short ID | Preserve the authored spelling; update the alias's target reference only where that reference itself uses a changed element name. |
| Mixed qualified path | Resolve each prefix independently. An alias or short prefix stays fixed while an affected element-name segment changes. |
| Prefix exposing an external/inherited member | Change the renamed prefix even when the final target keeps its native identity and declaring owner. |
| Explicitly named redefinition | Preserve its own name; unnamed redefinition chains follow the renamed inherited name. |

The pinned Xtext resource scope provider selects native Memberships for exact
`ID` and `UNRESTRICTED_NAME` leaves. The native QualifiedName converter decodes
quoted names and global qualification; no ASCII regex splits a SysML path.
Redefinition queries retain the native provider's redefinition and skip context.
The final selected Membership's element must be the original linked EObject.
`reference_spans[].name_binding` records the status, UTF-16 token ranges,
spellings, name kinds and target identities. Unsupported or errored extraction
is explicit; an affected reference cannot be repaired by guessing its spelling.

New qualified identities use the exact native owner. Root declarations and
quoted names or owners containing `::` therefore do not depend on string
splitting. The expected native fingerprint changes only typed identity fields;
short IDs, unrelated local names, status words and prose remain independent.
The candidate is reparsed and its complete extracted fingerprint, registry and
ordered resolved-reference targets must match the requested change. Typed
workflow/view bindings update atomically. Retained configuration scope bytes stay
fixed, with fresh findings and explicit reconciliation where names became stale.

The [synthetic source](../../examples/workbench/composition/reference-names.sysml)
provides ownership and Unicode-type views over the same model. Regression cases
cover alias chains and collisions, equal short/name spellings, inherited and
redefined members, global/quoted paths, roots, CRLF/multifile source preservation,
CLI parity and Git retry/reopen/restore. Local browser checks exercise direct
and site-callback renames, lost acknowledgements, exact reload/retry, original
SVG/font provenance and reconstructed exports on desktop and narrow screens.
The physical font adapter uses a fixed additional repertoire from the exact
original TTFs, preserving precomposed Latin names such as `Sénsor::unit`.
The profile's source advances are checked independently against TrueType
tables and actual Chromium glyphs and text advances. General Unicode shaping
and glyphs outside that qualified profile remain open.
Site callbacks in that harness are synthetic host registrations; they do not
establish actual Codex or ChatGPT acceptance.

Replacement names retain the current limit: one ASCII identifier beginning with
a letter, at most 64 characters. Authoring quoted/Unicode replacement names,
short-only declarations without a native qualified identity, conjugated and
other unadapted reference forms, and native qualified-name linker limitations
remain open obligations. A diagnostic input is refused, not silently normalized.
These boundaries do not reduce the agreed union of existing support or close
the physical-composition capability. Follow the [SVG fidelity contract](composition-svg-fidelity.md)
for its diagrams and the central parity matrix for remaining completion gates.
