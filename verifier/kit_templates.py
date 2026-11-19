"""Bounded, catalog-pinned adaptations of engineering-palette SVG masters."""
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'engineering-library'
CATALOG_SHA256 = '1a75aae3836202b203f08936d1e6d3f6745c124fd431a24cbe1c26d7f38628c6'
NS = 'http://www.w3.org/2000/svg'
SVG = '{' + NS + '}'
ET.register_namespace('', NS)
LABEL = 'palette-src-labels-redesign-labelslanes-connection-labels-boxed-artwork'
ARROW = 'palette-src-foundation-foundation-arrowheads-filled-triangle-artwork'
DASHED = 'palette-foundation-lines-dashed-artwork'
GAP = 'palette-src-foundation-foundation-crossings-gap-artwork'
TITLE_BLOCK = 'palette-refined-documents-documents-page1-title-block'
REVISION_BLOCK = 'palette-refined-documents-documents-page1-revision-block'
FIGURE_HEADING = 'palette-refined-documents-documents-page1-navigation-figure-heading-1'
LEGEND = 'palette-refined-documents-documents-page1-navigation-legend'
DOC_TEMPLATES = frozenset((TITLE_BLOCK, REVISION_BLOCK, FIGURE_HEADING, LEGEND))
TEMPLATES = frozenset(f'palette-{shape}-{tone}-{pattern}' for shape in ('rectangle', 'circle')
                      for tone in ('white', 'reverse', 'grey') for pattern in ('plain', 'dots', 'diagonal')) | {LABEL}
_ALLOWED = {'svg', 'defs', 'g', 'mask', 'pattern', 'rect', 'circle', 'path', 'use', 'text', 'tspan', 'title'}
_PREFIX = re.compile(r'^[A-Za-z_][A-Za-z0-9_.-]*$')
_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
_URL = re.compile(r'url\(\s*[\'"]?#([^\s)\'"]+)[\'"]?\s*\)')


def _source(template_id):
    if template_id not in TEMPLATES | DOC_TEMPLATES and template_id not in (ARROW, GAP, DASHED):
        raise ValueError('Unsupported kit template')
    raw_index = (ROOT / 'index.json').read_bytes()
    if sha256(raw_index).hexdigest() != CATALOG_SHA256:
        raise ValueError('Kit catalog hash mismatch')
    catalog = json.loads(raw_index)
    matches = [row for row in catalog['components'] if row['id'] == template_id]
    if len(matches) != 1:
        raise ValueError('Kit catalog identity mismatch')
    row = matches[0]
    path = (ROOT / row['file']).resolve()
    if not path.is_relative_to(ROOT.resolve()) or path.suffix != '.svg':
        raise ValueError('Invalid kit component path')
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Kit component hash mismatch')
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Unsafe SVG declaration')
    doc = ET.fromstring(raw)
    ids, refs = set(), []
    for el in doc.iter():
        if not isinstance(el.tag, str) or not el.tag.startswith(SVG) or el.tag[len(SVG):] not in _ALLOWED:
            raise ValueError('Unsupported kit SVG element')
        if el.get('id'):
            if el.get('id') in ids: raise ValueError('Duplicate kit SVG ID')
            ids.add(el.get('id'))
        for key, value in el.attrib.items():
            name = key.split('}')[-1]
            if name.lower().startswith('on') or name == 'style': raise ValueError('Unsafe kit SVG attribute')
            if name == 'href':
                if not value.startswith('#'): raise ValueError('External kit SVG reference')
                refs.append(value[1:])
            if 'url(' in value.lower():
                local = _URL.findall(value)
                if len(local) != value.lower().count('url('): raise ValueError('External kit SVG reference')
                refs.extend(local)
            if name in ('aria-labelledby', 'aria-describedby'): refs.extend(value.split())
    if not set(refs) <= ids: raise ValueError('Unresolved kit SVG reference')
    return row, raw, doc


def source_record(template_id):
    """Return the pinned source SVG and the allowed presentation adaptations."""
    row, raw, _ = _source(template_id)
    return {'id': template_id, 'file': row['file'], 'sha256': row['sha256'],
            'catalog_sha256': CATALOG_SHA256, 'svg': raw.decode('utf-8'),
            'edits': ['content-fit geometry', 'selected colors', 'remove specimen text',
                      'resize label backing for actual text', 'namespace local IDs']}


def dashed_route_style():
    """Read the saved dashed route; callers change endpoints, not dash geometry."""
    _, _, doc = _source(DASHED)
    line = _one(doc, lambda e: e.tag == SVG+'path' and e.get('stroke-dasharray') is not None)
    return {key: line.get(key) for key in ('stroke-dasharray', 'stroke-linecap', 'stroke-width')}


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Invalid geometry')
    return value


def _params(prefix, *colors):
    if not isinstance(prefix, str) or not _PREFIX.fullmatch(prefix): raise ValueError('Invalid SVG prefix')
    if any(not isinstance(c, str) or not _COLOR.fullmatch(c) for c in colors): raise ValueError('Expected opaque sRGB hex colors')


def _one(root, predicate):
    found = [e for e in root.iter() if predicate(e)]
    if len(found) != 1: raise ValueError('Kit template structure changed')
    return deepcopy(found[0])


def _set_box(el, x, y, w, h):
    if el.tag == SVG+'circle':
        if abs(w-h)>1e-8: raise ValueError('Circle width and height must match')
        el.attrib.update(cx=str(x+w/2), cy=str(y+h/2), r=str(w/2))
    else:
        el.attrib.update(x=str(x), y=str(y), width=str(w), height=str(h))


def document_frame(template_id, *, x, y, column_widths, row_heights, prefix,
                   fill='#ffffff', stroke='#000000'):
    """Adapt a pinned document table, preserving its original rule topology.

    The four admitted source specimens have fixed cell ownership. Column/row
    sizes may change; rules cannot be added, removed or supplied by the caller.
    Text and specimen glyphs are removed so consumers retain editable labels.
    """
    _params(prefix, fill, stroke)
    x,y=map(_num,(x,y))
    if template_id not in DOC_TEMPLATES: raise ValueError('Unsupported document template')
    row,_,doc=_source(template_id)
    specs={
        TITLE_BLOCK: ([930,1112,1198,1350],[680,734,792,850],
            'M930 734 H1350 M930 792 H1350 M1112 734 V850 M1198 734 V792',
            [('title',0,0,3,1),('drawing',0,1,1,1),('revision',1,1,1,1),('sheet',2,1,1,1),('figure',0,2,1,1),('scale',1,2,2,1)]),
        REVISION_BLOCK: ([1100,1150,1330],[100,135,169,205],
            'M1100 135 H1330 M1100 169 H1330 M1150 135 V205',
            [('heading',0,0,2,1),('revision_heading',0,1,1,1),('change_heading',1,1,1,1),('revision',0,2,1,1),('change',1,2,1,1)]),
        FIGURE_HEADING: ([100,525],[100,155],None,[('heading',0,0,1,1)]),
        LEGEND: ([100,540],[630,673,830],'M100 673 H540',[('heading',0,0,1,1),('body',0,1,1,1)])}
    xs,ys,expected,cells=specs[template_id]
    if not isinstance(column_widths,(tuple,list)) or not isinstance(row_heights,(tuple,list)) or len(column_widths)!=len(xs)-1 or len(row_heights)!=len(ys)-1:
        raise ValueError('Document table row/column shape mismatch')
    widths=[_num(v) for v in column_widths];heights=[_num(v) for v in row_heights]
    if any(v<=0 for v in widths+heights) or sum(widths)>8192 or sum(heights)>8192:
        raise ValueError('Invalid document table geometry')
    xx=[x];yy=[y]
    for value in widths:xx.append(xx[-1]+value)
    for value in heights:yy.append(yy[-1]+value)
    group=ET.Element(SVG+'g',{'id':prefix,'data-kit-template':template_id,'data-kit-sha256':row['sha256']})
    outer=_one(doc,lambda e:e.tag==SVG+'rect' and e.get('x')==str(xs[0]) and e.get('y')==str(ys[0]))
    _set_box(outer,x,y,sum(widths),sum(heights));outer.attrib.update(fill=fill,stroke=stroke)
    group.append(outer)
    if expected is not None:
        rules=_one(doc,lambda e:e.tag==SVG+'path' and e.get('d')==expected)
        # The source command sequence stays exact; each original rule contact
        # maps to its matching row/column boundary without stretching strokes.
        parts=re.findall(r'[MHV]|-?\d+(?:\.\d+)?',expected)
        mapped=[];i=0
        while i<len(parts):
            command=parts[i];mapped.append(command);i+=1
            axes=(xs,ys) if command=='M' else ((xs,) if command=='H' else (ys,))
            for axis in axes:
                value=float(parts[i]);i+=1
                target=xx if axis is xs else yy
                if value not in axis:raise ValueError('Document rule contact changed')
                mapped.append(str(target[axis.index(value)]))
        rules.set('d',' '.join(mapped));rules.set('stroke',stroke);group.append(rules)
    bounds=[{'id':key,'x':xx[c],'y':yy[r],'width':xx[c+cw]-xx[c],'height':yy[r+rh]-yy[r]} for key,c,r,cw,rh in cells]
    return {'svg':ET.tostring(group,encoding='unicode'),'cells':bounds,'template':template_id,
            'sha256':row['sha256'],'x':x,'y':y,'width':sum(widths),'height':sum(heights)}


def frame(template_id, *, x, y, width, height, fill, stroke, stroke_width, prefix, text_bounds=None):
    """Return a content-fit SVG group; text is drawn independently by the caller.

    ``text_bounds`` is absolute (x, y, width, height), including desired padding.
    Use a unique prefix for every placement in the enclosing SVG.
    """
    _params(prefix, fill, stroke)
    x,y,width,height,stroke_width = map(_num, (x,y,width,height,stroke_width))
    if width<=0 or height<=0 or stroke_width<=0: raise ValueError('Nonpositive geometry')
    row, _, doc = _source(template_id)
    if template_id not in TEMPLATES: raise ValueError('Unsupported frame template')
    group = ET.Element(SVG+'g', {'data-kit-template': template_id, 'data-kit-sha256': row['sha256']})
    if template_id == LABEL:
        box = _one(doc, lambda e: e.tag == SVG+'rect' and e.get('width')=='96' and e.get('height')=='30')
        _set_box(box,x,y,width,height);box.attrib.update(fill=fill,stroke=stroke,**{'stroke-width':str(stroke_width)})
        group.append(box)
        return ET.tostring(group,encoding='unicode')
    is_circle = template_id.startswith('palette-circle-')
    shape = _one(doc, lambda e: e.get('id') == ('shape-circle' if is_circle else 'shape-rectangle'))
    _set_box(shape,x,y,width,height)
    shape_id = prefix+'-shape'; shape.set('id',shape_id)
    defs=ET.SubElement(group,SVG+'defs');defs.append(shape)
    uses=[e for e in doc.iter(SVG+'use') if e.get('href') in ('#shape-circle','#shape-rectangle')]
    if len(uses) not in (2,3): raise ValueError('Kit shape layers changed')
    pattern = None
    if len(uses)==3:
        pattern = _one(doc,lambda e:e.tag==SVG+'pattern')
        old_id=pattern.get('id');new_id=prefix+'-pattern';pattern.set('id',new_id);defs.append(pattern)
    for i, original in enumerate(uses):
        layer=deepcopy(original);layer.set('href','#'+shape_id);layer.attrib.pop('mask',None)
        if i==0: layer.set('fill',fill)
        elif i==len(uses)-1: layer.attrib.update(fill='none',stroke=stroke,**{'stroke-width':str(stroke_width)})
        else: layer.set('fill',f'url(#{new_id})')
        group.append(layer)
    if pattern is not None and text_bounds is not None:
        if not isinstance(text_bounds,(tuple,list)) or len(text_bounds)!=4: raise ValueError('Invalid text bounds')
        bx,by,bw,bh=map(_num,text_bounds)
        if bw<=0 or bh<=0 or bx<x or by<y or bx+bw>x+width or by+bh>y+height:
            raise ValueError('Text backing outside frame')
        if is_circle and any(((px-(x+width/2))/(width/2))**2+((py-(y+height/2))/(height/2))**2>1+1e-9 for px in (bx,bx+bw) for py in (by,by+bh)):
            raise ValueError('Text backing outside circle')
        backing=_one(doc,lambda e:e.tag==SVG+'rect' and e.get('data-role')=='label-backing')
        _set_box(backing,bx,by,bw,bh);backing.set('id',prefix+'-backing');backing.set('fill',fill);group.append(backing)
    return ET.tostring(group,encoding='unicode')


def arrow_marker(prefix, colour):
    """Return a marker built from the palette's filled-triangle arrowhead."""
    _params(prefix, colour)
    row, _, doc=_source(ARROW)
    triangle=_one(doc,lambda e:e.tag==SVG+'path' and e.get('d')=='M250 125 L232 115 L232 135 Z')
    triangle.set('transform','translate(-250 -125)');triangle.set('fill',colour)
    marker=ET.Element(SVG+'marker',{'id':prefix+'-arrow','viewBox':'-18 -10 18 20','refX':'0','refY':'0',
        'markerWidth':'18','markerHeight':'20','markerUnits':'userSpaceOnUse','orient':'auto',
        'data-kit-template':ARROW,'data-kit-sha256':row['sha256']})
    marker.append(triangle)
    defs=ET.Element(SVG+'defs');defs.append(marker)
    return ET.tostring(defs,encoding='unicode')


def gap_marker(*, prefix, x, y, under_angle, over_angle, colour, stroke_width, background='#ffffff'):
    """Draw a source-derived gap at a nonjoining crossing of two routes.

    Angles are degrees from the positive x axis and must differ by 20 through
    160 degrees modulo 180. The caller supplies an actual interior crossing,
    a uniform opaque background and clearance for the marker. The source's
    15-unit under-route gap at 2.5-unit stroke scales uniformly with
    stroke_width. ``colour`` is the over-route color; the under-route is erased
    only inside the gap and is otherwise left untouched. The over-route redraw
    length grows with obliquity to cover the erasure.
    """
    _params(prefix, colour, background)
    x,y,under_angle,over_angle,stroke_width=map(_num,(x,y,under_angle,over_angle,stroke_width))
    if stroke_width<=0: raise ValueError('Nonpositive stroke width')
    angle=(over_angle-under_angle)%180
    if angle < 20-1e-7 or angle > 160+1e-7:
        raise ValueError('Crossing angle must be between 20 and 160 degrees modulo 180')
    row,_,doc=_source(GAP)
    crossing=_one(doc,lambda e:e.tag==SVG+'path' and e.get('class')=='crossing-line')
    interrupted=_one(doc,lambda e:e.tag==SVG+'path' and e.get('class')=='interrupted-line')
    if crossing.get('d')!='M55 125 H245' or interrupted.get('d')!='M150 95 V117.5 M150 132.5 V155':
        raise ValueError('Kit crossing geometry changed')
    scale=stroke_width/2.5
    group=ET.Element(SVG+'g',{'id':prefix+'-gap','data-kit-template':GAP,'data-kit-sha256':row['sha256'],
        'data-under-angle':str(under_angle),'data-over-angle':str(over_angle),
        'transform':f'translate({x} {y})'})
    # The erased interval is the source's 15-unit gap between its two segments.
    interrupted.set('d','M150 117.5 V132.5')
    interrupted.attrib.update(fill='none',stroke=background,**{'stroke-width':'4.5','stroke-linecap':'butt',
        'transform':f'rotate({under_angle-90}) scale({scale}) translate(-150 -125)'})
    group.append(interrupted)
    # Crop the original straight over-line around the crossing, extending it as
    # needed to repaint the oblique portion removed by the gap erasure.
    half=10/abs(math.sin(math.radians(angle)))
    crossing.set('d',f'M{150-half:.8f} 125 H{150+half:.8f}')
    crossing.attrib.update(fill='none',stroke=colour,**{'stroke-width':'2.5','stroke-linecap':'butt',
        'transform':f'rotate({over_angle}) scale({scale}) translate(-150 -125)'})
    group.append(crossing)
    return ET.tostring(group,encoding='unicode')
