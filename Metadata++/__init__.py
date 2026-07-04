#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
# Metadata+ Plugin for Calibre 9.x
# Import name: metadata_plus  (matches plugin-import-name-metadata_plus.txt)

__license__   = 'GPL v3'
__copyright__ = '2026, Metadata+ Plugin'
__docformat__ = 'restructuredtext en'

from calibre.customize import InterfaceActionBase  # type: ignore

class MetadataPlusPlugin(InterfaceActionBase):
    name                    = 'Metadata++'
    description             = (
        'Fetch and enrich book metadata from Amazon, Goodreads, Kobo, '
        'Google Books, Open Library, WorldCat, Library of Congress, '
        'Internet Archive, and ISBNdb. Works for any title/author/ISBN '
        'regardless of ebook file format (EPUB, AZW3, AZW, KFX, PDF, MOBI, '
        'etc.) and does not restrict results by language. Includes '
        'best-quality cover fetching (HEAD-probed), best-synopsis selection '
        'across all sources, auto-ISBN discovery, fuzzy matching, ISBN '
        'repair, async downloads, SQLite cache, and duplicate detection.'
    )
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = 'Metadata+ Plugin'
    version                 = (6, 2, 14)
    minimum_calibre_version = (5, 0, 0)

    #: Must match: calibre_plugins.<import-name-from-txt-file>.action:ClassName
    actual_plugin = 'calibre_plugins.metadata_plus.action:MetadataPlusAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.metadata_plus.ui.config import ConfigWidget  # type: ignore
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.commit()
