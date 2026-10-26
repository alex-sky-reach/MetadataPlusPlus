#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

from qt.core import QToolButton, QMenu  # type: ignore

from calibre.gui2.actions import InterfaceAction  # type: ignore
from calibre.gui2 import error_dialog, info_dialog, warning_dialog  # type: ignore

try:
    from calibre_plugins.metadata_plus.core.i18n import tr  # type: ignore
except Exception:
    def tr(key, **kwargs):
        return key


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
        self.qaction.setToolTip(tr('action_tooltip'))

        # Build the dropdown menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self._build_menu()

        # Left-click on the toolbar button triggers fetch
        self.qaction.triggered.connect(self.fetch_all)

    def _build_menu(self):
        """Populate the dropdown menu with translated labels (called once,
        from genesis()). apply_settings() re-texts these same QAction
        objects afterwards rather than rebuilding them — create_menu_action
        registers each action's unique_name with calibre's global keyboard-
        shortcut manager, and calling it twice for the same unique_name
        risks a duplicate-registration error, so the menu structure itself
        is only ever built once per session."""
        self.menu.clear()

        self.act_fetch_all = self.create_menu_action(
            self.menu, 'mp-fetch-all',
            tr('menu_fetch_all'),
            icon=None,
            triggered=self.fetch_all,
            description=tr('menu_fetch_all_desc'))

        self.menu.addSeparator()

        self.act_detect_dupes = self.create_menu_action(
            self.menu, 'mp-detect-dupes',
            tr('menu_detect_dupes'),
            triggered=self.detect_duplicates)

        self.act_repair_isbn = self.create_menu_action(
            self.menu, 'mp-repair-isbn',
            tr('menu_repair_isbn'),
            triggered=self.repair_isbns)

        self.act_clear_cache = self.create_menu_action(
            self.menu, 'mp-clear-cache',
            tr('menu_clear_cache'),
            triggered=self.clear_cache)

        self.menu.addSeparator()

        self.act_configure = self.create_menu_action(
            self.menu, 'mp-configure',
            tr('menu_configure'),
            triggered=self.show_config)

    def initialization_complete(self):
        pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_ids(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, tr('no_selection_title'),
                tr('no_selection_msg'), show=True)
            return []
        return list(map(self.gui.library_view.model().id, rows))

    def _refresh_gui(self):
        self.gui.library_view.model().refresh()
        self.gui.tags_view.recount()
        if hasattr(self.gui, 'current_db') and hasattr(self.gui.current_db, 'clean'):
            self.gui.current_db.clean()
        if hasattr(self.gui, 'book_details'):
            self.gui.book_details.update_details(self.gui.library_view.currentIndex())
        if hasattr(self.gui, 'cover_flow'):
            self.gui.cover_flow.dataChanged()

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
                tr('dupe_min_selection_msg'), show=True)
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
            try:
                mi = db.get_metadata(book_id, index_is_id=True)
            except TypeError:
                mi = db.get_metadata(book_id)
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
        info_dialog(self.gui, tr('isbn_repair_dialog_title'),
            tr('isbn_repair_result_msg', repaired=repaired, skipped=skipped),
            show=True)
        self._refresh_gui()

    def clear_cache(self):
        from calibre_plugins.metadata_plus.core.cache import MetadataCache  # type: ignore
        MetadataCache().clear()
        info_dialog(self.gui, 'Metadata++', tr('cache_cleared_msg'), show=True)

    def show_config(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def apply_settings(self):
        # Called by calibre after the user hits Apply/OK in the plugin's
        # config dialog. Re-text the already-created menu actions in place
        # (see _build_menu's docstring for why we don't rebuild them) so a
        # changed "Interface language" setting is reflected immediately,
        # without needing to restart calibre.
        self.qaction.setToolTip(tr('action_tooltip'))
        if hasattr(self, 'act_fetch_all'):
            self.act_fetch_all.setText(tr('menu_fetch_all'))
            self.act_fetch_all.setStatusTip(tr('menu_fetch_all_desc'))
            self.act_detect_dupes.setText(tr('menu_detect_dupes'))
            self.act_repair_isbn.setText(tr('menu_repair_isbn'))
            self.act_clear_cache.setText(tr('menu_clear_cache'))
            self.act_configure.setText(tr('menu_configure'))
