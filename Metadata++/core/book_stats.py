#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

"""
Metadata++ book-stats header (v6.2.35).

Builds an optional stats header (page count / word count / reading time /
tags) that can be prepended to the synopsis, e.g.:

    Page Count: 344
    Word Count: 103,844
    Reading Time: 08h:39m
    Tags: Young Adult, Mystery, Thriller, Dark Academia, LGBT, Contemporary, Fiction
    -----------------------------

    <synopsis text, unchanged, in whatever language the book is>

WORD COUNT is estimated by opening the book's own EPUB file (if the book
has one) as a zip archive, stripping HTML from every content document,
and counting whitespace-separated tokens. This is a real measurement of
THIS book's actual text, not a guess — but it IS an approximation: it
doesn't respect exact spine reading order or exclude front/back matter
(copyright page, ToC, etc.), so treat it as a close estimate rather than
a certified count. Non-EPUB-only books (pure AZW3/MOBI/PDF with no EPUB
format present) fall back to returning None — parsing those binary/DRM-
prone formats reliably is out of scope here; the header simply omits the
Word Count / Reading Time lines in that case rather than guessing.

PAGE COUNT prefers a real value from a "#pages"-style custom column if one
exists in the library (added by e.g. a page-count plugin), since that's an
actual page count rather than an estimate. Only if no such column is set
does it fall back to estimating from the word count (~275 words/page, a
commonly used approximation for a standard paperback trim size) — and
that fallback is clearly labelled "(est.)" rather than presented as fact.
"""

import re
import zipfile
import html as _html

__all__ = ['get_word_count_from_epub', 'estimate_reading_time',
           'get_page_count', 'build_stats_header']

_TAG_RE = re.compile(r'<[^>]+>')
_SCRIPT_STYLE_RE = re.compile(r'<(script|style)[^>]*>.*?</\1>', re.I | re.S)
_WORD_RE = re.compile(r'\S+')

_PAGE_COUNT_COLUMNS = ('#pages', '#page_count', '#pagecount', '#numpages')


def get_word_count_from_epub(path, log=None):
    """
    Return an estimated word count for the EPUB at `path`, or None if it
    can't be opened/parsed. Reads every .xhtml/.html/.htm entry in the zip
    (skipping obvious nav/toc files), strips tags, and counts tokens.
    """
    try:
        total = 0
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist()
                     if n.lower().endswith(('.xhtml', '.html', '.htm'))
                     and 'nav' not in n.lower().rsplit('/', 1)[-1]]
            for name in names:
                try:
                    raw = z.read(name).decode('utf-8', errors='ignore')
                except Exception:
                    continue
                text = _SCRIPT_STYLE_RE.sub(' ', raw)
                text = _TAG_RE.sub(' ', text)
                text = _html.unescape(text)
                total += len(_WORD_RE.findall(text))
        return total if total > 0 else None
    except Exception as e:
        if log:
            log.debug('get_word_count_from_epub failed for %s: %s', path, e)
        return None


def estimate_reading_time(word_count, wpm=200):
    """Return 'HHh:MMm' for a given word count at `wpm` words/minute."""
    if not word_count:
        return None
    try:
        wpm = int(wpm)
    except Exception:
        wpm = 200
    if wpm <= 0:
        wpm = 200
    total_minutes = int(round(word_count / float(wpm)))
    hours, minutes = divmod(total_minutes, 60)
    return '{:02d}h:{:02d}m'.format(hours, minutes)


def get_page_count(mi, word_count=None):
    """
    Return (page_count, is_estimate). page_count is None if neither a
    custom column nor a word-count-based estimate is available.
    """
    for col in _PAGE_COUNT_COLUMNS:
        try:
            val = mi.get(col, None)
        except Exception:
            val = None
        if val:
            try:
                return int(val), False
            except Exception:
                continue
    if word_count:
        return int(round(word_count / 275.0)), True
    return None, False


def build_stats_header(page_count=None, page_is_estimate=False,
                        word_count=None, reading_time=None, tags=None):
    """
    Build the 'Page Count / Word Count / Reading Time / Tags -----' header
    block, in that fixed field order. Any missing field is simply omitted
    (e.g. no header line for tags if the book has none) rather than shown
    as empty. Returns '' if nothing at all is available.
    """
    lines = []
    if page_count:
        lines.append('Page Count: {}{}'.format(
            page_count, ' (est.)' if page_is_estimate else ''))
    if word_count:
        lines.append('Word Count: {:,}'.format(word_count))
    if reading_time:
        lines.append('Reading Time: {}'.format(reading_time))
    if tags:
        lines.append('Tags: {}'.format(', '.join(tags)))
    if not lines:
        return ''
    lines.append('-----------------------------')
    return '\n'.join(lines)
