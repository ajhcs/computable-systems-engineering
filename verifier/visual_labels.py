"""Explicit, native-element-bound presentation wording; never model renaming."""
from copy import deepcopy
import json
from pathlib import Path

from .engineering_views import ID
from .visual_style import require_supported_text


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate label JSON key: {key}")
        result[key] = value
    return result


def load_labels(value=None):
    """Validate a label dictionary or JSON file; None selects exact native names."""
    if value is None:
        return None
    if isinstance(value, (str, Path)):
        value = json.loads(Path(value).read_text(), object_pairs_hook=_unique,
                           parse_constant=lambda text: (_ for _ in ()).throw(ValueError(f"Nonfinite {text}")))
    if not isinstance(value, dict) or set(value) != {"version", "view", "title", "labels"}:
        raise ValueError("Labels need exactly version, view, title and labels")
    if type(value['version']) is not int or value['version'] != 1:
        raise ValueError("Expected presentation labels version 1")
    if not isinstance(value['view'], str) or not ID.fullmatch(value['view']):
        raise ValueError("Labels need a supported view ID")
    require_supported_text(value['title'])
    if not value['title'].strip() or not isinstance(value['labels'], list):
        raise ValueError("Labels need a nonempty title and a labels list")
    seen = set()
    for label in value['labels']:
        if not isinstance(label, dict) or set(label) != {'element', 'text'}:
            raise ValueError("Each display label needs exactly element and text")
        for field in ('element', 'text'):
            require_supported_text(label[field])
            if not label[field].strip():
                raise ValueError(f"Display label {field} cannot be blank")
        if label['element'] in seen:
            raise ValueError("Repeated display label native element: " + label['element'])
        seen.add(label['element'])
    return deepcopy(value)


def apply_labels(projection, value=None):
    """Return separate wording, preserving the checked projection byte for byte."""
    record = load_labels(value)
    if record is not None and record['view'] != projection['id']:
        raise ValueError("Display labels select a different view")
    nodes = projection['nodes']
    by_element, node_ids, labels = {}, set(), {}
    for node in nodes:
        element, node_id = node['element'], node['id']
        if element in by_element or node_id in node_ids:
            raise ValueError("Presentation requires unique native bindings and node IDs")
        require_supported_text(element)
        require_supported_text(node['text'])
        by_element[element] = node_id
        node_ids.add(node_id)
        labels[node_id] = node['text']
    bindings = [] if record is None else record['labels']
    for binding in bindings:
        if binding['element'] not in by_element:
            raise ValueError("Display label binds outside the selected native view: " + binding['element'])
        labels[by_element[binding['element']]] = binding['text']
    return {'title': 'Function decomposition' if record is None else record['title'],
            'labels': labels, 'bindings': deepcopy(bindings)}
