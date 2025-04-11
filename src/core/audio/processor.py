"""
Audio processing module for DocToAudiobook.
"""

import os
import logging
from typing import Dict, Any, Optional
from pydub import AudioSegment
from ..models.audio import AudioSettings
from ..utils.error import ErrorHandler

class AudioProcessor:
    """Handles audio processing operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize audio processor."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
    def process_audio(self, audio_path: str, settings: AudioSettings) -> AudioSegment:
        """Process audio file with given settings."""
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Apply settings
            if settings.speed != 1.0:
                audio = self._adjust_speed(audio, settings.speed)
                
            if settings.volume != 0:
                audio = self._adjust_volume(audio, settings.volume)
                
            if settings.normalize:
                audio = self._normalize(audio)
                
            return audio
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'audio_path': audio_path,
                'settings': settings.dict()
            })
            raise
            
    def _adjust_speed(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Adjust audio speed."""
        try:
            return audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            })
        except Exception as e:
            self.logger.error(f"Error adjusting speed: {e}")
            return audio
            
    def _adjust_volume(self, audio: AudioSegment, volume: float) -> AudioSegment:
        """Adjust audio volume."""
        try:
            return audio + volume
        except Exception as e:
            self.logger.error(f"Error adjusting volume: {e}")
            return audio
            
    def _normalize(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio levels."""
        try:
            return audio.normalize()
        except Exception as e:
            self.logger.error(f"Error normalizing audio: {e}")
            return audio 