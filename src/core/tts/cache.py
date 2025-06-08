"""
TTS cache module for DocToAudiobook.
"""

import os
import sqlite3
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from ..utils.error import ErrorHandler

class TTSCache:
    """Manages caching of TTS audio files."""
    def __init__(self, cache_dir: str = "tts_cache", max_size: int = 1000, logger: Optional[logging.Logger] = None):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        os.makedirs(cache_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        try:
            db_path = os.path.join(self.cache_dir, "tts_cache.db")
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.cursor = self.conn.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT UNIQUE,
                    audio_path TEXT,
                    voice_settings TEXT,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    text_length INTEGER DEFAULT 0
                )
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_text_hash ON cache(text_hash)
            """)
            self.conn.commit()
            self.logger.info(f"Initialized TTS cache database at {db_path}")
        except Exception as e:
            self.error_handler.log_error(e, {'cache_dir': self.cache_dir})
            raise

    def get_cached_audio(self, text: str, settings: Dict[str, Any]) -> Optional[str]:
        try:
            text_hash = self._generate_hash(text, settings)
            self.cursor.execute("""
                SELECT audio_path, last_accessed, access_count
                FROM cache
                WHERE text_hash = ?
            """, (text_hash,))
            result = self.cursor.fetchone()
            if result:
                audio_path, last_accessed, access_count = result
                if not os.path.exists(audio_path):
                    self.logger.warning(f"Cache entry exists but file not found: {audio_path}")
                    self.cursor.execute("DELETE FROM cache WHERE text_hash = ?", (text_hash,))
                    self.conn.commit()
                    return None
                self.cursor.execute("""
                    UPDATE cache
                    SET last_accessed = ?, access_count = ?
                    WHERE text_hash = ?
                """, (datetime.now(), access_count + 1, text_hash))
                self.conn.commit()
                self.logger.info(f"Cache hit for text hash {text_hash[:8]}... (path: {audio_path})")
                return audio_path
            self.logger.info(f"Cache miss for text hash {text_hash[:8]}...")
            return None
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text) if isinstance(text, str) else 'unknown',
                'settings': str(settings)
            })
            return None

    def cache_audio(self, text: str, settings: Dict[str, Any], audio_path: str):
        try:
            text_hash = self._generate_hash(text, settings)
            if not os.path.exists(audio_path):
                self.logger.warning(f"Cannot cache audio - file does not exist: {audio_path}")
                return
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                self.logger.warning(f"Cannot cache audio - file is empty: {audio_path}")
                return
            self.logger.info(f"Caching audio at {audio_path} (size: {file_size} bytes) with hash {text_hash[:8]}...")
            self.cursor.execute("""
                INSERT OR REPLACE INTO cache
                (text_hash, audio_path, voice_settings, created_at, last_accessed, access_count, text_length)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                text_hash,
                audio_path,
                str(settings),
                datetime.now(),
                datetime.now(),
                1,
                len(text) if isinstance(text, str) else 0
            ))
            self.conn.commit()
            self._cleanup_cache()
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text) if isinstance(text, str) else 'unknown',
                'settings': str(settings),
                'audio_path': audio_path
            })
            self.logger.error(f"Error caching audio: {e}")

    def _generate_hash(self, text: str, settings: Dict[str, Any]) -> str:
        import hashlib
        import json
        normalized_text = ' '.join(text.split())
        if isinstance(settings, dict):
            voice_settings = {
                'voice': settings.get('voice', 'alloy'),
                'model': settings.get('model', 'tts-1'),
                'speed': settings.get('speed', 1.0),
                'style': settings.get('style', 'neutral'),
                'emotion': settings.get('emotion', '')
            }
            sorted_settings = json.dumps(voice_settings, sort_keys=True)
        else:
            sorted_settings = str(settings)
        text_hash = hashlib.md5(normalized_text.encode()).hexdigest()
        settings_hash = hashlib.md5(sorted_settings.encode()).hexdigest()
        return f"{text_hash}_{settings_hash}"

    def _cleanup_cache(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM cache")
            count = self.cursor.fetchone()[0]
            if count > self.max_size:
                self.cursor.execute("""
                    DELETE FROM cache
                    WHERE id IN (
                        SELECT id FROM cache
                        ORDER BY last_accessed ASC
                        LIMIT ?
                    )
                """, (count - self.max_size,))
                self.conn.commit()
        except Exception as e:
            self.error_handler.log_error(e, {'max_size': self.max_size})
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    AVG(access_count) as avg_accesses,
                    SUM(text_length) as total_text_length
                FROM cache
            """)
            result = self.cursor.fetchone()
            total_size = 0
            try:
                self.cursor.execute("SELECT audio_path FROM cache")
                paths = self.cursor.fetchall()
                for (path,) in paths:
                    if os.path.exists(path):
                        total_size += os.path.getsize(path)
            except Exception as size_error:
                self.logger.warning(f"Error calculating cache size: {size_error}")
            return {
                'total_entries': result[0] or 0,
                'total_accesses': result[1] or 0,
                'avg_accesses': result[2] or 0,
                'total_text_length': result[3] or 0,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
            }
        except Exception as e:
            self.error_handler.log_error(e)
            return {
                'total_entries': 0,
                'total_accesses': 0,
                'avg_accesses': 0,
                'total_text_length': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0
            }

    def clear_cache(self, delete_files: bool = True) -> Dict[str, Any]:
        try:
            before_stats = self.get_cache_stats()
            audio_files = []
            if delete_files:
                self.cursor.execute("SELECT audio_path FROM cache")
                audio_files = [path[0] for path in self.cursor.fetchall()]
            self.cursor.execute("DELETE FROM cache")
            self.conn.commit()
            deleted_count = 0
            if delete_files:
                for file_path in audio_files:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_count += 1
                    except Exception as del_error:
                        self.logger.warning(f"Failed to delete cache file {file_path}: {del_error}")
            self.logger.info(f"Cache cleared. Removed {deleted_count} audio files.")
            return {
                'status': 'success',
                'entries_removed': before_stats['total_entries'],
                'files_deleted': deleted_count,
                'space_freed_mb': before_stats['total_size_mb']
            }
        except Exception as e:
            self.error_handler.log_error(e)
            return {
                'status': 'error',
                'error': str(e),
                'entries_removed': 0,
                'files_deleted': 0
            } 