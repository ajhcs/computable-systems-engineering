"""Bounded reads of exact authoritative SysML bytes; no second model or verdict."""
from hashlib import sha256

from .composition_edit import EditError


def files(document):
    return [{'file': name, 'sha256': sha256(text.encode('utf-8')).hexdigest(), 'codepoints': len(text)}
            for name, text in sorted(document.files.items())]


def chunk(document, file, offset, limit):
    if (not isinstance(file, str) or file not in document.files or type(offset) is not int or offset < 0
            or type(limit) is not int or not 1 <= limit <= 65536):
        raise EditError('input', 'Choose an existing model file, nonnegative codepoint offset and limit 1 through 65536')
    text = document.files[file]
    if offset > len(text):
        raise EditError('input', 'Source offset exceeds the exact file')
    end = min(len(text), offset+limit)
    value = text[offset:end]
    return {'file': file, 'file_sha256': sha256(text.encode('utf-8')).hexdigest(),
            'file_codepoints': len(text), 'offset': offset, 'offset_units': 'unicode_codepoints',
            'text': value, 'chunk_sha256': sha256(value.encode('utf-8')).hexdigest(),
            'next_offset': end if end < len(text) else None, 'encoding': 'utf-8',
            'bundle_sha256': document.revision, 'claim': 'exact_source_read_not_engineering_acceptance'}
