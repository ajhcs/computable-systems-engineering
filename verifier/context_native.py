"""Bounded traversal of explicit linked native declaration references.

These references do not reconcile a selected configuration, prove that an
instance is present, or establish directed item/control flow. Connection paths
come from the native parser, never from splitting source text or labels. The
guards and ancestry fields follow ``configuration._reconcile_connected``;
configuration selection and its stronger endpoint proof remain separate.
"""

REFERENCE_CLAIM_SCOPE = 'parsed_native_declaration_references_not_configuration_or_flow'
MAX_RECORDS = 10000
MAX_ENDPOINT_COMPONENTS = 32  # SysmlBridge.connectionFacts' linked-chain bound.
MAX_ANCESTORS = 512
MAX_REFERENCE_WORK = 100000


def add_native_references(index, graph, *, connections=None):
    """Add explicit references to an existing native graph; return unresolved rows.

    ``index`` maps existing native keys to ``{category, record}``; ``graph`` maps
    those keys to target/reason lists. Neither native records nor index are
    modified. Pass the complete parser ``inventory['connections']`` explicitly:
    named-only indexes cannot otherwise disclose omitted anonymous connectors.

    Returned records contain ``rule``, ``status``, native anchor ``ids``,
    ``detail`` and ``claim_scope``. Connector records also have a ``scope_hint``
    with their unchanged owner/source location. If either endpoint context is
    unavailable, a caller must conservatively retain the unresolved record for a
    selected declaration in the same owner/source context; disjointness was not
    established. No synthetic native identity is assigned to an anonymous row.

    A named supported connector refers to every exact component in its linked
    paths. Reverse traversal is restricted to the explicitly named endpoint
    context or usage owner. A type-owned port shared by several instances does
    not make a connection incident on every instance of that type. Definition
    ancestry and port typing are followed only toward their declared targets.
    """
    if type(index) is not dict or type(graph) is not dict or len(index) > MAX_RECORDS:
        raise ValueError('Native reference index exceeds its bounded map contract')
    if connections is None:
        connections = [item['record'] for item in index.values()
                       if item['category'] == 'connections']
    if type(connections) is not list or len(connections) > MAX_RECORDS:
        raise ValueError('Native connections need a bounded list')
    unresolved = []
    work = 0

    def spend(count=1):
        nonlocal work
        work += count
        if work > MAX_REFERENCE_WORK:
            raise ValueError('Native reference traversal work cap exceeded')

    def key(category, name):
        spend()
        value = category + ':' + name if type(name) is str and name else None
        return value if value in index and value in graph else None

    def edge(left, right, reason, reciprocal=False):
        spend()
        if left not in graph or right not in graph:
            return
        reasons = graph[left].setdefault(right, [])
        if reason not in reasons:
            reasons.append(reason)
        if reciprocal:
            edge(right, left, reason)

    def issue(rule, status, anchors, detail, row=None, endpoint_anchors=(), contexts_complete=True):
        result = {'rule': rule, 'status': status,
                  'ids': sorted(anchor for anchor in set(anchors) if anchor in graph),
                  'detail': detail, 'claim_scope': REFERENCE_CLAIM_SCOPE}
        if row is not None:
            result['scope_hint'] = {
                field: row.get(field) for field in
                ('qualified_name', 'owner', 'owner_kind', 'source', 'line')}
            result['scope_hint']['endpoint_anchors'] = sorted(set(endpoint_anchors))
            result['scope_hint']['conservative_same_context'] = (not contexts_complete
                                                                or not bool(endpoint_anchors))
        unresolved.append(result)

    # Direct declaration references are one-way: a shared type does not imply
    # references back to every usage or every derived definition.
    for identity, item in sorted(index.items()):
        spend()
        row, category = item['record'], item['category']
        if category == 'ports':
            target = key('port_definitions', row.get('type'))
            if target is None:
                issue('native_port_type', 'unknown', [identity],
                      'The port has no single available exact direct port-definition reference.')
            else:
                edge(identity, target, 'native_port_direct_type_reference')
        if category not in ('part_definitions', 'port_definitions'):
            continue
        parents = row.get('supertypes', [])
        if type(parents) is not list or len(parents) > MAX_ANCESTORS:
            issue('native_definition_ancestry', 'unsupported', [identity],
                  'Native definition ancestry is not an available bounded reference list.')
            continue
        for parent in parents:
            target = key(category, parent)
            if target is None:
                issue('native_definition_ancestry', 'unknown', [identity],
                      'An explicitly declared native supertype is absent from the supplied context.')
            else:
                edge(identity, target, 'native_declared_supertype_reference')
        if category == 'port_definitions' and row.get('is_conjugated'):
            target = key('port_definitions', row.get('original_port_definition'))
            if target is None:
                issue('native_conjugated_port_type', 'unknown', [identity],
                      'The conjugated port definition has no available exact original definition.')
            else:
                edge(identity, target, 'native_conjugated_original_type_reference')

    def location(row):
        return (row.get('qualified_name') or '', row.get('source') or '',
                row.get('line') if type(row.get('line')) is int else -1)

    for row in sorted(connections, key=location):
        spend()
        connector = key('connections', row.get('qualified_name'))
        owner = key('parts', row.get('owner'))
        definition_owner = (key('part_definitions', row.get('owner')) or
                            key('port_definitions', row.get('owner')))
        anchors = {value for value in (connector, owner, definition_owner) if value}
        endpoint_anchors, targets = set(), set()
        ends = row.get('ends')
        supported = (row.get('supported') is True and row.get('kind') == 'ConnectionUsage'
                     and not any(row.get(flag) for flag in
                                 ('has_native_value', 'has_non_typing_specialization',
                                  'is_variation', 'is_variant'))
                     and type(ends) is list and len(ends) == 2)
        paths_available = contexts_complete = True
        if type(ends) is not list or len(ends) != 2:
            paths_available = contexts_complete = False
            ends = []
        for end in ends:
            spend()
            path = end.get('path') if type(end) is dict else None
            if (type(path) is not list or not 1 <= len(path) <= MAX_ENDPOINT_COMPONENTS
                    or any(type(name) is not str or not name for name in path)):
                paths_available = contexts_complete = False
                supported = False
                continue
            # Preserve the complete parser path. Its exact first context usage
            # establishes reverse traversal; a shared type-owned member does not.
            end_anchors = set()
            first = key('parts', path[0])
            if first is not None:
                first_row = index[first]['record']
                if first_row.get('owner_kind') == 'Package' or first == owner:
                    end_anchors.add(first)
            if owner is not None:
                end_anchors.add(owner)
            endpoint_anchors.update(end_anchors)
            contexts_complete = (contexts_complete and end.get('status') == 'supported'
                                 and bool(end_anchors or definition_owner))
            for position, name in enumerate(path):
                target = key('ports' if position == len(path) - 1 else 'parts', name)
                if target is None:
                    paths_available = contexts_complete = False
                else:
                    targets.add(target)
            supported = supported and end.get('status') == 'supported'
        anchors.update(endpoint_anchors)
        if row.get('qualified_name') is None:
            issue('native_anonymous_connection', 'unknown', anchors,
                  'An anonymous native connection has no qualified identity in this view; '
                  'its endpoint dependency coverage remains unresolved.', row, endpoint_anchors,
                  contexts_complete)
            continue
        if connector is None or not paths_available:
            issue('native_connection_reference', 'unknown', anchors,
                  'A native connection identity or exact linked endpoint-path declaration is '
                  'missing from the supplied context.', row, endpoint_anchors, contexts_complete)
            continue
        if not supported:
            issue('native_connection_reference', 'unsupported', anchors,
                  'Only parser-supported unspecialized ordinary binary static connection '
                  'references are traversed; this connection remains unresolved.', row, endpoint_anchors,
                  contexts_complete)
            continue
        if not contexts_complete:
            issue('native_connection_context', 'unknown', anchors,
                  'At least one native endpoint lacks an exact context usage or definition owner; '
                  'shared port types cannot supply instance incidence.', row, endpoint_anchors,
                  contexts_complete)
            continue
        for target in sorted(targets):
            edge(connector, target, 'native_linked_endpoint_path_reference')
        for anchor in sorted(endpoint_anchors | ({definition_owner} if definition_owner else set())):
            edge(anchor, connector, 'native_connection_context_reference', reciprocal=True)

    return sorted(unresolved, key=lambda row: (row['rule'], row['ids'], row['detail'],
                                               str(row.get('scope_hint', {}))))
