"""Selected original SysML1.4 sequence reading: message order, no derived timing."""
from pathlib import Path
import json,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference-extension';S='http://www.w3.org/2000/svg';E.register_namespace('',S)
def main():
 d=json.loads((P/'source/sequence-projection.json').read_text());lines=d['lifelines'];msgs=d['messages'];svg=E.Element('{'+S+'}svg',{'width':'1280','height':'900','viewBox':'0 0 1280 900','role':'img','aria-labelledby':'title desc'})
 def el(tag,a,txt=None,parent=svg):e=E.SubElement(parent,'{'+S+'}'+tag,{k:str(v) for k,v in a.items()});e.text=txt;return e
 def text(x,y,t,size=19,id=None):return el('text',{'x':x,'y':y,'font-family':'Arial, sans-serif','font-size':size,'fill':'#172F45',**({'data-source-id':id} if id else {})},t)
 el('title',{'id':'title'},'TMT maintenance analysis: selected message order')
 el('desc',{'id':'desc'},'analysisDriver sends asynchronous Abort, Maintenance Alignment and Abort signals to peas in that order. Three messages and six event endpoints retained. Source duration constraints are retained in XML but not transcribed into timed assertions.')
 el('rect',{'width':1280,'height':900,'fill':'white'})
 defs=el('defs',{});m=el('marker',{'id':'async','markerWidth':12,'markerHeight':12,'refX':11,'refY':6,'orient':'auto','markerUnits':'userSpaceOnUse'},parent=defs);el('path',{'d':'M1 1 L11 6 L1 11','stroke':'#172F45','stroke-width':2,'fill':'none'},parent=m)
 text(52,48,'Maintenance analysis | selected signal exchange order',28);text(52,81,'TMT APS | simplified SysML1.4 Sequence reading | timing not transcribed',18);el('line',{'x1':52,'x2':1228,'y1':105,'y2':105,'stroke':'#4F6678'})
 cells=[]
 for line,x in zip(lines,[330,960]):
  cells.append({'kind':'lifeline','source_id':line['id'],'represents':line['represents'],'name':line['name'],'x':x,'header_y':180,'line_top':260,'line_bottom':690})
  el('rect',{'x':x-140,'y':180,'width':280,'height':80,'fill':'#F0F4F7','stroke':'#172F45','stroke-width':2,'data-source-id':line['id']})
  text(x-100,228,line['name'],22,line['represents']);el('line',{'x1':x,'x2':x,'y1':260,'y2':690,'stroke':'#4F6678','stroke-dasharray':'9 7','data-source-id':line['id']})
 for n,(msg,y) in enumerate(zip(msgs,[345,455,565])):
  cells.append({'kind':'message','source_id':msg['id'],'sort':msg['sort'],'signal':msg['signal'],'send_event':msg['send_event'],'receive_event':msg['receive_event'],'source':lines[0]['id'],'target':lines[1]['id'],'order':n,'y':y})
  el('line',{'x1':330,'x2':960,'y1':y,'y2':y,'stroke':'#172F45','stroke-width':2,'marker-end':'url(#async)','data-source-id':msg['id'],'data-source':lines[0]['id'],'data-target':lines[1]['id'],'data-send-event':msg['send_event'],'data-receive-event':msg['receive_event'],'data-sort':msg['sort']})
  text(485,y-16,msg['signal'],21,msg['signature_id'])
  for event,x in [(msg['send_event'],330),(msg['receive_event'],960)]:el('circle',{'cx':x,'cy':y,'r':0,'data-source-id':event})
 text(52,745,'Reading: analysisDriver sends Abort, then Maintenance Alignment, then Abort to peas.',19)
 text(52,780,'Source message sort: asynchSignal. Event order is local to each lifeline.',18)
 text(52,815,'Duration records retained in source XML; 60s/2000s are not invented exact timers here.',18)
 text(52,850,'Selected v2 message-order transcription; full timed scenario and simulation remain unverified.',17)
 (P/'rendered/06-tmt-sequence-order.svg').write_bytes(E.tostring(svg,encoding='utf-8',xml_declaration=True));(P/'rendered/06-tmt-sequence-order.geometry.json').write_text(json.dumps(cells,indent=2)+'\n')
 mx=E.Element('mxfile',{'host':'app.diagrams.net','agent':'source-grounded-reference','version':'24.7.17'});di=E.SubElement(mx,'diagram',{'id':'tmt-sequence-order','name':'Selected maintenance message order'});gm=E.SubElement(di,'mxGraphModel',{'pageWidth':'1280','pageHeight':'900'});rt=E.SubElement(gm,'root');E.SubElement(rt,'mxCell',{'id':'0'});E.SubElement(rt,'mxCell',{'id':'1','parent':'0'})
 for c in cells:
  if c['kind']=='lifeline':
   ce=E.SubElement(rt,'mxCell',{'id':c['source_id'],'sourceId':c['source_id'],'value':c['name'],'vertex':'1','parent':'1','style':'shape=umlLifeline;perimeter=lifelinePerimeter;participant=rectangle;size=80;fillColor=#F0F4F7;strokeColor=#172F45;fontSize=22;html=0;'});E.SubElement(ce,'mxGeometry',{'x':str(c['x']-140),'y':'180','width':'280','height':'510','as':'geometry'})
  else:
   ce=E.SubElement(rt,'mxCell',{'id':c['source_id'],'sourceId':c['source_id'],'value':c['signal'],'edge':'1','parent':'1','source':c['source'],'target':c['target'],'sendEvent':c['send_event'],'receiveEvent':c['receive_event'],'messageSort':c['sort'],'style':'edgeStyle=none;endArrow=open;endFill=0;strokeColor=#172F45;fontSize=21;exitX=0.5;entryX=0.5;exitY='+str((c['y']-180)/510)+';entryY='+str((c['y']-180)/510)+';'});E.SubElement(ce,'mxGeometry',{'relative':'1','as':'geometry'})
 (P/'rendered/06-tmt-sequence-order.drawio').write_bytes(E.tostring(mx,encoding='utf-8',xml_declaration=True));print('Selected source-style sequence SVG/draw.io generated.')
if __name__=='__main__':main()
