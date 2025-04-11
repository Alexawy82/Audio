"""
TTS engine module for DocToAudiobook.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import openai
from pydub import AudioSegment
from ..models.tts import TTSSettings
from ..utils.error import ErrorHandler
from .cache import TTSCache
# Import EnhancedTTS here to avoid circular import
from .enhanced import EnhancedTTS

class TTSEngine:
    """Handles text-to-speech conversion."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize TTS engine."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self.cache = TTSCache()
        self.enhanced = EnhancedTTS(logger=self.logger)
        
    def generate_audio(self, text: str, settings: TTSSettings) -> AudioSegment:
        """Generate audio from text using TTS."""
        try:
            # Generate unique hash for caching
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            settings_hash = hashlib.md5(str(settings.dict()).encode()).hexdigest()
            combined_hash = f"{text_hash}_{settings_hash}"
            
            self.logger.info(f"Audio hash: {combined_hash[:8]}... for text of length {len(text)}")
            
            # Check cache first
            cached_audio_path = self.cache.get_cached_audio(text, settings.dict())
            if cached_audio_path and os.path.exists(cached_audio_path):
                self.logger.info(f"Using cached audio from {cached_audio_path}")
                try:
                    return AudioSegment.from_mp3(cached_audio_path)
                except Exception as cache_error:
                    self.logger.warning(f"Failed to load cached audio: {cache_error}, generating new audio")
                
            # Generate new audio
            self.logger.info("Generating new audio")
            audio = self._generate_audio(text, settings)
            
            # Cache the result to a file
            temp_audio_path = os.path.join(self.cache.cache_dir, f"tts_{combined_hash[:16]}.mp3")
            audio.export(temp_audio_path, format="mp3")
            
            # Add to cache database
            self.cache.cache_audio(text, settings.dict(), temp_audio_path)
            self.logger.info(f"Cached audio to {temp_audio_path}")
            
            return audio
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text),
                'settings': settings.dict() if hasattr(settings, 'dict') else str(settings)
            })
            raise
            
    def _generate_audio(self, text: str, settings: TTSSettings) -> AudioSegment:
        """Generate audio using OpenAI TTS API."""
        try:
            # Split text into chunks if needed
            chunks = self._split_text(text, settings.max_chunk_size)
            
            # Generate audio for each chunk
            audio_segments = []
            for chunk in chunks:
                audio = self._generate_chunk_audio(chunk, settings)
                audio_segments.append(audio)
                
            # Combine audio segments
            if len(audio_segments) > 1:
                return self._combine_audio_segments(audio_segments)
            return audio_segments[0]
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text),
                'settings': settings.dict()
            })
            raise
            
    def _split_text(self, text: str, max_chunk_size: int) -> List[str]:
        """Split text into chunks of appropriate size."""
        try:
            # Enforce the 4000 character limit for OpenAI API
            safe_max_size = min(max_chunk_size, 4000)
            self.logger.info(f"Splitting text using max size of {safe_max_size} characters")
            
            # Use the enhanced text splitting from EnhancedTTS
            return self.enhanced._split_text_to_chunks(text, safe_max_size)
        except Exception as e:
            self.error_handler.log_error(e, {'text_length': len(text)})
            # Fallback to simple chunking
            self.logger.warning(f"Using fallback text chunking due to error: {e}")
            chunks = []
            safe_max_size = min(max_chunk_size, 4000)  # Ensure we respect OpenAI's 4096 limit
            
            # Split by paragraphs first for more natural breaks
            paragraphs = text.split('\n\n')
            current_chunk = ''
            
            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) + 2 <= safe_max_size:
                    if current_chunk:
                        current_chunk += '\n\n' + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # If paragraph itself is too long, split arbitrarily
                    if len(paragraph) > safe_max_size:
                        for i in range(0, len(paragraph), safe_max_size):
                            chunk = paragraph[i:i+safe_max_size]
                            if chunk:  # Only add non-empty chunks
                                chunks.append(chunk)
                    else:
                        current_chunk = paragraph
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
                
            # If no chunks were created, but text is too long, force splitting
            if not chunks:
                if len(text) > safe_max_size:
                    self.logger.warning(f"Forcing text split into chunks of {safe_max_size} characters")
                    # Simple character-based chunking as last resort
                    for i in range(0, len(text), safe_max_size):
                        chunks.append(text[i:i+safe_max_size])
                else:
                    chunks = [text]
            
            self.logger.info(f"Split text into {len(chunks)} chunks (fallback method)")
            return chunks
            
    def _generate_chunk_audio(self, text: str, settings: TTSSettings) -> AudioSegment:
        """Generate audio for a single text chunk."""
        try:
            # Call OpenAI TTS API
            response = openai.audio.speech.create(
                model=settings.model,
                voice=settings.voice,
                input=text,
                response_format="mp3"
            )
            
            # Convert response to AudioSegment
            audio = AudioSegment.from_mp3(response.content)
            
            # Apply enhancements if enabled
            if settings.enhance:
                audio = self.enhanced.enhance_audio(audio, settings)
                
            return audio
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'text_length': len(text),
                'settings': settings.dict()
            })
            raise
            
    def _combine_audio_segments(self, segments: List[AudioSegment]) -> AudioSegment:
        """Combine multiple audio segments into one."""
        try:
            combined = segments[0]
            for segment in segments[1:]:
                combined += segment
            return combined
            
        except Exception as e:
            self.error_handler.log_error(e, {'segment_count': len(segments)})
            raise 