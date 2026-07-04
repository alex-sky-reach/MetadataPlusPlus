#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""ISBN validation, repair, and conversion utilities."""

import re


def _strip(isbn):
    return re.sub(r'[\s\-]', '', isbn or '')


def check_isbn10(isbn):
    s = _strip(isbn)
    if len(s) != 10:
        return False
    total = 0
    for i, c in enumerate(s[:-1]):
        if not c.isdigit():
            return False
        total += int(c) * (10 - i)
    check = s[-1]
    check_val = 10 if check in ('x', 'X') else (int(check) if check.isdigit() else -1)
    if check_val < 0:
        return False
    return (total + check_val) % 11 == 0


def check_isbn13(isbn):
    s = _strip(isbn)
    if len(s) != 13 or not s.isdigit():
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s[:-1]))
    check = (10 - (total % 10)) % 10
    return check == int(s[-1])


def is_valid_isbn(isbn):
    s = _strip(isbn)
    if len(s) == 10:
        return check_isbn10(s)
    if len(s) == 13:
        return check_isbn13(s)
    return False


def isbn10_to_13(isbn10):
    s = _strip(isbn10)
    if len(s) != 10:
        return None
    base = '978' + s[:-1]
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base))
    check = (10 - (total % 10)) % 10
    return base + str(check)


def isbn13_to_10(isbn13):
    s = _strip(isbn13)
    if len(s) != 13 or not s.startswith('978'):
        return None
    base = s[3:12]
    total = sum(int(c) * (10 - i) for i, c in enumerate(base))
    check = (11 - (total % 11)) % 11
    return base + ('X' if check == 10 else str(check))


def repair_isbn(isbn):
    """
    Try to repair a malformed ISBN string.
    Returns (repaired_isbn, was_repaired) or (None, False) if unrepairable.
    """
    if not isbn:
        return None, False
    s = _strip(isbn)
    # Already valid?
    if is_valid_isbn(s):
        return s, False
    # Try stripping leading/trailing garbage chars
    for length in (13, 10):
        m = re.search(r'\d{' + str(length) + r'}', s)
        if m:
            candidate = m.group(0)
            if length == 10:
                # append X check
                c = candidate
                if check_isbn10(c):
                    return c, True
            elif length == 13:
                if check_isbn13(candidate):
                    return candidate, True
    # Try fixing single-digit checksum error for ISBN-13
    if len(s) == 13 and s[:-1].isdigit():
        base = s[:-1]
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base))
        correct_check = str((10 - (total % 10)) % 10)
        if correct_check != s[-1]:
            return base + correct_check, True
    # Try fixing single-digit checksum for ISBN-10
    if len(s) == 10 and s[:-1].isdigit():
        base = s[:-1]
        total = sum(int(c) * (10 - i) for i, c in enumerate(base))
        check = (11 - (total % 11)) % 11
        correct = 'X' if check == 10 else str(check)
        return base + correct, True
    return None, False


def normalize_isbn(isbn):
    """Return canonical ISBN-13 for any valid input (ISBN-10 or ISBN-13)."""
    s = _strip(isbn)
    if check_isbn13(s):
        return s
    if check_isbn10(s):
        return isbn10_to_13(s)
    repaired, _ = repair_isbn(s)
    if repaired:
        return normalize_isbn(repaired)
    return None


def extract_isbn_from_text(text):
    """Find any ISBN-like pattern in free text and return normalized if valid."""
    if not text:
        return None
    candidates = re.findall(r'(?:ISBN[:\s-]*)?(97[89][\d\s\-]{10,17}|\d[\d\s\-]{8,11}[\dX])', text, re.I)
    for c in candidates:
        s = _strip(c)
        if is_valid_isbn(s):
            return normalize_isbn(s)
    return None
