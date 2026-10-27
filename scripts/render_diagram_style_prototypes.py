"""Matched presentation-only prototypes for accepted source-ID-bearing diagrams."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E,re
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference';O=R/'examples/diagram-style-prototypes'
STYLES={
'technical-ledger':{'name':'Technical Ledger','canvas':'#FAFAF7','ink':'#171918','line':'#434A47','surface':'#F0F1EB','nested':'#F7F7F2','secondary':'#434A47','note':'#8B3D16','title_font':'DejaVu Sans Mono, monospace'},
'instrument-record':{'name':'Instrument Record','canvas':'#121816','ink':'#F0F4EE','line':'#A8B5AA','surface':'#1C2520','nested':'#273329','secondary':'#CBD6CE','note':'#F4C178','title_font':'DejaVu Sans Mono, monospace'},
'quiet-precision':{'name':'Quiet Precision','canvas':'#FFFFFF','ink':'#171717','line':'#616161','surface':'#F5F5F5','nested':'#FAFAFA','secondary':'#555555','note':'#265DA8','title_font':'Arial, sans-serif'},
'research-folio':{'name':'Research Folio','canvas':'#F8F5ED','ink':'#24221E','line':'#665F52','surface':'#EEEBDD','nested':'#F4F1E7','secondary':'#665F52','note':'#A34D2E','title_font':'Times New Roman, serif'},
'engineering-standard':{'name':'Engineering Standard','canvas':'#FFFFFF','ink':'#172F45','line':'#4F6678','surface':'#F0F4F7','nested':'#F7F9FB','secondary':'#4F6678','note':'#8A3D10','title_font':'Arial, sans-serif'}}
FILES=['01-tmt-maintenance','02-tmt-timing','03-ape-composition','04-ape-optical']
NS={'s':'http://www.w3.org/2000/svg'};E.register_namespace('',NS['s'])
def recolors(t):
 return {'#ffffff':t['canvas'],'#FFFFFF':t['canvas'],'white':t['canvas'],'#eef4f8':t['surface'],'#f4f7fa':t['nested'],'#365268':t['line'],'#203346':t['ink'],'#506273':t['secondary'],'#cad5df':t['line'],'#9dabb5':t['line'],'#8b4b18':t['note'],'#172F45':t['ink'],'#4F6678':t['line'],'#F0F4F7':t['surface']}
COLOR_PROPERTIES={'fillColor','strokeColor','fontColor','gradientColor','labelBackgroundColor','labelBorderColor','swimlaneFillColor','separatorColor','imageBackground','imageBorder'}
def recolor_drawio_style(style,mapping):
 # Preserve named styles, separators, order, repeated keys and every non-color field exactly.
 fields=[]
 for field in style.split(';'):
  key,separator,value=field.partition('=')
  fields.append(key+separator+mapping.get(value,value) if separator and key in COLOR_PROPERTIES else field)
 return ';'.join(fields)
def noncolor_drawio_style(style):
 return [field for field in style.split(';') if field.partition('=')[0] not in COLOR_PROPERTIES]

def svg_semantics(root):
 def visit(e):
  attrs={k:v for k,v in e.attrib.items() if k not in ['fill','stroke','stroke-width','font-family','font-weight','font-size','class'] and k not in ['data-treatment']}
  return [e.tag,attrs,e.text or '',[visit(c) for c in e if c.attrib.get('data-presentation-only')!='true']]
 return visit(root)
def drawio_semantics(root):
 def visit(e):
  notation=noncolor_drawio_style(e.attrib.get('style',''))
  return [e.tag,{k:v for k,v in e.attrib.items() if k not in ['style','background','agent','modified']},notation,e.text or '',[visit(c) for c in e]]
 return visit(root)
def render(style_id,t,stem,print_variant=False):
 target=O/(style_id+('-print' if print_variant else ''));target.mkdir(parents=True,exist_ok=True)
 original=E.parse(P/'rendered'/(stem+'.svg')).getroot();before=svg_semantics(original);mapping=recolors(t)
 for e in original.iter():
  for k in ['fill','stroke']:
   if e.attrib.get(k) in mapping:e.set(k,mapping[e.attrib[k]])
  if e.tag.endswith('text') and e.attrib.get('y')=='48':e.set('font-family',t['title_font'])
  if e.tag.endswith('polyline') and e.attrib.get('points')=='52,104 1228,104' and style_id in ['technical-ledger','instrument-record']:e.set('stroke-width','3')
 desc=original.find('s:desc',NS);desc.text=desc.text or ''
 # Keep the existing equivalent text/meaning untouched; rendering provenance is outside the formal content.
 note=E.SubElement(original,'{'+NS['s']+'}text',{'x':'52','y':'889','font-size':'12','font-family':'DejaVu Sans Mono, monospace','fill':t['secondary'],'data-presentation-only':'true'})
 note.text=t['name']+(' / designed light print variant' if print_variant else '')+' | presentation prototype; identical source semantics and coordinates'
 assert svg_semantics(original)==before,'SVG semantics or geometry changed'
 (target/(stem+'.svg')).write_bytes(E.tostring(original,encoding='utf-8',xml_declaration=True))
 dx=E.parse(P/'rendered'/(stem+'.drawio')).getroot();dbefore=drawio_semantics(dx)
 for e in dx.iter():
  if 'style' in e.attrib:
   e.set('style',recolor_drawio_style(e.attrib['style'],mapping))
  if e.tag=='mxGraphModel':e.set('background',t['canvas'])
 assert drawio_semantics(dx)==dbefore,'Editable meaning or geometry changed'
 (target/(stem+'.drawio')).write_bytes(E.tostring(dx,encoding='utf-8',xml_declaration=True))
 (target/(stem+'.geometry.json')).write_bytes((P/'rendered'/(stem+'.geometry.json')).read_bytes())
 return {'treatment':style_id,'print_variant':print_variant,'file':str((target/(stem+'.svg')).relative_to(O)),'source_svg_sha256':hashlib.sha256((P/'rendered'/(stem+'.svg')).read_bytes()).hexdigest(),'geometry_sha256':hashlib.sha256((target/(stem+'.geometry.json')).read_bytes()).hexdigest(),'source_geometry_byte_identical':True,'svg_semantics_equal':True,'drawio_semantics_equal':True}
def contrast(a,b):
 def l(c):
  rgb=[int(c[i:i+2],16)/255 for i in [1,3,5]];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb];return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
 x,y=sorted([l(a),l(b)]);return (y+.05)/(x+.05)
def main():
 global P
 O.mkdir(exist_ok=True);results=[];checks=[]
 for sid,t in STYLES.items():
  for bg in [t['canvas'],t['surface'],t['nested']]:
   for role in ['ink','secondary','note','line']:
    c=contrast(t[role],bg);threshold=3 if role=='line' else 4.5
    assert c>=threshold,(sid,role,bg,c)
    checks.append({'treatment':sid,'role':role,'background':bg,'ratio':round(c,3),'threshold':threshold})
  results += [render(sid,t,stem) for stem in FILES]
 # A dark treatment must provide a designed light print counterpart, not inversion.
 results += [render('instrument-record',STYLES['technical-ledger']|{'name':'Instrument Record'},stem,True) for stem in FILES]
 P=R/'examples/engineering-reference-extension'
 for sid in ['technical-ledger','engineering-standard']:
  results += [render(sid,STYLES[sid],stem) for stem in ['05-tmt-exposure']]
 P=R/'examples/engineering-reference'
 (O/'tokens.json').write_text(json.dumps(STYLES,indent=2)+'\n')
 (O/'semantic-validation.json').write_text(json.dumps({'matched_views':20,'source_extension_views':2,'light_print_variants':4,'checks':results,'contrast':checks,'scope':'Fixed-geometry presentation prototypes. No human reading superiority, native editor round-trip or v2 graphical conformance asserted.'},indent=2)+'\n')
 print(json.dumps({'views':len(results),'contrast_checks':len(checks),'semantic_primitive_equality':'pass','geometry_byte_identity':'pass'}))
if __name__=='__main__':main()
