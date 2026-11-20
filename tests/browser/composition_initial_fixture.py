"""Synthetic prospective project; explicit retained grant for compute restart."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_startup import InitialCompositionHTTPServer

parser=argparse.ArgumentParser()
parser.add_argument('folder')
parser.add_argument('--port',type=int,default=0)
parser.add_argument('--connection',default='connection.json')
args=parser.parse_args();folder=Path(args.folder).resolve()
folder.mkdir(mode=0o700,exist_ok=True)
boot_path=folder/'boot.json'
if boot_path.exists():
    boot=json.loads(boot_path.read_text())
else:
    boot={'project_id':str(uuid4()),'root_element_id':str(uuid4()),'view_id':'PC'}
    with open(os.open(boot_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as out:json.dump(boot,out)
server=InitialCompositionHTTPServer(CompositionProject(folder/'project.git'),boot['project_id'],boot['root_element_id'],boot['view_id'],args.port)
connection={'url':server.origin+'/start#access='+server.access,'origin':server.origin,'project':str(folder/'project.git'),
            'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],**boot}
with open(os.open(folder/args.connection,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as out:json.dump(connection,out)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
