"""Explicit release scope; omitted reference cases never pass by being skipped."""
import json
from pathlib import Path

KEYS = ('C-maintenance', 'D-smart-grid', 'E-ape-allocation')
HELD = ('A-bank', 'B-healthcare')


def require_case(key):
    if key in HELD:
        raise ValueError(f'{key} is held: source adaptation rights remain unresolved; no released payload or qualification')
    if key not in KEYS:
        raise ValueError(f'Unsupported ecosystem case: {key}')
    return key


def require_release_scope(root):
    root = Path(root)
    scope = json.loads((root / 'release.json').read_text())
    if scope['included_cases'] != list(KEYS) or scope['held_cases'] != list(HELD):
        raise ValueError('Release scope must explicitly include C/D/E and hold A/B')
    for key in KEYS:
        for folder, suffix in [('models', '.sysml'), ('native', '.facts.json'),
                               ('rendered', '.svg'), ('rendered', '.png'),
                               ('rendered', '.drawio'), ('rendered', '.view.json'),
                               ('source', '.presentation-notes.json')]:
            if not (root / folder / (key + suffix)).is_file():
                raise ValueError(f'Missing required retained case artifact: {folder}/{key}{suffix}')
        if not (root / 'source' / (key[0] + '-ledger.json')).is_file():
            raise ValueError(f'Missing required derivative ledger: {key}')
    for folder in ('models', 'native', 'rendered', 'source'):
        for path in (root / folder).iterdir():
            if path.name.startswith(('A-', 'B-')):
                raise ValueError(f'Held case payload is outside the release scope: {path.name}')
