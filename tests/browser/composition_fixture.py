"""Synthetic native/Git fixture for the physical navigation browser checks."""
from pathlib import Path
import argparse,json,os,runpy,sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('view');p.add_argument('--retained-findings',action='store_true');args=p.parse_args()
root=ROOT;output=Path(args.output);output.mkdir(mode=0o700,exist_ok=False)
scope={'version':'configuration-1.0','root':{'native_name':'DiagramComposition::current','type':'DiagramComposition::Assembly'},'selected_roles':{'Left':{'parent':'$root','native_name':'DiagramComposition::current::left','type':'DiagramComposition::Device'}},'open_alternatives':[],'connections':[]}
records={'left.scope.json':{'kind':'retained_configuration','text':json.dumps(scope)}}
models={'model.sysml':(root/'examples/workbench/composition/diagram-model.sysml').read_text()}
if args.view=='CROSS':
 document,layout=runpy.run_path(str(root/'tests/test_composition_view.py'))['crossing_example']()
 models=document.files
 records={'crossing.layout.json':{'kind':'composition_layout','text':json.dumps(layout)}}
if args.view=='PC_USAGE':
 records['labels.json']={'kind':'display_labels','text':json.dumps({'version':1,'view':'PC_USAGE','title':'Physical parts','labels':[{'element':'DiagramComposition::current::left','text':'A < B & </script><script>globalThis.INJECTED=true</script>'}]})}
if args.retained_findings:
 missing={name:{'parent':'$root','native_name':'DiagramComposition::current::'+name,
                'type':'DiagramComposition::Device'} for name in ('missingOne','missingTwo')}
 failing_scope={**scope,'selected_roles':{**scope['selected_roles'],**missing}}
 records['missing.scope.json']={'kind':'retained_configuration','text':json.dumps(failing_scope)}
project,_=CompositionProject.create(output/'project.git',models,project_id=str(uuid4()),request_id=str(uuid4()),linked_records=records)
server=CompositionHTTPServer(project,args.view)
with open(os.open(output/'connection.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w')as f:json.dump({'url':server.origin+'/#access='+server.access,'origin':server.origin,'pid':os.getpid(),'project':str(project.repository)},f)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
