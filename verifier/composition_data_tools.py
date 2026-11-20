"""Model-facing physical composition tools backed by a granted native project."""
from base64 import b64encode
from hashlib import sha256
from uuid import UUID

from scripts import component_agent

from .composition_edit import EditError
from .composition_inspection import page, project as inspect_document
from .composition_removal_views import physical_view_ids
from .composition_source import chunk, files
from .composition_view import project as project_view


CATALOG_READS = {
    'catalog_search': {'query', 'family', 'sysml', 'limit', 'cursor'},
    'catalog_inspect': {'component_id', 'catalog_sha256', 'include_svg'},
    'catalog_selection': {'schema', 'catalog_sha256', 'component_ids'},
}


def catalog_read(operation, payload):
    """Read the same component catalog and exact records as the artwork CLI."""
    fields = CATALOG_READS.get(operation)
    if fields is None or not isinstance(payload, dict) or payload.keys() != fields:
        raise EditError('input', 'Supply the documented component catalog fields')
    try:
        if operation == 'catalog_selection':
            component_agent.validate_selection(payload)
            return payload
        if operation == 'catalog_search':
            for key, maximum in (('family', 256), ('sysml', 256), ('cursor', 2048)):
                value = payload[key]
                if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= maximum):
                    raise EditError('input', f'Use bounded text or null for {key}')
            return component_agent.search(**payload)

        if type(payload['include_svg']) is not bool:
            raise EditError('input', 'Choose whether this exact read includes SVG artwork')
        root = component_agent.library.LIBRARY.resolve()
        expected = payload['catalog_sha256']
        if expected != component_agent.revision(root):
            raise EditError('stale_catalog', 'Repeat discovery before inspecting the component')
        result = component_agent.describe(payload['component_id'], root)
        if result['catalog_sha256'] != expected:
            raise EditError('stale_catalog', 'Repeat discovery before inspecting the component')
        if payload['include_svg']:
            component = result['component']
            path = (root / component['file']).resolve()
            if not path.is_relative_to(root) or path.suffix != '.svg':
                raise EditError('artifact_error', 'The catalog entry does not name a local SVG')
            with path.open('rb') as stream:
                raw = stream.read(65537)
            if len(raw) > 65536 or sha256(raw).hexdigest() != component['sha256']:
                raise EditError('artifact_error', 'The catalog SVG bytes do not match the admitted artwork')
            result['svg_base64'] = b64encode(raw).decode('ascii')
        return result
    except component_agent.RequestError as exc:
        raise EditError(exc.code, str(exc)) from exc


class CompositionDataTools:
    """A trusted host supplies the allowed project for each read or write.

    The resolver returns a project only after checking the verified request
    principal's read grant. No tool argument supplies a path or a principal.
    Preview uses the existing native verifier and returns an unsaved result.
    """

    def __init__(self, resolve_project):
        self._resolve_project = resolve_project

    def _snapshot(self, project_id):
        if not isinstance(project_id, str):
            raise EditError('input', 'Choose an exact project UUID')
        try:
            canonical = str(UUID(project_id))
        except ValueError as exc:
            raise EditError('input', 'Choose an exact project UUID') from exc
        if project_id != canonical:
            raise EditError('input', 'Choose an exact project UUID')
        project = self._resolve_project(project_id)
        if project is None:
            raise EditError('project_grant', 'No grant for this project operation')
        # Check the trusted mapping against the stored native identity before
        # exposing any bytes.
        snapshot = project.snapshot()
        if snapshot['document'].project_id != project_id:
            raise EditError('project_grant', 'No grant for this project operation')
        return project, snapshot

    @staticmethod
    def _identity(snapshot):
        document = snapshot['document']
        return {'project_id': document.project_id, 'revision': snapshot['revision'],
                'commit': snapshot['commit'], 'bundle_sha256': document.revision}

    def _bound(self, project_id, revision, bundle_sha256):
        _, snapshot = self._snapshot(project_id)
        identity = self._identity(snapshot)
        if (type(revision) is not int or revision != identity['revision']
                or bundle_sha256 != identity['bundle_sha256']):
            raise EditError('stale_revision', 'Read the current project snapshot before inspecting it')
        return snapshot, identity

    def snapshot(self, project_id):
        _, snapshot = self._snapshot(project_id)
        document = snapshot['document']
        return {**self._identity(snapshot), 'view_ids': physical_view_ids(document),
                'model_sources': files(document),
                'retained_reviews': [{'file': review['file'], 'scope_sha256': review['scope_sha256'],
                    'status': review['report']['status'], 'finding_count': len(review['report']['findings'])}
                    for review in document.configuration_reviews]}

    def occurrences(self, project_id, revision, bundle_sha256, view_id, *, origin=None, offset=0, limit=25):
        snapshot, identity = self._bound(project_id, revision, bundle_sha256)
        document = snapshot['document']
        if view_id is None:
            inspection = inspect_document(document, None, {})
        elif isinstance(view_id, str) and view_id in physical_view_ids(document):
            inspection = project_view(document, view_id)['inspection']
        else:
            raise EditError('view_unavailable', 'The saved physical view is unavailable')
        return {**identity, 'inspection_page': page(inspection, origin=origin, offset=offset,
                    limit=limit, expected_bundle_sha256=bundle_sha256)}

    def source(self, project_id, revision, bundle_sha256, file, offset, limit):
        snapshot, identity = self._bound(project_id, revision, bundle_sha256)
        return {**identity, **chunk(snapshot['document'], file, offset, limit)}

    def retained_review(self, project_id, revision, bundle_sha256, file, scope_sha256, *, offset=0, limit=25):
        snapshot, identity = self._bound(project_id, revision, bundle_sha256)
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise EditError('input', 'Use a nonnegative finding offset and limit from 1 through 100')
        document = snapshot['document']
        review = next((row for row in document.configuration_reviews if row['file'] == file), None)
        if review is None or scope_sha256 != review['scope_sha256']:
            raise EditError('scope_unavailable', 'Choose the exact retained scope from this snapshot')
        report = review['report']
        findings = report['findings']
        if offset > len(findings):
            raise EditError('input', 'The finding offset exceeds this retained report')
        end = min(len(findings), offset + limit)
        return {**identity, 'file': file, 'scope_sha256': scope_sha256,
                'status': report['status'], 'checked': report['checked'], 'offset': offset,
                'findings': findings[offset:end], 'total_findings': len(findings),
                'next_offset': end if end < len(findings) else None,
                'claim': 'page_of_existing_retained_review_with_unchanged_scope'}

    def preview(self, project_id, request):
        project, snapshot = self._snapshot(project_id)
        candidate = project.preview(request)
        document = candidate['document']
        # The native revision is authoritative. Bind this response to the
        # captured project grant before returning any candidate details.
        if snapshot['commit'] != candidate['base_commit'] or document.project_id != project_id:
            raise EditError('stale_revision', 'Project changed before candidate inspection')
        return {key: value for key, value in candidate.items() if key != 'document'} | {
            'project_id': project_id, 'candidate_bundle_sha256': document.revision,
            'configuration_review_identities': [
                {'file': row['file'], 'scope_sha256': row['scope_sha256'], 'status': row['report']['status']}
                for row in document.configuration_reviews],
        }

    def lookup_receipt(self, project_id, request):
        project, _ = self._snapshot(project_id)
        return {'project_id': project_id, **project.lookup_receipt(request)}
