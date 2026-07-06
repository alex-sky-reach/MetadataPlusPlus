#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

"""
Metadata++ interface translations (v6.2.26).

Small self-contained translation helper for the plugin's user-facing
dialog strings — the "Fetching from all sources" progress/results dialog,
the Choose Cover / Choose Description pickers, and the Options screen.

Deliberately NOT translated: log output (both the in-dialog Log tab and
the on-disk debug log), exception text, and provider/source names. Log
text is meant to be pasted into bug reports, and mixed-language logs are
harder to triage than English-only ones — so logging always stays in
English regardless of the interface language setting.

Supported interface languages: English (en), Italian (it), Spanish (es),
Romanian (ro). Any missing key or language falls back to English, and any
completely unknown key falls back to the key itself (visible-but-safe,
rather than crashing a dialog over a missing translation).

Usage:
    from calibre_plugins.metadata_plus.core.i18n import tr
    label = QLabel(tr('choose_cover_button', n=7))
"""

INTERFACE_LANGUAGES = [
    ('en', 'English'),
    ('it', 'Italiano'),
    ('es', 'Español'),
    ('ro', 'Română'),
]

_STRINGS = {
    # ── Fetch / Results dialog ──────────────────────────────────────────
    'fetch_dialog_title': {
        'en': 'Metadata++ — Fetching from all sources',
        'it': 'Metadata++ — Recupero da tutte le fonti',
        'es': 'Metadata++ — Obteniendo de todas las fuentes',
        'ro': 'Metadata++ — Se preiau date din toate sursele',
    },
    'initialising': {
        'en': 'Initialising…', 'it': 'Inizializzazione…',
        'es': 'Inicializando…', 'ro': 'Se inițializează…',
    },
    'status_complete': {
        'en': 'Complete — {found}/{total} books with metadata. {errors} error(s).',
        'it': 'Completato — {found}/{total} libri con metadati. {errors} errore/i.',
        'es': 'Completado — {found}/{total} libros con metadatos. {errors} error(es).',
        'ro': 'Finalizat — {found}/{total} cărți cu metadate. {errors} eroare/i.',
    },
    'tab_results': {
        'en': 'Results', 'it': 'Risultati', 'es': 'Resultados', 'ro': 'Rezultate',
    },
    'tab_log': {
        'en': 'Log', 'it': 'Registro', 'es': 'Registro', 'ro': 'Jurnal',
    },
    'btn_clear_log': {
        'en': 'Clear log', 'it': 'Svuota registro',
        'es': 'Borrar registro', 'ro': 'Golește jurnalul',
    },
    'btn_select_all': {
        'en': 'Select All', 'it': 'Seleziona tutto',
        'es': 'Seleccionar todo', 'ro': 'Selectează tot',
    },
    'btn_deselect_all': {
        'en': 'Deselect All', 'it': 'Deseleziona tutto',
        'es': 'Deseleccionar todo', 'ro': 'Deselectează tot',
    },
    'btn_apply_selected': {
        'en': '✔ Apply Selected Metadata', 'it': '✔ Applica metadati selezionati',
        'es': '✔ Aplicar metadatos seleccionados', 'ro': '✔ Aplică metadatele selectate',
    },
    'btn_close': {
        'en': 'Close', 'it': 'Chiudi', 'es': 'Cerrar', 'ro': 'Închide',
    },

    # ── Result panel field labels ───────────────────────────────────────
    'field_sources': {
        'en': 'Sources', 'it': 'Fonti', 'es': 'Fuentes', 'ro': 'Surse',
    },
    'field_cover': {
        'en': 'Cover', 'it': 'Copertina', 'es': 'Portada', 'ro': 'Copertă',
    },
    'field_title': {
        'en': 'Title', 'it': 'Titolo', 'es': 'Título', 'ro': 'Titlu',
    },
    'field_authors': {
        'en': 'Authors', 'it': 'Autori', 'es': 'Autores', 'ro': 'Autori',
    },
    'field_publisher': {
        'en': 'Publisher', 'it': 'Editore', 'es': 'Editorial', 'ro': 'Editură',
    },
    'field_pubdate': {
        'en': 'Pub. Date', 'it': 'Data pubbl.', 'es': 'Fecha public.', 'ro': 'Data public.',
    },
    'field_description': {
        'en': 'Description', 'it': 'Descrizione', 'es': 'Descripción', 'ro': 'Descriere',
    },
    'field_tags': {
        'en': 'Tags / Categories', 'it': 'Tag / Categorie',
        'es': 'Etiquetas / Categorías', 'ro': 'Etichete / Categorii',
    },
    'field_rating': {
        'en': 'Rating', 'it': 'Valutazione', 'es': 'Valoración', 'ro': 'Evaluare',
    },
    'field_language': {
        'en': 'Language', 'it': 'Lingua', 'es': 'Idioma', 'ro': 'Limbă',
    },
    'field_identifiers': {
        'en': 'Identifiers', 'it': 'Identificatori', 'es': 'Identificadores', 'ro': 'Identificatori',
    },
    'choose_cover_button': {
        'en': 'Choose Cover… ({n})', 'it': 'Scegli copertina… ({n})',
        'es': 'Elegir portada… ({n})', 'ro': 'Alege coperta… ({n})',
    },
    'view_cover_button': {
        'en': 'View Cover', 'it': 'Visualizza copertina',
        'es': 'Ver portada', 'ro': 'Vizualizează coperta',
    },
    'choose_description_button': {
        'en': 'Choose Description… ({n})', 'it': 'Scegli descrizione… ({n})',
        'es': 'Elegir descripción… ({n})', 'ro': 'Alege descrierea… ({n})',
    },

    # ── Cover chooser dialog ────────────────────────────────────────────
    'cover_chooser_title': {
        'en': 'Metadata++ — Choose Cover', 'it': 'Metadata++ — Scegli copertina',
        'es': 'Metadata++ — Elegir portada', 'ro': 'Metadata++ — Alege coperta',
    },
    'cover_chooser_instructions': {
        'en': '{n} cover candidate(s) found across all sources. Click a cover to '
              'preview/select it, or double-click to pick it immediately.',
        'it': 'Trovate {n} copertine candidate tra tutte le fonti. Clicca su una '
              'copertina per anteprima/selezione, oppure fai doppio clic per '
              'sceglierla subito.',
        'es': 'Se encontraron {n} portada(s) candidatas en todas las fuentes. Haz '
              'clic en una portada para previsualizarla/seleccionarla, o haz doble '
              'clic para elegirla de inmediato.',
        'ro': 'S-au găsit {n} coperte candidate în toate sursele. Fă clic pe o '
              'copertă pentru previzualizare/selectare, sau dublu clic pentru a o '
              'alege imediat.',
    },
    'btn_use_selected_cover': {
        'en': '✔ Use Selected Cover', 'it': '✔ Usa copertina selezionata',
        'es': '✔ Usar portada seleccionada', 'ro': '✔ Folosește coperta selectată',
    },
    'btn_cancel': {
        'en': 'Cancel', 'it': 'Annulla', 'es': 'Cancelar', 'ro': 'Anulează',
    },
    'loading': {
        'en': 'Loading…', 'it': 'Caricamento…', 'es': 'Cargando…', 'ro': 'Se încarcă…',
    },
    'err_select_cover_first': {
        'en': 'Please select a cover first.', 'it': 'Seleziona prima una copertina.',
        'es': 'Selecciona primero una portada.', 'ro': 'Selectează întâi o copertă.',
    },
    'err_select_description_first': {
        'en': 'Please select a description first.',
        'it': 'Seleziona prima una descrizione.',
        'es': 'Selecciona primero una descripción.',
        'ro': 'Selectează întâi o descriere.',
    },

    # ── Description/synopsis chooser dialog ─────────────────────────────
    'description_chooser_title': {
        'en': 'Metadata++ — Choose Description',
        'it': 'Metadata++ — Scegli descrizione',
        'es': 'Metadata++ — Elegir descripción',
        'ro': 'Metadata++ — Alege descrierea',
    },
    'description_chooser_instructions': {
        'en': '{n} description(s) found across all sources. Select one on the '
              'left to preview it, then click Use Selected.',
        'it': 'Trovate {n} descrizioni tra tutte le fonti. Selezionane una a '
              'sinistra per visualizzarla in anteprima, poi clicca su Usa selezionata.',
        'es': 'Se encontraron {n} descripción(es) en todas las fuentes. Selecciona '
              'una a la izquierda para previsualizarla y luego haz clic en Usar '
              'seleccionada.',
        'ro': 'S-au găsit {n} descrieri în toate sursele. Selectează una din stânga '
              'pentru previzualizare, apoi apasă Folosește selecția.',
    },
    'btn_use_selected_description': {
        'en': '✔ Use Selected Description', 'it': '✔ Usa descrizione selezionata',
        'es': '✔ Usar descripción seleccionada', 'ro': '✔ Folosește descrierea selectată',
    },
    'lbl_source': {
        'en': 'Source', 'it': 'Fonte', 'es': 'Fuente', 'ro': 'Sursă',
    },
    'lbl_language': {
        'en': 'Language', 'it': 'Lingua', 'es': 'Idioma', 'ro': 'Limbă',
    },
    'lbl_score': {
        'en': 'Score', 'it': 'Punteggio', 'es': 'Puntuación', 'ro': 'Scor',
    },

    # ── Options tab ──────────────────────────────────────────────────────
    'tab_general': {
        'en': 'General', 'it': 'Generale', 'es': 'General', 'ro': 'General',
    },
    'tab_sources': {
        'en': 'Sources', 'it': 'Fonti', 'es': 'Fuentes', 'ro': 'Surse',
    },
    'tab_weights': {
        'en': 'Weights', 'it': 'Pesi', 'es': 'Ponderaciones', 'ro': 'Ponderi',
    },
    'tab_options': {
        'en': 'Options', 'it': 'Opzioni', 'es': 'Opciones', 'ro': 'Opțiuni',
    },
    'tab_diagnostics': {
        'en': 'Diagnostics', 'it': 'Diagnostica', 'es': 'Diagnóstico', 'ro': 'Diagnosticare',
    },
    'interface_language_label': {
        'en': 'Interface language:', 'it': 'Lingua dell\u2019interfaccia:',
        'es': 'Idioma de la interfaz:', 'ro': 'Limba interfeței:',
    },

    # ── Main toolbar dropdown menu (action.py) ──────────────────────────
    'action_tooltip': {
        'en': 'Fetch rich metadata from 8 sources: Amazon, Kobo, Google '
              'Books, Open Library, WorldCat, LoC, Internet Archive, ISBNdb',
        'it': 'Recupera metadati completi da 8 fonti: Amazon, Kobo, Google '
              'Books, Open Library, WorldCat, LoC, Internet Archive, ISBNdb',
        'es': 'Obtén metadatos completos de 8 fuentes: Amazon, Kobo, Google '
              'Books, Open Library, WorldCat, LoC, Internet Archive, ISBNdb',
        'ro': 'Preia metadate complete din 8 surse: Amazon, Kobo, Google '
              'Books, Open Library, WorldCat, LoC, Internet Archive, ISBNdb',
    },
    'menu_fetch_all': {
        'en': 'Fetch Metadata (All Sources)',
        'it': 'Recupera metadati (tutte le fonti)',
        'es': 'Obtener metadatos (todas las fuentes)',
        'ro': 'Preia metadate (toate sursele)',
    },
    'menu_fetch_all_desc': {
        'en': 'Parallel fetch from every enabled source',
        'it': 'Recupero in parallelo da tutte le fonti attive',
        'es': 'Obtención en paralelo de todas las fuentes activas',
        'ro': 'Preluare în paralel din toate sursele active',
    },
    'menu_detect_dupes': {
        'en': 'Detect Duplicates in Selection',
        'it': 'Rileva duplicati nella selezione',
        'es': 'Detectar duplicados en la selección',
        'ro': 'Detectează duplicatele în selecție',
    },
    'menu_repair_isbn': {
        'en': 'Repair / Validate ISBNs',
        'it': 'Ripara / Valida ISBN',
        'es': 'Reparar / Validar ISBN',
        'ro': 'Repară / Validează ISBN-uri',
    },
    'menu_clear_cache': {
        'en': 'Clear Metadata Cache',
        'it': 'Svuota cache metadati',
        'es': 'Borrar caché de metadatos',
        'ro': 'Golește memoria cache a metadatelor',
    },
    'menu_configure': {
        'en': 'Configure Metadata++…',
        'it': 'Configura Metadata++…',
        'es': 'Configurar Metadata++…',
        'ro': 'Configurează Metadata++…',
    },
    'no_selection_title': {
        'en': 'Metadata++ — No selection',
        'it': 'Metadata++ — Nessuna selezione',
        'es': 'Metadata++ — Sin selección',
        'ro': 'Metadata++ — Nicio selecție',
    },
    'no_selection_msg': {
        'en': 'Please select one or more books first.',
        'it': 'Seleziona prima uno o più libri.',
        'es': 'Selecciona primero uno o más libros.',
        'ro': 'Selectează întâi una sau mai multe cărți.',
    },
    'dupe_min_selection_msg': {
        'en': 'Select at least 2 books to check for duplicates.',
        'it': 'Seleziona almeno 2 libri per verificare i duplicati.',
        'es': 'Selecciona al menos 2 libros para comprobar duplicados.',
        'ro': 'Selectează cel puțin 2 cărți pentru a verifica duplicatele.',
    },
    'isbn_repair_dialog_title': {
        'en': 'Metadata++ — ISBN Repair',
        'it': 'Metadata++ — Riparazione ISBN',
        'es': 'Metadata++ — Reparación de ISBN',
        'ro': 'Metadata++ — Repararea ISBN',
    },
    'isbn_repair_result_msg': {
        'en': '{repaired} ISBN(s) repaired/normalized. {skipped} skipped.',
        'it': '{repaired} ISBN riparati/normalizzati. {skipped} saltati.',
        'es': '{repaired} ISBN reparados/normalizados. {skipped} omitidos.',
        'ro': '{repaired} ISBN reparate/normalizate. {skipped} omise.',
    },
    'cache_cleared_msg': {
        'en': 'Cache cleared.', 'it': 'Cache svuotata.',
        'es': 'Caché borrada.', 'ro': 'Cache golit.',
    },

    # ── Config dialog: Sources tab ───────────────────────────────────────
    'grp_global_sources': {
        'en': 'Global Sources  (always active)',
        'it': 'Fonti globali  (sempre attive)',
        'es': 'Fuentes globales  (siempre activas)',
        'ro': 'Surse globale  (mereu active)',
    },
    'grp_lang_sources': {
        'en': 'Language-Specific Sources\n'
              '✦ Auto-activated when the book\'s language matches — '
              'tick to always query regardless of language',
        'it': 'Fonti specifiche per lingua\n'
              '✦ Attivate automaticamente quando la lingua del libro '
              'corrisponde — spunta per interrogarle sempre',
        'es': 'Fuentes específicas por idioma\n'
              '✦ Se activan automáticamente cuando el idioma del libro '
              'coincide — marca para consultarlas siempre',
        'ro': 'Surse specifice limbii\n'
              '✦ Activate automat când limba cărții se potrivește — '
              'bifează pentru a le interoga mereu',
    },
    'grp_api_keys': {
        'en': 'API Keys', 'it': 'Chiavi API',
        'es': 'Claves API', 'ro': 'Chei API',
    },
    'lbl_google_api_key': {
        'en': 'Google Books API Key:', 'it': 'Chiave API Google Books:',
        'es': 'Clave API de Google Books:', 'ro': 'Cheie API Google Books:',
    },
    'lbl_isbndb_api_key': {
        'en': 'ISBNdb API Key:', 'it': 'Chiave API ISBNdb:',
        'es': 'Clave API de ISBNdb:', 'ro': 'Cheie API ISBNdb:',
    },

    # ── Config dialog: Weights tab ───────────────────────────────────────
    'grp_global_weights': {
        'en': 'Global Source Weights  (higher = preferred)',
        'it': 'Pesi globali delle fonti  (più alto = preferito)',
        'es': 'Ponderaciones globales de fuentes  (más alto = preferido)',
        'ro': 'Ponderi globale ale surselor  (mai mare = preferat)',
    },
    'grp_lang_weights': {
        'en': 'Language-Specific Source Weights',
        'it': 'Pesi delle fonti specifici per lingua',
        'es': 'Ponderaciones de fuentes específicas por idioma',
        'ro': 'Ponderi ale surselor specifice limbii',
    },

    # ── Config dialog: Options tab ───────────────────────────────────────
    'grp_network': {
        'en': 'Network', 'it': 'Rete', 'es': 'Red', 'ro': 'Rețea',
    },
    'lbl_timeout': {
        'en': 'Timeout:', 'it': 'Timeout:', 'es': 'Tiempo de espera:', 'ro': 'Timp de așteptare:',
    },
    'lbl_retries': {
        'en': 'Retries per source:', 'it': 'Tentativi per fonte:',
        'es': 'Reintentos por fuente:', 'ro': 'Reîncercări per sursă:',
    },
    'grp_metadata': {
        'en': 'Metadata', 'it': 'Metadati', 'es': 'Metadatos', 'ro': 'Metadate',
    },
    'cb_isbn_repair': {
        'en': 'Auto-repair / validate ISBN',
        'it': 'Ripara / valida automaticamente ISBN',
        'es': 'Reparar / validar ISBN automáticamente',
        'ro': 'Repară / validează automat ISBN',
    },
    'cb_normalize': {
        'en': 'Normalize multilingual metadata',
        'it': 'Normalizza metadati multilingue',
        'es': 'Normalizar metadatos multilingües',
        'ro': 'Normalizează metadatele multilingve',
    },
    'cb_duplicates': {
        'en': 'Detect duplicates after fetch',
        'it': 'Rileva duplicati dopo il recupero',
        'es': 'Detectar duplicados tras la obtención',
        'ro': 'Detectează duplicatele după preluare',
    },
    'cb_synopsis_header': {
        'en': 'Prepend page/word count, reading time & tags to synopsis',
        'it': 'Antepone numero pagine/parole, tempo di lettura e tag alla trama',
        'es': 'Anteponer nº de páginas/palabras, tiempo de lectura y etiquetas a la sinopsis',
        'ro': 'Adaugă la început nr. de pagini/cuvinte, timp de citire și etichete la sinopsis',
    },
    'lbl_reading_speed': {
        'en': 'Reading speed:',
        'it': 'Velocità di lettura:',
        'es': 'Velocidad de lectura:',
        'ro': 'Viteză de citire:',
    },
    'lbl_fuzzy_threshold': {
        'en': 'Fuzzy match threshold:', 'it': 'Soglia di corrispondenza approssimata:',
        'es': 'Umbral de coincidencia difusa:', 'ro': 'Prag de potrivire aproximativă:',
    },
    'lbl_preferred_language': {
        'en': 'Preferred language:', 'it': 'Lingua preferita:',
        'es': 'Idioma preferido:', 'ro': 'Limbă preferată:',
    },
    'grp_cover_art': {
        'en': 'Cover Art', 'it': 'Copertine', 'es': 'Portadas', 'ro': 'Coperte',
    },
    'cb_auto_cover': {
        'en': 'Auto-download best cover',
        'it': 'Scarica automaticamente la copertina migliore',
        'es': 'Descargar automáticamente la mejor portada',
        'ro': 'Descarcă automat cea mai bună copertă',
    },
    'lbl_min_cover_dim': {
        'en': 'Min cover dimension:', 'it': 'Dimensione minima copertina:',
        'es': 'Dimensión mínima de portada:', 'ro': 'Dimensiune minimă copertă:',
    },
    'cb_probe_covers': {
        'en': 'Probe cover file sizes (HEAD request) — picks highest-resolution image',
        'it': 'Verifica dimensione file copertine (richiesta HEAD) — sceglie l\u2019immagine a risoluzione più alta',
        'es': 'Comprobar tamaño de archivo de portadas (solicitud HEAD) — elige la imagen de mayor resolución',
        'ro': 'Verifică dimensiunea fișierelor copertelor (cerere HEAD) — alege imaginea cu cea mai mare rezoluție',
    },
    'cb_probe_ol_cover': {
        'en': 'Direct Open Library cover lookup by ISBN',
        'it': 'Ricerca diretta copertina su Open Library tramite ISBN',
        'es': 'Búsqueda directa de portada en Open Library por ISBN',
        'ro': 'Căutare directă a copertei pe Open Library după ISBN',
    },
    'lbl_cover_probe_timeout': {
        'en': 'Cover probe timeout:', 'it': 'Timeout verifica copertina:',
        'es': 'Tiempo de espera de comprobación de portada:', 'ro': 'Timp de așteptare verificare copertă:',
    },
    'grp_isbn_autodiscovery': {
        'en': 'ISBN Auto-Discovery', 'it': 'Rilevamento automatico ISBN',
        'es': 'Detección automática de ISBN', 'ro': 'Detectare automată ISBN',
    },
    'cb_isbn_lookup': {
        'en': 'Auto-discover ISBN from ASIN (Amazon dp/ page scrape) when missing',
        'it': 'Rileva automaticamente l\u2019ISBN dall\u2019ASIN (scraping pagina dp/ Amazon) quando mancante',
        'es': 'Detectar automáticamente el ISBN a partir del ASIN (extracción de la página dp/ de Amazon) cuando falte',
        'ro': 'Detectează automat ISBN din ASIN (extragere pagină dp/ Amazon) când lipsește',
    },
    'grp_cache': {
        'en': 'Cache', 'it': 'Cache', 'es': 'Caché', 'ro': 'Cache',
    },
    'lbl_cache_ttl': {
        'en': 'Cache TTL:', 'it': 'Durata cache:',
        'es': 'Duración de la caché:', 'ro': 'Durata cache-ului:',
    },
    'btn_clear_cache_now': {
        'en': 'Clear Cache Now', 'it': 'Svuota cache ora',
        'es': 'Borrar caché ahora', 'ro': 'Golește cache-ul acum',
    },
    'grp_browser_fallback': {
        'en': 'Browser Fallback (Playwright / Firefox)',
        'it': 'Fallback browser (Playwright / Firefox)',
        'es': 'Alternativa de navegador (Playwright / Firefox)',
        'ro': 'Alternativă browser (Playwright / Firefox)',
    },
    'cb_browser_fallback': {
        'en': 'Use Firefox browser as fallback for bot-blocked sources '
              '(Amazon, Kobo, Casa del Libro, FNAC, Feltrinelli, Libraccio, SBN, Goodreads)',
        'it': 'Usa il browser Firefox come alternativa per le fonti bloccate '
              'dai sistemi anti-bot (Amazon, Kobo, Casa del Libro, FNAC, Feltrinelli, Libraccio, SBN, Goodreads)',
        'es': 'Usar el navegador Firefox como alternativa para fuentes bloqueadas '
              'por sistemas antibots (Amazon, Kobo, Casa del Libro, FNAC, Feltrinelli, Libraccio, SBN, Goodreads)',
        'ro': 'Folosește browserul Firefox ca alternativă pentru sursele blocate '
              'de sisteme anti-bot (Amazon, Kobo, Casa del Libro, FNAC, Feltrinelli, Libraccio, SBN, Goodreads)',
    },
    'cb_browser_headless': {
        'en': 'Run browser headless (no visible Firefox window)',
        'it': 'Esegui il browser in modalità headless (nessuna finestra Firefox visibile)',
        'es': 'Ejecutar el navegador en modo headless (sin ventana de Firefox visible)',
        'ro': 'Rulează browserul headless (fără fereastră Firefox vizibilă)',
    },
    'cb_amazon_direct_only': {
        'en': 'Amazon: direct lookup only (skip title-search fallback when ASIN/ISBN is known) '
              '-- prevents multiple browser windows opening for search candidates',
        'it': 'Amazon: solo ricerca diretta (salta la ricerca per titolo quando ASIN/ISBN è noto) '
              '-- evita l\u2019apertura di più finestre del browser per i candidati di ricerca',
        'es': 'Amazon: solo búsqueda directa (omite la búsqueda por título cuando se conoce el ASIN/ISBN) '
              '-- evita que se abran varias ventanas del navegador para los candidatos de búsqueda',
        'ro': 'Amazon: doar căutare directă (omite căutarea după titlu când ASIN/ISBN este cunoscut) '
              '-- evită deschiderea mai multor ferestre de browser pentru candidații de căutare',
    },
    'lbl_browser_page_timeout': {
        'en': 'Browser page timeout:', 'it': 'Timeout pagina browser:',
        'es': 'Tiempo de espera de página del navegador:', 'ro': 'Timp de așteptare pagină browser:',
    },
    'btn_check_install_playwright': {
        'en': 'Check / Install Playwright', 'it': 'Verifica / Installa Playwright',
        'es': 'Comprobar / Instalar Playwright', 'ro': 'Verifică / Instalează Playwright',
    },

    # ── Config dialog: Diagnostics tab ───────────────────────────────────
    'grp_logging': {
        'en': 'Logging', 'it': 'Registrazione', 'es': 'Registro', 'ro': 'Jurnalizare',
    },
    'lbl_log_level': {
        'en': 'Log level:', 'it': 'Livello di log:',
        'es': 'Nivel de registro:', 'ro': 'Nivel de jurnalizare:',
    },
    'lbl_recent_log': {
        'en': 'Recent log:', 'it': 'Registro recente:',
        'es': 'Registro reciente:', 'ro': 'Jurnal recent:',
    },
    'placeholder_log_output': {
        'en': 'Plugin log output appears here…',
        'it': 'L\u2019output del registro del plugin appare qui…',
        'es': 'La salida del registro del complemento aparece aquí…',
        'ro': 'Ieșirea jurnalului pluginului apare aici…',
    },

    # ── Playwright setup dialog ──────────────────────────────────────────
    'grp_dependency_status': {
        'en': 'Dependency Status', 'it': 'Stato delle dipendenze',
        'es': 'Estado de las dependencias', 'ro': 'Starea dependențelor',
    },
    'checking_ellipsis': {
        'en': 'Checking...', 'it': 'Verifica in corso...',
        'es': 'Comprobando...', 'ro': 'Se verifică...',
    },
    'lbl_system_python': {
        'en': 'System Python:', 'it': 'Python di sistema:',
        'es': 'Python del sistema:', 'ro': 'Python de sistem:',
    },
    'lbl_playwright_pkg': {
        'en': 'Playwright package:', 'it': 'Pacchetto Playwright:',
        'es': 'Paquete Playwright:', 'ro': 'Pachet Playwright:',
    },
    'lbl_firefox_binary': {
        'en': 'Firefox browser binary:', 'it': 'Eseguibile del browser Firefox:',
        'es': 'Ejecutable del navegador Firefox:', 'ro': 'Executabil browser Firefox:',
    },
    'lbl_install_output': {
        'en': 'Install output:', 'it': 'Output installazione:',
        'es': 'Salida de la instalación:', 'ro': 'Ieșire instalare:',
    },
    'btn_install_playwright': {
        'en': 'Install / Reinstall Playwright', 'it': 'Installa / Reinstalla Playwright',
        'es': 'Instalar / Reinstalar Playwright', 'ro': 'Instalează / Reinstalează Playwright',
    },
    'btn_install_firefox': {
        'en': 'Install / Reinstall Firefox', 'it': 'Installa / Reinstalla Firefox',
        'es': 'Instalar / Reinstalar Firefox', 'ro': 'Instalează / Reinstalează Firefox',
    },
    'btn_recheck': {
        'en': 'Re-check', 'it': 'Verifica di nuovo',
        'es': 'Volver a comprobar', 'ro': 'Reverifică',
    },

    # ── Choose Cover dialog: "current cover in calibre" candidate ───────
    'current_cover_label': {
        'en': 'Current cover (in calibre)', 'it': 'Copertina attuale (in calibre)',
        'es': 'Portada actual (en calibre)', 'ro': 'Coperta actuală (în calibre)',
    },
}


def tr(key, **kwargs):
    """
    Translate `key` into the currently configured interface language.
    Falls back to English, then to the raw key, if a translation is
    missing. Any kwargs are applied via str.format() against the chosen
    string (e.g. tr('choose_cover_button', n=7)).
    """
    lang = 'en'
    try:
        from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
        lang = (prefs.get('interface_language', 'en') or 'en')[:2]
    except Exception:
        pass

    entry = _STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get('en') or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
