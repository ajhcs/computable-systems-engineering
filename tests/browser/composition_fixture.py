"""Synthetic native/Git fixture for the physical navigation browser checks."""
from pathlib import Path
import argparse,json,os,sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('view');args=p.parse_args()
root=ROOT;output=Path(args.output);output.mkdir(mode=0o700,exist_ok=False)
scope={'version':'configuration-1.0','root':{'native_name':'DiagramComposition::current','type':'DiagramComposition::Assembly'},'selected_roles':{'Left':{'parent':'$root','native_name':'DiagramComposition::current::left','type':'DiagramComposition::Device'}},'open_alternatives':[],'connections':[]}
records={'left.scope.json':{'kind':'retained_configuration','text':json.dumps(scope)}}
if args.view=='PC_USAGE':
 records['labels.json']={'kind':'display_labels','text':json.dumps({'version':1,'view':'PC_USAGE','title':'Physical parts','labels':[{'element':'DiagramComposition::current::left','text':'A < B & </script><script>globalThis.INJECTED=true</script>'}]})}
project,_=CompositionProject.create(output/'project.git',{'model.sysml':(root/'examples/workbench/composition/diagram-model.sysml').read_text()},project_id=str(uuid4()),request_id=str(uuid4()),linked_records=records)
server=CompositionHTTPServer(project,args.view)
with open(os.open(output/'connection.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w')as f:json.dump({'url':server.origin+'/#access='+server.access,'origin':server.origin,'pid':os.getpid(),'project':str(project.repository)},f)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
