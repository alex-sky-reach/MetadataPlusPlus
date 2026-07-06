#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

import logging
import datetime

from qt.core import (  # type: ignore
    Qt, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QWidget, QGridLayout, QCheckBox,
    QThread, pyqtSignal, QObject, QGroupBox, QSplitter, QTextBrowser,
    QSizePolicy, QFrame, QTabWidget, QPixmap, QListWidget, QListWidgetItem,
)

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request # type: ignore

from calibre.gui2 import error_dialog, info_dialog, question_dialog  # type: ignore

try:
    from calibre_plugins.metadata_plus.core.i18n import tr  # type: ignore
except Exception:
    def tr(key, **kwargs):  # fallback: return the raw key if i18n.py is missing
        return key


UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'


# ── GUI log handler ────────────────────────────────────────────────────────────

class _QtLogSignaller(QObject):
    """Plain QObject whose sole purpose is to carry a thread-safe pyqtSignal."""
    log_line = pyqtSignal(str)          # HTML-coloured line


class GUILogHandler(logging.Handler):
    """
    Logging handler that forwards every record to the dialog's Log tab
    via a Qt signal (thread-safe).  One instance is shared per dialog.
    """

    # Colour map: level → (background or text colour, bold?)
    _COLOURS = {
        logging.DEBUG:    ('#888888', False),
        logging.INFO:     ('#cccccc', False),
        logging.WARNING:  ('#ffaa00', True),
        logging.ERROR:    ('#ff4444', True),
        logging.CRITICAL: ('#ff0000', True),
    }

    def __init__(self, signaller):
        super().__init__()
        self._signaller = signaller
        self.setFormatter(logging.Formatter('%(asctime)s  %(levelname)-8s  %(message)s',
                                            datefmt='%H:%M:%S'))

    def emit(self, record):
        try:
            msg = self.format(record)
            colour, bold = self._COLOURS.get(record.levelno, ('#cccccc', False))
            safe = (msg
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))
            if bold:
                html = '<span style="color:{};font-weight:bold">{}</span>'.format(colour, safe)
            else:
                html = '<span style="color:{}">{}</span>'.format(colour, safe)
            self._signaller.log_line.emit(html)
        except Exception:
            pass


# ── Worker thread ──────────────────────────────────────────────────────────────

class FetchWorker(QThread):
    progress  = pyqtSignal(int, str)
    book_done = pyqtSignal(int, object, object)   # book_id, mi, result_dict
    finished  = pyqtSignal()
    error_sig = pyqtSignal(str)

    def __init__(self, db, ids, parent=None):
        QThread.__init__(self, parent)
        self.db     = db
        self.ids    = ids
        self._abort = False
        # Signaller used by GUILogHandler — lives on the worker thread but
        # its signal is connected from the main thread after construction.
        self._log_signaller = _QtLogSignaller()

    def abort(self):
        self._abort = True

    def run(self):
        from calibre_plugins.metadata_plus.engine.fetch_engine import fetch_for_book  # type: ignore
        try:
            from calibre_plugins.metadata_plus.providers.browser_fetch import browser_close  # type: ignore
        except Exception:
            browser_close = None

        # Install our GUI handler onto the plugin logger for the duration
        # of this worker's run so every log.* call inside fetch_engine
        # (and providers, fuzzy, etc.) is forwarded to the Log tab.
        plugin_log = logging.getLogger('metadata_plus')
        gui_handler = GUILogHandler(self._log_signaller)
        gui_handler.setLevel(logging.DEBUG)
        plugin_log.addHandler(gui_handler)

        total = len(self.ids)
        ts_start = datetime.datetime.now().strftime('%H:%M:%S')
        self._log_signaller.log_line.emit(
            '<span style="color:#44aaff;font-weight:bold">'
            '════ Metadata++ run started at {} — {} book(s) ════'
            '</span>'.format(ts_start, total)
        )

        for i, book_id in enumerate(self.ids):
            if self._abort:
                self._log_signaller.log_line.emit(
                    '<span style="color:#ffaa00;font-weight:bold">'
                    '⚠  Fetch aborted by user after {}/{} books.'
                    '</span>'.format(i, total)
                )
                break

            mi    = self.db.get_metadata(book_id, index_is_id=True)
            title = mi.title or 'Unknown'

            self.progress.emit(
                int(i / total * 100),
                'Fetching ({}/{}): {}'.format(i + 1, total, title[:55])
            )

            # ── Book header in log ─────────────────────────────────────────
            self._log_signaller.log_line.emit(
                '<span style="color:#aaddff;font-weight:bold">'
                '── Book {}/{}: &quot;{}&quot; (id={}) ──'
                '</span>'.format(i + 1, total,
                                 title[:60].replace('&','&amp;').replace('<','&lt;'),
                                 book_id)
            )

            data  = None
            error = None
            try:
                data = fetch_for_book(self.db, book_id)
            except Exception as e:
                error = 'Error on "{}": {}'.format(title[:40], e)
                self.error_sig.emit(error)

            # ── Book result summary in log ─────────────────────────────────
            if error:
                self._log_signaller.log_line.emit(
                    '<span style="color:#ff4444;font-weight:bold">'
                    '✘  EXCEPTION: {}'
                    '</span>'.format(error.replace('<','&lt;'))
                )
            elif data:
                sources = ', '.join(data.get('sources', []) or ['?'])
                fields  = [k for k in ('title','authors','publisher','pubdate',
                                       'comments','tags','rating','language',
                                       'identifiers','cover_url')
                           if data.get(k)]
                self._log_signaller.log_line.emit(
                    '<span style="color:#66dd66;font-weight:bold">'
                    '✔  Result OK — sources: {}  |  fields: {}'
                    '</span>'.format(
                        sources.replace('<','&lt;'),
                        ', '.join(fields) or 'none'
                    )
                )
            else:
                self._log_signaller.log_line.emit(
                    '<span style="color:#ff8800;font-weight:bold">'
                    '✘  No metadata found for this book (all sources returned nothing).'
                    '</span>'
                )

            self.book_done.emit(book_id, mi, data)

        self.progress.emit(100, 'Done — {} book(s) processed'.format(total))

        ts_end = datetime.datetime.now().strftime('%H:%M:%S')
        self._log_signaller.log_line.emit(
            '<span style="color:#44aaff;font-weight:bold">'
            '════ Run finished at {} ════'
            '</span>'.format(ts_end)
        )

        # Remove our handler so it doesn't accumulate on reruns
        if browser_close is not None:
            try:
                browser_close()
            except Exception:
                pass

        plugin_log.removeHandler(gui_handler)
        self.finished.emit()


# ── Cover Chooser dialog ─────────────────────────────────────────────────────
#
# Mirrors calibre's own built-in "pick the best cover" grid from its identify-
# metadata dialog: every candidate cover collected from every source is shown
# as a thumbnail; the user clicks to preview/select or double-clicks to
# accept immediately. This lets the user override the automatic pick — e.g.
# when a padded/letterboxed Google Books cover was chosen automatically but
# a clean full-bleed Amazon cover is available and clearly better.

class _CoverBatchLoader(QThread):
    """Downloads every candidate cover in parallel and reports back per-item
    (dimensions + quality flags) so the grid can show useful hints (size,
    ⚠ padded, ⚠ blank) without blocking the UI thread."""

    one_loaded = pyqtSignal(int, bytes, object, object)  # index, data, dims, flags

    def __init__(self, candidates, parent=None):
        QThread.__init__(self, parent)
        self.candidates = candidates
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        from calibre_plugins.metadata_plus.providers.providers import (  # type: ignore
            fetch_cover_bytes, measure_image_bytes,
            has_white_border_padding, is_blank_or_placeholder_image)
        import threading as _threading

        def _one(index, cand):
            if self._abort:
                return
            # v6.2.28: a candidate representing calibre's own current cover
            # for this book carries its bytes directly (local_data) rather
            # than a URL — there's nothing to download, and it obviously
            # isn't a network placeholder, so skip straight to measuring it.
            if cand.get('local_data'):
                data = cand['local_data']
                dims = measure_image_bytes(data) if data else (0, 0)
                if not self._abort:
                    self.one_loaded.emit(index, data, dims, {})
                return
            data = fetch_cover_bytes(cand.get('url', ''), timeout=15)
            dims = measure_image_bytes(data) if data else (0, 0)
            flags = {}
            if data:
                try:
                    flags['padded'] = has_white_border_padding(data)
                except Exception:
                    pass
                try:
                    flags['blank'] = is_blank_or_placeholder_image(data, url=cand.get('url', ''))
                except Exception:
                    pass
            if not self._abort:
                self.one_loaded.emit(index, data or b'', dims, flags)

        threads = [_threading.Thread(target=_one, args=(i, c), daemon=True)
                   for i, c in enumerate(self.candidates)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)


class _CoverGridThumb(QFrame):
    """One clickable thumbnail tile in the Cover Chooser grid."""

    clicked       = pyqtSignal()
    doubleClicked = pyqtSignal()

    def __init__(self, candidate, parent=None):
        QFrame.__init__(self, parent)
        self.candidate = candidate
        self.data = b''
        self.setFixedSize(168, 248)
        self.setFrameShape(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        v = QVBoxLayout(self)
        v.setContentsMargins(6, 6, 6, 6)
        self.img_lbl = QLabel(tr('loading'))
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setFixedSize(154, 200)
        v.addWidget(self.img_lbl)
        self.info_lbl = QLabel(candidate.get('source', '?')[:26])
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setStyleSheet('font-size: 10px;')
        v.addWidget(self.info_lbl)

        self.set_selected(False)

    def set_selected(self, selected):
        self.setStyleSheet(
            'QFrame { border: 3px solid #2a82da; background: #223344; }'
            if selected else
            'QFrame { border: 1px solid #777; }'
        )

    def set_pixmap_data(self, data, dims=None, flags=None):
        self.data = data or b''
        pix = QPixmap()
        if data:
            pix.loadFromData(data)
        if pix.isNull():
            self.img_lbl.setText('(no preview)')
            return
        self.img_lbl.setPixmap(pix.scaled(
            154, 200, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

        notes = []
        if dims and dims[0] and dims[1]:
            notes.append('{}×{}'.format(dims[0], dims[1]))
        if flags and flags.get('padded'):
            notes.append('⚠ padded')
        if flags and flags.get('blank'):
            notes.append('⚠ blank')
        base = self.candidate.get('source', '?')[:26]
        self.info_lbl.setText(base + ('\n' + '  '.join(notes) if notes else ''))

    def mousePressEvent(self, ev):
        self.clicked.emit()
        QFrame.mousePressEvent(self, ev)

    def mouseDoubleClickEvent(self, ev):
        self.doubleClicked.emit()
        QFrame.mouseDoubleClickEvent(self, ev)


class CoverChooserDialog(QDialog):
    """
    Modal dialog listing every candidate cover found across all sources for
    one book, as a grid of thumbnails — the manual equivalent of calibre's
    own built-in cover picker.

    candidates: list of {'url': str, 'source': str, 'weight': int}
    current_url: the URL currently selected (pre-highlighted if present)

    After exec() == Accepted: .selected_url and .selected_data (raw bytes,
    already downloaded) hold the user's choice.
    """

    def __init__(self, candidates, current_url=None, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(tr('cover_chooser_title'))
        self.setMinimumSize(760, 560)
        self.candidates    = candidates
        self.selected_url  = current_url
        self.selected_data = b''
        self._tiles = []
        self._loader = None
        self._build_ui()
        self._start_loading()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(QLabel(
            '<b>{}</b>'.format(
                tr('cover_chooser_instructions', n=len(self.candidates)))))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid = QGridLayout(container)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        cols = 4
        for i, cand in enumerate(self.candidates):
            tile = _CoverGridThumb(cand)
            tile.clicked.connect(lambda _checked=False, idx=i: self._select(idx))
            tile.doubleClicked.connect(lambda _checked=False, idx=i: self._select_and_accept(idx))
            self.grid.addWidget(tile, i // cols, i % cols)
            self._tiles.append(tile)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton(tr('btn_use_selected_cover'))
        ok_btn.clicked.connect(self._accept_selected)
        cancel_btn = QPushButton(tr('btn_cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _start_loading(self):
        # Pre-select whichever tile matches the cover currently in use.
        for i, cand in enumerate(self.candidates):
            if cand.get('url') == self.selected_url:
                self._select(i)
                break

        self._loader = _CoverBatchLoader(self.candidates, self)
        self._loader.one_loaded.connect(self._on_one_loaded)
        self._loader.start()

    def _on_one_loaded(self, index, data, dims, flags):
        if index >= len(self._tiles):
            return
        # v6.2.27: hide confirmed blank/placeholder candidates outright
        # instead of merely annotating them — a small "⚠ blank" caption
        # underneath a full-size "image not available" thumbnail is easy
        # to miss, and the whole point of this dialog is to offer only
        # real choices. If the (now-hidden) tile was the pre-selected
        # default, fall through to the first still-visible tile instead.
        if flags and flags.get('blank'):
            self._tiles[index].setVisible(False)
            was_selected = (self.candidates[index].get('url') == self.selected_url)
            if was_selected:
                self.selected_url  = None
                self.selected_data = b''
                for i, tile in enumerate(self._tiles):
                    if tile.isVisible():
                        self._select(i)
                        break
            return
        self._tiles[index].set_pixmap_data(data, dims, flags)
        if (data and self.candidates[index].get('url') == self.selected_url
                and not self.selected_data):
            self.selected_data = data

    def _select(self, index):
        if index < 0 or index >= len(self._tiles):
            return
        for i, tile in enumerate(self._tiles):
            tile.set_selected(i == index)
        self.selected_url  = self.candidates[index].get('url')
        self.selected_data = self._tiles[index].data

    def _select_and_accept(self, index):
        self._select(index)
        self._accept_selected()

    def _accept_selected(self):
        if not self.selected_url:
            error_dialog(self, 'Metadata++', tr('err_select_cover_first'), show=True)
            return
        if not self.selected_data:
            # Background download for this one hasn't finished yet — fetch
            # it synchronously rather than making the user wait/retry.
            from calibre_plugins.metadata_plus.providers.providers import fetch_cover_bytes  # type: ignore
            self.selected_data = fetch_cover_bytes(self.selected_url, timeout=15)
        self.accept()

    def _stop_loader(self):
        if self._loader and self._loader.isRunning():
            self._loader.abort()
            self._loader.wait(3000)

    def reject(self):
        self._stop_loader()
        QDialog.reject(self)

    def closeEvent(self, ev):
        self._stop_loader()
        QDialog.closeEvent(self, ev)


# ── Synopsis Chooser dialog ──────────────────────────────────────────────────

class SynopsisChooserDialog(QDialog):
    """
    Modal dialog listing every candidate description/synopsis found across
    all sources for one book — the synopsis equivalent of CoverChooserDialog
    above, mirroring calibre's own multi-source metadata comparison UI.

    candidates: list of {'text': str, 'source': str, 'lang': str,
                          'score': float, 'weight': int}
    current_text: the text currently selected (pre-highlighted if present)

    After exec() == Accepted: .selected_text holds the user's choice.
    """

    def __init__(self, candidates, current_text=None, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(tr('description_chooser_title'))
        self.setMinimumSize(780, 480)
        self.candidates    = candidates
        self.selected_text = current_text
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(QLabel(
            '<b>{}</b>'.format(
                tr('description_chooser_instructions', n=len(self.candidates)))))

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.list = QListWidget()
        self.list.setMinimumWidth(240)
        start_row = 0
        for i, cand in enumerate(self.candidates):
            text = cand.get('text', '')
            lang = cand.get('lang', '')
            item = QListWidgetItem('{}  —  {} chars{}'.format(
                cand.get('source', '?'), len(text),
                '  [{}]'.format(lang) if lang else ''))
            self.list.addItem(item)
            if text == self.selected_text:
                start_row = i
        splitter.addWidget(self.list)

        self.preview = QTextBrowser()
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self.list.currentRowChanged.connect(self._on_row_changed)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton(tr('btn_use_selected_description'))
        ok_btn.clicked.connect(self._accept_selected)
        cancel_btn = QPushButton(tr('btn_cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

        if self.candidates:
            self.list.setCurrentRow(start_row)

    def _on_row_changed(self, row):
        if row < 0 or row >= len(self.candidates):
            self.preview.setPlainText('')
            return
        cand = self.candidates[row]
        header = '<b>{}:</b> {}'.format(tr('lbl_source'), cand.get('source', '?'))
        if cand.get('lang'):
            header += '&nbsp;&nbsp;<b>{}:</b> {}'.format(tr('lbl_language'), cand['lang'])
        if cand.get('score') is not None:
            header += '&nbsp;&nbsp;<b>{}:</b> {:.1f}'.format(tr('lbl_score'), cand['score'])
        body = (cand.get('text', '')
                .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                .replace('\n', '<br>'))
        self.preview.setHtml('{}<hr>{}'.format(header, body))

    def _accept_selected(self):
        row = self.list.currentRow()
        if row < 0:
            error_dialog(self, 'Metadata++', tr('err_select_description_first'), show=True)
            return
        self.selected_text = self.candidates[row].get('text', '')
        self.accept()


# ── Per-book result panel ──────────────────────────────────────────────────────

class BookResultPanel(QGroupBox):
    # (data_key, i18n string key) — label text is resolved via tr() at
    # build time (not import time) so it reflects the interface language
    # currently set in Options even if it's changed without restarting.
    FIELDS = [
        ('title',       'field_title'),
        ('authors',     'field_authors'),
        ('publisher',   'field_publisher'),
        ('pubdate',     'field_pubdate'),
        ('comments',    'field_description'),
        ('tags',        'field_tags'),
        ('rating',      'field_rating'),
        ('language',    'field_language'),
        ('identifiers', 'field_identifiers'),
    ]

    def __init__(self, book_id, mi, data, parent=None, db=None):
        label = mi.title or 'Book #{}'.format(book_id)
        QGroupBox.__init__(self, label[:80], parent)
        self.book_id    = book_id
        self.mi         = mi
        self.data       = data
        self.db         = db
        self.checkboxes = {}

        # Cover state — kept separate from `checkboxes`/FIELDS because a
        # cover isn't a simple mi.<attr> assignment; MetadataFetchDialog._apply()
        # reads these directly. manual_cover_data is set only when the user
        # explicitly picks a cover via "Choose Cover…", and always wins.
        self.cover_cb          = None
        self.selected_cover_url = (data or {}).get('cover_url') or ''
        self.manual_cover_data  = None
        self._cover_thumb_thread = None

        # Description chooser state
        self._comments_val_lbl = None

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        if not self.data:
            layout.addWidget(QLabel(
                '<i>No metadata found from any source.</i><br>'
                '<small>Check the <b>Log</b> tab above for per-source errors '
                '(e.g. a source timing out or being blocked) — that usually '
                'explains why nothing came back for this book.</small>'))
            return

        sources = ', '.join(self.data.get('sources', []))
        src_lbl = QLabel('<small><b>{}:</b> {}</small>'.format(tr('field_sources'), sources))
        layout.addWidget(src_lbl)

        # ── Cover row ─────────────────────────────────────────────────────
        cover_candidates = self.data.get('cover_candidates') or (
            [{'url': self.data['cover_url'], 'source': (self.data.get('sources') or ['?'])[0],
              'weight': 1}]
            if self.data.get('cover_url') else []
        )
        self._cover_candidates = cover_candidates
        if cover_candidates:
            cover_row = QHBoxLayout()
            self.cover_cb = QCheckBox()
            self.cover_cb.setChecked(True)
            cover_row.addWidget(self.cover_cb)

            lbl_key = QLabel('<b>{}</b>'.format(tr('field_cover')))
            lbl_key.setFixedWidth(100)
            cover_row.addWidget(lbl_key)

            self.cover_thumb = QLabel('…')
            self.cover_thumb.setFixedSize(52, 76)
            self.cover_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cover_thumb.setStyleSheet('border: 1px solid #777;')
            cover_row.addWidget(self.cover_thumb)

            self.cover_source_lbl = QLabel(
                '{} candidate(s) — best: {}'.format(
                    len(cover_candidates), cover_candidates[0].get('source', '?')))
            self.cover_source_lbl.setWordWrap(True)
            cover_row.addWidget(self.cover_source_lbl, 1)

            choose_btn = QPushButton(
                tr('choose_cover_button', n=len(cover_candidates))
                if len(cover_candidates) > 1 else tr('view_cover_button'))
            choose_btn.clicked.connect(self._choose_cover)
            cover_row.addWidget(choose_btn)

            layout.addLayout(cover_row)
            self._load_cover_thumb(self.selected_cover_url)

        grid = QGridLayout()
        grid.setColumnStretch(2, 1)

        row = 0
        for key, label_key in self.FIELDS:
            val = self.data.get(key)
            if not val:
                continue
            label = tr(label_key)
            if isinstance(val, list):
                display = ', '.join(str(v) for v in val)
            elif isinstance(val, dict):
                display = ', '.join('{}:{}'.format(k, v) for k, v in val.items())
            else:
                display = str(val)

            cb = QCheckBox()
            cb.setChecked(True)
            lbl_key = QLabel('<b>{}</b>'.format(label))
            lbl_key.setFixedWidth(100)
            lbl_val = QLabel(display[:300] + ('…' if len(display) > 300 else ''))
            lbl_val.setWordWrap(True)

            grid.addWidget(cb,      row, 0)
            grid.addWidget(lbl_key, row, 1)
            grid.addWidget(lbl_val, row, 2)

            if key == 'comments':
                self._comments_val_lbl = lbl_val
                synopsis_candidates = self.data.get('comment_candidates') or []
                if len(synopsis_candidates) > 1:
                    choose_desc_btn = QPushButton(
                        tr('choose_description_button', n=len(synopsis_candidates)))
                    choose_desc_btn.clicked.connect(self._choose_description)
                    grid.addWidget(choose_desc_btn, row, 3)

            self.checkboxes[key] = cb
            row += 1

        layout.addLayout(grid)

    # ── Cover helpers ─────────────────────────────────────────────────────────

    def _load_cover_thumb(self, url):
        if not url:
            self.cover_thumb.setText('✘')
            return
        self.cover_thumb.setText('…')
        self._cover_thumb_thread = _CoverBatchLoader([{'url': url}], self)
        self._cover_thumb_thread.one_loaded.connect(self._on_thumb_loaded)
        self._cover_thumb_thread.start()

    def _on_thumb_loaded(self, index, data, dims, flags):
        if not data:
            self.cover_thumb.setText('✘')
            return
        pix = QPixmap()
        pix.loadFromData(data)
        if pix.isNull():
            self.cover_thumb.setText('✘')
            return
        self.cover_thumb.setPixmap(pix.scaled(
            52, 76, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def _get_current_cover_bytes(self):
        """
        Return this book's current cover bytes as already stored in
        calibre, or b'' if it has none. Same dual-path approach as
        MetadataFetchDialog._current_cover_quality (get_metadata(get_cover=
        True) first, db.cover() as a fallback for older/newer calibre DB
        APIs) since that's the version confirmed to work reliably across
        calibre releases.
        """
        if not self.db:
            return b''
        try:
            mi = self.db.get_metadata(self.book_id, index_is_id=True, get_cover=True)
            if mi.cover_data and len(mi.cover_data) >= 2 and mi.cover_data[1]:
                return mi.cover_data[1]
        except Exception:
            pass
        try:
            result = self.db.cover(self.book_id, index_is_id=True)
            if result is None:
                return b''
            if hasattr(result, 'read'):
                return result.read() or b''
            if isinstance(result, (bytes, bytearray)):
                return bytes(result)
        except Exception:
            pass
        return b''

    def _choose_cover(self):
        # v6.2.28: offer the book's CURRENT calibre cover as a selectable
        # candidate too, so "none of the fetched covers are better than
        # what I already have" is one click away instead of requiring the
        # user to cancel and leave the existing cover untouched by
        # unchecking the Cover row entirely.
        candidates = list(self._cover_candidates)
        current_data = self._get_current_cover_bytes()
        if current_data:
            candidates = [{
                'url':         'local://current-cover-{}'.format(self.book_id),
                'source':      tr('current_cover_label'),
                'weight':      0,
                'local_data':  current_data,
            }] + candidates
        dlg = CoverChooserDialog(candidates, self.selected_cover_url, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_url:
            self.selected_cover_url = dlg.selected_url
            self.manual_cover_data  = dlg.selected_data or None
            self.data['cover_url']  = dlg.selected_url
            src = next((c.get('source', '?') for c in candidates
                        if c.get('url') == dlg.selected_url), '?')
            self.cover_source_lbl.setText('Manually selected — {}'.format(src))
            if dlg.selected_data:
                pix = QPixmap()
                pix.loadFromData(dlg.selected_data)
                if not pix.isNull():
                    self.cover_thumb.setPixmap(pix.scaled(
                        52, 76, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation))
            else:
                self._load_cover_thumb(dlg.selected_url)

    # ── Description helpers ─────────────────────────────────────────────────

    def _choose_description(self):
        candidates = self.data.get('comment_candidates') or []
        if not candidates:
            return
        dlg = SynopsisChooserDialog(candidates, self.data.get('comments'), self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_text:
            self.data['comments'] = dlg.selected_text
            if self._comments_val_lbl is not None:
                display = dlg.selected_text
                self._comments_val_lbl.setText(
                    display[:300] + ('…' if len(display) > 300 else ''))
            cb = self.checkboxes.get('comments')
            if cb is not None:
                cb.setChecked(True)

    def get_selected(self):
        if not self.data:
            return None
        out = {k: self.data[k] for k, cb in self.checkboxes.items()
               if cb.isChecked() and k in self.data}
        return out or None


# ── Main dialog ────────────────────────────────────────────────────────────────

class MetadataFetchDialog(QDialog):

    def __init__(self, parent, db, ids):
        QDialog.__init__(self, parent)
        self.db      = db
        self.ids     = ids
        self._panels = []
        self._errors  = []
        self.setWindowTitle(tr('fetch_dialog_title'))
        self.setMinimumSize(800, 620)
        self._build_ui()
        self._start()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Progress bar
        self.status_lbl = QLabel(tr('initialising'))
        self.progress   = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.status_lbl)
        root.addWidget(self.progress)

        # Tabs: Results | Log
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Results tab
        results_widget = QWidget()
        rw_layout = QVBoxLayout(results_widget)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.results_layout = QVBoxLayout(self.container)
        self.results_layout.addStretch()
        self.scroll.setWidget(self.container)
        rw_layout.addWidget(self.scroll)
        self.tabs.addTab(results_widget, tr('tab_results'))

        # Log tab — dark background for readability
        self.log_view = QTextBrowser()
        self.log_view.setStyleSheet(
            'background-color: #1e1e1e; color: #cccccc;'
            'font-family: monospace; font-size: 11px;'
        )
        self.log_view.setOpenExternalLinks(False)

        # Toolbar row inside Log tab
        log_widget  = QWidget()
        log_layout  = QVBoxLayout(log_widget)
        log_toolbar = QHBoxLayout()
        self._log_clear_btn = QPushButton(tr('btn_clear_log'))
        self._log_clear_btn.setFixedWidth(90)
        self._log_clear_btn.clicked.connect(self.log_view.clear)
        log_toolbar.addWidget(self._log_clear_btn)
        log_toolbar.addStretch()
        log_layout.addLayout(log_toolbar)
        log_layout.addWidget(self.log_view)
        self.tabs.addTab(log_widget, tr('tab_log'))

        # Buttons
        btn_row = QHBoxLayout()
        self.sel_all_btn  = QPushButton(tr('btn_select_all'))
        self.desel_btn    = QPushButton(tr('btn_deselect_all'))
        self.apply_btn    = QPushButton(tr('btn_apply_selected'))
        self.apply_btn.setEnabled(False)
        self.cancel_btn   = QPushButton(tr('btn_cancel'))
        self.close_btn    = QPushButton(tr('btn_close'))
        self.close_btn.setVisible(False)

        btn_row.addWidget(self.sel_all_btn)
        btn_row.addWidget(self.desel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.close_btn)
        root.addLayout(btn_row)

        self.sel_all_btn.clicked.connect(self._select_all)
        self.desel_btn.clicked.connect(self._deselect_all)
        self.apply_btn.clicked.connect(self._apply)
        self.cancel_btn.clicked.connect(self._cancel)
        self.close_btn.clicked.connect(self.accept)

    # ── Worker wiring ──────────────────────────────────────────────────────────

    def _start(self):
        self.worker = FetchWorker(self.db, self.ids, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.book_done.connect(self._on_book_done)
        self.worker.finished.connect(self._on_finished)
        self.worker.error_sig.connect(self._on_error)
        # Wire the log signaller that lives inside the worker
        self.worker._log_signaller.log_line.connect(self._append_log)
        self.worker.start()

    def _append_log(self, html_line):
        """Append one HTML line to the Log tab and auto-scroll to bottom."""
        self.log_view.append(html_line)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_progress(self, pct, msg):
        self.progress.setValue(pct)
        self.status_lbl.setText(msg)

    def _on_book_done(self, book_id, mi, data):
        # Remove trailing stretch
        count = self.results_layout.count()
        last  = self.results_layout.itemAt(count - 1)
        if last and last.spacerItem():
            self.results_layout.removeItem(last)

        panel = BookResultPanel(book_id, mi, data, db=self.db)
        self.results_layout.addWidget(panel)
        self._panels.append(panel)
        self.results_layout.addStretch()

    def _on_error(self, msg):
        self._errors.append(msg)
        # Error is also forwarded via GUILogHandler, but keep the tab badge
        # updated by bumping the Log tab title
        idx = self.tabs.indexOf(self.tabs.findChild(QWidget, '') or self.tabs.widget(1))
        self.tabs.setTabText(1, 'Log ({} error{})'.format(
            len(self._errors), 's' if len(self._errors) != 1 else ''))

    def _on_finished(self):
        self.apply_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)
        found = sum(1 for p in self._panels if p.data)
        self.status_lbl.setText(
            tr('status_complete', found=found, total=len(self._panels),
               errors=len(self._errors))
        )
        # Always show Log tab badge with final counts
        ok  = found
        nok = len(self._panels) - found
        err = len(self._errors)
        badge = 'Log — ✔{} ✘{}{}'.format(
            ok, nok,
            ' ⚠{}'.format(err) if err else ''
        )
        self.tabs.setTabText(1, badge)

        # Switch to Log tab when there are errors OR when no results found
        if self._errors or found == 0:
            self.tabs.setCurrentIndex(1)

    # ── Bulk select ────────────────────────────────────────────────────────────

    def _select_all(self):
        for p in self._panels:
            for cb in p.checkboxes.values():
                cb.setChecked(True)

    def _deselect_all(self):
        for p in self._panels:
            for cb in p.checkboxes.values():
                cb.setChecked(False)

    # ── Apply ──────────────────────────────────────────────────────────────────

    # ── Cover helpers ──────────────────────────────────────────────────────────

    def _current_cover_quality(self, book_id):
        """
        Return the (pixels, file_bytes) quality tuple for the book's existing
        cover, or (0, 0) if it has none.

        ROOT CAUSE OF COVER-REPLACEMENT BUG (fixed here):
        self.db is gui.current_db which is Calibre's legacy LibraryDatabase2
        object.  In this API, db.cover(book_id, index_is_id=True, as_file=False)
        IGNORES the as_file keyword and always returns a file-like object, not
        bytes.  len() on a file-like object raises TypeError, which the outer
        try/except caught silently, making this method always return (0, 0).
        With existing_q = (0, 0), ANY fetched cover with readable pixel
        dimensions immediately won the comparison — so the plugin replaced
        a 1205×1500 px / 305 KB existing cover with a tiny Google Books
        thumbnail on every single run.

        Fix: read cover bytes through get_metadata(get_cover=True) and
        mi.cover_data, which works identically across all Calibre versions
        (legacy and new cache DB).  mi.cover_data is a (fmt, bytes) tuple
        where fmt is a string like 'jpeg' and bytes is the raw image data.
        Fall back to db.cover() with explicit file-object handling as a
        secondary path for any edge case where get_metadata doesn't populate
        cover_data.
        """
        try:
            from calibre_plugins.metadata_plus.providers.providers import (  # type: ignore
                content_cover_quality)

            raw = None

            # Primary path: get_metadata with get_cover=True — works on all
            # Calibre versions and returns raw bytes in mi.cover_data[1].
            try:
                mi = self.db.get_metadata(book_id, index_is_id=True,
                                          get_cover=True)
                if mi.cover_data and len(mi.cover_data) >= 2:
                    raw = mi.cover_data[1]
            except Exception:
                raw = None

            # Secondary path: db.cover() — handle both file-object (old API)
            # and bytes (new API) returns.
            if not raw:
                try:
                    result = self.db.cover(book_id, index_is_id=True)
                    if result is None:
                        return (0, 0)
                    if hasattr(result, 'read'):
                        raw = result.read()   # file-like object (old API)
                    elif isinstance(result, (bytes, bytearray)):
                        raw = bytes(result)   # already bytes (new API)
                except Exception:
                    return (0, 0)

            if not raw or len(raw) < 500:
                return (0, 0)

            q = content_cover_quality(raw)
            if q[0] > 0:
                return q

            # Measurement still failed after Pillow fallback inside
            # measure_image_bytes — use conservative size-based estimate
            # (2 bytes/pixel lower bound for colour JPEG) so a large
            # existing cover is never accidentally beaten by a small fetch.
            return (len(raw) // 2, len(raw))

        except Exception:
            pass
        return (0, 0)

    def _fetch_best_cover(self, panel):
        """
        Download all candidate covers and return the one with the highest
        quality that is also a clean, trustworthy, full-bleed image (no white
        border padding, not blank/placeholder).

        Strategy
        --------
        1. Build candidate list: cover_url first, then all cover_alts.
        2. Skip audiobook cover URLs (is_audiobook_cover).
        3. Download each candidate (up to 8 MB).
        4. Flag a candidate as "untrustworthy" if either:
             - has_white_border_padding() — white/near-white margins on
               2+ edges (editorial/marketing image with added whitespace), or
             - is_blank_or_placeholder_image() — the whole canvas is a flat
               or near-flat colour / handful of colours (broken thumbnail,
               "no cover available" tile, generic filler image) — this
               catches full-canvas blanks that the border-only check above
               can't see, and non-white placeholder colours.
           Both cases inflate raw pixel count without representing the
           actual book cover — a bigger blank image is not a better cover.
        5. Return the highest cover_quality() candidate among the
           trustworthy ones.
        6. If ALL candidates are untrustworthy, fall back to the best one
           anyway (a bad cover beats no cover at all), but tell the caller
           via the returned `problematic` flag so it can refuse to let this
           candidate silently overwrite a perfectly good existing cover.

        Returns
        -------
        (url, data, problematic) — `problematic` is True when the returned
        candidate was padded/blank and should only replace an existing
        cover if the book currently has none.
        """
        from calibre_plugins.metadata_plus.providers.providers import (  # type: ignore
            fetch_cover_bytes, is_audiobook_cover, cover_quality,
            has_white_border_padding, is_blank_or_placeholder_image)

        if not panel.data:
            return None, b'', False

        candidates = []
        main = panel.data.get('cover_url', '')
        if main:
            candidates.append(main)
        for alt in panel.data.get('cover_alts', []) or []:
            if alt and alt not in candidates:
                candidates.append(alt)

        clean_best_url,  clean_best_data,  clean_best_q  = None, b'', (0, 0)
        bad_best_url,    bad_best_data,    bad_best_q    = None, b'', (0, 0)

        for url in candidates:
            if is_audiobook_cover(url):
                continue
            data = fetch_cover_bytes(url, timeout=15)
            if len(data) < 5000:
                continue
            q = cover_quality(data)
            untrustworthy = (has_white_border_padding(data)
                              or is_blank_or_placeholder_image(data, url=url))
            if untrustworthy:
                # Keep as fallback only
                if q > bad_best_q:
                    bad_best_q, bad_best_url, bad_best_data = q, url, data
            else:
                if q > clean_best_q:
                    clean_best_q, clean_best_url, clean_best_data = q, url, data

        # Prefer a clean, trustworthy cover; fall back to the best bad one
        # only when nothing clean was found at all.
        if clean_best_url:
            return clean_best_url, clean_best_data, False
        return bad_best_url, bad_best_data, True

    # ── Apply ──────────────────────────────────────────────────────────────────

    def _apply(self):
        from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
        from calibre_plugins.metadata_plus.providers.providers import content_cover_quality  # type: ignore
        from calibre_plugins.metadata_plus.core.book_stats import (  # type: ignore
            get_word_count_from_epub, estimate_reading_time,
            get_page_count, build_stats_header)

        applied = 0
        cover_kept = 0
        cover_updated = 0
        cover_skipped = 0   # auto_cover disabled or no URL

        for panel in self._panels:
            if not panel.data:
                continue

            # NOTE: sel can be empty (e.g. the user unchecked every metadata
            # field because they only wanted to change the cover via
            # "Choose Cover…") — that must NOT skip the cover logic below,
            # so we only conditionally touch mi/set_metadata, then always
            # fall through to the cover section.
            sel = panel.get_selected() or {}
            if sel:
                mi = self.db.get_metadata(panel.book_id, index_is_id=True)

                if sel.get('title'):      mi.title     = sel['title']
                if sel.get('authors'):    mi.authors   = list(sel['authors'])
                if sel.get('publisher'):  mi.publisher = sel['publisher']
                if sel.get('comments'):
                    comments = sel['comments']
                    # v6.2.35: optional "Page Count / Word Count / Reading
                    # Time / Tags -----" header, opt-in via prefs. Tags use
                    # whatever is about to be saved this run if the user
                    # fetched/selected new ones, else the book's existing
                    # tags — either way, computed AFTER the user's final
                    # selections, not at fetch time.
                    if prefs.get('include_synopsis_stats_header', False):
                        try:
                            tags = list(sel['tags']) if sel.get('tags') else list(mi.tags or [])
                            word_count = None
                            try:
                                fmts = self.db.formats(panel.book_id, index_is_id=True) or ''
                                fmts = [f.strip().upper() for f in fmts.split(',') if f.strip()]
                                if 'EPUB' in fmts:
                                    epub_path = self.db.format_abspath(
                                        panel.book_id, 'EPUB', index_is_id=True)
                                    if epub_path:
                                        word_count = get_word_count_from_epub(epub_path)
                            except Exception:
                                word_count = None
                            reading_wpm = int(prefs.get('reading_speed_wpm', 200) or 200)
                            reading_time = estimate_reading_time(word_count, wpm=reading_wpm) if word_count else None
                            page_count, page_is_est = get_page_count(mi, word_count=word_count)
                            header = build_stats_header(
                                page_count=page_count, page_is_estimate=page_is_est,
                                word_count=word_count, reading_time=reading_time,
                                tags=tags)
                            if header:
                                comments = header + '\n\n' + comments
                        except Exception:
                            pass  # never let header-building block saving the synopsis itself
                    mi.comments = comments
                if sel.get('tags'):       mi.tags      = list(sel['tags'])
                if sel.get('language'):   mi.language  = sel['language']
                if sel.get('rating'):
                    try:
                        mi.rating = float(sel['rating']) * 2
                    except Exception:
                        pass
                if sel.get('identifiers'):
                    mi.set_identifiers(sel['identifiers'])
                if sel.get('pubdate'):
                    from calibre.utils.date import parse_date  # type: ignore
                    try:
                        mi.pubdate = parse_date(sel['pubdate'])
                    except Exception:
                        pass

                self.db.set_metadata(panel.book_id, mi, commit=True)
                applied += 1

            # ── Cover logic ────────────────────────────────────────────────
            # Rule 0: the per-book cover checkbox (unchecked = leave this
            #         book's cover alone entirely, even if auto_cover is on).
            # Rule 0b: a manually-picked cover (via "Choose Cover…") is the
            #          user's own explicit judgement call — it is applied
            #          unconditionally, the same way calibre's own cover
            #          picker works, bypassing the auto-heuristics below.
            # Rule 1: otherwise, auto_cover must be enabled.
            # Rule 2: Download the best non-audiobook candidate cover via
            #         _fetch_best_cover(), which also flags whether the
            #         winning candidate is "problematic" — i.e. it has white
            #         border padding or is a blank/placeholder image (see
            #         has_white_border_padding() / is_blank_or_placeholder_
            #         image() in providers.py).
            # Rule 3a: If the fetched candidate is problematic, it is NOT a
            #          trustworthy representation of the actual cover, no
            #          matter how large its raw canvas is — a bigger blank
            #          or whitespace-padded image is not a better cover.
            #          Such a candidate is only ever used when the book has
            #          NO existing cover at all; otherwise the existing
            #          cover is always kept untouched, regardless of pixel
            #          counts.
            # Rule 3b: If the fetched candidate is clean, compare it against
            #          the existing cover with content_cover_quality() (more
            #          real content pixels × file bytes wins; ties keep the
            #          existing cover).
            # This means a user's hand-picked (or otherwise legitimate)
            # cover is NEVER silently replaced by a lower-quality, padded,
            # or blank/placeholder image from the internet.

            cover_wanted = panel.cover_cb is None or panel.cover_cb.isChecked()
            if not cover_wanted:
                cover_skipped += 1
                continue

            if panel.manual_cover_data:
                # User explicitly picked this cover via "Choose Cover…" —
                # honour it directly, no heuristic comparison needed.
                self.db.set_cover(panel.book_id, panel.manual_cover_data)
                cover_updated += 1
                continue

            if not prefs.get('auto_cover', True) or not panel.data:
                cover_skipped += 1
                continue

            fetched_url, fetched_data, fetched_problematic = \
                self._fetch_best_cover(panel)

            if not fetched_data:
                cover_skipped += 1
                continue

            existing_q = self._current_cover_quality(panel.book_id)

            if fetched_problematic:
                # Padded / blank / placeholder candidate — only acceptable
                # as a last resort when there's nothing to protect.
                if existing_q == (0, 0):
                    self.db.set_cover(panel.book_id, fetched_data)
                    cover_updated += 1
                else:
                    cover_kept += 1
                continue

            fetched_q = content_cover_quality(fetched_data)

            if fetched_q > existing_q:
                # Fetched cover is strictly better (more pixels, or same
                # pixels but larger file = more detail / less compression).
                self.db.set_cover(panel.book_id, fetched_data)
                cover_updated += 1
            else:
                # Existing cover is at least as good — keep it untouched.
                cover_kept += 1

        # Build a human-friendly summary line for the cover outcome
        cover_parts = []
        if cover_updated:
            cover_parts.append('{} cover(s) updated'.format(cover_updated))
        if cover_kept:
            cover_parts.append('{} existing cover(s) kept (already better)'.format(cover_kept))
        if cover_skipped:
            cover_parts.append('{} cover(s) skipped (no candidate / disabled)'.format(cover_skipped))
        cover_msg = '  |  '.join(cover_parts) if cover_parts else ''

        info_dialog(
            self, 'Metadata++ — Done',
            'Updated {} book(s){}.'.format(
                applied,
                '\n' + cover_msg if cover_msg else ''
            ),
            show=True,
        )
        self.accept()

    def _cancel(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            # Signal the worker to stop processing new books
            self.worker.abort()
            # Disconnect all signals from the worker before we destroy the
            # dialog.  If we call reject() while the worker thread is still
            # running and emitting signals (progress, book_done, log lines…),
            # Qt delivers those signals to the already-deleted C++ objects
            # that back the dialog's widgets, which causes a segfault /
            # Calibre crash.  Disconnecting here makes the remaining emits
            # safe no-ops from Qt's perspective.
            try:
                self.worker.progress.disconnect()
                self.worker.book_done.disconnect()
                self.worker.finished.disconnect()
                self.worker.error_sig.disconnect()
                self.worker._log_signaller.log_line.disconnect()
            except Exception:
                pass  # already disconnected or never connected — harmless
            # Wait briefly for the worker to finish its current network call
            # so we don't pull the rug out mid-write.  25 s is enough for
            # one provider timeout; we don't block the UI because abort()
            # makes the worker skip all remaining books immediately.
            self.worker.wait(25000)
        try:
            from calibre_plugins.metadata_plus.providers.browser_fetch import browser_close  # type: ignore
            browser_close()
        except Exception:
            pass
        self.reject()


# ── Duplicate report dialog ────────────────────────────────────────────────────

class DuplicateDialog(QDialog):
    def __init__(self, parent, db, dupes):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Metadata++ — Duplicate Detection')
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        if not dupes:
            layout.addWidget(QLabel('No duplicates detected in the selected books.'))
        else:
            layout.addWidget(QLabel('<b>{} potential duplicate pair(s) found:</b>'.format(len(dupes))))
            browser = QTextBrowser()
            lines = []
            for id1, id2 in dupes:
                mi1 = db.get_metadata(id1, index_is_id=True)
                mi2 = db.get_metadata(id2, index_is_id=True)
                lines.append(
                    '• <b>{}</b> / <i>{}</i><br>'
                    '  &nbsp;&nbsp;vs<br>'
                    '  <b>{}</b> / <i>{}</i><hr>'.format(
                        mi1.title, ', '.join(mi1.authors),
                        mi2.title, ', '.join(mi2.authors),
                    )
                )
            browser.setHtml('<br>'.join(lines))
            layout.addWidget(browser)
        btn = QPushButton('Close')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
