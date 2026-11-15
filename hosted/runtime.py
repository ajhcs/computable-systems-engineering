"""Bounded request adapters around existing CSE commands; no submitted code or URLs."""
from contextlib import contextmanager
from hashlib import sha256
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MAX_INPUT = 1_000_000
MAX_OUTPUT = 1_800_000
SKILLS = tuple(sorted(p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md')))
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\Z')
SCRIPTS = frozenset({'sysml.py', 'verify.py', 'queueing.py', 'failure_analysis.py',
    'analyze.py', 'measures.py', 'prose.py', 'requirements.py', 'concept_review.py',
    'configuration.py', 'sysml_view.py', 'sysml_testgen.py', 'sysml_present.py', 'icons.py'})


def error(code, detail, status='error'):
    return {'status': status, 'error': {'code': code, 'detail': detail},
            'acceptance': 'not_evaluated'}


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def references(path):
    """Only public packaged Markdown under skills/docs, with a bounded response."""
    if not isinstance(path, str) or '\\' in path:
        return error('reference_path', 'Use a packaged skills/ or docs/ Markdown path.')
    p = Path(path)
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('skills', 'docs'):
        return error('reference_path', 'Use a packaged skills/ or docs/ Markdown path.')
    target = (ROOT / p).resolve()
    if not target.is_relative_to(ROOT) or target.suffix != '.md' or not target.is_file():
        return error('reference_path', 'The packaged Markdown reference was not found.')
    raw = target.read_bytes()
    if len(raw) > 100_000:
        return error('reference_limit', 'Reference exceeds the hosted read limit.')
    return {'status': 'pass', 'path': path, 'sha256': sha256(raw).hexdigest(),
            'text': raw.decode('utf-8')}


def guidance(skill):
    if skill not in SKILLS:
        return error('unknown_skill', 'Select an exact skill name.', ) | {'skills': list(SKILLS)}
    return references(f'skills/{skill}/SKILL.md')


def validate_files(files):
    if not isinstance(files, dict) or not 1 <= len(files) <= 32:
        raise ValueError('Supply 1..32 named UTF-8 files.')
    total = 0
    for name, content in files.items():
        if not isinstance(name, str) or not NAME.fullmatch(name) or '..' in name:
            raise ValueError('File names must be flat names without traversal or options.')
        if Path(name).suffix not in ('.sysml', '.json', '.txt', '.md') or not isinstance(content, str):
            raise ValueError('Only UTF-8 .sysml, .json, .txt and .md file contents are accepted.')
        total += len(content.encode('utf-8'))
    if total > MAX_INPUT:
        raise ValueError('Combined file contents exceed the 1 MB request limit.')


def named(files, name, suffix=None):
    if name not in files or (suffix and not name.endswith(suffix)):
        raise ValueError('Every input path must identify a supplied file of the expected type.')
    return name


def model_names(files):
    models = sorted(name for name in files if name.endswith('.sysml'))
    if not models:
        raise ValueError('Supply at least one .sysml model file.')
    return models


@contextmanager
def workspace():
    # One stable path preserves multi-file model identities across stateless calls.
    # A process lock prevents concurrent requests (or server processes) sharing it.
    parent = Path(os.environ.get('CSE_JOB_ROOT', ROOT / '.tmp/hosted')).resolve()
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (parent / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Hosted runtime is busy; retry this request later.') from None
        path = parent / 'request'
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(mode=0o700)
        try:
            yield path, lock.fileno()
        finally:
            shutil.rmtree(path)
            fcntl.flock(lock, fcntl.LOCK_UN)


def run(script, files, arguments, *, artifacts=False, timeout=30):
    """Execute only a trusted script and adapter-authored argv, then remove all inputs."""
    try:
        if script not in SCRIPTS:
            raise ValueError('Unknown hosted operation.')
        validate_files(files)
        with workspace() as (job, lock_fd):
            for name, content in files.items():
                (job / name).write_text(content, encoding='utf-8')
            env = {k: os.environ[k] for k in ('PATH', 'JAVA_HOME', 'CSE_SYSML_CACHE') if k in os.environ}
            env.update(HOME=str(job), TMPDIR=str(job), PYTHONPATH=str(ROOT),
                PYTHONDONTWRITEBYTECODE='1',
                JAVA_TOOL_OPTIONS='-XX:MaxMetaspaceSize=192m -XX:CompressedClassSpaceSize=64m '
                                  '-XX:ReservedCodeCacheSize=64m -XX:ActiveProcessorCount=1')
            command = [sys.executable, '-B', str(ROOT / 'hosted/job.py'),
                       str(ROOT / 'scripts' / script), *arguments]
            with (job / '.stdout').open('w+b') as out, (job / '.stderr').open('w+b') as err:
                child = subprocess.Popen(command, cwd=job, env=env, stdout=out, stderr=err,
                                         start_new_session=True, pass_fds=(lock_fd,))
                try:
                    child.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    return error('time_limit', 'The hosted time limit was reached; no successful verdict.', 'incomplete')
                finally:
                    # Also reap descendants after a checker failure or early return.
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if out.tell() > MAX_OUTPUT:
                    return error('output_limit', 'Result exceeds the response limit; no successful verdict.', 'incomplete')
                out.seek(0)
                raw = out.read(MAX_OUTPUT + 1).decode('utf-8')
            if child.returncode not in (0, 1, 2):
                return error('checker_terminated', 'Checker terminated before producing a complete result.')
            if not raw.strip():
                return error('checker_output', 'Checker did not produce a JSON result.')
            # Keep every checker status and claim scope; never promote a non-success.
            report = json.loads(raw)
            if not isinstance(report, dict) or 'status' not in report:
                return error('checker_output', 'Checker did not produce a status-bearing JSON object.')
            if child.returncode and report['status'] == 'pass':
                return error('checker_exit', 'Checker exited unsuccessfully; its result is unusable.')
            result = {'status': report['status'], 'report': report,
                      'inputs': {name: sha256(text.encode('utf-8')).hexdigest() for name, text in files.items()},
                      'acceptance': 'not_evaluated'}
            if artifacts and (job / 'output').exists():
                result['files'] = []
                total = len(raw.encode('utf-8'))
                for path in sorted((job / 'output').rglob('*')):
                    if path.is_symlink():
                        raise ValueError('Generated symlinks are not returned.')
                    if path.is_file():
                        data = path.read_bytes()
                        total += len(data)
                        if total > MAX_OUTPUT:
                            return error('artifact_limit', 'Generated artifacts exceed the inline response limit.', 'incomplete')
                        result['files'].append({'name': path.relative_to(job / 'output').as_posix(),
                            'sha256': sha256(data).hexdigest(), 'content': data.decode('utf-8')})
            # Preserve checker bytes/values, including source labels used in digests.
            # The deployed request root is fixed and contains no account secrets.
            return result
    except RuntimeError as exc:
        return error('busy', str(exc))
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError):
        return error('invalid_request', 'Invalid input or unavailable runtime. Consult the selected record contract.')


def required_args(required):
    if required is None:
        return []
    if not isinstance(required, list) or len(required) > 100 or any(
            not isinstance(x, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,127}', x) for x in required):
        raise ValueError('Required check IDs must be explicit bounded identifiers.')
    return [part for value in required for part in ('--required', value)]


def record_check(operation, record, required=None):
    commands = {'queues': ('queueing.py', []), 'failures': ('failure_analysis.py', []),
        'calculations': ('analyze.py', ['calculations']),
        'function-flow': ('analyze.py', ['functional-graph']),
        'measures': ('measures.py', ['check'])}
    try:
        script, prefix = commands[operation]
        if required and operation in ('function-flow', 'measures'):
            raise ValueError('This operation has no required-ID option.')
        return run(script, {'record.json': encode(record)}, prefix + ['record.json'] + required_args(required))
    except (ValueError, TypeError, KeyError, RecursionError):
        return error('invalid_record', 'Supply a finite JSON record and valid required check IDs.')


def check_sysml(files, *, kind=None, syntax_only=False, review=False, manifest=None, evidence=None):
    try:
        validate_files(files)
        args = model_names(files) + ['--json']
        if kind is not None:
            if kind not in ('concept', 'conops', 'scenario'):
                raise ValueError('Unknown draft kind.')
            args += ['--kind', kind]
        if syntax_only:
            args += ['--syntax-only']
        if review:
            args += ['--review']
        for option, name in (('--manifest', manifest), ('--evidence', evidence)):
            if name is not None:
                args += [option, named(files, name, '.json')]
        return run('sysml.py', files, args)
    except (ValueError, TypeError, KeyError):
        return error('invalid_request', 'Supply model files and only explicitly named companion inputs.')


def scoped_review(operation, files, scope, scope_sha256, sources=None):
    try:
        validate_files(files)
        if not re.fullmatch(r'[a-f0-9]{64}', scope_sha256):
            raise ValueError('Retain the independently selected scope SHA-256.')
        args = ['check', *model_names(files), '--scope', named(files, scope, '.json'),
                '--scope-sha256', scope_sha256, '--json']
        if operation == 'concept':
            if not isinstance(sources or {}, dict) or len(sources or {}) > 24:
                raise ValueError('Supply a bounded explicit source binding map.')
            for identity, name in (sources or {}).items():
                if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', identity):
                    raise ValueError('Invalid source identity.')
                args += ['--source', identity + '=' + named(files, name)]
        elif sources:
            raise ValueError('Sources apply only to concept review.')
        return run({'concept': 'concept_review.py', 'configuration': 'configuration.py'}[operation], files, args)
    except (ValueError, TypeError, KeyError):
        return error('invalid_scope', 'Supply a retained scope digest, model and explicit source bindings.')
