#!/usr/bin/env python3
"""Capture source identities and public command declarations without executing them.

Baseline receipts belong in ignored work/, because source paths and dirty-file
inventories may describe private material. This is an inventory, not qualification.
"""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def declarations(path):
    """Retain exact argparse declarations and tool definitions for human mapping."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (UnicodeError, SyntaxError):
        return []
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ('add_parser', 'add_argument'):
                args = [a.value for a in node.args if isinstance(a, ast.Constant)
                        and isinstance(a.value, str)]
                choices = next((ast.unparse(k.value) for k in node.keywords if k.arg == 'choices'), None)
                found.append({'line': node.lineno, 'kind': node.func.attr,
                              'arguments': args, 'choices_source': choices})
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                   and d.func.attr == 'tool' for d in node.decorator_list):
                found.append({'line': node.lineno, 'kind': 'mcp_tool', 'name': node.name})
    return sorted(found, key=lambda d: d['line'])


def capture(root):
    root = Path(root).resolve()
    paths = git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')
    files, commands = [], {}
    for raw in sorted(set(paths)):
        if not raw:
            continue
        name = raw.decode('utf-8')
        path = root / name
        if path.is_symlink():
            # Record the link itself; do not follow it into private/outside data.
            import os
            files.append({'path': name, 'symlink': os.readlink(path)})
        elif path.is_file():
            content = path.read_bytes()
            files.append({'path': name, 'sha256': sha256(content).hexdigest(), 'bytes': len(content)})
            if name.endswith('.py') and (name.startswith('scripts/') or
                    name.endswith('/scripts/cse.py') or name == 'hosted/server.py'):
                items = declarations(path)
                if items:
                    commands[name] = items
        else:
            files.append({'path': name, 'missing': True})
    return {'root': str(root), 'head': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'status': git(root, 'status', '--porcelain=v1').decode(),
            'files': files, 'command_declarations': commands,
            'claim': 'source inventory only; command declarations require semantic mapping'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='append', required=True, metavar='NAME=ROOT')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'version': 'cse-workbench-baseline-1', 'sources': {}}
    for binding in args.source:
        name, root = binding.split('=', 1)
        if name in result['sources']:
            parser.error('Duplicate source name')
        result['sources'][name] = capture(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite a preservation receipt.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({k: {'head': v['head'], 'files': len(v['files']),
                         'entrypoints': len(v['command_declarations'])}
                      for k, v in result['sources'].items()}, indent=2))


if __name__ == '__main__':
    main()
