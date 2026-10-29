#!/usr/bin/env python3
"""Build original editable CSE identity artwork. This is an explanatory graphic."""
from html import escape
from pathlib import Path
import sys,json

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from verifier.visual_style import font_css

HERE=Path(__file__).resolve().parent
INK='#18363F';TEAL='#126C70';PAPER='#F8F7F1';LINE='#C6D3CF';ORANGE='#D26C3C'

def text(x,y,value,size=28,fill=INK,weight=400,family='Space Grotesk',extra=''):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{escape(value)}</text>'

def rect(x,y,w,h,fill,stroke='none',r=0,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" {extra}/>'

def overview():
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="830" viewBox="0 0 1600 830" role="img" aria-labelledby="title desc">',
           '<title id="title">Computable Systems Engineering — a clearer picture of complex systems</title>',
           '<desc id="desc">Original explanatory illustration: a question, an editable connected model, and inspectable evidence. The marks describe the CSE workflow; they are not a formal SysML model, a product screenshot, or a verification result.</desc>',
           '<style><![CDATA['+font_css()+']]></style>',rect(0,0,1600,830,PAPER),
           '<path d="M0 0H1600V830H0Z" fill="none" stroke="#DFE5DE" stroke-width="2"/>']
    # A visible alignment rail ties the three editorial regions together.
    parts += [rect(72,72,44,44,TEAL,r=10),
              '<path d="M85 95H103M94 86V104" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>',
              text(134,104,'COMPUTABLE SYSTEMS ENGINEERING',25,TEAL,700),
              text(72,253,'A clearer picture.',82,INK,700,'Inter'),
              text(72,350,'Better questions.',82,INK,700,'Inter'),
              text(76,422,'Connected models. Inspectable evidence.',30),
              text(76,470,'You guide the decisions.',30,TEAL),
              '<path d="M76 539H1524" stroke="'+LINE+'" stroke-width="2"/>']
    # Open-ended model motif, deliberately non-notational: no engineering edge
    # kinds, direction, multiplicity, or computed status is implied.
    parts += ['<g aria-label="Illustrative connected model">',
              '<path d="M1186 200H1366V316H1458M1186 200V368H1074M1186 200H1032V110M1186 200V94" fill="none" stroke="'+LINE+'" stroke-width="4" stroke-linecap="round"/>',
              rect(1090,151,190,95,TEAL,r=15),text(1185,209,'MODEL',30,'#FFFFFF',700,extra='text-anchor="middle"'),
              rect(1280,278,184,80,'#E7EEEA',r=12),text(1372,328,'People',27,INK,extra='text-anchor="middle"'),
              rect(970,329,184,80,'#E7EEEA',r=12),text(1062,379,'Technology',25,INK,extra='text-anchor="middle"'),
              '<circle cx="1032" cy="110" r="15" fill="'+ORANGE+'"/><circle cx="1186" cy="94" r="9" fill="'+TEAL+'"/><circle cx="1458" cy="316" r="9" fill="'+ORANGE+'"/>',
              text(1216,415,'Decisions stay visible.',24,TEAL),'</g>']
    positions=[76,580,1084]
    rows=[('01','ASK','Start with a real question.'),('02','MODEL','Make the relationships explicit.'),('03','CHECK','See what the evidence supports.')]
    for x,(number,heading,detail) in zip(positions,rows):
        parts += [text(x,610,number,24,TEAL),text(x+55,614,heading,34,INK,700),text(x,674,detail,25)]
    parts += [text(76,775,'IDEAS  /  OPERATIONS  /  SOFTWARE  /  EQUIPMENT  /  SERVICES',21,TEAL),
              text(1524,775,'CSE',25,TEAL,700,extra='text-anchor="end"'),'</svg>']
    return '\n'.join(parts)+'\n'

def connected():
    ledger=json.loads((ROOT/'examples/configuration-review/connected/generated/view.json').read_text())
    graph=ledger['system_view'];nodes=graph['nodes'];edges=graph['edges']
    assert ledger['status']=='pass' and set(nodes)=={'$root','Sensor','Enterprise'} and set(edges)=={'DataLink'}
    edge=edges['DataLink']
    assert edge['directed'] is False and edge['from']['role']=='Sensor' and edge['to']['role']=='Enterprise'
    assert nodes['Sensor']['parent']=='$root'
    assert nodes['$root']['kind']=='root' and nodes['Sensor']['kind']=='selected_role' and nodes['Enterprise']['kind']=='external_role'
    root_id=escape(nodes['$root']['native_name'],quote=True)
    sensor_id=escape(nodes['Sensor']['native_name'],quote=True)
    peer_id=escape(nodes['Enterprise']['native_name'],quote=True)
    edge_id=escape(edge['native_name'],quote=True)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="820" viewBox="0 0 1600 820" role="img" aria-labelledby="title desc">',
           '<title id="title">A selected current system and its external connection</title>',
           '<desc id="desc">Simplified model-derived presentation of the checked synthetic LinkContext example. A sensor role is inside the selected current system. Its output port is connected by ordinary undirected native adjacency to an external receiver input. Labels are shortened; full native paths remain in the linked system reader and ledger. Multiplicity and behavior are not drawn.</desc>',
           '<style><![CDATA['+font_css()+']]></style>',rect(0,0,1600,820,PAPER),
           text(72,74,'CONNECTED CONTEXT',24,TEAL,700),
           text(72,147,'The selected system. The exact connection.',48,INK,700,'Inter'),
           f'<g data-native="{root_id}" data-kind="selected-root">',
           rect(72,212,850,373,'#E7EEEA',LINE,18),text(108,268,'Current system',34,INK,700),
           text(108,308,nodes['$root']['native_name'],23,TEAL),
           f'<g data-native="{sensor_id}" data-parent="{root_id}">',
           rect(110,352,774,184,'#FFFFFF',TEAL,12,extra='stroke-width="2"'),
           text(146,411,'Sensor',38,INK,700),text(146,455,'Selected nested role',25,TEAL),
           text(146,496,nodes['Sensor']['type'],22,INK),
           text(854,458,edge['from']['port'].split('::')[-1],24,TEAL,extra='text-anchor="end"'),'</g></g>',
           f'<g data-native="{peer_id}" data-kind="external-peer">',
           rect(1122,352,406,184,'#F4E8DD','#D6C3B2',12),
           text(1156,410,nodes['Enterprise']['type'].split('::')[-1],38,INK,700),text(1156,454,'Explicit external peer',24,INK),
           text(1156,494,nodes['Enterprise']['native_name'],21,INK),'</g>',
           f'<g data-native="{edge_id}" data-directed="false" data-from-port="{escape(edge["from"]["port"],quote=True)}" data-to-port="{escape(edge["to"]["port"],quote=True)}">',
           '<path d="M884 446H1122" fill="none" stroke="'+TEAL+'" stroke-width="3"/>',
           '<circle cx="884" cy="446" r="7" fill="#FFFFFF" stroke="'+TEAL+'" stroke-width="3"/>',
           '<circle cx="1122" cy="446" r="7" fill="#FFFFFF" stroke="'+TEAL+'" stroke-width="3"/>',
           text(1003,424,'DataLink',23,TEAL,extra='text-anchor="middle"'),
           text(1106,483,edge['to']['port'].split('::')[-1],22,TEAL,extra='text-anchor="end"'),'</g>',
           '<path d="M72 642H1528" stroke="'+LINE+'" stroke-width="2"/>',
           text(72,699,'Selected native identities • retained scope • fresh view check',29,TEAL),
           text(72,755,'Synthetic model-derived example. The line shows adjacency; direction, protocol, and behavior are unassessed.',23,INK),
           '</svg>']
    return '\n'.join(parts)+'\n'

def build():
    sources={'cse-overview.svg':overview(),'connected-overview.svg':connected()}
    for name,value in sources.items():
        if '--check' in sys.argv:
            assert (HERE/name).read_text()==value,'Stale README source: '+name
        else:(HERE/name).write_text(value)

if __name__=='__main__':build()
