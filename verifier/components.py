"""Presentation components with explicit, non-authoritative modeling contexts."""
from pathlib import Path
from hashlib import sha256
from xml.etree import ElementTree as ET
import base64, json, re, shutil

ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'assets/engineering-library'
SVG='{http://www.w3.org/2000/svg}'

def inventory(root=LIBRARY):
    data=json.loads((Path(root)/'index.json').read_text())
    if data.get('schema')!='cse.component-library/1':raise ValueError('Unsupported component schema')
    rows=data['components'];ids=[r['id'] for r in rows]
    if data['count']!=len(ids) or len(ids)!=len(set(ids)):raise ValueError('Duplicate IDs or incorrect count')
    return rows

def select(query='',sysml=None,family=None,root=LIBRARY):
    return [r for r in inventory(root) if
            (not family or family.casefold() in r['family'].casefold()) and
            (not sysml or sysml in r['mapping']['sysml_v2']+r['mapping']['sysml_v1']) and
            all(word in json.dumps(r,ensure_ascii=False).casefold() for word in query.casefold().split())]

def component(id,root=LIBRARY):
    return next((r for r in inventory(root) if r['id']==id),None)

def validate(root=LIBRARY):
    root=Path(root).resolve(); rows=inventory(root)
    for row in rows:
        path=(root/row['file']).resolve()
        if not path.is_relative_to(root) or path.suffix!='.svg':raise ValueError('Invalid component path: '+row['id'])
        if sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Component hash mismatch: '+row['id'])
        doc=ET.parse(path).getroot();ids=[];refs=[]
        for e in doc.iter():
            if e.tag in (SVG+'image',SVG+'script',SVG+'foreignObject'):raise ValueError('Unsupported SVG content: '+row['id'])
            if e.get('id'):ids.append(e.get('id'))
            for k,v in e.attrib.items():
                if k.endswith('href'):
                    if not v.startswith('#'):raise ValueError('External SVG dependency: '+row['id'])
                    refs.append(v[1:])
                refs+=re.findall(r'url\(#([^)]*)\)',v)
                if k in ('aria-labelledby','aria-describedby'):refs+=v.split()
        if len(ids)!=len(set(ids)) or not set(refs)<=set(ids):raise ValueError('Unresolved/duplicate SVG IDs: '+row['id'])
        mapping=row['mapping']
        if mapping['formal_sysml_glyph'] or not mapping['rationale'] or not mapping['cse_skills']:raise ValueError('Invalid modeling context: '+row['id'])
        if not set(row.get('children',[]))<={r['id'] for r in rows}:raise ValueError('Missing child component')
    receipt=json.loads((root/'integrations/receipt.json').read_text())
    if receipt['index_sha256']!=sha256((root/'index.json').read_bytes()).hexdigest():raise ValueError('Stale adapter index')
    for rel,digest in receipt['outputs'].items():
        path=(root/rel).resolve()
        if not path.is_relative_to(root) or sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Stale adapter output: '+rel)
    return {'status':'pass','components':len(rows),'scope':'SVG integrity and declared context; engineering model semantics remain external'}

def drawio(rows,out,root=LIBRARY):
    """Write documented mxlibrary XML with editable cell metadata and vector images."""
    entries=[]
    for row in rows:
        raw=(Path(root)/row['file']).read_bytes()
        model=ET.Element('mxGraphModel');g=ET.SubElement(model,'root')
        ET.SubElement(g,'mxCell',id='0');ET.SubElement(g,'mxCell',id='1',parent='0')
        obj=ET.SubElement(g,'object',{'id':'component','label':row['name'],'cseId':row['id'],
            'cseLibraryVersion':'0.2.0-alpha.5','cseTreatment':row.get('treatment',''),
            'cseContext':row['mapping']['principle'],'cseModelBinding':'unbound',
            'cseApproval':row.get('approval_state','proposed')})
        image='data:image/svg+xml,'+base64.b64encode(raw).decode()
        cell=ET.SubElement(obj,'mxCell',{'parent':'1','vertex':'1','style':'shape=image;imageAspect=1;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;html=0;image='+image+';'})
        ET.SubElement(cell,'mxGeometry',{'width':'132','height':'132','as':'geometry'})
        entries.append({'xml':ET.tostring(model,encoding='unicode'),'w':132,'h':132,'title':row['name']+' ['+row['id']+']','tags':row['family']+' '+row['mapping']['principle']})
    doc=ET.Element('mxlibrary');doc.text=json.dumps(entries,ensure_ascii=False)
    Path(out).parent.mkdir(parents=True,exist_ok=True);ET.ElementTree(doc).write(out,encoding='utf-8',xml_declaration=True)

def export(format,out,rows=None,root=LIBRARY):
    root=Path(root);out=Path(out);rows=inventory(root) if rows is None else rows
    validate(root)
    out.mkdir(parents=True,exist_ok=True)
    if format=='drawio':drawio(rows,out/'cse-components.xml',root)
    elif format=='svg':pass
    elif format=='kernspan':
        if len(rows)!=len(inventory(root)):raise ValueError('Kernspan atlas export requires the whole library; filter with the adapter search API')
        for path in (root/'integrations/kernspan').iterdir():
            if path.is_file():shutil.copyfile(path,out/path.name)
    else:raise ValueError('Unsupported export format')
    # Keep every metadata file reference usable in the exported project bundle,
    # including the editable vector masters beside screen-atlas derivatives.
    for row in rows:
        target=out/row['file'];target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/row['file'],target)
    (out/'components.json').write_text(json.dumps({'schema':'cse.component-library/1','count':len(rows),'components':rows},indent=2)+'\n')
    return {'status':'pass','format':format,'count':len(rows),'directory':str(out)}
