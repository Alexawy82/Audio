"""
Configuration manager module for handling application settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

class ConfigManager:
    """Manages application configuration settings with improved error handling and type safety."""
    
    def __init__(self, config_file: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to config file. If None, uses default location.
            logger: Optional logger instance. If None, creates a new logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Set base directory
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'data')
        
        if config_file:
            self.config_file = os.path.abspath(config_file)
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".doctoaudiobook")
            self.config_file = os.path.join(config_dir, "config.json")
            
        self.config = self._load_config()
        self.create_directories()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if it doesn't exist."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                return self._merge_with_defaults(loaded_config)
            return self._get_default_config()
        except json.JSONDecodeError:
            self.logger.warning(f"Error decoding config file {self.config_file}. Using defaults.")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._get_default_config()
            
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist."""
        defaults = self._get_default_config()
        
        def deep_update(source: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in overrides.items():
                if isinstance(value, dict) and key in source and isinstance(source[key], dict):
                    deep_update(source[key], value)
                else:
                    source[key] = value
            return source
            
        return deep_update(defaults.copy(), loaded_config)
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with all required settings."""
        return {
            "api_key": "",
            "output_dir": os.path.join(self.data_dir, 'output'),
            "temp_dir": os.path.join(self.data_dir, 'temp'),
            "cache_dir": os.path.join(self.data_dir, 'cache'),
            "uploads_dir": os.path.join(self.data_dir, 'uploads'),
            "logs_dir": os.path.join(self.data_dir, 'logs'),
            "db_path": os.path.join(self.data_dir, 'database'),
            "max_chunk_size": 2000,
            "voice_settings": {
                "model": "tts-1",
                "voice": "alloy",
                "speed": 1.0,
                "style": "neutral",
                "emotion": "",
                "language": "en"
            },
            "audio_settings": {
                "normalize": True,
                "compress": True,
                "remove_silence": True,
                "format": "mp3",
                "quality": "high",
                "bitrate": "192k",
                "pause_between_chapters": 1000,
                "pause_between_chunks": 200,
                "combine_chapters": True
            },
            "recent_files": []
        }
        
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Config saved to: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default."""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save."""
        self.config[key] = value
        return self.save_config()
        
    def get_config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self.config.copy()
        
    def get_api_key(self) -> str:
        """Get API key."""
        return self.get("api_key", "")
        
    def set_api_key(self, api_key: str) -> bool:
        """Set API key."""
        return self.set("api_key", api_key)
        
    def get_output_dir(self) -> str:
        """Get output directory."""
        output_dir = self.get("output_dir", os.path.join(self.data_dir, 'output'))
        # Ensure it's an absolute path
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(self.base_dir, output_dir)
        return output_dir
        
    def set_output_dir(self, output_dir: str) -> bool:
        """Set output directory."""
        return self.set("output_dir", output_dir)
        
    def get_temp_dir(self) -> str:
        """Get temporary directory."""
        temp_dir = self.get("temp_dir", os.path.join(self.data_dir, 'temp'))
        # Ensure it's an absolute path
        if not os.path.isabs(temp_dir):
            temp_dir = os.path.join(self.base_dir, temp_dir)
        return temp_dir
        
    def set_temp_dir(self, temp_dir: str) -> bool:
        """Set temporary directory."""
        return self.set("temp_dir", temp_dir)
        
    def get_cache_dir(self) -> str:
        """Get cache directory."""
        cache_dir = self.get("cache_dir", os.path.join(self.data_dir, 'cache'))
        # Ensure it's an absolute path
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(self.base_dir, cache_dir)
        return cache_dir
        
    def set_cache_dir(self, cache_dir: str) -> bool:
        """Set cache directory."""
        return self.set("cache_dir", cache_dir)
        
    def get_uploads_dir(self) -> str:
        """Get uploads directory."""
        uploads_dir = self.get("uploads_dir", os.path.join(self.data_dir, 'uploads'))
        # Ensure it's an absolute path
        if not os.path.isabs(uploads_dir):
            uploads_dir = os.path.join(self.base_dir, uploads_dir)
        return uploads_dir
        
    def set_uploads_dir(self, uploads_dir: str) -> bool:
        """Set uploads directory."""
        return self.set("uploads_dir", uploads_dir)
        
    def get_logs_dir(self) -> str:
        """Get logs directory."""
        logs_dir = self.get("logs_dir", os.path.join(self.data_dir, 'logs'))
        # Ensure it's an absolute path
        if not os.path.isabs(logs_dir):
            logs_dir = os.path.join(self.base_dir, logs_dir)
        return logs_dir
        
    def set_logs_dir(self, logs_dir: str) -> bool:
        """Set logs directory."""
        return self.set("logs_dir", logs_dir)
        
    def get_database_path(self) -> str:
        """Get the database path for job storage."""
        db_path = self.get("db_path", os.path.join(self.data_dir, 'database'))
        # Ensure it's an absolute path
        if not os.path.isabs(db_path):
            db_path = os.path.join(self.base_dir, db_path)
        if not db_path.endswith('.db'):
            db_path += '/jobs.db'
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return db_path
        
    def get_max_chunk_size(self) -> int:
        """Get maximum chunk size."""
        return self.get("max_chunk_size", 2000)
        
    def set_max_chunk_size(self, max_chunk_size: int) -> bool:
        """Set maximum chunk size."""
        return self.set("max_chunk_size", max_chunk_size)
        
    def get_voice_settings(self) -> Dict[str, Any]:
        """Get voice settings with defaults."""
        defaults = self._get_default_config()["voice_settings"]
        current = self.get("voice_settings", {})
        merged = defaults.copy()
        merged.update(current)
        return merged
        
    def set_voice_settings(self, voice_settings: Dict[str, Any]) -> bool:
        """Set voice settings."""
        if "voice_settings" not in self.config:
            self.config["voice_settings"] = {}
        self.config["voice_settings"].update(voice_settings)
        return self.save_config()
        
    def get_audio_settings(self) -> Dict[str, Any]:
        """Get audio settings with defaults."""
        defaults = self._get_default_config()["audio_settings"]
        current = self.get("audio_settings", {})
        merged = defaults.copy()
        merged.update(current)
        return merged
        
    def set_audio_settings(self, audio_settings: Dict[str, Any]) -> bool:
        """Set audio settings."""
        if "audio_settings" not in self.config:
            self.config["audio_settings"] = {}
        self.config["audio_settings"].update(audio_settings)
        return self.save_config()
        
    def get_recent_files(self) -> List[str]:
        """Get list of recent files."""
        return self.get("recent_files", [])
        
    def add_recent_file(self, file_path: Union[str, Path]) -> bool:
        """Add a file to recent files list."""
        file_path_str = str(file_path)
        recent_files = self.get_recent_files()
        
        if file_path_str in recent_files:
            recent_files.remove(file_path_str)
        recent_files.insert(0, file_path_str)
        
        # Keep only the last 10 files
        recent_files = recent_files[:10]
        return self.set("recent_files", recent_files)
        
    def create_directories(self) -> None:
        """Create necessary directories for the application."""
        try:
            # Create data directory
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Create subdirectories
            dirs = [
                self.get_output_dir(),
                self.get_temp_dir(),
                self.get_cache_dir(),
                self.get_uploads_dir(),
                self.get_logs_dir(),
                os.path.dirname(self.get_database_path())
            ]
            
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.debug(f"Created directory: {dir_path}")
                
        except Exception as e:
            self.logger.error(f"Error creating directories: {e}")
            raise
        
    def validate(self) -> bool:
        """Validate configuration."""
        try:
            # Check required directories
            dirs = [
                self.get_output_dir(),
                self.get_temp_dir(),
                self.get_cache_dir(),
                self.get_uploads_dir(),
                self.get_logs_dir()
            ]
            
            for dir_path in dirs:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    
            # Check API key if OpenAI is selected
            if self.get_voice_settings().get('model', '').startswith('tts-'):
                if not self.get_api_key():
                    self.logger.warning("OpenAI API key not set")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False 