# MetadataPlusPlus — Provider Extraction Reference

> Plugin version: v6.2.13  
> All providers share the call signature: `(title, author, isbn, asin, lang, timeout, retries, log)`  
> All providers run in **parallel threads** via `fetch_engine.py` and their results are merged afterward.

---

## How the Engine Works (fetch_engine.py)

1. **ISBN repair** — malformed ISBNs are corrected before any lookup
2. **ISBN auto-discovery** — if no ISBN is known, tries Google Books + Open Library to find one from title/author
3. **Cache lookup** — results are cached per book for a configurable number of days (default 7)
4. **Parallel fetch** — all active sources run simultaneously in daemon threads
5. **Merge** — results are combined; the best synopsis is selected by `(source weight × 10) + synopsis_quality(text)`, not raw length
6. **Cover selection** — audiobook covers are vetoed; remaining covers are scored by URL hints or probed via HTTP HEAD

---

## Source 1: Google Books

**Endpoint:** `https://www.googleapis.com/books/v1/volumes` (official JSON API)  
**Optional API key** configured in plugin Options tab — without it the anonymous quota is shared across all unauthenticated callers from the same IP.

### Search Strategy (stops on first hit)
1. `?q=isbn:<isbn>` — direct ISBN lookup
2. `?q=intitle:<title>+inauthor:<author>` — structured field search
3. `?q=<title> <author>` — plain combined query
4. `?q=<asin>` — ASIN as keyword (only if no ISBN)

Requests up to 10 results; picks the single best candidate by scoring:
`title_similarity × 2 + author_similarity + min(description_length, 2000) / 4 + cover_bonus(10)`

### Fields Extracted
| Field | JSON path |
|---|---|
| title | `volumeInfo.title` |
| authors | `volumeInfo.authors[]` |
| publisher | `volumeInfo.publisher` |
| pubdate | `volumeInfo.publishedDate` |
| comments | `volumeInfo.description` (fallback: `subtitle`) |
| tags | `volumeInfo.categories[]` |
| rating | `volumeInfo.averageRating` (rounded int) |
| language | `volumeInfo.language` |
| isbn | `industryIdentifiers[]` — ISBN_13 preferred over ISBN_10 |
| cover_url | `imageLinks.extraLarge/large/medium/thumbnail` + 3 alternate `zoom=1/2/6` URLs via `books.google.com/books/content?id=<volumeId>` |

---

## Source 2: Open Library

**Endpoints:**
- `https://openlibrary.org/api/books?bibkeys=ISBN:<isbn>&format=json&jscmd=data`
- `https://openlibrary.org/api/books?bibkeys=ASIN:<asin>&format=json&jscmd=data`
- `https://openlibrary.org/search.json?q=<query>&limit=5`
- `https://openlibrary.org/search.json?title=<t>&author=<a>&limit=5`

### Search Strategy (stops on first hit)
1. ISBN bibkey lookup
2. ASIN bibkey lookup
3. Plain `q=<title+author>` search
4. Structured `title=&author=` search

For search-path results, makes a **second call** to `/works/<key>.json` to fetch the full work-level description (richer than edition-level).

### Fields Extracted
| Field | Source |
|---|---|
| title | `title` |
| authors | `author_name[]` (search) / `authors[].name` (bibkey) |
| publisher | `publisher[0]` (search) / `publishers[].name` (bibkey) |
| pubdate | `first_publish_year` (search) / `publish_date` (bibkey) |
| comments | Work-level `/works/<key>.json → description` → fallback `first_sentence` |
| tags | `subject[]` (up to 15) |
| language | `language[0]` |
| isbn | `isbn[]` — ISBN-13 preferred |
| cover_url | `covers.openlibrary.org/b/id/<cover_i>-L.jpg` with ISBN and OLID fallback alternates |

---

## Source 3: Goodreads

**Method:** HTML scrape (public API retired December 2020)  
**Default weight: 9** (highest of any source) — because it yields full, untruncated synopses

### Two-Step Process
1. **Search page:** `https://www.goodreads.com/search?q=<isbn or title+author>`  
   — Extracts the first `/book/show/<id>` link via regex (handles relative, absolute, and single-quoted hrefs)
2. **Book page:** fetches that URL and parses:

### Fields Extracted
| Field | Extraction method |
|---|---|
| title | `og:title` meta tag (strips trailing ` \| Goodreads` suffix) |
| authors | `_parse_og_generic` JSON-LD `"author"` → fallback `class="authorName"` span |
| comments | Scans all `"description":"..."` JSON strings in the page's embedded JS payload — **picks the longest match** (full, untruncated synopsis). Fallback to `og:description` |
| rating | `"averageRating":"<float>"` JSON pattern |
| tags | All `"genreName":"..."` JSON values (up to 10, deduplicated) |
| cover_url | `og:image` |
| language | Passed through from the book's stored language (Goodreads doesn't expose language in a reliable field) |

---

## Source 4: WorldCat

**STATUS: PERMANENTLY DEAD — no-op.**  
`xisbn.worldcat.org` was shut down in 2016. The function returns `None` immediately without any network call. Kept in the registry and UI for potential future resurrection at a different URL.

---

## Source 5: Library of Congress (LOC)

**Endpoint:** `https://www.loc.gov/books/?q=<query>&fo=json&count=3`

### Search Strategy
1. `isbn:<isbn>` query
2. `title:"<title>" AND contributor:"<author>"` structured query
3. Plain `<title> <author>` fallback (if structured returns no results)

**Session block:** a single 403 from LOC trips a session-wide flag — all subsequent LOC calls in the same run are skipped automatically.

### Fields Extracted
| Field | Source |
|---|---|
| title | `title` |
| authors | `contributors[]` or `creator[]` |
| publisher | `publisher_or_distributor_number` |
| pubdate | `date` |
| comments | `description` or `notes` (list joined with space) |
| tags | `subject_headings[]` (up to 15) |
| language | `language[0]` |
| isbn | passed through |
| cover_url | `image_url[0]` |

---

## Source 6: Internet Archive

**Endpoint:** `https://archive.org/advancedsearch.php` (Solr JSON API, no key needed)

### Search Query
- `isbn:<isbn> AND mediatype:texts`
- `title:(<title>) AND creator:(<author>) AND mediatype:texts`
- `identifier:<asin> AND mediatype:texts`

**API fields requested:** `identifier,title,creator,publisher,date,subject,language,isbn,description`

### Fields Extracted
| Field | Source |
|---|---|
| title | `title` |
| authors | `creator` (string or list, normalized) |
| publisher | `publisher` |
| pubdate | `date` |
| comments | `description` (list joined if array) |
| tags | `subject[]` (up to 15) |
| language | `language` |
| identifiers | `isbn` + `archive.org:<identifier>` |
| cover_url | `https://archive.org/services/img/<identifier>` |

---

## Source 7: ISBNdb

**Endpoint:** `https://api2.isbndb.com/book/<isbn>` or `/books/<query>?page=1&pageSize=3`  
**Requires a paid API key** — returns `None` immediately if no key is configured.  
Key is sent as the `Authorization` header.

### Fields Extracted
| Field | Source |
|---|---|
| title | `title` |
| authors | `authors[]` |
| publisher | `publisher` |
| pubdate | `date_published` |
| comments | `synopsis` → `overview` → `description` |
| language | `language` |
| isbn | `isbn13` |
| cover_url | `image` |

---

## Source 8: Amazon

**Method:** HTML scrape — most complex provider  
**Routes to the correct storefront by book language:**

| Language | TLD |
|---|---|
| es (Spanish) | amazon.es |
| it (Italian) | amazon.it |
| fr (French) | amazon.fr |
| de (German) | amazon.de |
| ja (Japanese) | amazon.co.jp |
| pt (Portuguese) | amazon.com.br |
| nl, pl, sv, tr, ar, hi, zh | amazon.nl/.pl/.se/.com.tr/.ae/.in/.cn |
| all others | amazon.com |

A matching `Accept-Language` header is set per TLD so the regional HTML layout is served.  
Added **realistic browser headers** (Sec-Fetch-\*, Sec-Ch-Ua, Cache-Control) to reduce WAF fingerprinting blocks.

### Three-Step Lookup (stops on first successful parse)
1. **Direct ASIN dp/:** `https://www.amazon.com/dp/<asin>` → local TLD fallback
2. **Direct ISBN dp/:** `https://www.amazon.com/dp/<isbn>` → local TLD fallback
3. **Search fallback:** `https://www.<tld>/s?k=<title+author>&i=stripbooks`
   - Strips subtitle and edition noise from query before searching
   - Adds a small randomized delay (~0.4–0.9s) between requests
   - Collects all `data-asin="..."` values; sorts real ASINs (contain a letter) before ISBN-10s; tries up to 5 dp/ pages until one yields a parseable title

**Bot-block detection** (`_amazon_page_is_blocked`): every fetched page is checked against 7 signatures before parsing:
- "Enter the characters" (classic CAPTCHA)
- "api-services-support"
- "Sorry, we just need to make sure"
- "To discuss automated access"
- "captcha" (generic)
- "Type the characters you see"
- "something went wrong on our end"

**Audiobook pages** are also detected and skipped (checks `productGroup:audible`, `Listening Length`, narrator/Audible/ACX signals).

### Title Extraction — 6-Step Priority Cascade
1. `id="productTitle"` span (classic layout)
2. `data-feature-name="title"` / `id="dp-title"` (newer SPA layout, .es/.it)
3. JSON-LD `@type:Book "name"` field
4. React/Apollo `"title":{"value":"..."}` JSON
5. `og:title` meta tag (validated — bare "Amazon.es" and junk values rejected)
6. `<title>` tag (last resort, noisy)

### All Fields Extracted from dp/ Pages
| Field | Extraction method |
|---|---|
| title | 6-step cascade above |
| authors | `class="author"` spans → JSON-LD `"author":[{"name":...}]` → `og:author` meta |
| publisher | `Publisher:` label regex → JSON-LD `"publisher"` |
| isbn | `ISBN-13:` / `ISBN-10:` / `Print ISBN:` / JSON `"isbn"` patterns |
| comments | 6-step cascade: JSON-LD description → React JSON `"description":{"value":...}` → `og:description` meta → `bookDescription_feature_div` → `a-expander-content` block → `productDescription <p>` |
| cover_url | `"hiRes"/"large"/"medium"` JSON → `id="landingImage"` src → `og:image`; URL upgraded to `_SL1500_` resolution |
| identifiers | ASIN from `"ASIN":"..."` JSON; ISBN from above |

---

## Sources 9–13: Kobo Regional (5 variants)

| Provider | Locale | Storefront |
|---|---|---|
| `fetch_kobo_com` | en-US | kobo.com/en |
| `fetch_kobo_es` | es-ES | kobo.com/es |
| `fetch_kobo_it` | it-IT | kobo.com/it |
| `fetch_kobo_fr` | fr-FR | kobo.com/fr |
| `fetch_kobo_de` | de-DE | kobo.com/de |

All share `_fetch_kobo_storefront()` — only the locale string differs.

### Two-Step Scrape
1. `https://www.kobo.com/<locale>/search?query=<isbn or title+author>`  
   — Finds first `href="/<locale>/ebook/..."` link (fallback: any `/xx/ebook/` path)
2. Fetches product page, parsed by `_parse_kobo_page`

### Page Parsing
- Iterates all `<script type="application/ld+json">` blocks looking for `@type:Book` or `@type:Product`
- Fallback: `_parse_og_generic` (og:title, og:description, og:image)

### Fields Extracted (from JSON-LD)
| Field | Source |
|---|---|
| title | `name` |
| authors | `author[].name` |
| publisher | `publisher` / `publishedBy` |
| pubdate | `datePublished` (first 10 chars) |
| comments | `description` |
| cover_url | `image` or `thumbnailUrl` |
| isbn | `isbn` field (cleaned of dashes/spaces) |
| language | locale code (en/es/it/fr/de) |

---

## Source 14: Casa del Libro — *Spanish*

**Endpoint:** `casadellibro.com` HTML scrape

**Steps:**
1. ISBN direct: `casadellibro.com/busqueda-por-isbn?isbn=<isbn>`
2. Title+author search: `casadellibro.com/busqueda-generica?busqueda=<q>` → first `/libro/...` link → product page

### Fields Extracted (`_parse_casadellibro_page`)
| Field | Extraction |
|---|---|
| title | `og:title` or `<h1 class="product...">` |
| authors | `itemprop="author"` or JSON `"author"` |
| publisher | `Editorial:` / `Publisher:` label or JSON `"publisher"` |
| pubdate | Spanish date label regex (4-digit year) |
| comments | JSON `"description"` (40+ chars) or `div[id/class*=sinopsis]` |
| cover_url | `og:image` or `img.portada/cover` |
| isbn | `ISBN: <13 digits>` regex |
| language | `es` (hardcoded) |

---

## Source 15: FNAC Spain — *Spanish*

**Endpoint:** `fnac.es/SearchResult/ResultList.aspx?SCat=2&Search=<q>` → product page

Finds product link via 4 URL-pattern regexes (Livre/Libro/Book path fragments, `/a<id>/` form).

### Fields Extracted (`_parse_fnac_page`)
| Field | Extraction |
|---|---|
| title | `og:title` |
| authors | JSON `"author"` or `itemprop="author"` |
| publisher | JSON `"publisher"` |
| comments | JSON `"description"` (40+ chars, `\n` cleaned) |
| cover_url | `og:image` |
| isbn | `ISBN: <13 digits>` regex |

---

## Source 16: Feltrinelli — *Italian*

**Endpoint:** `lafeltrinelli.it/ricerca/libri?q=<q>` → first `href="/...libro/ebook..."` → product page

Falls back to parsing JSON-LD directly from the search results page if the product page fetch fails.

### Fields Extracted (`_parse_feltrinelli_jsonld`)
Same as Kobo JSON-LD extraction (iterates `<script type="application/ld+json">` for `@type:Book/Product`):
title, authors, publisher, pubdate, comments, cover_url, isbn, language=`it`

Fallback: `_parse_og_generic` (og:title, og:description, og:image)

---

## Source 17: Libraccio — *Italian*

**Endpoint:**
- ISBN direct: `libraccio.it/libro/<isbn>.html`
- Search: `libraccio.it/ricerca?q=<q>` → first `/libro/...html` link

### Fields Extracted (`_parse_ibs_page` — shared IBS/Libraccio HTML structure)
JSON-LD `@type:Book/Product` first, fallback `_parse_og_generic`:
title, authors, publisher, comments, cover_url, isbn, language=`it`

---

## Source 18: BNF — Bibliothèque nationale de France — *French*

**Endpoint:** `catalogue.bnf.fr/api/SRU` — SRU/UNIMARC XML protocol, **no key required**

### CQL Query
- `bib.isbn = "<isbn>"`
- `bib.title all "<title>" and bib.author all "<author>"`
- `bib.title all "<title>"`

### Fields Extracted (UNIMARC XML — `_parse_bnf_unimarc`)
| Field | UNIMARC tag/subfield |
|---|---|
| title | 200$a (+ 200$e subtitle) |
| authors | 700$a+$b (primary) + 701$a (joint author) |
| publisher | 210$c |
| pubdate | 210$d |
| isbn | 010$a |
| language | 101$a |
| tags | 606$a + 607$a (subject headings, up to 15) |

*No cover URL — BNF SRU responses do not include images.*

---

## Source 19: BNE — Biblioteca Nacional de España — *Spanish*

**Primary endpoint:** `catalogo.bne.es/sru/sru` — SRU/MARCXML, **no key required**

### CQL Query
- `isbn="<isbn>"`
- `title="<title>" and author="<author>"`
- `title="<title>"`

### Fields Extracted (MARC 21 XML — `_parse_bne_marcxml`)
| Field | MARC tag/subfield |
|---|---|
| title | 245$a + 245$b (subtitle) |
| authors | 100$a (main entry) + 700$a (added entries) |
| publisher | 264$b or 260$b |
| pubdate | 264$c or 260$c (digits only, first 4) |
| isbn | 020$a |
| language | 041$a |
| tags | 650$a + 651$a (up to 15) |

**HTML fallback** if SRU fails: `catalogo.bne.es/discovery/search?...`  
Tries `_parse_og_generic`, then MARC-style table regex for Título/Autor/ISBN labels.

---

## Source 20: SBN — Servizio Bibliotecario Nazionale — *Italian*

**Endpoint:** `opac.sbn.it` HTML (no clean REST API)

**Queries:**
- ISBN: `opac.sbn.it/web/sbn/home?q=isbn:<isbn>`
- Title/author: `opac.sbn.it/web/sbn/risultati-ricerca-avanzata?titolo=<title>&autore=<author>`

### Page Parsing
1. JSON-LD `@type:Book` or `@type:CreativeWork` — extracts `name` as title
2. HTML table fallback — regex labels: `Titolo`, `Autore/Responsabilità`, `Editore/Publisher`, `ISBN`

### Fields Extracted
| Field | Source |
|---|---|
| title | JSON-LD `name` or HTML `Titolo` label |
| authors | HTML `Autore/Responsabilità` label |
| publisher | HTML `Editore/Publisher` label |
| isbn | HTML `ISBN:` label |
| language | `it` (hardcoded) |

---

## Field Coverage Matrix

| Source | Title | Authors | Publisher | Pubdate | Synopsis | Tags | Rating | ISBN | Cover |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Google Books | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| Open Library | Y | Y | Y | Y | Y | Y | - | Y | Y |
| **Goodreads** | Y | Y | - | - | **Best** | Y | Y | Y | Y |
| WorldCat | **DEAD** | | | | | | | | |
| LOC | Y | Y | Y | Y | Y | Y | - | Y | Y |
| Internet Archive | Y | Y | Y | Y | Y | Y | - | Y | Y |
| ISBNdb | Y | Y | Y | Y | Y | - | - | Y | Y |
| Amazon | Y | Y | Y | - | Y | - | - | Y | Y |
| Kobo (x5) | Y | Y | Y | Y | Y | - | - | Y | Y |
| Casa del Libro | Y | Y | Y | Y | Y | - | - | Y | Y |
| FNAC | Y | Y | Y | - | Y | - | - | Y | Y |
| Feltrinelli | Y | Y | Y | Y | Y | - | - | Y | Y |
| Libraccio | Y | Y | Y | - | Y | - | - | Y | Y |
| BNF | Y | Y | Y | Y | - | Y | - | Y | - |
| BNE | Y | Y | Y | Y | - | Y | - | Y | - |
| SBN | Y | Y | Y | - | - | - | - | Y | - |

---

## HTTP Infrastructure Notes

- **User-Agent:** `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36`
- **Retry logic:** up to `retries` attempts (default 2) with exponential backoff (`min(2^attempt, 8)` seconds) on HTTP 429, 500, 502, 503, 504
- **Google 429** → trips a per-book cooldown (30s); resets at the start of each new book
- **Google 403** → logs the API error message from the response body; diagnoses key vs. quota issues
- **Amazon search 503** → trips a per-TLD cooldown (60s); resets at the start of each new book
- **LOC 403** → session-wide block for the rest of the run
- **SSL errors** → one automatic retry with 2s delay
- **Cover URL upgrading:** Amazon covers are rewritten to `_SL1500_`; Open Library covers to `-L.jpg`
- **Audiobook cover veto:** any cover URL matching Audible/ACX CDN paths is scored -1 and never wins
