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

try:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode, quote_plus
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError # type: ignore
    from urllib import urlencode, quote_plus # type: ignore

from calibre_plugins.metadata_plus.core.fuzzy import similarity  # type: ignore

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
    """Return Content-Length in bytes via HEAD, or 0 on failure."""
    try:
        req = Request(url, headers={'User-Agent': UA})
        req.get_method = lambda: 'HEAD'
        resp = urlopen(req, timeout=timeout)
        cl = resp.headers.get('Content-Length', '0')
        return int(cl) if cl and str(cl).isdigit() else 0
    except Exception as e:
        if log:
            log.debug('HEAD failed %s: %s', url[:80], e)
        return 0


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
    """
    if not data or len(data) < 24:
        return (0, 0)
    import struct
    # PNG: magic 8 bytes, then IHDR chunk (4 len + 4 type + 4W + 4H)
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        try:
            w, h = struct.unpack('>II', data[16:24])
            return (w, h)
        except Exception:
            return (0, 0)
    # JPEG: scan for SOF0/SOF2 markers
    if data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xff:
                break
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):  # SOF0, SOF2
                try:
                    h, w = struct.unpack('>HH', data[i + 5:i + 9])
                    return (w, h)
                except Exception:
                    break
            try:
                seg_len = struct.unpack('>H', data[i + 2:i + 4])[0]
            except Exception:
                break
            i += 2 + seg_len
        return (0, 0)
    # WEBP: RIFF....WEBPVP8 / VP8L / VP8X
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        chunk = data[12:16]
        if chunk == b'VP8 ' and len(data) > 30:
            try:
                w = struct.unpack('<H', data[26:28])[0] & 0x3FFF
                h = struct.unpack('<H', data[28:30])[0] & 0x3FFF
                return (w + 1, h + 1)
            except Exception:
                return (0, 0)
        if chunk == b'VP8L' and len(data) > 25:
            try:
                bits = struct.unpack('<I', data[21:25])[0]
                w = (bits & 0x3FFF) + 1
                h = ((bits >> 14) & 0x3FFF) + 1
                return (w, h)
            except Exception:
                return (0, 0)
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
    on at least 2 of its 4 edges.
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
            _white_ratio(arr[:bw, :]),
            _white_ratio(arr[-bw:, :]),
            _white_ratio(arr[:, :bw]),
            _white_ratio(arr[:, -bw:]),
        ]
        padded_sides = sum(1 for r in sides if r >= min_ratio)
        return padded_sides >= 2
    except Exception:
        return False


def is_blank_or_placeholder_image(data, std_threshold=10.0, min_unique_colours=6):
    """
    Return True when a cover image is effectively blank / a placeholder.
    """
    try:
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

        buckets = (arr // 16).astype(_np.int32)
        flat = buckets.reshape(-1, 3)
        unique = len({tuple(row) for row in flat.tolist()})
        if unique < min_unique_colours:
            return True

        return False
    except Exception:
        return False


def cover_quality(data):
    """
    Return a quality tuple (pixels, file_bytes) for a raw cover image.
    pixels = width × height (0 if unreadable).
    Higher is better; compare as plain tuples (pixels first, then size).
    """
    if not data:
        return (0, 0)
    w, h = measure_image_bytes(data)
    return (w * h, len(data))


def best_cover(cover_candidates, min_size=200):
    """Return the highest-scoring non-audiobook cover URL (heuristic, no download)."""
    best_url, best_score = None, -1
    for url, weight in cover_candidates:
        s = score_cover(url)
        if s < 0:          # audiobook — skip entirely
            continue
        s += weight * 2
        if s > best_score:
            best_score, best_url = s, url
    return best_url


def probe_best_cover(cover_candidates, timeout=8, log=None):
    """
    Score all candidates, HEAD-probe the top 6 (excluding audiobook URLs),
    return the one with the largest actual file size. Falls back to the
    heuristic winner.
    """
    if not cover_candidates:
        return None

    # Filter audiobook URLs before scoring
    clean = [(url, w) for url, w in cover_candidates
             if url and score_cover(url) >= 0]
    if not clean:
        return None

    scored = sorted(
        [(score_cover(url) + w * 2, url) for url, w in clean],
        reverse=True
    )
    if not scored:
        return None

    import threading
    top = [u for _, u in scored[:6]]
    sizes = {}
    lock = threading.Lock()

    def probe(u):
        cl = _head_content_length(u, timeout=timeout, log=log)
        with lock:
            sizes[u] = cl

    threads = [threading.Thread(target=probe, args=(u,), daemon=True) for u in top]
    for t in threads: t.start()
    for t in threads: t.join(timeout=timeout + 1)

    probed = [(sizes.get(u, 0), u) for u in top if sizes.get(u, 0) > 2000]
    if probed:
        return max(probed, key=lambda x: x[0])[1]
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
    Never restricts by language.

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

    for q in queries:
        if not q:
            continue
        url = ('https://www.googleapis.com/books/v1/volumes'
               '?q={}&maxResults=10&printType=books'.format(q))
        if api_key:
            url += '&key={}'.format(quote_plus(api_key))
        data = _jget(url, timeout, retries, log)
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
        if volume_id:
            cover_alts.append(
                'https://books.google.com/books/content?id={}'
                '&printsec=frontcover&img=1&zoom=1&source=gbs_api'.format(volume_id))
            cover_alts.append(
                'https://books.google.com/books/content?id={}'
                '&printsec=frontcover&img=1&zoom=2&source=gbs_api'.format(volume_id))
            cover_alts.append(
                'https://books.google.com/books/content?id={}'
                '&printsec=frontcover&img=1&zoom=6&source=gbs_api'.format(volume_id))
        if raw:
            clean = re.sub(r'[&?]zoom=\d', '', raw)
            clean = re.sub(r'[&?]edge=\w+', '', clean).rstrip('&?')
            cover_alts.append(clean + ('&' if '?' in clean else '?') + 'zoom=6&fife=w1200')
            cover_alts.append(clean + ('&' if '?' in clean else '?') + 'zoom=3')

        cover_url = cover_alts[0] if cover_alts else raw
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

            return {
                'title':       doc.get('title', ''),
                'authors':     doc.get('author_name', []),
                'publisher':   ', '.join(doc.get('publisher', [])[:1]),
                'pubdate':     str(doc.get('first_publish_year', '')),
                'comments':    comments,
                'tags':        doc.get('subject', [])[:15],
                'language':    (doc.get('language', [''])[0] if doc.get('language') else ''),
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
        best_desc = _clean_goodreads_description(og['comments'])
    if best_desc and len(best_desc) >= 20:
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

    return {
        'title':       doc.get('title', ''),
        'authors':     creators,
        'publisher':   doc.get('publisher', ''),
        'pubdate':     str(doc.get('date', '')),
        'comments':    comments,
        'tags':        subjects[:15],
        'language':    doc.get('language', ''),
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
        # Also try the local TLD if .com fails (e.g. some regional Kindle titles)
        if not result and local_tld != 'amazon.com':
            url2 = 'https://www.{}/dp/{}'.format(local_tld, asin)
            if log:
                log.info('Amazon: trying %s dp/ for ASIN %s', local_tld, asin)
            raw2 = _amazon_fetch(url2, timeout, 1, hdrs, log)
            if raw2:
                result = _parse_amazon_page(raw2, asin, log=log)
                if result and log:
                    log.info('Amazon: got result via %s dp/ %s', local_tld, asin)
                elif log:
                    log.debug('Amazon: %s dp/ page for ASIN %s parsed but no '
                              'usable title found', local_tld, asin)

    # ── 2. Direct dp/ lookup by ISBN ─────────────────────────────────────────
    if not result and isbn:
        if log:
            log.info('Amazon: trying dp/ lookup for ISBN %s', isbn)
        url = 'https://www.amazon.com/dp/{}'.format(isbn)
        raw = _amazon_fetch(url, timeout, retries, hdrs, log)
        if raw:
            result = _parse_amazon_page(raw, isbn, log=log)
            if result and log:
                log.info('Amazon: got result via ISBN dp/ %s', isbn)
            elif log:
                log.debug('Amazon: dp/ page for ISBN %s parsed but no usable '
                          'title found', isbn)
        # Also try local TLD — regional ISBNs often resolve better there
        if not result and local_tld != 'amazon.com':
            url2 = 'https://www.{}/dp/{}'.format(local_tld, isbn)
            if log:
                log.info('Amazon: trying %s dp/ for ISBN %s', local_tld, isbn)
            raw2 = _amazon_fetch(url2, timeout, 1, hdrs, log)
            if raw2:
                result = _parse_amazon_page(raw2, isbn, log=log)
                if result and log:
                    log.info('Amazon: got result via %s dp/ %s', local_tld, isbn)
                elif log:
                    log.debug('Amazon: %s dp/ page for ISBN %s parsed but no '
                              'usable title found', local_tld, isbn)

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
    if not result and (title or author) and not _skip_search:
        if log and _skip_search is False and _direct_only:
            log.debug('Amazon: direct-only mode — skipping title search (ASIN/ISBN known)')
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

                for found_id in candidates:
                    if log:
                        log.info('Amazon: search candidate %s, fetching dp/ page', found_id)
                    purl = 'https://www.{}/dp/{}'.format(local_tld, found_id)
                    praw = _amazon_fetch(purl, timeout, 1, hdrs, log)
                    if praw:
                        candidate_result = _parse_amazon_page(praw, found_id, log=log)
                        if candidate_result and candidate_result.get('title'):
                            result = candidate_result
                            break
                        elif log:
                            log.debug('Amazon: dp/ page for candidate %s was real '
                                      'HTML but no title could be parsed from it '
                                      '— trying next candidate', found_id)
                    elif log:
                        log.debug('Amazon: dp/ fetch for candidate %s returned '
                                  'no content (timeout/network error) — trying '
                                  'next candidate', found_id)

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
    _AMAZON_PAGE_TITLE_RE = re.compile(
        r'^\s*amazon\.(?:com|es|it|fr|de|co\.uk|co\.jp|com\.br|nl|pl|se|com\.tr|ae|in|cn|ca|com\.mx)\s*:'
        r'.*:\s*(?:tienda kindle|kindle store|libros|libri(?: in altre lingue)?|'
        r'ebooks?|livres|b[üu]cher|boutique kindle|ebook kindle)\s*$',
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
