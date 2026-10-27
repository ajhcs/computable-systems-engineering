#!/usr/bin/env python3
"""Check the retained C/D/E derivative contracts without rendering or reparsing."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'examples/ecosystem-diagram-reference'
sys.path.insert(0, str(BASE / 'tools'))
from cases import KEYS, require_case, require_release_scope
from source_check import validate_source
from presentation_check import validate_presentations
from reference_media import inspect_svg, inspect_png


def validate(root=BASE):
    root = Path(root)
    require_release_scope(root)
    try:
        source = validate_source(root)
        presentations = validate_presentations(root)
    except (KeyError, TypeError, StopIteration, ET.ParseError) as exc:
        raise ValueError(f'Malformed retained derivative contract: {exc}') from exc
    for key in KEYS:
        inspect_svg(root / 'rendered' / (key + '.svg'), root / 'fonts/font-source.json', root / 'fonts/LICENSE.txt', root / 'fonts')
        if inspect_png(root / 'rendered' / (key + '.png'))['metadata']:
            raise ValueError('PNG contains unreviewed embedded metadata: ' + key)
    manifest = json.loads((root / 'validation/artifacts.json').read_text())
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.suffix != '.pyc'
              and p != root / 'validation/artifacts.json'}
    if actual != set(manifest['sha256']):
        raise ValueError('Incomplete or extra curated artifact inventory')
    for name, digest in manifest['sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed curated artifact: ' + name)
    return {
        'status': 'pass', 'views': len(presentations), 'included_cases': list(KEYS),
        'source_and_geometry_assertions': source['source_and_geometry_assertions'],
        'presentations': presentations,
        'fresh_parser_run': 'not_run', 'fresh_browser_render': 'not_run',
        'limits': 'Checks retained derivative ledgers, recorded linked facts, SVG geometry and exact supplied artifacts; no fresh source acquisition, source authenticity, simulation, full migration, native editor round-trip or engineering acceptance.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='Require an included case; the complete C/D/E pack is still checked')
    parser.add_argument('--receipt', type=Path, help='Create a new receipt outside the curated reference directory; existing files and symlinks are preserved')
    args = parser.parse_args()
    try:
        if args.case:
            require_case(args.case)
        if args.receipt:
            requested = args.receipt.expanduser()
            # Canonicalize the parent for the curated-directory boundary, but
            # never dereference the final name (including a dangling symlink).
            receipt = requested.parent.resolve(strict=True) / requested.name
            if receipt == BASE or BASE in receipt.parents:
                raise ValueError('Receipt must be outside the curated reference directory')
        result = validate()
        if args.receipt:
            # Exclusive creation also rejects a file/symlink created after the
            # directory check. Do not replace or truncate an existing output.
            with receipt.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(result, indent=2) + '\n')
    except (ValueError, KeyError, OSError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in result.items() if k != 'presentations'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
