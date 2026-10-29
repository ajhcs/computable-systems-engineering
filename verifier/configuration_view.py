"""Deterministic presentations of freshly reconciled current-system facts.

These artifacts are simplified model-derived views. Artifact equality is not
SysML graphical conformance, executable behavior, or engineering acceptance.
"""
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import textwrap

from .foundation import read_regular

VERSION = 'configuration-system-artifacts-1.0'
GRAPH_VERSION = 'configuration-system-view-1.0'
FILES = ('system.svg', 'index.html', 'view.json')
STATUSES = {'pass', 'fail', 'unknown', 'unsupported', 'not_run', 'error'}
MAX_ARTIFACT = 32_000_000


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def _graph(report):
    graph = report.get('system_view')
    if not isinstance(graph, dict) or graph.get('version') != GRAPH_VERSION:
        raise ValueError('A connected configuration-1.1 report is required for a system view')
    if report.get('status') not in STATUSES or graph.get('status') != report['status']:
        raise ValueError('The graph must retain the configuration result status')
    nodes, edges = graph.get('nodes'), graph.get('edges')
    if not isinstance(nodes, dict) or len(nodes) > 513 or not isinstance(edges, dict) or len(edges) > 256:
        raise ValueError('System view exceeds the bounded node/edge contract')
    for key, node in nodes.items():
        if not isinstance(key, str) or not isinstance(node, dict) or node.get('kind') not in ('root', 'selected_role', 'external_role'):
            raise ValueError('Malformed current-system node')
        if any(not isinstance(node.get(field), str) for field in ('native_name', 'type')):
            raise ValueError('Node identities and types must be explicit text')
    for key, edge in edges.items():
        if not isinstance(key, str) or not isinstance(edge,dict) or edge.get('kind') != 'native_connection' or edge.get('directed') is not False:
            raise ValueError('Only reconciled undirected native adjacency is supported')
        for end in ('from', 'to'):
            endpoint = edge.get(end)
            if not isinstance(endpoint, dict) or endpoint.get('role') not in nodes or not isinstance(endpoint.get('port'), str):
                raise ValueError('An edge endpoint must name a reconciled node and port')
            if not isinstance(endpoint.get('path'), list) or not endpoint['path'] or any(not isinstance(x, str) for x in endpoint['path']):
                raise ValueError('An edge endpoint must retain its linked native feature path')
    if not isinstance(graph.get('omissions'), list) or not isinstance(graph.get('open_alternatives'), list):
        raise ValueError('The current-system graph must expose omissions and open alternatives')
    return graph


def _lines(value, width=30):
    return textwrap.wrap(str(value), width=width, break_long_words=True, break_on_hyphens=False) or ['']


def _diagnostics(report):
    return report.get('native', {}).get('parser_issues') or []


def _diagnostic_summary(report):
    issues = _diagnostics(report)
    warnings = sum(str(issue.get('severity', '')).upper() == 'WARNING' for issue in issues)
    label = 'warning' if warnings == 1 else 'warnings'
    return f'Native diagnostics: {len(issues)} ({warnings} {label}). Full diagnostics appear in the reader and ledger.'


def _svg(report, ledger):
    graph = report['system_view']; nodes = graph['nodes']; edges = graph['edges']
    ports = {key: set() for key in nodes}
    for edge in edges.values():
        for end in ('from', 'to'):
            endpoint=edge[end]; ports[endpoint['role']].add(endpoint['port'])
    positions = {}; port_positions = {}; column_y = [170, 170]
    for key, node in sorted(nodes.items(), key=lambda row: (row[1]['kind'] == 'external_role', row[0] != '$root', row[0])):
        col = 1 if node['kind'] == 'external_role' else 0
        x = 55 if col == 0 else 885
        labels = [('native', line) for line in _lines(node['native_name'])]
        labels += [('type', line) for line in _lines(node['type'])]
        labels += [('parent', line) for line in _lines('Parent: '+str(node.get('parent') or 'current context'))]
        heading = _lines(key,22)
        body_start = 54 + 24 * len(heading)
        port_start = body_start + 20 * len(labels) + 16
        height = port_start + 28 * len(ports[key]) + 22
        positions[key] = (x, column_y[col], 500, height, labels, col, heading, body_start)
        for index, port in enumerate(sorted(ports[key])):
            port_positions[(key, port)] = (x + (500 if col == 0 else 0), column_y[col]+port_start+index*28)
        column_y[col] += height + 32
    height = max(column_y)+130
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Current system: selected native declarations and connections</title>',
           '<desc id="desc">Simplified model-derived presentation of retained configuration obligations. Lines show undirected native connection adjacency; no flow, protocol, behavior, or complete architecture claim.</desc>',
           '<metadata>'+escape(_json(ledger))+'</metadata>',
           '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#203746}.id{font-size:20px;font-weight:bold}.small{font-size:15px}.muted{fill:#4b606e}.edge{fill:none;stroke:#526e86;stroke-width:2}.port{fill:white;stroke:#526e86;stroke-width:2}</style>',
           f'<rect width="1440" height="{height}" fill="#f7f9fb"/>',
           '<text x="55" y="42" font-size="26" font-weight="bold">Current system — retained configuration obligations</text>',
           f'<text x="55" y="77" font-size="20">Result: {escape(report["status"])} · simplified model-derived presentation</text>',
           '<text x="55" y="107" class="small">Selected declarations at left; explicit external peers at right. Lines are undirected adjacency.</text>',
           '<text x="55" y="133" class="small">Only reconciled facts are drawn. Findings, omitted checks and unselected topology appear in the reader and ledger.</text>',
           '<text x="55" y="157" class="small">'+escape(_diagnostic_summary(report))+'</text>']
    # Draw outside the cards; there are no arrows because ordinary connect is
    # adjacency rather than an item-flow or control-flow declaration.
    for index, (key, edge) in enumerate(sorted(edges.items())):
        a=port_positions[(edge['from']['role'],edge['from']['port'])];b=port_positions[(edge['to']['role'],edge['to']['port'])]
        ac=positions[edge['from']['role']][5];bc=positions[edge['to']['role']][5]
        lane=600+(index % 9)*24
        if ac == bc == 1:lane=840-(index % 9)*24
        native_label=edge.get('native_name') or ('anonymous connection owned by '+str(edge.get('owner')))
        out.append(f'<path class="edge" d="M {a[0]} {a[1]} H {lane} V {b[1]} H {b[0]}"><title>{escape(key+": "+native_label)}</title></path>')
        label_y=(a[1]+b[1])/2
        out.append(f'<text x="{lane+5}" y="{label_y-6}" class="small">C{index+1}</text>')
    for key, (x,y,w,h,labels,col,heading,body_start) in positions.items():
        node=nodes[key];fill='#edf2fb' if col == 0 else '#f2eef9'
        out.append(f'<g data-role-id="{escape(key, quote=True)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#899eaf"/>')
        for index,line in enumerate(heading):out.append(f'<text x="{x+18}" y="{y+30+index*24}" class="id">{escape(line)}</text>')
        out.append(f'<text x="{x+18}" y="{y+30+24*len(heading)}" class="small muted">{escape(node["kind"].replace("_"," "))}</text>')
        for index, (kind,line) in enumerate(labels):
            out.append(f'<text x="{x+18}" y="{y+body_start+index*20}" class="small {"muted" if kind != "native" else ""}">{escape(line)}</text>')
        for port in sorted(ports[key]):
            px,py=port_positions[(key,port)];full_label=port.split('::')[-1]
            label=full_label if len(full_label)<=26 else full_label[:25]+'…'
            out.append(f'<circle cx="{px}" cy="{py}" r="5" class="port"><title>{escape(port)}</title></circle>')
            tx=x+w-14 if col == 0 else x+14;anchor='end' if col == 0 else 'start'
            out.append(f'<text x="{tx}" y="{py+5}" text-anchor="{anchor}" class="small" data-native-port="{escape(port,quote=True)}">{escape(label)}</text>')
        out.append('</g>')
    footer=height-75
    out.extend([f'<text x="55" y="{footer}" class="small">Native model {escape(str(report.get("model_sha256", "unavailable")))}</text>',
                f'<text x="55" y="{footer+25}" class="small">Scope {escape(str(report.get("scope_sha256", "unavailable")))}</text>',
                '</svg>'])
    return '\n'.join(out)+'\n'


def _html(report):
    graph=report['system_view'];rows=[]
    node_rows=''.join('<tr><th>'+escape(key)+'</th><td>'+escape(node['kind'].replace('_',' '))+'</td><td><code>'+escape(node['native_name'])+'</code></td><td><code>'+escape(node['type'])+'</code></td><td>'+escape(str(node.get('parent') or 'current context'))+'</td></tr>' for key,node in sorted(graph['nodes'].items()))
    for index,(key, edge) in enumerate(sorted(graph['edges'].items())):
        def endpoint(end):
            value=edge[end]
            return escape(value['role'])+'<br/><code>'+escape(value['port'])+'</code><br/><small>Feature path: '+escape(' / '.join(value['path']))+'</small>'
        native_label=edge.get('native_name') or ('anonymous connection owned by '+str(edge.get('owner')))
        rows.append('<tr><th>C'+str(index+1)+' · '+escape(key)+'</th><td><code>'+escape(native_label)+'</code></td><td>'+endpoint('from')+'</td><td>'+endpoint('to')+'</td></tr>')
    findings=''.join('<li><strong>'+escape(str(f.get('id', '')))+' '+escape(str(f.get('status', '')))+':</strong> '+escape(str(f.get('detail', '')))+'</li>' for f in report.get('findings', []))
    diagnostics=''.join('<li><strong>'+escape(str(issue.get('severity', 'ISSUE')))+':</strong> <code>'+escape(str(issue.get('source') or 'native input'))+':'+escape(str(issue.get('line', '?')))+'</code> '+escape(str(issue.get('message', '')))+'</li>' for issue in _diagnostics(report))
    omissions=''.join('<li><strong>'+escape(str(o.get('id','')))+' '+escape(str(o.get('status','')))+':</strong> '+escape(str(o.get('reason','')))+'</li>' for o in graph['omissions'])
    alternatives=''.join('<li><code>'+escape(str(x))+'</code></li>' for x in graph['open_alternatives'])
    limits=''.join('<li>'+escape(str(x))+'</li>' for x in report.get('limits', []))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Current system — retained configuration</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;max-width:1440px;margin:2rem auto;padding:0 1rem;color:#203746;background:#f7f9fb}}.frame{{overflow:auto;border:1px solid #a7b7c4;background:white}}.frame img{{display:block;max-width:none}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:12px;border:1px solid #b8c5cf;vertical-align:top;text-align:left;overflow-wrap:anywhere}}code,small{{overflow-wrap:anywhere}}.status{{padding:1rem;border-left:5px solid #526e86;background:#edf2fb}}li{{margin:.6rem 0}}</style></head>
<body><h1>Current system — retained configuration obligations</h1><p class="status"><strong>Result: {escape(report['status'])}</strong>. Simplified model-derived presentation of selected native declarations and binary connection adjacency.</p>
<p>The diagram shows reconciled selected roles and explicit external peers. Ordinary connections are undirected; their placement does not establish data direction, a vendor protocol, execution, installation, or a complete architecture. Unreconciled required checks and native topology outside the retained scope remain listed below. Open alternatives are separate from current selections.</p>
<p><a href="system.svg">Editable SVG</a> · <a href="view.json">Source and view ledger</a></p><div class="frame"><img src="system.svg" width="1440" alt="Reconciled current-system roles and undirected native connection adjacency"/></div>
<h2>Current declarations</h2><table><thead><tr><th>Role ID</th><th>Kind</th><th>Native declaration</th><th>Direct type</th><th>Selected parent</th></tr></thead><tbody>{node_rows}</tbody></table>
<h2>Retained connection identities</h2><table><thead><tr><th>Connection ID</th><th>Native connection</th><th>Endpoint A</th><th>Endpoint B</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Findings</h2><ul>{findings or '<li>No findings within the retained scope.</li>'}</ul>
<h2>Native parser diagnostics</h2><p>{escape(_diagnostic_summary(report))} These diagnostics retain their native severity and do not change the retained-scope result by themselves.</p><ul>{diagnostics or '<li>No native parser diagnostics.</li>'}</ul>
<h2>Omitted or unresolved checks</h2><ul>{omissions or '<li>No omissions reported within the retained graph contract.</li>'}</ul>
<h2>Open library alternatives</h2><ul>{alternatives or '<li>No explicit open alternatives retained.</li>'}</ul>
<h2>Evidence limits</h2><ul>{limits}</ul><p>Model: <code>{escape(str(report.get('model_sha256')))}</code><br/>Scope: <code>{escape(str(report.get('scope_sha256')))}</code></p></body></html>
'''


def render_artifacts(report):
    """Render only facts produced by the connected native reconciliation route."""
    graph=_graph(report)
    ledger={'version':VERSION,'renderer_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'configuration_report_sha256':sha256(_json(report).encode()).hexdigest(),
            'status':report['status'],'model_sha256':report.get('model_sha256'),
            'model_files':report.get('model_files'),'scope_sha256':report.get('scope_sha256'),
            'checker_sha256':report.get('checker_sha256'),'native':report.get('native'),
            'system_view':graph,'findings':report.get('findings',[]),'limits':report.get('limits',[]),
            'edge_aliases':{'C'+str(index+1):key for index,key in enumerate(sorted(graph['edges']))},
            'claim_scope':'artifact_fidelity_to_fresh_connected_configuration_report',
            'behavior':'not_run','acceptance':'not_evaluated'}
    artifacts={'view.json':json.dumps(ledger,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n',
               'system.svg':_svg(report,ledger),'index.html':_html(report)}
    if any(len(text.encode())>MAX_ARTIFACT for text in artifacts.values()):
        raise ValueError('Rendered view exceeds artifact size bound')
    return artifacts


def write_view(report, destination):
    artifacts=render_artifacts(report);destination=Path(destination)
    destination.mkdir(parents=False,exist_ok=False)
    written=[]
    try:
        for name in FILES:
            with (destination/name).open('x',encoding='utf-8',newline='\n') as output:
                output.write(artifacts[name]);written.append(destination/name)
    except Exception:
        for path in written:path.unlink(missing_ok=True)
        try:destination.rmdir()
        except OSError:pass
        raise
    return {'version':VERSION,'status':report['status'],'configuration_status':report['status'],
            'output':str(destination),'files':{name:sha256(artifacts[name].encode()).hexdigest() for name in FILES},
            'claim_scope':'derived_current_system_presentation','acceptance':'not_evaluated'}


def check_view(report, destination):
    """Compare saved artifacts with fresh native-derived output; never load their facts."""
    result={'version':VERSION,'status':'error','configuration_status':report.get('status'),
            'view_status':'not_run','findings':[],'model_sha256':report.get('model_sha256'),
            'scope_sha256':report.get('scope_sha256'),'claim_scope':'artifact_fidelity_to_fresh_connected_configuration_report',
            'behavior':'not_run','acceptance':'not_evaluated'}
    try:
        expected=render_artifacts(report);destination=Path(destination)
        if destination.is_symlink() or not destination.is_dir():raise ValueError('View must be a regular artifact directory')
        if {p.name for p in destination.iterdir()} != set(FILES):raise ValueError('View directory must contain exactly the three generated artifacts')
        changed=[name for name in FILES if read_regular(destination/name,MAX_ARTIFACT)!=expected[name].encode()]
        result['view_status']='fail' if changed else 'pass'
        if changed:result['findings'].append({'rule':'view_mismatch','status':'fail','files':changed,'detail':'Saved artifacts differ from the fresh native-derived view; regenerate after reconciling the change'})
        result['status']='fail' if changed else report['status']
    except (OSError,ValueError,TypeError,KeyError) as exc:
        result['findings'].append({'rule':'view_input','status':'error','detail':str(exc)})
    return result
