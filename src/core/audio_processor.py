"""
Audio processor module for handling audio file processing and manipulation.
"""

import os
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import shutil

class AudioProcessor:
    """Handles audio file processing and manipulation."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.logger = logging.getLogger(__name__)
        
        # Set ffmpeg path
        ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            AudioSegment.converter = ffmpeg_path
            self.logger.info(f"Using ffmpeg from: {ffmpeg_path}")
        else:
            # Try to find ffmpeg in system PATH
            ffmpeg_in_path = shutil.which('ffmpeg')
            if ffmpeg_in_path:
                AudioSegment.converter = ffmpeg_in_path
                self.logger.info(f"Using system ffmpeg from: {ffmpeg_in_path}")
            else:
                self.logger.warning("ffmpeg not found in bin directory or system PATH")
        
    def process_audio(self, audio: AudioSegment, settings: dict = None) -> AudioSegment:
        """
        Process audio with various enhancements.
        
        Args:
            audio: AudioSegment object to process
            settings: Dictionary with processing settings
            
        Returns:
            Processed AudioSegment
        """
        self.logger.info(f"Processing audio with type: {type(audio)}")
        
        # Validate input
        if audio is None:
            self.logger.error("Cannot process None audio")
            raise ValueError("Audio input cannot be None")
            
        if not isinstance(audio, AudioSegment):
            self.logger.error(f"Invalid input: expected AudioSegment, got {type(audio)}")
            raise TypeError(f"Expected AudioSegment object, got {type(audio)}")
        
        # Check if audio has valid data
        if len(audio) == 0:
            self.logger.warning("Received empty audio segment (0 ms duration)")
            # Return empty audio rather than raising an error
            return audio
            
        if settings is None:
            settings = {}
            
        self.logger.info(f"Audio settings: {settings}")
            
        try:
            # Apply processing steps based on settings
            normalize_audio = settings.get('normalize', True)
            compress_audio = settings.get('compression', False)
            target_lufs = settings.get('target_lufs', -16.0)
            remove_silence = settings.get('remove_silence', False)
            
            # Create a copy to avoid modifying the original
            # AudioSegment doesn't have a copy() method, so we use a slice operation to clone it
            processed_audio = audio[:]
            
            # Apply processing steps
            if normalize_audio:
                self.logger.info("Applying normalization")
                processed_audio = self._normalize_audio(processed_audio, target_lufs)
                
            if compress_audio:
                self.logger.info("Applying compression")
                processed_audio = self._compress_dynamic_range(processed_audio)
                
            if remove_silence:
                self.logger.info("Removing silence")
                processed_audio = self._remove_silence(processed_audio)
            
            self.logger.info(f"Audio processing complete. Original duration: {len(audio)/1000:.2f}s, Processed duration: {len(processed_audio)/1000:.2f}s")
            return processed_audio
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            # In case of error, return the original audio instead of failing
            self.logger.warning("Returning original unprocessed audio due to processing error")
            return audio
            
    def combine_audio_files(self, input_files: List[str], output_file: str) -> bool:
        """Combine multiple audio files into a single file.
        
        Args:
            input_files: List of input audio file paths
            output_file: Path to save the combined audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not input_files:
                self.logger.error("No input files provided")
                return False
                
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Combine audio segments
            combined = AudioSegment.empty()
            for file_path in input_files:
                audio = AudioSegment.from_file(file_path)
                combined += audio
                
            # Export combined audio
            combined.export(output_file, format='mp3')
            return True
            
        except Exception as e:
            self.logger.error(f"Error combining audio files: {e}")
            return False
            
    def _normalize_audio(self, audio: AudioSegment, target_lufs: float) -> AudioSegment:
        """Normalize audio to target LUFS level."""
        try:
            return normalize(audio, headroom=0.1)
        except Exception as e:
            self.logger.error(f"Error normalizing audio: {e}")
            raise
            
    def _compress_dynamic_range(self, audio: AudioSegment) -> AudioSegment:
        """Compress dynamic range of audio."""
        try:
            return compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
        except Exception as e:
            self.logger.error(f"Error compressing dynamic range: {e}")
            raise
            
    def _remove_silence(self, audio: AudioSegment, 
                       silence_threshold: float = -50.0,
                       min_silence_len: int = 1000) -> AudioSegment:
        """Remove silence from audio."""
        try:
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Find silent regions
            silent_regions = np.where(np.abs(samples) < 10 ** (silence_threshold / 20))[0]
            
            # Group consecutive silent samples
            silent_groups = []
            current_group = []
            
            for i in range(len(silent_regions)):
                if not current_group or silent_regions[i] - current_group[-1] == 1:
                    current_group.append(silent_regions[i])
                else:
                    if len(current_group) >= min_silence_len:
                        silent_groups.append((current_group[0], current_group[-1]))
                    current_group = [silent_regions[i]]
                    
            if len(current_group) >= min_silence_len:
                silent_groups.append((current_group[0], current_group[-1]))
                
            # Remove silent regions
            if silent_groups:
                # Create new audio segment
                new_audio = AudioSegment.empty()
                start = 0
                
                for start_silence, end_silence in silent_groups:
                    # Add non-silent segment
                    if start_silence > start:
                        new_audio += audio[start:start_silence]
                    start = end_silence + 1
                    
                # Add remaining audio
                if start < len(audio):
                    new_audio += audio[start:]
                    
                return new_audio
                
            return audio
            
        except Exception as e:
            self.logger.error(f"Error removing silence: {e}")
            raise
            
    def get_audio_duration(self, file_path: str) -> float:
        """Get duration of audio file in seconds."""
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            raise
            
    def get_audio_info(self, file_path: str) -> dict:
        """Get information about audio file."""
        try:
            audio = AudioSegment.from_file(file_path)
            return {
                'duration': len(audio) / 1000.0,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'frame_count': audio.frame_count(),
                'max_amplitude': audio.max,
                'rms': audio.rms
            }
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            raise 