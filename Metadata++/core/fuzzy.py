#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""Fuzzy matching and multilingual metadata normalization."""

import re
import unicodedata


# ── Basic string normalization ────────────────────────────────────────────────

def normalize_str(s):
    """Lowercase, strip accents, remove punctuation."""
    if not s:
        return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _words(s):
    return set(normalize_str(s).split())


# ── Levenshtein distance (pure Python, no deps) ──────────────────────────────

def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Only keep two rows
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1)
            ))
        prev = curr
    return prev[-1]


def similarity(a, b):
    """Return 0–100 similarity score."""
    na, nb = normalize_str(a), normalize_str(b)
    if not na and not nb:
        return 100
    if not na or not nb:
        return 0
    dist = levenshtein(na, nb)
    max_len = max(len(na), len(nb))
    ratio = int(round((1 - dist / max_len) * 100))
    # Boost for word overlap
    wa, wb = _words(a), _words(b)
    if wa and wb:
        overlap = len(wa & wb) / max(len(wa), len(wb))
        ratio = int(round((ratio + overlap * 100) / 2))
    return max(0, min(100, ratio))


def title_matches(t1, t2, threshold=80):
    return similarity(t1, t2) >= threshold


def author_matches(a1, a2, threshold=75):
    """Handle 'Last, First' vs 'First Last' variations."""
    def normalize_author(a):
        a = normalize_str(a)
        if ',' in a:
            parts = [p.strip() for p in a.split(',', 1)]
            a = parts[1] + ' ' + parts[0]
        return a
    return similarity(normalize_author(a1), normalize_author(a2)) >= threshold


# ── Article stripping ─────────────────────────────────────────────────────────

_ARTICLES = {
    'en': ['the', 'a', 'an'],
    'it': ['il', 'lo', 'la', 'i', 'gli', 'le', "l'"],
    'de': ['der', 'die', 'das', 'ein', 'eine'],
    'fr': ['le', 'la', 'les', 'un', 'une', "l'"],
    'es': ['el', 'la', 'los', 'las', 'un', 'una'],
    'pt': ['o', 'a', 'os', 'as', 'um', 'uma'],
}

def strip_articles(title, lang='en'):
    words = normalize_str(title).split()
    articles = _ARTICLES.get(lang, _ARTICLES['en'])
    if words and words[0] in articles:
        return ' '.join(words[1:])
    return ' '.join(words)


# ── Language normalization ────────────────────────────────────────────────────

_LANG_MAP = {
    # ISO 639-1 / common variants
    'english': 'en', 'eng': 'en',
    'italian': 'it', 'ita': 'it', 'italiano': 'it',
    'german':  'de', 'deu': 'de', 'deutsch': 'de', 'ger': 'de',
    'french':  'fr', 'fra': 'fr', 'français': 'fr', 'fre': 'fr',
    'spanish': 'es', 'spa': 'es', 'español': 'es', 'sp': 'es',  # 'sp' is a legacy Calibre code
    'portuguese': 'pt', 'por': 'pt',
    'japanese': 'ja', 'jpn': 'ja',
    'chinese':  'zh', 'zho': 'zh',
    'russian':  'ru', 'rus': 'ru',
    'arabic':   'ar', 'ara': 'ar',
    'dutch':    'nl', 'nld': 'nl',
    'polish':   'pl', 'pol': 'pl',
}

def normalize_language(lang_raw):
    if not lang_raw:
        return ''
    key = lang_raw.lower().strip()
    return _LANG_MAP.get(key, key[:2] if len(key) >= 2 else key)


# ── Publisher normalization ───────────────────────────────────────────────────

def normalize_publisher(pub):
    if not pub:
        return ''
    # Strip common suffixes
    pub = re.sub(
        r'\b(inc\.?|llc\.?|ltd\.?|corp\.?|publishing|publishers|press|books|group|co\.?)\b',
        '', pub, flags=re.I
    )
    return re.sub(r'\s+', ' ', pub).strip().title()


# ── Date normalization ────────────────────────────────────────────────────────

def normalize_pubdate(raw):
    """Try to return a YYYY-MM-DD or YYYY string."""
    if not raw:
        return ''
    raw = raw.strip()
    # Already YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', raw):
        return raw
    # YYYY
    m = re.search(r'\b(19|20)\d{2}\b', raw)
    if m:
        return m.group(0)
    return raw


# ── Synopsis / comments quality scoring ───────────────────────────────────────

# Boilerplate / junk fragments that indicate a scraped synopsis is not real
# back-cover copy — store navigation text, truncation markers, cookie
# banners, etc. that sometimes leak into og:description or div scrapes.
_SYNOPSIS_JUNK_PATTERNS = [
    r'javascript is disabled',
    r'enable cookies',
    r'add to (cart|basket|wishlist)',
    r'free shipping',
    r'sign in to',
    r'create an account',
    r'\bclick here\b',
    r'see more on amazon',
    r'visit the .* store',
    r'^\s*\.\.\.\s*$',
    r'page not found',
    r'access denied',
    r'are you a robot',
    # Amazon's fixed Kindle-store sales pitch -- stamped into the page's
    # meta-description on every Kindle product page that lacks a real
    # "About this book" synopsis. Caught at the source in
    # providers._parse_amazon_page (_looks_like_kindle_boilerplate); listed
    # here too as defense-in-depth so any other provider/path that happens
    # to scrape this same text gets it heavily penalised by
    # synopsis_quality() rather than silently winning a merge.
    r'kindle edition by',
    r'download it once and read it',
    r'note taking and highlighting while reading',
]
_SYNOPSIS_JUNK_RE = re.compile('|'.join(_SYNOPSIS_JUNK_PATTERNS), re.I)

# Leftover HTML entities / escape sequences indicate a scrape that wasn't
# fully cleaned — a strong signal the text will look broken to the user.
_UNESCAPED_ENTITY_RE = re.compile(r'&[a-zA-Z]{2,8};|&#\d{2,5};|\\u[0-9a-fA-F]{4}')


def synopsis_quality(text):
    """
    Return a quality score (float) for a candidate synopsis/comments string.
    Higher is better. Used to break ties and to penalise garbled scrapes so
    that a shorter, clean synopsis from a strong source can beat a longer
    but junk-laden one from a weak source.

    Heuristics (all cheap, no network):
      - Length contributes positively but with strongly diminishing returns
        past ~500 characters (very long "synopses" are often whole
        front-matter dumps, multiple concatenated reviews, or repeated
        boilerplate, not a clean blurb) — capped so length alone can never
        out-score a clean text's quality penalties.
      - Boilerplate / navigation junk phrases are penalised per occurrence
        (not a single flat deduction) so repeated junk text can't simply
        out-length its own penalty.
      - Leftover HTML entities or unicode escapes are a moderate penalty
        (sign of incomplete scraping/decoding).
      - A high ratio of non-letter characters (markup remnants, repeated
        punctuation) is penalised.
      - Ends mid-sentence with no terminal punctuation and a trailing
        ellipsis/cutoff marker → penalised (truncated scrape).
    """
    if not text:
        return 0.0
    t = text.strip()
    if not t:
        return 0.0

    length = len(t)
    # Diminishing-returns length score, hard-capped at 80 points total so
    # no amount of raw length can outweigh a serious quality penalty below.
    length_score = min(length, 500) / 6.25          # 0–80, maxes out at 500 chars
    if length > 500:
        length_score += min((length - 500) / 100.0, 10)  # tiny extra credit, capped at +10

    score = length_score

    # Junk boilerplate: penalise PER occurrence (capped) instead of a flat
    # amount, so repeating/padding junk text doesn't dilute the penalty.
    junk_hits = len(_SYNOPSIS_JUNK_RE.findall(t))
    if junk_hits:
        score -= min(junk_hits * 35, 200)

    entity_hits = len(_UNESCAPED_ENTITY_RE.findall(t))
    if entity_hits:
        score -= min(entity_hits * 5, 60)

    letters = sum(1 for c in t if c.isalpha())
    if length > 0:
        letter_ratio = letters / length
        if letter_ratio < 0.55:
            score -= 50

    # Truncation markers at the very end ("...", "…", "Read more", "[...]")
    tail = t[-30:].lower()
    if re.search(r'(\.\.\.|…)\s*$', tail) or 'read more' in tail or tail.endswith('[...]'):
        score -= 15

    # Reward a real terminal sentence punctuation at the end
    if t[-1:] in '.!?"\u201d\u00bb':
        score += 5

    return max(0.0, score)

def is_duplicate(mi1, mi2, title_thresh=85, author_thresh=80):
    """Return True if two Calibre metadata objects look like duplicates."""
    t1 = mi1.title or ''
    t2 = mi2.title or ''
    if not title_matches(t1, t2, title_thresh):
        return False
    a1 = ', '.join(mi1.authors) if mi1.authors else ''
    a2 = ', '.join(mi2.authors) if mi2.authors else ''
    if a1 and a2 and not author_matches(a1, a2, author_thresh):
        return False
    return True
