#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

from qt.core import QToolButton, QMenu  # type: ignore

from calibre.gui2.actions import InterfaceAction  # type: ignore
from calibre.gui2 import error_dialog, info_dialog, warning_dialog  # type: ignore


class MetadataPlusAction(InterfaceAction):

    name        = 'Metadata++'

    # action_spec = (text, icon_file, tooltip, keyboard_shortcut)
    # icon_file = None means we set it manually in genesis() via get_icons()
    action_spec = ('Metadata++', None,
                   'Fetch rich metadata from 8 sources: Amazon, Kobo, '
                   'Google Books, Open Library, WorldCat, LoC, '
                   'Internet Archive, ISBNdb', None)

    # Show the dropdown arrow on the toolbar button
    popup_type               = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    action_add_menu          = True
    action_menu_clone_qaction = 'Fetch Metadata (All Sources)'

    # Empty = allowed everywhere; this makes it appear in the main toolbar
    dont_add_to    = frozenset()
    dont_remove_from = frozenset()

    def genesis(self):
        # Load icon from the images/ folder inside the ZIP
        icon = get_icons('images/metadata_plus.png')  # type: ignore
        self.qaction.setIcon(icon)

        # Build the dropdown menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        self.create_menu_action(
            self.menu, 'mp-fetch-all',
            'Fetch Metadata (All Sources)',
            icon=None,
            triggered=self.fetch_all,
            description='Parallel fetch from every enabled source')

        self.menu.addSeparator()

        self.create_menu_action(
            self.menu, 'mp-detect-dupes',
            'Detect Duplicates in Selection',
            triggered=self.detect_duplicates)

        self.create_menu_action(
            self.menu, 'mp-repair-isbn',
            'Repair / Validate ISBNs',
            triggered=self.repair_isbns)

        self.create_menu_action(
            self.menu, 'mp-clear-cache',
            'Clear Metadata Cache',
            triggered=self.clear_cache)

        self.menu.addSeparator()

        self.create_menu_action(
            self.menu, 'mp-configure',
            'Configure Metadata+…',
            triggered=self.show_config)

        # Left-click on the toolbar button triggers fetch
        self.qaction.triggered.connect(self.fetch_all)

    def initialization_complete(self):
        pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_ids(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, 'Metadata++ — No selection',
                'Please select one or more books first.', show=True)
            return []
        return list(map(self.gui.library_view.model().id, rows))

    def _refresh_gui(self):
        self.gui.library_view.model().refresh()
        self.gui.tags_view.recount()

    # ── Actions ───────────────────────────────────────────────────────────────

    def fetch_all(self):
        ids = self._selected_ids()
        if not ids:
            return
        from calibre_plugins.metadata_plus.ui.dialogs import MetadataFetchDialog  # type: ignore
        d = MetadataFetchDialog(self.gui, self.gui.current_db, ids)
        if d.exec():
            self._refresh_gui()

    def detect_duplicates(self):
        ids = self._selected_ids()
        if not ids:
            return
        if len(ids) < 2:
            warning_dialog(self.gui, 'Metadata++',
                'Select at least 2 books to check for duplicates.', show=True)
            return
        from calibre_plugins.metadata_plus.engine.fetch_engine import detect_duplicates_in_library  # type: ignore
        from calibre_plugins.metadata_plus.ui.dialogs import DuplicateDialog  # type: ignore
        dupes = detect_duplicates_in_library(self.gui.current_db, ids)
        d = DuplicateDialog(self.gui, self.gui.current_db, dupes)
        d.exec()

    def repair_isbns(self):
        ids = self._selected_ids()
        if not ids:
            return
        from calibre_plugins.metadata_plus.core.isbn_utils import (  # type: ignore
            repair_isbn, normalize_isbn, is_valid_isbn)
        db = self.gui.current_db
        repaired = skipped = 0
        for book_id in ids:
            mi   = db.get_metadata(book_id, index_is_id=True)
            isbn = (mi.identifiers or {}).get('isbn', '')
            if not isbn:
                skipped += 1
                continue
            if is_valid_isbn(isbn):
                norm = normalize_isbn(isbn)
                if norm and norm != isbn:
                    mi.identifiers['isbn'] = norm
                    db.set_metadata(book_id, mi, commit=True)
                    repaired += 1
                continue
            fixed, _ = repair_isbn(isbn)
            if fixed:
                mi.identifiers['isbn'] = normalize_isbn(fixed) or fixed
                db.set_metadata(book_id, mi, commit=True)
                repaired += 1
            else:
                skipped += 1
        info_dialog(self.gui, 'Metadata++ — ISBN Repair',
            '{} ISBN(s) repaired/normalized. {} skipped.'.format(repaired, skipped),
            show=True)
        self._refresh_gui()

    def clear_cache(self):
        from calibre_plugins.metadata_plus.core.cache import MetadataCache  # type: ignore
        MetadataCache().clear()
        info_dialog(self.gui, 'Metadata++', 'Cache cleared.', show=True)

    def show_config(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def apply_settings(self):
        pass
