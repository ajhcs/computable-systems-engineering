"""Render a bounded selected original-notation Activity reading; not native v2 conformance."""
from pathlib import Path
import json,xml.etree.ElementTree as E,base64,zlib
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference-extension';S='http://www.w3.org/2000/svg';E.register_namespace('',S)
def main():
 d=json.loads((P/'source/action-facts.json').read_text());nodes={n['kind']:n for n in d['nodes']}
 # Node identities and flow types come from the pinned original, not arbitrary presentation IDs.
 ids={k.split(':')[-1]:v['id'] for k,v in nodes.items()};cells=[]
 def add(kind,id=None,**kw):cells.append({'kind':kind,'source_id':id,**kw})
 add('initial',ids['InitialNode'],x=805,y=190,r=12)
 add('fork',ids['ForkNode'],x=505,y=275,w=610,h=10)
 add('send',ids['SendSignalAction'],x=425,y=405,w=310,h=100,label='SH_Take_exposure_Cmd')
 add('accept',ids['AcceptEventAction'],x=850,y=405,w=310,h=100,label='SH_Take_exposure_Ack')
 add('join',ids['JoinNode'],x=505,y=625,w=610,h=10)
 add('final',ids['ActivityFinalNode'],x=805,y=725,r=16)
 add('parameter',ids['ActivityParameterNode'],x=80,y=430,w=190,h=65,label='dit : Integer')
 pin='_18_0_4_baa02e2_1437598400072_462138_170530';add('pin',pin,x=413,y=448,w=12,h=14,label='p')
 paths={
 (ids['InitialNode'],ids['ForkNode']):'805,202 805,275',
 (ids['ForkNode'],ids['SendSignalAction']):'580,285 580,405',
 (ids['ForkNode'],ids['AcceptEventAction']):'1005,285 1005,405',
 (ids['SendSignalAction'],ids['JoinNode']):'580,505 580,625',
 (ids['AcceptEventAction'],ids['JoinNode']):'1005,505 1005,625',
 (ids['JoinNode'],ids['ActivityFinalNode']):'805,635 805,709',
 (ids['ActivityParameterNode'],pin):'270,455 413,455'}
 for e in d['edges']:add('edge',e['id'],source=e['source'],target=e['target'],flow_type=e['kind'],points=paths[(e['source'],e['target'])])
 add('annotation','_17_0_2_3_41e01aa_1382548607674_333485_74722',x=423,y=551,label='via PEAS2SHOut')
 svg=E.Element('{'+S+'}svg',{'width':'1280','height':'900','viewBox':'0 0 1280 900','role':'img','aria-labelledby':'title desc'})
 def el(tag,attrs,parent=svg,text=None):
  e=E.SubElement(parent,'{'+S+'}'+tag,{k:str(v) for k,v in attrs.items()});e.text=text;return e
 el('title',{'id':'title'},text='TMT Take SH Exposure: source-style Activity reading')
 el('desc',{'id':'desc'},text='Initial node forks into sending SH_Take_exposure_Cmd with dit Integer via PEAS2SHOut and accepting SH_Take_exposure_Ack. Both branches join before the final node. Six control flows and one input object flow retained. No Ack image field or executable behavior is asserted.')
 el('rect',{'width':1280,'height':900,'fill':'white'})
 defs=el('defs',{});marker=el('marker',{'id':'arrow','markerWidth':10,'markerHeight':10,'refX':9,'refY':5,'orient':'auto','markerUnits':'userSpaceOnUse'},defs);el('path',{'d':'M0 0 L10 5 L0 10','fill':'none','stroke':'#172F45','stroke-width':2},marker)
 def text(x,y,t,size=19,id=None):
  return el('text',{'x':x,'y':y,'font-size':size,'font-family':'Arial, sans-serif','fill':'#172F45',**({'data-source-id':id} if id else {})},text=t)
 text(52,48,'Take SH Exposure',28);text(52,81,'TMT APS | selected SysML 1.4 Activity reading | original source semantics',18)
 el('line',{'x1':52,'y1':105,'x2':1228,'y2':105,'stroke':'#4F6678'})
 # Lines behind nodes, with source endpoint attributes.
 for c in cells:
  if c['kind']=='edge':el('polyline',{'points':c['points'],'fill':'none','stroke':'#172F45','stroke-width':2,'marker-end':'url(#arrow)','data-source-id':c['source_id'],'data-source':c['source'],'data-target':c['target'],'data-flow-type':c['flow_type']})
 for c in cells:
  k=c['kind'];attrs={'data-source-id':c['source_id'],'data-kind':k,'stroke':'#172F45','stroke-width':2,'fill':'#F0F4F7'}
  if k in ['fork','join','parameter','pin']:
   el('rect',attrs|{'x':c['x'],'y':c['y'],'width':c['w'],'height':c['h'],'fill':'#172F45' if k in ['fork','join'] else '#F0F4F7'})
  elif k in ['initial','final']:
   el('circle',attrs|{'cx':c['x'],'cy':c['y'],'r':c['r'],'fill':'#172F45' if k=='initial' else 'white'})
   if k=='final':el('circle',{'cx':c['x'],'cy':c['y'],'r':10,'fill':'#172F45','data-source-id':c['source_id']})
  elif k in ['send','accept']:
   x,y,w,h=c['x'],c['y'],c['w'],c['h'];p=[(x,y),(x+w-22,y),(x+w,y+h/2),(x+w-22,y+h),(x,y+h)] if k=='send' else [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x+22,y+h/2)]
   el('polygon',attrs|{'points':' '.join(f'{a},{b}' for a,b in p)})
   text(x+35,y+58,c['label'],18,c['source_id'])
  if k=='parameter':text(c['x']+18,c['y']+39,c['label'],20,c['source_id'])
  if k=='pin':text(c['x']-8,c['y']-10,c['label'],18,c['source_id'])
  if k=='annotation':text(c['x'],c['y'],c['label'],18,c['source_id'])
 text(52,807,'Reading: fork starts send and accept branches; join requires both. dit feeds send argument p.',18)
 text(52,839,'Source Ack has no image field. No timeout, unit, receive port or execution result is invented.',18)
 text(52,870,'Redrawn selected v1 notation; paired v2 is a scoped transcription. See source ledger and notices.',16)
 (P/'rendered/05-tmt-exposure.svg').write_bytes(E.tostring(svg,encoding='utf-8',xml_declaration=True))
 (P/'rendered/05-tmt-exposure.geometry.json').write_text(json.dumps(cells,indent=2)+'\n')
 mx=E.Element('mxfile',{'host':'app.diagrams.net','agent':'source-grounded-reference','version':'24.7.17'});diagram=E.SubElement(mx,'diagram',{'name':'Take SH Exposure - selected source-style reading','id':'tmt-exposure'});gm=E.SubElement(diagram,'mxGraphModel',{'pageWidth':'1280','pageHeight':'900','background':'#FFFFFF'});rt=E.SubElement(gm,'root');E.SubElement(rt,'mxCell',{'id':'0'});E.SubElement(rt,'mxCell',{'id':'1','parent':'0'})
 def stencil(kind):
  p=[(0,0),(93,0),(100,50),(93,100),(0,100)] if kind=='send' else [(0,0),(100,0),(100,100),(0,100),(7,50)]
  s=E.Element('shape',{'w':'100','h':'100','aspect':'variable','strokewidth':'inherit'});fg=E.SubElement(s,'foreground');path=E.SubElement(fg,'path');E.SubElement(path,'move',{'x':str(p[0][0]),'y':str(p[0][1])})
  for x,y in p[1:]:E.SubElement(path,'line',{'x':str(x),'y':str(y)})
  E.SubElement(path,'close');E.SubElement(fg,'fillstroke')
  return 'stencil('+base64.b64encode(zlib.compress(E.tostring(s),9)[2:-4]).decode()+')'
 for c in cells:
  if c['kind']=='edge':continue
  k=c['kind'];style='strokeColor=#172F45;fillColor=#F0F4F7;fontColor=#172F45;fontSize=18;whiteSpace=wrap;html=0;'
  if k in ['send','accept']:style+='shape='+stencil(k)+';'
  elif k=='final':
   glyph='<shape w="100" h="100" aspect="fixed" strokewidth="inherit"><foreground><fillcolor color="#FFFFFF"/><ellipse x="0" y="0" w="100" h="100"/><fillstroke/><fillcolor color="#172F45"/><ellipse x="18.75" y="18.75" w="62.5" h="62.5"/><fillstroke/></foreground></shape>'
   style+='shape=stencil('+base64.b64encode(zlib.compress(glyph.encode(),9)[2:-4]).decode()+');'
  elif k=='initial':style+='shape=ellipse;fillColor=#172F45;'
  elif k in ['fork','join']:style+='fillColor=#172F45;'
  elif k=='pin':style+='verticalLabelPosition=top;verticalAlign=bottom;labelPosition=left;align=right;'
  elif k=='annotation':style+='text;strokeColor=none;fillColor=none;align=left;'
  cell=E.SubElement(rt,'mxCell',{'id':c['source_id'],'sourceId':c['source_id'],'value':c.get('label',''),'vertex':'1','parent':'1','style':style})
  x,y,w,h=(c['x']-c['r'],c['y']-c['r'],2*c['r'],2*c['r']) if k in ['initial','final'] else (c['x'],c['y'],c.get('w',300),c.get('h',30))
  E.SubElement(cell,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})
 for c in cells:
  if c['kind']!='edge':continue
  cell=E.SubElement(rt,'mxCell',{'id':c['source_id'],'sourceId':c['source_id'],'flowType':c['flow_type'],'edge':'1','parent':'1','source':c['source'],'target':c['target'],'style':'edgeStyle=none;endArrow=open;endFill=0;strokeColor=#172F45;'})
  E.SubElement(cell,'mxGeometry',{'relative':'1','as':'geometry'})
 (P/'rendered/05-tmt-exposure.drawio').write_bytes(E.tostring(mx,encoding='utf-8',xml_declaration=True));print('Source-linked SVG/draw.io generated.')
if __name__=='__main__':main()
