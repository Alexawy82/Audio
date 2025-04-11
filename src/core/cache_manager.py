"""
Cache management module for handling TTS caching.
"""

import os
import json
import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class TTSCache:
    """Cache for TTS API calls to avoid regenerating the same content."""
    
    def __init__(self, cache_dir: str = "tts_cache", 
                 db_path: str = "tts_cache.db",
                 logger: Optional[logging.Logger] = None):
        self.cache_dir = Path(cache_dir)
        self.db_path = db_path
        self.logger = logger or logging.getLogger(__name__)
        
        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize cache database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        content_hash TEXT PRIMARY KEY,
                        audio_file TEXT NOT NULL,
                        voice_settings TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        last_accessed REAL NOT NULL,
                        access_count INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error initializing cache database: {e}")
            raise
            
    def _get_content_hash(self, text: str, voice_settings: Dict[str, Any]) -> str:
        """
        Generate a unique hash for the text and voice settings.
        
        Args:
            text: Text content
            voice_settings: Voice settings dictionary
            
        Returns:
            SHA-256 hash string
        """
        content_str = f"{text}|{json.dumps(voice_settings, sort_keys=True)}"
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
    def get_cached_audio(self, text: str, voice_settings: Dict[str, Any]) -> Optional[str]:
        """
        Check if audio for the given text and settings exists in cache.
        
        Args:
            text: Text content
            voice_settings: Voice settings dictionary
            
        Returns:
            Path to cached audio file if found, None otherwise
        """
        try:
            content_hash = self._get_content_hash(text, voice_settings)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT audio_file, last_accessed, access_count
                    FROM cache
                    WHERE content_hash = ?
                """, (content_hash,))
                
                row = cursor.fetchone()
                if row:
                    audio_file = row[0]
                    if os.path.exists(audio_file):
                        # Update access statistics
                        cursor.execute("""
                            UPDATE cache
                            SET last_accessed = ?,
                                access_count = access_count + 1
                            WHERE content_hash = ?
                        """, (datetime.now().timestamp(), content_hash))
                        conn.commit()
                        
                        self.logger.info(f"Cache hit for content hash {content_hash}")
                        return audio_file
                    else:
                        # Remove invalid cache entry
                        cursor.execute("""
                            DELETE FROM cache
                            WHERE content_hash = ?
                        """, (content_hash,))
                        conn.commit()
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking cache: {e}")
            return None
            
    def cache_audio(self, text: str, voice_settings: Dict[str, Any],
                   audio_file: str) -> bool:
        """
        Cache audio file for the given text and settings.
        
        Args:
            text: Text content
            voice_settings: Voice settings dictionary
            audio_file: Path to audio file
            
        Returns:
            True if successful
        """
        try:
            content_hash = self._get_content_hash(text, voice_settings)
            now = datetime.now().timestamp()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO cache (
                        content_hash, audio_file, voice_settings,
                        created_at, last_accessed, access_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    content_hash,
                    audio_file,
                    json.dumps(voice_settings),
                    now,
                    now,
                    1
                ))
                
                conn.commit()
                
            self.logger.info(f"Cached audio for content hash {content_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching audio: {e}")
            return False
            
    def cleanup(self, max_age_days: int = 30, min_access_count: int = 1) -> None:
        """
        Clean up old and unused cache entries.
        
        Args:
            max_age_days: Maximum age in days
            min_access_count: Minimum access count
        """
        try:
            cutoff_time = (datetime.now() - timedelta(days=max_age_days)).timestamp()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get entries to remove
                cursor.execute("""
                    SELECT content_hash, audio_file
                    FROM cache
                    WHERE created_at < ? AND access_count < ?
                """, (cutoff_time, min_access_count))
                
                for row in cursor.fetchall():
                    content_hash, audio_file = row
                    
                    # Remove audio file
                    try:
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
                    except Exception as e:
                        self.logger.warning(f"Could not remove audio file {audio_file}: {e}")
                        
                    # Remove cache entry
                    cursor.execute("""
                        DELETE FROM cache
                        WHERE content_hash = ?
                    """, (content_hash,))
                    
                conn.commit()
                
            self.logger.info("Cache cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}") 