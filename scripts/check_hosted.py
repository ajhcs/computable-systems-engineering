#!/usr/bin/env python3
"""Exercise hosted tools over actual MCP HTTP using public synthetic fixtures."""
import argparse
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import sys
import urllib.request
import urllib.error

from mcp import Client

ROOT = Path(__file__).resolve().parents[1]


async def check(url):
    observations = []
    def text(name):
        return (ROOT / 'examples' / name).read_text()
    def record(name):
        return json.loads(text(name))
    async with Client(url, read_timeout_seconds=45) as client:
        listing = await client.list_tools()
        advertised = {tool.name for tool in listing.tools}
        assert len(advertised) >= 17
        for tool in listing.tools:
            readonly = tool.name in ('get_engineering_guidance', 'read_engineering_reference')
            assert tool.annotations.read_only_hint == readonly
            assert not tool.annotations.open_world_hint and not tool.annotations.destructive_hint
            assert tool.output_schema['type'] == 'object'
            assert 'status' in tool.output_schema['required']
        async def call(name, arguments, expected='pass'):
            reply = await client.call_tool(name, arguments)
            value = reply.structured_content
            assert isinstance(value, dict), (name, reply)
            assert value['status'] == expected, (name, value)
            assert reply.is_error == (expected in ('error', 'incomplete')), (name, reply)
            observations.append({'tool': name, 'status': expected})
            print('PASS', name, expected, flush=True)
            return value
        await call('get_engineering_guidance', {'skill': 'develop-system-concept'})
        await call('read_engineering_reference', {'path': 'docs/queue-analysis.md'})
        await call('read_engineering_reference', {'path': '/etc/passwd'}, 'error')
        await call('check_sysml_model', {'files': {'concept.sysml': text('sysml/concept.sysml')},
                                       'syntax_only': True, 'kind': 'concept'})
        await call('check_sysml_model', {'files': {'../model.sysml': 'package P;'}}, 'error')
        # Keep independently retained exact fixture scope bytes and source bindings.
        concept = {name: text('concept-review/software/' + name)
                   for name in ('concept.sysml', 'scope.json', 'brief.md', 'checks.md')}
        await call('review_system_concept', {'files': concept, 'scope': 'scope.json',
            'scope_sha256': sha256(concept['scope.json'].encode()).hexdigest(),
            'sources': {'BRIEF': 'brief.md', 'CHECKS': 'checks.md'}})
        config = {name: text('configuration-review/' + name)
                  for name in ('current.sysml', 'library.sysml', 'scope.json')}
        await call('review_system_configuration', {'files': config, 'scope': 'scope.json',
            'scope_sha256': sha256(config['scope.json'].encode()).hexdigest()})
        for tool, fixture in [('analyze_engineering_queue', 'queueing/service-pool.json'),
                              ('analyze_system_failures', 'failure-analysis/qualitative.json'),
                              ('check_engineering_calculations', 'calculations/energy-budget.json'),
                              ('check_measure_definition', 'measurement-definitions/request-duration-v1.json'),
                              ('check_finite_model', 'engineering-gallery/water-sampling/finite-scenarios.json')]:
            await call(tool, {'record': record(fixture)})
        await call('analyze_engineering_queue', {'record': record('queueing/service-pool.json'),
                                               'required': ['Missing']}, 'fail')
        await call('check_function_flow', {'record': record('function-flow/order-fulfillment.json')})
        await call('check_function_flow', {'record': {}}, 'unsupported')
        await call('check_engineering_prose', {'text': 'The station records the receipt.',
            'kind': 'description', 'sentence_words': 25, 'paragraph_words': 100, 'document_words': 100})
        await call('generate_property_tests', {'files': {'ack.sysml': text('sysml/ack.sysml')}})
        context = await call('read_model_context', {'files': {'concept.sysml': text('sysml/concept.sysml')},
                                         'native_name': 'ToolLibraryConcept::AllocateTool'}, 'unknown')
        assert context['report']['retrieval_status'] == 'pass'
        await call('render_function_tree', {'files': {'station.sysml': text('engineering-gallery/water-sampling/station.sysml')},
                                           'view': 'FT_STATION'})
        found = await call('search_engineering_components', {'query': 'pump', 'limit': 2})
        component = found['report']['items'][0]['id']
        await call('inspect_engineering_component', {'component_id': component})
        await call('export_engineering_components', {'component_ids': [component],
            'catalog_sha256': found['report']['catalog_sha256'], 'format': 'drawio'})
        await call('export_engineering_components', {'component_ids': [component],
            'catalog_sha256': '0' * 64, 'format': 'svg'}, 'error')
        assert advertised <= {x['tool'] for x in observations}, advertised - {x['tool'] for x in observations}
    return {'status': 'pass', 'url': url, 'tools_exercised': len(advertised), 'observations': observations,
            'scope': 'Synthetic MCP HTTP integration; not ChatGPT-client, deployment or directory approval.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url', default='http://127.0.0.1:8080/mcp')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = asyncio.run(check(args.url))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'observations'}))


if __name__ == '__main__':
    main()
