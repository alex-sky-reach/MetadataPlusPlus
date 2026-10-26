#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""
Async fetch engine — v6.2.13
New in v6.2.13:
  - All sources, including the regional/experimental ones (Kobo regional,
    Casa del Libro, FNAC, BNE, Feltrinelli, Libraccio, SBN, BNF, LOC,
    WorldCat, ISBNdb), are now active by default per explicit user request.
    _SOURCE_DEFAULTS updated to match config.py. This does not change
    whether those endpoints actually respond — see providers.py for the
    confirmed 403/404 status of each — it only changes whether the plugin
    bothers to ask them.

Async fetch engine — v6.2.11
New in v6.2.11:
  - NEW global source: Goodreads (fetch_goodreads in providers.py), on by
    default with weight 9 — the highest of any source — because field
    testing shows its synopses are consistently longer and cleaner than
    Google Books/Open Library's, so it's meant to dominate the
    best-synopsis scoring in _merge_results (see v6.2.8 entry below for how
    that scoring works) rather than just being "one more source".
  - Fixed root cause of the repeated WorldCat "[WinError 10054] ...
    interrotta ... dall'host remoto" lines in field logs: use_worldcat was
    missing from the v6.2.9 stale-prefs migration list in config.py, so
    anyone who had it persisted as True from an older build kept hitting
    the dead xisbn.worldcat.org endpoint on every single run despite the
    in-code default being False since v6.2.x. config.py now clears it too,
    and as defense-in-depth fetch_worldcat() itself no longer makes any
    network call at all (see providers.py v6.2.11).

Async fetch engine — v6.2.10
New in v6.2.10:
  - Per-source diagnostic summary: when a book's fetch collects zero raw
    results, a single "Per-source outcome: name=ok|empty|error|timeout"
    line is now logged at INFO level so the cause is visible without
    switching log_level to DEBUG. Previously "No result from %s" was only
    logged at DEBUG, so a run that legitimately found nothing from any
    source gave no clue which sources actually tried and failed vs. never
    ran at all.
  - See providers.py changelog for the matching fetch_amazon bot-page
    detection fix — this is the main fix for the repeated "Amazon: search
    candidate X, fetching dp/ page" ... "Collected 0 raw results" pattern
    seen in field logs even when dp/ pages were being fetched successfully.

Async fetch engine — v6.2.9
New in v6.2.9:
  - Root-cause fix for "v6.2.8 still shows kobo_com/casadellibro/etc. as
    active sources": calibre's JSONConfig persists *explicit* values to
    disk. Anyone who had already run v6.2.7 (whose defaults were True for
    these sources) got True written into their on-disk prefs file.
    Changing the in-code default to False in v6.2.8 does not retroactively
    overwrite an already-persisted True — prefs.get() always returns the
    stored value over the coded default. That's why the field log kept
    showing every blocked source as "active" even on the v6.2.8 build.
    Fixed in config.py with a one-time migration that runs on plugin load:
    it deletes the stale persisted True for the specific known-blocked
    keys (kobo_com/es/it/fr/de, casadellibro, fnac_es, bne, bnf,
    feltrinelli, libraccio, sbn, loc) so they fall back to the new False
    default, gated by a migration-version marker so it only runs once and
    never fights a later deliberate user re-enable.

New in v6.2.8:
  - Best-synopsis selection no longer ranks by raw text length. Field logs
    showed it was possible for a long but low-quality scraped synopsis to
    beat a short, clean one from a trusted source (Google Books, Open
    Library). Now scores (source weight × 10) + synopsis_quality(text),
    so source trust dominates and text quality (boilerplate/truncation/
    garbled-markup detection, see fuzzy.synopsis_quality) breaks ties —
    raw length only matters up to a small, capped bonus.
  - Stale-cache bug fixed: entries written by plugin versions before the
    "identifiers-only is not a result" guard existed were being served
    back verbatim on cache hit, producing the confusing
    "✔ Result OK — fields: identifiers" log line with no real metadata.
    Cache reads are now re-validated with _is_substantive_result() before
    being trusted; stale entries are discarded and the book is re-fetched.
  - Casa del Libro, FNAC, BNE, Feltrinelli, Libraccio, SBN, and all Kobo
    regional storefronts no longer auto-activate by language. Field logs
    show every one of these returning HTTP 403/404 on every single run —
    their search endpoints are bot-blocked or have moved. They remain in
    SOURCE_REGISTRY and the Sources tab (marked "experimental") so they
    can be manually re-enabled/retested, but no longer cost ~5-10s of
    dead-end requests per book by default. See providers.py changelog
    for verified-working sources (Amazon, Google Books, Open Library,
    Internet Archive — unchanged and still auto-active).

New in v6.2.7:
  - Kobo: replaced single dead 'kobo' source (storeapi retired) with five
    regional providers: kobo_com, kobo_es, kobo_it, kobo_fr, kobo_de.
    kobo_com is always active (global English catalogue); the regional ones
    auto-activate alongside their language-specific peers (kobo_es with es,
    kobo_it with it, etc.).
  - BNE: updated to use fixed SRU endpoint (datos.bne.es was 404).
  - FNAC: improved headers for reduced 403 rate.

New in v6.2.6 (bugfix):
  - _sources_for_lang step 2: fixed auto-activation of language-specific
    providers (Feltrinelli, SBN, Casa del Libro, BNE, etc.). Previously,
    config.py sets use_feltrinelli=False etc. in prefs.defaults, and step 2
    checked `prefs.get(toggle_key) is False` — which matched the default,
    not just an explicit user choice. Fix: check `toggle_key in prefs` (only
    True when the user has written the key) before skipping auto-activation.
  - _sanitize_title: detect underscore-separated filename-style titles
    (e.g. "Marcello_Veneziani_Nietzsche_e_Marx_si_davano_la_mano_2025"),
    replace underscores with spaces, and strip trailing 4-digit years so all
    providers receive a human-readable query string.
  - See providers.py v6.2.6 for the Amazon ISBN dp/ local-TLD fix.

Changes vs v6.2 (v6.2.5):
  - New providers registered: casadellibro, fnac_es, feltrinelli, libraccio,
    bnf, bne, sbn — all language-specific storefronts/national libraries.
  - reset_google_cooldown() called at the start of every fetch_for_book()
    so a Google 429 on book N does not suppress Google for books N+1, N+2…
  - Amazon search cooldown is now per-TLD (dict) and fully reset per book.
  - Language-aware source enabling: Spanish/Italian/French/German books
    automatically activate their native providers even if the user left them
    on default settings — with a lower weight so they supplement rather than
    override the global sources.
  - All other logic (ISBN repair, cache, merge, cover probing) unchanged.
"""

import threading
import logging
import os
import re

from calibre.utils.config import config_dir  # type: ignore

from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
from calibre_plugins.metadata_plus.core.cache import MetadataCache  # type: ignore
from calibre_plugins.metadata_plus.core.synopsis_cleaner import clean_synopsis  # type: ignore
from calibre_plugins.metadata_plus.core.isbn_utils import normalize_isbn, repair_isbn, is_valid_isbn  # type: ignore
from calibre_plugins.metadata_plus.core.fuzzy import (  # type: ignore
    normalize_language, normalize_publisher, normalize_pubdate,
    title_matches, author_matches, is_duplicate, normalize_str,
    synopsis_quality, similarity, _SYNOPSIS_JUNK_RE,
)
from calibre_plugins.metadata_plus.providers.providers import (  # type: ignore
    fetch_google, fetch_openlibrary, fetch_worldcat, fetch_loc,
    fetch_internetarchive, fetch_isbndb, fetch_amazon, fetch_goodreads,
    fetch_kobo_com, fetch_kobo_es, fetch_kobo_it, fetch_kobo_fr, fetch_kobo_de,
    fetch_casadellibro, fetch_fnac_es, fetch_feltrinelli, fetch_libraccio,
    fetch_bnf, fetch_bne, fetch_sbn,
    fetch_isbn_by_title, fetch_openlibrary_cover,
    best_cover, probe_best_cover, score_cover,
    reset_amazon_search_cooldown, reset_google_cooldown,
)

# Placeholder titles calibre uses when it doesn't know the real title
_UNKNOWN_TITLES = {'unknown', 'no title', '', 'untitled'}


def _get_logger():
    logger = logging.getLogger('metadata_plus')
    if not logger.handlers:
        log_path = os.path.join(config_dir, 'metadata_plus.log')
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        logger.addHandler(sh)
    level = getattr(logging, prefs.get('log_level', 'INFO'), logging.INFO)
    logger.setLevel(level)
    return logger


# ── Source registry ────────────────────────────────────────────────────────────
# Format: name -> (fetch_fn, toggle_pref_key, weight_pref_key)

SOURCE_REGISTRY = {
    # ── Global / English-primary sources ──────────────────────────────────────
    'google':          (fetch_google,          'use_google',          'weight_google'),
    'goodreads':       (fetch_goodreads,       'use_goodreads',       'weight_goodreads'),
    'openlibrary':     (fetch_openlibrary,     'use_openlibrary',     'weight_openlibrary'),
    'worldcat':        (fetch_worldcat,        'use_worldcat',        'weight_worldcat'),
    'loc':             (fetch_loc,             'use_loc',             'weight_loc'),
    'internetarchive': (fetch_internetarchive, 'use_internetarchive', 'weight_internetarchive'),
    'amazon':          (fetch_amazon,          'use_amazon',          'weight_amazon'),
    # ── Kobo regional storefronts ──────────────────────────────────────────────
    # kobo_com = global English catalogue (always-on like Amazon/Google)
    # kobo_es/it/fr/de = auto-activate for their respective language
    'kobo_com':        (fetch_kobo_com,        'use_kobo_com',        'weight_kobo_com'),
    'kobo_es':         (fetch_kobo_es,         'use_kobo_es',         'weight_kobo_es'),
    'kobo_it':         (fetch_kobo_it,         'use_kobo_it',         'weight_kobo_it'),
    'kobo_fr':         (fetch_kobo_fr,         'use_kobo_fr',         'weight_kobo_fr'),
    'kobo_de':         (fetch_kobo_de,         'use_kobo_de',         'weight_kobo_de'),
    # ── Spanish-language sources ───────────────────────────────────────────────
    'casadellibro':    (fetch_casadellibro,    'use_casadellibro',    'weight_casadellibro'),
    'fnac_es':         (fetch_fnac_es,         'use_fnac_es',         'weight_fnac_es'),
    'bne':             (fetch_bne,             'use_bne',             'weight_bne'),
    # ── Italian-language sources ───────────────────────────────────────────────
    'feltrinelli':     (fetch_feltrinelli,     'use_feltrinelli',     'weight_feltrinelli'),
    'libraccio':       (fetch_libraccio,       'use_libraccio',       'weight_libraccio'),
    'sbn':             (fetch_sbn,             'use_sbn',             'weight_sbn'),
    # ── French-language sources ────────────────────────────────────────────────
    'bnf':             (fetch_bnf,             'use_bnf',             'weight_bnf'),
}

# Sources that use HTML scraping and support browser-based fetching.
# Only these are re-run in the sequential browser pass that fires when the
# parallel first-pass fetch returns zero results and the user has the browser
# fallback enabled.  API-only sources (google, openlibrary, internetarchive,
# loc, bnf, bne, sbn, worldcat, isbndb) are intentionally excluded because
# a browser can't meaningfully improve an API request that already failed.
BROWSER_CAPABLE_SOURCES = frozenset({
    'goodreads',
    'amazon',
    'kobo_com', 'kobo_es', 'kobo_it', 'kobo_fr', 'kobo_de',
    'casadellibro', 'fnac_es',
    'feltrinelli', 'libraccio', 'sbn',
})

# Default source states — language-specific ones are OFF by default but get
# auto-activated when the book's language matches (see _sources_for_lang below).
_SOURCE_DEFAULTS = {
    'use_google':          True,
    'use_goodreads':       True,
    'use_openlibrary':     True,
    'use_worldcat':        True,    # fetch_worldcat() is a no-op (dead endpoint) — see providers.py
    'use_loc':             True,
    'use_internetarchive': True,
    'use_amazon':          True,
    # Kobo regional
    'use_kobo_com':        True,
    'use_kobo_es':         True,
    'use_kobo_it':         True,
    'use_kobo_fr':         True,
    'use_kobo_de':         True,
    'use_isbndb':          True,    # no-op unless an API key is configured
    'use_casadellibro':    True,
    'use_fnac_es':         True,
    'use_bne':             True,
    'use_feltrinelli':     True,
    'use_libraccio':       True,
    'use_sbn':             True,
    'use_bnf':             True,
}

# Which sources to auto-activate for each language (ISO-639-1 code).
# These are added to the active set when the book's language matches,
# ONLY if the user hasn't explicitly turned them off (set to False in prefs).
#
# v6.2.8: Casa del Libro, FNAC, BNE, Feltrinelli, Libraccio, SBN, and all
# Kobo regional storefronts are NOT auto-activated any more. Field logs
# show every one of these scraping endpoints returning HTTP 403/404 on
# every run (anti-bot blocking or endpoints that have since moved) — they
# were contributing zero results while adding several seconds of latency
# and noisy warnings per book. They remain available in SOURCE_REGISTRY
# and the Sources tab (marked "experimental") for anyone who wants to
# manually re-test or fix the underlying scrape; they just no longer
# auto-activate by language. Re-add a language entry here once a given
# source's endpoint is confirmed working again.
_LANG_AUTO_SOURCES = {
    'la': ['openlibrary', 'loc'],  # Latin texts — covered by OL/LOC, both
                                    # of which use stable, documented APIs.
}


def _src_enabled(key):
    """Read source toggle; fall back to _SOURCE_DEFAULTS or True."""
    val = prefs.get(key)
    if val is None:
        return _SOURCE_DEFAULTS.get(key, True)
    return bool(val)


def _sources_for_lang(lang):
    """
    Return the set of source names that should run for this language,
    merging the user's explicit toggles with language-aware auto-activation.

    Rules:
      1. A source with use_X = True (explicit or default) is always included.
      2. A language-specific source in _LANG_AUTO_SOURCES[lang] is included
         UNLESS the user has explicitly set use_X = False in prefs.
      3. A source with use_X = False is always excluded.
    """
    active = {}

    # Step 1: collect sources the user/defaults have turned on
    for name, (fn, toggle_key, weight_key) in SOURCE_REGISTRY.items():
        if _src_enabled(toggle_key):
            weight = prefs.get(weight_key) or _default_weight(name)
            active[name] = (fn, weight)

    # Step 2: auto-activate language-specific sources
    if lang and lang[:2] in _LANG_AUTO_SOURCES:
        for name in _LANG_AUTO_SOURCES[lang[:2]]:
            if name in active:
                continue  # already included
            if name not in SOURCE_REGISTRY:
                continue
            fn, toggle_key, weight_key = SOURCE_REGISTRY[name]
            # Only skip if the user has *explicitly* written False into the
            # prefs JSON file. The defaults dict also has these set to False
            # (so they appear OFF in the UI by default), but that must not
            # suppress auto-activation — otherwise Italian books never get
            # Feltrinelli/SBN and Spanish books never get Casa del Libro/BNE.
            # Calibre's JSONConfig: `key in prefs` is True only when the user
            # has written the key, not when it merely exists in .defaults.
            if toggle_key in prefs and not prefs[toggle_key]:
                continue
            weight = prefs.get(weight_key) or _default_weight(name)
            active[name] = (fn, weight)

    return active


def _default_weight(name):
    """Fallback weight for sources not yet in user prefs."""
    defaults = {
        'casadellibro': 7, 'fnac_es': 6, 'bne': 7,
        'feltrinelli':  7, 'libraccio': 6, 'sbn': 7,
        'bnf': 7,
        'google': 9, 'amazon': 8, 'openlibrary': 7,
        'goodreads': 9,
        'loc': 8, 'internetarchive': 5, 'worldcat': 6,
        'kobo_com': 7, 'kobo_es': 7, 'kobo_it': 7, 'kobo_fr': 7, 'kobo_de': 7,
        'isbndb': 8,
    }
    return defaults.get(name, 5)


_REAL_ASIN_RE = re.compile(r'^[A-Z0-9]{10}$')

def _is_real_asin(value):
    return bool(value and _REAL_ASIN_RE.match(value))


def _extract_asin(identifiers):
    for key in ('amazon', 'asin', 'mobi-asin'):
        val = identifiers.get(key, '') or ''
        if _is_real_asin(val):
            return val
    return ''


def _sanitize_title(title, author):
    if not title:
        return title

    # ── Filename-style titles ─────────────────────────────────────────────────
    # Calibre sometimes inherits the filename as the title, e.g.
    # "Marcello_Veneziani_Nietzsche_e_Marx_si_davano_la_mano_2025".
    # Heuristic: if underscores outnumber spaces by 3:1 or more, treat them
    # as word separators and convert to a normal title.
    underscore_count = title.count('_')
    space_count      = title.count(' ')
    if underscore_count >= 3 and underscore_count >= space_count * 3:
        title = title.replace('_', ' ')
        # Strip trailing 4-digit year appended by some rippers/tools
        title = re.sub(r'\s+(19|20)\d{2}\s*$', '', title).strip()

    if not author:
        return title

    # ── Strip author name appended to title ───────────────────────────────────
    candidates = [author.strip()]
    for part in re.split(r'[,;&]', author):
        part = part.strip()
        if len(part) > 3:
            candidates.append(part)
    for cand in candidates:
        pattern = r'\s*[-–—]\s*' + re.escape(cand) + r'\s*$'
        cleaned = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
        if cleaned and cleaned != title:
            return cleaned
    return title


def _fetch_source(name, fn, title, author, isbn, asin, lang, weight, results, lock, log, outcomes=None):
    log.debug('Starting fetch from %s (isbn=%r asin=%r lang=%r)', name, isbn, asin, lang)
    timeout = prefs.get('timeout', 20)
    retries = prefs.get('retries', 2)
    try:
        data = fn(title, author, isbn, asin=asin, lang=lang,
                  timeout=timeout, retries=retries, log=log)
        if data:
            data['_weight'] = weight
            log.info('Got result from %s: title=%r', name, data.get('title', '')[:50])
            with lock:
                results.append(data)
            if outcomes is not None:
                outcomes[name] = 'ok'
        else:
            log.debug('No result from %s', name)
            if outcomes is not None:
                outcomes[name] = 'empty'
    except Exception:
        log.error('Provider %s raised an exception:', name, exc_info=True)
        if outcomes is not None:
            outcomes[name] = 'error'


def _fetch_isbndb_source(title, author, isbn, asin, weight, results, lock, log):
    api_key = prefs.get('isbndb_key', '')
    if not api_key:
        return
    timeout = prefs.get('timeout', 20)
    retries = prefs.get('retries', 2)
    lookup = isbn or asin
    try:
        data = fetch_isbndb(title, author, lookup, api_key,
                            timeout=timeout, retries=retries, log=log)
        if data:
            data['_weight'] = weight
            with lock:
                results.append(data)
    except Exception:
        log.error('ISBNdb raised an exception:', exc_info=True)


# ── ISBN / ASIN helpers ────────────────────────────────────────────────────────

def _isbn_from_asin_via_amazon(asin, timeout, log):
    import re
    from calibre_plugins.metadata_plus.providers.providers import _get, UA  # type: ignore

    hdrs = {
        'User-Agent': UA,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    url = 'https://www.amazon.com/dp/{}'.format(asin)
    raw = _get(url, timeout, 1, headers=hdrs, log=log)
    if not raw:
        return ''

    for m in re.finditer(r'"isbn"\s*:\s*"(\d{10,13})"', raw, re.I):
        candidate = m.group(1)
        if is_valid_isbn(candidate):
            log.info('Found ISBN %s in Amazon JSON-LD for ASIN %s', candidate, asin)
            return candidate

    for pat in [
        r'Print ISBN[^<]{0,20}[\s:]+([0-9]{3}[-\s]?[0-9]{10}|[0-9]{13}|[0-9]{10})',
        r'ISBN-13[^<]{0,10}[\s:]+([0-9]{3}[-\s]?[0-9]{10}|[0-9]{13})',
        r'ISBN-10[^<]{0,10}[\s:]+([0-9][-\s]?[0-9]{9}|[0-9]{10})',
    ]:
        m = re.search(pat, raw, re.I)
        if m:
            candidate = re.sub(r'[-\s]', '', m.group(1))
            if is_valid_isbn(candidate):
                log.info('Found ISBN %s on Amazon dp page for ASIN %s', candidate, asin)
                return candidate

    return ''


def _discover_isbn(title, author, asin, log):
    if not prefs.get('auto_isbn_lookup', True):
        return ''
    if not asin:
        return ''
    timeout = prefs.get('timeout', 20)
    log.info('Trying Amazon dp page ISBN scrape for ASIN %s', asin)
    return _isbn_from_asin_via_amazon(asin, timeout, log)


def _isbn_from_results(results, log):
    for r in sorted(results, key=lambda r: r.get('_weight', 1), reverse=True):
        cand = (r.get('identifiers') or {}).get('isbn', '')
        if cand and is_valid_isbn(normalize_isbn(cand) or cand):
            if log:
                log.info('ISBN %s recovered from %s result (no extra '
                         'network call needed)', cand, r.get('source', '?'))
            return cand
    return ''


# ── Merge logic ────────────────────────────────────────────────────────────────

_CONTENT_KEYS = {'title', 'authors', 'publisher', 'pubdate', 'tags',
                 'rating', 'language', 'comments', 'cover_url'}


def _is_substantive_result(data):
    """
    Return True if a merged-result dict has real bibliographic content
    (title/authors/synopsis/cover/etc.), not just an `identifiers` dict.
    Used both to gate _merge_results() output and to re-validate cache
    entries written by older plugin versions that lacked this guard.
    """
    if not data:
        return False
    return bool(set(data.keys()) & _CONTENT_KEYS)


def _strip_edition_noise(t):
    """
    Strip trailing parenthetical / bracketed noise from a book title so that
    fuzzy matching is done on the core title only.

    Handles (in order):
      1. Edition/format tags anywhere:
         "(Spanish Edition)", "(Kindle Edition)", "[eBook]", …
      2. Series/volume suffixes — the most common source of false-negative
         fuzzy matches, e.g.
           "Los equilibrios posibles (Orillas y caminos nº 3)"   → "Los equilibrios posibles"
           "Dune (Dune Chronicles, Book 1)"                      → "Dune"
           "The Hobbit (Lord of the Rings vol. 0)"               → "The Hobbit"
         Pattern: trailing (...) or [...] that contains at least one digit
         (volume/part number) OR a series-indicator keyword.
      3. Subtitle split on common separators ( : – — ).

    v6.2.14 — Bug fix: the old regex only stripped edition/format tags,
    completely ignoring series suffixes.  This caused every result whose
    title was returned with a series appendage to fail fuzzy matching and
    be silently discarded — which in turn triggered an unnecessary second
    browser pass (double-fetch), wasting ~30 s per book.
    """
    if not t:
        return t
    # 1. Edition/format tags (e.g. "(Spanish Edition)", "[Kindle]")
    t = re.sub(
        r'\s*[\(\[][^()\[\]]{0,40}(edition|edición|ebook|kindle)[^()\[\]]{0,10}[\)\]]',
        '', t, flags=re.I)
    # 2. Trailing series/volume parentheticals — e.g.
    #    "(Orillas y caminos nº 3)", "(Dune Chronicles, Book 1)",
    #    "(Book 2)", "[Vol. 5]", "(Series Name #3)"
    #    Match: trailing (...) or [...] that contain a digit, OR
    #    a series keyword (book|vol|part|tome|nº|no\.|#|series|saga|trilogy)
    _SERIES_PAT = re.compile(
        r'\s*[\(\[]'
        r'(?=[^\(\)\[\]]*(?:\d|'
        r'\b(?:book|vol|volume|part|tome|n[oº°]|series|saga|trilogy|'
        r'libro|banda|deel|band|tomo|capitulo|chapter)\b'
        r'))'
        r'[^\(\)\[\]]{1,80}'
        r'[\)\]]\s*$',
        re.I | re.UNICODE,
    )
    # Apply repeatedly to peel off multiple trailing parentheticals
    for _ in range(4):
        stripped = _SERIES_PAT.sub('', t).strip()
        if stripped == t:
            break
        t = stripped
    # 3. Subtitle split
    t = re.split(r'\s*[:/–—]\s*', t, maxsplit=1)[0]
    return t.strip()


def _title_prefix_match(book_title, result_title, log=None):
    """
    Return True when one normalized title is a leading substring of the other.

    This is the last-resort fuzzy check before a result is discarded — it
    catches cases like:
      query  : "Los Equilibrios Posibles"
      result : "Los equilibrios posibles (Orillas y caminos nº 3)"
    where, after _strip_edition_noise, the series suffix was not fully
    cleaned (e.g. a non-standard format).  We compare the shorter string
    against the start of the longer one; at least 5 chars must match to
    avoid false positives on very short titles.

    v6.2.14 — previously this check existed only for single-result fetches;
    extended to all result sets because the false-discard / double-fetch bug
    was also triggered with 2+ results (Amazon + Goodreads both returning
    the same series-suffixed title).
    """
    bt = normalize_str(_strip_edition_noise(book_title))
    rt = normalize_str(_strip_edition_noise(result_title))
    if not bt or not rt or min(len(bt), len(rt)) < 5:
        return False
    match = rt.startswith(bt) or bt.startswith(rt)
    if match and log:
        log.info('Title prefix-match fallback accepted: %r vs %r',
                 book_title[:40], result_title[:40])
    return match


def _detect_synopsis_lang(text):
    """
    Lightweight language detector for synopsis scoring — no external deps.
    Returns a 2-letter ISO code ('en', 'es', 'it', 'fr', 'de', 'pt', …)
    or '' if undetermined.

    Method: score the text against per-language stop-word sets.  Stop-words
    are so frequent that even a 200-character excerpt will contain several;
    the language with the most hits wins.  This is intentionally simple —
    we only need it to reliably distinguish English from Spanish/Italian/
    French/German/Portuguese, which stop-words do extremely well.
    """
    if not text or len(text) < 30:
        return ''
    words = set(re.findall(r'\b[a-záéíóúàèìòùâêîôûäëïöüñçß]+\b',
                           text.lower()))
    _STOPS = {
        'en': {'the','of','and','to','a','in','is','it','you','that','he',
               'was','for','on','are','with','as','his','they','at','be',
               'this','from','or','an','by','not','but','what','all','were'},
        'es': {'de','la','el','en','y','a','que','los','las','por','un','una',
               'con','se','su','lo','es','del','al','para','como','más','pero',
               'sus','le','ya','o','fue','este','ha','si','porque','esta'},
        'it': {'di','il','la','e','in','un','che','a','le','per','del','una',
               'dei','con','si','è','da','lo','della','non','al','sul','ha',
               'gli','come','anche','ma','questo','tra','nel','sua','più'},
        'fr': {'le','de','et','la','les','des','en','un','une','du','est','que',
               'qui','dans','il','au','par','sur','ce','se','pas','avec','tout',
               'plus','son','ou','mais','pour','comme','elle','nous','je'},
        'de': {'die','der','und','in','den','von','zu','das','mit','sich','des',
               'auf','für','ist','im','dem','nicht','ein','eine','als','auch',
               'es','an','werden','aus','er','hat','dass','sie','nach','wird'},
        'pt': {'de','a','o','que','e','do','da','em','um','para','com','uma',
               'os','no','se','na','por','mais','as','dos','como','mas','foi',
               'ao','ele','das','tem','seu','sua','ou','quando','muito'},
    }
    scores = {lang: len(words & stops) for lang, stops in _STOPS.items()}
    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    # Require at least 3 hits to avoid random matches on very short snippets
    return best_lang if best_score >= 3 else ''


def _merge_results(results, book_title, book_author, book_lang='',
                   probe_covers=False, log=None):
    if not results:
        return None

    results_sorted = sorted(results, key=lambda r: r.get('_weight', 1), reverse=True)

    title_unknown = (not book_title or
                     book_title.lower().strip() in _UNKNOWN_TITLES)

    merged = {}
    cover_candidates = []
    comment_candidates = []

    for r in results_sorted:
        rtitle      = r.get('title', '')
        rauthors    = r.get('authors', [])
        rauthor_str = ', '.join(rauthors) if rauthors else ''
        weight      = r.get('_weight', 1)
        source_name = r.get('source') or '?'

        thresh_t = prefs.get('fuzzy_threshold', 80)
        if not title_unknown and book_title and rtitle:
            base_thresh = max(40, thresh_t - 30)
            passes = title_matches(book_title, rtitle, base_thresh)
            if not passes:
                passes = title_matches(_strip_edition_noise(book_title),
                                        _strip_edition_noise(rtitle), base_thresh)
            if not passes:
                # Last resort: prefix match — catches series-suffixed titles
                # that survived _strip_edition_noise (e.g. non-standard formats).
                # Previously only applied to single-result fetches; now applies
                # to all result sets (v6.2.14 double-fetch bug fix).
                passes = _title_prefix_match(book_title, rtitle, log)
            if not passes:
                if log:
                    log.debug('Fuzzy title mismatch, skipping result from %s '
                              '(%r vs %r)', r.get('source', '?'), book_title[:40], rtitle[:40])
                continue

        # ── Author cross-check veto (v6.2.20) ──────────────────────────────
        # If both the search author and the result author are known and
        # non-trivial, and they are clearly different people (similarity < 35),
        # reject this result even when the title passed fuzzy matching.
        # This catches cases where a shared title prefix fools the title
        # matcher into accepting a completely different book from a different
        # author (field case: "La Dama Revelada" / Fanny Finch accepted a
        # Google result for "La dama de la reina" / Shannon Drake).
        # Threshold 35 is intentionally low — only blocks truly different
        # names; "Last, First" vs "First Last" formatting and minor
        # transliteration differences score well above 35.
        if book_author and rauthor_str:
            if not author_matches(book_author, rauthor_str, threshold=35):
                if log:
                    log.info('Author veto: skipping result from %s '
                             '(title matched but author %r ≠ %r)',
                             r.get('source', '?'), rauthor_str[:30], book_author[:30])
                continue

        # v6.2.26: tag each cover candidate with the language of the result
        # (edition) it came from, when known, so covers pulled from a
        # wrong-language edition (e.g. Google Books returning the Spanish
        # edition's cover for an Italian-language book) can be filtered out
        # downstream the same way wrong-language synopses are.
        r_lang = (r.get('language') or '').lower()[:2]
        cv = r.get('cover_url', '')
        if cv:
            cover_candidates.append((cv, weight, source_name, r_lang))
        for alt in r.get('cover_alts', []):
            if alt:
                cover_candidates.append((alt, max(1, weight - 1), source_name, r_lang))

        comments = r.get('comments', '')
        if comments and len(comments.strip()) >= 20:
            # v6.2.35: repair HTML/whitespace formatting artifacts (unescaped
            # &nbsp;, sentences glued together where a stripped paragraph
            # break used to be, embedded press-quotes glued onto their
            # attribution) BEFORE scoring/length checks below — see
            # core/synopsis_cleaner.py for what this does and doesn't do
            # (formatting repair only, never rewords/retranslates anything).
            comments = clean_synopsis(comments.strip())
            # Store (text, weight, result_lang, source_name) — result_lang is
            # what the source reported for this specific result, not the
            # book's lang.
            result_lang = (r.get('language') or '').lower()[:2]
            comment_candidates.append((comments, weight, result_lang, source_name))

        for key in ('authors', 'publisher', 'pubdate',
                    'rating', 'language', 'identifiers'):
            val = r.get(key)
            if val and key not in merged:
                merged[key] = val

        # ── Title: best-similarity wins, not first-by-weight ───────────────
        # BUG (fixed here): previously title was collected with the same
        # first-wins/weight-ordered loop as every other field.  Since Google
        # (weight=9) ranks above Amazon (weight=8), a Google wrong-book
        # title like 'La Mano de la Serpiente' beat Amazon's correct
        # 'La Cabeza de la Serpiente' just because Google's result appeared
        # first in the weight-sorted list.
        #
        # Fix: always pick the title whose similarity to book_title is
        # highest, regardless of source weight.  Weight is used as a
        # tie-breaker only when two titles score equally.  The book's own
        # title is also always a candidate (it can't be worse than any
        # provider's guess).
        rtitle_val = r.get('title', '')
        if rtitle_val:
            title_sim = similarity(book_title, rtitle_val) if book_title else 0
            existing  = merged.get('_title_candidate')   # (sim, weight, title)
            if existing is None or (title_sim, weight) > (existing[0], existing[1]):
                merged['_title_candidate'] = (title_sim, weight, rtitle_val)

        # ── Tags: collect all then filter, don't first-wins ────────────────
        # BUG (fixed here): tags used the same first-wins/weight loop, so
        # Google's 'Juvenile Nonfiction' (from a mismatched wrong-book
        # result that nonetheless passed the title fuzzy-threshold) won
        # over correct tags simply because Google had a higher weight.
        #
        # Fix: accumulate all tags from ALL sources that passed the title/
        # author veto, then apply a junk-tag blocklist and a title-match
        # bonus before building the final tag list.  Tags from a source
        # whose title similarity to the book title is high are preferred;
        # generic/wrong-genre tags from weak-match sources are filtered out.
        rtags = r.get('tags') or []
        if rtags:
            title_sim_for_tags = similarity(book_title, rtitle_val) if (book_title and rtitle_val) else 50
            merged.setdefault('_tag_candidates', []).append(
                (rtags, weight, title_sim_for_tags))

    if not merged and not comment_candidates:
        return None

    # ── Finalise title ──────────────────────────────────────────────────────
    tc = merged.pop('_title_candidate', None)
    if tc:
        merged['title'] = tc[2]
        if log and book_title and tc[2] != book_title:
            log.debug('Merge title: chose %r (sim=%d) over book title %r',
                      tc[2][:50], tc[0], book_title[:50])

    # ── Finalise tags ───────────────────────────────────────────────────────
    # Junk-tag blocklist: generic, wrong-genre, or content-free strings that
    # pollute the tag field when a source mismatches the book.
    _JUNK_TAGS_RE = re.compile(
        r'^(juvenile|nonfiction|fiction|juvenile fiction|juvenile nonfiction|'
        r'general|miscellaneous|unclassified|unknown|other|'
        r'libros en idiomas extranjeros|foreign language study|'
        r'english as a second language|language arts|'
        r'books?|ebooks?|kindle|digital)$',
        re.I,
    )
    tag_candidates = merged.pop('_tag_candidates', [])
    if tag_candidates:
        # Sort by (title_similarity DESC, weight DESC) so correct-match sources win
        tag_candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
        best_sim = tag_candidates[0][2]
        # Only use tags from sources whose title similarity is at least
        # as good as the best source's sim minus 20 points, to avoid
        # accepting tags from a clearly-mismatched source.
        sim_floor = max(0, best_sim - 20)
        seen_tags = []
        seen_lower = set()
        for rtags, _w, tsim in tag_candidates:
            if tsim < sim_floor:
                continue
            for tag in rtags:
                tag = tag.strip()
                tl = tag.lower()
                if not tag or tl in seen_lower:
                    continue
                if _JUNK_TAGS_RE.match(tl):
                    if log:
                        log.debug('Merge tags: dropped junk tag %r', tag)
                    continue
                seen_tags.append(tag)
                seen_lower.add(tl)
                if len(seen_tags) >= 15:
                    break
            if len(seen_tags) >= 15:
                break
        if seen_tags:
            merged['tags'] = seen_tags

    # If the only thing we collected is identifiers (no title, authors, synopsis,
    # cover, etc.) treat it as a failed fetch so the caller sees "no result" rather
    # than "Result OK — fields: identifiers".  Identifiers are saved in the
    # fetch_for_book caller separately via the ASIN/ISBN we already know.
    has_content = bool(merged.keys() & _CONTENT_KEYS) or bool(comment_candidates)
    if not has_content:
        if log:
            log.warning('Merge produced only identifiers — treating as no result '
                        '(all sources failed to extract title/synopsis/cover)')
        return None

    if comment_candidates:
        # Best synopsis scoring: (source_weight × 10) + text_quality + lang_bonus.
        #
        # lang_bonus (v6.2.18): +20 when the synopsis language matches the
        # book's language, -15 when it clearly doesn't.  This is strong
        # enough to prefer a slightly lower-weight same-language synopsis
        # over a higher-weight wrong-language one — e.g. Goodreads (weight
        # 10) returning an English synopsis for a Spanish book will lose to
        # Amazon (weight 8) returning a Spanish synopsis once the -15/+20
        # delta is applied.
        #
        # Language is determined in two steps:
        #   1. Use the 'language' field the source reported for this result.
        #   2. If absent/ambiguous, detect it from the synopsis text itself
        #      using _detect_synopsis_lang() (stop-word fingerprinting).
        # Neither step is perfect; if detection fails (returns '') no
        # bonus/penalty is applied so the old weight+quality scoring
        # decides as before.
        _target_lang = (book_lang or '').lower()[:2]

        def _comment_score(c):
            text, weight, result_lang = c[0], c[1], c[2]
            base = weight * 10 + synopsis_quality(text)
            if not _target_lang:
                return base
            # Determine synopsis language
            slang = result_lang or _detect_synopsis_lang(text)
            if not slang:
                return base          # can't tell — neutral
            if slang == _target_lang:
                return base + 60     # language matches ✔ (v6.2.26: widened
                                      # from +20 so a same-language synopsis
                                      # always beats a wrong-language one
                                      # regardless of weight/quality delta)
            return base - 60         # wrong language ✘ (v6.2.26: widened
                                      # from -15 for the same reason)

        scored_comments = sorted(comment_candidates, key=_comment_score, reverse=True)
        best_text, best_weight, _, _ = scored_comments[0]

        # v6.2.28 ROOT-CAUSE FIX: "Best synopsis chosen" always accepted
        # whatever scored highest even when EVERY candidate was garbage —
        # if a marketplace/seller-listing snippet ("Brand New. Ship
        # worldwide.", 25 chars) was the only thing collected, it still
        # "won" by default and got applied as if it were the book's real
        # synopsis. A hard floor now applies regardless of how the ranking
        # came out: too short, or a confirmed junk/boilerplate match (see
        # fuzzy._SYNOPSIS_JUNK_PATTERNS), means NO synopsis is set at all —
        # leaving the field empty (or the book's existing description
        # untouched) is strictly better than saving visible junk.
        _best_quality = synopsis_quality(best_text)
        _is_hard_junk = bool(_SYNOPSIS_JUNK_RE.search(best_text or ''))
        _synopsis_accepted = False
        if len((best_text or '').strip()) < 40 or _best_quality <= 5.0 or _is_hard_junk:
            if log:
                log.warning(
                    'Best synopsis candidate rejected as junk/too-short '
                    '(%d chars, quality=%.1f%s) — no synopsis will be set '
                    'from %d candidate(s): %r',
                    len(best_text or ''), _best_quality,
                    ' [matches junk pattern]' if _is_hard_junk else '',
                    len(comment_candidates), (best_text or '')[:80])
        else:
            merged['comments'] = best_text
            _synopsis_accepted = True
        if log and _synopsis_accepted:
            best_slang = scored_comments[0][2] or _detect_synopsis_lang(best_text)
            lang_note = ''
            if _target_lang:
                if best_slang == _target_lang:
                    lang_note = ', lang=✔ {} match'.format(_target_lang)
                elif best_slang:
                    lang_note = ', lang=✘ {} (book={})'.format(best_slang, _target_lang)
                else:
                    lang_note = ', lang=? undetermined'
            log.info('Best synopsis chosen: %d chars, weight=%d, quality=%.1f%s '
                      '(from %d candidate(s))',
                      len(best_text), best_weight, synopsis_quality(best_text),
                      lang_note,
                      len(comment_candidates))

        # ── Expose every candidate for the manual "Choose Description…"
        # dialog (dialogs.py: SynopsisChooserDialog) — previously only the
        # single winning synopsis was ever kept, so a user who preferred a
        # different (but still valid) source's description had no way to
        # get it back short of re-running the whole fetch with sources
        # disabled. Deduplicate by leading text so near-identical scrapes
        # from mirrored sources don't clutter the picker.
        # v6.2.26: if at least one candidate matches the book's language,
        # drop the mismatched ones from the manual picker entirely rather
        # than just sorting them lower. Previously every wrong-language
        # synopsis found by any source stayed in the "Choose Description…"
        # list forever, which is how an Italian book ended up with a picker
        # full of Spanish/English options and only one correct Italian one
        # buried among them. If NOTHING matches the target language, all
        # candidates are kept (better to offer a wrong-language synopsis
        # than none at all) and each is clearly labelled with its language.
        seen_synopsis = set()
        synopsis_candidates = []
        any_lang_match = False
        if _target_lang:
            for text, c_weight, result_lang, c_source in scored_comments:
                slang = result_lang or _detect_synopsis_lang(text)
                if slang == _target_lang:
                    any_lang_match = True
                    break
        for text, c_weight, result_lang, c_source in scored_comments:
            dedupe_key = text[:200]
            if dedupe_key in seen_synopsis:
                continue
            # v6.2.28: don't offer a marketplace-listing snippet or other
            # confirmed junk as a choosable "description" option either —
            # the same hard floor that gates auto-selection applies here.
            if len(text.strip()) < 40 or _SYNOPSIS_JUNK_RE.search(text):
                if log:
                    log.debug('Merge: dropping junk/too-short %s synopsis '
                              'from picker: %r', c_source, text[:60])
                continue
            slang = result_lang or _detect_synopsis_lang(text) or ''
            if _target_lang and any_lang_match and slang and slang != _target_lang:
                if log:
                    log.debug('Merge: dropping %s synopsis (lang=%s) from picker '
                              '— %s match(es) available', c_source, slang, _target_lang)
                continue
            seen_synopsis.add(dedupe_key)
            synopsis_candidates.append({
                'text':   text,
                'source': c_source,
                'weight': c_weight,
                'lang':   slang,
                'score':  _comment_score((text, c_weight, result_lang, c_source)),
            })
            if len(synopsis_candidates) >= 12:
                break
        merged['comment_candidates'] = synopsis_candidates

    if not merged:
        return None

    if prefs.get('normalize_lang', True) and 'language' in merged:
        merged['language'] = normalize_language(merged['language'])
    if 'publisher' in merged:
        merged['publisher'] = normalize_publisher(merged['publisher'])
    if 'pubdate' in merged:
        merged['pubdate'] = normalize_pubdate(merged['pubdate'])

    if probe_covers and cover_candidates:
        merged['cover_url'] = probe_best_cover(
            cover_candidates,
            timeout=prefs.get('cover_probe_timeout', 8),
            log=log,
        )
        if log:
            log.info('Best probed cover: %s', (merged.get('cover_url', '') or '')[:80])
    else:
        merged['cover_url'] = best_cover(
            cover_candidates,
            prefs.get('cover_min_size', 200),
        )

    # ── Build full/alt candidate lists (BUG FIX, v6.2.25) ───────────────────
    # ROOT CAUSE OF THE "padded Google Books cover chosen over the clean
    # Amazon cover" BUG: cover_candidates here collects every cover_url +
    # cover_alts from every source that passed the title/author match, but
    # historically only the SINGLE winner of best_cover()/probe_best_cover()
    # was ever written into merged['cover_url'] — merged['cover_alts'] was
    # never populated at all. probe_best_cover() only does a HEAD
    # Content-Length probe (no image download, no white-border check), so a
    # padded/letterboxed image with a larger file size than the clean image
    # (padding adds bytes) could win outright, and dialogs.py's
    # _fetch_best_cover() — which DOES do proper white-border/blank-image
    # filtering — never got a second candidate to fall back to, because
    # cover_alts was always empty. The padded cover then sailed through as
    # the only option.
    #
    # Fix: keep every deduplicated candidate URL (scored, best first) so
    # both the automatic padding-aware picker in dialogs.py and the new
    # manual Cover Chooser dialog have the real alternatives — e.g. a clean
    # full-bleed Amazon cover — available to prefer over a padded one.
    if cover_candidates:
        # v6.2.26: if any cover candidate comes from a result whose language
        # matches the book, drop candidates tagged with a confirmed *other*
        # language (covers with no language info, e.g. Goodreads/OpenLibrary
        # which don't reliably report per-cover language, are always kept —
        # only a confirmed mismatch is excluded). Mirrors the synopsis-picker
        # fix above and is what actually stops a Spanish-edition cover from
        # outranking the correct Italian one once Google/Amazon report
        # language correctly (see provider fixes in providers.py).
        _target_lang = (book_lang or '').lower()[:2]
        any_cover_lang_match = any(
            cl == _target_lang for _, _, _, cl in cover_candidates if cl
        ) if _target_lang else False

        seen_cover_urls = set()
        scored_covers = []
        for url, weight, source_name, c_lang in cover_candidates:
            if not url or url in seen_cover_urls:
                continue
            if (_target_lang and any_cover_lang_match and
                    c_lang and c_lang != _target_lang):
                if log:
                    log.debug('Merge: dropping %s cover (lang=%s) — %s match(es) '
                              'available', source_name, c_lang, _target_lang)
                continue
            seen_cover_urls.add(url)
            scored_covers.append((score_cover(url) + weight * 2, url, source_name, weight))
        scored_covers.sort(key=lambda x: -x[0])

        chosen_cover_url = merged.get('cover_url', '')
        merged['cover_alts'] = [
            u for _, u, _, _ in scored_covers if u != chosen_cover_url
        ][:12]
        merged['cover_candidates'] = [
            {'url': u, 'source': s, 'weight': w}
            for _, u, s, w in scored_covers
        ][:15]
        if log and len(scored_covers) > 1:
            log.info('Cover candidates: %d found across sources (best=%s…)',
                      len(scored_covers), (chosen_cover_url or '')[:60])

    merged['sources'] = list({r.get('source', '') for r in results if r.get('source')})
    return merged


# ── Browser pass ───────────────────────────────────────────────────────────────

def _run_browser_pass(active_sources, title, author, isbn, asin, lang,
                      results, lock, log):
    """
    Sequential browser pass — called only when the parallel first-pass fetch
    returned zero results AND use_browser_fallback is enabled in prefs.

    Re-runs every active browser-capable source ONE AT A TIME (no threads) so
    only one Firefox process is ever open at a time.  Sets
    providers._browser_pass_active = True for the duration so that each
    provider's internal _browser_fallback_enabled() check returns True,
    routing requests through browser_get() instead of urllib.

    Uses retries=0 so urllib fails fast (one attempt) before handing off to
    the browser — avoids wasting 2× retry delay on requests we know are
    bot-blocked.
    """
    try:
        import calibre_plugins.metadata_plus.providers.providers as _prov_mod  # type: ignore
        from calibre_plugins.metadata_plus.providers.browser_fetch import is_browser_available  # type: ignore
    except Exception:
        return
    if not is_browser_available():
        log.warning(
            'Browser pass: playwright/Firefox not found -- browser pass skipped. '
            'Go to plugin Options > Browser Fallback and click '
            '"Check / Install Playwright" to set it up.'
        )
        return

    candidates = [
        (name, fn, weight)
        for name, (fn, weight) in active_sources.items()
        if name in BROWSER_CAPABLE_SOURCES
    ]
    if not candidates:
        return

    log.info(
        'Browser pass: 0 results from parallel fetch -- retrying %d '
        'HTML-scrape source(s) via Firefox: %s',
        len(candidates),
        ', '.join(n for n, _, _ in candidates),
    )

    timeout = prefs.get('timeout', 20)
    _prov_mod._browser_pass_active = True
    try:
        for name, fn, weight in candidates:
            try:
                data = fn(title, author, isbn, asin=asin, lang=lang,
                          timeout=timeout, retries=0, log=log)
                if data:
                    data['_weight'] = weight
                    log.info(
                        'Browser pass: got result from %s: title=%r',
                        name, data.get('title', '')[:50],
                    )
                    with lock:
                        results.append(data)
            except Exception:
                log.error('Browser pass: %s raised an exception:',
                          name, exc_info=True)
    finally:
        _prov_mod._browser_pass_active = False


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_for_book(db, book_id):
    """
    Main entry point. Fetch metadata for a single book.
    Returns merged dict or None.
    """
    log = _get_logger()

    # Reset ALL per-book cooldowns so previous books' rate-limit hits
    # don't suppress sources for this book.
    reset_amazon_search_cooldown()
    reset_google_cooldown()

    try:
        mi = db.get_metadata(book_id, index_is_id=True)
    except TypeError:
        mi = db.get_metadata(book_id)
    title  = mi.title or ''
    author = ', '.join(mi.authors) if mi.authors else ''
    idents = mi.identifiers or {}

    isbn = idents.get('isbn', '') or ''
    asin = _extract_asin(idents)
    # Normalize the book's language code before using it for source routing.
    # Calibre sometimes stores legacy codes like 'sp' (Spanish) or 'iw' (Hebrew)
    # that don't match the ISO-639-1 codes used in _LANG_AUTO_SOURCES and
    # _LANG_TO_AMAZON_TLD. normalize_language() maps these to the canonical form.
    lang = normalize_language((mi.language or '').strip().lower())[:2]
    mobi_asin = idents.get('mobi-asin', '') or ''

    raw_title = title
    title = _sanitize_title(title, author)
    if title != raw_title:
        log.info('Title sanitized: %r -> %r', raw_title[:60], title[:60])

    raw_mobi_asin = idents.get('mobi-asin', '') or ''
    if raw_mobi_asin and not asin:
        log.warning(
            'mobi-asin %r is not a valid Amazon ASIN (expected 10 chars) — '
            'skipping ASIN-based lookups for this book', raw_mobi_asin[:40]
        )

    log.info('fetch_for_book: title=%r author=%r isbn=%r asin=%r lang=%r',
             title[:60], author[:40], isbn, asin or '(none)', lang or '(none)')

    # ── Step 1: ISBN repair ───────────────────────────────────────────────────
    if isbn and prefs.get('auto_isbn_repair', True):
        if not is_valid_isbn(isbn):
            repaired, _ = repair_isbn(isbn)
            if repaired:
                log.info('Repaired ISBN %s → %s', isbn, repaired)
                isbn = repaired
    if isbn:
        isbn = normalize_isbn(isbn) or isbn

    # ── Step 2: Auto-discover ISBN from ASIN (cheap path only) ───────────────
    discovered_isbn = ''
    if not isbn:
        discovered_isbn = _discover_isbn(title, author, asin, log)
        if discovered_isbn:
            isbn = discovered_isbn

    # ── Step 3: Cache lookup ──────────────────────────────────────────────────
    cache      = MetadataCache()
    cache_days = prefs.get('cache_days', 7)
    cache_key  = isbn or asin or title
    if cache_days > 0:
        cached = cache.get(title, author, cache_key, 'merged', cache_days)
        if cached and _is_substantive_result(cached):
            log.info('Cache hit for %r', title)
            return cached
        elif cached:
            # Stale entry from an older plugin version (pre has_content guard)
            # that stored an identifiers-only result. Discard and re-fetch.
            log.info('Cache hit for %r was identifiers-only (stale entry from '
                     'an older version) — discarding and re-fetching', title)

    # ── Step 4: Parallel fetch ────────────────────────────────────────────────
    # Determine which sources to run (includes language-specific auto-activation)
    active_sources = _sources_for_lang(lang)
    if log:
        log.info('Active sources for lang=%r: %s',
                 lang or 'any', ', '.join(sorted(active_sources.keys())))

    results = []
    lock    = threading.Lock()
    threads = []
    # source name -> 'ok' | 'empty' | 'error' — used only to print a one-line
    # per-source summary when the whole fetch comes back empty, so the cause
    # is visible at INFO level without needing to flip log_level to DEBUG.
    outcomes = {}

    for name, (fn, weight) in active_sources.items():
        t = threading.Thread(
            target=_fetch_source,
            args=(name, fn, title, author, isbn, asin, lang, weight, results, lock, log, outcomes),
            daemon=True,
        )
        threads.append(t)
        t.start()

    if _src_enabled('use_isbndb'):
        t = threading.Thread(
            target=_fetch_isbndb_source,
            args=(title, author, isbn, asin,
                  prefs.get('weight_isbndb', 8),
                  results, lock, log),
            daemon=True,
        )
        threads.append(t)
        t.start()

    _per_req_timeout = prefs.get('timeout', 20)
    _retries         = prefs.get('retries', 2)
    timeout_secs     = _per_req_timeout * (_retries + 1) + 5
    for t in threads:
        t.join(timeout=timeout_secs)

    log.info('Collected %d raw results for %r', len(results), title[:50])
    if not results and outcomes:
        # Self-diagnosing summary: which sources returned nothing and why,
        # without needing DEBUG log level. 'timeout' means the thread never
        # finished within the join() window (network hang / very slow site).
        summary = ', '.join('{}={}'.format(n, outcomes.get(n, 'timeout'))
                            for n in sorted(active_sources.keys()))
        log.info('Per-source outcome: %s', summary)

    # ── Step 4c: Browser pass ─────────────────────────────────────────────────
    # Trigger when the parallel fetch yielded NO usable result — meaning either:
    #   (a) zero raw results, or
    #   (b) raw results exist but ALL failed fuzzy title matching.
    # We detect (b) with a lightweight pre-merge (no cover-probing, no logging)
    # so the browser pass fires even when sources like Google/LOC returned a
    # result for a completely different book (a known failure mode for obscure
    # Kindle-only titles that have no print edition in any catalogue).
    if prefs.get('use_browser_fallback', False):
        _pre_merged = _merge_results(results, title, author,
                                     book_lang=lang,
                                     probe_covers=False, log=None)
        if _pre_merged is None:
            _before_browser_pass = len(results)
            _run_browser_pass(
                active_sources, title, author, isbn, asin, lang,
                results, lock, log,
            )
            _new_from_browser = len(results) - _before_browser_pass
            if _new_from_browser > 0:
                log.info('Browser pass collected %d new result(s) for %r',
                         _new_from_browser, title[:50])
            else:
                log.info('Browser pass: no additional results found via '
                         'browser fallback for %r', title[:50])

    # ── Step 4b: pick up ISBN the parallel fetch already found ─────────────
    if not isbn and not discovered_isbn:
        discovered_isbn = _isbn_from_results(results, log)
        if discovered_isbn:
            isbn = discovered_isbn

    # ── Step 5: Direct Open Library cover probe ───────────────────────────────
    lookup_isbn = isbn or ''
    if lookup_isbn and prefs.get('probe_openlibrary_cover', True):
        ol_cover = fetch_openlibrary_cover(
            lookup_isbn,
            timeout=prefs.get('cover_probe_timeout', 8),
            log=log,
        )
        if ol_cover:
            results.append({
                '_weight':   prefs.get('weight_openlibrary', 7),
                'cover_url': ol_cover,
                'source':    'Open Library (direct cover)',
            })
            log.info('Open Library direct cover: %s', ol_cover)

    # ── Step 6: Merge ─────────────────────────────────────────────────────────
    probe_covers = prefs.get('probe_cover_sizes', True)
    merged = _merge_results(results, title, author,
                            book_lang=lang,
                            probe_covers=probe_covers, log=log)

    if merged:
        if discovered_isbn:
            merged.setdefault('identifiers', {})
            merged['identifiers'].setdefault('isbn', discovered_isbn)
            log.info('Auto-discovered ISBN %s saved', discovered_isbn)
        if asin:
            merged.setdefault('identifiers', {})
            merged['identifiers'].setdefault('amazon', asin)
        if mobi_asin:
            merged.setdefault('identifiers', {})
            merged['identifiers'].setdefault('mobi-asin', mobi_asin)

        if cache_days > 0:
            cache.put(title, author, cache_key, 'merged', merged)
    else:
        log.warning('No merged result for %r (isbn=%r asin=%r, raw=%d)',
                    title[:50], isbn, asin, len(results))

    return merged


def detect_duplicates_in_library(db, book_ids):
    """Return list of (id1, id2) pairs that look like duplicates."""
    if not prefs.get('detect_duplicates', True):
        return []
    try:
        metas = [(bid, db.get_metadata(bid, index_is_id=True)) for bid in book_ids]
    except TypeError:
        metas = [(bid, db.get_metadata(bid)) for bid in book_ids]
    dupes = []
    seen  = set()
    for i, (id1, mi1) in enumerate(metas):
        for id2, mi2 in metas[i+1:]:
            pair = (min(id1, id2), max(id1, id2))
            if pair in seen:
                continue
            if is_duplicate(mi1, mi2,
                            prefs.get('fuzzy_threshold', 85),
                            max(60, prefs.get('fuzzy_threshold', 85) - 10)):
                dupes.append(pair)
                seen.add(pair)
    return dupes
