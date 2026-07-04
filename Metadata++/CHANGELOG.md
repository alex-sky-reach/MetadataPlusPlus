Metadata providers — v6.2.17
New in v6.2.17:
  - _parse_amazon_page synopsis extraction: fixed a THIRD class of junk
    synopsis, distinct from both v6.2.15's title-echo and v6.2.16's Kindle
    boilerplate. Some Amazon storefronts fall back to using the raw browser
    <title> tag content as the meta-description when neither a real
    synopsis nor the Kindle sales-pitch template is present:
        "Amazon.com: <Title> (<Edition>) eBook : <Author>: Tienda Kindle"
    Field-confirmed: ASIN B0H6JD9QXN "Todo lo que el agua calla" (Payá,
    Eugenio) produced "Amazon.com: Todo lo que el agua calla: Un thriller
    sobre lo que un pueblo eligió no saber (Spanish Edition) eBook : Payá,
    Eugenio: Tienda Kindle" -- 144 characters of page-title breadcrumb, not
    a synopsis. Added _looks_like_amazon_page_title(), which recognises
    this pattern via its fixed "Amazon.<tld>: ... : <store-section-label>"
    structure (Tienda Kindle / Libros / Kindle Store / Libri in altre
    lingue / Livres / Bücher / eBooks), combined into _is_junk_synopsis()
    alongside the existing title-echo and Kindle-boilerplate checks.
  - fetch_goodreads(): fixed a real bug where Goodreads SEARCH pages (not
    just book pages) were assumed to be immune to bot-blocking and fetched
    with plain urllib only. In practice a blocked/challenge search response
    contains zero /book/show/ links -- identical in shape to a genuine "no
    results" page -- so real books were being logged as "likely no match on
    Goodreads for this title" when the actual cause was urllib being
    blocked. Field-confirmed: "Todo lo que el agua calla" by Payá, Eugenio
    is a real, listed Goodreads title that nonetheless produced this false
    "no match" log line. New _goodreads_search_fetch() retries the same
    search URL through Playwright/Firefox whenever the urllib attempt
    yields no /book/show/ link, before concluding it's a genuine miss --
    mirroring the browser-first treatment _goodreads_fetch() already gives
    the book page itself, just applied one step earlier at the search step.
  - fetch_google(): added a minimum title-similarity floor to candidate
    selection. Previously max(candidates, key=_candidate_score) could
    return a book with NO real title relationship to the query, because
    _candidate_score also rewards description length and cover presence --
    a completely unrelated book with a long description could outscore the
    correct (but possibly synopsis-light) result. Field-confirmed: querying
    "Todo lo que el agua calla" returned 'El alcalde rojas' as Google's top
    pick (similarity score 18/100). fetch_engine._merge_results' downstream
    fuzzy-title filter did correctly discard this mismatch before it ever
    reached the user, so this was a silent inefficiency rather than a
    user-visible bug, but it wasted a request, polluted the log with a
    misleading "Got result from google: title='El alcalde rojas'" line,
    and was fragile against any future change to that downstream filter.
    The new floor compares both the raw title AND a subtitle-stripped
    version (matching exactly what _merge_results checks downstream,
    avoiding a regression where a correct match with a long Google subtitle
    -- raw similarity 40/100 -- would have been wrongly rejected by a naive
    un-stripped floor; the same match scores 100/100 once both sides are
    reduced to their pre-colon title). Candidates failing the floor are
    dropped before scoring even begins; if NO candidate from a given query
    clears it, that query's results are skipped entirely and the next,
    progressively looser query is tried instead of returning a confident-
    looking wrong book.

New in v6.2.16:
  - _parse_amazon_page synopsis extraction: fixed a SECOND, separate class of
    junk synopsis that v6.2.15's _looks_like_title_echo() did not catch.
    On Kindle product pages with no real "About this book" blurb, Amazon
    stamps a fixed marketing template into <meta name="description"> /
    og:description instead:
        "<Title> - Kindle edition by <Author>. Download it once and read
         it on your Kindle device, PC, phones or tablets. Use features
         like bookmarks, note taking and highlighting while reading
         <Title>."
    Field-confirmed: ASIN B0H1NMW17W "La Capa: Thriller Psicologico" (Caine,
    James) produced exactly this 277-character template as the saved
    Description. It slipped past the title-echo filter because most of its
    words (download, device, phones, tablets, bookmarks, note taking,
    highlighting) are NOT title words, so the word-overlap ratio that
    catches simple title-repeats stayed well under the 75% threshold.
    Fix: added _looks_like_kindle_boilerplate(), which recognises this
    fixed template directly via its characteristic English phrases plus
    Spanish/Italian/French storefront variants ("Descargue... lea en su
    dispositivo Kindle", "Scarica... leggi sul tuo dispositivo Kindle",
    "Téléchargez... lisez-le sur votre Kindle"). Applied alongside the
    title-echo check (now combined as _is_junk_synopsis()) across all 6
    synopsis-extraction patterns, not just the meta-description one.
  - fuzzy.py _SYNOPSIS_JUNK_PATTERNS: added the same Kindle-boilerplate
    phrases here too as defense-in-depth, so synopsis_quality() heavily
    penalises this text if it ever reaches the merge step via a different
    extraction path, rather than only catching it at the Amazon-provider
    source.

New in v6.2.15:
  - _parse_amazon_page synopsis extraction: fixed bug where, on pages with
    no real bookDescription block, the og:description / meta name=description
    tag was accepted as the synopsis even when it contained nothing but the
    page title (and often the author) repeated verbatim — e.g. "Votos
    Quebrados: Abandonada en el altar, embarazada y atrapada - Tess Mitchel"
    being saved as the book's "Description" field instead of a real blurb.
    Added _looks_like_title_echo() which compares every synopsis candidate
    (across all 6 extraction patterns, not just the meta-description one)
    against the already-extracted title and rejects it if the candidate is
    the title with only an author/edition suffix appended, is identical to
    the title after normalising punctuation, or has ≥75% word-overlap with
    the title while not being substantially longer. Real synopses (narrative
    prose, much longer than the title, mostly different vocabulary) pass
    through unaffected.
  - _clean_goodreads_description(): fixed a second, separate text-corruption
    bug. Goodreads' embedded page JSON uses standard JSON string escapes,
    including \uXXXX for curly quotes and accented characters (\u2019 for
    the apostrophe in "All'inizio", \u00e8/\u00e0/\u00f2 for accented
    Italian/Spanish/French vowels, etc.). The previous cleanup only
    hand-replaced \n, \r\n, \" and \' via .replace() and left every
    \uXXXX sequence as literal backslash-u text in the saved synopsis —
    e.g. "All\u2019inizio" instead of "All'inizio", or "Non mi
    permetter\u00e0" instead of "Non mi permetterà". This silently
    corrupted synopses for any language with accented characters or
    curly-quote punctuation, which is most non-English text.
    Fix: the captured JSON string value is now decoded with json.loads()
    (wrapped in quotes), which correctly resolves every JSON escape
    sequence in one safe pass. A manual \uXXXX-resolving fallback handles
    the rare case where the captured text isn't valid JSON on its own.
    fuzzy.synopsis_quality() already penalised leftover \uXXXX sequences
    as a "garbled scrape" signal (_UNESCAPED_ENTITY_RE) — that penalty
    was masking the bug's symptom without fixing its cause; the underlying
    extraction is now correct so accented-language synopses are no longer
    penalised or visibly broken.
  - Amazon and Goodreads were already browser-first via Playwright/Firefox
    (see _amazon_fetch / _goodreads_fetch in providers.py, both call
    browser_get() before any urllib fallback whenever
    browser_fetch.is_browser_available() is True) — confirmed working as
    intended and left unchanged in this release. Requires:
        1. pip install playwright   (into a SYSTEM Python, not Calibre's)
        2. playwright install firefox
    Once installed, every Amazon and Goodreads request automatically goes
    through a real Firefox browser with no further configuration needed.
  - Reverted the v6.2.15-draft "Search manually" button row (🔎 Amazon /
    🔎 Goodreads opening the system's default browser) added to
    BookResultPanel in dialogs.py — explicitly not wanted; removed
    cleanly along with its now-unused helper methods and imports.

New in v6.2.14 (Jadehawk Edits):
  - _amazon_fetch(): added one-time log.warning when urllib returns a bot-block
    page and the browser fallback is not active, directing the user to Options >
    Browser Fallback > "Check / Install Playwright".
  - browser_fetch.py _browser_get(): fixed Windows-incompatible '&&' in the
    "no playwright found" warning message -- now uses two separate numbered
    install instructions.
  - fetch_engine.py _run_browser_pass(): upgraded the "browser pass skipped"
    message from log.info to log.warning and added setup instructions.
  - config.py: new _PlaywrightSetupDialog and _InstallerThread for live-output
    playwright install wizard accessible via "Check / Install Playwright" button.
  - _page_is_audiobook(): removed the "soft signal" block (audible.com +
    acx.com links, 2+ required).  Amazon includes BOTH of these as footer
    navigation links on EVERY product page — Kindle ebooks, print books,
    toys, everything — so they have zero discriminating value as
    audiobook indicators.  Field-confirmed false positive: ASIN B0F344HDYN
    "Target Practice" (Kindle ebook by Ramsay Sinclair) was incorrectly
    detected as an audiobook because the page footer contained the standard
    audible.com and acx.com nav links, while all three reliable signals
    (productGroup JSON, binding JSON, Listening Length) were absent.
    The three remaining checks (strong JSON productGroup/binding and
    Listening Length) are sufficient to identify real Audible pages.
  - Removed dead _AUDIOBOOK_PAGE_SIGNALS compiled regex constant that was
    defined but never referenced.
  - _page_is_audiobook(): fixed false-positive on Kindle pages that carry a
    Whispersync for Voice cross-sell widget.  Such pages contain "audible.com",
    "Narrated by", "Whispersync", and "Listening Length" for the companion
    audiobook edition — all of which previously triggered the function to
    return True on a valid Kindle product page (confirmed with ASIN
    B09TN5CL12 "Drown the Sea: Dying Gods Book One").  Fix:
      1. Check "binding":"Kindle Edition" in the page's embedded JSON
         first — if present, return False immediately (the page is
         definitively NOT an audiobook regardless of upsell content).
      2. Removed "Whispersync" and "Narrated by/Narrator" from the
         soft-signal list — both appear verbatim in Kindle cross-sell
         widgets and are not reliable standalone audiobook indicators.
    True Audible product pages are still reliably caught by the two
    strong JSON signals ("productGroup":"audible" and "binding":"audible
    download") which continue to return True before the short-circuit fires.
  - _dump_amazon_debug_html(): new helper that writes raw HTML to calibre's
    config directory (metadata_plus_debug_amazon_<id>_<reason>.html) for
    offline inspection.  Called automatically when _page_is_audiobook()
    returns True (reason='audiobook') or when all 6 title-extraction
    patterns fail (reason='notitle'), so any future parser failure produces
    a concrete file to diff against a known-good page.