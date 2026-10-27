from pathlib import Path
import json,html,textwrap,base64,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];OUT=R/'rendered'
def esc(x):return html.escape(str(x),quote=True)
INK='#142334';MUTED='#3f4e61';LINE='#34455b';PAPER='#f7f8fa'
THEMES={
 'gray':('#e4eaf0','#374452','dots'),
 'blue':('#d6e9ff','#124373','diagonal'),
 'amber':('#ffebc0','#6b3d04','horizontal'),
 'purple':('#eadcf7','#512575','cross'),
 'teal':('#d8f1ed','#10534d','diagonal'),
 'white':('#ffffff','#3f4e61','dots')}
class Drawing:
 def __init__(self,key,w,h,title,subtitle):
  self.key,self.w,self.h=key,w,h;self.nodes=[];self.edges=[];self.annotations=[];self.body=[];self.notes=[]
  self.body.append(f'<rect width="{w}" height="{h}" fill="{PAPER}"/>')
  self.body.append('<rect width="100%" height="132" fill="url(#paperShade)"/>')
  self.text(48,36,{'C':'C  /  MAINTENANCE','D':'D  /  DOMAIN INTERACTIONS','E':'E  /  PORT ALLOCATION'}[key[0]],12,MUTED,weight=600)
  self.text(48,80,title,34,INK,weight=600)
  subs={'A':'Tasks, handoffs and the waiting path','B':'Entry → elective scheduling → surgery','C':'VC distiller · Engine room 3','D':'Communication relationships and electrical connections','E':'Symmetric matrix · Four unique allocations'}
  if key[0] in ['A','B']:self.text(48,113,subs[key[0]],17,MUTED)
  self.boundaries={}
  facts=json.loads((R/'native'/(key+'.facts.json')).read_text())['elements']
  for e in facts:
   if e['kind']=='SuccessionAsUsage' and e.get('owner'):
    a=e['source'].get('qualified') or '';b=e['targets'][0].get('qualified') or ''
    if a=='Actions::Action::start':self.boundaries[b.rsplit('::',1)[-1]]='entry'
    if b=='Actions::Action::done':self.boundaries[a.rsplit('::',1)[-1]]='exit'
 def text(self,x,y,s,size=16,color=INK,anchor='start',weight=400,owner=None,mono=False):
  a=f' data-label-owner="{esc(owner)}"' if owner else ''
  f=' font-family="Plex Mono"' if mono else ''
  self.body.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}"{a}{f}>{esc(s)}</text>')
 def lines(self,x,y,lines,size=16,anchor='middle',owner=None,color=INK,weight=500):
  for i,s in enumerate(lines):self.text(x,y+i*(size+5),s,size,color,anchor,weight,owner)
 def rect(self,x,y,w,h,fill,stroke=None,rx=0,extra=''):
  self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+f' {extra}/>')
 def theme(self,id,kind):
  if self.key[0]=='A':
   roles=json.loads((R/'source/A-ledger.json').read_text())['nodes'];role=next(n['role'] for n in roles if n['id']==id)
   return {'Customer':'gray','FirstLineTeller':'blue','SecondLineTeller':'amber','Supervisor':'purple'}[role]
  if self.key[0]=='B':
   if id=='B07':return 'amber'
   nodes=json.loads((R/'source/B-ledger.json').read_text())['nodes'];g=next(n['group'] for n in nodes if n['id']==id)
   return 'purple' if g=='OR Department' else 'teal' if g=='Elective scheduling' else 'gray' if g=='Exit' else 'blue'
  return 'white' if self.key[0] in ['D','E'] else 'teal'
 def box(self,id,label,x,y,w,h,kind='ActionUsage',fill='#fff',native=None,small=None):
  node={'id':id,'label':label,'x':x,'y':y,'w':w,'h':h,'kind':kind,'native_id':native['id'] if native else None,'qualified':native['qualified'] if native else None};self.nodes.append(node)
  self.body.append(f'<g data-node="{esc(id)}" data-native-id="{esc(node["native_id"])}">')
  t=self.theme(id,kind);bg,accent,pattern=THEMES[t]
  texture=self.boundaries.get(id) if self.key[0] in ['A','B'] else 'projection' if self.key[0]=='E' and id=='ASMLCS_Control_if' else None
  node['texture_property']=texture
  if kind in ['DecisionNode','MergeNode']:
   path=f'M{x+w/2},{y} L{x+w},{y+h/2} L{x+w/2},{y+h} L{x},{y+h/2} Z'
   self.body.append(f'<path d="{path}" fill="{accent if kind=="MergeNode" else bg}" stroke="{LINE if kind=="MergeNode" else accent}" stroke-width="1.8"/>')
  elif kind=='TimedTask':
   self.rect(x,y,w,h,fill,rx=4);self.rect(x,y,w,h,'url(#barShade)',rx=4)
  else:
   radius=10 if kind=='ActionUsage' else 4
   self.rect(x,y,w,h,bg,accent,rx=radius,extra='filter="url(#lift)"')
   if kind=='ActionUsage':
    if texture:self.rect(x+1,y+1,w-2,h-2,'url(#'+texture+'Texture)',rx=radius)
    self.rect(x+1,y+1,w-2,h-2,'url(#nodeShade)',rx=radius)
   if self.key[0]=='E' and texture:self.rect(x+1,y+1,w-2,h-2,'url(#projectionTexture)',rx=radius)
   self.rect(x+1,y+9,4,h-18,accent,rx=2)
  if kind not in ['MergeNode','TimedTask']:
   if kind=='DecisionNode':
    ls=textwrap.wrap(label,18,break_long_words=False);self.lines(x+w/2,y+h/2-((len(ls)-1)*21)/2+5,ls,16,owner=id,color=INK,weight=600)
   elif self.key[0] in ['A','B']:
    fs=16.5;chars=int((w-42)/7.8);ls=textwrap.wrap(label,chars,break_long_words=False)
    self.text(x+21,y+21,id,11.5,accent,weight=400,owner=id,mono=True)
    # Fixed label inset; B compact cards carry up to two source lines (three when necessary).
    first=y+47 if self.key[0]=='A' else y+41
    self.lines(x+21,first,ls,fs,'start',id,INK,500)
   else:
    if self.key[0]=='E':
     alias=json.loads((R/'source/display-aliases.json').read_text())['E'][id]['display'];node['display_label']=alias
     self.text(x+22,y+31,alias,17,INK,weight=500,owner=id)
     self.text(x+22,y+57,label,12,MUTED,owner=id,mono=True)
    else:
     ls=textwrap.wrap(label,max(15,int((w-40)/8.5)),break_long_words=False)
     self.lines(x+22,y+h/2-((len(ls)-1)*22)/2+(0 if small else 6),ls,17,'start',id,INK,500)
     if small:self.text(x+22,y+h-12,small,12.5,MUTED,owner=id)
  self.body.append('</g>');return node
 def edge(self,id,source,target,points,label=None,native=None,directed=True,dash=False,lp=None,color=LINE):
  e={'id':id,'source':source,'target':target,'points':points,'label':label,'native_id':native['id'] if native else None,'directed':directed};self.edges.append(e)
  path='M'+' L'.join(f'{x},{y}' for x,y in points)
  self.body.append(f'<path data-edge="{esc(id)}" data-native-id="{esc(e["native_id"])}" d="{path}" fill="none" stroke="{color}" stroke-width="2.2"'+(' marker-end="url(#arrow)"' if directed else '')+(' stroke-dasharray="7 5"' if dash else '')+'/>')
  if label:
   x,y=lp or points[len(points)//2];self.text(x,y,label,15,'#263e57',weight=600,owner=id)
 def note(self,x,y,s):self.notes.append(s)
 def save(self):
  source={'C':'NASA · Figure B-10 · 1995','D':'NIST SP 1108 · Figure 3-1 · 2010','E':'Open-MBEE APE model · 288a863 · adapted October 2026'}[self.key[0]]
  self.body.append(f'<line x1="48" y1="{self.h-54}" x2="{self.w-48}" y2="{self.h-54}" stroke="#ccd3dd"/>')
  self.text(48,self.h-26,source,12,MUTED)
  self.text(self.w-48,self.h-26,'Model-derived · Review 03',12,MUTED,'end')
  fonts=''
  for name,file,weight in [('Plex Sans','IBMPlexSans-Regular.woff2',400),('Plex Sans','IBMPlexSans-Medium.woff2',500),('Plex Sans','IBMPlexSans-SemiBold.woff2',600),('Plex Mono','IBMPlexMono-Regular.woff2',400)]:
   data=base64.b64encode((R/'fonts'/file).read_bytes()).decode();fonts+=f'@font-face{{font-family:"{name}";src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:{weight};font-style:normal;}}'
  defs='<style>'+fonts+'text{font-kerning:normal;font-variant-numeric:tabular-nums;}</style><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#34455b"/></marker><linearGradient id="paperShade" x2="0" y2="1"><stop stop-color="#ffffff"/><stop offset="1" stop-color="#f7f8fa"/></linearGradient><linearGradient id="nodeShade" x2="0" y2="1"><stop stop-color="#ffffff" stop-opacity=".32"/><stop offset="1" stop-color="#22354e" stop-opacity=".035"/></linearGradient><linearGradient id="barShade" x2="0" y2="1"><stop stop-color="#ffffff" stop-opacity=".18"/><stop offset="1" stop-color="#000000" stop-opacity=".08"/></linearGradient><filter id="lift" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="2" stdDeviation="1.5" flood-color="#122333" flood-opacity=".09"/></filter>'
  defs+='<pattern id="entryTexture" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".85" fill="#142334" opacity=".2"/></pattern><pattern id="exitTexture" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M-2,2 L2,-2 M0,9 L9,0 M7,11 L11,7" stroke="#142334" stroke-width=".7" opacity=".22"/></pattern><pattern id="projectionTexture" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M-2,2 L2,-2 M0,10 L10,0 M8,12 L12,8" stroke="#142334" stroke-width=".65" opacity=".18"/></pattern>'
  # All fine print remains available to assistive reading and in the adjacent notes, not as canvas filler.
  description='Custom model-derived presentation. '+(' '.join(self.notes))
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc"><title id="title">{esc(self.key)}</title><desc id="desc">{esc(description)}</desc><defs>{defs}</defs><g font-family="Plex Sans" fill="{INK}">'+''.join(self.body)+'</g></svg>'
  (OUT/(self.key+'.svg')).write_text(svg)
  (OUT/(self.key+'.view.json')).write_text(json.dumps({'key':self.key,'width':self.w,'height':self.h,'nodes':self.nodes,'edges':self.edges,'annotations':self.annotations},indent=2)+'\n')
  (OUT/(self.key+'.presentation-notes.json')).write_text(json.dumps({'key':self.key,'removed_canvas_notes':self.notes,'source_footer':source,'classification':'Custom model-derived presentation; no formal graphical-conformance, execution or engineer acceptance claim'},indent=2)+'\n')
  # Geometry companion: labels and relations, not a promise to reproduce SVG fonts, textures or interchange SysML.
  mx=E.Element('mxfile',host='app.diagrams.net');di=E.SubElement(mx,'diagram',name=self.key);mo=E.SubElement(di,'mxGraphModel');rt=E.SubElement(mo,'root');E.SubElement(rt,'mxCell',id='0');E.SubElement(rt,'mxCell',id='1',parent='0')
  for n in self.nodes:
   style='rhombus;' if n['kind'] in ['DecisionNode','MergeNode'] else 'rounded=1;'
   c=E.SubElement(rt,'mxCell',id=n['id'],value=n.get('display_label',n['label'])+('\n'+n['label'] if n.get('display_label') else ''),style=style+'whiteSpace=wrap;html=0;fontFamily=IBM Plex Sans;fontSize=16;',vertex='1',parent='1',cseNativeId=str(n['native_id']),cseQualified=str(n['qualified']));E.SubElement(c,'mxGeometry',x=str(n['x']),y=str(n['y']),width=str(n['w']),height=str(n['h']),**{'as':'geometry'})
  for e in self.edges:
   c=E.SubElement(rt,'mxCell',id=e['id'],value=e['label'] or '',source=e['source'],target=e['target'],edge='1',parent='1',style='edgeStyle=orthogonalEdgeStyle;endArrow='+('block' if e['directed'] else 'none')+';',cseNativeId=str(e['native_id']));geo=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'});arr=E.SubElement(geo,'Array',**{'as':'points'})
   for x,y in e['points'][1:-1]:E.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  E.indent(mx);(OUT/(self.key+'.drawio')).write_text(E.tostring(mx,encoding='unicode'))
