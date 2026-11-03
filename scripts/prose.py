#!/usr/bin/env python3
"""Check selected budgets on an actual UTF-8 plain-text deliverable."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.prose import MAX_CHARACTERS, check_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--kind', required=True, choices=('procedure', 'description'))
    parser.add_argument('--sentence-words', type=int)
    parser.add_argument('--paragraph-words', type=int)
    parser.add_argument('--document-words', type=int)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        if args.file.suffix.lower() not in ('.txt', '.md'):
            raise ValueError('Only plain UTF-8 .txt or .md files are supported; extract rendered text first')
        if not args.file.is_file() or args.file.is_symlink():
            raise ValueError('Input must be a regular file, not a symbolic link')
        with args.file.open('rb') as source:
            data = source.read(MAX_CHARACTERS * 4 + 1)
        if len(data) > MAX_CHARACTERS * 4:
            raise ValueError('Input exceeds the byte analysis limit')
        report = check_text(data.decode('utf-8'), kind=args.kind,
            sentence_words=args.sentence_words, paragraph_words=args.paragraph_words,
            document_words=args.document_words)
    except (OSError, UnicodeError, ValueError) as exc:
        report = {'status': 'error', 'error': str(exc), 'findings': []}
    report['file'] = str(args.file.resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{report['status']}: {report['file']} {report.get('counts', {})}")
        for item in report['findings']:
            print(f"{item['line']}:{item['column']} {item['rule']}: {item['count']} words > {item['limit']}")
        if report.get('findings_truncated'):
            print(f"Showing {report['returned_findings']} of {report['total_findings']} findings; status remains fail.")
        if 'error' in report:
            print(report['error'])
    return {'pass': 0, 'fail': 1}.get(report['status'], 2)


if __name__ == '__main__':
    sys.exit(main())
