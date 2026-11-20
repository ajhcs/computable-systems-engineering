"""Synthetic native name/alias fixture; credentials remain in a private receipt."""
from pathlib import Path
import argparse,json,os,sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer
from tests.test_composition_edit import REFERENCE_SOURCE,REFERENCE_SCOPE
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('view');args=p.parse_args()
output=Path(args.output);output.mkdir(mode=0o700,exist_ok=False)
records={'scope.json':{'kind':'retained_configuration','text':json.dumps(REFERENCE_SCOPE,indent=2)+'\n'}}
project,_=CompositionProject.create(output/'project.git',{'reference.sysml':REFERENCE_SOURCE},
    project_id=str(uuid4()),request_id=str(uuid4()),linked_records=records)
server=CompositionHTTPServer(project,args.view)
with open(os.open(output/'connection.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w')as f:
 json.dump({'url':server.origin+'/#access='+server.access,'origin':server.origin,'pid':os.getpid(),'project':str(project.repository)},f)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
