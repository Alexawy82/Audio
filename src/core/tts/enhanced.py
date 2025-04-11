"""
Enhanced TTS module for audio quality improvements.
"""

import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any, List
import re
from pydub import AudioSegment, effects
from pydub.effects import normalize, compress_dynamic_range
from ..utils.error import ErrorHandler
from ..models.tts import TTSSettings

class EnhancedTTS:
    """Provides enhanced audio processing for TTS outputs."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize enhanced TTS processor."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
    def enhance_audio(self, audio: AudioSegment, settings: TTSSettings) -> AudioSegment:
        """Apply audio enhancements based on settings."""
        try:
            # Apply audio enhancements based on settings
            if settings.noise_reduction:
                audio = self._apply_noise_reduction(audio)
                
            if settings.equalization:
                audio = self._apply_equalization(audio)
                
            if settings.compression:
                audio = self._apply_compression(audio)
                
            if settings.normalize:
                audio = self._apply_normalization(audio)
                
            return audio
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'audio_length': len(audio),
                'settings': settings.dict() if hasattr(settings, 'dict') else vars(settings)
            })
            return audio  # Return original audio if enhancement fails
            
    def _apply_noise_reduction(self, audio: AudioSegment) -> AudioSegment:
        """Apply noise reduction to audio segment."""
        try:
            # Noise reduction implementation using sox or other tools would go here
            # For now, we'll just implement a simple high-pass filter to remove low-frequency noise
            self.logger.debug("Applying noise reduction")
            
            # Create a temporary file for processing with external tools if needed
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                    try:
                        # Export audio to temp file
                        audio.export(temp_input.name, format="wav")
                        
                        # TODO: Implement actual noise reduction using external tools
                        # For now, just return the original audio
                        
                        # Read processed audio
                        return audio
                    finally:
                        # Clean up temp files
                        os.remove(temp_input.name)
                        os.remove(temp_output.name)
        except Exception as e:
            self.error_handler.log_error(e, {'audio_length': len(audio)})
            return audio
            
    def _apply_equalization(self, audio: AudioSegment) -> AudioSegment:
        """Apply equalization to audio segment."""
        try:
            self.logger.debug("Applying equalization")
            
            # Simple equalization: boost high frequencies for clarity
            # Real implementation would use proper EQ filters
            
            # Create a temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                    try:
                        # Export audio to temp file
                        audio.export(temp_input.name, format="wav")
                        
                        # TODO: Implement actual equalization using pydub or external tools
                        # For now, just return the original audio
                        
                        # Read processed audio
                        return audio
                    finally:
                        # Clean up temp files
                        os.remove(temp_input.name)
                        os.remove(temp_output.name)
        except Exception as e:
            self.error_handler.log_error(e, {'audio_length': len(audio)})
            return audio
            
    def _apply_compression(self, audio: AudioSegment) -> AudioSegment:
        """Apply compression to audio segment."""
        try:
            self.logger.debug("Applying compression")
            
            # Apply dynamic range compression
            # This makes quiet parts louder and loud parts quieter
            processed = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
            
            return processed
            
        except Exception as e:
            self.error_handler.log_error(e, {'audio_length': len(audio)})
            return audio
            
    def _apply_normalization(self, audio: AudioSegment) -> AudioSegment:
        """Apply normalization to audio segment."""
        try:
            self.logger.debug("Applying normalization")
            
            # Normalize audio to standard level
            processed = normalize(audio, headroom=0.1)
            
            return processed
            
        except Exception as e:
            self.error_handler.log_error(e, {'audio_length': len(audio)})
            return audio
            
    def _enhance_text_for_emotion(self, text: str, style: str, emotion: str) -> str:
        """
        Enhance the text input for better emotional delivery.
        Adds style markers that improve the TTS emotional response.
        """
        # No enhancement for neutral style
        if style == "neutral" or not style:
            return text
            
        # Basic cleanup of the text
        enhanced_text = text.strip()
        
        if style == "cheerful" or emotion == "happy":
            # Add markers for cheerful tone
            enhanced_text = f"[Cheerfully] {enhanced_text}"
            
            # Add occasional emphasis markers for important words
            words = enhanced_text.split()
            if len(words) > 10:
                # Add emphasis to approximately 10% of words for longer texts
                for i in range(len(words)):
                    if i % 10 == 0 and len(words[i]) > 3:
                        words[i] = f"*{words[i]}*"
                enhanced_text = " ".join(words)
                
        elif style == "sad":
            # Add markers for sad tone
            enhanced_text = f"[With sadness] {enhanced_text}"
            
            # Slow down apparent pacing with occasional pauses
            sentences = re.split(r'(?<=[.!?])\s+', enhanced_text)
            for i in range(len(sentences)):
                if i > 0 and i < len(sentences) - 1:
                    sentences[i] = sentences[i] + "..."
            enhanced_text = " ".join(sentences)
            
        elif style == "excited":
            # Add markers for excited tone
            enhanced_text = f"[Excitedly] {enhanced_text}"
            
            # Add exclamation emphasis
            enhanced_text = enhanced_text.replace('.', '!')
            
            # Add emphasis to important words
            words = enhanced_text.split()
            for i in range(len(words)):
                if i % 6 == 0 and len(words[i]) > 3:
                    words[i] = f"*{words[i]}*"
            enhanced_text = " ".join(words)
            
        elif style == "serious":
            # Add markers for serious tone
            enhanced_text = f"[Seriously] {enhanced_text}"
            
            # Add more formal, deliberate pacing
            sentences = re.split(r'(?<=[.!?])\s+', enhanced_text)
            enhanced_text = ". ".join(sentences)
            
        return enhanced_text
        
    def _apply_audio_style_effects(self, audio: AudioSegment, style: str) -> AudioSegment:
        """
        Apply audio effects based on the style to enhance emotional quality.
        """
        try:
            if style == "neutral" or not style:
                return audio
                
            # Make a copy of the audio to avoid modifying the original
            # AudioSegment doesn't have a copy() method, so we use a slice operation to clone it
            processed = audio[:]
                
            if style == "cheerful" or style == "happy":
                # Slightly increase tempo for cheerful tone
                processed = self._adjust_speed(processed, 1.05)
                # Slight boost to higher frequencies for brightness
                processed = self._apply_high_shelf_filter(processed, 3000, gain_db=2.0)
                
            elif style == "sad":
                # Slow tempo slightly for sad tone
                processed = self._adjust_speed(processed, 0.95)
                # Slight bass boost for warmth and reduce treble for darkness
                processed = self._apply_low_shelf_filter(processed, 200, gain_db=2.0)
                processed = self._apply_high_shelf_filter(processed, 3000, gain_db=-2.0)
                
            elif style == "excited":
                # Faster tempo for excitement
                processed = self._adjust_speed(processed, 1.1)
                # Boost mids and highs for clarity and energy
                processed = self._apply_high_shelf_filter(processed, 2000, gain_db=3.0)
                
            elif style == "serious":
                # Slightly slower for gravitas
                processed = self._adjust_speed(processed, 0.98)
                # Boost low-mids for depth
                processed = self._apply_low_shelf_filter(processed, 300, gain_db=2.5)
                
            return processed
            
        except Exception as e:
            self.error_handler.log_error(e, {'style': style, 'audio_length': len(audio)})
            return audio
            
    def _adjust_speed(self, audio: AudioSegment, speed_factor: float) -> AudioSegment:
        """Adjust the speed of audio without changing pitch."""
        try:
            if speed_factor == 1.0:
                return audio
                
            # Simple speed adjustment using PyDub
            # Note: This changes pitch, but it's a lightweight approach
            frames = int(audio.frame_count() / speed_factor)
            return audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed_factor)
            }).set_frame_rate(audio.frame_rate)
            
        except Exception as e:
            self.error_handler.log_error(e, {'speed_factor': speed_factor})
            return audio
            
    def _apply_low_shelf_filter(self, audio: AudioSegment, frequency: int, gain_db: float) -> AudioSegment:
        """Apply a low shelf filter to boost or cut bass frequencies."""
        try:
            # For now, use a simplified approach with PyDub's default filter
            # We could implement a more sophisticated filter later
            if gain_db > 0:
                return audio.low_shelf_filter(frequency, gain_db)
            else:
                return audio.low_shelf_filter(frequency, gain_db)
        except Exception as e:
            self.error_handler.log_error(e, {'frequency': frequency, 'gain_db': gain_db})
            return audio
            
    def _apply_high_shelf_filter(self, audio: AudioSegment, frequency: int, gain_db: float) -> AudioSegment:
        """Apply a high shelf filter to boost or cut treble frequencies."""
        try:
            # For now, use a simplified approach with PyDub's default filter
            if gain_db > 0:
                return audio.high_shelf_filter(frequency, gain_db)
            else:
                return audio.high_shelf_filter(frequency, gain_db)
        except Exception as e:
            self.error_handler.log_error(e, {'frequency': frequency, 'gain_db': gain_db})
            return audio
            
    def _split_text_to_chunks(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Split text into chunks of max_chunk_size, trying to break at sentence boundaries.
        
        Args:
            text: The text to split
            max_chunk_size: Maximum size of each chunk in characters
            
        Returns:
            List of text chunks
        """
        try:
            # ENFORCE OPENAI API LIMIT: Never exceed 4000 chars (API limit is 4096)
            safe_max_size = min(max_chunk_size, 4000)
            
            # If text is shorter than max chunk size, return as is
            if len(text) <= safe_max_size:
                return [text]
                
            self.logger.info(f"Splitting text of length {len(text)} into chunks of max {safe_max_size} chars")
            
            chunks = []
            current_chunk = ""
            
            # Split by paragraph breaks first for best natural chunking
            paragraphs = re.split(r'\n\s*\n', text)
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                    
                # If adding this paragraph would exceed chunk size, start a new chunk
                if current_chunk and len(current_chunk) + len(paragraph) + 2 > safe_max_size:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # If paragraph itself is too long, split it by sentences
                if len(paragraph) > safe_max_size:
                    self.logger.debug(f"Splitting long paragraph of {len(paragraph)} chars")
                    
                    # Try to split by sentences using regex for better accuracy
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    
                    for sentence in sentences:
                        # If this sentence fits in the current chunk, add it
                        if len(current_chunk) + len(sentence) + 1 <= safe_max_size:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                        else:
                            # If current chunk is not empty, add it to chunks
                            if current_chunk:
                                chunks.append(current_chunk)
                            
                            # If sentence itself is too long, split it further
                            if len(sentence) > safe_max_size:
                                self.logger.debug(f"Splitting very long sentence of {len(sentence)} chars")
                                
                                # First try to split by phrases/clauses
                                phrases = re.split(r'(?<=[,;:])\s+', sentence)
                                
                                phrase_chunk = ""
                                for phrase in phrases:
                                    if len(phrase_chunk) + len(phrase) + 1 <= safe_max_size:
                                        if phrase_chunk:
                                            phrase_chunk += " " + phrase
                                        else:
                                            phrase_chunk = phrase
                                    else:
                                        # Save current phrase chunk
                                        if phrase_chunk:
                                            chunks.append(phrase_chunk)
                                        
                                        # If phrase itself is too long, split arbitrarily
                                        if len(phrase) > safe_max_size:
                                            # Split at word boundaries if possible
                                            words = phrase.split()
                                            word_chunk = ""
                                            
                                            for word in words:
                                                if len(word_chunk) + len(word) + 1 <= safe_max_size:
                                                    if word_chunk:
                                                        word_chunk += " " + word
                                                    else:
                                                        word_chunk = word
                                                else:
                                                    if word_chunk:
                                                        chunks.append(word_chunk)
                                                    
                                                    # If single word is too long (rare), split arbitrarily
                                                    if len(word) > safe_max_size:
                                                        for i in range(0, len(word), safe_max_size):
                                                            chunks.append(word[i:i+safe_max_size])
                                                    else:
                                                        word_chunk = word
                                            
                                            # Add final word chunk
                                            if word_chunk:
                                                chunks.append(word_chunk)
                                        else:
                                            phrase_chunk = phrase
                                
                                # Add final phrase chunk
                                if phrase_chunk:
                                    chunks.append(phrase_chunk)
                            else:
                                current_chunk = sentence
                else:
                    # Add paragraph to current chunk or start a new chunk
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
            
            # Add final chunk if not empty
            if current_chunk:
                chunks.append(current_chunk)
            
            # Final verification: no chunk should exceed our safe limit
            verified_chunks = []
            for chunk in chunks:
                if len(chunk) > safe_max_size:
                    # If a chunk is still too large, force split it
                    self.logger.warning(f"Found chunk of {len(chunk)} chars > {safe_max_size} limit, force splitting")
                    for i in range(0, len(chunk), safe_max_size):
                        verified_chunks.append(chunk[i:i+safe_max_size])
                else:
                    verified_chunks.append(chunk)
            
            # Validate chunks
            total_chars = sum(len(chunk) for chunk in verified_chunks)
            expected_chars = len(text.strip())
            
            self.logger.info(f"Split text into {len(verified_chunks)} chunks with total {total_chars} chars (original: {expected_chars} chars)")
            
            # Alert if we lost significant content
            if total_chars < expected_chars * 0.95:
                self.logger.warning(f"Possible content loss during text chunking: {expected_chars} vs {total_chars} chars")
            
            # Ensure we don't have any empty chunks
            verified_chunks = [chunk for chunk in verified_chunks if chunk.strip()]
            
            # Final safety check
            max_chunk_length = max((len(chunk) for chunk in verified_chunks), default=0)
            if max_chunk_length > 4000:
                self.logger.error(f"Text chunking failed! Max chunk size is {max_chunk_length}, exceeding OpenAI's limit")
                # Emergency fallback to character chunking
                verified_chunks = []
                for i in range(0, len(text), 3800):  # Using 3800 to be extra safe
                    verified_chunks.append(text[i:i+3800])
                self.logger.info(f"Emergency character chunking created {len(verified_chunks)} chunks")
                
            return verified_chunks
            
        except Exception as e:
            self.logger.error(f"Error splitting text into chunks: {e}")
            # Fallback to simple chunking at 3800 characters (well under the 4096 limit)
            self.logger.warning("Using fallback simple chunking method")
            chunks = []
            safe_size = 3800  # Extra safe limit
            
            # Last resort - just split every N characters
            for i in range(0, len(text), safe_size):
                chunks.append(text[i:i+safe_size])
            
            self.logger.info(f"Fallback chunking created {len(chunks)} chunks")
            return chunks

    def test_api_key(self) -> bool:
        """Test if the API key is valid."""
        try:
            # Import our helper to get a clean OpenAI client
            from ..utils.openai_helper import get_openai_client
            from ..config_manager import ConfigManager
            
            # Get API key from config manager
            config_manager = ConfigManager()
            api_key = config_manager.get_api_key()
            
            if not api_key:
                self.logger.warning("No API key configured")
                return False
            
            try:
                # Create a clean client using our helper  
                client = get_openai_client(api_key)
                
                # Test the TTS API with a minimal request
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input="This is a test of the OpenAI API key.",
                    response_format="mp3"
                )
            except Exception as e:
                self.logger.error(f"API key validation failed: {e}")
                return False
            return True
        except Exception as e:
            self.error_handler.log_error(e, {'context': 'API key validation'})
            return False

    def generate_audio(self, text: str, settings: TTSSettings) -> AudioSegment:
        """Generate audio from text using TTS."""
        temp_path = None
        try:
            self.logger.info(f"Generating audio from text ({len(text)} chars)")
            
            # Import our helper to get a clean OpenAI client
            from ..utils.openai_helper import get_openai_client
            from ..config_manager import ConfigManager
            
            # Get API key from config manager
            config_manager = ConfigManager()
            api_key = config_manager.get_api_key()
            
            if not api_key:
                raise ValueError("No API key configured")
                
            # Validate input text
            if not text or not text.strip():
                self.logger.error("Empty text provided for TTS generation")
                raise ValueError("Cannot generate audio from empty text")
            
            # Create a temporary file for audio
            temp_path = None
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                temp_path = tmp.name
                self.logger.debug(f"Created temporary file: {temp_path}")
            
            # Trap any format errors early
            if not os.path.exists(temp_path):
                self.logger.error(f"Failed to create temporary file at {temp_path}")
                raise IOError(f"Failed to create temporary file at {temp_path}")
            
            # Apply text enhancements for emotional style
            enhanced_text = self._enhance_text_for_emotion(text, settings.style, settings.emotion)
            self.logger.info(f"Enhanced text with style '{settings.style}' and emotion '{settings.emotion}'")
            
            # OpenAI TTS API has a 4096 character limit
            # We'll split the text into chunks and process each one separately if needed
            max_chunk_size = 4000  # Safe limit to stay under the 4096 character API restriction
            
            # Always split the text into chunks to be safe, even for smaller texts
            total_chars = len(enhanced_text)
            self.logger.info(f"Preparing text ({total_chars} chars) for processing")
            
            # Split text into manageable chunks for the API
            chunks = self._split_text_to_chunks(enhanced_text, max_chunk_size)
            self.logger.info(f"Split text into {len(chunks)} chunks (each ≤ {max_chunk_size} chars) for processing")
            
            # Process each chunk and combine the audio
            combined_audio = None
            
            # Validate our chunks before processing
            if not chunks:
                self.logger.error(f"No text chunks to process! Original text length: {len(enhanced_text)}")
                raise ValueError("Text chunking failed - no chunks created")
                
            # Log chunk details for debugging
            total_chunk_chars = sum(len(c) for c in chunks)
            self.logger.info(f"Preparing to process {len(chunks)} chunks with total {total_chunk_chars} characters")
            
            for i, text_chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(text_chunk)} chars)")
                
                # Generate audio with OpenAI TTS API
                try:
                    # Create a clean client using our helper
                    client = get_openai_client(api_key)
                    
                    # Call the API with retry logic
                    max_retries = 3
                    response = None
                    
                    for retry in range(max_retries):
                        try:
                            self.logger.info(f"Calling OpenAI TTS API for chunk {i+1} (attempt {retry+1})")
                            response = client.audio.speech.create(
                                model=settings.model,
                                voice=settings.voice,
                                speed=settings.speed,
                                input=text_chunk,
                                response_format="mp3"
                            )
                            break
                        except Exception as e:
                            if retry == max_retries - 1:
                                raise
                            self.logger.warning(f"TTS API call failed (attempt {retry+1}): {e}, retrying...")
                            time.sleep(1)  # Brief delay before retry
                    
                    if response is None:
                        raise ValueError("Failed to get response from OpenAI TTS API after multiple attempts")
                        
                    # Create a temp file for this chunk
                    chunk_temp_path = None
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as chunk_tmp:
                        chunk_temp_path = chunk_tmp.name
                    
                    # Save the audio to the temporary file
                    with open(chunk_temp_path, 'wb') as f:
                        f.write(response.content)
                        
                    # Verify the file was written correctly
                    if os.path.getsize(chunk_temp_path) == 0:
                        raise ValueError(f"OpenAI returned empty audio content for chunk {i+1}")
                    
                    # Load the audio segment
                    chunk_audio = AudioSegment.from_mp3(chunk_temp_path)
                    self.logger.info(f"Generated audio for chunk {i+1} with duration: {len(chunk_audio)/1000:.2f} seconds")
                    
                    # Add to combined audio
                    if combined_audio is None:
                        combined_audio = chunk_audio
                    else:
                        combined_audio += chunk_audio
                    
                    # Clean up temp file
                    if chunk_temp_path and os.path.exists(chunk_temp_path):
                        try:
                            os.unlink(chunk_temp_path)
                        except Exception as e:
                            self.logger.warning(f"Error removing chunk temp file {chunk_temp_path}: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing chunk {i+1}: {e}")
                    raise ValueError(f"Error generating audio for text chunk {i+1}: {str(e)}")
            
            # Save the combined audio to the main temp file
            if combined_audio is None:
                raise ValueError("Failed to generate any audio")
                
            combined_audio.export(temp_path, format="mp3")
            
            # Verify the file was written correctly
            if os.path.getsize(temp_path) == 0:
                raise ValueError("Generated empty audio file")
            
            # Load the audio segment for consistent return type
            audio = AudioSegment.from_mp3(temp_path)
            self.logger.info(f"Combined audio generated with total duration: {len(audio)/1000:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error in OpenAI TTS API: {e}")
            raise ValueError(f"Error generating audio: {str(e)}")
        
        # Apply enhancements if requested
        if settings.enhance:
            try:
                audio = self.enhance_audio(audio, settings)
            except Exception as e:
                self.logger.error(f"Error applying enhancements: {e}")
                # Continue with unenhanced audio rather than failing
        
        # Apply style-specific audio effects
        try:
            audio = self._apply_audio_style_effects(audio, settings.style)
        except Exception as e:
            self.logger.error(f"Error applying style effects: {e}")
            # Continue with base audio rather than failing
        
        # Final validation
        if not isinstance(audio, AudioSegment):
            self.logger.error(f"Invalid audio object after processing: {type(audio)}")
            raise ValueError(f"Audio processing failed to return a valid AudioSegment object")
            
        self.logger.info(f"Successfully generated audio with duration: {len(audio)/1000:.2f} seconds")
        return audio
            
    def cleanup(self):
        """Clean up resources."""
        try:
            # In this implementation, there's no specific cleanup needed for the TTS engine
            # But this is a good place for any future cleanup operations
            self.logger.debug("TTS engine cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")