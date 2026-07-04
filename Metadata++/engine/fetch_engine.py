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
from calibre_plugins.metadata_plus.core.isbn_utils import normalize_isbn, repair_isbn, is_valid_isbn  # type: ignore
from calibre_plugins.metadata_plus.core.fuzzy import (  # type: ignore
    normalize_language, normalize_publisher, normalize_pubdate,
    title_matches, author_matches, is_duplicate, normalize_str,
    synopsis_quality,
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
    if not t:
        return t
    t = re.sub(r'\s*[\(\[][^()\[\]]{0,40}(edition|edición|ebook|kindle)[^()\[\]]{0,10}[\)\]]',
               '', t, flags=re.I)
    t = re.split(r'\s*[:/–—]\s*', t, maxsplit=1)[0]
    return t.strip()


def _merge_results(results, book_title, book_author, probe_covers=False, log=None):
    if not results:
        return None

    results_sorted = sorted(results, key=lambda r: r.get('_weight', 1), reverse=True)
    single_result = len(results_sorted) == 1

    title_unknown = (not book_title or
                     book_title.lower().strip() in _UNKNOWN_TITLES)

    merged = {}
    cover_candidates = []
    cover_candidate_rows = []
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
            if not passes and single_result:
                bt = normalize_str(_strip_edition_noise(book_title))
                rt = normalize_str(_strip_edition_noise(rtitle))
                if bt and rt and (rt.startswith(bt) or bt.startswith(rt)):
                    passes = True
                    if log:
                        log.info('Single-source result kept via title-prefix '
                                 'fallback (%r vs %r)', book_title[:40], rtitle[:40])
            if not passes:
                if log:
                    log.debug('Fuzzy title mismatch, skipping result from %s '
                              '(%r vs %r)', r.get('source', '?'), book_title[:40], rtitle[:40])
                continue

        cv = r.get('cover_url', '')
        if cv:
            cover_candidates.append((cv, weight))
            cover_candidate_rows.append({'url': cv, 'source': source_name, 'weight': weight})
        for alt in r.get('cover_alts', []):
            if alt:
                alt_weight = max(1, weight - 1)
                cover_candidates.append((alt, alt_weight))
                cover_candidate_rows.append({'url': alt, 'source': source_name, 'weight': alt_weight})

        comments = r.get('comments', '')
        if comments and len(comments.strip()) >= 20:
            comment_candidates.append((comments.strip(), weight, source_name))

        for key in ('title', 'authors', 'publisher', 'pubdate',
                    'tags', 'rating', 'language', 'identifiers'):
            val = r.get(key)
            if val and key not in merged:
                merged[key] = val

    if not merged and not comment_candidates:
        return None

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
        # Best synopsis = highest combined score of (source weight, text
        # quality), NOT raw character count. Previously this used
        # max(len(text), weight) which let a long but garbled/boilerplate
        # scrape from a low-trust source beat a short, clean synopsis from
        # a high-trust source like Google Books or Open Library.
        #
        # Scoring: weight is the dominant signal (×10, since weights only
        # range 1-10) and synopsis_quality() supplies a 0-100ish text-quality
        # score that rewards clean, well-formed prose and penalises
        # boilerplate/truncation/leftover markup.
        def _comment_score(c):
            text, weight = c[0], c[1]
            return weight * 10 + synopsis_quality(text)

        scored_comments = sorted(comment_candidates, key=_comment_score, reverse=True)
        best_text, best_weight, _best_source = scored_comments[0]
        merged['comments'] = best_text
        if log:
            log.info('Best synopsis chosen: %d chars, weight=%d, quality=%.1f '
                      '(from %d candidate(s))',
                      len(best_text), best_weight, synopsis_quality(best_text),
                      len(comment_candidates))

        seen_synopsis = set()
        synopsis_candidates = []
        for text, c_weight, c_source in scored_comments:
            dedupe_key = text[:200]
            if dedupe_key in seen_synopsis:
                continue
            seen_synopsis.add(dedupe_key)
            synopsis_candidates.append({
                'text': text,
                'source': c_source,
                'weight': c_weight,
                'lang': '',
                'score': _comment_score((text, c_weight, c_source)),
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

    if cover_candidate_rows:
        seen_cover_urls = set()
        scored_rows = []
        for cand in cover_candidate_rows:
            url = cand.get('url')
            if not url or url in seen_cover_urls:
                continue
            seen_cover_urls.add(url)
            scored_rows.append((score_cover(url) + cand.get('weight', 1) * 2, cand))
        scored_rows.sort(key=lambda item: -item[0])
        chosen_cover_url = merged.get('cover_url', '')
        merged['cover_candidates'] = [cand for _score, cand in scored_rows][:15]
        merged['cover_alts'] = [
            cand.get('url') for _score, cand in scored_rows
            if cand.get('url') and cand.get('url') != chosen_cover_url
        ][:12]

    merged['sources'] = list({r.get('source', '') for r in results if r.get('source')})
    return merged


# ── Browser pass ───────────────────────────────────────────────────────────────

def _run_browser_pass(active_sources, title, author, isbn, asin, lang,
                      results, lock, log, outcomes=None):
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
        if name in BROWSER_CAPABLE_SOURCES and (outcomes or {}).get(name) != 'ok'
    ]
    if not candidates:
        return

    log.info(
        'Browser pass: retrying %d '
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

    mi     = db.get_metadata(book_id, index_is_id=True)
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
        before_browser = len(results)

        _run_browser_pass(
            active_sources, title, author, isbn, asin, lang,
            results, lock, log, outcomes,
        )

        try:
            from calibre_plugins.metadata_plus.providers.browser_fetch import browser_close  # type: ignore
            browser_close()
        except Exception:
            pass

        after_browser = len(results)

        if after_browser > before_browser:
            log.info('Browser-capable pass added %d result(s) for %r',
                     after_browser - before_browser, title[:50])

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
    metas = [(bid, db.get_metadata(bid, index_is_id=True)) for bid in book_ids]
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
