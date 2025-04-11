"""
TTS cache module for DocToAudiobook.
"""

import os
import sqlite3
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..utils.error import ErrorHandler

class TTSCache:
    """Manages caching of TTS audio files."""
    
    def __init__(self, cache_dir: str = "tts_cache", max_size: int = 1000, logger: Optional[logging.Logger] = None):
        """Initialize TTS cache."""
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
    def _init_db(self):
        """Initialize cache database."""
        try:
            db_path = os.path.join(self.cache_dir, "tts_cache.db")
            
            # Create database with WAL journal mode for better performance and multi-process safety
            # The check_same_thread=False allows use from multiple threads
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            
            # Enable WAL mode for better concurrent access
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            
            self.cursor = self.conn.cursor()
            
            # Create cache table if it doesn't exist
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
            
            # Create an index on text_hash for faster lookups
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_text_hash ON cache(text_hash)
            """)
            
            self.conn.commit()
            
            self.logger.info(f"Initialized TTS cache database at {db_path}")
            
        except Exception as e:
            self.error_handler.log_error(e, {'cache_dir': self.cache_dir})
            raise
            
    def get_cached_audio(self, text: str, settings: Dict[str, Any]) -> Optional[str]:
        """Get cached audio file if it exists."""
        try:
            text_hash = self._generate_hash(text, settings)
            
            # Check if audio exists in cache
            self.cursor.execute("""
                SELECT audio_path, last_accessed, access_count
                FROM cache
                WHERE text_hash = ?
            """, (text_hash,))
            
            result = self.cursor.fetchone()
            if result:
                audio_path, last_accessed, access_count = result
                
                # Verify the file exists
                if not os.path.exists(audio_path):
                    self.logger.warning(f"Cache entry exists but file not found: {audio_path}")
                    # Remove invalid entry
                    self.cursor.execute("DELETE FROM cache WHERE text_hash = ?", (text_hash,))
                    self.conn.commit()
                    return None
                
                # Update access count and timestamp
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
        """Cache a new audio file."""
        try:
            text_hash = self._generate_hash(text, settings)
            
            # Verify the audio file exists
            if not os.path.exists(audio_path):
                self.logger.warning(f"Cannot cache audio - file does not exist: {audio_path}")
                return
                
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                self.logger.warning(f"Cannot cache audio - file is empty: {audio_path}")
                return
                
            self.logger.info(f"Caching audio at {audio_path} (size: {file_size} bytes) with hash {text_hash[:8]}...")
            
            # Insert or update cache entry
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
            
            # Clean up old entries if cache is full
            self._cleanup_cache()
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text) if isinstance(text, str) else 'unknown',
                'settings': str(settings),
                'audio_path': audio_path
            })
            # Don't re-raise to avoid breaking the main flow if caching fails
            self.logger.error(f"Error caching audio: {e}")
            
    def _generate_hash(self, text: str, settings: Dict[str, Any]) -> str:
        """Generate a unique hash for text and settings."""
        import hashlib
        import json
        
        # Normalize text by removing extra whitespace
        normalized_text = ' '.join(text.split())
        
        # Sort settings dict to ensure consistent order
        sorted_settings = {}
        if isinstance(settings, dict):
            # Extract only the relevant settings that affect audio generation
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
        
        # Create hash of text and settings separately 
        text_hash = hashlib.md5(normalized_text.encode()).hexdigest()
        settings_hash = hashlib.md5(sorted_settings.encode()).hexdigest()
        
        # Combine hashes
        return f"{text_hash}_{settings_hash}"
        
    def _cleanup_cache(self):
        """Clean up old cache entries."""
        try:
            # Get total number of entries
            self.cursor.execute("SELECT COUNT(*) FROM cache")
            count = self.cursor.fetchone()[0]
            
            if count > self.max_size:
                # Delete oldest entries
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
        """Get cache statistics."""
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
            
            # Also get total disk usage
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
        """Clear the cache database and optionally delete audio files."""
        try:
            # Get stats before clearing
            before_stats = self.get_cache_stats()
            
            # Get list of files to delete
            audio_files = []
            if delete_files:
                self.cursor.execute("SELECT audio_path FROM cache")
                audio_files = [path[0] for path in self.cursor.fetchall()]
            
            # Clear the cache table
            self.cursor.execute("DELETE FROM cache")
            self.conn.commit()
            
            # Delete audio files
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