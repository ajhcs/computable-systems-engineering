#!/usr/bin/env python3
"""Create an offline documentary function-tree presentation from native SysML."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.visual_projection import PresentationError, write_presentation
from verifier.visual_style import load_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', nargs='+')
    parser.add_argument('--view', required=True)
    parser.add_argument('--output', required=True, help='new output directory (must not exist)')
    parser.add_argument('--profile', help='validated presentation style JSON')
    parser.add_argument('--body', choices=('paper', 'white', 'tint'), default='paper')
    parser.add_argument('--target-width', type=int, default=1200)
    parser.add_argument('--show-ids', action='store_true', help='show view ID and node IDs/levels after native names (hidden by default)')
    args = parser.parse_args()
    try:
        report = write_presentation(args.model, args.output, view_id=args.view,
                                    profile=load_profile(args.profile), body=args.body,
                                    target_width=args.target_width, show_ids=args.show_ids)
    except PresentationError as exc:
        report = exc.report
    except (OSError, ValueError, KeyError) as exc:
        report = {'status': 'error', 'findings': [{'code': 'presentation', 'detail': str(exc)}]}
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
