"""Private synthetic saved-project fixture for live role inspection checks."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer
folder=Path(sys.argv[1]).resolve();folder.mkdir(mode=0o700)
data=json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
case=next(c for c in data['cases'] if c['id']==('inherited' if sys.argv[2] in ('large','typing') else sys.argv[2]))
if sys.argv[2]=='typing':
    case['models']['model.sysml']=case['models']['model.sysml'].replace('part def Sensor;', 'part def Sensor;\n    part def Other;')
if sys.argv[2]=='large':
    case['models']['model.sysml']=case['models']['model.sysml'].replace('part def Base {',
        'part def Base {\n'+''.join(f'part extra{i:03} : Sensor;\n' for i in range(110)))
    scope=json.loads(case['retained_scope_text'])
    scope['selected_roles'].update({f'Extra{i:03}':{'parent':'$root',
        'native_name':f'Composition::Base::extra{i:03}','type':'Composition::Sensor'} for i in range(110)})
    case['retained_scope_text']=json.dumps(scope,indent=2)+'\n'
project,_=CompositionProject.create(folder/'project.git',case['models'],project_id=data['project_id'],request_id=str(uuid4()),
 linked_records={'scope.json':{'kind':'retained_configuration','text':case['retained_scope_text']}})
server=CompositionHTTPServer(project,'PC_CONTEXT')
connection={'url':server.origin+'/#access='+server.access,'project':str(project.repository),'case':case['id']}
file=folder/'connection.json';file.write_text(json.dumps(connection)+'\n');file.chmod(0o600)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
