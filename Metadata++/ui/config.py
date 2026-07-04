#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'

from qt.core import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QGroupBox, QSpinBox, QFormLayout, QLineEdit, QTabWidget,
    QSlider, Qt, QDoubleSpinBox, QComboBox, QPushButton,
    QTextEdit, QPlainTextEdit, QSizePolicy, QMessageBox, QApplication,
    QDialog, QThread, pyqtSignal, QObject, QFont, QTimer,
)
from calibre.utils.config import JSONConfig  # type: ignore

import sys as _sys
# Suppress console windows spawned by subprocess on Windows.
# Without this flag every subprocess.run / Popen call opens a
# black CMD window briefly, which is jarring in a Qt plugin.
_CREATE_NO_WINDOW = 0x08000000 if _sys.platform == 'win32' else 0

prefs = JSONConfig('plugins/metadata_plus2')

# ── Defaults ─────────────────────────────────────────────────────────────────
prefs.defaults.update({
    # ── Global source toggles ─────────────────────────────────────────────────
    # v6.2.13: all sources, including the regional/experimental ones, are now
    # ON by default per explicit user request. IMPORTANT — this does not
    # "fix" them: kobo.com/lafeltrinelli.it/fnac.es/libraccio.it/opac.sbn.it
    # 403- or 404- the server-side requests this plugin makes (confirmed in
    # field logs), and catalogo.bne.es's SRU endpoint URL has changed/moved
    # (404). Those are real, external problems with the target sites, not
    # something a calibre plugin can patch around — turning them on just
    # means they'll show up in "Active sources" and contribute a harmless
    # "empty"/"error" line to the per-source outcome summary instead of being
    # skipped. Untick any of them in Sources if you'd rather skip the wasted
    # request time.
    'use_amazon':          True,
    'use_kobo_com':        True,
    'use_kobo_es':         True,
    'use_kobo_it':         True,
    'use_kobo_fr':         True,
    'use_kobo_de':         True,
    'use_google':          True,
    'use_goodreads':       True,   # NEW v6.2.11 — high-trust synopsis source
    'use_openlibrary':     True,
    'use_worldcat':        True,   # xisbn retired 2016 — fetch_worldcat() is a no-op, see providers.py
    'use_loc':             True,   # loc.gov 403-blocks most IPs
    'use_internetarchive': True,
    'use_isbndb':          True,   # no-op unless an API key is set below
    # ── Spanish-language sources ──────────────────────────────────────────────
    # casadellibro/fnac_es/bne search URLs return 403/404 to server-side
    # requests in the field log (anti-bot blocking, or the search endpoint
    # has moved).
    'use_casadellibro':    True,
    'use_fnac_es':         True,
    'use_bne':             True,
    # ── Italian-language sources ──────────────────────────────────────────────
    # feltrinelli/libraccio/sbn search URLs return 403/404 in the field log
    # for the same reason.
    'use_feltrinelli':     True,
    'use_libraccio':       True,
    'use_sbn':             True,
    # ── French-language sources ───────────────────────────────────────────────
    'use_bnf':             True,
    # ── API keys ──────────────────────────────────────────────────────────────
    'isbndb_key': '',
    'google_api_key': '',
    # ── Source weights (1–10) ─────────────────────────────────────────────────
    'weight_amazon':          8,
    'weight_kobo_com':        7,
    'weight_kobo_es':         7,
    'weight_kobo_it':         7,
    'weight_kobo_fr':         7,
    'weight_kobo_de':         7,
    'weight_google':          9,
    'weight_goodreads':       9,
    'weight_openlibrary':     7,
    'weight_worldcat':        6,
    'weight_loc':             8,
    'weight_internetarchive': 5,
    'weight_isbndb':          8,
    'weight_casadellibro':    7,
    'weight_fnac_es':         6,
    'weight_bne':             7,
    'weight_feltrinelli':     7,
    'weight_libraccio':       6,
    'weight_sbn':             7,
    'weight_bnf':             7,
    # ── Behavior ──────────────────────────────────────────────────────────────
    'timeout':           20,
    'retries':           2,
    'auto_cover':        True,
    'cover_min_size':    200,
    'fuzzy_threshold':   80,
    'cache_days':        7,
    'auto_isbn_repair':  True,
    'normalize_lang':    True,
    'detect_duplicates': True,
    'prefer_language':   'en',
    'log_level':         'INFO',
    # ── Cover quality & ISBN auto-discovery ───────────────────────────────────
    'probe_cover_sizes':       True,
    'cover_probe_timeout':     8,
    'probe_openlibrary_cover': True,
    'auto_isbn_lookup':        True,
    # ── Browser fallback (Playwright / Firefox) ───────────────────────────────
    # opt-in, off by default; gracefully no-ops when playwright is not installed
    'use_browser_fallback': False,
    'browser_headless':     True,
    'browser_timeout':      30,
    # When True (default), Amazon skips the title-search fallback when a direct
    # ASIN or ISBN is already known — avoids opening 5+ browser windows to probe
    # search-result candidates that are often the wrong edition/format.
    'amazon_direct_only':   True,
})


# ── One-time migration: correct stale persisted prefs from older versions ─────
#
# JSONConfig persists *explicit* values to disk the first time they're
# written (e.g. on first plugin-config save, or in some calibre versions,
# as soon as a value is read with a default supplied). v6.2.7 shipped with
# use_kobo_com / use_casadellibro / use_fnac_es / use_bne / use_feltrinelli /
# use_libraccio / use_sbn = True as defaults; anyone who ran that version
# got those written into their on-disk config. Bumping the in-code default
# to False in v6.2.8 does NOT retroactively change an already-persisted
# True value — prefs.get() returns the stored value regardless of what the
# new default is. That's why "Active sources" kept showing kobo_com etc.
# even after upgrading to a build whose default was False.
#
# This migration runs once (gated by a version marker key) and force-resets
# only the specific sources that are currently known to be 403/404-blocked,
# but ONLY if the user never visited the Sources tab to make their own
# explicit choice after the experimental warning was added (heuristic:
# we track our own migration marker, not a generic "did the user touch
# this key" signal, so a user who deliberately re-enables one of these
# after upgrading will not have it silently reset on a later launch).
_MIGRATION_KEY = '_migrated_disable_blocked_sources_v628'
_BLOCKED_SOURCES_RESET = (
    'use_kobo_com', 'use_kobo_es', 'use_kobo_it', 'use_kobo_fr', 'use_kobo_de',
    'use_casadellibro', 'use_fnac_es', 'use_bne', 'use_bnf',
    'use_feltrinelli', 'use_libraccio', 'use_sbn',
    'use_loc',   # loc.gov 403s most IPs; confirmed blocked in field logs too
)

def _migrate_disable_blocked_sources():
    if prefs.get(_MIGRATION_KEY):
        return  # already migrated on a previous launch
    for key in _BLOCKED_SOURCES_RESET:
        if key in prefs:
            del prefs[key]   # fall back to the (now-False) coded default
    prefs[_MIGRATION_KEY] = True

_migrate_disable_blocked_sources()


# v6.2.11: use_worldcat was *not* in _BLOCKED_SOURCES_RESET above, even
# though xisbn.worldcat.org has been dead since 2016 and the coded default
# has been False for a while. Anyone who had use_worldcat=True persisted
# from an even older build than the v6.2.8/9 ones kept it active forever —
# the v628 migration marker above had already fired for them, so simply
# adding 'use_worldcat' to _BLOCKED_SOURCES_RESET would not retroactively
# fix already-migrated installs. This is a separate migration with its own
# marker so it runs exactly once for everyone, including users who already
# ran the v628 migration.
_MIGRATION_KEY_WORLDCAT = '_migrated_disable_worldcat_v6211'

def _migrate_disable_worldcat():
    if prefs.get(_MIGRATION_KEY_WORLDCAT):
        return
    if 'use_worldcat' in prefs:
        del prefs['use_worldcat']  # fall back to the False coded default
    prefs[_MIGRATION_KEY_WORLDCAT] = True

_migrate_disable_worldcat()


# ── Playwright auto-installer ─────────────────────────────────────────────────

class _InstallerThread(QThread):
    """Worker thread that runs a subprocess and streams its combined stdout+stderr."""
    line_ready   = pyqtSignal(str)   # one output line at a time
    finished_ok  = pyqtSignal(bool)  # True = returncode 0

    def __init__(self, cmd_parts, parent=None):
        super().__init__(parent)
        self._cmd = cmd_parts

    def run(self):
        import subprocess
        try:
            proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # merge stderr into stdout
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=_CREATE_NO_WINDOW,
            )
            assert proc.stdout is not None   # guaranteed by stdout=PIPE above
            for line in proc.stdout:
                self.line_ready.emit(line.rstrip())
            proc.wait()
            self.finished_ok.emit(proc.returncode == 0)
        except Exception as exc:
            self.line_ready.emit('ERROR: {}'.format(exc))
            self.finished_ok.emit(False)


class _CheckThread(QThread):
    """
    Runs the 3-step dependency check (Python -> playwright -> Firefox) entirely
    off the main thread so the dialog stays interactive during the full probe
    (the Firefox launch test can take up to 45 s).

    Emits one step_result signal per check so each label row updates
    the moment that step finishes, rather than all-at-once at the end.
    """
    # step_name in {'python', 'playwright', 'firefox'}
    # ok is True (pass) / False (fail) / None (skipped)
    step_result = pyqtSignal(str, object, str)   # step_name, ok, text
    check_done  = pyqtSignal(str, bool)           # python_path (''=>not found), playwright_ok

    def run(self):
        import subprocess, os, sys as _s

        calibre_exe = os.path.normcase(os.path.realpath(_s.executable))

        def _test(cmd):
            """Return Python version string if cmd is a non-Calibre Python 3, else None."""
            try:
                r1 = subprocess.run(
                    cmd + ['-c', 'import sys; print(sys.executable)'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=5, creationflags=_CREATE_NO_WINDOW)
                if r1.returncode != 0:
                    return None
                real = os.path.normcase(os.path.realpath(
                    r1.stdout.decode('utf-8', errors='replace').strip()))
                if real == calibre_exe:
                    return None   # this IS Calibre's embedded Python
                r2 = subprocess.run(
                    cmd + ['--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=5, creationflags=_CREATE_NO_WINDOW)
                if r2.returncode != 0:
                    return None
                return (r2.stdout or r2.stderr).decode('utf-8', errors='replace').strip()
            except Exception:
                return None

        # ── 1. Find system Python ──────────────────────────────────────────────
        py_variants = [
            ['py', '-3.12'], ['py', '-3.11'], ['py', '-3.10'],
            ['py', '-3.13'], ['py', '-3.9'],  ['py', '-3'],
        ]
        simple_candidates = ['python3', 'python', 'py', 'python3.exe', 'python.exe']

        python_path = ''
        ver_str = None
        for parts in py_variants:
            ver_str = _test(parts)
            if ver_str:
                python_path = ' '.join(parts)
                break
        if not python_path:
            for exe in simple_candidates:
                ver_str = _test([exe])
                if ver_str:
                    python_path = exe
                    break

        if python_path:
            self.step_result.emit('python', True,
                                  '{} — {}'.format(python_path, ver_str or ''))
        else:
            self.step_result.emit('python', False,
                                  'No system Python found.  '
                                  'Install Python 3.8+ from https://python.org')
            self.check_done.emit('', False)
            return

        # ── 2. playwright package ──────────────────────────────────────────────
        sys_cmd = python_path.split()
        playwright_ok = False
        try:
            r = subprocess.run(
                sys_cmd + ['-c',
                    'from playwright.sync_api import sync_playwright; '
                    'import playwright; '
                    'print(getattr(playwright, "__version__", "installed"))'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=15, creationflags=_CREATE_NO_WINDOW)
            if r.returncode == 0:
                pw_ver = r.stdout.decode('utf-8', errors='replace').strip()
                playwright_ok = True
                self.step_result.emit('playwright', True, 'v{}'.format(pw_ver))
            else:
                self.step_result.emit('playwright', False,
                                      'Not installed — click "Install / Reinstall Playwright"')
        except Exception as exc:
            self.step_result.emit('playwright', False, str(exc))

        # ── 3. Firefox binary ──────────────────────────────────────────────────
        if playwright_ok:
            try:
                launch_script = (
                    'from playwright.sync_api import sync_playwright; '
                    'p = sync_playwright().start(); '
                    'b = p.firefox.launch(headless=True); '
                    'b.close(); p.stop(); print("ok")')
                r = subprocess.run(
                    sys_cmd + ['-c', launch_script],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=45, creationflags=_CREATE_NO_WINDOW)
                if r.returncode == 0 and b'ok' in r.stdout:
                    self.step_result.emit('firefox', True,
                                          'Launched and closed successfully')
                else:
                    self.step_result.emit('firefox', False,
                                          'Binary missing — click "Install / Reinstall Firefox"')
            except subprocess.TimeoutExpired:
                self.step_result.emit('firefox', False, 'Timed out (>45 s)')
            except Exception as exc:
                self.step_result.emit('firefox', False, str(exc))
        else:
            self.step_result.emit('firefox', None, 'Skipped — playwright not available')

        self.check_done.emit(python_path, playwright_ok)


class _PlaywrightSetupDialog(QDialog):
    """
    Check / install dialog for Playwright + Firefox browser binary.

    Phase 1 — automatic 3-step check on open (same probes as before).
    Phase 2 — four buttons:
      "Install / Reinstall Playwright"  — pip install --force-reinstall playwright
      "Install / Reinstall Firefox"     — playwright install firefox
      "Re-check"                        — rerun the 3-step probe
      "Close"

    Install output is streamed live into a monospace QPlainTextEdit so the
    user can see pip/playwright progress without opening a terminal.
    Both install buttons use force-reinstall, making the action idempotent
    regardless of whether the check passed or failed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Browser Fallback Setup — Playwright / Firefox')
        self.setMinimumWidth(580)
        self.setMinimumHeight(500)
        self._system_python = None   # e.g. 'py -3.11' or 'python'
        self._playwright_ok = False
        self._installer_thread = None
        self._check_thread = None    # _CheckThread running in background

        layout = QVBoxLayout(self)

        # ── Status panel ──────────────────────────────────────────────────────
        status_grp = QGroupBox('Dependency Status')
        status_form = QFormLayout(status_grp)
        self._lbl_python     = QLabel('Checking...')
        self._lbl_playwright = QLabel('Checking...')
        self._lbl_firefox    = QLabel('Checking...')
        self._lbl_python.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_playwright.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_firefox.setTextFormat(Qt.TextFormat.RichText)
        status_form.addRow('System Python:', self._lbl_python)
        status_form.addRow('Playwright package:', self._lbl_playwright)
        status_form.addRow('Firefox browser binary:', self._lbl_firefox)
        layout.addWidget(status_grp)

        # ── Live output area ──────────────────────────────────────────────────
        layout.addWidget(QLabel('Install output:'))
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        mono = QFont('Courier New', 9)
        mono.setFixedPitch(True)
        self._output.setFont(mono)
        self._output.setMinimumHeight(200)
        layout.addWidget(self._output)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._btn_install_pw = QPushButton('Install / Reinstall Playwright')
        self._btn_install_pw.setToolTip(
            'Runs:  <python> -m pip install --force-reinstall playwright')
        self._btn_install_pw.clicked.connect(self._install_playwright)

        self._btn_install_ff = QPushButton('Install / Reinstall Firefox')
        self._btn_install_ff.setToolTip(
            'Runs:  <python> -m playwright install firefox')
        self._btn_install_ff.clicked.connect(self._install_firefox)

        self._btn_recheck = QPushButton('Re-check')
        self._btn_recheck.clicked.connect(self._run_check)

        self._btn_close = QPushButton('Close')
        self._btn_close.clicked.connect(self.accept)

        btn_row.addWidget(self._btn_install_pw)
        btn_row.addWidget(self._btn_install_ff)
        btn_row.addWidget(self._btn_recheck)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_close)
        layout.addLayout(btn_row)

        # Defer the check until after the dialog is fully painted.
        # QTimer.singleShot(0) posts the call to the event queue so the
        # dialog renders its "Checking..." labels before any subprocess runs.
        QTimer.singleShot(0, self._run_check)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _set_label(self, lbl, ok, text):
        if ok is True:
            lbl.setText(
                '<span style="color:#22bb44;font-weight:bold">OK</span>'
                '  <span style="color:#cccccc">{}</span>'.format(text))
        elif ok is False:
            lbl.setText(
                '<span style="color:#ee4444;font-weight:bold">FAIL</span>'
                '  <span style="color:#cccccc">{}</span>'.format(text))
        else:
            lbl.setText(
                '<span style="color:#888888">{}</span>'.format(text))

    def _run_check(self):
        """Start the background 3-step dependency check (non-blocking)."""
        if self._check_thread and self._check_thread.isRunning():
            return
        self._system_python = None
        self._playwright_ok = False
        self._set_label(self._lbl_python,     None, 'Checking...')
        self._set_label(self._lbl_playwright, None, 'Checking...')
        self._set_label(self._lbl_firefox,    None, 'Checking...')
        for btn in (self._btn_install_pw, self._btn_install_ff,
                    self._btn_recheck, self._btn_close):
            btn.setEnabled(False)
        self._check_thread = _CheckThread(self)
        self._check_thread.step_result.connect(self._on_step_result)
        self._check_thread.check_done.connect(self._on_check_done)
        self._check_thread.start()

    def _on_step_result(self, step, ok, text):
        """Slot: update one label row as each check step finishes."""
        lbl = {'python':     self._lbl_python,
               'playwright': self._lbl_playwright,
               'firefox':    self._lbl_firefox}.get(step)
        if lbl is not None:
            self._set_label(lbl, ok, text)

    def _on_check_done(self, python_path, playwright_ok):
        """Slot: fired by _CheckThread when all three steps are done."""
        self._system_python = python_path or None
        self._playwright_ok = playwright_ok
        self._btn_install_pw.setEnabled(bool(self._system_python))
        self._btn_install_ff.setEnabled(bool(self._system_python))
        self._btn_recheck.setEnabled(True)
        self._btn_close.setEnabled(True)

    def _run_install(self, cmd_parts, label):
        """Launch installer thread; streams output to the text area."""
        if self._installer_thread and self._installer_thread.isRunning():
            return
        self._output.appendPlainText('\n--- {} ---'.format(label))
        self._output.appendPlainText('$ ' + ' '.join(cmd_parts))
        self._output.appendPlainText('')
        # Disable all buttons while install runs
        for btn in (self._btn_install_pw, self._btn_install_ff,
                    self._btn_recheck, self._btn_close):
            btn.setEnabled(False)

        thread = _InstallerThread(cmd_parts, self)
        thread.line_ready.connect(self._on_output_line)
        thread.finished_ok.connect(self._on_install_done)
        thread.start()
        self._installer_thread = thread

    def _on_output_line(self, line):
        self._output.appendPlainText(line)
        # Auto-scroll to bottom
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_install_done(self, success):
        self._output.appendPlainText(
            '\n--- Completed OK ---' if success else '\n--- FAILED ---')
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())
        # Re-enable buttons and auto-recheck
        self._btn_install_pw.setEnabled(True)
        self._btn_install_ff.setEnabled(True)
        self._btn_recheck.setEnabled(True)
        self._btn_close.setEnabled(True)
        self._run_check()

    def _install_playwright(self):
        if not self._system_python:
            return
        sys_cmd = self._system_python.split()
        self._run_install(
            sys_cmd + ['-m', 'pip', 'install', '--force-reinstall', 'playwright'],
            'Installing playwright (force-reinstall)...')

    def _install_firefox(self):
        if not self._system_python:
            return
        sys_cmd = self._system_python.split()
        self._run_install(
            sys_cmd + ['-m', 'playwright', 'install', 'firefox'],
            'Installing Firefox browser binary...')


class WeightSlider(QWidget):
    def __init__(self, label, key, parent=None):
        QWidget.__init__(self, parent)
        self.key = key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.lbl = QLabel(label)
        self.lbl.setFixedWidth(160)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 10)
        self.slider.setValue(prefs[key])
        self.slider.setFixedWidth(120)
        self.val_lbl = QLabel(str(prefs[key]))
        self.val_lbl.setFixedWidth(20)
        self.slider.valueChanged.connect(lambda v: self.val_lbl.setText(str(v)))
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)
        layout.addWidget(self.val_lbl)
        layout.addStretch()

    def value(self):
        return self.slider.value()


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Tab 1: Sources ────────────────────────────────────────────────────
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)

        # ── Global sources ────────────────────────────────────────────────────
        global_grp = QGroupBox('Global Sources  (always active)')
        global_form = QFormLayout(global_grp)
        self.src_checks = {}
        global_sources = [
            ('use_amazon',          'Amazon  (routes to .es / .it / .fr / .de automatically)'),
            ('use_goodreads',       'Goodreads  (best-effort scrape — usually the richest, cleanest synopsis)'),
            ('use_kobo_com',        'Kobo  (kobo.com — currently 403-blocks server requests; off by default)'),
            ('use_google',          'Google Books'),
            ('use_openlibrary',     'Open Library'),
            ('use_internetarchive', 'Internet Archive'),
            ('use_loc',             'Library of Congress  (may 403-block some IPs)'),
            ('use_worldcat',        'WorldCat  (xISBN retired 2016 — usually empty)'),
            ('use_isbndb',          'ISBNdb  (requires API key below)'),
        ]
        for key, label in global_sources:
            cb = QCheckBox()
            cb.setChecked(prefs[key])
            self.src_checks[key] = cb
            global_form.addRow(label, cb)
        src_layout.addWidget(global_grp)

        # ── Language-specific sources ─────────────────────────────────────────
        lang_grp = QGroupBox(
            'Language-Specific Sources\n'
            '✦ Auto-activated when the book\'s language matches — '
            'tick to always query regardless of language')
        lang_form = QFormLayout(lang_grp)

        lang_sources = [
            # Spanish — marked experimental: search endpoints currently
            # 403/404 to server-side requests as of this build; left in for
            # manual testing since these sites change frequently.
            ('use_casadellibro', '🇪🇸  Casa del Libro  (casadellibro.com)  [experimental — currently blocked]'),
            ('use_fnac_es',      '🇪🇸🇫🇷 FNAC  (fnac.es)  [experimental — currently blocked]'),
            ('use_bne',          '🇪🇸  Biblioteca Nacional de España  (bne.es)  [experimental — currently blocked]'),
            ('use_kobo_es',      '🇪🇸  Kobo España  (kobo.com/es)  [experimental — currently blocked]'),
            # Italian
            ('use_feltrinelli',  '🇮🇹  Feltrinelli  (lafeltrinelli.it)  [experimental — currently blocked]'),
            ('use_libraccio',    '🇮🇹  Libraccio / IBS  (libraccio.it)  [experimental — currently blocked]'),
            ('use_sbn',          '🇮🇹  SBN — Servizio Bibliotecario Nazionale  (sbn.it)  [experimental — currently blocked]'),
            ('use_kobo_it',      '🇮🇹  Kobo Italia  (kobo.com/it)  [experimental — currently blocked]'),
            # French
            ('use_bnf',          '🇫🇷  BNF — Bibliothèque nationale de France  (data.bnf.fr)  [experimental — currently blocked]'),
            ('use_kobo_fr',      '🇫🇷  Kobo France  (kobo.com/fr)  [experimental — currently blocked]'),
            # German
            ('use_kobo_de',      '🇩🇪  Kobo Deutschland  (kobo.com/de)  [experimental — currently blocked]'),
        ]
        for key, label in lang_sources:
            cb = QCheckBox()
            cb.setChecked(prefs[key])
            self.src_checks[key] = cb
            note = QLabel(label)
            note.setWordWrap(True)
            lang_form.addRow(note, cb)
        src_layout.addWidget(lang_grp)

        # ── API Keys ──────────────────────────────────────────────────────────
        key_grp = QGroupBox('API Keys')
        key_form = QFormLayout(key_grp)
        self.google_api_key = QLineEdit(prefs['google_api_key'])
        self.google_api_key.setPlaceholderText(
            'Optional — raises the Google Books quota well above the shared anonymous limit')
        self.google_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        key_form.addRow('Google Books API Key:', self.google_api_key)
        self.isbndb_key = QLineEdit(prefs['isbndb_key'])
        self.isbndb_key.setPlaceholderText('Enter ISBNdb API key…')
        self.isbndb_key.setEchoMode(QLineEdit.EchoMode.Password)
        key_form.addRow('ISBNdb API Key:', self.isbndb_key)
        src_layout.addWidget(key_grp)
        src_layout.addStretch()
        tabs.addTab(src_tab, 'Sources')

        # ── Tab 2: Weights ────────────────────────────────────────────────────
        wt_tab = QWidget()
        wt_layout = QVBoxLayout(wt_tab)

        wt_global_grp = QGroupBox('Global Source Weights  (higher = preferred)')
        wt_global_inner = QVBoxLayout(wt_global_grp)
        self.weight_widgets = {}
        global_weight_sources = [
            ('weight_amazon',          'Amazon'),
            ('weight_goodreads',       'Goodreads'),
            ('weight_kobo_com',        'Kobo  (kobo.com — global)'),
            ('weight_google',          'Google Books'),
            ('weight_openlibrary',     'Open Library'),
            ('weight_internetarchive', 'Internet Archive'),
            ('weight_loc',             'Library of Congress'),
            ('weight_worldcat',        'WorldCat'),
            ('weight_isbndb',          'ISBNdb'),
        ]
        for key, label in global_weight_sources:
            w = WeightSlider(label, key)
            self.weight_widgets[key] = w
            wt_global_inner.addWidget(w)
        wt_layout.addWidget(wt_global_grp)

        wt_lang_grp = QGroupBox('Language-Specific Source Weights')
        wt_lang_inner = QVBoxLayout(wt_lang_grp)
        lang_weight_sources = [
            ('weight_casadellibro', '🇪🇸 Casa del Libro'),
            ('weight_fnac_es',      '🇪🇸🇫🇷 FNAC'),
            ('weight_bne',          '🇪🇸 BNE'),
            ('weight_kobo_es',      '🇪🇸 Kobo España'),
            ('weight_feltrinelli',  '🇮🇹 Feltrinelli'),
            ('weight_libraccio',    '🇮🇹 Libraccio'),
            ('weight_sbn',          '🇮🇹 SBN'),
            ('weight_kobo_it',      '🇮🇹 Kobo Italia'),
            ('weight_bnf',          '🇫🇷 BNF'),
            ('weight_kobo_fr',      '🇫🇷 Kobo France'),
            ('weight_kobo_de',      '🇩🇪 Kobo Deutschland'),
        ]
        for key, label in lang_weight_sources:
            w = WeightSlider(label, key)
            self.weight_widgets[key] = w
            wt_lang_inner.addWidget(w)
        wt_layout.addWidget(wt_lang_grp)
        wt_layout.addStretch()
        tabs.addTab(wt_tab, 'Weights')

        # ── Tab 3: Options ────────────────────────────────────────────────────
        opt_tab = QWidget()
        opt_layout = QVBoxLayout(opt_tab)

        net_grp = QGroupBox('Network')
        net_form = QFormLayout(net_grp)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 120)
        self.spin_timeout.setValue(prefs['timeout'])
        self.spin_timeout.setSuffix(' s')
        self.spin_retries = QSpinBox()
        self.spin_retries.setRange(0, 5)
        self.spin_retries.setValue(prefs['retries'])
        net_form.addRow('Timeout:', self.spin_timeout)
        net_form.addRow('Retries per source:', self.spin_retries)
        opt_layout.addWidget(net_grp)

        meta_grp = QGroupBox('Metadata')
        meta_form = QFormLayout(meta_grp)
        self.cb_isbn_repair  = QCheckBox('Auto-repair / validate ISBN')
        self.cb_isbn_repair.setChecked(prefs['auto_isbn_repair'])
        self.cb_normalize    = QCheckBox('Normalize multilingual metadata')
        self.cb_normalize.setChecked(prefs['normalize_lang'])
        self.cb_duplicates   = QCheckBox('Detect duplicates after fetch')
        self.cb_duplicates.setChecked(prefs['detect_duplicates'])
        self.spin_fuzzy = QSpinBox()
        self.spin_fuzzy.setRange(50, 100)
        self.spin_fuzzy.setValue(prefs['fuzzy_threshold'])
        self.spin_fuzzy.setSuffix('%')
        self.combo_lang = QComboBox()
        langs = [('en','English'),('it','Italian'),('de','German'),
                 ('fr','French'),('es','Spanish'),('pt','Portuguese'),
                 ('ja','Japanese'),('nl','Dutch'),('pl','Polish')]
        for code, name in langs:
            self.combo_lang.addItem(name, code)
        idx = self.combo_lang.findData(prefs['prefer_language'])
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        meta_form.addRow(self.cb_isbn_repair)
        meta_form.addRow(self.cb_normalize)
        meta_form.addRow(self.cb_duplicates)
        meta_form.addRow('Fuzzy match threshold:', self.spin_fuzzy)
        meta_form.addRow('Preferred language:', self.combo_lang)
        opt_layout.addWidget(meta_grp)

        cover_grp = QGroupBox('Cover Art')
        cover_form = QFormLayout(cover_grp)
        self.cb_cover = QCheckBox('Auto-download best cover')
        self.cb_cover.setChecked(prefs['auto_cover'])
        self.spin_cover_min = QSpinBox()
        self.spin_cover_min.setRange(50, 1000)
        self.spin_cover_min.setValue(prefs['cover_min_size'])
        self.spin_cover_min.setSuffix(' px')
        self.cb_probe_covers = QCheckBox(
            'Probe cover file sizes (HEAD request) — picks highest-resolution image')
        self.cb_probe_covers.setChecked(prefs['probe_cover_sizes'])
        self.cb_probe_ol_cover = QCheckBox(
            'Direct Open Library cover lookup by ISBN')
        self.cb_probe_ol_cover.setChecked(prefs['probe_openlibrary_cover'])
        self.spin_probe_timeout = QSpinBox()
        self.spin_probe_timeout.setRange(2, 30)
        self.spin_probe_timeout.setValue(prefs['cover_probe_timeout'])
        self.spin_probe_timeout.setSuffix(' s')
        cover_form.addRow(self.cb_cover)
        cover_form.addRow('Min cover dimension:', self.spin_cover_min)
        cover_form.addRow(self.cb_probe_covers)
        cover_form.addRow(self.cb_probe_ol_cover)
        cover_form.addRow('Cover probe timeout:', self.spin_probe_timeout)
        opt_layout.addWidget(cover_grp)

        isbn_grp = QGroupBox('ISBN Auto-Discovery')
        isbn_form = QFormLayout(isbn_grp)
        self.cb_isbn_lookup = QCheckBox(
            'Auto-discover ISBN from ASIN (Amazon dp/ page scrape) when missing')
        self.cb_isbn_lookup.setChecked(prefs['auto_isbn_lookup'])
        isbn_form.addRow(self.cb_isbn_lookup)
        opt_layout.addWidget(isbn_grp)

        cache_grp = QGroupBox('Cache')
        cache_form = QFormLayout(cache_grp)
        self.spin_cache = QSpinBox()
        self.spin_cache.setRange(0, 90)
        self.spin_cache.setValue(prefs['cache_days'])
        self.spin_cache.setSuffix(' days  (0 = disabled)')
        cache_form.addRow('Cache TTL:', self.spin_cache)
        btn_clear = QPushButton('Clear Cache Now')
        btn_clear.clicked.connect(self._clear_cache)
        cache_form.addRow(btn_clear)
        opt_layout.addWidget(cache_grp)

        browser_grp = QGroupBox('Browser Fallback (Playwright / Firefox)')
        browser_form = QFormLayout(browser_grp)
        self.cb_browser_fallback = QCheckBox(
            'Use Firefox browser as fallback for bot-blocked sources '
            '(Amazon, Kobo, Casa del Libro, FNAC, Feltrinelli, Libraccio, SBN, Goodreads)')
        self.cb_browser_fallback.setChecked(prefs['use_browser_fallback'])
        self.cb_browser_headless = QCheckBox(
            'Run browser headless (no visible Firefox window)')
        self.cb_browser_headless.setChecked(prefs['browser_headless'])
        self.cb_amazon_direct_only = QCheckBox(
            'Amazon: direct lookup only (skip title-search fallback when ASIN/ISBN is known) '
            '-- prevents multiple browser windows opening for search candidates')
        self.cb_amazon_direct_only.setChecked(prefs['amazon_direct_only'])
        self.spin_browser_timeout = QSpinBox()
        self.spin_browser_timeout.setRange(10, 120)
        self.spin_browser_timeout.setValue(prefs['browser_timeout'])
        self.spin_browser_timeout.setSuffix(' s')
        btn_playwright = QPushButton('Check / Install Playwright')
        btn_playwright.clicked.connect(self._check_playwright)
        browser_form.addRow(self.cb_browser_fallback)
        browser_form.addRow(self.cb_browser_headless)
        browser_form.addRow(self.cb_amazon_direct_only)
        browser_form.addRow('Browser page timeout:', self.spin_browser_timeout)
        browser_form.addRow(btn_playwright)
        opt_layout.addWidget(browser_grp)

        opt_layout.addStretch()
        tabs.addTab(opt_tab, 'Options')

        # ── Tab 4: Diagnostics ────────────────────────────────────────────────
        diag_tab = QWidget()
        diag_layout = QVBoxLayout(diag_tab)
        log_grp = QGroupBox('Logging')
        log_form = QFormLayout(log_grp)
        self.combo_log = QComboBox()
        for lvl in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            self.combo_log.addItem(lvl)
        self.combo_log.setCurrentText(prefs['log_level'])
        log_form.addRow('Log level:', self.combo_log)
        diag_layout.addWidget(log_grp)

        self.diag_log = QTextEdit()
        self.diag_log.setReadOnly(True)
        self.diag_log.setPlaceholderText('Plugin log output appears here…')
        self.diag_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        diag_layout.addWidget(QLabel('Recent log:'))
        diag_layout.addWidget(self.diag_log)
        self._load_log()
        tabs.addTab(diag_tab, 'Diagnostics')

    def _check_playwright(self):
        """Open the Playwright setup dialog (check + auto-install with live output)."""
        _PlaywrightSetupDialog(self).exec()

    def _clear_cache(self):
        try:
            from calibre_plugins.metadata_plus.core.cache import MetadataCache  # type: ignore
            MetadataCache().clear()
        except Exception:
            pass

    def _load_log(self):
        try:
            import os
            from calibre.utils.config import config_dir  # type: ignore
            log_path = os.path.join(config_dir, 'metadata_plus.log')
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                self.diag_log.setPlainText(''.join(lines[-200:]))
        except Exception:
            pass

    def commit(self):
        for key, cb in self.src_checks.items():
            prefs[key] = cb.isChecked()
        for key, w in self.weight_widgets.items():
            prefs[key] = w.value()
        prefs['isbndb_key']       = self.isbndb_key.text().strip()
        prefs['google_api_key']   = self.google_api_key.text().strip()
        prefs['timeout']          = self.spin_timeout.value()
        prefs['retries']          = self.spin_retries.value()
        prefs['auto_isbn_repair'] = self.cb_isbn_repair.isChecked()
        prefs['normalize_lang']   = self.cb_normalize.isChecked()
        prefs['detect_duplicates']= self.cb_duplicates.isChecked()
        prefs['fuzzy_threshold']  = self.spin_fuzzy.value()
        prefs['prefer_language']  = self.combo_lang.currentData()
        prefs['auto_cover']       = self.cb_cover.isChecked()
        prefs['cover_min_size']   = self.spin_cover_min.value()
        prefs['probe_cover_sizes']       = self.cb_probe_covers.isChecked()
        prefs['probe_openlibrary_cover'] = self.cb_probe_ol_cover.isChecked()
        prefs['cover_probe_timeout']     = self.spin_probe_timeout.value()
        prefs['auto_isbn_lookup']        = self.cb_isbn_lookup.isChecked()
        prefs['cache_days']              = self.spin_cache.value()
        prefs['use_browser_fallback']    = self.cb_browser_fallback.isChecked()
        prefs['browser_headless']        = self.cb_browser_headless.isChecked()
        prefs['amazon_direct_only']      = self.cb_amazon_direct_only.isChecked()
        prefs['browser_timeout']         = self.spin_browser_timeout.value()
        prefs['log_level']               = self.combo_log.currentText()
