#!/usr/bin/env python3
"""Run a private loopback development UI for one saved physical view."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--view-id', required=True)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--connection-file', required=True, help='exclusive-create private local connection receipt')
    args = parser.parse_args()
    server = CompositionHTTPServer(CompositionProject(args.project), args.view_id, args.port)
    try:
        receipt = {'url': server.origin + '/#access=' + server.access, 'pid': os.getpid(),
                   'project_id': server.session.state()['projection']['project_id'],
                   'view': args.view_id, 'claim': 'private_loopback_development_not_hosted_application_acceptance'}
        with open(os.open(args.connection_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
            json.dump(receipt, output, indent=2)
            output.write('\n')
        print(json.dumps({'origin': server.origin, 'connection_file': args.connection_file}), flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
