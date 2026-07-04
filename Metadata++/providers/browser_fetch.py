#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""
browser_fetch.py -- Playwright/Firefox browser layer -- MetadataPlusPlus

Runs Playwright in a system-Python subprocess and reuses one Firefox
browser/context/page across browser_get() calls.  This keeps visible Firefox
usage to one window per calibre/plugin process instead of one window per URL.
"""

import atexit
import json
import os
import subprocess
import sys
import tempfile
import threading

# Suppress console windows created by subprocess calls on Windows.
_CREATE_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0

# ── System Python discovery ────────────────────────────────────────────────────
_find_lock             = threading.Lock()
_system_python_cmd     = None
_system_python_checked = False

# ── Browser worker state ───────────────────────────────────────────────────────
_browser_semaphore = threading.Semaphore(1)
_worker_lock       = threading.Lock()
_worker_proc       = None
_worker_key        = None
_worker_script     = None

# Use the same UA a real Firefox 125 on Windows 10 x64 sends.
_FIREFOX_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) '
    'Gecko/20100101 Firefox/125.0'
)

_STEALTH_JS = (
    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    "if(navigator.plugins.length===0){"
    "Object.defineProperty(navigator,'plugins',{get:()=>{"
    "const a=[1,2,3];a.item=i=>a[i];a.namedItem=()=>null;a.refresh=()=>{};return a;"
    "}});"
    "}"
    "try{Object.defineProperty(navigator,'languages',{"
    "get:()=>(navigator.language?[navigator.language,'en']:['en-US','en'])"
    "});}catch(e){}"
    "try{delete window.__playwright;}catch(e){}"
    "try{delete window.__pw_manual;}catch(e){}"
    "try{delete window.__PW_inspect;}catch(e){}"
)

_FF_PREFS = {
    'media.peerconnection.enabled':              False,
    'privacy.resistFingerprinting':              False,
    'app.update.auto':                           False,
    'app.update.enabled':                        False,
    'toolkit.telemetry.enabled':                 False,
    'datareporting.healthreport.uploadEnabled':  False,
}


def _find_system_python_with_playwright():
    """Find and cache a non-Calibre system Python with playwright installed."""
    global _system_python_cmd, _system_python_checked

    if _system_python_checked:
        return _system_python_cmd

    with _find_lock:
        if _system_python_checked:
            return _system_python_cmd
        _system_python_checked = True

        calibre_exe  = os.path.normcase(os.path.realpath(sys.executable))
        check_script = 'from playwright.sync_api import sync_playwright; print("ok")'

        py_launcher_variants = [
            ['py', '-3.12'], ['py', '-3.11'], ['py', '-3.10'],
            ['py', '-3.13'], ['py', '-3.9'],  ['py', '-3'],
        ]
        simple_candidates = ['python3', 'python', 'py', 'python3.exe', 'python.exe']

        def _test(cmd_parts):
            try:
                id_r = subprocess.run(
                    cmd_parts + ['-c', 'import sys; print(sys.executable)'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
                    creationflags=_CREATE_NO_WINDOW,
                )
                if id_r.returncode == 0:
                    real = os.path.normcase(os.path.realpath(
                        id_r.stdout.decode('utf-8', errors='replace').strip()
                    ))
                    if real == calibre_exe:
                        return False
                r = subprocess.run(
                    cmd_parts + ['-c', check_script],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
                    creationflags=_CREATE_NO_WINDOW,
                )
                return r.returncode == 0
            except (OSError, subprocess.TimeoutExpired, Exception):
                return False

        for parts in py_launcher_variants:
            if _test(parts):
                _system_python_cmd = parts
                return parts

        for exe in simple_candidates:
            if _test([exe]):
                _system_python_cmd = [exe]
                return [exe]

        return None


def is_browser_available():
    """Return True if a system Python with playwright is reachable."""
    return _find_system_python_with_playwright() is not None


def browser_get(url, headers=None, timeout=30, log=None):
    """
    Fetch `url` using a persistent Playwright Firefox worker.
    Returns rendered HTML as str, or None on failure.
    """
    sys_python = _find_system_python_with_playwright()
    if sys_python is None:
        if log:
            log.warning(
                'browser_fetch: no system Python with playwright found. '
                'Install commands:\n'
                '  1.  pip install playwright\n'
                '  2.  playwright install firefox'
            )
        return None

    headless = False
    try:
        from calibre_plugins.metadata_plus.ui.config import prefs  # type: ignore
        headless = bool(prefs.get('browser_headless', True))
        timeout  = int(prefs.get('browser_timeout', timeout))
    except Exception:
        pass

    hdrs        = headers or {}
    accept_lang = hdrs.get('Accept-Language', 'en-US,en;q=0.9')
    locale      = accept_lang.split(',')[0].strip()
    timeout_ms  = int(timeout * 1000)

    extra_headers = {
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;'
            'q=0.9,image/avif,image/webp,*/*;q=0.8'
        ),
        'Accept-Language':           accept_lang,
        'Accept-Encoding':           'gzip, deflate, br',
        'Cache-Control':             'no-cache',
        'Pragma':                    'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'DNT':                       '1',
        'Sec-Fetch-Dest':            'document',
        'Sec-Fetch-Mode':            'navigate',
        'Sec-Fetch-Site':            'none',
        'Sec-Fetch-User':            '?1',
    }

    with _browser_semaphore:
        html = _worker_fetch(sys_python, url, extra_headers, locale,
                             headless, timeout_ms, log)
    return html


def _worker_fetch(sys_python, url, extra_headers, locale, headless, timeout_ms, log=None):
    proc = _ensure_worker(sys_python, headless, locale, extra_headers, log)
    if proc is None:
        return None

    try:
        req = json.dumps({'url': url, 'timeout_ms': int(timeout_ms)})
        proc.stdin.write((req + '\n').encode('utf-8'))
        proc.stdin.flush()

        status = proc.stdout.readline().decode('utf-8', errors='replace').strip()
        size_s = proc.stdout.readline().decode('utf-8', errors='replace').strip()
        if not status or not size_s:
            if log:
                log.warning('browser_fetch: reusable Firefox worker exited unexpectedly')
            _stop_worker()
            return None

        size = int(size_s)
        body = proc.stdout.read(size).decode('utf-8', errors='replace')
        proc.stdout.readline()  # trailing separator newline

        if status != 'OK':
            if log:
                log.warning('browser_fetch: worker failed for %s: %s',
                            url[:80], body[-300:] if body else '(no error)')
            # Keep the worker alive: its script recreates page/context after
            # navigation failures. Do not launch a fallback Firefox window here.
            return None

        if log:
            log.debug('browser_fetch: worker fetched %d bytes for %s',
                      len(body), url[:100])
        return body if body.strip() else None
    except Exception as e:
        if log:
            log.warning('browser_fetch: worker transport error for %s: %s',
                        url[:80], e)
        _stop_worker()
        return None


def _ensure_worker(sys_python, headless, locale, extra_headers, log=None):
    global _worker_proc, _worker_key, _worker_script

    key = (' '.join(sys_python), bool(headless), locale,
           repr(sorted(extra_headers.items())))
    with _worker_lock:
        if (_worker_proc is not None and _worker_proc.poll() is None
                and _worker_key == key):
            return _worker_proc

        _stop_worker_locked()
        script_path = _write_worker_script(headless, locale, extra_headers)
        try:
            proc = subprocess.Popen(
                sys_python + [script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=_CREATE_NO_WINDOW,
            )
            _worker_proc = proc
            _worker_key = key
            _worker_script = script_path
            if log:
                log.info('browser_fetch: started reusable Firefox worker (%s headless=%s)',
                         ' '.join(sys_python), headless)
            return proc
        except Exception as e:
            if log:
                log.warning('browser_fetch: could not start reusable Firefox worker: %s', e)
            try:
                os.unlink(script_path)
            except Exception:
                pass
            _worker_proc = None
            _worker_key = None
            _worker_script = None
            return None


def _write_worker_script(headless, locale, extra_headers):
    script = '\n'.join([
        'import json, random, sys, time',
        'from playwright.sync_api import sync_playwright',
        f'_headless = {repr(headless)}',
        f'_locale = {repr(locale)}',
        f'_ua = {repr(_FIREFOX_UA)}',
        f'_extra_hdrs = {repr(extra_headers)}',
        f'_stealth_js = {repr(_STEALTH_JS)}',
        f'_ff_prefs = {repr(_FF_PREFS)}',
        '',
        'def _block_resources(route, request):',
        '    u = request.url.lower()',
        '    if "m.media-amazon.com" in u or "images-na.ssl-images-amazon.com" in u:',
        '        return route.continue_()',
        '    if "goodreads.com" in u and ("/books/" in u or "/images/" in u):',
        '        return route.continue_()',
        '    if request.resource_type in ("stylesheet", "font", "media"):',
        '        return route.abort()',
        '    blocked = ("google-analytics.com", "doubleclick.net", "amazon-adsystem.com",',
        '               "fls-na.amazon.com", "amazonvideo.com", "googletagmanager.com",',
        '               "facebook.com", "twitter.com", "scorecardresearch.com",',
        '               "quantserve.com", "omtrdc.net")',
        '    if any(d in u for d in blocked):',
        '        return route.abort()',
        '    return route.continue_()',
        '',
        'def _handle_continue_challenge(page):',
        '    selectors = ["input#continue",',
        '                 "xpath=/html/body/div/div[1]/div[3]/div/div/form/div/div/span"]',
        '    for sel in selectors:',
        '        try:',
        '            btn = page.locator(sel)',
        '            if btn.count() > 0 and btn.first.is_visible(timeout=1000):',
        '                btn.first.click(timeout=3000)',
        '                page.wait_for_load_state("domcontentloaded", timeout=5000)',
        '                page.wait_for_timeout(1500)',
        '                return True',
        '        except Exception:',
        '            continue',
        '    return False',
        '',
        'def _new_context(browser):',
        '    ctx = browser.new_context(',
        '        viewport={"width": 1366, "height": 768},',
        '        user_agent=_ua,',
        '        locale=_locale,',
        '        timezone_id="America/New_York",',
        '        extra_http_headers=_extra_hdrs,',
        '    )',
        '    page = ctx.new_page()',
        '    page.add_init_script(_stealth_js)',
        '    page.route("**/*", _block_resources)',
        '    return ctx, page',
        '',
        'with sync_playwright() as pw:',
        '    browser = pw.firefox.launch(',
        '        headless=_headless,',
        '        args=["--no-sandbox"],',
        '        firefox_user_prefs=_ff_prefs,',
        '    )',
        '    ctx, page = _new_context(browser)',
        '    for line in sys.stdin:',
        '        try:',
        '            req = json.loads(line)',
        '            time.sleep(0.3 + random.random() * 0.5)',
        '            try:',
        '                page.goto(req["url"], wait_until="networkidle", timeout=int(req["timeout_ms"]))',
        '            except Exception:',
        '                try:',
        '                    ctx.close()',
        '                except Exception:',
        '                    pass',
        '                ctx, page = _new_context(browser)',
        '                page.goto(req["url"], wait_until="networkidle", timeout=int(req["timeout_ms"]))',
        '            _handle_continue_challenge(page)',
        '            page.wait_for_timeout(1500 + random.randint(0, 500))',
        '            html = page.content()',
        '            if len(html.encode("utf-8")) < 5000:',
        '                page.wait_for_timeout(4000 + random.randint(0, 1000))',
        '                html = page.content()',
        '            out = html.encode("utf-8", errors="replace")',
        '            sys.stdout.buffer.write(b"OK\\n")',
        '            sys.stdout.buffer.write((str(len(out)) + "\\n").encode("ascii"))',
        '            sys.stdout.buffer.write(out + b"\\n")',
        '            sys.stdout.buffer.flush()',
        '        except Exception as e:',
        '            out = str(e).encode("utf-8", errors="replace")',
        '            sys.stdout.buffer.write(b"ERR\\n")',
        '            sys.stdout.buffer.write((str(len(out)) + "\\n").encode("ascii"))',
        '            sys.stdout.buffer.write(out + b"\\n")',
        '            sys.stdout.buffer.flush()',
        '    try:',
        '        ctx.close()',
        '    except Exception:',
        '        pass',
        '    browser.close()',
    ])
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='_mpp_browser_worker.py',
        delete=False, encoding='utf-8'
    ) as f:
        f.write(script)
        return f.name


def _stop_worker_locked():
    global _worker_proc, _worker_key, _worker_script
    proc = _worker_proc
    script_path = _worker_script
    _worker_proc = None
    _worker_key = None
    _worker_script = None

    if proc is not None:
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass
    if script_path:
        try:
            os.unlink(script_path)
        except Exception:
            pass


def _stop_worker():
    with _worker_lock:
        _stop_worker_locked()


def browser_close():
    """Shut down the reusable browser worker, if one is running."""
    _stop_worker()


atexit.register(browser_close)
