#!/usr/bin/env python3
"""Build a local CSE marketplace from one committed Git tree, without dirty files."""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = frozenset({'.codex-plugin', 'assets', 'docs', 'examples', 'scripts',
                         'skills', 'tests', 'tools', 'verifier'})
FILES = frozenset({'AGENTS.md', 'CONTRIBUTING.md', 'LICENSE', 'README.md',
                   'plugin.json', 'requirements-analysis.txt'})


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def included(name):
    parts = PurePosixPath(name).parts
    return bool(parts) and (parts[0] in DIRECTORIES or name in FILES)


def build(repo, revision, destination, marketplace_name='cse-local'):
    repo = Path(repo).resolve()
    destination = Path(destination).resolve()
    if destination == repo or repo in destination.parents:
        raise ValueError('Package output must be outside the source checkout')
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}')
    tree = git(repo, 'rev-parse', commit + '^{tree}')
    if destination.exists():
        raise ValueError('Package output already exists; use a fresh directory')
    destination.mkdir(parents=True)
    package = destination / 'plugins/computable-systems-engineering'
    package.mkdir(parents=True)
    archive = subprocess.Popen(['git', '-C', str(repo), 'archive', '--format=tar', commit],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    records = {}
    try:
        with tarfile.open(fileobj=archive.stdout, mode='r|') as stream:
            for member in stream:
                name = member.name.rstrip('/')
                if not included(name):
                    continue
                parts = PurePosixPath(name).parts
                if PurePosixPath(name).is_absolute() or '..' in parts:
                    raise ValueError('Unsafe archive member: ' + name)
                path = package.joinpath(*parts)
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if member.issym():
                    target = PurePosixPath(member.linkname)
                    resolved = (path.parent / str(target)).resolve()
                    if target.is_absolute() or package not in resolved.parents:
                        raise ValueError('Nonportable symlink: ' + name)
                    path.symlink_to(member.linkname)
                    records[name] = {'symlink': member.linkname}
                elif member.isfile():
                    data = stream.extractfile(member).read()
                    path.write_bytes(data)
                    path.chmod(0o755 if member.mode & 0o111 else 0o644)
                    records[name] = {'sha256': sha256(data).hexdigest(), 'bytes': len(data),
                                     'mode': '755' if member.mode & 0o111 else '644'}
                else:
                    raise ValueError('Unsupported archive member: ' + name)
        stderr = archive.stderr.read().decode()
        if archive.wait() != 0:
            raise ValueError('git archive failed: ' + stderr)
    finally:
        archive.stdout.close()
        archive.stderr.close()
        if archive.poll() is None:
            archive.terminate()
            archive.wait()
    portable = json.loads((package / 'plugin.json').read_text())
    native = json.loads((package / '.codex-plugin/plugin.json').read_text())
    if portable['name'] != native['name'] or portable['version'] != native['version']:
        raise ValueError('Portable and native plugin identities differ')
    skills = sorted(p.parent.name for p in (package / 'skills').glob('*/SKILL.md'))
    if len(skills) != 11:
        raise ValueError('Expected eleven independently invocable CSE skills')
    marketplace = {'name': marketplace_name,
                   'interface': {'displayName': 'Computable Systems Engineering — Local'},
                   'plugins': [{'name': portable['name'],
                                'source': {'source': 'local', 'path': './plugins/' + portable['name']},
                                'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                                'category': 'Productivity'}]}
    manifest = destination / '.agents/plugins/marketplace.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(marketplace, indent=2) + '\n')
    receipt = {'schema': 'cse.plugin-source/1', 'status': 'pass', 'commit': commit, 'tree': tree,
               'name': portable['name'], 'version': portable['version'], 'skills': skills,
               'selection': {'directories': sorted(DIRECTORIES), 'files': sorted(FILES),
                             'omitted': 'Git metadata, CI, source-only aliases, ignored and untracked files'},
               'files': records,
               'scope': 'Committed source export and byte inventory; no installation or acceptance claim.'}
    (destination / 'source-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--marketplace-name', default='cse-local')
    args = parser.parse_args()
    try:
        result = build(args.repo, args.ref, args.out, args.marketplace_name)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}))
        return 1
    print(json.dumps({key: result[key] for key in ('status', 'commit', 'tree', 'name', 'version')} |
                     {'payload_files': len(result['files']), 'marketplace': str(args.out.resolve())}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
