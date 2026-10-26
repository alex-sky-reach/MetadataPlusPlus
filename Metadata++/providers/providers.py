#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""
Metadata providers — v6.2.14
New in v6.2.14 (Jadehawk Edits):
  - _page_is_audiobook(): removed the "soft signal" block (audible.com +
    acx.com links, 2+ required).  Amazon includes BOTH of these as footer
    links on EVERY product page, so they were never reliable product-type
    indicators and caused false positives on normal Kindle/print pages
    (confirmed with ASIN B0F344HDYN "Target Practice").  The three
    structural JSON signals (productGroup, binding, Listening Length) are
    sufficient.
  - _amazon_fetch(): added a one-time log.warning when urllib returns a
    bot-block page and the browser fallback is not active, telling the user
    to enable "Use Firefox browser as fallback" in plugin Options.  The
    warning fires at most once per Calibre session (module-level
    _browser_block_hint_logged flag) so it is not spammy.
  - browser_fetch.py: fixed Windows-incompatible && in the "install
    playwright" warning message; replaced with two numbered install steps.
  - fetch_engine.py _run_browser_pass(): upgraded silent log.info "browser
    pass skipped" to log.warning with step-by-step setup instructions so
    the user knows exactly how to enable the browser fallback.
  - config.py: added _InstallerThread (QThread) + _PlaywrightSetupDialog
    (QDialog) — a live-output wizard that runs "pip install playwright" then
    "playwright install firefox" with streaming progress and a final
    pass/fail banner.  _check_playwright() now opens this dialog instead of
    showing a static text panel.

Metadata providers — v6.2.13
New in v6.2.13:
  - _get(): Google 403s are now diagnosed instead of treated as a generic
    blocked response. Unlike the keyless 429 (shared anonymous per-minute
    quota), a 403 almost always means the configured API key itself has a
    problem — Books API not enabled for it, wrong project, a referer/IP
    restriction, or the key's *daily* (not per-minute) quota is exhausted —
    or, if no key is set, that the anonymous daily quota is exhausted. The
    response body's error message is now extracted and logged so the real
    cause is visible instead of a bare "HTTP 403".
  - All sources active by default per explicit user request — see
    fetch_engine.py v6.2.13. Reminder: this changes whether the plugin asks
    kobo.com/lafeltrinelli.it/fnac.es/libraccio.it/opac.sbn.it/
    catalogo.bne.es, not whether those sites respond — they were disabled
    specifically because field logs show them 403/404-ing every request.

Metadata providers — v6.2.12
New in v6.2.12:
  - _get(): fixed a real bug — HTTP 500/502/504 (transient server errors,
    e.g. the Internet Archive 502 seen in field logs) were never retried,
    unlike 429/503 which already had a backoff-and-retry path. A single
    502 on attempt 1 now correctly retries up to `retries` times with the
    same exponential backoff used for 429/503, instead of giving up
    immediately.
  - fetch_google: optional Google Books API key support (Options tab →
    "Google Books API Key"). Field logs show 429 firing on literally the
    very first Google call of a brand-new run — that pattern means the
    *anonymous* per-IP quota (shared across everyone hitting Google Books
    without a key from that IP/network) was already exhausted before this
    plugin even made a request, which no amount of in-plugin backoff can
    fix. A free key from Google Cloud Console gets a much higher quota and
    is appended to every request when set; left blank, behaviour is
    unchanged.
  - fetch_goodreads: search misses are now logged at INFO instead of DEBUG,
    so "goodreads=empty" in the per-source outcome line is no longer
    indistinguishable from a silent failure — you can now see in the log
    whether Goodreads genuinely has no listing for a title (common for
    very obscure self-published books) vs. something else going wrong.
    Link-matching regex also widened to handle single-quoted and absolute
    -URL hrefs in the search results page.

Metadata providers — v6.2.11
New in v6.2.11:
  - NEW fetch_goodreads: Goodreads (goodreads.com) HTML scrape — registered
    as a global, on-by-default source with a high weight specifically
    because its synopses are usually long, clean, and untruncated, so they
    tend to win the best-synopsis scoring in fetch_engine._merge_results
    (see that file's v6.2.11 changelog entry). Also supplies rating and
    genre tags.
  - fetch_worldcat now returns immediately without making any network call,
    regardless of the use_worldcat toggle's stored value. xisbn.worldcat.org
    has been dead since 2016, but a stale persisted True from an old config
    (use_worldcat was missing from the v6.2.9 stale-prefs migration) was
    still triggering a real connection attempt on every run, surfacing as a
    raw socket reset ("[WinError 10054] ... interrotta ... dall'host
    remoto") in field logs instead of a clean HTTP failure. Fixed at both
    layers: config.py's migration now also clears use_worldcat, and this
    function no longer makes the dead call even if some other on-disk
    config still has it set to True.

Metadata providers — v6.2.10
New in v6.2.10:
  - fetch_amazon: added _amazon_page_is_blocked(), a broader bot-challenge
    page detector. The previous code only checked for one CAPTCHA-page
    string ("Enter the characters"), so several other Amazon interstitial
    pages (the "Sorry, we just need to make sure you're not a robot" page,
    the automated-access warning page, etc.) were being treated as real
    HTML — fed straight to the title parser, which correctly found no real
    product title in them and returned nothing, with zero indication of
    *why*. Every dead end in fetch_amazon now logs whether the page was a
    confirmed bot-block or a real page the parser genuinely failed on.
  - fetch_amazon: added realistic Sec-Fetch-*/Sec-Ch-Ua/Cache-Control
    headers (matching what an actual Chrome navigation sends) and a small
    randomized pre-search delay. Field logs showed the /s? search endpoint
    503-ing on the very first attempt for nearly every book, which looks
    like edge-WAF fingerprinting of non-browser-shaped requests rather
    than pure per-request rate limiting.
  - _parse_amazon_page now accepts an optional `log` param so the
    audiobook-page bailout is visible in diagnostics instead of silent.

Metadata providers — v6.2.7
New in v6.2.7:
  - fetch_kobo (dead stub) replaced with real regional Kobo store providers:
    fetch_kobo_com, fetch_kobo_es, fetch_kobo_it, fetch_kobo_fr, fetch_kobo_de.
    Each provider targets the matching Kobo storefront via the public search
    endpoint (store.kobobooks.com/<locale>/Search?Query=…) and parses JSON-LD /
    og: tags from the product page.  The old monolithic 'kobo' source is gone;
    regional sources auto-activate exactly like Feltrinelli/BNE/BNF do.
  - fetch_bne: primary endpoint changed from datos.bne.es/api/obras.json
    (returns 404 as of 2024) to the BNE SRU catalogue endpoint
    (bne.es/es/Catalogos/BibliografiaEspanola/…); HTML fallback also updated
    to use the modern catalogue.bne.es search URL format.
  - fetch_fnac_es: added Sec-Fetch-* and cache-control headers that reduce
    the 403 rate on fnac.es; added a plain-text fallback search URL pattern
    that works even when the full search page is blocked.

New in v6.2.6 (bugfix):
  - fetch_amazon ISBN dp/ lookup: added local-TLD fallback (e.g. amazon.it
    for Italian ISBNs) mirroring the existing ASIN dp/ fallback — regional
    ISBNs that redirect on amazon.com now resolve correctly.

New in v6.2.5:
  - fetch_amazon search fallback: strip "(Spanish Edition)" / "(Edición…)"
    and subtitle noise from the query before searching — prevents Amazon
    from surfacing a print-edition ISBN-10 in data-asin instead of the
    Kindle ASIN.
  - fetch_amazon search fallback: try up to 5 data-asin candidates instead
    of only the first; real ASINs (contain a letter) are tried before
    pure-digit ISBN-10 values; each candidate is only kept if _parse_amazon_page
    returns a non-empty title.
  - fetch_amazon search fallback: log "trying next" when a dp/ page yields
    no title so the behaviour is visible in the run log.

New in v6.2.4:
  - _parse_amazon_page: added _AMAZON_JUNK_TITLES blocklist so og:title
    values like "Amazon.es" (returned by bot-challenged or redirect pages)
    are rejected rather than stored as the book title.
  - _parse_amazon_page: centralised _clean_amazon_title() helper validates
    every title candidate before accepting it — applied to all 6 extraction
    patterns so a junk value in any slot can't slip through.
  - _parse_amazon_page: added data-feature-name="title" / id="dp-title"
    patterns (newer SPA layout used on .es/.it) as pattern 2.
  - _parse_amazon_page: og:title now also matched when content= attribute
    appears before property= (attribute order varies across storefronts).
  - _parse_amazon_page: JSON-LD pattern uses .{0,3000}? (allows any char
    including '}') instead of [^}]{0,2000} which broke on nested objects.

New in v6.2.3:
  - _parse_amazon_page: added 4 additional title extraction patterns (JSON-LD
    "name", og:title, React/Apollo JSON, <title> tag) so regional storefronts
    like amazon.es that don't always render id="productTitle" now return a
    title rather than an identifiers-only dict that gets discarded by merge.
  - _parse_amazon_page: now returns {} (not an identifiers-only dict) when no
    title can be extracted — prevents "Merge produced only identifiers" warning.
  - _parse_amazon_page: added JSON-LD and og:author fallbacks for author
    extraction on regional storefronts.
  - fetch_amazon: sets locale-appropriate Accept-Language header (e.g.
    es-ES for amazon.es) so regional storefronts serve their native HTML
    layout where productTitle and author spans are reliably present.

New in v6.2:
  - fetch_amazon: now routes to language-appropriate Amazon storefront
    (amazon.es for Spanish, amazon.it for Italian, amazon.fr for French,
    amazon.de for German, amazon.co.jp for Japanese, amazon.com.br for
    Portuguese-BR) rather than always hitting amazon.com. This is the main
    fix for 503 errors on non-English books — amazon.com actively bot-blocks
    searches for titles in languages it doesn't primarily serve.
  - fetch_amazon: per-book cooldown reset means a 503 on one book no longer
    suppresses the search fallback for ALL subsequent books in the run.
  - fetch_google: Google Books 429 cooldown is now per-book (not session-wide)
    so a rate-limit hit on book N doesn't poison every later book. Backoff
    is shorter and smarter: 2 s initial, max 8 s, never retried after 429.
  - NEW fetch_casadellibro: Casa del Libro (casadellibro.com) — major Spanish
    bookstore with rich metadata for Spanish-language titles.
  - NEW fetch_fnac_es: FNAC Spain (fnac.es) — good Spanish coverage.
  - NEW fetch_feltrinelli: Feltrinelli (lafeltrinelli.it) — largest Italian
    bookstore chain, rich metadata for Italian titles.
  - NEW fetch_libraccio: Libraccio (libraccio.it) — Italian second-hand /
    general books with good coverage.
  - NEW fetch_bnf: Bibliothèque nationale de France (data.bnf.fr) — open
    SPARQL / JSON-LD API, good for French books.
  - NEW fetch_bne: Biblioteca Nacional de España (bne.es) SRU endpoint —
    excellent for Spanish-language books including Latin American editions.
  - NEW fetch_sbn: Servizio Bibliotecario Nazionale (sbn.it) SRU endpoint
    — Italian national library catalogue; best authority for Italian ISBNs.
  - All new providers accept the same (title, author, isbn, asin, lang,
    timeout, retries, log) signature as all existing providers.

Bugfixes carried forward from v6.1:
  - fetch_amazon: `lang` kwarg accepted (was missing → TypeError on every call)
  - fetch_google: langRestrict removed; best-scored candidate selected
  - fetch_openlibrary: work-level description fetched for title/author path
  - All providers: no language restriction anywhere
"""

import os
import re
import json
import time
import ssl
import hashlib

try:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode, quote_plus
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError # type: ignore
    from urllib import urlencode, quote_plus # type: ignore

from calibre_plugins.metadata_plus.core.fuzzy import similarity, normalize_str, normalize_language  # type: ignore
from calibre_plugins.metadata_plus.core.isbn_utils import isbn13_to_10  # type: ignore

# ── Browser fallback (Playwright/Firefox) ─────────────────────────────────────
# Optional layer that routes bot-blocked requests through a real Firefox
# browser. Only active when playwright is installed AND the
# 'use_browser_fallback' pref is True in plugin Options.
# Falls back silently to the standard urllib path when unavailable.
try:
    from calibre_plugins.metadata_plus.providers.browser_fetch import (  # type: ignore
        browser_get as _browser_get,
        is_browser_available as _is_browser_available,
    )
except Exception:
    def _browser_get(*args, **kwargs): return None      # noqa: E306
    def _is_browser_available(): return False           # noqa: E306


# Module-level flag: set to True by fetch_engine during the orchestrated
# browser pass (sequential, triggered after the parallel first-pass returns
# zero results).  False in normal operation so NO inline browser calls fire
# while all providers are running concurrently in their own threads.
_browser_pass_active = False
# One-time flag: suppress repeat warnings about missing browser when Amazon
# returns a block page.  Reset each calibre launch (module-level).
_browser_block_hint_logged = False


def _browser_fallback_enabled():
    """Return True only during the engine-controlled sequential browser pass."""
    return _browser_pass_active and _is_browser_available()


# ── Browser-first fetch helpers ────────────────────────────────────────────────
# Amazon and Goodreads are ALWAYS fetched via Firefox first (when Playwright is
# available), falling back to urllib only if the browser call fails or returns
# nothing.  This is independent of _browser_pass_active so the browser fires
# during BOTH the normal parallel pass AND the sequential browser pass.

def _amazon_fetch(url, timeout, retries, hdrs, log):
    """
    Browser-first fetch for an Amazon URL.  Never returns a bot-block page.
    Falls back to urllib when playwright is not available or the browser fails.
    """
    if _is_browser_available():
        if log:
            log.info('Amazon: fetching via browser: %s', url[:80])
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
        if raw and not _amazon_page_is_blocked(raw):
            return raw
        if raw and log:
            log.debug('Amazon: browser returned a block page for %s', url[:60])
        elif not raw and log:
            log.debug('Amazon: browser returned no content for %s -- falling back to urllib', url[:60])
    # urllib fallback (also used when playwright is not installed)
    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if raw and _amazon_page_is_blocked(raw):
        if log:
            log.debug('Amazon: urllib also returned a block page for %s', url[:60])
        global _browser_block_hint_logged
        if not _browser_block_hint_logged and not _is_browser_available():
            _browser_block_hint_logged = True
            if log:
                log.warning(
                    'Amazon: page blocked by bot-detection and browser fallback is not '
                    'active. Enable "Use Firefox browser as fallback" in plugin Options '
                    'for better results.')
        return None
    return raw


def _goodreads_fetch(url, timeout, retries, hdrs, log):
    """
    Browser-first fetch for a Goodreads URL.  Falls back to urllib when
    playwright is not available or the browser returns nothing.
    Independent of _browser_pass_active.
    """
    if _is_browser_available():
        if log:
            log.info('Goodreads: fetching via browser: %s', url[:80])
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
        if raw:
            return raw
        if log:
            log.debug('Goodreads: browser returned no content for %s -- falling back to urllib', url[:60])
    return _get(url, timeout, retries, headers=hdrs, log=log)


UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
      'AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/124.0.0.0 Safari/537.36')


# ── Amazon bot-challenge / interstitial page detection ────────────────────────
# Amazon serves several different anti-bot pages depending on storefront,
# trigger reason, and A/B test bucket — not just the classic CAPTCHA. Only
# checking for "Enter the characters" (the CAPTCHA page text) let several
# other block-page variants slip through as if they were real HTTP 200
# product pages: the parser would then correctly find no real title in them
# (there isn't one), return {}, and the caller had no way to tell "this was
# a block page" apart from "this was a real page the parser failed on".
# This function is the single source of truth for "is this raw HTML
# actually a usable product/search page" and is used everywhere fetch_amazon
# decides whether to bother parsing a response.
_AMAZON_BLOCK_SIGNATURES = (
    'Enter the characters',          # classic image CAPTCHA page
    'api-services-support',          # API throttle / support redirect
    'Sorry, we just need to make sure',  # "are you a robot" interstitial
    'To discuss automated access',   # automated-access warning page
    'captcha',                        # generic catch-all (case-insensitive check below)
    'Type the characters you see',
    'something went wrong on our end',
)

def _amazon_page_is_blocked(raw):
    """Return True if `raw` looks like an Amazon bot-block/interstitial page
    rather than real product/search HTML."""
    if not raw:
        return True
    low = raw.lower()
    for sig in _AMAZON_BLOCK_SIGNATURES:
        if sig.lower() in low:
            return True
    return False

# ── Amazon storefront routing ──────────────────────────────────────────────────
# Map ISO-639-1 language codes to the most relevant Amazon TLD.
# This avoids sending Spanish/Italian/French searches to amazon.com which
# actively 503s non-English queries.
_LANG_TO_AMAZON_TLD = {
    'es': 'amazon.es',
    'it': 'amazon.it',
    'fr': 'amazon.fr',
    'de': 'amazon.de',
    'ja': 'amazon.co.jp',
    'pt': 'amazon.com.br',
    'nl': 'amazon.nl',
    'pl': 'amazon.pl',
    'sv': 'amazon.se',
    'tr': 'amazon.com.tr',
    'ar': 'amazon.ae',
    'hi': 'amazon.in',
    'zh': 'amazon.cn',
}
_DEFAULT_AMAZON_TLD = 'amazon.com'

# Map Amazon TLD → Accept-Language header value so that regional storefronts
# return their native-language HTML (the title/author spans differ between
# the English and localised layouts — sending en-US to amazon.es causes it
# to serve a partially-English page where productTitle may be absent).
_AMAZON_TLD_TO_ACCEPT_LANG = {
    'amazon.es':     'es-ES,es;q=0.9',
    'amazon.it':     'it-IT,it;q=0.9',
    'amazon.fr':     'fr-FR,fr;q=0.9',
    'amazon.de':     'de-DE,de;q=0.9',
    'amazon.co.jp':  'ja-JP,ja;q=0.9',
    'amazon.com.br': 'pt-BR,pt;q=0.9',
    'amazon.nl':     'nl-NL,nl;q=0.9',
    'amazon.pl':     'pl-PL,pl;q=0.9',
    'amazon.se':     'sv-SE,sv;q=0.9',
    'amazon.com.tr': 'tr-TR,tr;q=0.9',
    'amazon.ae':     'ar-AE,ar;q=0.9',
    'amazon.in':     'hi-IN,hi;q=0.5,en-IN;q=0.9',
    'amazon.cn':     'zh-CN,zh;q=0.9',
}


def _amazon_tld_for_lang(lang):
    """Return the best Amazon TLD for a given ISO-639-1 language code."""
    if not lang:
        return _DEFAULT_AMAZON_TLD
    return _LANG_TO_AMAZON_TLD.get(lang.lower()[:2], _DEFAULT_AMAZON_TLD)


# ── Per-language Amazon search cooldowns ──────────────────────────────────────
# We maintain a separate cooldown bucket per Amazon TLD so that a 503 from
# amazon.es does not also suppress searches on amazon.com (different IP
# treatment, different throttle windows).
_amazon_search_cooldowns = {}  # tld -> float (epoch when cooldown expires)

def _amazon_search_in_cooldown(tld):
    return time.time() < _amazon_search_cooldowns.get(tld, 0.0)

def _amazon_search_trip_cooldown(tld, seconds=60):
    _amazon_search_cooldowns[tld] = time.time() + seconds

def reset_amazon_search_cooldown():
    """Reset ALL Amazon search cooldowns at the start of each fetch run."""
    _amazon_search_cooldowns.clear()


# ── Google Books cooldown (per-book, not session-wide) ────────────────────────
# Resets to 0 at the start of each book's fetch so a 429 on book N only
# affects book N, not every subsequent book in the library run.
_google_cooldown_until = [0.0]

def _google_in_cooldown():
    return time.time() < _google_cooldown_until[0]

def _google_trip_cooldown(seconds=30):
    """Short per-book cooldown — 30 s is enough, and it resets per book anyway."""
    _google_cooldown_until[0] = time.time() + seconds

def reset_google_cooldown():
    """Call at the start of each book's fetch to clear any leftover Google cooldown."""
    _google_cooldown_until[0] = 0.0


# ── Session-level LOC block ────────────────────────────────────────────────────
_loc_blocked = [False]

def _loc_mark_blocked():
    _loc_blocked[0] = True

def _loc_is_blocked():
    return _loc_blocked[0]


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _get(url, timeout=20, retries=2, headers=None, log=None):
    is_google = 'googleapis.com/books' in url
    if is_google and _google_in_cooldown():
        if log:
            log.debug('Skipping Google Books call (per-book cooldown): %s', url[:80])
        return None

    hdrs = {'User-Agent': UA, 'Accept': 'application/json, text/html, */*'}
    if headers:
        hdrs.update(headers)
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=hdrs)
            resp = urlopen(req, timeout=timeout)
            return resp.read().decode('utf-8', errors='replace')
        except HTTPError as e:
            if log:
                log.warning('HTTP %s for %s (attempt %d)', e.code, url[:80], attempt+1)
            if e.code == 429 and is_google:
                _google_trip_cooldown(30)
                return None
            if e.code == 403 and is_google:
                # Unlike a keyless 429 (shared anonymous quota throttling),
                # a 403 here almost always means something is wrong with the
                # configured API key itself (not enabled for the Books API,
                # wrong project, restricted referer/IP, or the key's *daily*
                # quota — separate from the per-minute one — is exhausted).
                # Surface Google's actual error message so the real cause is
                # visible instead of a bare "HTTP 403".
                reason = ''
                try:
                    body = e.read().decode('utf-8', errors='replace')
                    rm = re.search(r'"message"\s*:\s*"([^"]+)"', body)
                    if rm:
                        reason = rm.group(1)
                except Exception:
                    pass
                if log:
                    log.warning(
                        'Google Books 403%s — if you set an API key in Options, '
                        'verify the "Books API" is enabled for it in Google Cloud '
                        'Console and that it has no referer/IP restriction; if you '
                        'left the key blank, this can also mean the daily '
                        '(not per-minute) anonymous quota is exhausted.',
                        ': {}'.format(reason) if reason else '')
                _google_trip_cooldown(30)
                return None
            if e.code == 403:
                if 'loc.gov' in url:
                    _loc_mark_blocked()
                    if log:
                        log.warning('LOC: 403 received — marking as blocked for this session')
                return None
            if e.code == 404:
                return None
            if e.code == 503 and 'amazon.' in url:
                # Extract TLD from URL for per-TLD cooldown
                tld_m = re.search(r'(amazon\.[a-z.]+)/', url)
                tld = tld_m.group(1) if tld_m else 'amazon.com'
                if '/s?' in url or 'field-keywords' in url:
                    _amazon_search_trip_cooldown(tld, 60)
                    if log:
                        log.warning('Amazon search 503 on %s — tripping cooldown 60s', tld)
                return None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            return None
        except URLError as e:
            reason = getattr(e, 'reason', None)
            is_ssl_error = isinstance(reason, ssl.SSLError)
            if is_ssl_error and attempt == 0:
                if log:
                    log.warning('SSL handshake error on %s (attempt %d) — retrying: %s',
                                url[:80], attempt + 1, reason)
                time.sleep(2)
                continue
            if log:
                log.warning('URLError %s (attempt %d)', e, attempt+1)
            if attempt < retries:
                time.sleep(1)
                continue
            return None
        except ssl.SSLError as e:
            if attempt == 0:
                if log:
                    log.warning('SSL error on %s (attempt %d) — retrying: %s',
                                url[:80], attempt + 1, e)
                time.sleep(2)
                continue
            if log:
                log.warning('SSL error on %s (attempt %d, giving up): %s', url[:80], attempt + 1, e)
            return None
        except Exception as e:
            if log:
                log.warning('Error fetching %s: %s', url[:80], e)
            return None
    return None


def _jget(url, timeout=20, retries=2, log=None, headers=None):
    raw = _get(url, timeout, retries, headers=headers, log=log)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _head_content_length(url, timeout=10, log=None):
    """
    Return the byte size of the resource at `url`, or 0 on failure.

    v6.2.23: Amazon's image CDN (m.media-amazon.com / images-na.ssl-
    images-amazon.com) frequently returns 403/empty-body on HEAD requests
    even though the same URL serves a GET just fine — a known anti-
    hotlinking behaviour, not a sign the image doesn't exist. Since
    probe_best_cover() drops any candidate whose probed size comes back
    as 0, this silently disqualified real, high-resolution Amazon covers
    (already upgraded to _SL1500_ by _upgrade_amazon_cover) in favour of
    a lower-resolution Google Books cover that happens to answer HEAD
    cleanly — exactly the "wrong/lower-quality cover gets applied" bug
    reported by users whose book already had the correct high-res Amazon
    art.

    Fix: try HEAD first (cheap, no body download). If it fails or returns
    no usable Content-Length, fall back to a ranged GET (Range: bytes=0-0)
    — most CDNs that block HEAD still honour ranged GETs — and read the
    real size from the Content-Range header. As a last resort, do a plain
    GET and measure len(data) directly. A Referer header matching the
    image host's own site is also added, since some CDNs (Amazon's
    included) use it as a lightweight hotlink check.
    """
    def _referer_for(u):
        lu = u.lower()
        if 'media-amazon.com' in lu or 'ssl-images-amazon.com' in lu:
            return 'https://www.amazon.com/'
        if 'books.google.com' in lu or 'googleusercontent.com' in lu:
            return 'https://books.google.com/'
        return None

    headers = {'User-Agent': UA}
    ref = _referer_for(url)
    if ref:
        headers['Referer'] = ref

    # 1. Plain HEAD
    try:
        req = Request(url, headers=headers)
        req.get_method = lambda: 'HEAD'
        resp = urlopen(req, timeout=timeout)
        cl = resp.headers.get('Content-Length', '0')
        n = int(cl) if cl and str(cl).isdigit() else 0
        if n > 0:
            return n
    except Exception as e:
        if log:
            log.debug('HEAD failed %s: %s', url[:80], e)

    # 2. Ranged GET — ask for 1 byte, read the real size off Content-Range.
    #    Many hosts (including Amazon's image CDN) block HEAD but allow this.
    try:
        range_headers = dict(headers)
        range_headers['Range'] = 'bytes=0-0'
        req = Request(url, headers=range_headers)
        resp = urlopen(req, timeout=timeout)
        cr = resp.headers.get('Content-Range', '')  # e.g. 'bytes 0-0/123456'
        if cr and '/' in cr:
            total = cr.rsplit('/', 1)[-1].strip()
            if total.isdigit():
                return int(total)
        cl = resp.headers.get('Content-Length', '0')
        n = int(cl) if cl and str(cl).isdigit() else 0
        if n > 1:  # a real Content-Length here (not just the 1 ranged byte)
            return n
    except Exception as e:
        if log:
            log.debug('Ranged GET failed %s: %s', url[:80], e)

    # 3. Last resort — full GET, measure actual bytes downloaded.
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=timeout)
        data = resp.read()
        if data:
            return len(data)
    except Exception as e:
        if log:
            log.debug('Fallback GET failed %s: %s', url[:80], e)

    return 0


def _http_get_bytes(url, timeout=10, log=None):
    """
    Download and return the full response body of `url`, or b'' on
    failure. Used where we need to actually inspect image content (e.g.
    Google Books placeholder-hash comparison) rather than just its size.
    """
    headers = {'User-Agent': UA}
    lu = url.lower()
    if 'media-amazon.com' in lu or 'ssl-images-amazon.com' in lu:
        headers['Referer'] = 'https://www.amazon.com/'
    elif 'books.google.com' in lu or 'googleusercontent.com' in lu:
        headers['Referer'] = 'https://books.google.com/'
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=timeout)
        return resp.read() or b''
    except Exception as e:
        if log:
            log.debug('_http_get_bytes failed %s: %s', url[:80], e)
        return b''


# ── Cover helpers ──────────────────────────────────────────────────────────────

def _upgrade_amazon_cover(url):
    if not url:
        return url
    u = re.sub(r'\._[A-Z]{2}\d+_', '._SL1500_', url)
    if u == url:
        u = re.sub(r'_SL\d+_', '_SL1500_', url)
    if u == url:
        u = re.sub(r'_AC_\w+_', '_AC_SL1500_', url)
    return u


def _upgrade_openlibrary_cover(url):
    if not url:
        return url
    return re.sub(r'-(S|M)\.jpg', '-L.jpg', url, flags=re.IGNORECASE)


def _google_cover_from_id(volume_id):
    if not volume_id:
        return ''
    return ('https://books.google.com/books/publisher/content'
            '?id={}&printsec=frontcover&img=1&zoom=1'
            '&source=gbs_api'.format(volume_id))


def is_audiobook_cover(url):
    """
    Return True when a cover URL almost certainly belongs to an audiobook
    edition rather than a print/ebook edition.

    Audiobook covers slip in from two main sources:
      • Amazon: Audible titles stored under /Audible/ CDN paths, or ASIN
        pages for Audible editions (B0… ASINs whose dp/ page is an
        Audible product).
      • Google Books / Open Library: occasionally index the Audible edition
        ahead of the print edition for audio-first releases.

    We check the URL for known audiobook CDN hostnames and path fragments.
    This is a URL-only heuristic — cheap, no network call needed.
    The page-level check (title contains "Unabridged", product type is
    Audible) is done separately in _parse_amazon_page and fetch_amazon.
    """
    if not url:
        return False
    u = url.lower()
    # Audible / ACX CDN hostnames
    audiobook_hosts = (
        'images-na.ssl-images-amazon.com/images/i/audible',
        'acx-prod',
        'images.audible',
        'm.media-amazon.com/images/i/audible',
    )
    for h in audiobook_hosts:
        if h in u:
            return True
    # Audible product page path fragments
    audiobook_paths = (
        '/audible/',
        'audiblecdn',
        'acx-images',
        'audible_',
    )
    for p in audiobook_paths:
        if p in u:
            return True
    return False


def score_cover(url):
    """
    Heuristic quality score for a cover URL (0–100).
    Higher = larger / higher-resolution image.
    Audiobook covers are penalised to -1 so they are always ranked last
    and will never beat even a mediocre book cover.
    """
    if not url:
        return 0
    # Hard veto: audiobook covers get a score that can never win
    if is_audiobook_cover(url):
        return -1

    score = 50
    u = url.lower()
    for hint in ('sl1500', 'sl1200', 'sl800', 'sl500', 'large', 'hires',
                 'highres', 'w800', 'w600', '-l.jpg', 'zoom=3', 'zoom=6',
                 '1920', '1228'):
        if hint in u:
            score += 25
            break
    for hint in ('sl160', 'sl75', 'thumb', 'small', 'tiny', '-s.jpg',
                 '-m.jpg', 'zoom=0', 'zoom=1', 'sz=', 'resize='):
        if hint in u:
            score -= 20
            break
    if url.startswith('https'):
        score += 5
    return max(0, min(100, score))


def measure_image_bytes(data):
    """
    Return (width, height) in pixels from raw image bytes, or (0, 0) on failure.
    Supports PNG, JPEG and WEBP without requiring Pillow — reads the file
    header only, which is always present in the first ~30 bytes.

    BUG FIXED: the original implementation only handled the most common JPEG
    SOF0/SOF2 markers and would silently return (0, 0) for:
      - Progressive JPEGs with SOF2 markers preceded by unusual segments
      - JPEG 2000 / JFIF variants
      - Images returned by Calibre's db.cover() which may be converted
        internally and padded differently

    Fix: when the fast header-only parser returns (0, 0), fall back to Pillow
    (always available inside Calibre's bundled Python environment) for a
    complete, reliable parse.  The fast path is tried first so the common
    case has zero overhead; Pillow is only called if the fast path fails.
    """
    if not data or len(data) < 24:
        return (0, 0)
    import struct

    # ── Fast header-only path ─────────────────────────────────────────────
    # PNG: magic 8 bytes, then IHDR chunk (4 len + 4 type + 4W + 4H)
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        try:
            w, h = struct.unpack('>II', data[16:24])
            if w > 0 and h > 0:
                return (w, h)
        except Exception:
            pass

    # JPEG: scan for SOF0 / SOF1 / SOF2 / SOF3 markers
    if data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xff:
                break
            marker = data[i + 1]
            # SOF0=0xC0  SOF1=0xC1  SOF2=0xC2  SOF3=0xC3 — all contain dimensions
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                try:
                    h, w = struct.unpack('>HH', data[i + 5:i + 9])
                    if w > 0 and h > 0:
                        return (w, h)
                except Exception:
                    break
            # Skip to next segment; 0xD8 (SOI) and 0xD9 (EOI) have no length
            if marker in (0xD8, 0xD9):
                i += 2
                continue
            try:
                seg_len = struct.unpack('>H', data[i + 2:i + 4])[0]
            except Exception:
                break
            i += 2 + seg_len

    # WEBP: RIFF....WEBPVP8 / VP8L / VP8X
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        chunk = data[12:16]
        if chunk == b'VP8 ' and len(data) > 30:
            try:
                w = struct.unpack('<H', data[26:28])[0] & 0x3FFF
                h = struct.unpack('<H', data[28:30])[0] & 0x3FFF
                if w > 0 and h > 0:
                    return (w + 1, h + 1)
            except Exception:
                pass
        elif chunk == b'VP8L' and len(data) > 25:
            try:
                bits = struct.unpack('<I', data[21:25])[0]
                w = (bits & 0x3FFF) + 1
                h = ((bits >> 14) & 0x3FFF) + 1
                if w > 0 and h > 0:
                    return (w, h)
            except Exception:
                pass

    # ── Pillow fallback ───────────────────────────────────────────────────
    # Reached only when the fast header parser failed.  Pillow is bundled
    # with Calibre so it's always available inside a plugin; using it here
    # handles progressive JPEGs, JPEG 2000, GIF, TIFF, BMP, and any other
    # format the fast path doesn't cover.
    try:
        from PIL import Image  # type: ignore  # available in Calibre's Python
        import io
        with Image.open(io.BytesIO(data)) as img:
            w, h = img.size
            if w > 0 and h > 0:
                return (w, h)
    except Exception:
        pass

    return (0, 0)


def fetch_cover_bytes(url, timeout=15, log=None):
    """
    Download a cover image and return its raw bytes, or b'' on failure.
    Caps download at 8 MB to avoid runaway transfers.
    """
    if not url:
        return b''
    try:
        req = Request(url, headers={'User-Agent': UA})
        resp = urlopen(req, timeout=timeout)
        data = resp.read(8 * 1024 * 1024)
        return data if len(data) > 1000 else b''
    except Exception as e:
        if log:
            log.debug('fetch_cover_bytes failed for %s: %s', url[:80], e)
        return b''


def has_white_border_padding(data, border_px=20, white_threshold=240, min_ratio=0.80):
    """
    Return True when a cover image has substantial white/near-white padding
    on at least 2 of its 4 edges — a sign that this is a marketing/editorial
    image with added whitespace rather than a clean full-bleed book cover.

    Some Amazon and publisher image CDNs deliver the cover art centred on a
    white background (e.g. Amazon's editorial-image endpoint, some Penguin/
    Random House jacket files).  These images have higher raw pixel counts
    than the equivalent full-bleed version, which causes cover_quality() to
    incorrectly prefer them over the existing library cover even though they
    are visually inferior (the actual illustration occupies only ~80% of the
    canvas).

    Detection: sample a strip of `border_px` pixels from each of the 4 edges.
    If >= 2 edges have >= `min_ratio` of pixels brighter than `white_threshold`
    on all three RGB channels, the cover is flagged as padded.

    Requires numpy (bundled with Calibre).  Returns False safely on any error.
    """
    try:
        import io as _io
        from PIL import Image as _PIL  # type: ignore
        import numpy as _np
        img = _PIL.open(_io.BytesIO(data)).convert('RGB')
        w, h = img.size
        if w < 50 or h < 50:
            return False
        arr = _np.array(img)
        bw = max(border_px, min(w, h) // 25)

        def _white_ratio(strip):
            white = (_np.array(strip) > white_threshold).all(axis=2).sum()
            return white / (strip.shape[0] * strip.shape[1])

        sides = [
            _white_ratio(arr[:bw, :]),    # top
            _white_ratio(arr[-bw:, :]),   # bottom
            _white_ratio(arr[:, :bw]),    # left
            _white_ratio(arr[:, -bw:]),   # right
        ]
        padded_sides = sum(1 for r in sides if r >= min_ratio)
        return padded_sides >= 2
    except Exception:
        return False


# ── Google Books "no cover available" reference-hash detector (v6.2.28) ────
# ROOT CAUSE (field-confirmed, twice): Google Books' own volumeInfo.
# imageLinks sometimes lists a thumbnail URL for a volume that, when
# actually fetched, serves Google's generic "image not available" tile
# instead of real art — the API metadata is stale even though the image
# link itself resolves fine (HTTP 200, plausible byte size). This means
# checking "does imageLinks exist" (the v6.2.27 fix) is necessary but not
# sufficient, and the pixel-statistics heuristics in
# is_blank_or_placeholder_image() below don't reliably catch this specific
# graphic either (it has just enough anti-aliased text/icon detail to
# survive std-dev, unique-colour, AND bytes-per-pixel checks).
#
# Google's placeholder is a fixed, non-book-specific asset: requesting a
# books/content cover for ANY nonexistent/coverless volume ID returns the
# exact same image bytes. So instead of guessing at pixel statistics, we
# fetch that reference image ONCE per plugin process (a deliberately-bogus
# ID), hash it, and compare every books.google.com cover download against
# that hash before trusting it. This is self-updating if Google ever
# changes the placeholder graphic (each process re-fetches its own
# reference) and has no false-positive risk against real cover art.
_google_placeholder_hash = None
_google_placeholder_phash = None
_google_placeholder_lock = None


def _average_hash_bits(data, hash_size=16):
    """
    Compute a simple size-independent 'average hash' (aHash) of an image:
    downsample to a small hash_size x hash_size grayscale canvas, then set
    each bit based on whether that pixel is above/below the mean. Because
    the image is normalized to a fixed small canvas first, two renders of
    the SAME graphic at different original resolutions (e.g. Google Books'
    placeholder served at 128x200 vs 1280x1670) hash identically or very
    nearly so -- unlike a raw byte/SHA-256 hash, which differs for every
    distinct resolution even when the visual content is identical.

    Returns an int bitmask, or None if Pillow isn't available / decode fails.
    """
    try:
        import io as _io
        from PIL import Image as _PIL  # type: ignore
        img = _PIL.open(_io.BytesIO(data)).convert('L').resize(
            (hash_size, hash_size), _PIL.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / float(len(pixels))
        bits = 0
        for p in pixels:
            bits = (bits << 1) | (1 if p > avg else 0)
        return bits
    except Exception:
        return None


def _hamming_distance(a, b):
    return bin(a ^ b).count('1')


def _get_google_placeholder_hash(timeout=8, log=None):
    global _google_placeholder_hash, _google_placeholder_phash, _google_placeholder_lock
    import threading
    if _google_placeholder_lock is None:
        _google_placeholder_lock = threading.Lock()
    with _google_placeholder_lock:
        if _google_placeholder_hash is not None:
            return _google_placeholder_hash
        try:
            # A syntactically-valid-looking but essentially-guaranteed-to-
            # not-exist Google Books volume ID. Google always answers with
            # its generic placeholder rather than a 404 for this endpoint.
            bogus_url = ('https://books.google.com/books/content?id='
                         'zzzzzzzzzzzzzzzzzzzz9999&printsec=frontcover'
                         '&img=1&zoom=1&source=gbs_api')
            data = _http_get_bytes(bogus_url, timeout=timeout, log=log)
            if data and len(data) > 200:
                _google_placeholder_hash = hashlib.sha256(data).hexdigest()
                _google_placeholder_phash = _average_hash_bits(data)
                if log:
                    log.debug('Google placeholder reference hash captured '
                              '(%d bytes)', len(data))
            else:
                _google_placeholder_hash = ''
                _google_placeholder_phash = None
        except Exception:
            _google_placeholder_hash = ''
            _google_placeholder_phash = None
        return _google_placeholder_hash


def _get_google_placeholder_phash(timeout=8, log=None):
    # Ensures the reference (and its phash) have been captured, then
    # returns the phash. Piggy-backs on the same cached fetch as the exact
    # hash so this never triggers a second network call.
    _get_google_placeholder_hash(timeout=timeout, log=log)
    return _google_placeholder_phash


def is_google_placeholder_cover(data, url='', timeout=8, log=None):
    """
    True when `data` is confirmed to be Google Books' "image not available"
    placeholder graphic (see module comment above). Only meaningful for
    books.google.com cover URLs; harmless (always False) for anything else.

    Two checks are tried:
      1. Exact SHA-256 match against a reference fetch -- fast, zero false
         positives, but only fires when the candidate happens to be the
         same pixel dimensions as the reference.
      2. A size-independent perceptual hash (aHash) comparison -- catches
         the placeholder at ANY resolution, since Google renders the same
         graphic scaled to whatever size was requested (field-confirmed:
         a single book's cover candidates included the placeholder at
         1280x1670, 1200x1565, and 575x750 -- three different sizes, none
         of which matched a single fixed-size reference hash). A small
         Hamming-distance threshold allows for minor resampling/JPEG noise
         differences between resolutions while still requiring the images
         to be near-identical in overall layout/content.
    """
    if not data or not url or 'books.google.com' not in url.lower():
        return False
    try:
        ref = _get_google_placeholder_hash(timeout=timeout, log=log)
        if not ref:
            return False
        if hashlib.sha256(data).hexdigest() == ref:
            return True
        ref_phash = _get_google_placeholder_phash(timeout=timeout, log=log)
        cand_phash = _average_hash_bits(data)
        if ref_phash is not None and cand_phash is not None:
            # 256-bit hash (16x16); allow a small amount of drift from
            # resampling/compression differences across resolutions.
            if _hamming_distance(ref_phash, cand_phash) <= 10:
                return True
        return False
    except Exception:
        return False


def _edge_band_is_blank(gray_arr, from_edge, frac=0.32, flat_std_threshold=1.5,
                         contrast_ratio=6.0):
    """
    True when a contiguous band covering `frac` of the image, taken from one
    edge ('top', 'bottom', 'left', 'right'), is near-PERFECTLY flat AND the
    rest of the image is meaningfully more varied than that.

    Exists to catch a corruption pattern the whole-canvas checks in
    is_blank_or_placeholder_image() miss: a partially-decoded or otherwise
    broken cover fetch where (for example) the top ~65% renders real
    illustration/typography correctly but the bottom ~35% is a flat white/
    grey fill left over from the failed portion of the download. Whole-
    canvas standard deviation looks fine (the healthy 65% dominates), and
    has_white_border_padding() only samples a thin edge strip and requires
    >= 2 padded edges, so a single large blank band at ONE edge slips past
    both. Field-confirmed: a 128x185 Google Books cover candidate rendering
    only its upper ~65% with a blank lower band.

    IMPORTANT — false-positive guard: a genuinely minimalist cover design
    can legitimately have a large flat-coloured region (e.g. a plain
    background band behind the title). Flagging on absolute flatness alone
    would misfire on those. So this requires BOTH:
      1. The band itself is near-perfectly flat (std < flat_std_threshold,
         a much stricter bar than "just fairly plain" — genuine printed/
         photographed flat regions still carry some residual texture/
         JPEG noise; a bare undecoded/placeholder fill typically doesn't).
      2. The REST of the image is dramatically more varied than the band
         (contrast_ratio×) — i.e. there's a stark discontinuity between
         "real detail lives here" and "nothing lives here", rather than an
         image that is just uniformly calm/minimalist throughout.
    """
    h, w = gray_arr.shape
    if from_edge == 'top':
        n = max(1, int(h * frac)); band = gray_arr[:n, :]; rest = gray_arr[n:, :]
    elif from_edge == 'bottom':
        n = max(1, int(h * frac)); band = gray_arr[-n:, :]; rest = gray_arr[:-n, :]
    elif from_edge == 'left':
        n = max(1, int(w * frac)); band = gray_arr[:, :n]; rest = gray_arr[:, n:]
    else:
        n = max(1, int(w * frac)); band = gray_arr[:, -n:]; rest = gray_arr[:, :-n]
    band_std = float(band.std())
    if band_std >= flat_std_threshold:
        return False
    rest_std = float(rest.std())
    return rest_std > flat_std_threshold * contrast_ratio


def is_blank_or_placeholder_image(data, std_threshold=10.0, min_unique_colours=6,
                                   url='', log=None):
    """
    Return True when a cover image is effectively blank / a placeholder —
    a near-uniform flat colour (or two-tone) canvas rather than genuine
    cover artwork.

    WHY THIS EXISTS: has_white_border_padding() only inspects a thin strip
    along each of the 4 edges, so it correctly catches a real illustration
    centred on a white/near-white background. It does NOT catch:
      - A cover CDN response that is blank/placeholder across its ENTIRE
        canvas (e.g. a broken Google Books thumbnail, a generic "no cover
        available" tile, or a solid-colour stock image) — there's no
        illustrated centre for the border check to contrast against.
      - Placeholder colours other than white (light grey "unavailable"
        tiles, flat brand-colour filler images, etc.).
    These images can still have a large raw pixel canvas (satisfying
    cover_quality()'s pixel-count comparison) while conveying zero real
    information about what the book actually looks like — exactly the
    "truthfulness" problem: a bigger blank image is not a better cover.

    Detection: downsample to a small 32x32 thumbnail (fast, robust to
    JPEG noise) and check:
      1. Overall pixel value standard deviation — real cover art has
         strong contrast/detail even at 32x32; flat or near-flat images
         don't.
      2. Number of visually distinct colours (coarse-bucketed to 4 bits
         per channel) — a handful of buckets means large flat regions.
      3. Compression efficiency (bytes/pixel) — flat placeholder graphics
         compress far more efficiently than real photographed/illustrated
         art.
      4. A large, near-PERFECTLY-flat band at one edge (top/bottom/left/
         right), on a separate 64x64 grid — catches partially-decoded or
         otherwise broken fetches where most of the canvas is real
         content but a big contiguous chunk near one edge is a flat
         leftover fill (see _edge_band_is_blank()'s docstring). Deliberately
         requires near-zero variance (not just "fairly plain"), because
         testing showed a genuinely blank/undecoded fill reads as almost
         exactly 0.0 std, while even an intentionally flat-coloured real
         design consistently shows some texture/JPEG noise (~2+) — so this
         threshold is set to exploit that gap without flagging legitimate
         minimalist cover designs.
    Any signal alone flags the image as blank/placeholder.

    NOTE ON A KNOWN REMAINING GAP: a low-contrast "no cover available" CDN
    placeholder (flat background + a couple of soft rectangular text-bars +
    a small icon, all in muted greys) can sometimes have just enough tonal
    variety to survive every check above. An edge/gradient-density signal
    was tried for this and DROPPED after testing showed it doesn't reliably
    separate that case from genuinely minimalist real cover art (both
    landed in a similar, overlapping range) — shipping it would trade
    "misses a placeholder" for "flags real covers", which is worse. If a
    specific recurring placeholder source is identified (the way Google
    Books' one was, via is_google_placeholder_cover()), a reference-hash
    fingerprint is the more reliable fix; a general pixel heuristic isn't
    a safe way to solve it.

    Requires Pillow + numpy (bundled with Calibre). Returns False safely
    on any error, and treats undecodable/too-tiny images as blank too
    (they can't be a trustworthy cover either).
    """
    try:
        # v6.2.28: check the reliable, self-updating reference-hash signal
        # FIRST -- see is_google_placeholder_cover()'s docstring for why
        # this exists (Google's own imageLinks metadata can point at a
        # coverless volume's placeholder, which survives every pixel-
        # statistics check below). Only ever matches for books.google.com
        # URLs; a no-op (and no extra network call) for everything else.
        if url and is_google_placeholder_cover(data, url=url, log=log):
            return True

        import io as _io
        from PIL import Image as _PIL  # type: ignore
        import numpy as _np
        img = _PIL.open(_io.BytesIO(data)).convert('RGB')
        w, h = img.size
        if w < 30 or h < 30:
            return True
        thumb = img.resize((32, 32))
        arr = _np.array(thumb).astype(_np.float32)

        if arr.std() < std_threshold:
            return True

        buckets = (arr // 16).astype(_np.int32)          # 16 buckets/channel
        flat = buckets.reshape(-1, 3)
        unique = len({tuple(row) for row in flat.tolist()})
        if unique < min_unique_colours:
            return True

        # v6.2.27: THIRD signal — compression efficiency. Real photographed
        # / illustrated cover art has high pixel-level entropy and does not
        # compress anywhere near as efficiently as a simple flat-colour
        # "image not available" / icon+text placeholder tile — even when
        # that placeholder has just enough anti-aliased text to survive
        # both checks above (field-confirmed: this is exactly what let
        # Google Books' own coverless-volume placeholder through). A real
        # cover JPEG/PNG at typical book-cover resolutions essentially
        # never compresses below ~0.03 bytes/pixel; simple flat-graphic
        # placeholders routinely compress to well under that.
        bytes_per_pixel = len(data) / float(w * h)
        if bytes_per_pixel < 0.03:
            return True

        # v6.2.35: FOURTH signal — a large blank band at one edge, on a
        # slightly higher-resolution 64x64 grayscale grid (fine enough to
        # resolve a ~30% band reliably; the 32x32 thumb above is enough
        # for whole-canvas stats but too coarse for this). Whole-canvas
        # std/colour-count/compression checks above can all look healthy
        # when only part of the canvas is broken — see
        # _edge_band_is_blank()'s docstring for the field-confirmed case
        # this catches (a truncated Google Books cover fetch).
        gray64 = _np.array(img.convert('L').resize((64, 64))).astype(_np.float32)
        for edge in ('top', 'bottom', 'left', 'right'):
            if _edge_band_is_blank(gray64, edge):
                return True

        return False
    except Exception:
        return False


def cover_quality(data):
    """
    Return a quality tuple (pixels, file_bytes) for a raw cover image.
    pixels = width × height (0 if unreadable).
    Higher is better; compare as plain tuples (pixels first, then size).

    Note: this function does NOT penalise white-border padding — the caller
    (_fetch_best_cover in dialogs.py) uses has_white_border_padding() to
    filter padded candidates before comparing quality tuples.
    """
    if not data:
        return (0, 0)
    w, h = measure_image_bytes(data)
    return (w * h, len(data))


def content_cover_quality(data):
    """
    Like cover_quality(), but padding-aware.

    ROOT CAUSE OF THE "good cover replaced by a padded thumbnail" BUG:
    cover_quality() intentionally does NOT penalise white-border padding
    (see its docstring) — that filtering was only ever applied *between*
    fetched candidates, inside dialogs.py's _fetch_best_cover(). But when
    every fetched candidate for a book turns out to be padded (e.g. only a
    letterboxed Google Books/Amazon editorial thumbnail is available),
    _fetch_best_cover() falls back to returning that padded image anyway
    (a padded cover beats no cover). The *final* decision of whether to
    overwrite the book's existing cover then compared raw cover_quality()
    tuples — and a padded canvas's blank margins inflate its width*height
    enough to numerically outscore a smaller but full-bleed, higher-quality
    existing cover, even though the padded image is visually worse.

    Fix: when has_white_border_padding() flags an image, measure the
    pixel count of just the non-white content region (crop out the
    margins) instead of the full padded canvas. A clean full-bleed cover
    is unaffected (its content region ~= its full canvas), while a
    padded image's inflated whitespace no longer counts in its favour.
    """
    if not data:
        return (0, 0)
    w, h = measure_image_bytes(data)
    if w <= 0 or h <= 0:
        return (0, 0)
    pixels = w * h
    try:
        if has_white_border_padding(data):
            import io as _io
            from PIL import Image as _PIL  # type: ignore
            import numpy as _np
            img = _PIL.open(_io.BytesIO(data)).convert('RGB')
            arr = _np.array(img)
            non_white = ~(arr > 240).all(axis=2)  # True where pixel is NOT near-white
            rows = _np.where(non_white.any(axis=1))[0]
            cols = _np.where(non_white.any(axis=0))[0]
            if len(rows) and len(cols):
                content_h = int(rows[-1] - rows[0] + 1)
                content_w = int(cols[-1] - cols[0] + 1)
                content_pixels = content_w * content_h
                if 0 < content_pixels < pixels:
                    pixels = content_pixels
    except Exception:
        pass
    return (pixels, len(data))


def best_cover(cover_candidates, min_size=200):
    """
    Return the highest-scoring non-audiobook cover URL (heuristic, no download).
    cover_candidates: iterable of (url, weight) or (url, weight, source) tuples
    — only the first two positions are used here.
    """
    best_url, best_score = None, -1
    for cand in cover_candidates:
        url, weight = cand[0], cand[1]
        s = score_cover(url)
        if s < 0:          # audiobook — skip entirely
            continue
        s += weight * 2
        if s > best_score:
            best_score, best_url = s, url
    return best_url


def probe_best_cover(cover_candidates, timeout=8, log=None):
    """
    Score all candidates, then actually DOWNLOAD and content-validate the
    top few (excluding audiobook URLs) in score order, returning the first
    one that is a real, non-blank, reasonably-sized image. Falls back to
    the heuristic winner only if every probed candidate fails validation.

    cover_candidates: iterable of (url, weight) or (url, weight, source)
    tuples — only the first two positions are used here.

    v6.2.28 ROOT-CAUSE FIX: this used to be a cheap HEAD-only Content-
    Length probe with NO image-content awareness at all — it just picked
    whichever candidate reported the largest byte size over HEAD/ranged-
    GET. That is exactly how a Google Books "image not available"
    placeholder (a real, non-tiny, valid JPEG — see
    is_google_placeholder_cover()'s docstring) kept winning "Best probed
    cover" even after upstream fixes stopped fabricating speculative
    Google cover URLs: Google's own imageLinks metadata can point at a
    placeholder for a genuinely coverless volume, and a HEAD probe cannot
    tell that apart from a real cover of similar file size. Now each
    candidate is fully downloaded (not just HEAD'd) and run through
    is_blank_or_placeholder_image() before being trusted — the same
    validation the Cover Chooser dialog already applies — so the
    automatic "best" pick and the manual picker can no longer disagree
    about which candidates are real.
    """
    if not cover_candidates:
        return None

    # Filter audiobook URLs before scoring
    clean = [(cand[0], cand[1]) for cand in cover_candidates
             if cand[0] and score_cover(cand[0]) >= 0]
    if not clean:
        return None

    scored = sorted(
        [(score_cover(url) + w * 2, url) for url, w in clean],
        reverse=True
    )
    if not scored:
        return None

    import threading
    top = [u for _, u in scored[:8]]
    results = {}
    lock = threading.Lock()

    def fetch_and_validate(u):
        data = _http_get_bytes(u, timeout=timeout, log=log)
        ok = False
        if data and len(data) > 2000:
            try:
                ok = not is_blank_or_placeholder_image(data, url=u, log=log)
            except Exception:
                ok = True  # validation itself failed — don't punish the candidate
        with lock:
            results[u] = (len(data) if data else 0, ok)

    threads = [threading.Thread(target=fetch_and_validate, args=(u,), daemon=True)
               for u in top]
    for t in threads: t.start()
    for t in threads: t.join(timeout=timeout + 2)

    # Prefer the highest-scoring candidate (top-first order preserved) that
    # both downloaded successfully AND passed content validation.
    for u in top:
        size, ok = results.get(u, (0, False))
        if size > 2000 and ok:
            return u

    # Nothing validated cleanly — fall back to the largest-downloaded one
    # that at least isn't a zero-byte failure, rather than a confirmed
    # placeholder, so a real-but-unvalidatable image still beats nothing.
    downloaded = [(results[u][0], u) for u in top if results.get(u, (0, False))[0] > 2000]
    if downloaded:
        if log:
            log.warning('probe_best_cover: no candidate passed content '
                        'validation — falling back to largest downloaded '
                        '(%d candidates tried)', len(top))
        return max(downloaded, key=lambda x: x[0])[1]

    return scored[0][1]


# ── ISBN auto-discovery ────────────────────────────────────────────────────────

def fetch_isbn_by_title(title, author, timeout=20, log=None):
    """Find an ISBN from title+author using Google Books and Open Library."""
    candidates = []

    for q_parts in [
        ([('intitle:' + quote_plus(title)) if title else '',
          ('inauthor:' + quote_plus(author)) if author else '']),
        ([quote_plus('{} {}'.format(title or '', author or '').strip())]),
    ]:
        q = '+'.join(p for p in q_parts if p)
        if not q:
            continue
        data = _jget('https://www.googleapis.com/books/v1/volumes'
                     '?q={}&maxResults=5'.format(q), timeout=timeout, log=log)
        if data:
            for item in data.get('items', [])[:5]:
                for iid in item.get('volumeInfo', {}).get('industryIdentifiers', []):
                    if iid.get('type') in ('ISBN_13', 'ISBN_10'):
                        candidates.append(iid['identifier'])
        if candidates:
            break

    if title:
        q2 = quote_plus('{} {}'.format(title, author or '').strip())
        data2 = _jget('https://openlibrary.org/search.json?q={}&limit=5'.format(q2),
                      timeout=timeout, log=log)
        if data2:
            for doc in data2.get('docs', [])[:5]:
                for isbn in doc.get('isbn', []):
                    if len(isbn) in (10, 13):
                        candidates.append(isbn)

    for c in candidates:
        if len(c) == 13 and c.startswith('978'):
            return c
    for c in candidates:
        if len(c) == 13:
            return c
    for c in candidates:
        if len(c) == 10:
            return c
    return ''


# ── Google Books ───────────────────────────────────────────────────────────────

def fetch_google(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Search Google Books. Per-book cooldown (not session-wide) so a 429 on
    one book does not poison subsequent books in the same run.
    Tries: isbn lookup → intitle/inauthor → plain query → ASIN keyword.
    Picks the candidate with the best title/author match + richest synopsis.
    Does not hard-restrict by language (a langRestrict query param caused
    zero-result regressions on some books whose language Google mis-tags),
    but candidates whose reported language matches the book's language get
    a large scoring bonus (v6.2.26) so a same-language edition is preferred
    over a richer-looking wrong-language one when Google returns several
    editions for the same query.

    v6.2.12: if the user has set an API key (Options tab → Google Books API
    Key), it's appended to every request. The anonymous/keyless quota is
    shared across *all* unauthenticated callers from the same IP and is easy
    to exhaust within a single short library-scanning session — field logs
    showed 429 on literally the first Google call of a brand-new run, which
    only an IP-wide quota (not a per-session one) explains. A free API key
    from Google Cloud Console gets a dramatically higher per-day quota and
    is the only real fix for that; there is no in-code workaround for a
    quota that's already exhausted before the request is made.
    """
    api_key = ''
    try:
        from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
        api_key = (prefs.get('google_api_key', '') or '').strip()
    except Exception:
        pass

    if api_key and (api_key.startswith('AQ.') or not api_key.startswith('AIza')):
        if log:
            log.warning(
                'Google Books: configured google_api_key appears to be a Google Gemini / AI Studio key '
                'or invalid key, not a Google Books Cloud Console API key (expected AIza...). '
                'Using keyless request instead.'
            )
        api_key = ''

    queries = []
    if isbn:
        queries.append('isbn:{}'.format(isbn))
    if title or author:
        parts = []
        if title:  parts.append('intitle:' + quote_plus(title))
        if author: parts.append('inauthor:' + quote_plus(author))
        queries.append('+'.join(parts))
        plain = quote_plus('{} {}'.format(title or '', author or '').strip())
        if plain:
            queries.append(plain)
    if asin and not isbn:
        queries.append(quote_plus(asin))

    _target_lang = (lang or '').lower()[:2]

    for q in queries:
        if not q:
            continue
        url = ('https://www.googleapis.com/books/v1/volumes'
               '?q={}&maxResults=10&printType=books'.format(q))
        if api_key:
            url += '&key={}'.format(quote_plus(api_key))
        data = _jget(url, timeout, retries, log)
        if (not data or not data.get('items')) and api_key:
            url_nokey = 'https://www.googleapis.com/books/v1/volumes?q={}&maxResults=10&printType=books'.format(q)
            data = _jget(url_nokey, timeout, retries, log)
        if not data or not data.get('items'):
            continue

        candidates = [item for item in data['items']
                      if item.get('volumeInfo', {}).get('title')]
        if not candidates:
            continue

        def _candidate_score(item):
            info = item.get('volumeInfo', {})
            desc = info.get('description', '') or ''
            score = 0
            if title:
                score += similarity(title, info.get('title', '')) * 2
            if author and info.get('authors'):
                score += similarity(author, ', '.join(info['authors']))
            score += min(len(desc), 2000) / 4.0
            if info.get('imageLinks'):
                score += 10
            if _target_lang:
                cand_lang = (info.get('language', '') or '').lower()[:2]
                if cand_lang == _target_lang:
                    score += 600
                elif cand_lang:
                    score -= 400
            return score

        # FOURTH bug (this fix): _candidate_score always returned
        # max(candidates, key=_candidate_score) even when EVERY candidate
        # was a poor title match -- there was no minimum-similarity floor,
        # so "best of a bad batch" could still be a completely unrelated
        # book if it happened to have a longer description or a cover image
        # (each worth real score points regardless of title match).
        # Field-confirmed: searching "Todo lo que el agua calla" (Payá,
        # Eugenio) returned 'El alcalde rojas' as Google's top pick -- an
        # unrelated book that simply scored better than the other 9 loose
        # intitle: matches. _merge_results' fuzzy title filter in
        # fetch_engine.py did correctly discard this result downstream, so
        # it never reached the user, but it wasted a request, polluted the
        # log, and is fragile (a future relaxation of that downstream
        # filter would let mismatches like this leak through).
        #
        # Fix: require a minimum title-similarity score before a candidate
        # is even eligible, independent of description length or cover
        # presence. Crucially, the comparison strips subtitle/edition noise
        # first (matching exactly what fetch_engine._merge_results does
        # downstream) -- a raw, un-stripped comparison badly underscores
        # correct matches whose Google subtitle differs from the library's
        # short title (e.g. "Todo lo que el agua calla" vs Google's "Todo lo
        # que el agua calla: Un thriller sobre lo que un pueblo eligió no
        # saber" scores only 40/100 raw, but 100/100 once the part after the
        # colon is stripped from both sides) -- an un-stripped floor would
        # have rejected that CORRECT match right alongside the wrong one.
        if title:
            def _strip_subtitle(t):
                if not t:
                    return t
                t = re.sub(
                    r'\s*[\(\[][^()\[\]]{0,40}(edition|edici[oó]n|ebook|kindle)[^()\[\]]{0,10}[\)\]]',
                    '', t, flags=re.I)
                return re.split(r'\s*[:/\u2013\u2014]\s*', t, maxsplit=1)[0].strip()

            MIN_TITLE_SIMILARITY = 40  # 0-100 scale; matches fetch_engine's
                                       # downstream merge floor so this early
                                       # check and the later one agree.
            stripped_title = _strip_subtitle(title)

            def _clears_floor(item):
                cand_title = item.get('volumeInfo', {}).get('title', '')
                raw_sim     = similarity(title, cand_title)
                stripped_sim = similarity(stripped_title, _strip_subtitle(cand_title))
                return max(raw_sim, stripped_sim) >= MIN_TITLE_SIMILARITY

            candidates = [c for c in candidates if _clears_floor(c)]
            if not candidates:
                if log:
                    log.debug('Google Books: all candidates for query %r failed the '
                             'minimum title-similarity floor (%d) -- trying next query',
                             q[:60], MIN_TITLE_SIMILARITY)
                continue

        best = max(candidates, key=_candidate_score)
        info = best.get('volumeInfo', {})

        volume_id = best.get('id', '')
        idents = {}
        for iid in info.get('industryIdentifiers', []):
            if iid.get('type') == 'ISBN_13':
                idents['isbn'] = iid['identifier']
            elif iid.get('type') == 'ISBN_10' and 'isbn' not in idents:
                idents['isbn'] = iid['identifier']
        if asin:
            idents['amazon'] = asin

        thumb = info.get('imageLinks', {})
        raw   = (thumb.get('extraLarge') or thumb.get('large') or
                 thumb.get('medium') or thumb.get('thumbnail') or '')
        cover_alts = []
        # v6.2.27 ROOT-CAUSE FIX for "image not available" covers reaching
        # the final choice/auto-select: this used to build 3 speculative
        # id-based frontcover URLs for EVERY candidate that had a volume_id,
        # regardless of whether Google's own volumeInfo.imageLinks said a
        # cover actually exists. Those URLs don't 404 for a coverless
        # volume -- they return Google's real, valid, non-tiny "image not
        # available" placeholder JPEG, which passed every size/HEAD-probe
        # check downstream and got auto-picked as "best" cover (field-
        # confirmed: books.google.com/books/content?id=t5Ke0QEACAAJ...).
        # They were also listed BEFORE the confirmed-real `raw` thumbnail
        # URL, so even when a real cover DID exist, the speculative guess
        # could still be tried/shown first.
        #
        # Fix: only ever build a books.google.com/content URL when
        # imageLinks confirms Google has *some* thumbnail for this volume
        # (raw is non-empty) -- and even then, the confirmed real `raw` URL
        # (and its higher-res zoom variants) come first, with the id-based
        # guess added only as one extra last-resort alternative. If
        # imageLinks is empty, no Google cover is offered for this
        # candidate at all: no cover is strictly better than a guaranteed
        # placeholder that can outrank a real Amazon/Goodreads cover.
        if raw:
            clean = re.sub(r'[&?]zoom=\d', '', raw)
            clean = re.sub(r'[&?]edge=\w+', '', clean).rstrip('&?')
            cover_alts.append(clean + ('&' if '?' in clean else '?') + 'zoom=6&fife=w1200')
            cover_alts.append(clean + ('&' if '?' in clean else '?') + 'zoom=3')
            cover_alts.append(raw)
            if volume_id:
                cover_alts.append(
                    'https://books.google.com/books/content?id={}'
                    '&printsec=frontcover&img=1&zoom=6&source=gbs_api'.format(volume_id))

        cover_url = cover_alts[0] if cover_alts else ''
        comments = info.get('description', '') or info.get('subtitle', '')

        return {
            'title':       info.get('title', ''),
            'authors':     info.get('authors', []),
            'publisher':   info.get('publisher', ''),
            'pubdate':     info.get('publishedDate', ''),
            'comments':    comments,
            'tags':        info.get('categories', []),
            'rating':      int(round(info.get('averageRating', 0))),
            'language':    info.get('language', ''),
            'identifiers': idents,
            'cover_url':   cover_url,
            'cover_alts':  [u for u in cover_alts[1:] if u],
            'source':      'Google Books',
        }

    return None


# ── Open Library ───────────────────────────────────────────────────────────────

def fetch_openlibrary(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Tries: ISBN → ASIN bibkey → title/author search (plain + structured).
    Work-level description fetched for title/author path.
    """
    if isbn:
        url  = ('https://openlibrary.org/api/books'
                '?bibkeys=ISBN:{}&format=json&jscmd=data'.format(isbn))
        data = _jget(url, timeout, retries, log)
        if data:
            key = 'ISBN:{}'.format(isbn)
            info = data.get(key)
            if info:
                result = _parse_ol_book(info, isbn)
                if asin:
                    result.setdefault('identifiers', {})['amazon'] = asin
                return result

    if asin:
        url  = ('https://openlibrary.org/api/books'
                '?bibkeys=ASIN:{}&format=json&jscmd=data'.format(asin))
        data = _jget(url, timeout, retries, log)
        if data:
            key  = 'ASIN:{}'.format(asin)
            info = data.get(key)
            if info:
                result = _parse_ol_book(info, isbn)
                result.setdefault('identifiers', {})['amazon'] = asin
                return result

    search_urls = []
    if title or author:
        plain = quote_plus('{} {}'.format(title or '', author or '').strip())
        search_urls.append(
            'https://openlibrary.org/search.json?q={}&limit=5'.format(plain))
        structured_parts = []
        if title:  structured_parts.append('title=' + quote_plus(title))
        if author: structured_parts.append('author=' + quote_plus(author))
        if structured_parts:
            search_urls.append(
                'https://openlibrary.org/search.json?{}&limit=5'.format(
                    '&'.join(structured_parts)))

    for surl in search_urls:
        data = _jget(surl, timeout, retries, log)
        if not data:
            continue
        for doc in data.get('docs', []):
            if not doc.get('title'):
                continue
            cover_id  = doc.get('cover_i')
            olid_list = doc.get('edition_key', [])
            isbns     = doc.get('isbn', [])
            best_isbn = next((i for i in isbns if len(i) == 13), '')
            if not best_isbn:
                best_isbn = next((i for i in isbns if len(i) == 10), '')

            covers = []
            if cover_id:
                covers.append('https://covers.openlibrary.org/b/id/{}-L.jpg'.format(cover_id))
                covers.append('https://covers.openlibrary.org/b/id/{}-M.jpg'.format(cover_id))
            if best_isbn:
                covers.append('https://covers.openlibrary.org/b/isbn/{}-L.jpg'.format(best_isbn))
            if olid_list:
                covers.append('https://covers.openlibrary.org/b/olid/{}-L.jpg'.format(
                    olid_list[0]))

            idents = {'isbn': best_isbn} if best_isbn else {}
            if asin:
                idents['amazon'] = asin

            comments = _fetch_ol_work_description(
                doc.get('key', ''), timeout, log)
            if not comments:
                fs = doc.get('first_sentence')
                if isinstance(fs, list) and fs:
                    comments = fs[0]
                elif isinstance(fs, str):
                    comments = fs

            _target_lang = (lang or '').lower()[:2]
            ol_langs = doc.get('language', [])
            if _target_lang:
                ol_lang = next((l for l in ol_langs if normalize_language(l) == _target_lang), '') or (ol_langs[0] if ol_langs else '')
            else:
                ol_lang = next((l for l in ol_langs if normalize_language(l) == 'en'), '') or (ol_langs[0] if ol_langs else '')

            return {
                'title':       doc.get('title', ''),
                'authors':     doc.get('author_name', []),
                'publisher':   ', '.join(doc.get('publisher', [])[:1]),
                'pubdate':     str(doc.get('first_publish_year', '')),
                'comments':    comments,
                'tags':        doc.get('subject', [])[:15],
                'language':    ol_lang,
                'identifiers': idents,
                'cover_url':   covers[0] if covers else '',
                'cover_alts':  covers[1:],
                'source':      'Open Library',
            }

    return None


def _fetch_ol_work_description(work_key, timeout=20, log=None):
    if not work_key:
        return ''
    if not work_key.startswith('/'):
        work_key = '/' + work_key
    url  = 'https://openlibrary.org{}.json'.format(work_key)
    data = _jget(url, timeout, 1, log=log)
    if not data:
        return ''
    desc = data.get('description', '')
    if isinstance(desc, dict):
        desc = desc.get('value', '')
    return desc.strip() if isinstance(desc, str) else ''


def _parse_ol_book(info, isbn):
    covers   = info.get('cover', {})
    raw_cov  = covers.get('large', covers.get('medium', covers.get('small', '')))
    cover_url = _upgrade_openlibrary_cover(raw_cov)

    cover_alts = []
    if isbn:
        cover_alts.append('https://covers.openlibrary.org/b/isbn/{}-L.jpg'.format(isbn))
    desc = info.get('description', '')
    if isinstance(desc, dict):
        desc = desc.get('value', '')
    if not desc:
        excs = info.get('excerpts', [])
        if excs and isinstance(excs[0], dict):
            t = excs[0].get('text', '')
            desc = t.get('value', '') if isinstance(t, dict) else str(t)

    return {
        'title':       info.get('title', ''),
        'authors':     [a['name'] for a in info.get('authors', [])],
        'publisher':   ', '.join(p['name'] for p in info.get('publishers', [])),
        'pubdate':     info.get('publish_date', ''),
        'comments':    desc,
        'tags':        [s['name'] for s in info.get('subjects', [])][:15],
        'identifiers': {'isbn': isbn} if isbn else {},
        'cover_url':   cover_url,
        'cover_alts':  cover_alts,
        'source':      'Open Library',
    }


# ── Goodreads ──────────────────────────────────────────────────────────────────
# KNOWN BUG (fixed here): when a Goodreads book page has no synopsis text in
# its embedded JSON payload (common for freshly-synced self-published titles
# that only got a title+cover import, not a description), the code fell back
# to the page's <meta name="description"> tag. But when THAT is also empty,
# Goodreads serves its generic site-wide tagline instead of nothing:
# "Discover and share books you love on Goodreads." — 49 chars, long enough
# to pass the `len >= 20` sanity check, so it was accepted as if it were a
# real book-specific synopsis. Explicitly reject this known boilerplate string
# (and close variants) so a book with no real Goodreads synopsis correctly
# contributes no 'comments' field at all, instead of polluting the merge /
# "Choose Description" picker with Goodreads' marketing copy.
_GOODREADS_BOILERPLATE_DESCRIPTIONS = {
    'discover and share books you love on goodreads.',
    'discover and share books you love on goodreads',
}


def _is_goodreads_boilerplate(text):
    return text.strip().lower() in _GOODREADS_BOILERPLATE_DESCRIPTIONS

# Goodreads retired its public Developer API in Dec 2020, so this scrapes the
# public-facing site: a search page resolves title/author/isbn to a
# /book/show/<id> URL, then the book page itself supplies title, author,
# rating, genres, cover and — most importantly — a full, untruncated
# synopsis. Goodreads descriptions are typically longer and cleaner than the
# og:description meta tag (which Goodreads truncates with a trailing
# "...more" link), so we pull the full text out of the page's embedded JSON
# payload first and only fall back to Open Graph tags if that's missing.
# Registered as a high-weight global source (see fetch_engine.SOURCE_REGISTRY)
# so its synopsis tends to win the best-synopsis scoring in _merge_results.

_GOODREADS_TRAILING_UI_RE = re.compile(r'(?:\s*\.\.\.\s*)?\(less\)\s*$|\s*\.\.\.\s*more\s*$', re.I)


def _clean_goodreads_description(text):
    """
    Clean a raw description string pulled out of Goodreads' embedded page
    JSON via regex (i.e. still containing JSON string escapes).

    BUG FIXED: the previous version only un-escaped \\n, \\r\\n, \\" and \\'
    literally via .replace(), but Goodreads' JSON frequently uses \\uXXXX
    escapes for curly quotes and other punctuation (\\u2019 for ’, \\u201c /
    \\u201d for “ ”, \\u2013 / \\u2014 for – —, etc.) — these were left as
    literal backslash-u sequences in the saved synopsis instead of being
    decoded to the actual character, producing garbled text like
    "All\\u2019inizio" instead of "All'inizio".

    Fix: decode the whole string as a JSON string value first (handles ALL
    JSON escapes correctly and safely, including \\uXXXX, \\n, \\", etc. in
    one pass) before doing any further cleanup. Falls back to the old
    manual-replace approach only if JSON decoding fails (malformed capture).
    """
    if not text:
        return text

    decoded = None
    try:
        # Wrap in quotes and run through the JSON decoder — this is the
        # correct, complete way to resolve every escape sequence JSON
        # allows (\n, \r, \t, \", \\, \/, \uXXXX) in a single safe pass,
        # rather than hand-rolling a partial set of .replace() calls.
        decoded = json.loads('"' + text + '"')
    except Exception:
        decoded = None

    if decoded is not None:
        text = decoded
    else:
        # Fallback: best-effort manual unescaping if the capture wasn't
        # valid JSON (e.g. an unbalanced backslash from a regex edge case).
        text = text.replace('\\r\\n', '\n').replace('\\n', '\n')
        text = text.replace('\\"', '"').replace("\\'", "'")
        # Manually resolve the most common \uXXXX escapes JSON decoding
        # would otherwise have handled.
        def _unescape_u(m):
            try:
                return chr(int(m.group(1), 16))
            except Exception:
                return m.group(0)
        text = re.sub(r'\\u([0-9a-fA-F]{4})', _unescape_u, text)

    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    text = _GOODREADS_TRAILING_UI_RE.sub('', text)
    return text.strip()


_GOODREADS_BOOK_LINK_RES = (
    re.compile(r'href="(/book/show/\d+[^"]*)"'),
    re.compile(r"href='(/book/show/\d+[^']*)'"),
    # Some result rows render an absolute URL instead of a relative path.
    re.compile(r'href="(https://www\.goodreads\.com/book/show/\d+[^"]*)"'),
)

def _goodreads_find_book_url(raw):
    """Pull the first /book/show/<id> link out of a Goodreads search results page."""
    for pat in _GOODREADS_BOOK_LINK_RES:
        m = pat.search(raw)
        if m:
            href = m.group(1)
            return href if href.startswith('http') else 'https://www.goodreads.com' + href
    return ''


def _goodreads_search_fetch(search_url, timeout, retries, hdrs, log):
    """
    Browser-first fetch for a Goodreads SEARCH page.

    BUG FIXED: the previous version assumed "search pages are not
    bot-blocked" and used plain urllib only. That assumption is wrong —
    Goodreads (like Amazon) can serve a bot-challenge/empty-shell page to a
    non-browser request, which contains zero /book/show/ links. The code
    then logged this as "title search page loaded but no /book/show/ link
    found ... likely no match on Goodreads for this title", which is
    indistinguishable from a genuine empty search result, even though the
    real cause was urllib being blocked, not the book being absent from
    Goodreads. Field-confirmed: "Todo lo que el agua calla" by Payá,
    Eugenio is a real, listed Goodreads book, yet a plain urllib search
    request returned a page with no extractable result link.

    Fix: if the urllib search response doesn't yield a /book/show/ link,
    retry the SAME search URL through the Playwright browser (when
    available) before concluding there's genuinely no match. This mirrors
    the browser-first treatment _goodreads_fetch() already gives to the
    book PAGE itself, just applied one step earlier to the search step.
    """
    raw = _get(search_url, timeout, retries, headers=hdrs, log=log)
    if raw:
        url = _goodreads_find_book_url(raw)
        if url:
            return url
    # urllib found nothing usable -- try the browser before giving up,
    # since an empty/blocked search page looks identical to "no match".
    if _is_browser_available():
        if log:
            log.info('Goodreads: search via urllib found no result link -- '
                     'retrying via browser: %s', search_url[:80])
        braw = _browser_get(search_url, headers=hdrs, timeout=timeout, log=log)
        if braw:
            url = _goodreads_find_book_url(braw)
            if url:
                return url
            if log:
                log.debug('Goodreads: browser search page also had no '
                         '/book/show/ link -- likely a genuine no-match')
    return ''


def fetch_goodreads(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Goodreads (goodreads.com) — best-effort HTML scrape (no public API since
    Dec 2020). Tries an ISBN search first (most precise), then falls back to
    a title+author search.

    v6.2.12: search misses are now logged at INFO (not DEBUG) — field logs
    showed "goodreads=empty" with zero supporting detail, identical to a
    crash, so there was no way to tell "no matching book on Goodreads"
    (very plausible for obscure self-published titles, which often simply
    aren't catalogued there) apart from "the scraper's HTML parsing broke".

    v6.2.17: search requests are now browser-first-on-miss via
    _goodreads_search_fetch() (see its docstring) — a plain urllib search
    request can be served a bot-challenge page indistinguishable from a
    genuine "no results" page, so every miss now gets one retry through
    Playwright before being logged as a real no-match.
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    book_url = ''
    if isbn:
        search_url = 'https://www.goodreads.com/search?q={}'.format(quote_plus(isbn))
        book_url = _goodreads_search_fetch(search_url, timeout, retries, hdrs, log)
        if not book_url and log:
            log.info('Goodreads: ISBN search found no /book/show/ link for %s '
                     '(no match, or page layout changed)', isbn)

    if not book_url and (title or author):
        q = '{} {}'.format(title or '', author or '').strip()
        search_url = 'https://www.goodreads.com/search?q={}'.format(quote_plus(q))
        book_url = _goodreads_search_fetch(search_url, timeout, retries, hdrs, log)
        if not book_url and log:
            log.info('Goodreads: title search found no /book/show/ link '
                     'for %r (likely no match on Goodreads for this title)', q[:60])

    if not book_url:
        return None

    if log:
        log.debug('Goodreads: resolved book page %s', book_url[:90])
    page = _goodreads_fetch(book_url, timeout, retries, hdrs, log)
    if not page:
        if log:
            log.info('Goodreads: book page %s failed to load', book_url[:90])
        return None

    result = {}

    og = _parse_og_generic(page)
    if og.get('title'):
        result['title'] = re.sub(r'\s*\|\s*Goodreads.*$', '', og['title']).strip()
    if og.get('cover_url'):
        result['cover_url'] = og['cover_url']
    if og.get('authors'):
        result['authors'] = og['authors']

    if not result.get('authors'):
        am = re.search(
            r'<a[^>]+class="[^"]*authorName[^"]*"[^>]*>\s*<span[^>]*>([^<]+)</span>',
            page, re.I)
        if am:
            result['authors'] = [am.group(1).strip()]

    # Prefer the full, untruncated description embedded in the page's JSON
    # payload over the (often truncated) og:description.
    best_desc = ''
    for m in re.finditer(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"', page):
        cand = _clean_goodreads_description(m.group(1))
        if len(cand) > len(best_desc):
            best_desc = cand
    if not best_desc and og.get('comments'):
        candidate = _clean_goodreads_description(og['comments'])
        if not _is_goodreads_boilerplate(candidate):
            best_desc = candidate
    if best_desc and len(best_desc) >= 20 and not _is_goodreads_boilerplate(best_desc):
        result['comments'] = best_desc

    rm = re.search(r'"averageRating"\s*:\s*"?([\d.]+)"?', page)
    if rm:
        try:
            result['rating'] = float(rm.group(1))
        except ValueError:
            pass

    genres = re.findall(r'"genreName"\s*:\s*"([^"]+)"', page)
    if genres:
        seen = []
        for g in genres:
            if g not in seen:
                seen.append(g)
        result['tags'] = seen[:10]

    if not result.get('title'):
        if log:
            log.debug('Goodreads: book page %s yielded no parseable title — discarding', book_url[:80])
        return None

    result['source'] = 'Goodreads'
    if lang:
        result['language'] = lang
    _inject_idents(result, isbn, asin)
    return result


# ── WorldCat ───────────────────────────────────────────────────────────────────

def fetch_worldcat(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    KNOWN LIMITATION: xisbn.worldcat.org was shut down in 2016 — dead endpoint.
    This now returns immediately without making a network call, regardless
    of how the 'WorldCat' toggle is set — field logs showed that a stale
    leftover True value from an older on-disk config (the use_worldcat key
    was missing from the v6.2.9 migration's blocked-sources list — now
    fixed in config.py) was still causing a doomed connection attempt on
    every run, surfacing as a raw socket error
    ("[WinError 10054] ... interrotta ... dall'host remoto") instead of a
    clean HTTP error, because the host no longer answers at all.
    Disable 'WorldCat' in Sources to hide it from the active-sources list.
    """
    if log:
        log.debug('WorldCat: xisbn.worldcat.org has been dead since 2016 — skipping without a network call')
    return None
    # Unreachable — kept only for reference in case the endpoint is ever
    # resurrected at a different URL.
    if not isbn:
        return None
    url  = ('http://xisbn.worldcat.org/webservices/xid/isbn/{}?method=getMetadata&format=json&fl=*'.format(isbn))
    data = _jget(url, timeout, 0, log)
    if not data:
        return None
    lst = data.get('list', [])
    if not lst:
        return None
    item    = lst[0]
    authors = item.get('author', '')
    oclcnum = (item.get('oclcnum') or [''])[0]
    covers  = []
    if oclcnum:
        covers.append('https://covers.openlibrary.org/b/oclc/{}-L.jpg'.format(oclcnum))
    if isbn:
        covers.append('https://covers.openlibrary.org/b/isbn/{}-L.jpg'.format(isbn))
    idents = {'isbn': isbn, 'oclc': oclcnum}
    if asin:
        idents['amazon'] = asin
    return {
        'title':       item.get('title', ''),
        'authors':     [a.strip() for a in re.split(r'[;,]', authors)] if authors else [],
        'publisher':   item.get('publisher', ''),
        'pubdate':     item.get('year', ''),
        'language':    item.get('lang', ''),
        'identifiers': idents,
        'cover_url':   covers[0] if covers else '',
        'cover_alts':  covers[1:],
        'source':      'WorldCat',
    }


# ── Library of Congress ────────────────────────────────────────────────────────

def fetch_loc(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    if _loc_is_blocked():
        if log:
            log.debug('LOC: skipping (session blocked after earlier 403)')
        return None

    hdrs = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.loc.gov/books/',
    }
    if isbn:
        q = 'isbn:{}'.format(isbn)
    elif title or author:
        parts = []
        if title:  parts.append('title:"{}"'.format(title))
        if author: parts.append('contributor:"{}"'.format(author))
        q = ' AND '.join(parts)
    elif asin:
        q = asin
    else:
        return None

    url  = 'https://www.loc.gov/books/?q={}&fo=json&count=3'.format(quote_plus(q))
    data = _jget(url, timeout, retries, log, headers=hdrs)
    if not data:
        return None
    results = data.get('results', [])
    if not results:
        plain = quote_plus('{} {}'.format(title or '', author or '').strip())
        data  = _jget('https://www.loc.gov/books/?q={}&fo=json&count=3'.format(plain),
                      timeout, retries, log, headers=hdrs)
        if not data:
            return None
        results = data.get('results', [])
    if not results:
        return None

    item     = results[0]
    subjects = [s for s in item.get('subject_headings', []) if isinstance(s, str)]
    creators = item.get('contributors', []) or item.get('creator', [])
    auth_list = [c if isinstance(c, str) else c.get('label', '') for c in creators]
    img_urls  = item.get('image_url', []) or []
    cover_url = img_urls[0] if img_urls else ''
    cover_alts = img_urls[1:3] if len(img_urls) > 1 else []
    idents = {'isbn': isbn} if isbn else {}
    if asin:
        idents['amazon'] = asin
    desc = item.get('description', '') or item.get('notes', '')
    if isinstance(desc, list):
        desc = ' '.join(d for d in desc if isinstance(d, str))
    comments = desc.strip() if isinstance(desc, str) else ''

    return {
        'title':       item.get('title', ''),
        'authors':     [a for a in auth_list if a],
        'publisher':   item.get('publisher_or_distributor_number', ''),
        'pubdate':     item.get('date', ''),
        'comments':    comments,
        'tags':        subjects[:15],
        'language':    (item.get('language', [''])[0] if item.get('language') else ''),
        'identifiers': idents,
        'cover_url':   cover_url,
        'cover_alts':  cover_alts,
        'source':      'Library of Congress',
    }


# ── Internet Archive ───────────────────────────────────────────────────────────

def fetch_internetarchive(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    if isbn:
        q = 'isbn:{} AND mediatype:texts'.format(isbn)
    elif title or author:
        parts = []
        if title:  parts.append('title:({})'.format(title))
        if author: parts.append('creator:({})'.format(author))
        q = ' AND '.join(parts) + ' AND mediatype:texts'
    elif asin:
        q = 'identifier:{} AND mediatype:texts'.format(asin)
    else:
        return None

    url  = ('https://archive.org/advancedsearch.php'
            '?q={}&fl=identifier,title,creator,publisher,date,subject,'
            'language,isbn,description&rows=3&output=json'.format(quote_plus(q)))
    data = _jget(url, timeout, retries, log)
    if not data:
        return None
    docs = data.get('response', {}).get('docs', [])
    if not docs:
        return None
    doc   = docs[0]
    ident = doc.get('identifier', '')

    creators = doc.get('creator', [])
    if isinstance(creators, str): creators = [creators]
    subjects = doc.get('subject', [])
    if isinstance(subjects, str): subjects = [subjects]
    comments = doc.get('description', '')
    if isinstance(comments, list): comments = ' '.join(comments)

    cover_url  = 'https://archive.org/services/img/{}'.format(ident) if ident else ''
    cover_alts = []
    if ident:
        cover_alts.append('https://archive.org/services/img/{}'.format(ident))

    id_dict = {}
    if isbn:
        id_dict['isbn'] = isbn
    if ident:
        id_dict['archive.org'] = ident
    if asin:
        id_dict['amazon'] = asin

    pub = doc.get('publisher', '')
    if isinstance(pub, list): pub = ', '.join(str(p) for p in pub if p)
    lang_val = doc.get('language', '')
    if isinstance(lang_val, list): lang_val = lang_val[0] if lang_val else ''

    return {
        'title':       doc.get('title', ''),
        'authors':     creators,
        'publisher':   pub or '',
        'pubdate':     str(doc.get('date', '')),
        'comments':    comments,
        'tags':        subjects[:15],
        'language':    lang_val or '',
        'identifiers': id_dict,
        'cover_url':   cover_url,
        'cover_alts':  cover_alts,
        'source':      'Internet Archive',
    }


# ── ISBNdb ─────────────────────────────────────────────────────────────────────

def fetch_isbndb(title, author, isbn, api_key, asin='', lang='', timeout=20, retries=2, log=None):
    if not api_key:
        return None
    hdrs = {'Authorization': api_key, 'User-Agent': UA}
    if isbn:
        url = 'https://api2.isbndb.com/book/{}'.format(isbn)
    else:
        q   = quote_plus('{} {}'.format(title or '', author or '').strip())
        url = 'https://api2.isbndb.com/books/{}?page=1&pageSize=3'.format(q)
    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    book = data.get('book') or (data.get('books') or [None])[0]
    if not book:
        return None
    authors = book.get('authors', [])
    if isinstance(authors, str):
        authors = [authors]
    comments = (book.get('synopsis') or book.get('overview') or
                book.get('description') or '')
    idents = {'isbn': book.get('isbn13', isbn or '')}
    if asin:
        idents['amazon'] = asin
    return {
        'title':       book.get('title', ''),
        'authors':     authors,
        'publisher':   book.get('publisher', ''),
        'pubdate':     book.get('date_published', ''),
        'comments':    comments,
        'language':    book.get('language', ''),
        'identifiers': idents,
        'cover_url':   book.get('image', ''),
        'source':      'ISBNdb',
    }


# ── Amazon ─────────────────────────────────────────────────────────────────────

def _title_plausible_match(a, b, min_similarity=20):
    """
    True unless `a` and `b` are clearly unrelated titles. Deliberately more
    lenient than fuzzy.title_matches() — this only exists to catch the
    "completely wrong product" case (e.g. Amazon search surfacing a movie
    for a book query), not to judge edition/translation differences.

    A bare similarity() threshold is NOT safe here: similarity() penalizes
    length mismatches heavily (Jaccard word-overlap + Levenshtein), so a
    common and totally legitimate case — calibre's short title vs Amazon's
    "Title: Full Subtitle Here" — can score LOWER than a genuinely
    unrelated pair (field-checked: "Tecnofascismo" vs its own full
    title+subtitle scored 15, while an unrelated book/movie pair scored
    12 — too close together for any single cutoff to separate safely).
    So a substring-containment check (handles truncation/subtitles) is
    tried first, with similarity() only as a fallback for everything else.
    """
    na, nb = normalize_str(a), normalize_str(b)
    if not na or not nb:
        return True  # can't tell — don't block on missing data
    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    if shorter and shorter in longer:
        return True
    return similarity(a, b) >= min_similarity


def fetch_amazon(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Fetches from the language-appropriate Amazon storefront.

    v6.2 change: `lang` is now used to route to the correct TLD:
      es → amazon.es, it → amazon.it, fr → amazon.fr, de → amazon.de, etc.
    This is the main fix for 503 errors on Spanish/Italian books —
    amazon.com actively bot-blocks searches for non-English titles.

    The direct dp/<asin> and dp/<isbn> lookups always try amazon.com first
    (product pages are globally accessible) then fall back to the local TLD.
    The search fallback uses the local TLD from the start.

    v6.2.10: all "is this a real page" checks now go through
    _amazon_page_is_blocked(), which recognises several Amazon bot-challenge
    page variants (not just the classic CAPTCHA). Previously only one
    signature was checked, so other block-page variants were treated as
    real HTML, fed to the parser, correctly found to contain no title, and
    silently discarded — with no way to tell "this was a block page" apart
    from "this was a real page the parser failed on". Every dead end now
    logs which of those two things actually happened.
    """
    result = {}
    # Determine which Amazon storefront to use for search first, so we can
    # set the correct Accept-Language header for that TLD.
    local_tld = _amazon_tld_for_lang(lang)
    accept_lang = _AMAZON_TLD_TO_ACCEPT_LANG.get(local_tld, 'en-US,en;q=0.9')
    # v6.2.10: added Sec-Fetch-*/Sec-Ch-Ua/Cache-Control headers. Amazon's
    # search endpoint (/s?k=...) was 503-ing on the very first attempt for
    # every single book in field logs — that pattern (instant block, not a
    # rate-limit-after-N-requests pattern) points to Amazon's edge WAF
    # fingerprinting requests that are missing headers a real browser always
    # sends, rather than pure request-volume throttling. These are the same
    # headers a Chrome navigation actually sends; product (dp/) pages were
    # less affected since they're more cacheable/less aggressively gated.
    hdrs = {
        'User-Agent': UA,
        'Accept-Language': accept_lang,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive',
    }

    _asin_valid = bool(asin and re.match(r'^[A-Z0-9]{10}$', asin))
    if not _asin_valid and asin:
        if log:
            log.warning('Amazon: ignoring non-ASIN identifier %r (not 10 chars)', asin[:40])
        asin = ''

    # ── 1. Direct dp/ lookup by ASIN (amazon.com; product pages are global) ──
    if asin:
        url = 'https://www.amazon.com/dp/{}'.format(asin)
        if log:
            log.info('Amazon: trying dp/ lookup for ASIN %s', asin)
        raw = _amazon_fetch(url, timeout, retries, hdrs, log)
        if raw:
            result = _parse_amazon_page(raw, asin, log=log)
            if result and log:
                log.info('Amazon: got result via ASIN dp/ %s', asin)
            elif log:
                log.debug('Amazon: dp/ page for ASIN %s parsed but no usable '
                          'title found (page was %d bytes)', asin, len(raw))
        # v6.2.31: also try the local TLD when .com gave a title but no
        # description — same Kindle-region-exclusivity issue as the ISBN
        # path below. A local result WITH a description replaces a bare
        # .com one; a local result without one only fills in if .com had
        # nothing at all.
        if (not result or not result.get('comments')) and local_tld != 'amazon.com':
            url2 = 'https://www.{}/dp/{}'.format(local_tld, asin)
            if log:
                log.info('Amazon: trying %s dp/ for ASIN %s', local_tld, asin)
            raw2 = _amazon_fetch(url2, timeout, 1, hdrs, log)
            if raw2:
                local_result = _parse_amazon_page(raw2, asin, log=log)
                if local_result and local_result.get('comments'):
                    result = local_result
                    if log:
                        log.info('Amazon: got result (with description) via '
                                 '%s dp/ %s', local_tld, asin)
                elif local_result and not result:
                    result = local_result
                    if log:
                        log.info('Amazon: got result via %s dp/ %s', local_tld, asin)
                elif log:
                    log.debug('Amazon: %s dp/ page for ASIN %s parsed but no '
                              'usable title found', local_tld, asin)

    # ── 2. Direct dp/ lookup by ISBN ─────────────────────────────────────────
    # v6.2.29 ROOT-CAUSE FIX: Amazon's dp/<id> path takes an ASIN or an
    # ISBN-10 — it does NOT resolve 13-digit ISBNs (field-confirmed: dp/
    # lookups for a valid ISBN-13 consistently returned a real-but-useless
    # "notitle" page on both amazon.com and the local TLD, for a book that
    # demonstrably exists and has a normal product page under its ISBN-10).
    # This silently produced zero Amazon data for every ISBN-13-only book —
    # and since "amazon_direct_only" (on by default) also skips the search
    # fallback whenever an ISBN is known, Amazon contributed NOTHING at
    # all, with no obvious sign why. Now the dp/ URL is built from the
    # ISBN-10 form whenever the given ISBN converts (nearly all 978-prefix
    # ISBN-13s do); the original string is tried too, in case of an
    # already-ISBN-10 identifier or a Kindle-only listing that happens to
    # accept the 13-digit form.
    _isbn10 = isbn13_to_10(isbn) if isbn else None
    _dp_isbn_candidates = []
    if _isbn10 and _isbn10 != isbn:
        _dp_isbn_candidates.append(_isbn10)
    if isbn:
        _dp_isbn_candidates.append(isbn)

    if not result and _dp_isbn_candidates:
        for _dp_id in _dp_isbn_candidates:
            if result and result.get('comments'):
                break
            if log:
                log.info('Amazon: trying dp/ lookup for ISBN %s', _dp_id)
            url = 'https://www.amazon.com/dp/{}'.format(_dp_id)
            raw = _amazon_fetch(url, timeout, retries, hdrs, log)
            if raw:
                result = _parse_amazon_page(raw, _dp_id, log=log)
                if result and log:
                    log.info('Amazon: got result via ISBN dp/ %s', _dp_id)
                elif log:
                    log.debug('Amazon: dp/ page for ISBN %s parsed but no usable '
                              'title found', _dp_id)
            # v6.2.31 ROOT-CAUSE FIX: previously this only ran when `result`
            # was still empty, so a "got a title but no description"
            # amazon.com page (field-confirmed: Kindle ebooks are commonly
            # exclusive to one regional storefront — amazon.com showed a
            # bare cross-market listing for a book that's actually sold on
            # amazon.es, with a full "Descripción del producto" only on the
            # .es page) permanently short-circuited Amazon's synopsis
            # contribution even though the real content was one TLD away.
            # Now the local TLD is also tried whenever the .com result is
            # missing a description, and if the local page has one, its
            # richer result REPLACES the bare .com one (rather than being
            # discarded just because .com "succeeded" first).
            if (not result or not result.get('comments')) and local_tld != 'amazon.com':
                url2 = 'https://www.{}/dp/{}'.format(local_tld, _dp_id)
                if log:
                    log.info('Amazon: trying %s dp/ for ISBN %s (%s)',
                             local_tld, _dp_id,
                             'no result yet' if not result else 'got title but no description on .com')
                raw2 = _amazon_fetch(url2, timeout, 1, hdrs, log)
                if raw2:
                    local_result = _parse_amazon_page(raw2, _dp_id, log=log)
                    if local_result and local_result.get('comments'):
                        result = local_result
                        if log:
                            log.info('Amazon: got result (with description) via '
                                     '%s dp/ %s', local_tld, _dp_id)
                    elif local_result and not result:
                        result = local_result
                        if log:
                            log.info('Amazon: got result via %s dp/ %s', local_tld, _dp_id)
                    elif log:
                        log.debug('Amazon: %s dp/ page for ISBN %s parsed but no '
                                  'usable title found', local_tld, _dp_id)

    # ── 3. Search fallback on the language-appropriate TLD ───────────────────
    # Skip the search when a direct ASIN/ISBN is already known and the user
    # has chosen direct-lookup-only mode (default: True).  The search opens
    # a browser window per candidate (up to 5), and all candidates for a
    # given ASIN are often other editions of the same Audible/audiobook entry.
    _direct_only = True
    try:
        from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
        _direct_only = bool(prefs.get('amazon_direct_only', True))
    except Exception:
        pass
    _skip_search = _direct_only and bool(asin or isbn)
    if not result and _skip_search:
        # v6.2.29: this is the actual "why did Amazon return nothing" case
        # — the direct ASIN/ISBN dp/ lookup(s) above all failed AND
        # amazon_direct_only is suppressing the title-search fallback that
        # would otherwise have found the book. This used to be a debug-
        # level message behind a condition that could never actually be
        # true when a search was really being skipped (comparing
        # `_skip_search is False` while describing the skip-search case),
        # so it never printed when it mattered. Now a clear, actionable
        # WARNING explains exactly what happened and how to change it.
        if log:
            log.warning(
                'Amazon: direct dp/ lookup found no usable page for %s — '
                'title-search fallback was NOT tried because "Amazon: '
                'direct lookup only" is enabled in Options (Options > '
                'Browser Fallback). Amazon will contribute nothing for '
                'this book. Disable that setting if you want Amazon '
                'tried via title search whenever the direct lookup fails.',
                asin or isbn)
    if not result and (title or author) and not _skip_search:
        if _amazon_search_in_cooldown(local_tld):
            if log:
                log.warning('Amazon: skipping search fallback on %s (in 503 cooldown)', local_tld)
            # Try .com as a second chance if local TLD is in cooldown
            if local_tld != _DEFAULT_AMAZON_TLD and not _amazon_search_in_cooldown(_DEFAULT_AMAZON_TLD):
                local_tld = _DEFAULT_AMAZON_TLD
            else:
                local_tld = None  # give up on search

        if local_tld:
            # Strip locale/edition noise from the title before searching.
            # "(Spanish Edition)", "(Edición española)" etc. confuse Amazon
            # search and cause it to surface the print ISBN instead of the
            # Kindle ASIN in the data-asin attribute.
            search_title = re.sub(
                r'\s*\([^)]{0,60}(?:Edition|Edici[oó]n|edizione|Ausgabe|[eé]dition|版)[^)]{0,30}\)\s*$',
                '', title or '', flags=re.I).strip() or title or ''
            # Also strip subtitle after ": ", " - ", " – " to keep the query tight
            search_title = re.split(r'\s*[–—]\s*|\s+-\s+|:\s+', search_title, maxsplit=1)[0].strip() \
                           or search_title

            q    = quote_plus('{} {}'.format(search_title, author or '').strip())
            surl = 'https://www.{}/s?k={}&i=stripbooks'.format(local_tld, q)
            if log:
                log.info('Amazon: trying search on %s for %r', local_tld, search_title[:50])
            # Small randomized pre-request delay: field logs show search
            # 503-ing on the very first attempt for almost every book run in
            # quick succession, which looks like burst-pattern detection
            # rather than pure per-request throttling. A sub-second jitter
            # costs little and makes consecutive requests look less robotic.
            time.sleep(0.4 + (hash(surl) % 50) / 100.0)  # ~0.4-0.9s, deterministic jitter
            raw = _amazon_fetch(surl, timeout, retries, hdrs, log)

            # v6.2.30: previously, a search that failed outright (timeout,
            # 503/bot-block) on the local TLD just gave up for THIS book —
            # the existing "fall back to .com" logic only helped a LATER
            # book in the same session avoid retrying a TLD already known
            # to be in cooldown, which does nothing for the book that just
            # failed. Now: if the local-TLD search produced no content at
            # all and we weren't already trying amazon.com, immediately
            # retry once on amazon.com in the same call — product/search
            # pages on .com are frequently less aggressively gated than a
            # just-hit regional storefront, and this gives the CURRENT book
            # a real second chance instead of only helping the next one.
            if not raw and local_tld != _DEFAULT_AMAZON_TLD:
                if log:
                    log.info('Amazon: search on %s failed outright — '
                             'retrying once on %s', local_tld, _DEFAULT_AMAZON_TLD)
                surl2 = 'https://www.{}/s?k={}&i=stripbooks'.format(_DEFAULT_AMAZON_TLD, q)
                raw = _amazon_fetch(surl2, timeout, 1, hdrs, log)
                if raw:
                    local_tld = _DEFAULT_AMAZON_TLD

            if raw:
                # Collect all data-asin values from the results page.
                # data-asin can contain ISBN-10s (all-digit 10-char strings)
                # as well as real ASINs (letter+digit mix starting with B0).
                # We try up to 3 candidates, preferring real ASINs first.
                all_asins = re.findall(r'data-asin="([A-Z0-9]{10})"', raw)
                # Deduplicate while preserving order
                seen_asins = set()
                candidates = []
                for a in all_asins:
                    if a and a not in seen_asins:
                        seen_asins.add(a)
                        candidates.append(a)

                # Sort: real ASINs (contain at least one letter) before
                # pure-digit ISBN-10s so we try the most likely hit first.
                def _asin_priority(a):
                    return 0 if re.search(r'[A-Z]', a) else 1
                candidates.sort(key=_asin_priority)
                candidates = candidates[:5]  # cap at 5 to avoid long loops

                if log and not candidates:
                    log.debug('Amazon: search on %s returned a real results page '
                              'but no data-asin values were found in it (page '
                              'layout may have changed, or zero results)', local_tld)

                # v6.2.26: previously accepted the FIRST candidate that
                # parsed a title, with no language check at all — so on a
                # storefront that stocks multiple language editions (every
                # Amazon TLD does; amazon.it lists Spanish/English/etc.
                # editions too), a wrong-language edition could win just for
                # appearing first in the search results. Now every parseable
                # candidate is checked against the requested `lang` (when
                # known); a same-language match is taken immediately, and a
                # wrong-language match is kept only as a fallback in case no
                # same-language candidate turns up among the (up to 5) tried.
                # v6.2.32 ROOT-CAUSE FIX: this loop validated LANGUAGE but
                # never validated that a search candidate is even the same
                # BOOK — a weak/no-match search (e.g. a self-published
                # Spanish title with no real amazon.com listing) can have
                # Amazon's search surface a data-asin for something from a
                # completely different department (field-confirmed: a
                # search for "Las hechiceras de Madrid Las Tres Amigas"
                # returned a Prime Video show, "Ver The Other End of the
                # Rope | Prime Video", as its data-asin candidate — real
                # HTML, a real title, a real "result", just for the wrong
                # product entirely). That got discarded later at merge time
                # by the title-similarity check there, so no wrong data
                # reached calibre — but it wasted a full page fetch, logged
                # a misleading "Got result from amazon" line, and (in a
                # book that DOES have a real Amazon match a few candidates
                # down the list) could have blocked trying the rest of the
                # candidates if this were the language match. Now a basic
                # title-relevance floor applies before language is even
                # considered: a candidate whose extracted title doesn't
                # resemble the book's title at all is skipped immediately,
                # not accepted as "the result".
                _target_lang = (lang or '').lower()[:2]
                _fallback_result = None
                for found_id in candidates:
                    if log:
                        log.info('Amazon: search candidate %s, fetching dp/ page', found_id)
                    purl = 'https://www.{}/dp/{}'.format(local_tld, found_id)
                    praw = _amazon_fetch(purl, timeout, 1, hdrs, log)
                    if praw:
                        candidate_result = _parse_amazon_page(praw, found_id, log=log)
                        if candidate_result and candidate_result.get('title'):
                            if title and not _title_plausible_match(title, candidate_result['title']):
                                if log:
                                    log.info(
                                        'Amazon: candidate %s title %r does not '
                                        'resemble %r — likely a wrong/unrelated '
                                        'product, not just a wrong edition; skipping',
                                        found_id, candidate_result['title'][:60],
                                        title[:60])
                                continue
                            cand_lang = (candidate_result.get('language') or '').lower()[:2]
                            if not _target_lang or not cand_lang or cand_lang == _target_lang:
                                result = candidate_result
                                break
                            # Wrong language confirmed — remember as a last
                            # resort but keep looking for a better match.
                            if log:
                                log.info('Amazon: candidate %s is %r edition, '
                                         'book is %r — trying next candidate',
                                         found_id, cand_lang, _target_lang)
                            if _fallback_result is None:
                                _fallback_result = candidate_result
                        elif log:
                            log.debug('Amazon: dp/ page for candidate %s was real '
                                      'HTML but no title could be parsed from it '
                                      '— trying next candidate', found_id)
                    elif log:
                        log.debug('Amazon: dp/ fetch for candidate %s returned '
                                  'no content (timeout/network error) — trying '
                                  'next candidate', found_id)
                if not result and _fallback_result is not None:
                    if log:
                        log.info('Amazon: no %r-language candidate found among %d '
                                 'tried — falling back to closest match (%r)',
                                 _target_lang, len(candidates),
                                 (_fallback_result.get('language') or '?'))
                    result = _fallback_result

    if result:
        idents = result.setdefault('identifiers', {})
        if asin:
            idents.setdefault('amazon', asin)
        if isbn:
            idents.setdefault('isbn', isbn)
        result['source'] = 'Amazon'
        return result
    return None


def _dump_amazon_debug_html(raw, identifier, reason, log):
    """
    Write the raw Amazon HTML to calibre's config directory so it can be
    opened in a browser for offline inspection.

    Called whenever _page_is_audiobook() returns True (reason='audiobook')
    or when _parse_amazon_page() returns no title (reason='notitle'), so
    you can diff the HTML against a known-good page to repair the parser.

    File written to: <calibre config dir>/metadata_plus_debug_amazon_<id>_<reason>.html
    """
    try:
        from calibre.utils.config import config_dir  # type: ignore
        safe_id = re.sub(r'[^\w\-]', '_', str(identifier))
        fname = 'metadata_plus_debug_amazon_{}_{}.html'.format(safe_id, reason)
        path = os.path.join(config_dir, fname)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(raw)
        log.info('Amazon: debug HTML (%s, %d bytes) dumped to %s', reason, len(raw), path)
    except Exception as exc:
        log.debug('Amazon: could not write debug HTML: %s', exc)


def _page_is_audiobook(raw):
    """
    Return True when a product page is clearly an Audible/audiobook edition.

    Detection order:
      1. Strong JSON signals — "productGroup":"audible" or
         "binding":"audible download" embedded in the page data.  These are
         the most reliable and are checked first.
      2. Kindle short-circuit — if the binding JSON says "Kindle Edition"
         the page is definitively a Kindle product, NOT an audiobook, even
         if it carries a Whispersync cross-sell widget.
      3. "Listening Length" in product details — reliable once we know the
         page is not a Kindle edition (guarded above).

    v6.2.14 (Jadehawk Edits): removed the "soft signal" block that checked for audible.com
    and acx.com links.  Amazon includes both in its footer navigation on
    EVERY product page, so they are useless as product-type indicators and
    caused false positives on normal Kindle/print pages (confirmed with ASIN
    B0F344HDYN "Target Practice" — a Kindle ebook incorrectly detected as
    an audiobook).  The three signals above are sufficient to identify real
    Audible product pages.
    """
    # Strong positive signals — structural JSON metadata
    if re.search(r'"productGroup"\s*:\s*"audible"', raw, re.I):
        return True
    if re.search(r'"binding"\s*:\s*"audible\s*download"', raw, re.I):
        return True

    # Short-circuit: Kindle Edition pages are never audiobooks.
    if re.search(r'"binding"\s*:\s*"kindle\s+edition"', raw, re.I):
        return False

    # "Listening Length" in a product detail row is a reliable audiobook
    # signal once we know the page is not a Kindle edition (guarded above).
    if re.search(r'Listening\s+Length', raw, re.I):
        return True

    return False


def _parse_amazon_page(raw, identifier, log=None):
    # Bail out early if this page is an audiobook product
    if _page_is_audiobook(raw):
        if log:
            log.debug('Amazon: page for %s is an audiobook edition — skipping', identifier)
            _dump_amazon_debug_html(raw, identifier, 'audiobook', log)
        return {}   # empty dict — no usable metadata from this audiobook page

    result = {}

    # ── Title extraction — try multiple patterns in priority order ────────────
    # Amazon has changed its HTML structure several times; regional storefronts
    # (especially .es/.it/.fr) and Kindle-only titles may omit the classic
    # id="productTitle" span and serve og:title as just "Amazon.es" on
    # bot-challenged or redirect pages.  We validate every candidate before
    # accepting it.

    # Known-bad values returned by Amazon when the real product title is absent
    # (bot-check pages, store homepages, login walls).
    _AMAZON_JUNK_TITLES = re.compile(
        r'^amazon\.(?:com|es|it|fr|de|co\.jp|com\.br|nl|pl|se|com\.tr|ae|in|cn)'
        r'|^amazon$'
        r'|robot check'
        r'|sign[\s-]?in'
        r'|page not found'
        r'|sorry[,!]?\s+we',
        re.I,
    )

    def _clean_amazon_title(t):
        """Strip store-name suffixes and edition noise; return '' if junk."""
        t = re.sub(r'<[^>]+>', '', t).strip()
        t = re.sub(r'\s+', ' ', t)
        # Strip trailing store suffixes: " - Amazon.es", ": Amazon.it: ..."
        t = re.split(r'\s*:\s*Amazon\.', t, maxsplit=1)[0].strip()
        t = re.sub(r'\s*[-–|]\s*Amazon\.[a-z.]+\s*$', '', t, flags=re.I).strip()
        # Strip "(Spanish Edition)", "(Edición española)", etc.
        t = re.sub(r'\s*\([^)]{0,40}(?:Edition|Edición|edizione)\)\s*$', '', t, flags=re.I).strip()
        if not t or _AMAZON_JUNK_TITLES.search(t):
            return ''
        return t

    _title_raw = ''

    # 1. Classic id="productTitle" span (most reliable when present)
    m = re.search(r'id=["\']productTitle["\'][^>]*>\s*(.*?)\s*</span>', raw, re.S)
    if m:
        _title_raw = _clean_amazon_title(m.group(1))

    # 2. data-feature-name="title" / dp-title (newer SPA layout used on .es/.it)
    if not _title_raw:
        for pat in [
            r'data-feature-name=["\']title["\'][^>]*>\s*<[^>]+>\s*(.*?)\s*</[^>]+>',
            r'id=["\']dp-title["\'][^>]*>\s*<[^>]+>\s*(.*?)\s*</[^>]+>',
        ]:
            m = re.search(pat, raw, re.S)
            if m:
                _title_raw = _clean_amazon_title(m.group(1))
                if _title_raw:
                    break

    # 3. JSON-LD @type:Book "name" field
    # Use a broader search that tolerates nested braces in the JSON block.
    if not _title_raw:
        # Forward search: @type:Book appears before "name"
        m = re.search(
            r'"@type"\s*:\s*"Book".{0,3000}?"name"\s*:\s*"((?:[^"\\]|\\.)+)"',
            raw, re.S)
        if not m:
            # Reverse: "name" before @type:Book (some serialisers reorder keys)
            m = re.search(
                r'"name"\s*:\s*"((?:[^"\\]|\\.)+)".{0,3000}?"@type"\s*:\s*"Book"',
                raw, re.S)
        if m:
            try:
                cand = m.group(1).encode('utf-8').decode('unicode_escape', errors='replace')
            except Exception:
                cand = m.group(1)
            _title_raw = _clean_amazon_title(cand)

    # 4. React/Apollo JSON "title":{"value":"..."} (modern SPA layout)
    if not _title_raw:
        m = re.search(r'"title"\s*:\s*\{"value"\s*:\s*"((?:[^"\\]|\\.)+)"', raw, re.S)
        if m:
            _title_raw = _clean_amazon_title(m.group(1))

    # 5. og:title meta tag — validated; "Amazon.es" bare value is rejected
    if not _title_raw:
        m = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']{3,})["\']',
            raw, re.I)
        if not m:
            # content= before property= (attribute order varies)
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']{3,})["\'][^>]+property=["\']og:title["\']',
                raw, re.I)
        if m:
            _title_raw = _clean_amazon_title(m.group(1))

    # 6. <title> tag — last resort; very noisy
    if not _title_raw:
        m = re.search(r'<title[^>]*>([^<]{5,})</title>', raw, re.I)
        if m:
            _title_raw = _clean_amazon_title(m.group(1))

    if _title_raw:
        result['title'] = _title_raw
    else:
        # Could not extract a real title — return empty so the caller treats
        # this as a failed parse rather than an identifiers-only result.
        if log:
            log.debug('Amazon: page for %s had no extractable title — all 6 patterns failed', identifier)
            _dump_amazon_debug_html(raw, identifier, 'notitle', log)
        return {}

    # ── Language extraction (v6.2.26) ────────────────────────────────────────
    # ROOT CAUSE of "Spanish edition picked for an Italian book search on
    # amazon.it": _parse_amazon_page never extracted a language at all, so
    # fetch_amazon's search-candidate loop had no way to tell a Spanish
    # Kindle edition apart from an Italian one — it just accepted whichever
    # of the first few data-asin candidates parsed a title. Amazon storefronts
    # sell books in every language regardless of TLD (amazon.it stocks
    # Spanish, English, etc. editions too), so the TLD alone is not a
    # reliable language signal.
    #
    # Two signals are checked, cheapest/most reliable first:
    #   1. The edition marker still present in the *raw* (uncleaned) title
    #      fragment, e.g. "(Spanish Edition)" / "(Edición española)" /
    #      "(edizione italiana)" — _clean_amazon_title() strips this before
    #      we ever see it above, so we re-derive it from _title_raw's source
    #      fragment captured before cleaning would have removed it. Since we
    #      don't keep that pre-clean string around, we re-search the raw
    #      page HTML directly for the same marker patterns instead.
    #   2. The "Language" / "Idioma" / "Lingua" / "Langue" / "Sprache" row in
    #      Amazon's product-details panel, which is present on most product
    #      pages regardless of storefront language.
    _AMAZON_LANG_WORDS = {
        'en': ('english', 'inglés', 'ingles', 'inglese', 'englisch', 'anglais'),
        'es': ('spanish', 'español', 'espanol', 'spagnolo', 'espagnol', 'castellano'),
        'it': ('italian', 'italiano', 'italien', 'italienisch'),
        'fr': ('french', 'francés', 'frances', 'francese', 'français', 'francais', 'franzosisch'),
        'de': ('german', 'alemán', 'aleman', 'tedesco', 'deutsch', 'allemand'),
        'pt': ('portuguese', 'portugués', 'portugues', 'portoghese', 'português', 'portugais'),
        'ro': ('romanian', 'rumano', 'rumeno', 'română', 'romana', 'roumain'),
        'nl': ('dutch', 'holandés', 'olandese', 'niederländisch', 'néerlandais'),
    }
    _lang_word_alt = '|'.join(w for words in _AMAZON_LANG_WORDS.values() for w in words)

    def _lang_code_for_word(word):
        word = word.lower()
        for code, words in _AMAZON_LANG_WORDS.items():
            if word in words:
                return code
        return ''

    detected_lang = ''

    # Signal 1: edition marker anywhere in the raw page ("(Spanish Edition)",
    # "(Edición española)", "(edizione italiana)", etc.)
    m = re.search(
        r'\(\s*(?:edici[oó]n|edizione)?\s*({})\s*(?:edition|edici[oó]n|edizione)?\s*\)'
        .format(_lang_word_alt),
        raw, re.I)
    if m:
        detected_lang = _lang_code_for_word(m.group(1))

    # Signal 2: product-details "Language:"/"Idioma:"/"Lingua:" row.
    if not detected_lang:
        m = re.search(
            r'(?:language|idioma|lingua|langue|sprache)\s*'
            r'(?:</[^>]+>\s*)?[:\uFF1A]?\s*(?:</?[^>]*>\s*)*({})'
            .format(_lang_word_alt),
            raw, re.I)
        if m:
            detected_lang = _lang_code_for_word(m.group(1))

    if detected_lang:
        result['language'] = detected_lang

    # ── Authors extraction ────────────────────────────────────────────────────
    authors = re.findall(r"class=[\"']author[\"'][^>]*>.*?<a[^>]*>(.*?)</a>", raw, re.S)
    if authors:
        result['authors'] = [re.sub(r'<[^>]+>', '', a).strip() for a in authors[:5]]
    # Fallback: JSON-LD "author" field (array or single object)
    if not result.get('authors'):
        # Array form: "author":[{"name":"..."},...]
        jld_authors = re.findall(r'"author"\s*:\s*\[(?:[^]]*?"name"\s*:\s*"([^"]+)"[^]]*?)+\]',
                                 raw, re.S)
        if not jld_authors:
            jld_authors = re.findall(r'"author"\s*:\s*\{"name"\s*:\s*"([^"]+)"', raw, re.S)
        if jld_authors:
            result['authors'] = [a.strip() for a in jld_authors[:5]]
    # Fallback: og:author or author meta tag
    if not result.get('authors'):
        m = re.search(r'<meta[^>]+(?:name=["\']author["\']|property=["\']book:author["\'])'
                      r'[^>]+content=["\']([^"\']{2,})["\']', raw, re.I)
        if m:
            result['authors'] = [m.group(1).strip()]

    for pat in [r'Publisher[^:]*?:\s*<[^>]*>([^<]+)',
                r'"publisher"\s*:\s*"([^"]+)"']:
        m = re.search(pat, raw, re.I)
        if m:
            result['publisher'] = re.split(r'[;\(]', m.group(1))[0].strip()
            break
    m = re.search(r'"ASIN"\s*:\s*"([A-Z0-9]{10})"', raw)
    page_asin = m.group(1) if m else ''
    result['identifiers'] = {'amazon': page_asin or identifier}

    for pat in [
        r'ISBN-13[^<]{0,10}[\s:]+([0-9]{3}[-\s]?[0-9]{10}|[0-9]{13})',
        r'ISBN-10[^<]{0,10}[\s:]+([0-9][-\s]?[0-9]{9}|[0-9]{10})',
        r'Print ISBN[^<]{0,20}[\s:]+([0-9]{3}[-\s]?[0-9]{10}|[0-9]{13}|[0-9]{10})',
        r'"isbn"\s*:\s*"(\d{10,13})"',
    ]:
        m = re.search(pat, raw, re.I)
        if m:
            candidate = re.sub(r'[-\s]', '', m.group(1))
            if len(candidate) in (10, 13):
                result['identifiers']['isbn'] = candidate
                break

    # --- Synopsis extraction ---
    # Amazon uses several different structures across storefronts and over time.
    # We try them in descending order of reliability; keep the longest match
    # that survives the title-echo check below.
    #
    # KNOWN BUG (fixed here): Amazon's <meta name="description"> / og:description
    # tag frequently contains nothing but the page title repeated verbatim
    # (e.g. content="Votos Quebrados: Abandonada en el altar, embarazada y
    # atrapada... - Tess Mitchel"), NOT the actual book synopsis. Pattern #3
    # below had no safeguard against this, so on pages without a real
    # bookDescription block, the "synopsis" silently became a copy of the
    # title.  Every candidate is now checked against the already-extracted
    # title with _looks_like_title_echo() before being accepted.
    desc = ''

    def _looks_like_title_echo(candidate, title):
        """
        Return True when `candidate` is substantially just `title` repeated
        (optionally with author/edition noise appended), rather than an
        actual synopsis.  This is what Amazon's meta-description tag often
        contains when no real product description exists.
        """
        if not candidate or not title:
            return False
        cand_norm  = re.sub(r'[^\w\s]', '', candidate.lower()).strip()
        title_norm = re.sub(r'[^\w\s]', '', title.lower()).strip()
        if not cand_norm or not title_norm:
            return False
        # Case 1: candidate starts with the title (title + " - Author" etc.)
        if cand_norm.startswith(title_norm) and len(cand_norm) < len(title_norm) + 60:
            return True
        # Case 2: candidate IS the title with only minor punctuation/casing diff
        if cand_norm == title_norm:
            return True
        # Case 3: word-overlap ratio is very high AND candidate isn't much
        # longer than the title (a real synopsis is always substantially
        # longer than the title it describes).
        title_words = set(title_norm.split())
        cand_words  = set(cand_norm.split())
        if title_words and len(cand_words) <= len(title_words) * 1.6:
            overlap = len(title_words & cand_words) / len(title_words)
            if overlap >= 0.75:
                return True
        return False

    # ── Kindle-store boilerplate detector ──────────────────────────────────────
    # SECOND BUG (this fix): _looks_like_title_echo() only catches candidates
    # that are mostly the title's own words repeated. It completely misses
    # Amazon's other standard junk text — the fixed Kindle-store sales pitch
    # that Amazon stamps into <meta name="description"> on EVERY Kindle
    # product page when no real "About this book" synopsis is present:
    #
    #   "<Title> - Kindle edition by <Author>. Download it once and read it
    #    on your Kindle device, PC, phones or tablets. Use features like
    #    bookmarks, note taking and highlighting while reading <Title>."
    #
    # This text is 200-300+ characters, mostly DIFFERENT words from the
    # title (download, device, phones, tablets, bookmarks, note taking,
    # highlighting...), so the word-overlap ratio in _looks_like_title_echo
    # falls well below the 75% threshold and the junk sails through as if it
    # were a real synopsis (confirmed: "La Capa: Thriller Psicologico" ->
    # 277-char Kindle boilerplate, accepted as the book's Description).
    #
    # Fix: recognise this fixed marketing template directly via its
    # characteristic phrases, which never appear in a genuine synopsis.
    _KINDLE_BOILERPLATE_RE = re.compile(
        r'kindle edition by|download it once and read it|'
        r'use features like bookmarks[,]?\s*note taking|'
        r'note taking and highlighting while reading|'
        r'read it on your kindle device|'
        r'descargue.*lea en su dispositivo kindle|'  # Spanish storefront variant
        r'scarica.*leggi sul tuo dispositivo kindle|'  # Italian storefront variant
        r't[ée]l[ée]chargez.*lisez.le sur votre kindle',  # French storefront variant
        re.I,
    )

    def _looks_like_kindle_boilerplate(candidate):
        """
        Return True when `candidate` is Amazon's generic Kindle-store sales
        pitch ("Download it once and read it on your Kindle device...")
        rather than an actual book synopsis.  This fixed template is stamped
        into the page's meta-description whenever no real "About this book"
        blurb exists, on every regional Amazon storefront.
        """
        if not candidate:
            return False
        return bool(_KINDLE_BOILERPLATE_RE.search(candidate))

    # ── Amazon <title>-tag junk detector ───────────────────────────────────────
    # THIRD bug (this fix): some Amazon storefronts fall back to using the raw
    # browser <title> tag content as the og:description / meta-description
    # value when no real synopsis or Kindle-boilerplate text is present.
    # That <title> tag is the page's own SEO title line, not a synopsis:
    #
    #   "Amazon.com: <Title> (<Edition>) eBook : <Author>: Tienda Kindle"
    #   "Amazon.es: <Title>: <Author>: Libros"
    #   "Amazon.it: <Title>: <Author>: Libri in altre lingue"
    #
    # Field-confirmed: ASIN B0H6JD9QXN "Todo lo que el agua calla" (Payá,
    # Eugenio) produced "Amazon.com: Todo lo que el agua calla: ... (Spanish
    # Edition) eBook : Payá, Eugenio: Tienda Kindle" as the saved Description
    # — a 144-character string that is essentially just the page's <title>,
    # not back-cover copy.  This pattern starts with "Amazon.<tld>:" followed
    # by a colon-separated structure ending in a store-section label
    # (Tienda Kindle / Libros / Kindle Store / eBooks / Libri), which never
    # occurs in genuine synopsis prose.
    # v6.2.26: previously this only matched when "Amazon.<tld>:" appeared at
    # the START of the string. Field-confirmed variant has the book's own
    # title first and "Amazon.<tld>: <section>" trailing at the END instead
    # — e.g. "Tecnofascismo: ... (Spanish Edition) eBook : Cesare, Donatella
    # di, Cortés Fernández, Lara: Amazon.it: Kindle Store" — which the
    # start-anchored pattern let straight through as a "182 char synopsis".
    # Now matches either ordering.
    _AMAZON_TLDS_RE = (r'com|es|it|fr|de|co\.uk|co\.jp|com\.br|nl|pl|se|'
                       r'com\.tr|ae|in|cn|ca|com\.mx')
    _AMAZON_STORE_SECTIONS_RE = (r'tienda kindle|kindle store|libros|'
                                 r'libri(?: in altre lingue)?|ebooks?|livres|'
                                 r'b[üu]cher|boutique kindle|ebook kindle')
    _AMAZON_PAGE_TITLE_RE = re.compile(
        r'^\s*amazon\.(?:{tld})\s*:.*:\s*(?:{sec})\s*$'
        r'|:\s*amazon\.(?:{tld})\s*:\s*(?:{sec})\s*$'
        .format(tld=_AMAZON_TLDS_RE, sec=_AMAZON_STORE_SECTIONS_RE),
        re.I,
    )

    def _looks_like_amazon_page_title(candidate):
        """
        Return True when `candidate` is Amazon's own page <title> tag content
        (store-name prefix + colon-separated breadcrumb ending in a store
        section label) rather than a real book synopsis.
        """
        if not candidate:
            return False
        return bool(_AMAZON_PAGE_TITLE_RE.search(candidate))

    def _is_junk_synopsis(candidate, title):
        """Combined guard: reject title-echoes, Kindle boilerplate, and
        Amazon's own page-<title>-tag content masquerading as a synopsis."""
        return (_looks_like_title_echo(candidate, title) or
                _looks_like_kindle_boilerplate(candidate) or
                _looks_like_amazon_page_title(candidate))

    _title_for_echo_check = result.get('title', '')

    # 1. JSON-LD @type:Book description — most reliable on .es/.it/.fr pages
    m = re.search(r'"@type"\s*:\s*"Book"[^}]{0,3000}"description"\s*:\s*"((?:[^"\\]|\\.)+)"',
                  raw, re.S)
    if not m:
        m = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.){40,})"[^}]{0,3000}"@type"\s*:\s*"Book"',
                      raw, re.S)
    if m:
        candidate = m.group(1)
        try:
            candidate = candidate.encode('utf-8').decode('unicode_escape', errors='replace')
        except Exception:
            pass
        candidate = re.sub(r'\\n', ' ', candidate)
        candidate = re.sub(r'<[^>]+>', '', candidate)
        candidate = re.sub(r'\s+', ' ', candidate).strip()
        if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
            desc = candidate

    # 2. React/Apollo JSON state: "description":{"value":"..."}
    if len(desc) < 30:
        m = re.search(r'"description"\s*:\s*\{"value"\s*:\s*"((?:[^"\\]|\\.)+)"', raw, re.S)
        if m:
            candidate = re.sub(r'\\n', ' ', m.group(1))
            candidate = re.sub(r'<[^>]+>', '', candidate)
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
                desc = candidate

    # 3. og:description / meta name=description — present on virtually all
    #    storefronts, but UNRELIABLE: frequently just echoes the title/author,
    #    or — more commonly for Kindle books — is Amazon's fixed "Download it
    #    once and read it on your Kindle device..." sales pitch rather than a
    #    real synopsis.  Kept last among the "metadata tag" patterns (after
    #    the two JSON-LD/Apollo patterns which pull from structured book
    #    data) and always passed through both junk filters before acceptance.
    if len(desc) < 30:
        m = re.search(r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])[^>]+content=["\']((?:[^"\'\\]|\\.){30,})["\']',
                      raw, re.I)
        if m:
            candidate = re.sub(r'<[^>]+>', '', m.group(1))
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
                desc = candidate
            elif log and _is_junk_synopsis(candidate, _title_for_echo_check):
                if _looks_like_kindle_boilerplate(candidate):
                    reason = 'Kindle boilerplate'
                elif _looks_like_amazon_page_title(candidate):
                    reason = 'Amazon page-title text'
                else:
                    reason = 'title echo'
                log.debug('Amazon: rejected meta-description for %s — %s '
                         '(%r)', identifier, reason, candidate[:60])

    # 4. bookDescription_feature_div — grab full inner content, not just first </div>
    if len(desc) < 30:
        m = re.search(r'id=["\']bookDescription_feature_div["\'][^>]*>(.*?)(?=<div[^>]+id=|</section|</article|\Z)',
                      raw, re.S)
        if m:
            candidate = re.sub(r'<[^>]+>', '', m.group(1))
            candidate = re.sub(r'\\n', ' ', candidate)
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
                desc = candidate

    # 5. a-expander-content block (modern Amazon layout used on .es/.it/.fr)
    if len(desc) < 30:
        for m in re.finditer(r'class=["\'][^"\']* a-expander-content[^"\']* ["\'][^>]*>(.*?)</div>',
                             raw, re.S):
            candidate = re.sub(r'<[^>]+>', '', m.group(1))
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
                desc = candidate

    # 6. productDescription (legacy but still appears on marketplace pages)
    if len(desc) < 30:
        m = re.search(r'id=["\']productDescription["\'][^>]*>.*?<p>(.*?)</p>', raw, re.S)
        if m:
            candidate = re.sub(r'<[^>]+>', '', m.group(1))
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) > len(desc) and not _is_junk_synopsis(candidate, _title_for_echo_check):
                desc = candidate

    if len(desc) >= 30:
        # v6.2.27 bugfix: collapsible description blocks (bookDescription_
        # feature_div, a-expander-content) include their own "Read more" /
        # "Leggi di più" toggle-button INSIDE the div whose HTML we strip
        # tags from above -- the button's visible label survives as plain
        # text glued onto the end of the real synopsis (field-confirmed:
        # an Italian Amazon page's synopsis ended in "...Leggi di più").
        # Strip it before saving.
        _READMORE_TRAILING_RE = re.compile(
            r'\s*(?:\.{3}|…)?\s*(?:leggi\s+di\s+pi[uù]|read\s+more|show\s+more|'
            r'see\s+more|continue\s+reading|'
            r'leer\s+m[aá]s|ver\s+m[aá]s|mostrar\s+m[aá]s|'
            r'cite[sș]te\s+mai\s+mult|vezi\s+mai\s+mult|afl[aă]\s+mai\s+multe|'
            r'lire\s+la\s+suite|en\s+savoir\s+plus|'
            r'mehr\s+lesen|weiterlesen)\s*[»›》]?\s*$',
            re.I,
        )
        desc = _READMORE_TRAILING_RE.sub('', desc).rstrip()
        result['comments'] = desc

    cover_pats = [
        r'"hiRes"\s*:\s*"(https://[^"]+)"',
        r'"large"\s*:\s*"(https://[^"]+)"',
        r'"medium"\s*:\s*"(https://[^"]+)"',
        "src=[\"']([^\"']+)[\"'][^>]*id=[\"']landingImage[\"']",
        "<img[^>]+id=[\"']landingImage[\"'][^>]+src=[\"']([^\"']+)[\"']",
        "property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']",
    ]
    for pat in cover_pats:
        m = re.search(pat, raw)
        if m:
            result['cover_url'] = _upgrade_amazon_cover(m.group(1))
            break
    return result


# ── Kobo regional storefronts ──────────────────────────────────────────────────
#
# Kobo's storeapi.kobo.com endpoint is retired.  The working public interface
# is the storefront search at store.kobobooks.com/<locale>/Search, which serves
# JSON-LD and Open Graph tags on product pages.
#
# Regional mapping used by fetch_engine:
#   kobo_com  → en-US  (global / English)
#   kobo_es   → es-ES  (Spain / Latin America)
#   kobo_it   → it-IT
#   kobo_fr   → fr-FR
#   kobo_de   → de-DE
#
# Each provider is a thin wrapper around _fetch_kobo_storefront() with a
# different locale string so the UI/log can tell them apart.

_KOBO_LOCALE_HEADERS = {
    'en-US': 'en-US,en;q=0.9',
    'es-ES': 'es-ES,es;q=0.9',
    'it-IT': 'it-IT,it;q=0.9',
    'fr-FR': 'fr-FR,fr;q=0.9',
    'de-DE': 'de-DE,de;q=0.9',
}

_KOBO_LOCALE_TO_STORE_URL = {
    'en-US': 'https://www.kobo.com/en/search?query={q}',
    'es-ES': 'https://www.kobo.com/es/search?query={q}',
    'it-IT': 'https://www.kobo.com/it/search?query={q}',
    'fr-FR': 'https://www.kobo.com/fr/search?query={q}',
    'de-DE': 'https://www.kobo.com/de/search?query={q}',
}

_KOBO_LOCALE_TO_PRODUCT_BASE = {
    'en-US': 'https://www.kobo.com/en/ebook/',
    'es-ES': 'https://www.kobo.com/es/ebook/',
    'it-IT': 'https://www.kobo.com/it/ebook/',
    'fr-FR': 'https://www.kobo.com/fr/ebook/',
    'de-DE': 'https://www.kobo.com/de/ebook/',
}


def _fetch_kobo_storefront(title, author, isbn, asin, lang, locale, source_name,
                            timeout=20, retries=2, log=None):
    """
    Shared implementation for all Kobo regional providers.

    Strategy:
      1. Search the Kobo storefront search page for the title+author query.
      2. Extract the first ebook product link from the search results HTML.
      3. Fetch the product page and parse JSON-LD / og: tags.

    Kobo product pages always include JSON-LD @type:Book and og: meta tags
    which yield title, author, publisher, ISBN, description and cover.
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.9',
        'Accept-Language': _KOBO_LOCALE_HEADERS.get(locale, 'en-US,en;q=0.9'),
        'Referer': 'https://www.kobo.com/',
        'Cache-Control': 'no-cache',
    }

    q = isbn or '{} {}'.format(title or '', author or '').strip()
    if not q:
        return None

    search_url = _KOBO_LOCALE_TO_STORE_URL.get(
        locale, _KOBO_LOCALE_TO_STORE_URL['en-US']
    ).format(q=quote_plus(q))

    raw = _get(search_url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('%s: urllib blocked for search -- retrying via browser', source_name)
        raw = _browser_get(search_url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    # ── Find first ebook product link ─────────────────────────────────────────
    # Kobo search results contain links like /en/ebook/book-slug/xxxxxxxx
    product_path = None
    product_base = _KOBO_LOCALE_TO_PRODUCT_BASE.get(locale, '')
    locale_code = locale.split('-')[0].lower()  # 'en', 'es', 'it', etc.

    # Pattern: href="/en/ebook/..." or href="/es/ebook/..."
    m = re.search(
        r'href=["\']((https://www\.kobo\.com)?/' + re.escape(locale_code) +
        r'/ebook/[^"\'?\s]+)["\']',
        raw, re.I)
    if not m:
        # Fallback: any /ebook/ path
        m = re.search(r'href=["\']((https://www\.kobo\.com)?/[a-z]{2}/ebook/[^"\'?\s]+)["\']',
                      raw, re.I)
    if not m:
        if log:
            log.debug('%s: no product link found in search results', source_name)
        return None

    product_path = m.group(1)
    if product_path.startswith('/'):
        product_url = 'https://www.kobo.com' + product_path
    else:
        product_url = product_path
    # Strip any query string fragment
    product_url = product_url.split('?')[0]

    praw = _get(product_url, timeout, 1, headers=hdrs, log=log)
    if not praw and _browser_fallback_enabled():
        if log:
            log.info('%s: urllib blocked for product page -- retrying via browser', source_name)
        praw = _browser_get(product_url, headers=hdrs, timeout=timeout, log=log)
    if not praw:
        return None

    result = _parse_kobo_page(praw)
    if result:
        result['source'] = source_name
        result['language'] = locale_code
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_kobo_page(raw):
    """
    Parse a Kobo product page.  Tries JSON-LD first, then og: tags.
    Kobo inlines a complete JSON-LD @type:Book block on all ebook pages.
    """
    result = {}

    # ── JSON-LD @type:Book ────────────────────────────────────────────────────
    for m in re.finditer(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            raw, re.S | re.I):
        try:
            data = json.loads(m.group(1))
            if not isinstance(data, dict):
                continue
            btype = data.get('@type', '')
            if 'Book' not in btype and 'Product' not in btype:
                continue
            if data.get('name'):
                result['title'] = data['name']
            # Author
            authors_raw = data.get('author', [])
            if isinstance(authors_raw, dict):
                authors_raw = [authors_raw]
            if isinstance(authors_raw, list):
                result['authors'] = [
                    a.get('name', '') for a in authors_raw
                    if isinstance(a, dict) and a.get('name')
                ]
            # Publisher
            pub = data.get('publisher') or data.get('publishedBy')
            if pub:
                if isinstance(pub, dict):
                    pub = pub.get('name', '')
                result['publisher'] = str(pub).strip()
            # Date
            if data.get('datePublished'):
                result['pubdate'] = str(data['datePublished'])[:10]
            # Description
            if data.get('description'):
                result['comments'] = data['description']
            # Cover
            img = data.get('image') or data.get('thumbnailUrl')
            if img:
                result['cover_url'] = img[0] if isinstance(img, list) else img
            # ISBN
            isbn_val = data.get('isbn', '')
            if isbn_val:
                clean = re.sub(r'[-\s]', '', str(isbn_val))
                if len(clean) in (10, 13):
                    result.setdefault('identifiers', {})['isbn'] = clean
            if result.get('title'):
                return result
        except (ValueError, TypeError):
            continue

    # ── Open Graph fallback ───────────────────────────────────────────────────
    og = _parse_og_generic(raw)
    if og.get('title'):
        result.update(og)

    # ISBN from page
    if not result.get('identifiers', {}).get('isbn'):
        m = re.search(r'ISBN[-:\s]*([0-9]{13})', raw, re.I)
        if m:
            result.setdefault('identifiers', {})['isbn'] = m.group(1)

    return result if result.get('title') else {}


# ── Public per-region Kobo providers ──────────────────────────────────────────

def fetch_kobo_com(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """Kobo global (kobo.com, en-US) — ebooks in any language."""
    return _fetch_kobo_storefront(title, author, isbn, asin, lang, 'en-US',
                                  'Kobo', timeout, retries, log)

def fetch_kobo_es(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """Kobo Spain (kobo.com/es) — Spanish-language ebook catalogue."""
    return _fetch_kobo_storefront(title, author, isbn, asin, lang, 'es-ES',
                                  'Kobo (es)', timeout, retries, log)

def fetch_kobo_it(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """Kobo Italy (kobo.com/it) — Italian-language ebook catalogue."""
    return _fetch_kobo_storefront(title, author, isbn, asin, lang, 'it-IT',
                                  'Kobo (it)', timeout, retries, log)

def fetch_kobo_fr(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """Kobo France (kobo.com/fr) — French-language ebook catalogue."""
    return _fetch_kobo_storefront(title, author, isbn, asin, lang, 'fr-FR',
                                  'Kobo (fr)', timeout, retries, log)

def fetch_kobo_de(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """Kobo Germany (kobo.com/de) — German-language ebook catalogue."""
    return _fetch_kobo_storefront(title, author, isbn, asin, lang, 'de-DE',
                                  'Kobo (de)', timeout, retries, log)


# ── Open Library direct cover probe ───────────────────────────────────────────

def fetch_openlibrary_cover(isbn, timeout=10, log=None):
    """Direct Open Library cover lookup; returns URL only if image exists."""
    if not isbn:
        return ''
    url  = 'https://covers.openlibrary.org/b/isbn/{}-L.jpg?default=false'.format(isbn)
    size = _head_content_length(url, timeout=timeout, log=log)
    return url if size > 5000 else ''


# ══════════════════════════════════════════════════════════════════════════════
# NEW PROVIDERS — v6.2: language-specific storefronts
# ══════════════════════════════════════════════════════════════════════════════

# ── Casa del Libro (Spanish) ───────────────────────────────────────────────────

def fetch_casadellibro(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Casa del Libro — largest Spanish bookstore (casadellibro.com).
    Excellent coverage of Spanish-language titles including Latin American editions.
    Uses their public search API (JSON endpoint used by the website's autocomplete).
    Falls back to their standard search page if the API returns nothing.
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'application/json, text/html, */*',
        'Referer': 'https://www.casadellibro.com/',
        'Accept-Language': 'es-ES,es;q=0.9',
    }

    # ── 1. ISBN direct lookup ─────────────────────────────────────────────────
    if isbn:
        url = 'https://www.casadellibro.com/busqueda-por-isbn?isbn={}'.format(isbn)
        raw = _get(url, timeout, 1, headers=hdrs, log=log)
        if not raw and _browser_fallback_enabled():
            if log:
                log.info('Casa del Libro: urllib blocked for ISBN lookup -- retrying via browser')
            raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
        if raw:
            result = _parse_casadellibro_page(raw)
            if result:
                result['source'] = 'Casa del Libro'
                _inject_idents(result, isbn, asin)
                return result

    # ── 2. Title + author search ──────────────────────────────────────────────
    q = '{} {}'.format(title or '', author or '').strip()
    if not q:
        return None
    url = 'https://www.casadellibro.com/busqueda-generica?busqueda={}'.format(quote_plus(q))
    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('Casa del Libro: urllib blocked for search -- retrying via browser')
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    # Extract first product link from search results
    m = re.search(r'href="(/libro/[^"]+)"', raw)
    if not m:
        return None
    product_url = 'https://www.casadellibro.com' + m.group(1)
    praw = _get(product_url, timeout, 1, headers=hdrs, log=log)
    if not praw and _browser_fallback_enabled():
        if log:
            log.info('Casa del Libro: urllib blocked for product page -- retrying via browser')
        praw = _browser_get(product_url, headers=hdrs, timeout=timeout, log=log)
    if not praw:
        return None
    result = _parse_casadellibro_page(praw)
    if result:
        result['source'] = 'Casa del Libro'
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_casadellibro_page(raw):
    """Parse a Casa del Libro product page."""
    result = {}

    # Title from og:title or h1
    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', raw, re.I)
    if not m:
        m = re.search(r'<h1[^>]*class=["\'][^"\']*product[^"\']*["\'][^>]*>(.*?)</h1>', raw, re.S | re.I)
    if m:
        result['title'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    # Author
    m = re.search(r'itemprop=["\']author["\']\s*>?\s*<[^>]+>([^<]+)<', raw, re.I)
    if not m:
        m = re.search(r'"author"\s*:\s*"([^"]+)"', raw)
    if m:
        result['authors'] = [m.group(1).strip()]

    # ISBN
    m = re.search(r'ISBN[-:\s]*([0-9]{13})', raw, re.I)
    if m:
        result.setdefault('identifiers', {})['isbn'] = m.group(1)

    # Publisher
    m = re.search(r'(?:Editorial|Publisher)[^:]*:\s*<[^>]*>([^<]+)<', raw, re.I)
    if not m:
        m = re.search(r'"publisher"\s*:\s*"([^"]+)"', raw)
    if m:
        result['publisher'] = m.group(1).strip()

    # Publication year
    m = re.search(r'(?:Fecha de publicaci[oó]n|publicación)[^:]*:\s*(?:<[^>]*>)?(\d{4})', raw, re.I)
    if m:
        result['pubdate'] = m.group(1)

    # Synopsis — try JSON-LD first, then div#synopsis
    m = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.){{40,}})"', raw)
    if not m:
        m = re.search(r'<div[^>]+(?:id|class)=["\'][^"\']*sinopsis[^"\']*["\'][^>]*>(.*?)</div>',
                      raw, re.S | re.I)
    if m:
        desc = re.sub(r'<[^>]+>', '', m.group(1))
        desc = re.sub(r'\s+', ' ', desc).strip()
        if len(desc) > 30:
            result['comments'] = desc

    # Cover
    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](https?://[^"\']+)["\']', raw, re.I)
    if not m:
        m = re.search(r'<img[^>]+(?:id|class)=["\'][^"\']*(?:portada|cover)[^"\']*["\'][^>]+src=["\'](https?://[^"\']+)["\']', raw, re.I)
    if m:
        result['cover_url'] = m.group(1)

    result['language'] = 'es'
    return result if result.get('title') else {}


# ── FNAC España (Spanish) ──────────────────────────────────────────────────────

def fetch_fnac_es(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    FNAC Spain (fnac.es) — good coverage of Spanish and French titles sold in Spain.
    Uses the FNAC public search endpoint.

    v6.2.7: added Sec-Fetch-* and cache-control headers that reduce the 403
    rate on fnac.es; broadened product-link regex to handle the actual href
    patterns returned by the current FNAC search page layout.
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://www.fnac.es/',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1',
    }

    if isbn:
        url = 'https://www.fnac.es/SearchResult/ResultList.aspx?SCat=2&Search={}'.format(isbn)
    elif title or author:
        q = '{} {}'.format(title or '', author or '').strip()
        url = 'https://www.fnac.es/SearchResult/ResultList.aspx?SCat=2&Search={}'.format(quote_plus(q))
    else:
        return None

    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('FNAC: urllib blocked for search -- retrying via browser')
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    # Find first product link — FNAC uses various URL patterns:
    #   /Livre-... /Libro-... /a.../ /n.../ and full https:// forms
    product_url = None
    for pat in [
        r'href="(https://www\.fnac\.es/[^"]+(?:Livre|Libro|Book|libro|livre)[^"]*)"',
        r'href="(/[^"]+(?:Livre|Libro|Book|libro|livre)[^"]*)"',
        r'href="(https://www\.fnac\.es/a\d+/[^"]*)"',
        r'href="(/a\d+/[^"]*)"',
    ]:
        m = re.search(pat, raw, re.I)
        if m:
            path = m.group(1)
            product_url = path if path.startswith('http') else 'https://www.fnac.es' + path
            break

    if not product_url:
        if log:
            log.debug('FNAC: no product link found in search results page')
        return None

    praw = _get(product_url, timeout, 1, headers=hdrs, log=log)
    if not praw and _browser_fallback_enabled():
        if log:
            log.info('FNAC: urllib blocked for product page -- retrying via browser')
        praw = _browser_get(product_url, headers=hdrs, timeout=timeout, log=log)
    if not praw:
        return None

    result = _parse_fnac_page(praw)
    if result:
        result['source'] = 'FNAC'
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_fnac_page(raw):
    """Parse a FNAC product page (works for fnac.es and fnac.com)."""
    result = {}

    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', raw, re.I)
    if m:
        result['title'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    m = re.search(r'"author"\s*:\s*"([^"]+)"', raw)
    if not m:
        m = re.search(r'itemprop=["\']author["\'][^>]*>\s*<[^>]+>([^<]+)<', raw, re.I)
    if m:
        result['authors'] = [m.group(1).strip()]

    m = re.search(r'ISBN[-:\s]*([0-9]{13})', raw, re.I)
    if m:
        result.setdefault('identifiers', {})['isbn'] = m.group(1)

    m = re.search(r'"publisher"\s*:\s*"([^"]+)"', raw)
    if m:
        result['publisher'] = m.group(1).strip()

    m = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.){40,})"', raw)
    if m:
        desc = m.group(1).replace('\\n', ' ').replace('\\"', '"')
        desc = re.sub(r'\s+', ' ', desc).strip()
        if len(desc) > 30:
            result['comments'] = desc

    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](https?://[^"\']+)["\']', raw, re.I)
    if m:
        result['cover_url'] = m.group(1)

    return result if result.get('title') else {}


# ── Feltrinelli (Italian) ──────────────────────────────────────────────────────

def fetch_feltrinelli(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    LaFeltrinelli (lafeltrinelli.it) — largest Italian bookstore chain.
    Excellent metadata for Italian-language titles. Uses their search API
    which returns JSON (same endpoint used by the website's autocomplete).
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'application/json, text/html, */*',
        'Referer': 'https://www.lafeltrinelli.it/',
        'Accept-Language': 'it-IT,it;q=0.9',
    }

    # ── Autocomplete / search API ─────────────────────────────────────────────
    q = isbn or '{} {}'.format(title or '', author or '').strip()
    if not q:
        return None

    # Feltrinelli search
    search_url = 'https://www.lafeltrinelli.it/ricerca/libri?q={}'.format(quote_plus(q))
    raw = _get(search_url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('Feltrinelli: urllib blocked for search -- retrying via browser')
        raw = _browser_get(search_url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    # Extract first product link
    m = re.search(r'href="(/[^"]+(?:libro|ebook)[^"]*)"', raw, re.I)
    if not m:
        # Try JSON-LD embedded in page
        return _parse_feltrinelli_jsonld(raw, isbn, asin)

    product_url = 'https://www.lafeltrinelli.it' + m.group(1)
    praw = _get(product_url, timeout, 1, headers=hdrs, log=log)
    if not praw and _browser_fallback_enabled():
        if log:
            log.info('Feltrinelli: urllib blocked for product page -- retrying via browser')
        praw = _browser_get(product_url, headers=hdrs, timeout=timeout, log=log)
    if not praw:
        return _parse_feltrinelli_jsonld(raw, isbn, asin)

    result = _parse_feltrinelli_jsonld(praw, isbn, asin)
    if result:
        return result

    # Fallback: parse open-graph tags
    result = _parse_og_generic(praw)
    if result:
        result['source'] = 'Feltrinelli'
        result['language'] = 'it'
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_feltrinelli_jsonld(raw, isbn, asin):
    """Extract metadata from JSON-LD <script> blocks on Feltrinelli pages."""
    result = {}
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         raw, re.S | re.I):
        try:
            data = json.loads(m.group(1))
            if not isinstance(data, dict):
                continue
            btype = data.get('@type', '')
            if 'Book' not in btype and 'Product' not in btype:
                continue
            if data.get('name'):
                result['title'] = data['name']
            authors_raw = data.get('author', [])
            if isinstance(authors_raw, dict):
                authors_raw = [authors_raw]
            if isinstance(authors_raw, list):
                result['authors'] = [a.get('name', '') for a in authors_raw if isinstance(a, dict) and a.get('name')]
            if data.get('publisher'):
                pub = data['publisher']
                if isinstance(pub, dict):
                    pub = pub.get('name', '')
                result['publisher'] = str(pub)
            if data.get('datePublished'):
                result['pubdate'] = str(data['datePublished'])[:10]
            if data.get('description'):
                result['comments'] = data['description']
            if data.get('image'):
                img = data['image']
                result['cover_url'] = img[0] if isinstance(img, list) else img
            # ISBN
            isbn_val = data.get('isbn', '') or ''
            if isbn_val and len(re.sub(r'[-\s]', '', isbn_val)) in (10, 13):
                result.setdefault('identifiers', {})['isbn'] = re.sub(r'[-\s]', '', isbn_val)
            if result.get('title'):
                result['source'] = 'Feltrinelli'
                result['language'] = 'it'
                _inject_idents(result, isbn, asin)
                return result
        except (ValueError, TypeError):
            continue
    return {}


# ── Libraccio (Italian) ────────────────────────────────────────────────────────

def fetch_libraccio(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    Libraccio (libraccio.it) — major Italian book retailer (IBS group).
    Good coverage including second-hand and out-of-print Italian books.
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,*/*',
        'Referer': 'https://www.libraccio.it/',
        'Accept-Language': 'it-IT,it;q=0.9',
    }

    if isbn:
        url = 'https://www.libraccio.it/libro/{}.html'.format(isbn)
        raw = _get(url, timeout, 1, headers=hdrs, log=log)
        if not raw and _browser_fallback_enabled():
            if log:
                log.info('Libraccio: urllib blocked for ISBN lookup -- retrying via browser')
            raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
        if raw:
            result = _parse_ibs_page(raw)
            if result:
                result['source'] = 'Libraccio'
                result['language'] = 'it'
                _inject_idents(result, isbn, asin)
                return result

    q = '{} {}'.format(title or '', author or '').strip()
    if not q:
        return None
    url = 'https://www.libraccio.it/ricerca?q={}'.format(quote_plus(q))
    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('Libraccio: urllib blocked for search -- retrying via browser')
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    m = re.search(r'href="(/libro/[^"]+\.html)"', raw, re.I)
    if not m:
        return None
    product_url = 'https://www.libraccio.it' + m.group(1)
    praw = _get(product_url, timeout, 1, headers=hdrs, log=log)
    if not praw and _browser_fallback_enabled():
        if log:
            log.info('Libraccio: urllib blocked for product page -- retrying via browser')
        praw = _browser_get(product_url, headers=hdrs, timeout=timeout, log=log)
    if not praw:
        return None

    result = _parse_ibs_page(praw)
    if result:
        result['source'] = 'Libraccio'
        result['language'] = 'it'
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_ibs_page(raw):
    """Parse an IBS/Libraccio/Feltrinelli product page (shared HTML structure)."""
    result = {}

    # Try JSON-LD first (most reliable)
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         raw, re.S | re.I):
        try:
            data = json.loads(m.group(1))
            if not isinstance(data, dict):
                continue
            if 'Book' in data.get('@type', '') or 'Product' in data.get('@type', ''):
                if data.get('name'):
                    result['title'] = data['name']
                authors_raw = data.get('author', [])
                if isinstance(authors_raw, dict):
                    authors_raw = [authors_raw]
                if isinstance(authors_raw, list):
                    result['authors'] = [a.get('name', '') for a in authors_raw
                                         if isinstance(a, dict) and a.get('name')]
                if data.get('publisher'):
                    pub = data['publisher']
                    result['publisher'] = pub.get('name', str(pub)) if isinstance(pub, dict) else str(pub)
                if data.get('description'):
                    result['comments'] = data['description']
                if data.get('image'):
                    img = data['image']
                    result['cover_url'] = img[0] if isinstance(img, list) else img
                isbn_val = data.get('isbn', '')
                if isbn_val:
                    clean = re.sub(r'[-\s]', '', str(isbn_val))
                    if len(clean) in (10, 13):
                        result.setdefault('identifiers', {})['isbn'] = clean
                if result.get('title'):
                    return result
        except (ValueError, TypeError):
            continue

    # Fallback: OG tags
    og = _parse_og_generic(raw)
    if og.get('title'):
        result.update(og)

    return result if result.get('title') else {}


# ── BNF — Bibliothèque nationale de France (French) ───────────────────────────

def fetch_bnf(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    BNF (data.bnf.fr) — French national library open data API.
    Excellent authority source for French-language books. Uses their
    SRU (Search/Retrieve via URL) endpoint — open, no key required.
    """
    hdrs = {'User-Agent': UA, 'Accept': 'application/json, text/xml, */*'}

    # ── SRU query ─────────────────────────────────────────────────────────────
    if isbn:
        cql = 'bib.isbn = "{}"'.format(isbn)
    elif title and author:
        cql = 'bib.title all "{}" and bib.author all "{}"'.format(
            title.replace('"', ''), author.replace('"', ''))
    elif title:
        cql = 'bib.title all "{}"'.format(title.replace('"', ''))
    else:
        return None

    url = ('https://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve'
           '&recordSchema=unimarcxchange&maximumRecords=1&query={}'.format(quote_plus(cql)))

    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw:
        return None

    # Parse UNIMARC XML
    result = _parse_bnf_unimarc(raw)
    if result:
        result['source'] = 'BNF'
        result['language'] = result.get('language') or 'fr'
        _inject_idents(result, isbn, asin)
        return result
    return None


def _parse_bnf_unimarc(xml):
    """Extract metadata from BNF UNIMARC XML response."""
    result = {}
    if not xml or '<record' not in xml:
        return {}

    def _tag(field, sub):
        """Extract UNIMARC subfield value."""
        pat = (r'<datafield[^>]+tag=["\']' + re.escape(field) +
               r'["\'][^>]*>.*?<subfield[^>]+code=["\']' + re.escape(sub) +
               r'["\'][^>]*>(.*?)</subfield>')
        m = re.search(pat, xml, re.S | re.I)
        return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

    def _tags(field, sub):
        """Extract all UNIMARC subfield values for a given tag."""
        pat = (r'<datafield[^>]+tag=["\']' + re.escape(field) +
               r'["\'][^>]*>(.*?)</datafield>')
        vals = []
        for m in re.finditer(pat, xml, re.S | re.I):
            block = m.group(1)
            sm = re.search(r'<subfield[^>]+code=["\']' + re.escape(sub) + r'["\'][^>]*>(.*?)</subfield>',
                           block, re.S)
            if sm:
                vals.append(re.sub(r'<[^>]+>', '', sm.group(1)).strip())
        return vals

    # Title: field 200 subfield a
    title = _tag('200', 'a')
    subtitle = _tag('200', 'e')
    if title:
        result['title'] = (title + ': ' + subtitle).strip(': ') if subtitle else title

    # Author: field 700 subfield a + b
    authors = []
    for m in re.finditer(r'<datafield[^>]+tag=["\']700["\'][^>]*>(.*?)</datafield>', xml, re.S | re.I):
        block = m.group(1)
        a = re.search(r'<subfield[^>]+code=["\']a["\'][^>]*>(.*?)</subfield>', block, re.S)
        b = re.search(r'<subfield[^>]+code=["\']b["\'][^>]*>(.*?)</subfield>', block, re.S)
        name_parts = []
        if a: name_parts.append(re.sub(r'<[^>]+>', '', a.group(1)).strip().rstrip(','))
        if b: name_parts.append(re.sub(r'<[^>]+>', '', b.group(1)).strip())
        if name_parts:
            authors.append(' '.join(name_parts))
    # Also field 701 (joint author)
    for m in re.finditer(r'<datafield[^>]+tag=["\']701["\'][^>]*>(.*?)</datafield>', xml, re.S | re.I):
        block = m.group(1)
        a = re.search(r'<subfield[^>]+code=["\']a["\'][^>]*>(.*?)</subfield>', block, re.S)
        if a:
            authors.append(re.sub(r'<[^>]+>', '', a.group(1)).strip().rstrip(','))
    if authors:
        result['authors'] = authors

    # Publisher: field 210 subfield c, year: 210 d
    result['publisher'] = _tag('210', 'c')
    result['pubdate']   = _tag('210', 'd')

    # ISBN: field 010 subfield a
    isbn_raw = _tag('010', 'a')
    if isbn_raw:
        clean = re.sub(r'[-\s]', '', isbn_raw)
        if len(clean) in (10, 13):
            result.setdefault('identifiers', {})['isbn'] = clean

    # Language: field 101 subfield a
    result['language'] = _tag('101', 'a') or 'fre'

    # Tags: field 600-610 subfield a
    tags = _tags('606', 'a') + _tags('607', 'a')
    if tags:
        result['tags'] = tags[:15]

    return result if result.get('title') else {}


# ── BNE — Biblioteca Nacional de España (Spanish) ─────────────────────────────

def fetch_bne(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    BNE (bne.es) — Spanish National Library catalogue.
    Outstanding authority for Spanish-language books and Latin American editions.
    Open endpoint, no API key required.

    v6.2.7: switched primary endpoint from datos.bne.es/api/obras.json
    (decommissioned — returns 404) to the BNE SRU/MARCXML endpoint at
    catálogo.bne.es, with HTML fallback via the modern catalogue search URL.
    """
    hdrs = {'User-Agent': UA, 'Accept': 'application/xml, text/xml, text/html, */*',
            'Accept-Language': 'es-ES,es;q=0.9'}

    # ── BNE SRU/MARCXML endpoint ──────────────────────────────────────────────
    if isbn:
        cql = 'isbn="{}"'.format(isbn)
    elif title and author:
        cql = 'title="{}" and author="{}"'.format(
            title.replace('"', ''), author.replace('"', ''))
    elif title:
        cql = 'title="{}"'.format(title.replace('"', ''))
    else:
        return None

    sru_url = (
        'https://catalogo.bne.es/sru/sru?version=1.2&operation=searchRetrieve'
        '&recordSchema=marcxml&maximumRecords=1&query={}'.format(quote_plus(cql))
    )
    raw = _get(sru_url, timeout, retries, headers=hdrs, log=log)
    if raw and '<record' in raw:
        result = _parse_bne_marcxml(raw)
        if result:
            result['source'] = 'BNE'
            result['language'] = result.get('language') or 'es'
            _inject_idents(result, isbn, asin)
            return result

    # ── HTML catalogue fallback ───────────────────────────────────────────────
    return _fetch_bne_html(title, author, isbn, asin, timeout, hdrs, log)


def _parse_bne_marcxml(xml):
    """
    Extract metadata from BNE MARCXML SRU response.
    MARC 21 fields used:
      245 $a/$b — title / subtitle
      100/700 $a — author(s)
      264/260 $b/$c — publisher / date
      020 $a — ISBN
      041 $a — language code
      650/651 $a — subject headings
    """
    result = {}
    if not xml or '<record' not in xml:
        return {}

    def _sub(tag, code):
        pat = (r'<(?:marc:)?datafield[^>]+tag=["\']' + re.escape(tag) +
               r'["\'][^>]*>.*?<(?:marc:)?subfield[^>]+code=["\']' + re.escape(code) +
               r'["\'][^>]*>(.*?)</(?:marc:)?subfield>')
        m = re.search(pat, xml, re.S | re.I)
        return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

    def _subs(tag, code):
        pat = (r'<(?:marc:)?datafield[^>]+tag=["\']' + re.escape(tag) +
               r'["\'][^>]*>(.*?)</(?:marc:)?datafield>')
        vals = []
        for block_m in re.finditer(pat, xml, re.S | re.I):
            sm = re.search(
                r'<(?:marc:)?subfield[^>]+code=["\']' + re.escape(code) +
                r'["\'][^>]*>(.*?)</(?:marc:)?subfield>',
                block_m.group(1), re.S)
            if sm:
                vals.append(re.sub(r'<[^>]+>', '', sm.group(1)).strip())
        return vals

    title_a = _sub('245', 'a').rstrip(' /:')
    title_b = _sub('245', 'b').rstrip(' /:')
    if title_a:
        result['title'] = (title_a + ': ' + title_b).strip(': ') if title_b else title_a

    authors = []
    a100 = _sub('100', 'a').rstrip(',')
    if a100:
        authors.append(a100)
    for a700 in _subs('700', 'a'):
        authors.append(a700.rstrip(','))
    if authors:
        result['authors'] = authors

    pub = _sub('264', 'b') or _sub('260', 'b')
    if pub:
        result['publisher'] = pub.rstrip(',')
    date = _sub('264', 'c') or _sub('260', 'c')
    if date:
        result['pubdate'] = re.sub(r'[^\d]', '', date)[:4]

    isbn_raw = _sub('020', 'a')
    if isbn_raw:
        clean = re.sub(r'[-\s]', '', isbn_raw.split('(')[0])
        if len(clean) in (10, 13):
            result.setdefault('identifiers', {})['isbn'] = clean

    lang_raw = _sub('041', 'a')
    if lang_raw:
        result['language'] = lang_raw[:3]

    subjects = _subs('650', 'a') + _subs('651', 'a')
    if subjects:
        result['tags'] = subjects[:15]

    return result if result.get('title') else {}


def _fetch_bne_html(title, author, isbn, asin, timeout, hdrs, log):
    """Fallback: BNE catalogue HTML search (modern URL format)."""
    q = isbn or '{} {}'.format(title or '', author or '').strip()
    if not q:
        return None
    # Modern BNE catalogue search URL
    url = 'https://catalogo.bne.es/discovery/search?query=any,contains,{}&vid=34BNE_INST:34BNE&lang=es'.format(
        quote_plus(q))
    raw = _get(url, timeout, 1, headers=hdrs, log=log)
    if not raw:
        return None

    result = _parse_og_generic(raw)
    if result and result.get('title'):
        result['source'] = 'BNE'
        result['language'] = 'es'
        _inject_idents(result, isbn, asin)
        return result

    # Try extracting from MARC-style table in the HTML
    title_m = re.search(r'(?:Título|Title)[^<]*</[^>]+>\s*<[^>]+>([^<]+)', raw, re.I)
    if title_m:
        res = {'title': title_m.group(1).strip(), 'language': 'es', 'source': 'BNE'}
        author_m = re.search(r'(?:Autor|Author)[^<]*</[^>]+>\s*<[^>]+>([^<]+)', raw, re.I)
        if author_m:
            res['authors'] = [author_m.group(1).strip()]
        isbn_m = re.search(r'ISBN[^<]*</[^>]+>\s*<[^>]+>([0-9X-]{10,17})', raw, re.I)
        if isbn_m:
            clean = re.sub(r'[-\s]', '', isbn_m.group(1))
            if len(clean) in (10, 13):
                res.setdefault('identifiers', {})['isbn'] = clean
        _inject_idents(res, isbn, asin)
        return res
    return None


# ── SBN — Servizio Bibliotecario Nazionale (Italian) ──────────────────────────

def fetch_sbn(title, author, isbn, asin='', lang='', timeout=20, retries=2, log=None):
    """
    SBN (sbn.it) — Italian National Library Service.
    Best authority source for Italian ISBNs and bibliographic records.
    Uses the OPAC SBN SRU/JSON endpoint (open, no key required).
    """
    hdrs = {
        'User-Agent': UA,
        'Accept': 'application/json, text/xml, */*',
        'Accept-Language': 'it-IT,it;q=0.9',
    }

    # OPAC SBN has a REST/JSON gateway
    if isbn:
        url = 'https://opac.sbn.it/web/sbn/home?q=isbn:{}'.format(isbn)
    elif title:
        q = quote_plus('{} {}'.format(title, author or '').strip())
        url = 'https://opac.sbn.it/web/sbn/risultati-ricerca-avanzata?titolo={}'.format(
            quote_plus(title or ''))
        if author:
            url += '&autore={}'.format(quote_plus(author))
    else:
        return None

    raw = _get(url, timeout, retries, headers=hdrs, log=log)
    if not raw and _browser_fallback_enabled():
        if log:
            log.info('SBN: urllib blocked -- retrying via browser')
        raw = _browser_get(url, headers=hdrs, timeout=timeout, log=log)
    if not raw:
        return None

    # Try JSON-LD embedded in the page
    result = {}
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         raw, re.S | re.I):
        try:
            data = json.loads(m.group(1))
            if not isinstance(data, dict):
                continue
            if 'Book' in data.get('@type', '') or 'CreativeWork' in data.get('@type', ''):
                if data.get('name'):
                    result['title'] = data['name']
                    result['language'] = 'it'
                    result['source'] = 'SBN'
                    _inject_idents(result, isbn, asin)
                    return result
        except (ValueError, TypeError):
            continue

    # Fallback: parse HTML table
    title_m = re.search(r'(?:Titolo|Titolo uniforme)[^<]*</[^>]+>\s*<[^>]+>([^<]+)', raw, re.I)
    if not title_m:
        title_m = re.search(r'<h1[^>]*>([^<]{5,})</h1>', raw)
    if title_m:
        result = {
            'title':    title_m.group(1).strip(),
            'language': 'it',
            'source':   'SBN',
        }
        author_m = re.search(r'(?:Autore|Responsabilità)[^<]*</[^>]+>\s*<[^>]+>([^<]+)', raw, re.I)
        if author_m:
            result['authors'] = [author_m.group(1).strip()]
        pub_m = re.search(r'(?:Editore|Publisher)[^<]*</[^>]+>\s*<[^>]+>([^<]+)', raw, re.I)
        if pub_m:
            result['publisher'] = pub_m.group(1).strip()
        isbn_m = re.search(r'ISBN[^<]*</[^>]+>\s*<[^>]+>([0-9X-]{10,17})', raw, re.I)
        if isbn_m:
            clean = re.sub(r'[-\s]', '', isbn_m.group(1))
            if len(clean) in (10, 13):
                result.setdefault('identifiers', {})['isbn'] = clean
        _inject_idents(result, isbn, asin)
        return result
    return None


# ── Shared helpers for new providers ──────────────────────────────────────────

def _inject_idents(result, isbn, asin):
    """Ensure isbn and amazon identifiers are set when known."""
    if isbn:
        result.setdefault('identifiers', {}).setdefault('isbn', isbn)
    if asin:
        result.setdefault('identifiers', {}).setdefault('amazon', asin)


def _parse_og_generic(raw):
    """
    Generic Open Graph / JSON-LD parser for any book page.
    Returns a partial result dict (may be empty).
    """
    result = {}

    # og:title
    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', raw, re.I)
    if m:
        result['title'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    # og:description
    m = re.search(r'<meta\s+(?:property=["\']og:description["\']|name=["\']description["\'])\s+content=["\'](.*?)["\']',
                  raw, re.I)
    if m:
        desc = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if len(desc) > 30:
            result['comments'] = desc

    # og:image
    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](https?://[^"\']+)["\']', raw, re.I)
    if m:
        result['cover_url'] = m.group(1)

    # JSON-LD author / publisher
    m = re.search(r'"author"\s*:\s*(?:"([^"]+)"|\{"[^"]*"\s*:\s*"([^"]+)")', raw)
    if m:
        result['authors'] = [(m.group(1) or m.group(2)).strip()]

    m = re.search(r'"publisher"\s*:\s*(?:"([^"]+)"|\{"[^"]*"\s*:\s*"([^"]+)")', raw)
    if m:
        result['publisher'] = (m.group(1) or m.group(2)).strip()

    return result
