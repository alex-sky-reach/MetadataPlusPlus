Calibre API compatibility & provider crash resilience — v6.2.36
New in v6.2.36:
  - BUG FIX: Guard against TypeError when normalizing publisher, language, and
    publication date from Open Library and Internet Archive responses that return
    lists/sequences instead of plain strings.
  - BUG FIX: Handle Calibre Cache.get_metadata() / cover() API differences
    gracefully to avoid TypeError: get_metadata() got an unexpected keyword
    argument 'index_is_id'.
  - BUG FIX: Prevent crash/segfault on dialog closure or cancellation by
    properly terminating background fetch workers and disconnecting Qt signals
    in reject() and closeEvent().
  - BUG FIX: Detect invalid Gemini/AI Studio API keys passed to Google Books
    API and fall back cleanly to keyless requests instead of raising HTTP 401.
  - BUG FIX: Resolve undefined variable and missing import (_target_lang and
    normalize_language) in Open Library provider fetch.

Firefox worker cleanup after metadata runs — v6.2.35
New in v6.2.35:
  - BUG FIX: Close the reusable Playwright/Firefox worker when a metadata
    fetch run finishes or is canceled, instead of leaving the visible Firefox
    window open until Calibre/plugin shutdown. The worker is still reused
    during a multi-book run; it is only closed at the run boundary.

Single-window Firefox worker (merged) — v6.2.34
New in v6.2.34:
  - MERGE: Firefox browser integration now reuses a single persistent
    browser window across every browser_get() call instead of launching a
    brand-new Firefox subprocess (and a brand-new visible window) for every
    fetch. Previously, each browser_get() call spawned Firefox from
    scratch, paying a ~3-5s launch cost EVERY time and leaving one visible
    window per URL fetched during a session -- confusing when several
    sources (Amazon, Goodreads, a search retry, etc.) all needed the
    browser fallback for the same book. browser_fetch.py now starts one
    long-lived worker subprocess on first use that keeps a single Firefox
    browser/context/page alive for the life of the calibre/plugin process,
    and talks to it over a simple line-based JSON stdin/stdout protocol
    for every subsequent fetch. If a fetch hits a hard navigation failure,
    only the context/page inside the existing worker is recreated -- never
    a second Firefox process or window.
  - This single-window worker architecture was carried over from the
    separately-shipped v6.2.14-based attached build, which added it first.
    On merge, it was combined with this branch's v6.2.33 networkidle
    root-cause fix (two-stage domcontentloaded + short best-effort
    networkidle wait) rather than the older single-stage
    wait_until="networkidle" navigation the v6.2.14 build still used for
    its worker's page.goto() call -- the older single-stage form would
    have reintroduced the exact "entire page discarded on networkidle
    timeout" bug that v6.2.33 fixed, just inside the new persistent
    worker instead of the old per-call subprocess. The merged worker gets
    both fixes: one reused window, and navigation that doesn't throw away
    a fully-loaded page just because Amazon's background telemetry never
    goes fully quiet.
  - No behaviour change to is_browser_available(), browser_get()'s public
    signature, or any caller in providers.py -- this is a drop-in
    replacement of the browser_fetch.py internals only.

Networkidle timeout root-cause fix — v6.2.33
New in v6.2.33:
  - ROOT-CAUSE FIX for a recurring failure pattern seen throughout many
    earlier reports in this log ("Page.goto: Timeout 30000ms exceeded...
    waiting until networkidle" on amazon.it/.es dp/ and search pages):
    page.goto(url, wait_until="networkidle") RAISES an exception --
    discarding the entire already-loaded page, zero content captured --
    whenever a site never goes fully network-silent within the timeout.
    Amazon product/search pages routinely never satisfy "networkidle" even
    with this plugin's own third-party ad/analytics blocklist in place,
    because Amazon's own same-origin telemetry, personalization widgets,
    and live-pricing XHRs keep firing indefinitely in the background --
    while the actual page content (title, description, cover) is almost
    always fully rendered within 2-3 seconds. So a real, usable page was
    being thrown away purely because it never went completely quiet.
  - Fixed with a two-stage navigation: goto() now only waits for
    "domcontentloaded" (fast, reliable -- content is present by then), then
    makes a short SEPARATE best-effort attempt at "networkidle" (8s, for
    Cloudflare/bot-challenge JS redirects that do need it) which is now
    allowed to time out harmlessly instead of aborting the whole fetch.
    This should reduce a meaningful fraction of the "browser_fetch:
    subprocess failed... Timeout 30000ms exceeded" warnings seen across
    Amazon dp/ and search fetches in earlier reports in this conversation.


New in v6.2.32:
  - Added a title-plausibility check to Amazon's search-candidate loop —
    it validated LANGUAGE (v6.2.26) but never validated that a candidate
    is even the same BOOK. Field-confirmed: a search for a self-published
    Spanish title with no real amazon.com listing surfaced a Prime Video
    show ("Ver The Other End of the Rope") as its data-asin candidate —
    real HTML, a real title, accepted as if it were "the result". calibre
    never actually got this wrong data (fetch_engine's own title-similarity
    check at merge time silently dropped it), but it wasted a full page
    fetch and logged a misleading "Got result from amazon" line, and could
    have blocked trying further candidates if it had matched the target
    language too.
  - A bare similarity() cutoff is NOT safe for this check: similarity()
    penalizes length differences heavily, so calibre's short title vs
    Amazon's "Title: Full Subtitle" scored LOWER (15) than the genuinely
    unrelated book/movie pair (12) in testing — too close for any single
    number to separate reliably. Added _title_plausible_match(): tries
    substring-containment first (handles the very common short-title-vs-
    full-title-with-subtitle case cleanly), falling back to a lenient
    similarity floor only for everything else.
  - On the specific book in this report ("Las hechiceras de Madrid Las
    Tres Amigas"): even with this fix, it will likely still come back
    empty — amazon.es was bot-blocked (503), the only amazon.com search
    candidate was the unrelated Prime Video result now correctly rejected,
    and neither Goodreads nor Google Books had any match at all for this
    exact title/author. This looks like a genuine "not indexed by any of
    these three sources" case rather than a bug — self-published or very
    small-press titles are sometimes simply absent from all three. Worth
    trying: search Google Books / Goodreads directly by hand to confirm
    whether the title is indexed there under slightly different
    punctuation (e.g. "Las hechiceras de Madrid: Las Tres Amigas" with a
    colon), since a missing separator between title and subtitle can hurt
    search matching on some sources.


New in v6.2.31:
  - ROOT-CAUSE FIX for "Amazon has a great synopsis on the actual site but
    the plugin doesn't fetch it, even though Amazon now shows up in
    sources": the ISBN/ASIN dp/ lookup tries amazon.com first (product
    pages are normally global), and as soon as THAT returned any usable
    title, every fallback attempt at the local TLD was skipped entirely —
    permanently, for the whole fetch. Kindle ebooks are commonly exclusive
    to one regional storefront (field-confirmed: this book's Kindle
    edition is sold on amazon.es; amazon.com showed a bare cross-market
    listing with a title but no "Descripción del producto" section at
    all). So the plugin recorded "got a result from Amazon" and stopped
    looking, while the actual synopsis sat one TLD away the whole time.
    Both the ISBN and ASIN dp/ lookup paths now also try the local TLD
    whenever the .com result is missing a description, and a local result
    that HAS one replaces the bare .com one rather than being discarded
    just because .com "succeeded" first.
  - This also directly addresses "why can't I choose between Amazon's and
    Google's synopsis" — the Choose Description picker already lists every
    non-junk candidate found (that mechanism was working correctly); the
    real gap was that Amazon's real description was never being collected
    in the first place for region-exclusive Kindle listings. With that
    fixed, if Amazon (and/or Google Books) has real content, it will show
    up as a selectable option alongside anything else found.


New in v6.2.30:
  - Clarification, not a bug: when every available source genuinely has no
    real synopsis for a book (field case: Goodreads' only "description"
    JSON field on the page belonged to a "Buy new" marketplace/ad widget,
    not the book itself — Goodreads simply doesn't have a real synopsis on
    file for this title), the v6.2.28 hard-junk-veto correctly refuses to
    save that ad snippet as if it were the synopsis. This is working as
    intended: no synopsis beats a fake one. The fix needed here is getting
    a source that DOES have a real synopsis (Amazon) to actually respond.
  - ROOT-CAUSE FIX: when Amazon's title-search on the local TLD (e.g.
    amazon.es) failed outright — Playwright networkidle timeout followed
    by an HTTP 503 bot-block, both seen in field logs — the existing
    "fall back to .com" logic only ever helped a LATER book in the same
    session avoid retrying a TLD already known to be in cooldown; it did
    nothing for the book that had just failed, since the cooldown record
    is only written AFTER the failure. Now a local-TLD search that
    produces no content at all is immediately retried once on amazon.com
    within the SAME call, giving that book's Amazon search a real second
    chance instead of silently giving up until the next book's fetch.
  - Reminder: this run also auto-discovered and saved the book's ISBN from
    Google Books. The NEXT fetch for this book will use the ISBN-based
    dp/ lookup (fixed in v6.2.29 to use the correct ISBN-10 form) instead
    of the search path — dp/ product pages tend to be less aggressively
    gated by Amazon's anti-bot system than the search endpoint, so
    re-running the fetch now that the ISBN is saved has a good chance of
    getting through even without today's retry fix.


New in v6.2.29:
  - ROOT-CAUSE FIX for "Amazon has a good synopsis on the actual site but
    the plugin never fetches it": Amazon's dp/<id> product-page path takes
    an ASIN or an ISBN-10 — it does NOT resolve 13-digit ISBNs. Every book
    known only by its ISBN-13 (the normal case — that's what's stored in
    calibre) hit a real-but-useless Amazon "notitle" page on both dp/
    attempts (amazon.com and the local TLD), field-confirmed for a book
    that has a perfectly normal product page under its ISBN-10 form. Now
    the ISBN-13 is converted to ISBN-10 (isbn_utils.isbn13_to_10) and tried
    FIRST in the dp/ URL, with the original string kept as a second
    attempt for identifiers that are already ISBN-10 or Kindle-only
    listings that happen to accept the 13-digit form.
  - Compounding that: "Amazon: direct lookup only" (Options > Browser
    Fallback, ON by default) skips the title-search fallback whenever an
    ASIN/ISBN is merely KNOWN — regardless of whether the direct dp/
    lookup actually found anything. So when the (now-fixed) ISBN-13 bug
    made dp/ fail, Amazon contributed nothing at all, silently: the
    fallback that would have found the book via search was never tried,
    and the one log line meant to explain why had an inverted/dead
    condition that could never actually fire in that situation. Amazon
    now logs a clear WARNING — naming the exact Options setting responsible
    — whenever direct lookup fails and direct-only mode is the reason
    search wasn't tried, so this is visible in the log instead of a silent
    "Amazon just isn't in the sources list" mystery.


New in v6.2.28:
  - ROOT-CAUSE FIX (round 2) for "image not available" covers: it turns out
    Google's own volumeInfo.imageLinks can point at a thumbnail URL that,
    when actually fetched, serves Google's generic placeholder anyway (the
    API metadata itself is stale for that volume) — so "does imageLinks
    exist" (the v6.2.27 fix) was necessary but not sufficient, and the
    pixel-statistics heuristics in is_blank_or_placeholder_image() don't
    reliably catch this specific graphic either. Added a reference-hash
    detector (is_google_placeholder_cover()): fetch Google's placeholder
    ONCE per session using a deliberately-bogus volume ID, hash it, and
    compare every books.google.com cover download against that hash before
    trusting it. Self-updating if Google ever changes the graphic, zero
    false-positive risk against real covers.
  - probe_best_cover() (the backend function that produces "Best probed
    cover" and the default pre-selected cover before you even open Choose
    Cover) used to be a cheap HEAD-only Content-Length probe with NO
    content awareness — it could not tell a real cover from a same-sized
    placeholder. It now fully downloads and content-validates (via
    is_blank_or_placeholder_image, same check the Cover Chooser dialog
    uses) the top-scoring candidates and returns the first one that's
    actually real, instead of just the largest by reported size.
  - MetadataCache gained a schema version baked into every cache key. This
    plugin caches merged fetch results (default 7-day TTL) — without a
    version bump, upgrading the plugin does NOT invalidate previously-
    cached results, so a book fetched before a fix kept serving the OLD
    (buggy) cached cover/synopsis for up to cache_days even with the new,
    fixed code installed. This is very likely why earlier fixes appeared
    "not to work" on books that had been fetched before. Bump
    CACHE_SCHEMA_VERSION in cache.py on any future change that alters what
    a cached result should contain.
  - ROOT-CAUSE FIX for junk synopses (e.g. a 25-character "Brand New. Ship
    worldwide." marketplace/seller-listing snippet applied as if it were
    the book's synopsis): the merge step always accepted whichever
    candidate scored highest, even when EVERY candidate was garbage. Added
    marketplace-listing boilerplate patterns (brand new, ship worldwide,
    condition: new/used, money-back guarantee, etc.) to the shared junk
    detector, AND a hard floor at merge time — too short (<40 chars), too
    low quality, or a confirmed junk-pattern match now means NO synopsis is
    set at all (from auto-selection or the manual picker) rather than
    saving visible junk. No synopsis beats a fake one.
  - Full config-dialog translation: every group box title, field label,
    checkbox, and button across the Sources, Weights, Options, and
    Diagnostics tabs (plus the Playwright setup dialog) now follows
    Interface Language — previously only a handful of Options-tab items
    were translated. Long technical/status annotations describing specific
    source behaviour (e.g. "[experimental — currently blocked]" notes)
    remain in English by design, same rationale as log output.
  - Note: the outer dialog CHROME title ("Customize plugin: Metadata++" /
    "Personalizza Metadata++" / etc.) is calibre's own wrapper around the
    plugin's config screen and follows calibre's OWN interface language
    setting, not this plugin's Interface Language pref — that title is not
    something a plugin's config widget can override.
  - Choose Cover dialog now offers the book's CURRENT calibre cover as a
    selectable candidate (labelled "Current cover (in calibre)"), so
    keeping the existing cover is one click away instead of requiring the
    Cover checkbox to be unchecked entirely.


New in v6.2.27:
  - ROOT-CAUSE FIX for "image not available" placeholder graphics reaching
    the final cover choice: fetch_google always built 3 speculative
    books.google.com/books/content?id=...&printsec=frontcover URLs for
    EVERY candidate with a volume_id, regardless of whether Google's own
    volumeInfo.imageLinks said a cover actually exists for that volume.
    Those URLs don't 404 for a coverless volume -- they return Google's
    real, valid, non-tiny "image not available" placeholder JPEG, which
    passed every existing size/HEAD-probe check and got auto-picked as
    "best" cover (field-confirmed: .../content?id=t5Ke0QEACAAJ...). They
    were also listed BEFORE the confirmed-real imageLinks thumbnail URL, so
    even when a real cover DID exist, the speculative guess could still be
    tried first. Fixed: a books.google.com id-based URL is now only ever
    offered as a last-resort extra alongside a CONFIRMED real thumbnail
    (imageLinks non-empty), and always listed after it. If imageLinks is
    empty, no Google cover is offered for that candidate at all.
  - is_blank_or_placeholder_image() gained a third detection signal
    (bytes-per-pixel compression efficiency) as defense-in-depth: Google's
    "image not available" tile has just enough anti-aliased text to defeat
    the existing std-dev/unique-colour checks, but — like any simple flat-
    graphic-plus-text placeholder — it compresses far more efficiently than
    real photographed/illustrated cover art at the same resolution.
  - CoverChooserDialog now HIDES any candidate tile that downloads as a
    confirmed blank/placeholder instead of just captioning it "⚠ blank"
    underneath a full-size "image not available" thumbnail (easy to miss,
    and defeats the purpose of a "choose the best one" dialog). If the
    hidden tile was the pre-selected default, selection falls through to
    the first remaining visible tile.
  - Fixed a synopsis-truncation-looking bug: Amazon's collapsible
    description blocks (bookDescription_feature_div, a-expander-content)
    include their own "Read more" / "Leggi di più" toggle button INSIDE the
    div whose HTML gets tag-stripped — the button's own visible label
    survived as plain text glued onto the end of the real synopsis
    (field-confirmed: an Italian Amazon page's saved synopsis ended in
    "...Leggi di più"). Now stripped for it/en/es/ro/fr/de before saving.
  - Translated the main toolbar dropdown menu (Fetch Metadata (All
    Sources), Detect Duplicates in Selection, Repair/Validate ISBNs, Clear
    Metadata Cache, Configure Metadata++…) and its result/error dialogs
    into the same 4 interface languages (en/it/es/ro). InterfaceAction now
    implements apply_settings() to re-text the menu immediately after the
    user changes Interface language in Options, without needing to
    restart calibre.


New in v6.2.26:
  - ROOT-CAUSE FIX for "Spanish cover/synopsis chosen for an Italian book":
    fetch_google's candidate scoring had zero language awareness -- Google
    Books often indexes several editions of the same title under one query
    (it/es/en all match "intitle:Tecnofascismo"), and the old score (title
    similarity + description length + cover presence) simply picked
    whichever edition had the richest-looking description, regardless of
    language. A same-language candidate now gets a +600 scoring bonus (a
    confirmed mismatch gets -400), large enough to override the
    description-length/cover delta.
  - ROOT-CAUSE FIX for the same bug on Amazon: fetch_amazon's search
    fallback accepted the FIRST search candidate that parsed a title, with
    no language check at all -- every Amazon storefront (including
    amazon.it) stocks editions in multiple languages, so a Spanish Kindle
    edition could win outright just for appearing first in the results.
    _parse_amazon_page now extracts the edition's language (from the
    "(Spanish Edition)"/"(edizione italiana)" marker and/or the page's
    Language/Idioma/Lingua product-details row) and the search loop now
    tries candidates in order looking for a language match, only falling
    back to a wrong-language result if nothing better turns up among the
    (up to 5) candidates tried.
  - Fixed a related Amazon junk-description bug: the page's own <title>-tag
    breadcrumb ("<Title> ... (Spanish Edition) eBook : <Author>: Amazon.it:
    Kindle Store") was being saved as if it were a real synopsis whenever
    the title-first ordering put "Amazon.<tld>: <section>" at the END of
    the string instead of the start -- the existing junk-title detector only
    matched the start-anchored ordering. Both orderings are now caught.
  - fetch_engine._merge_results: widened the synopsis language bonus/penalty
    from +20/-15 to +60/-60 so a same-language synopsis always outranks a
    wrong-language one regardless of source weight/quality, and the manual
    "Choose Description…" picker now drops wrong-language candidates
    entirely whenever at least one same-language candidate was found
    (previously every wrong-language synopsis from every source stayed in
    the picker forever). Cover candidates are now tagged with their source
    result's language too and filtered the same way.
  - NEW: i18n.py adds a small interface-translation layer (English,
    Italiano, Español, Română) covering the Fetch/Results dialog, the
    Choose Cover and Choose Description pickers, and the Options screen.
    Selectable via Options > Interface > Interface language. Log output is
    intentionally left in English always, so it can still be pasted
    directly into bug reports. (Not yet covering the Duplicate Detection
    dialog or per-source config labels in the Sources/Weights tabs.)


New in v6.2.25:
  - ROOT-CAUSE FIX for "padded/wrong cover chosen over a clearly better one"
    (still reproducing on top of v6.2.22-24's padding-aware comparison):
    fetch_engine._merge_results() collected cover_url + cover_alts from
    EVERY source into a single `cover_candidates` list, but only ever wrote
    the single winner of probe_best_cover() (a cheap HEAD Content-Length
    probe with NO white-border/blank-image awareness) into
    merged['cover_url'] -- merged['cover_alts'] was never populated at all.
    dialogs._fetch_best_cover(), which DOES do proper padding/blank
    filtering across every candidate, therefore only ever had ONE candidate
    to inspect (whatever probe_best_cover picked), so its "prefer a clean
    full-bleed cover over a padded one" logic had nothing else to fall back
    on -- a padded cover with a larger file size (padding adds bytes) could
    win the initial probe and there was no second candidate left to save it.
    Fixed: every deduplicated, scored candidate URL across all sources is
    now kept in merged['cover_alts'] (and merged['cover_candidates'] with
    per-candidate source labels), so the existing padding-aware picker in
    dialogs.py now actually has the real alternatives -- e.g. a clean
    full-bleed Amazon cover -- to prefer over a padded Google Books one.
  - NEW: merged['comment_candidates'] similarly exposes every synopsis
    candidate collected from every source (deduplicated, scored,
    source-labeled), not just the single automatic winner.
  - NEW: Cover Chooser dialog (dialogs.CoverChooserDialog) -- a grid of
    thumbnails for every candidate cover found for a book, mirroring
    calibre's own built-in "pick a cover" UI from its identify-metadata
    dialog. Click to preview/select, double-click to accept immediately.
    Reachable per-book via the new "Choose Cover…" button in the Results
    tab. A manually-chosen cover is applied unconditionally on Apply,
    bypassing the automatic quality heuristics entirely (the user's
    explicit choice always wins).
  - NEW: Synopsis Chooser dialog (dialogs.SynopsisChooserDialog) -- lists
    every candidate description found for a book with its source, language,
    and score; select one to preview the full text, then apply it.
    Reachable per-book via the new "Choose Description…" button next to
    the Description field in the Results tab.
  - NEW: per-book "update cover" checkbox in the Results tab (previously
    cover updates were controlled only by the global auto_cover preference
    with no per-book override).

Cover comparison — v6.2.24
New in v6.2.24:
  - FIX (external cover with white margins / blank content still won over a
    good existing cover): the padding-aware comparison added in v6.2.22 only
    protected against a fetched cover LOSING the pixel-count comparison after
    its white margins were cropped out -- if the cropped/padded canvas was
    still numerically larger than the existing cover (e.g. a big Google
    Books editorial thumbnail vs. a smaller but correct existing cover), it
    still won and overwrote a perfectly good existing cover. Raw pixel count
    was never a proxy for whether the image actually, truthfully represents
    the book.
  - NEW: providers.is_blank_or_placeholder_image() flags covers that are
    blank or near-blank across their ENTIRE canvas (not just the border
    strip that has_white_border_padding() inspects) -- broken CDN
    thumbnails, "no cover available" placeholder tiles, and flat
    non-white filler colours all get caught by downsampling to 32x32 and
    checking overall pixel variance and distinct-colour count.
  - CHANGED POLICY: dialogs._fetch_best_cover() now returns a third
    `problematic` flag (True when the winning candidate needed the padded/
    blank fallback bucket, i.e. no clean full-bleed candidate existed at
    all). dialogs._apply() now treats "problematic" candidates completely
    differently from "clean" ones: a problematic (padded or blank) fetched
    cover is ONLY ever applied when the book currently has no cover at all
    -- it can no longer overwrite an existing cover just by having a larger
    canvas. Clean, full-bleed candidates still go through the existing
    content_cover_quality() pixel/byte comparison as before. In short: a
    cover with white margins or blank content can no longer replace a real
    existing cover, regardless of resolution.

Cover comparison — v6.2.23
New in v6.2.23:
  - BUG FIX (wrong/lower-quality cover applied over a correct high-res
    Amazon cover): probe_best_cover() HEAD-probes the top-scored cover
    candidates and picks whichever responds with the largest actual file
    size, discarding any candidate whose probe returns 0 bytes. Amazon's
    image CDN (m.media-amazon.com / images-na.ssl-images-amazon.com)
    frequently refuses plain HEAD requests (403 / empty body) even though
    the same URL serves a normal GET just fine -- anti-hotlinking
    behaviour, not a sign the image is missing or small. As a result the
    real Amazon cover (already upgraded to _SL1500_, and correctly scored
    HIGHEST by the heuristic) was silently dropped, and a lower-resolution
    Google Books cover -- which happened to answer HEAD successfully --
    won the probe and got applied instead. _head_content_length() now
    falls back from a failed/empty HEAD to a ranged GET (Range:
    bytes=0-0, reading the true size off Content-Range), and finally to a
    full GET measuring the actual bytes downloaded, before giving up. A
    Referer header matching the image host is also sent, since some CDNs
    use it as a lightweight hotlink check. This lets Amazon (and other
    HEAD-unfriendly hosts) probe successfully so the genuinely
    best-scored cover wins instead of being disqualified by a transport
    quirk.

Cover comparison — v6.2.22
New in v6.2.22:
  - BUG FIX (good existing cover replaced by a padded fetched thumbnail):
    dialogs.py's _apply() already refused to overwrite a book's existing
    cover unless the freshly fetched one measured as strictly better —
    but "better" was decided purely by width x height. When no clean,
    full-bleed candidate was available and _fetch_best_cover() fell back
    to a letterboxed/white-bordered marketing thumbnail (common on
    Google Books / Amazon editorial image endpoints), that image's blank
    white margins inflated its raw pixel count enough to numerically
    beat a smaller, full-bleed, genuinely higher-quality existing cover
    — so the plugin swapped in the worse-looking padded cover.
  - NEW providers.content_cover_quality(): same (pixels, file_bytes)
    tuple as cover_quality(), but when has_white_border_padding() flags
    an image, the white margins are cropped out first and only the real
    artwork's pixel count is used. A clean cover is unaffected; a padded
    one no longer gets credit for its blank space.
  - dialogs.py's _current_cover_quality() and _apply() now both use
    content_cover_quality() instead of the raw pixel count, so the
    existing-vs-fetched comparison is padding-aware end to end.
  - Verified against a real-world case: a padded fetched thumbnail that
    previously scored 2,586,000 "pixels" (beating a 1,807,500-pixel
    existing cover) now correctly scores 1,300,758 after the crop, so
    the existing cover is kept.

Fetch engine + Fuzzy — v6.2.20
New in v6.2.20:
  - BUG FIX (wrong book returned): when a high-weight source (Google Books,
    weight 10) returns a result for a completely different book whose title
    shares a short prefix with the queried title, two independent fixes now
    block it from contaminating the merged result.

    ROOT CAUSE (field case):
      query:  "La Dama Revelada" / Fanny Finch
      Google: "La dama de la reina" / Shannon Drake
      "la dama" is a shared prefix → old title similarity = 54% → accepted
      Google's wrong title, author, publisher, ISBN all won priority (weight 10)
      over Amazon's correct data (weight 8) in the merge.

  - FIX 1 — fuzzy.py similarity(): switched word overlap from
    len(intersection)/max(len_a,len_b) to proper Jaccard
    len(intersection)/len(union). For the bug case:
      old: 2/max(3,4) = 50%   new: 2/5 = 40%
    That 10-point reduction brings the combined score from 54% to 49%,
    just below the 50% acceptance threshold, so the title match now fails.

  - FIX 2 (defence-in-depth) — fetch_engine.py _merge_results(): added an
    author cross-check veto after the title match passes. If both the
    search author and result author are known and author similarity < 35%
    (only truly different people; name-order variations score ≥ 50%), the
    result is discarded with an INFO-level "Author veto" log line.
    "Fanny Finch" vs "Shannon Drake" = 15% → vetoed even if title matched.

  - The two fixes are independent: either one alone would have prevented
    the bug; together they provide a robust double gate.

Fetch engine — v6.2.19
New in v6.2.19:
  - BUG FIX: synopsis language mismatch. When a translated book is
    fetched, high-trust sources like Goodreads often store the *English*
    edition's synopsis rather than the translated one. Previously the
    scoring only considered source weight and text quality, so a long
    English Goodreads synopsis (weight 10, quality ~95) would always beat
    a shorter but correctly-languaged Amazon/Google synopsis for a Spanish
    or Italian book.
  - _merge_results() now accepts book_lang and applies a language-match
    bonus/penalty to each synopsis candidate:
        +20  synopsis language matches book language  ✔
        -15  synopsis is in a clearly different language  ✘
          0  language undetermined (neutral — old behaviour)
    This delta (35 points total swing) is large enough to prefer a
    same-language synopsis from a weight-8 source over a wrong-language
    synopsis from a weight-10 source (whose raw score advantage is only
    10×2 = 20 points), while not overriding a case where all synopses are
    in the same language.
  - NEW _detect_synopsis_lang(): lightweight stop-word fingerprinter
    (en/es/it/fr/de/pt) with no external dependencies. Used as a fallback
    when the source result's 'language' field is absent or too coarse.
  - Log line now reports language match status:
      "Best synopsis chosen: 1200 chars, weight=8, quality=91.2, lang=✔ es match"
      "Best synopsis chosen: 2056 chars, weight=10, quality=95.0, lang=✘ en (book=es)"
    making it immediately visible when the wrong-language path was taken.
  - Both _merge_results() call sites (pre-merge browser-pass check and
    final merge) updated to pass book_lang=lang.

Fetch engine — v6.2.18
New in v6.2.18:
  - BUG FIX: _strip_edition_noise() now also strips trailing series/volume
    parentheticals such as "(Orillas y caminos nº 3)", "(Dune Chronicles,
    Book 1)", "[Vol. 5]", "(Book 2)", etc. Previously it only stripped
    edition/format tags like "(Spanish Edition)" or "[Kindle]", so any
    result whose title was returned with a series appendage would fail
    fuzzy matching and be silently discarded — even when Amazon and
    Goodreads both returned a perfectly valid result.
  - BUG FIX (double-fetch / redundant browser pass): The browser pass
    was firing even when the first parallel fetch had already collected
    valid results, because _pre_merged returned None due to the fuzzy
    mismatch above. Fixing _strip_edition_noise() eliminates the false
    mismatch, so _pre_merged correctly finds results and the browser pass
    is not triggered. The ~30 s wasted on duplicate Firefox launches for
    Goodreads and Amazon (visible in the field log as four consecutive
    browser_fetch: launching Firefox lines for the same two sources) no
    longer happens.
  - NEW _title_prefix_match() helper: extracted from the old
    single_result-only prefix check and extended to cover all result sets
    (not just single-source fetches). Acts as a final safety net for any
    series suffix format that _strip_edition_noise's regex doesn't catch.
    The single_result variable in _merge_results() is removed as it is no
    longer needed.

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