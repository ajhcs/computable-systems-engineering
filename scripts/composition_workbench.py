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
    parser.add_argument('--initial', action='store_true', help='start at an unsaved first-root session')
    parser.add_argument('--project-id', help='prospective project UUID; retain it across startup restarts')
    parser.add_argument('--root-element-id', help='prospective root UUID; retain it across startup restarts')
    args = parser.parse_args()
    if args.initial:
        if not args.project_id or not args.root_element_id:
            parser.error('Initial startup requires the retained project and root UUIDs')
        from verifier.composition_startup import InitialCompositionHTTPServer
        server = InitialCompositionHTTPServer(CompositionProject(args.project), args.project_id,
                                              args.root_element_id, args.view_id, args.port)
    else:
        if args.project_id or args.root_element_id:
            parser.error('Prospective identities apply only to initial startup')
        server = CompositionHTTPServer(CompositionProject(args.project), args.view_id, args.port)
    try:
        receipt = {'url': server.origin + ('/start#access=' if args.initial else '/#access=') + server.access, 'pid': os.getpid(),
                   'project_id': args.project_id if args.initial else server.session.state()['projection']['project_id'],
                   'view': args.view_id, 'claim': 'private_loopback_development_not_hosted_application_acceptance'}
        if args.initial:
            receipt['root_element_id'] = args.root_element_id
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
