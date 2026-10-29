# Synthetic connected design context

`library.sysml` supplies a sensor, its logical port, a system and an external
receiver. `current.sysml` defines the current system usage and an explicitly
referenced receiver, joined by an ordinary binary native connection. The
historical system and second receiver are deliberately present as unselected
same-type controls: using them changes the linked endpoint path even when local
port names and types remain the same.

The native adapter extracts linked feature chains, preserving the root usage,
declared nested role and declared port identities. It does not reconstruct paths
from source text or claim a protocol, transport direction, actual device,
installed topology or execution. Ordinary `connect` adjacency is undirected.
Anonymous connections retain owner and endpoint paths without inventing a name;
source file and line are diagnostics rather than semantic identities.

The native tests cover named/anonymous and reversed connections, retargeted
historical roots/peers, inherited ports, usage-owned relative endpoint paths,
removed connections/ports and binding connectors. Binding, flow, specialized or
other nonordinary connection kinds are retained as unsupported for this bounded
connection interpretation. This is a synthetic software fixture, not a real
engineering project or accepted architecture.

The [native-generated SVG](generated/system.svg), [HTML reader](generated/index.html)
and [trace ledger](generated/view.json) are saved outputs for this exact fixture.
The README's [simplified illustration](../../../assets/readme/connected-overview.svg)
derives from that ledger. It shortens labels and omits multiplicity; the native
outputs retain the checked facts and their explicit limitations.

The regression suite reruns native reconciliation and `check-view` against this
saved artifact directory. Regenerate into a new output directory with
`scripts/configuration.py view` when source or checker bytes change, review the
new output, then replace this fixture's generated artifacts. Keep screenshots
and other evidence outside the three-file native view directory.
