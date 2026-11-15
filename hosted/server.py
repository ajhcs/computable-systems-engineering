"""Stateless Streamable HTTP MCP service for the existing engineering runtime."""
import json
import os
from pathlib import Path
import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict

from mcp.server import MCPServer
from mcp import types
from starlette.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings

from hosted import runtime as rt


class ResultSchema(BaseModel):
    model_config = ConfigDict(extra='allow')
    status: Literal['pass', 'fail', 'unknown', 'unsupported', 'error', 'incomplete']


Result = Annotated[types.CallToolResult, ResultSchema]

server = MCPServer('Computable Systems Engineering', version=json.loads((rt.ROOT / 'plugin.json').read_text())['version'],
    instructions='Use get_engineering_guidance for the selected workflow and read only its needed references. '
    'Submit explicit model text and separately retained scope. Results preserve checker limits; '
    'generated tests are synthetic and no result establishes engineering acceptance. '
    'The service is stateless: return edited source and evidence to the user for retention.',
    log_level='WARNING')
READ = types.ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                             idempotentHint=True, openWorldHint=False)
COMPUTE = types.ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                                idempotentHint=True, openWorldHint=False)


def result(value):
    return types.CallToolResult(content=[types.TextContent(type='text', text=rt.encode(value))],
        structuredContent=value, isError=value.get('status') in ('error', 'incomplete'))


@server.tool(annotations=READ)
def get_engineering_guidance(skill: str) -> Result:
    """Read one of CSE's eleven engineering workflows, or obtain exact skill names for an unknown name."""
    return result(rt.guidance(skill))


@server.tool(annotations=READ)
def read_engineering_reference(path: str) -> Result:
    """Read a public Markdown contract named by a skill, using its packaged skills/ or docs/ path."""
    return result(rt.references(path))


@server.tool(annotations=COMPUTE)
def check_sysml_model(files: dict[str, str], kind: Literal['concept', 'conops', 'scenario'] | None = None,
        syntax_only: bool = False, review: bool = False, manifest: str | None = None,
        evidence: str | None = None) -> Result:
    """Parse supplied SysML v2 files and run the existing bounded CSE checks. files maps flat names to exact UTF-8 text, including any sibling .english.json profiles. Name retained manifest/evidence files explicitly. Syntax checks do not execute behavior; required reviews retain independent scope and supplied observations."""
    return result(rt.check_sysml(files, kind=kind, syntax_only=syntax_only, review=review,
                                manifest=manifest, evidence=evidence))


@server.tool(annotations=COMPUTE)
def review_system_concept(files: dict[str, str], scope: str, scope_sha256: str,
        sources: dict[str, str] | None = None) -> Result:
    """Review explicit concept coverage against the engineer's retained scope and its SHA-256. Supply all model/scope/source texts in files and explicit source-ID to filename bindings. The caller selects scope; this operation never accepts or invents obligations."""
    return result(rt.scoped_review('concept', files, scope, scope_sha256, sources))


@server.tool(annotations=COMPUTE)
def review_system_configuration(files: dict[str, str], scope: str,
        scope_sha256: str) -> Result:
    """Reconcile supplied SysML configuration against separately retained scope bytes and digest. Return existing architecture findings without changing the model or accepting a design."""
    return result(rt.scoped_review('configuration', files, scope, scope_sha256))


@server.tool(annotations=COMPUTE)
def analyze_engineering_queue(record: dict, required: list[str] | None = None) -> Result:
    """Analyze a declared finite FCFS workload or conditional M/M/c queue using the existing queue record contract. Retain independently selected required IDs; do not infer distributions or staffing suitability."""
    return result(rt.record_check('queues', record, required))


@server.tool(annotations=COMPUTE)
def analyze_system_failures(record: dict, required: list[str] | None = None) -> Result:
    """Check a declared Boolean fault tree, shared events and linked FMEA consistency. Quantitative results require explicit probabilities and independence/mission assumptions. Preserve required fault_tree, probability or fmea checks."""
    return result(rt.record_check('failures', record, required))


@server.tool(annotations=COMPUTE)
def check_engineering_calculations(record: dict, required: list[str] | None = None) -> Result:
    """Check declared equations and units using the CSE calculation record contract and selected required check IDs. No arbitrary code, source URL fetching or inferred physical validity."""
    return result(rt.record_check('calculations', record, required))


@server.tool(annotations=COMPUTE)
def check_function_flow(record: dict) -> Result:
    """Check an explicitly authored functional graph against the existing bounded graph contract. A graph-only result does not establish native SysML correspondence or observed operation."""
    return result(rt.record_check('function-flow', record))


@server.tool(annotations=COMPUTE)
def check_measure_definition(record: dict) -> Result:
    """Check a supplied versioned engineering measure definition, including its declared units, population and conditions. The engineer supplies metric meaning and thresholds."""
    return result(rt.record_check('measures', record))


@server.tool(annotations=COMPUTE)
def check_finite_model(record: dict, review: bool = False, manifest: dict | None = None,
        evidence: dict | None = None) -> Result:
    """Run the existing opt-in version-2 finite verifier on an authored model. Required review needs independently selected scope and evidence; finite caps and unsupported predicates remain explicit non-successes."""
    try:
        files = {'model.json': rt.encode(record)}
        args = ['model.json', '--json', '--assignment-cap', '10000', '--state-cap', '10000']
        if review:
            args += ['--review']
        for flag, name, value in (('--manifest', 'manifest.json', manifest), ('--evidence', 'evidence.json', evidence)):
            if value is not None:
                files[name] = rt.encode(value)
                args += [flag, name]
        return result(rt.run('verify.py', files, args))
    except (ValueError, TypeError, RecursionError):
        return result(rt.error('invalid_record', 'Supply finite JSON records.'))


@server.tool(annotations=COMPUTE)
def check_engineering_prose(text: str, kind: Literal['procedure', 'description'],
        sentence_words: int, paragraph_words: int, document_words: int) -> Result:
    """Check actual delivered UTF-8 prose against caller-selected word budgets. This lexical check does not establish STE conformance or preserve meaning without human review."""
    limits = (sentence_words, paragraph_words, document_words)
    if any(type(n) is not int or not 1 <= n <= 1_000_000 for n in limits):
        return result(rt.error('invalid_budget', 'Provide explicit positive word budgets up to 1000000.'))
    return result(rt.run('prose.py', {'report.txt': text}, ['report.txt', '--json', '--kind', kind,
        '--sentence-words', str(sentence_words), '--paragraph-words', str(paragraph_words),
        '--document-words', str(document_words)]))


@server.tool(annotations=COMPUTE)
def generate_property_tests(files: dict[str, str], manifest: str | None = None) -> Result:
    """Generate bounded synthetic variable-influence test pairs from supported SysML clauses. Generated pass/fail witnesses are not captured system observations."""
    try:
        rt.validate_files(files)
        args = rt.model_names(files) + ['--json', '--max-rows', '16', '--evaluation-cap', '1000']
        if manifest is not None:
            args += ['--manifest', rt.named(files, manifest, '.json')]
        return result(rt.run('sysml_testgen.py', files, args))
    except (ValueError, TypeError):
        return result(rt.error('invalid_request', 'Supply model text and an explicitly named manifest.'))


@server.tool(annotations=COMPUTE)
def read_model_context(files: dict[str, str], native_name: str) -> Result:
    """Read one exact native SysML identity and its bounded context from supplied source. A context view does not narrow retained review obligations."""
    try:
        rt.validate_files(files)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_:]{0,255}', native_name):
            raise ValueError('Supply an exact qualified native name.')
        return result(rt.run('sysml_view.py', files, rt.model_names(files) +
            ['--native-name', native_name, '--context', '--compact', '--limit', '32', '--max-bytes', '200000']))
    except (ValueError, TypeError):
        return result(rt.error('invalid_request', 'Supply model text and an exact native identity.'))


@server.tool(annotations=COMPUTE)
def render_function_tree(files: dict[str, str], view: str, target_width: int = 2400) -> Result:
    """Render a declared SysML function-tree view as editable SVG/HTML and source receipts. Return generated UTF-8 files inline; no stored public links. Other diagram families remain assistant-authored views with their own source-fidelity review."""
    try:
        rt.validate_files(files)
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', view):
            raise ValueError('Supply the existing view ID.')
        if type(target_width) is not int or not 320 <= target_width <= 8192:
            raise ValueError('Target width must be 320..8192 pixels.')
        return result(rt.run('sysml_present.py', files, rt.model_names(files) +
            ['--view', view, '--target-width', str(target_width), '--output', 'output'], artifacts=True))
    except (ValueError, TypeError):
        return result(rt.error('invalid_view', 'Select an existing declared view ID.'))


@server.tool(annotations=COMPUTE)
def search_engineering_components(query: str, limit: int = 6,
        cursor: str | None = None) -> Result:
    """Find a bounded shortlist of engineering artwork by concept, with exact IDs and a revision-bound cursor. Catalog artwork does not create engineering model meaning."""
    if len(query) > 256 or type(limit) is not int or not 1 <= limit <= 50 or (cursor and len(cursor) > 2048):
        return result(rt.error('search_limit', 'Use a query up to 256 characters and a limit of 1..50.'))
    args = ['list', '--query', query, '--limit', str(limit)]
    if cursor:
        args += ['--cursor', cursor]
    return result(rt.run('icons.py', {'request.json': '{}'}, args))


@server.tool(annotations=COMPUTE)
def inspect_engineering_component(component_id: str) -> Result:
    """Read provenance, treatment and modeling context for one exact artwork ID before selection or export."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,199}', component_id):
        return result(rt.error('invalid_id', 'Supply an exact catalog component ID.'))
    return result(rt.run('icons.py', {'request.json': '{}'}, ['show', component_id]))


@server.tool(annotations=COMPUTE)
def export_engineering_components(component_ids: list[str], catalog_sha256: str,
        format: Literal['svg', 'drawio']) -> Result:
    """Export 1..8 exact artwork IDs from the previously inspected catalog revision as editable SVG or Draw.io library files returned inline. IDs refer to artwork, independently of engineering-model IDs."""
    if not 1 <= len(component_ids) <= 8 or len(set(component_ids)) != len(component_ids) or any(
            not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,199}', n) for n in component_ids):
        return result(rt.error('invalid_selection', 'Select 1..8 distinct exact component IDs.'))
    selection = {'schema': 'cse.component-selection/1', 'catalog_sha256': catalog_sha256,
                 'component_ids': component_ids}
    return result(rt.run('icons.py', {'selection.json': rt.encode(selection)},
        ['export', '--format', format, '--selection', 'selection.json', '--out', 'output'], artifacts=True))


@server.custom_route('/health', methods=['GET'])
async def health(request):
    return JSONResponse({'status': 'ok', 'service': 'computable-systems-engineering',
                         'skills': len(rt.SKILLS), 'persistence': 'none'})


def app():
    return server.streamable_http_app(stateless_http=True, json_response=True,
        max_request_body_size=1_500_000,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
            allowed_hosts=['cse.open-informatics.org', 'container', 'localhost:*', '127.0.0.1:*'],
            allowed_origins=['https://chatgpt.com', 'https://cse.open-informatics.org', 'http://localhost:*']))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app(), host='0.0.0.0', port=int(os.environ.get('PORT', '8080')),
                access_log=False, log_level='warning')
