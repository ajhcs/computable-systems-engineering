"""Draw selected reviewed derivative facts; new layout, not source-figure copies."""
from pathlib import Path
import json,html,xml.etree.ElementTree as E,hashlib
R=Path(__file__).resolve().parents[1];P=R/'examples/engineering-reference';D=json.loads((P/'source/view-facts.json').read_text())
W,H=1280,900
class View:
 def __init__(self,name,title,subtitle):
  self.name=name;self.cells=[];self.svg=[]
  self.text(52,48,title,28,bold=True)
  self.text(52,82,subtitle,17,color='#506273')
  self.line([(52,104),(1228,104)],color='#cad5df')
 def text(self,x,y,lines,size=18,bold=False,color='#203346',sid=None,anchor='start'):
  if isinstance(lines,str):lines=[lines]
  for j,line in enumerate(lines):
   self.svg.append('<text x="'+str(x)+'" y="'+str(y+j*(size+7))+'" font-size="'+str(size)+'" fill="'+color+'" font-weight="'+('600' if bold else '400')+'" text-anchor="'+anchor+'" data-source-id="'+html.escape(sid or '',quote=True)+'">'+html.escape(line)+'</text>')
  self.cells.append({'kind':'text','x':x,'y':y-size,'w':max(len(s) for s in lines)*size*.6,'h':len(lines)*(size+7),'value':'\n'.join(lines),'source_id':sid,'size':size,'bold':bold,'color':color,'anchor':anchor})
 def box(self,key,x,y,w,h,title,details=(),sid=None,fill='#eef4f8',rounding=0,stereo=None):
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rounding}" fill="{fill}" stroke="#365268" stroke-width="1.5" data-source-id="{html.escape(sid or "",quote=True)}"/>')
  ty=y+28
  if stereo:self.text(x+w/2,ty,stereo,15,anchor='middle');ty+=24
  self.text(x+w/2,ty,title,18,bold=True,anchor='middle',sid=sid)
  if details:
   sep=ty+13;self.line([(x,sep),(x+w,sep)],color='#9dabb5')
   self.text(x+16,sep+30,list(details),17,sid=sid)
  self.cells.append({'kind':'box','id':key,'x':x,'y':y,'w':w,'h':h,'value':title,'source_id':sid,'fill':fill,'rounding':rounding,'stereo':stereo})
 def line(self,pts,label=None,lx=None,ly=None,arrow=False,dash=False,color='#365268',sid=None,diamond=False):
  attr=' stroke-dasharray="7 5"' if dash else ''
  attr+=' marker-end="url(#arrow)"' if arrow else ''
  points=' '.join(str(x)+','+str(y) for x,y in pts)
  self.svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.7"{attr} data-source-id="{html.escape(sid or "",quote=True)}"/>')
  if diamond:
   x,y=pts[0];self.svg.append(f'<polygon points="{x},{y} {x-5},{y+9} {x},{y+18} {x+5},{y+9}" fill="{color}"/>')
  if label:self.text(lx,ly,label,16,sid=sid)
  self.cells.append({'kind':'edge','points':pts,'value':label or '', 'source_id':sid,'arrow':arrow,'dash':dash,'diamond':diamond})
 def dot(self,key,x,y,sid,final=False):
  if final:self.svg.append(f'<circle cx="{x}" cy="{y}" r="11" fill="white" stroke="#203346" stroke-width="1.5"/>')
  self.svg.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#203346" data-source-id="{sid}"/>')
  self.cells.append({'kind':'dot','id':key,'x':x-11,'y':y-11,'w':22,'h':22,'value':'','source_id':sid,'final':final})
 def port(self,key,x,y,label,sid):
  self.svg.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" fill="white" stroke="#365268" stroke-width="1.5" data-source-id="{sid}"/>')
  self.cells.append({'kind':'port','id':key,'x':x-7,'y':y-7,'w':14,'h':14,'value':label,'source_id':sid})
 def footer(self,lines):
  self.line([(52,789),(1228,789)],color='#cad5df');self.text(52,819,lines,16,color='#506273')
 def save(self):
  svg='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="900" viewBox="0 0 1280 900"><title>'+html.escape(self.name)+'</title><desc>New model-derived selected view. Original notation/version, trace IDs and omissions are documented in the matched explanation. Not a native Cameo export.</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="#365268"/></marker></defs><rect width="1280" height="900" fill="#ffffff"/><g font-family="Arial, sans-serif">'+''.join(self.svg)+'</g></svg>'
  (P/'rendered'/(self.name+'.svg')).write_text(svg)
  # Each presentation primitive remains independently editable and carries source IDs.
  file=E.Element('mxfile',{'host':'app.diagrams.net','modified':'2026-10-01','agent':'source-grounded-view','version':'24.7.17'})
  diagram=E.SubElement(file,'diagram',{'name':self.name,'id':self.name})
  gm=E.SubElement(diagram,'mxGraphModel',{'page':'1','pageWidth':'1280','pageHeight':'900'});root=E.SubElement(gm,'root')
  E.SubElement(root,'mxCell',{'id':'0'});E.SubElement(root,'mxCell',{'id':'1','parent':'0'})
  for j,c in enumerate(self.cells):
   common={'id':f'c{j}','parent':'1','value':c['value'],'source_id':c.get('source_id') or ''}
   if c['kind']=='edge':
    common['original_label']=common['value'];common['value']=''
    cell=E.SubElement(root,'mxCell',dict(common,edge='1',style='endArrow='+('open' if c['arrow'] else 'none')+';startArrow='+('diamond' if c['diamond'] else 'none')+';startFill=1;dashed='+str(int(c['dash']))+';strokeColor=#365268;'))
    geo=E.SubElement(cell,'mxGeometry',{'relative':'1','as':'geometry'})
    pts=c['points'];E.SubElement(geo,'mxPoint',{'x':str(pts[0][0]),'y':str(pts[0][1]),'as':'sourcePoint'});E.SubElement(geo,'mxPoint',{'x':str(pts[-1][0]),'y':str(pts[-1][1]),'as':'targetPoint'})
    arr=E.SubElement(geo,'Array',{'as':'points'})
    for x,y in pts[1:-1]:E.SubElement(arr,'mxPoint',{'x':str(x),'y':str(y)})
   else:
    kind=c['kind']
    if kind=='text':
     style=f'text;html=0;strokeColor=none;fillColor=none;fontColor={c["color"]};fontSize={c["size"]};fontStyle={int(c["bold"])};align='+('center' if c['anchor']=='middle' else 'left')+';verticalAlign=top;'
     cx=c['x']-c['w']/2 if c['anchor']=='middle' else c['x']
    elif kind=='dot':style='ellipse;fillColor=#203346;strokeColor=#203346;'+('shape=doubleEllipse;' if c['final'] else '');cx=c['x']
    elif kind=='port':style='shape=rectangle;fillColor=#ffffff;strokeColor=#365268;noLabel=1;';cx=c['x']
    else:
     style='shape=rectangle;rounded='+str(int(bool(c['rounding'])))+';fillColor='+c['fill']+';strokeColor=#365268;noLabel=1;';cx=c['x']
    cell=E.SubElement(root,'mxCell',dict(common,vertex='1',style=style))
    E.SubElement(cell,'mxGeometry',{'x':str(cx),'y':str(c['y']),'width':str(c['w']),'height':str(c['h']),'as':'geometry'})
  (P/'rendered'/(self.name+'.drawio')).write_bytes(E.tostring(file,encoding='utf-8',xml_declaration=True))
  (P/'rendered'/(self.name+'.geometry.json')).write_text(json.dumps(self.cells,indent=2)+'\n')

def render():
 s=D['slices']['tmt-maintenance'];states={r['name']:r['id'] for r in s['states']}
 tr={(t['source_name'],t['target_name'],t['signals'][0]['name'] if t['signals'] else None):t for t in s['transitions']}
 edge=lambda a,b,sig:tr[(a,b,sig)]['id']
 v=View('01-tmt-maintenance','TMT APS | Maintenance alignment','Model-derived simplified SysML v1 state-machine view | original: SysML 1.4, February 2017')
 v.box('frame',52,132,1176,610,'PEAS lifecycle - selected maintenance scope',fill='#ffffff')
 v.box('composite',650,200,530,524,'Maintenance Alignment',sid=states['Maintenance Alignment'],fill='#f4f7fa',rounding=16)
 v.dot('initial',262,210,'_17_0_2_3_41e01aa_1383540424694_865498_58143')
 v.box('initializing',120,246,284,92,'Initializing',['do / InitializePEAS'],sid=states['Initializing'],rounding=12)
 v.line([(262,218),(262,246)],arrow=True,sid=edge('uml:Pseudostate','Initializing',None))
 v.box('standby',120,404,284,218,'StandBy',sid=states['StandBy'],rounding=12)
 v.line([(262,338),(262,404)],'InitComplete /',285,377,arrow=True,sid=edge('Initializing','StandBy','InitComplete'))
 v.dot('inner-initial',910,253,'_18_0_4_baa02e2_1437066432308_831145_152441')
 v.box('correction',687,304,455,100,'Correcting Rigid Body and Segment Figure',['do / Rigid Body and Segment Figure correction'],sid=states['Correcting Rigid Body and Segment Figure'],rounding=12)
 v.line([(910,261),(910,304)],'/ initTimer',932,287,arrow=True,sid=edge('uml:Pseudostate','Correcting Rigid Body and Segment Figure',None))
 v.box('broad',687,463,455,92,'Broad Band Phasing 1um',['do / Broad Band Phasing 1um'],sid=states['Broad Band Phasing 1um'],rounding=12)
 v.line([(910,404),(910,463)],'Finished / diffTime',932,439,arrow=True,sid=edge('Correcting Rigid Body and Segment Figure','Broad Band Phasing 1um','Finished'))
 v.box('narrow',687,612,455,92,'Narrow Band Phasing',['do / Narrow Band Phasing'],sid=states['Narrow Band Phasing'],rounding=12)
 v.line([(910,555),(910,612)],'Finished / diffTime',932,590,arrow=True,sid=edge('Broad Band Phasing 1um','Narrow Band Phasing','Finished'))
 v.line([(404,430),(650,430)],'Maintenance Alignment',424,418,arrow=True,sid=edge('StandBy','Maintenance Alignment','Maintenance Alignment'))
 v.line([(650,508),(404,508)],'Abort',493,494,arrow=True,sid=edge('Maintenance Alignment','StandBy','Abort'))
 v.line([(687,651),(524,651),(524,580),(404,580)],'Finished / FinalDiffTime',418,681,arrow=True,sid=edge('Narrow Band Phasing','StandBy','Finished'))
 v.dot('final',262,684,'_17_0_2_3_41e01aa_1383541815273_542603_65409',final=True)
 v.line([(262,622),(262,673)],'Finished',285,660,arrow=True,sid=edge('StandBy','uml:FinalState','Finished'))
 v.footer(['Abort exits the composite state; Finished on a phasing state advances that state. They are different events.',
           'Original Figure 2 / section 2.3 linked in the reference. New layout; actions retained as opaque specifications.',
           'Herzig et al. (2017), JPL/Caltech, TMT and No Magic. Native simulation and graphical conformance untested.'])
 v.save()

 timing=D['slices']['tmt-timing'];ids=timing['source_ids']
 v=View('02-tmt-timing','TMT APS | From requirement to a computable timing constraint','Selected source evidence: original 2017 Figures 7-8 + February native model | separate meanings retained')
 v.box('english',52,143,548,228,'REQ-2-APS-0017',['APS supports on-axis alignment in less than 30 minutes,','at a single elevation angle, when all optics are within','the alignment maintenance specifications.','','Full engineering conditions are retained as prose.'],sid=ids['requirement'],fill='#f4f7fa',stereo='source requirement - English paraphrase')
 v.box('formalization',675,143,553,228,'Maintenance Alignment Maximum Time',['maintenanceAlignmentTimeLimit: default 1800.0 s','','Original class default: February 2017.','A timing predicate alone does not verify the optics','or elevation-angle conditions.'],sid='_18_0_5_c0402fd_1464026223074_50206_149810',fill='#f4f7fa',stereo='original modeled formalization')
 v.text(52,415,['Source discrepancy: English uses < 30 min; mathematical model uses <= 1800 s.','At exactly 1800 s the source constraint passes, while the literal English timing condition does not.'],20,bold=True,color='#8b4b18')
 v.box('peas',52,511,360,152,'peas : PEAS',['tFinal : Real [seconds]','Maintenance effect:','tFinal = t1 - t0.'],sid=ids['duration'])
 v.box('constraint',677,518,551,190,'maintenanceAlignment : MaxTimeConstraint',['p1 : Real [seconds]','maxTime : Real [seconds]','','p1 <= maxTime'],sid='_18_0_2_baa02e2_1429562376319_87817_151513',stereo='<<constraint>>')
 v.line([(412,555),(677,555)],'=  p1',511,541,sid=ids['duration_binding'])
 v.line([(1228,275),(1250,275),(1250,756),(1000,756),(1000,708)],'=  maxTime',1060,778,sid=ids['limit_binding'])
 v.text(52,707,['Bindings equate values; these lines are not directional data transfers.','1560 s (paper-reported 26 min) meets both timing boundaries. No simulation was replayed.'],17)
 v.footer(['English-to-formalization association is documented by paper Figure 7; exact publication export is unverified.',
           'Scalar boundary checks preserve <=. They do not establish full REQ-2-APS-0017 satisfaction or acceptance.',
           'New model-derived schematic; derived SysML v2 model is separately parser-validated. Original figures are linked.'])
 v.save()

 s=D['slices']['ape-composition'];parts={p['type_name']:p for p in s['parts']}
 v=View('03-ape-composition','ESO APE reference | Active segmented mirror composition','Model-derived simplified SysML v1 block-definition view | original model: SysML 1.6, 2023 snapshot')
 v.box('asm',132,153,1016,126,'ActiveSegmentedMirror',['Selected composition only; physical values and other interfaces are omitted.'],sid='_15_0_bf10301_1202464929960_949157_5982',stereo='<<block>>',fill='#f4f7fa')
 xs=[132,483,834]
 for x,type_ in zip(xs,['Segment','PositionActuator','Mount']):
  p=parts[type_];v.box(type_,x,426,314,144,type_,sid=p['type_id'],stereo='<<block>>')
  center=x+157;v.line([(center,279),(center,426)],diamond=True,sid=p['id'])
  label=('seg [61]' if type_=='Segment' else 'pact [183]' if type_=='PositionActuator' else '[1] (implicit)')
  v.text(center+15,400,label,16,sid=p['id'])
 v.text(834,604,['Source Mount role is unnamed.','Only derived v2 names it mount.'],16)
 v.text(132,664,['The Cookbook explains three actuators per segment: 61 x 3 = 183.','The selected formal model composes all 183 actuators directly under the mirror.','No actuator-to-individual-segment allocation is added by this simplification.'],20)
 v.footer(['Real APE instrument; professionally reverse-engineered and simplified MBSE reference, not an as-built model.',
           'Cookbook section 5.3.5 / Figure 10 (2011) and pinned model (2023): traced match, not an identical export.',
           'New layout omits source photographs and quantitative values; Apache-2.0 model notices preserved.'])
 v.save()

 v=View('04-ape-optical','ESO APE reference | Optical boundary and nested ports','Model-derived simplified SysML v1 internal-block view | new layout preserves connectors, not invented flows')
 v.box('context',52,134,1176,613,'observatoryContext : ObservatoryContext',sid='_15_0_baa02e2_1202883879567_634876_2995',fill='#ffffff')
 v.box('ape',102,215,528,474,'ape_t : APE_Telescope',sid='_16_5_4_359f051f_1260449554968_992972_24991',fill='#f4f7fa')
 v.box('omb',136,300,349,315,'omb : OptoMechanicalBench',sid='_15_0_3c00182_1203339836217_958479_4963',fill='#ffffff')
 v.box('lens',171,478,277,78,'lg1 : LensGroup1',sid='_15_1_baa02e2_1210774914160_880510_12061')
 v.box('ut',793,359,387,242,'ut3 : UnitTelescope',sid='_15_0_baa02e2_1202884121520_857843_3293',fill='#f4f7fa')
 v.box('adapter',830,472,313,91,'ada : NasmythAdapter',sid='_15_1_baa02e2_1212914157343_515859_8565',fill='#ffffff')
 v.line([(448,517),(630,517)],sid='_16_6_1_382e050d_1263291033453_363731_11568')
 v.line([(630,517),(830,517)],sid='_16_6_1_382e050d_1263290942250_179892_11452')
 v.port('in',448,517,'in_oif','_15_1_bf10301_1210764986103_615550_6670')
 v.port('object',630,517,'object_oif','_15_1_bf10301_1210680977392_846759_11441')
 v.port('fov',830,517,'FoV_oif','_15_1_baa02e2_1212914971437_912712_9360')
 v.text(458,505,'in_oif',16);v.text(542,551,'object_oif',16);v.text(736,505,'FoV_oif',16)
 v.text(155,650,'lg1 is reached through the nested path omb.lg1.',18)
 v.text(698,277,['The English source describes telescope light','passing from the Nasmyth adapter into APE.','The selected 2023 connectors are undirected.'],18)
 v.footer(['2023 source: three untyped <<proxy>> ports. Squares omit 2011 Figure 20 port arrow glyphs.',
           'Connectors stay undirected; interface contracts, conjugation and full proxy-port semantics are not translated.',
           'Derived v2 exposes only lg1/ada for nested ends; ut3/ape_t retain private visibility.'])
 v.save()
 print(json.dumps({'views':4,'notation':'model-derived simplified views; not native source exports','output':str(P/'rendered')}))

if __name__=='__main__':render()
