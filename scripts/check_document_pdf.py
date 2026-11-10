#!/usr/bin/env python3
"""Inspect an exported PDF against selected font files and rendered resource use.

PyMuPDF is optional: absent/unsupported extraction produces no successful review.
Embedded sfnt names and weights are read with the standard library, not filenames.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys


def sfnt_identity(data):
    """Read a bounded single-font sfnt name and OS/2 table (TrueType/OpenType)."""
    if len(data) < 12 or data[:4] not in (b'\0\1\0\0', b'OTTO', b'true'):
        raise ValueError('embedded font is not a supported single sfnt font')
    count = struct.unpack_from('>H', data, 4)[0]
    if count > 256 or 12 + 16 * count > len(data):
        raise ValueError('invalid sfnt table directory')
    tables = {}
    for index in range(count):
        tag, _, start, size = struct.unpack_from('>4sIII', data, 12 + index * 16)
        if start + size > len(data):
            raise ValueError('sfnt table exceeds embedded font')
        tables[tag] = data[start:start + size]
    names, name = {}, tables.get(b'name', b'')
    if len(name) < 6:
        raise ValueError('embedded font has no readable name table')
    _, count, offset = struct.unpack_from('>HHH', name, 0)
    if count > 4096 or 6 + count * 12 > len(name):
        raise ValueError('invalid sfnt name records')
    for index in range(count):
        platform, _, _, name_id, size, start = struct.unpack_from('>HHHHHH', name, 6 + index * 12)
        if name_id not in (1, 2, 4, 6, 16, 17):
            continue
        if offset + start + size > len(name):
            raise ValueError('sfnt name exceeds table')
        raw = name[offset + start:offset + start + size]
        value = raw.decode('utf-16-be' if platform in (0, 3) else 'mac_roman').strip('\0')
        names.setdefault(str(name_id), [])
        if value not in names[str(name_id)]:
            names[str(name_id)].append(value)
    weight = tables.get(b'OS/2', b'')
    return {'names': names, 'postscript_names': names.get('6', []),
            'families': names.get('16', []) + names.get('1', []),
            'weight': struct.unpack_from('>H', weight, 4)[0] if len(weight) >= 6 else None}


def inspect_pdf(pdf_path, preflight, font_ids=None, expected_pages=None, raster_assets=0, formal_assets=0):
    report = {'schema': 'cse.document-pdf/1', 'status': 'unsupported', 'checks': {}, 'findings': [],
              'method': 'PyMuPDF extraction; standard-library embedded sfnt name and OS/2 table inspection',
              'claim_scope': 'exported_font_identity_and_page_geometry_only'}
    if type(preflight) is not dict or preflight.get('status') != 'pass':
        report.update(status='error', findings=['A successful selected-profile preflight is required.'])
        return report
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        report['findings'].append('PDF inspection requires an existing PyMuPDF installation; no dependency was installed.')
        return report
    try:
        pdf = Path(pdf_path)
        report.update(pdf=str(pdf.resolve()), sha256=hashlib.sha256(pdf.read_bytes()).hexdigest())
        doc = fitz.open(pdf)
        if doc.is_encrypted:
            raise ValueError('encrypted PDF inspection is unsupported')
        fonts, pages, seen, errors = [], [], set(), []
        for page in doc:
            for item in page.get_fonts(full=True):
                xref = item[0]
                if xref in seen:
                    continue
                seen.add(xref)
                try:
                    name, extension, kind, data = doc.extract_font(xref)
                    if not data:
                        raise ValueError('font is not embedded')
                    identity = sfnt_identity(data)
                    fonts.append({'xref': xref, 'pdf_basefont': item[3], 'format': extension,
                                  'embedded_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), **identity})
                except (ValueError, RuntimeError, UnicodeError, struct.error) as error:
                    errors.append(f'Font {item[3]}: {error}')
            spans = [span for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])
                     for span in line.get('spans', []) if span.get('text', '').strip()]
            tolerance = fitz.Rect(page.rect.x0 - 1, page.rect.y0 - 1, page.rect.x1 + 1, page.rect.y1 + 1)
            pages.append({'number': page.number + 1, 'width_pt': page.rect.width, 'height_pt': page.rect.height,
                          'text': page.get_text('text'), 'span_count': len(spans),
                          'text_bounds_inside_page': all(tolerance.contains(fitz.Rect(s['bbox'])) for s in spans),
                          'image_count': len(page.get_images(full=True)), 'drawing_count': len(page.get_drawings())})
        selected = [f for f in preflight['fonts'] if font_ids is None or f['id'] in font_ids]
        match = lambda expected, actual: (actual['weight'] == expected['weight'] and
                    (expected.get('postscript_name') in actual['postscript_names'] if expected.get('postscript_name')
                     else expected['family'] in actual['families']))
        checks = {'pages_present': bool(pages), 'text_present': any(p['span_count'] for p in pages),
                  'fonts_embedded_and_readable': bool(fonts) and not errors,
                  'selected_fonts_embedded': bool(selected) and all(any(match(f, a) for a in fonts) for f in selected),
                  'no_unselected_fonts': all(any(match(f, a) for f in selected) for a in fonts),
                  'text_within_pages': all(p['text_bounds_inside_page'] for p in pages),
                  'requested_page_count': expected_pages is None or len(pages) == expected_pages,
                  'selected_raster_graphics_present': not raster_assets or sum(p['image_count'] for p in pages) >= raster_assets,
                  'formal_vector_content_present': not formal_assets or sum(p['drawing_count'] for p in pages) > 0}
        report.update(status='pass' if all(checks.values()) else 'fail', checks=checks,
                      fonts=fonts, pages=pages, findings=errors, page_count=len(pages),
                      postscript_names=sorted({n for f in fonts for n in f['postscript_names']}),
                      weights=sorted({f['weight'] for f in fonts if f['weight'] is not None}))
        doc.close()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        report.update(status='error')
        report['findings'].append(str(error))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--profile-preflight', required=True)
    parser.add_argument('--output')
    parser.add_argument('--font-ids', help='Comma-separated font IDs actually used by browser glyphs')
    parser.add_argument('--expected-pages', type=int)
    parser.add_argument('--raster-assets', type=int, default=0)
    parser.add_argument('--formal-assets', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        report = inspect_pdf(args.pdf, json.loads(Path(args.profile_preflight).read_text()),
                             args.font_ids.split(',') if args.font_ids is not None else None,
                             args.expected_pages, args.raster_assets, args.formal_assets)
        if args.output:
            with Path(args.output).open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
    except (OSError, ValueError) as error:
        report = {'schema': 'cse.document-pdf/1', 'status': 'error', 'checks': {}, 'findings': [str(error)]}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
