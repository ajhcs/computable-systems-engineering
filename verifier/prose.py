"""Read-only, lexical prose budgets. These are CSE checks, not STE conformance."""
from hashlib import sha256
from bisect import bisect_right
import re

VERSION = 'prose-1.0'
MAX_CHARACTERS = 1_000_000
MAX_FINDINGS = 100
SNIPPET_CHARACTERS = 240


def check_text(text, *, kind, sentence_words=None, paragraph_words=None,
               document_words=None):
    """Count every non-whitespace token; never remove quotations or identifiers."""
    report = {'checker_version': VERSION, 'status': 'error',
              'claim_scope': 'selected_lexical_prose_budgets', 'kind': kind,
              'limits': {'sentence_words': sentence_words,
                         'paragraph_words': paragraph_words,
                         'document_words': document_words},
              'counts': {}, 'findings': [], 'total_findings': 0,
              'returned_findings': 0, 'findings_truncated': False,
              'diagnostic_limits': {'findings': MAX_FINDINGS,
                                    'snippet_characters': SNIPPET_CHARACTERS}}

    def finding(rule, start, end, count, limit):
        report['total_findings'] += 1
        if len(report['findings']) >= MAX_FINDINGS:
            report['findings_truncated'] = True
            return
        line_index = bisect_right(line_starts, start) - 1
        report['findings'].append({'rule': rule, 'start': start, 'end': end,
            'line': line_index + 1, 'column': start - line_starts[line_index] + 1,
            'count': count, 'limit': limit,
            'text': text[start:min(end, start + SNIPPET_CHARACTERS)],
            'text_truncated': end - start > SNIPPET_CHARACTERS})

    try:
        if kind not in ('procedure', 'description'):
            raise ValueError('kind must be procedure or description')
        limits = (sentence_words, paragraph_words, document_words)
        if all(limit is None for limit in limits):
            raise ValueError('Select at least one explicit word budget')
        if any(limit is not None and (type(limit) is not int or limit < 1)
               for limit in limits):
            raise ValueError('Word budgets must be positive integers')
        if type(text) is not str or not text.strip():
            raise ValueError('Input must be nonempty text')
        if len(text) > MAX_CHARACTERS:
            raise ValueError('Input exceeds the 1000000-character analysis limit')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in text):
            raise ValueError('Input contains non-text control characters')
        report['text_sha256'] = sha256(text.encode('utf-8')).hexdigest()
        line_starts = [0] + [match.end() for match in re.finditer('\n', text)]
        tokens = list(re.finditer(r'\S+', text))
        if document_words is not None and len(tokens) > document_words:
            finding('CSE-PROSE-DOCUMENT', tokens[0].start(), tokens[-1].end(),
                    len(tokens), document_words)
        paragraphs = list(re.finditer(r'\S(?:.*?\S)?(?=\r?\n[ \t]*\r?\n|\Z)',
                                      text, re.S))
        sentences = 0
        for paragraph in paragraphs:
            body = paragraph.group()
            count = len(re.findall(r'\S+', body))
            if paragraph_words is not None and count > paragraph_words:
                finding('CSE-PROSE-PARAGRAPH', paragraph.start(), paragraph.end(),
                        count, paragraph_words)
            # Only punctuation at a token boundary ends a sentence. Decimal
            # points and internal identifier punctuation do not split tokens.
            for sentence in re.finditer(r'\S.*?(?:[.!?][\"\u201d\u2019\)\]]*(?=\s|\Z)|\Z)', body, re.S):
                start = paragraph.start() + sentence.start()
                end = paragraph.start() + sentence.end()
                count = len(re.findall(r'\S+', sentence.group()))
                sentences += 1
                if sentence_words is not None and count > sentence_words:
                    finding('CSE-PROSE-SENTENCE', start, end, count, sentence_words)
        report['counts'] = {'words': len(tokens), 'paragraphs': len(paragraphs),
                            'sentences': sentences}
        report['returned_findings'] = len(report['findings'])
        report['status'] = 'fail' if report['total_findings'] else 'pass'
    except (ValueError, UnicodeError) as exc:
        report['error'] = str(exc)
    return report
