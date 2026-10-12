"""Pinned real-engineering reference extraction and bounded fidelity checks.

These are selected source slices, not a general XMI importer, v1/v2 converter,
native Cameo validator, or semantic-equivalence prover. No model code executes.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'examples/engineering-reference'
SOURCES={
 'tmt':{'archive':'TMT-2017-02-27.mdzip','sha256':'eb54c3105e4d894bb06378476f364bbf5cdb3bfad4cbf55f10fefacf6cad515f','entry':'com.nomagic.magicdraw.uml_model.model','version':'SysML 1.4 / MagicDraw 18.0','url':'https://github.com/Open-MBEE/TMT-SysML-Model/blob/87832a1657ccab023a90a6acfd0dff02d60e2b46/TMT.mdzip'},
 'ape':{'archive':'APE-ReferenceModel.mdzip','sha256':'66f8b6f9451ec8365d000feed6b0ed7b9141bebb6b24cb5b506724c1963dfcea','entry':'com.nomagic.magicdraw.uml_model.shared_model','version':'SysML 1.6 / MagicDraw 2022x v7','url':'https://github.com/Open-MBEE/OpenSE-Cookbook/blob/288a863025498a4d8bc8e945cfec640e6a90268c/Models/APE-ReferenceModel.mdzip'}
}
DIAGRAMS={
 'tmt-maintenance':('tmt','_18_0_2_b4c02e1_1437082104799_289314_203284'),
 'tmt-timing':('tmt',None),
 'ape-composition':('ape','_15_0_baa02e2_1204997376379_43454_9637'),
 'ape-optical':('ape','_15_0_baa02e2_1202884084083_833372_3197')
}
def local(tag): return tag.rsplit('}',1)[-1]
def xa(e,key): return next((v for n,v in e.attrib.items() if n.startswith('{') and local(n)==key),None)
def child(e,tag): return next((c for c in e if local(c.tag)==tag),None)
def xid(e): return xa(e,'id')
def plain(e): return {local(n):v for n,v in e.attrib.items()}
def strip_vendor(e):
 c=ET.fromstring(ET.tostring(e))
 for p in c.iter():
  for sub in list(p):
   if local(sub.tag)=='Extension': p.remove(sub)
 return c
def record(e,parents):
 return {'id':xid(e),'kind':xa(e,'type') or local(e.tag),'name':e.attrib.get('name'),
         'parent_id':xid(parents[e]) if e in parents else None,'attributes':plain(e),
         'children':[{'kind':local(c.tag),'attributes':plain(c),'text':c.text.strip() if c.text and c.text.strip() else None} for c in e if local(c.tag)!='Extension']}
def extract(source_root):
 result={'schema':'real-engineering-reference/1','source_scope':'Selected native-model slices; source figures are linked, not redistributed.','sources':SOURCES,'slices':{}}
 loaded={}
 for slug,source in SOURCES.items():
  path=source_root/slug/source['archive']; data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=source['sha256']: raise ValueError('Wrong source revision: '+str(path))
  with zipfile.ZipFile(path) as z:
   if z.testzip() is not None: raise ValueError('Corrupt native archive')
   xml=z.read(source['entry'])
  root=ET.fromstring(xml)
  idx={xid(e):e for e in root.iter() if xid(e)}
  parents={c:p for p in root.iter() for c in p}
  loaded[slug]=(root,idx,parents)
 for name,(slug,diagram) in DIAGRAMS.items():
  root,idx,parents=loaded[slug]
  used={c.attrib['href'].split('#')[-1] for c in idx[diagram].iter() if local(c.tag)=='usedObjects'} if diagram else set()
  retained=set(used) if name=='tmt-maintenance' else set()
  extra=set()
  if name=='tmt-maintenance':
   extra.add('_17_0_2_3_41e01aa_1383540424302_365385_58121')
   transitions=[]
   for i in sorted(used):
    e=idx[i]
    if xa(e,'type')!='uml:Transition': continue
    signals=[]
    for t in e:
     if local(t.tag)=='trigger':
      event=idx.get(t.attrib.get('event'))
      signal=idx.get(event.attrib.get('signal')) if event is not None else None
      signals.append({'event_id':xid(event) if event is not None else None,'signal_id':xid(signal) if signal is not None else None,'name':signal.attrib.get('name') if signal is not None else None})
      if event is not None: extra.add(xid(event))
      if signal is not None: extra.add(xid(signal))
    eff=child(e,'effect')
    if eff is not None:extra.add(xid(eff))
    transitions.append({'id':i,'source':e.attrib['source'],'target':e.attrib['target'],'source_name':idx[e.attrib['source']].attrib.get('name') or xa(idx[e.attrib['source']],'type'),'target_name':idx[e.attrib['target']].attrib.get('name') or xa(idx[e.attrib['target']],'type'),'signals':signals,'effect':eff.attrib.get('name') if eff is not None else None,'effect_id':xid(eff) if eff is not None else None,'effect_body':child(eff,'body').text if eff is not None and child(eff,'body') is not None else None,'guard':plain(child(e,'guard')) if child(e,'guard') is not None else None})
   extra.update(xid(c) for i in used for c in idx[i] if local(c.tag)=='doActivity' and xid(c))
   result['slices'][name]={'transitions':transitions}
  elif name=='tmt-timing':
   retained={
    '_2ca33d85-e793-40fa-9f3a-b3c90e37fd87__17_188f7b22-cc8f-4e5c-b35c-8e3fc63198fb',
    '_18_0_2_baa02e2_1429562376319_87817_151513',
    '_18_0_2_baa02e2_1429562376320_828902_151514',
    '_18_0_2_baa02e2_1429562376320_528739_151515',
    '_18_0_5_baa02e2_1454126902368_420796_169134',
    '_18_0_5_c0402fd_1464026223074_50206_149810',
    '_18_0_5_c0402fd_1464026223153_78622_149833',
    '_18_0_5_c0402fd_1464026223153_484492_149834',
    '_18_0_5_c0402fd_1464026223152_177814_149832',
    '_18_0_5_c0402fd_1464026509327_174724_150238',
    '_18_0_4_baa02e2_1438808102180_452510_161842'}
   for e in root.iter():
    if e.attrib.get('base_Class') in retained:extra.add(xid(e))
    if xa(e,'type')=='uml:Abstraction' and any(i in str(e.attrib) for i in retained):extra.add(xid(e))
    if local(e.tag)=='Refine' and e.attrib.get('base_Abstraction') in extra:extra.add(xid(e))
   rule=idx['_18_0_2_baa02e2_1429562376320_828902_151514']
   expression=next(c.text for c in rule.iter() if local(c.tag)=='body')
   prop=idx['_18_0_5_c0402fd_1464026223153_484492_149834']
   default=float(child(prop,'defaultValue').attrib['value'])
   req=next(e for e in root.iter() if e.attrib.get('TMT_ID')=='REQ-2-APS-0017' and 'Text' in e.attrib)
   text=' '.join(ET.fromstring(req.attrib['Text']).itertext()).strip()
   result['slices'][name]={'source_expression':expression,'limit_seconds':default,'original_requirement':text,'source_ids':{'requirement':req.attrib['base_Class'],'constraint':xid(rule),'limit':xid(prop),'duration':'_18_0_4_baa02e2_1438808102180_452510_161842','duration_binding':'_18_0_5_c0402fd_1464026509327_174724_150238','limit_binding':'_18_0_5_c0402fd_1464026223152_177814_149832'},'boundary_discrepancy':'English less than 30 minutes; original mathematical constraint is <= 1800 seconds. Do not silently reconcile.'}
  elif name=='ape-composition':
   retained={
    '_15_0_bf10301_1202464929960_949157_5982','_15_0_baa02e2_1204997460087_185642_9681',
    '_15_0_baa02e2_1204997471931_475271_9705','_16_6_1_38390512_1265838951058_526030_71009',
    '_15_0_baa02e2_1204997510902_964101_9752','_15_0_baa02e2_1204997513668_221125_9807',
    '_16_6_1_38390512_1265838967762_750737_71036'}
   extra.update(e.attrib['association'] for i in retained for e in [idx[i]] if 'association' in e.attrib)
   parts=[]
   for i in sorted(retained):
    e=idx[i]
    if xa(e,'type')=='uml:Property' and 'type' in e.attrib:
     lo,hi=child(e,'lowerValue'),child(e,'upperValue')
     parts.append({'id':i,'name':e.attrib.get('name'),'type_id':e.attrib['type'],'type_name':idx[e.attrib['type']].attrib['name'],'lower':int(lo.attrib['value']) if lo is not None else 1,'upper':int(hi.attrib['value']) if hi is not None else 1,'implicit_multiplicity':lo is None and hi is None,'aggregation':e.attrib.get('aggregation'),'owner_id':xid(parents[e])})
   result['slices'][name]={'parts':parts,'note':'Mount role is unnamed, multiplicity 1 implicit. Actuators are directly composed by ASM, not nested inside Segment.'}
  else:
   retained=set(used)-{i for i in used if xa(idx[i],'type')=='uml:Diagram'}
   extra={
    '_15_0_baa02e2_1202883879567_634876_2995','_15_0_bf10301_1202463993727_990869_4923',
    '_16_5_4_359f051f_1260448562906_634594_24892','_15_0_baa02e2_1202885375098_361835_4279',
    '_15_0_baa02e2_1203006674929_719130_4458','_15_0_bf10301_1202464003014_225685_4947',
    '_15_1_baa02e2_1212911438453_939051_5879','_16_5_4_359f051f_1260448645890_255328_24920'}
   connectors=[]
   for i in sorted(retained):
    e=idx[i]
    if xa(e,'type')=='uml:Connector':
     connectors.append({'id':i,'owner_id':xid(parents[e]),'ends':[plain(c) for c in e if local(c.tag)=='end']})
   for e in root.iter():
    if local(e.tag)=='NestedConnectorEnd' and e.attrib.get('base_ConnectorEnd') in retained:extra.add(xid(e))
   port_ids={'_15_1_bf10301_1210764986103_615550_6670','_15_1_bf10301_1210680977392_846759_11441','_15_1_baa02e2_1212914971437_912712_9360'}
   proxies=[e for e in root.iter() if local(e.tag)=='ProxyPort' and e.attrib.get('base_Port') in port_ids]
   extra.update(xid(e) for e in proxies)
   result['slices'][name]={'connectors':connectors,'port_stereotypes':[{'id':xid(e),'base_Port':e.attrib['base_Port'],'stereotype':'ProxyPort','namespace':e.tag.split('}')[0][1:]} for e in proxies],'note':'2023 untyped SysML 1.6 ProxyPort applications retained as original records. Plain v2 ports and square glyphs omit full proxy-interface semantics and the 2011 figure arrow glyphs; no item-flow direction invented. Only lg1/ada visibility widened in v2; ut3/ape_t remain private.'}
  retained|=extra
  # Enumerate every source-diagram element and direct member of retained classifiers.
  scope=used|retained
  for i in list(retained):
   if i in idx and xa(idx[i],'type') in ['uml:Class','uml:State']:
    scope.update(xid(c) for c in idx[i] if xid(c) and local(c.tag)!='Extension')
  rows=[]
  for i in sorted(scope):
   if i not in idx:rows.append({'id':i,'disposition':'omitted','reason':'Unresolved external reference; no invented content.'});continue
   e=idx[i];row=record(e,parents)
   row['disposition']='retained' if i in retained else 'omitted'
   row['reason']='Engineering meaning retained in selected source projection; presentation redrawn and implementation may remain opaque.' if i in retained else 'Outside selected structural/behavioral question: physical values, other interfaces, navigation, or vendor presentation.'
   rows.append(row)
  result['slices'][name].update({'project':slug,'source_diagram_id':diagram,'trace':rows,'retained_ids':sorted(retained)})
  fragment=ET.Element('extracted-source-fragment',{'modified':'2026-10-01: selected and reserialized; not a complete native model','archive_sha256':SOURCES[slug]['sha256']})
  # Keep source content once, and make any intentionally unselected direct members explicit.
  roots=[idx[i] for i in sorted(retained) if i in idx and not any(xid(p) in retained for p in ancestor_chain(idx[i],parents))]
  for e in roots:
   c=strip_vendor(e)
   fragment.append(c)
  ET.indent(fragment)
  (PACK/'source'/(name+'.xml')).write_bytes(ET.tostring(fragment,encoding='utf-8',xml_declaration=True))
 return result

def ancestor_chain(e,parents):
 while e in parents:
  e=parents[e];yield e

def check(projection):
 t=projection['slices']['tmt-maintenance']
 expected=[
 ('Initializing','StandBy','InitComplete',None),
 ('StandBy','Maintenance Alignment','Maintenance Alignment',None),
 ('Maintenance Alignment','StandBy','Abort',None),
 ('Correcting Rigid Body and Segment Figure','Broad Band Phasing 1um','Finished','diffTime'),
 ('Broad Band Phasing 1um','Narrow Band Phasing','Finished','diffTime'),
 ('Narrow Band Phasing','StandBy','Finished','FinalDiffTime'),
 ('StandBy','uml:FinalState','Finished',None)]
 got=[(x['source_name'],x['target_name'],x['signals'][0]['name'] if x['signals'] else None,x['effect']) for x in t['transitions'] if x['signals']]
 if sorted(map(str,got))!=sorted(map(str,expected)):raise ValueError('Original lifecycle semantics changed')
 if len(t['transitions'])!=9:raise ValueError('Missing initial transitions')
 timing=projection['slices']['tmt-timing']
 if timing['source_expression']!='p1<=maxTime' or timing['limit_seconds']!=1800:raise ValueError('Wrong timing revision/operator')
 if 'less than 30 minutes' not in timing['original_requirement']:raise ValueError('Lost English boundary')
 parts=projection['slices']['ape-composition']['parts']
 if {(p['type_name'],p['lower'],p['upper'],p['aggregation']) for p in parts}!={('Segment',61,61,'composite'),('PositionActuator',183,183,'composite'),('Mount',1,1,'composite')}:raise ValueError('Changed composition')
 if len({p['owner_id'] for p in parts})!=1:raise ValueError('Invented nested actuator allocation')
 optical=projection['slices']['ape-optical']['connectors']
 if len(optical)!=2:raise ValueError('Lost optical connectors')
 proxies=projection['slices']['ape-optical'].get('port_stereotypes',[])
 expected={'_15_1_bf10301_1210764986103_615550_6670','_15_1_bf10301_1210680977392_846759_11441','_15_1_baa02e2_1212914971437_912712_9360'}
 if len(proxies)!=3 or {p['base_Port'] for p in proxies}!=expected or any(p['stereotype']!='ProxyPort' or p['namespace']!='http://www.omg.org/spec/SysML/20181001/SysML' for p in proxies):raise ValueError('Lost original ProxyPort stereotype')
 rows={r['id']:r for r in projection['slices']['ape-optical']['trace']}
 if any(p['id'] not in rows or rows[p['id']].get('kind')!='ProxyPort' or rows[p['id']].get('attributes',{}).get('base_Port')!=p['base_Port'] or rows[p['id']].get('disposition')!='retained' for p in proxies):raise ValueError('ProxyPort trace drift')
 return {'checks':['archive byte/hash/integrity verified during extraction; --check checks saved contracts','nine transitions, events/effects and composite Abort source','original <= expression and 1800-second class default','strict English retained separately','direct 61/183/1 composition','two selected optical connectors with source end IDs'],'claim':'bounded source extraction/fidelity; not native-editor execution or general equivalence'}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--source-root',type=Path,default=ROOT/'work/authentic-sysml-sources')
 ap.add_argument('--check',action='store_true',help='Verify saved projection without rewriting it.')
 args=ap.parse_args()
 if args.check:
  saved=json.loads((PACK/'source/projection.json').read_text());return print(json.dumps(check(saved),indent=2))
 projection=extract(args.source_root);receipt=check(projection)
 (PACK/'source/projection.json').write_text(json.dumps(projection,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
