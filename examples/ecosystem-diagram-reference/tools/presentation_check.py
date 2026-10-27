"""Bounded, read-only SVG/fact correspondence for the three retained presentations."""
from collections import Counter
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from cases import KEYS, require_case, require_release_scope

def require(ok,message):
    if not ok:raise ValueError(message)

def numbers(value):
    return tuple(float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',value))

def validate_svg(key,facts,view,svg,aliases):
    require_case(key)
    root=ET.fromstring(svg) if isinstance(svg,str) else svg
    # Correspondence below uses the supplied coordinates, not a CSS/SVG
    # rendering engine. Reject transforms on marks or ancestors instead of
    # treating displaced geometry as if it remained in its recorded cell.
    for element in root.iter():
        require('transform' not in element.attrib and not element.tag.endswith('animateTransform'),key+': unsupported SVG transform')
        css=element.get('style','')
        if element.tag.endswith('style'):css+=''.join(element.itertext())
        require(not re.search(r'(?:^|[;{])\s*(?:-[a-z]+-)?(?:transform(?:-origin)?|translate|rotate|scale)\s*:',css,re.I),key+': unsupported CSS transform')
    elements=facts['elements'];by_native={e['id']:e for e in elements}
    groups={e.get('data-node'):e for e in root.iter() if e.get('data-node')}
    rows={n['id']:n for n in view['nodes']}
    require(set(groups)==set(rows) and len(groups)==len(view['nodes'])==sum(bool(e.get('data-node')) for e in root.iter()),key+': missing/extra/duplicate visible nodes')
    boundaries={}
    for e in elements:
        if e['kind']!='SuccessionAsUsage' or not e.get('owner'):continue
        a=e['source'].get('qualified');b=e['targets'][0].get('qualified')
        if a=='Actions::Action::start':boundaries[b.split('::')[-1]]='entry'
        if b=='Actions::Action::done':boundaries[a.split('::')[-1]]='exit'
    textures=set()
    for n in rows.values():
        g=groups[n['id']];native=by_native[n['native_id']]
        require(g.get('data-native-id')==n['native_id'] and native['qualified']==n['qualified'],key+': visible node identity')
        shape=next(e for e in g if e.tag.endswith(('rect','path')))
        x,y,w,h=(n[t] for t in ['x','y','w','h'])
        if n['kind'] in ['DecisionNode','MergeNode']:
            expected=(x+w/2,y,x+w,y+h/2,x+w/2,y+h,x,y+h/2)
            require(numbers(shape.get('d',''))==expected,key+': diamond geometry')
        else:require(tuple(float(shape.get(t)) for t in ['x','y','width','height'])==(x,y,w,h),key+': node geometry')
        expected='projection' if key[0]=='E' and aliases['E'][n['id']].get('projection')=='representative usage' else None
        actual={e.get('fill') for e in g.iter() if re.fullmatch(r'url\(#[\w-]*Texture\)',e.get('fill',''))}
        textures|=actual
        require(n.get('texture_property')==expected and actual==({f'url(#{expected}Texture)'} if expected else set()),key+': texture duplicates or invents a property at '+n['id'])
    drawn_edges={e.get('data-edge'):e for e in root.iter() if e.get('data-edge')}
    require(set(drawn_edges)=={e['id'] for e in view['edges']} and len(drawn_edges)==len(view['edges'])==sum(bool(e.get('data-edge')) for e in root.iter()),key+': missing/extra/duplicate visible edges')
    for e in view['edges']:
        shape=drawn_edges[e['id']]
        require(shape.get('data-native-id')==e['native_id'],key+': edge native identity')
        require(numbers(shape.get('d',''))==tuple(v for p in e['points'] for v in p),key+': edge geometry')
        require(bool(shape.get('marker-end'))==e['directed'],key+': edge direction')
    texts=[e for e in root.iter() if e.tag.endswith('text')]
    if key[0] in ['D','E']:
        column_x={}
        for row_id in rows:
            if row_id.endswith('-electrical'):continue
            candidates={float(t.get('x')) for t in texts if t.get('data-label-owner')==row_id and t.get('text-anchor')=='middle'}
            require(len(candidates)==1,key+': missing/ambiguous column heading')
            column_x[row_id]=candidates.pop()
        if key[0]=='D':
            visible=[]
            for e in root.iter():
                if e.get('data-relation'):
                    cx,cy=float(e.get('cx')),float(e.get('cy'))
                    r=e.get('data-row');c=e.get('data-col')
                    require(r in rows and c in column_x and cx==column_x[c] and rows[r]['y']<cy<rows[r]['y']+rows[r]['h'],key+': misplaced matrix marker')
                    visible.append((e.get('data-relation'),r,c))
            expected=[(a['native_id'],a['row'],a['column']) for a in view['annotations']]
        else:
            visible=[];alloc_by_name={e['name']:e['id'] for e in elements if e['kind']=='AllocationUsage'}
            for t in texts:
                if t.get('data-label-owner') not in alloc_by_name:continue
                x,y=float(t.get('x')),float(t.get('y'))
                row_ids=[n['id'] for n in rows.values() if n['y']<y<n['y']+n['h']]
                col_ids=[c for c,cx in column_x.items() if cx==x]
                require(len(row_ids)==len(col_ids)==1,key+': allocation arrow has no unique cell')
                visible.append((alloc_by_name[t.get('data-label-owner')],row_ids[0],col_ids[0],t.text))
            expected=[(a['native_id'],a['row'],a['column'],a['symbol']) for a in view['annotations']]
            for source_id,a in aliases['E'].items():
                owned=[t for t in texts if t.get('data-label-owner')==source_id]
                require(sum(t.text==source_id for t in owned)==2,key+': source identifier lost')
                require(any(t.text==a['display'] for t in groups[source_id].iter() if t.tag.endswith('text')),key+': readable row alias lost')
                require(' '.join(t.text for t in owned if t.get('text-anchor')=='middle' and t.text!=source_id)==a['display'],key+': column alias disagrees with row alias')
                require(all(float(t.get('font-size'))<=12 for t in owned if t.text==source_id),key+': technical name outranks human label')
        require(Counter(visible)==Counter(expected),key+': matrix meaning or cell count changed')
    regions={e.get('data-region') for e in root.iter()};panels={e.get('data-panel') for e in root.iter()}
    if key[0]=='C':require({'equipment-details','schedule-totals'}<=regions,'C: metadata/totals unowned')
    if key[0]=='D':require({'communication','electrical'}<=panels,'D: layer headings unowned')
    if key[0]=='E':require({'projection-key','direction-key'}<=regions and 'allocation-matrix' in panels,'E: matrix key unowned')
    return {'key':key,'nodes':len(rows),'edges':len(drawn_edges),'matrix_cells':len(view['annotations']),'semantic_texture_fills':sorted(textures)}

def validate_presentations(root):
    root=Path(root);require_release_scope(root);aliases=json.loads((root/'source/display-aliases.json').read_text());result=[]
    for key in KEYS:
        result.append(validate_svg(key,json.loads((root/'native'/(key+'.facts.json')).read_text()),json.loads((root/'rendered'/(key+'.view.json')).read_text()),(root/'rendered'/(key+'.svg')).read_text(),aliases))
    return result
