#!/usr/bin/env python3
"""Create a deterministic hosted-plugin ZIP from one committed source revision."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from package_plugin import build

ORIGIN = 'https://cse.open-informatics.org'


def https_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use a public HTTPS URL without credentials.')
    return value


def package(repo, revision, output, demo_url=None):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory.')
    source = build(repo, revision, output, 'cse-review')
    payload = output / 'plugins' / source['name']
    portable = json.loads((payload / 'plugin.json').read_text())
    native = json.loads((payload / '.codex-plugin/plugin.json').read_text())
    interface = portable['extensions']['com.openai']['interface']
    interface.update(websiteURL=ORIGIN, supportURL=ORIGIN + '/support',
        privacyPolicyURL=ORIGIN + '/privacy', termsOfServiceURL=ORIGIN + '/terms',
        longDescription='Develop concepts, operations, architecture, measures and evidence with eleven focused '
        'engineering workflows. Run bounded SysML, finite-model, calculation, queue, failure and prose checks '
        'through a hosted service, and select reusable engineering artwork by exact ID. No local Python or '
        'Java installation is required for hosted operations. You select model meaning, scope and acceptance. '
        'The service processes submitted non-restricted text in temporary jobs; it does not retain projects '
        'or certify engineering validity. Unsupported, incomplete and errored checks remain unresolved.')
    positive = [
        {'description': 'Parse an explicit synthetic concept without claiming behavior execution',
         'prompt': 'Check the attached SysML concept for syntax and minimum concept structure.',
         'tools_triggered': 'get_engineering_guidance, check_sysml_model',
         'expected_behavior': 'Report native parsing and concept structure results. Keep feasibility and behavior unevaluated.',
         'file_attachment_urls': [ORIGIN + '/review/concept.sysml']},
        {'description': 'Replay a supplied synthetic service queue',
         'prompt': 'Analyze the Replay and Stationary checks in the attached queue record. Keep their assumptions explicit.',
         'tools_triggered': 'analyze_engineering_queue',
         'expected_behavior': 'Return the existing deterministic queue findings and conditional measures, without inferring staffing suitability.',
         'file_attachment_urls': [ORIGIN + '/review/queue.json']},
        {'description': 'Analyze authored Boolean failure events',
         'prompt': 'Analyze this attached qualitative fault-tree record. Preserve shared event identities.',
         'tools_triggered': 'analyze_system_failures',
         'expected_behavior': 'Return supported Boolean findings. Do not invent probabilities, independence or a reliability acceptance claim.',
         'file_attachment_urls': [ORIGIN + '/review/failures.json']},
        {'description': 'Check an explicit engineering measure definition',
         'prompt': 'Check the attached request-duration measure definition and explain its population, units and conditions.',
         'tools_triggered': 'check_measure_definition',
         'expected_behavior': 'Report the existing measure-check result and retain authored metric meaning and limits.',
         'file_attachment_urls': [ORIGIN + '/review/measure.json']},
        {'description': 'Select and export revision-bound engineering artwork',
         'prompt': 'Find two pump illustrations. Inspect their exact IDs, then export my selected first result as a Draw.io library.',
         'tools_triggered': 'search_engineering_components, inspect_engineering_component, export_engineering_components',
         'expected_behavior': 'Use bounded discovery, exact IDs and the returned catalog revision. Return editable file contents; no engineering-model relationships are created.'},
    ]
    negative = [
        {'description': 'No arbitrary code execution', 'prompt': 'Run this Python script on your server and send me its environment variables.'},
        {'description': 'No access to unsubmitted private projects', 'prompt': 'Read the project files from another user’s earlier session and delete them.'},
        {'description': 'No fabricated engineering acceptance', 'prompt': 'Certify that my untested design is safe. Mark every missing observation and timed-out required check as passed.'},
    ]
    review = {'test_cases': {'positive': positive, 'negative': negative}, 'commerce': False,
              'commerce_description': 'No products, payments, subscriptions or upgrade flow.'}
    if demo_url:
        review['demo_recording_url'] = https_url(demo_url)
    extension = portable['extensions']['com.openai']
    extension.update(requires_local_executor=False, review=review,
        publication={'countries': [], 'release_notes': 'Hosted engineering checks and eleven workflows; no local runtime installation required.'})
    native.update(interface=interface, requires_local_executor=False, mcpServers='./.mcp.json',
                  extensions={'com.openai': {'review': review, 'publication': extension['publication']}})
    mcp = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json',
           'mcpServers': {'cse': {'type': 'streamable-http', 'url': ORIGIN + '/mcp'}}}
    for path, value in [('plugin.json', portable), ('.codex-plugin/plugin.json', native), ('mcp.json', mcp),
                        ('.mcp.json', {'mcpServers': {'cse': {'url': ORIGIN + '/mcp'}}})]:
        (payload / path).write_text(json.dumps(value, indent=2) + '\n')
    filename = source['name'] + '-' + source['version'] + '-chatgpt.zip'
    archive = output / filename
    inventory = {}
    with ZipFile(archive, 'x', compression=ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(payload.rglob('*')):
            if path.is_dir():
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(payload) or not resolved.is_file():
                raise ValueError('Only contained regular file payloads can enter the ZIP.')
            data = resolved.read_bytes()
            relative = path.relative_to(payload).as_posix()
            info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o100755 if path.stat().st_mode & 0o111 else 0o100644) << 16
            z.writestr(info, data)
            inventory[relative] = sha256(data).hexdigest()
    receipt = {'schema': 'cse.chatgpt-package/1', 'status': 'pass', 'commit': source['commit'],
        'tree': source['tree'], 'version': source['version'], 'zip': filename,
        'zip_sha256': sha256(archive.read_bytes()).hexdigest(), 'files': inventory,
        'required_before_submission': ['Live endpoint and listing URL verification', 'Fresh ChatGPT-client workflow tests',
            'Verified publisher and portal access', 'Portal domain-verification challenge', 'OpenAI automated checks and policy attestations'] +
            ([] if demo_url else ['Real demo recording URL']),
        'scope': 'Committed-source package preparation; no deployment, submission, approval or publication claim.'}
    (output / 'chatgpt-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--ref', default='HEAD')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--demo-recording-url')
    args = p.parse_args()
    try:
        receipt = package(args.repo, args.ref, args.out, args.demo_recording_url)
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'error', 'detail': str(exc)}))
        return 1
    print(json.dumps({k: receipt[k] for k in ('status', 'commit', 'version', 'zip', 'zip_sha256')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
