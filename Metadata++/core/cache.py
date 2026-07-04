#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
__license__ = 'GPL v3'
"""SQLite metadata cache with configurable TTL."""

import os
import json
import sqlite3
import hashlib
import time

from calibre.utils.config import config_dir  # type: ignore


class MetadataCache:
    DB_PATH = os.path.join(config_dir, 'metadata_plus_cache.db')

    def __init__(self):
        self._conn = None
        self._ensure_db()

    def _connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        return self._conn

    def _ensure_db(self):
        conn = self._connect()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key      TEXT PRIMARY KEY,
                data     TEXT NOT NULL,
                source   TEXT,
                ts       REAL NOT NULL
            )
        ''')
        conn.commit()

    @staticmethod
    def _make_key(title, author, isbn, source):
        raw = '|'.join([
            (title or '').lower().strip(),
            (author or '').lower().strip(),
            (isbn or '').strip(),
            (source or '').lower(),
        ])
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def get(self, title, author, isbn, source, ttl_days=7):
        if ttl_days <= 0:
            return None
        key = self._make_key(title, author, isbn, source)
        try:
            conn = self._connect()
            cur = conn.execute('SELECT data, ts FROM cache WHERE key=?', (key,))
            row = cur.fetchone()
            if row:
                data_json, ts = row
                age_days = (time.time() - ts) / 86400
                if age_days <= ttl_days:
                    return json.loads(data_json)
                # Expired — delete
                conn.execute('DELETE FROM cache WHERE key=?', (key,))
                conn.commit()
        except Exception:
            pass
        return None

    def put(self, title, author, isbn, source, data):
        key = self._make_key(title, author, isbn, source)
        try:
            conn = self._connect()
            conn.execute(
                'INSERT OR REPLACE INTO cache (key, data, source, ts) VALUES (?,?,?,?)',
                (key, json.dumps(data), source, time.time())
            )
            conn.commit()
        except Exception:
            pass

    def clear(self):
        try:
            conn = self._connect()
            conn.execute('DELETE FROM cache')
            conn.commit()
        except Exception:
            pass

    def purge_expired(self, ttl_days=7):
        if ttl_days <= 0:
            return
        cutoff = time.time() - ttl_days * 86400
        try:
            conn = self._connect()
            conn.execute('DELETE FROM cache WHERE ts < ?', (cutoff,))
            conn.commit()
        except Exception:
            pass

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
