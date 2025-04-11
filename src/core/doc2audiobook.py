"""
Document to Audiobook converter module.
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from pathlib import Path
from pydub import AudioSegment
from .document_processor import DocumentProcessor
from .audio_processor import AudioProcessor
from .chapter_manager import ChapterManager
from .bookmark_manager import BookmarkManager
from .tts import enhanced
EnhancedTTS = enhanced.EnhancedTTS
from .config_manager import ConfigManager
from .utils.error import error_handler
from .models.tts import TTSSettings, AudioFile, ConversionResult

class DocToAudiobook:
    """Converts documents to audiobooks."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the converter."""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.audio_processor = AudioProcessor()
        self.chapter_manager = ChapterManager()
        self.bookmark_manager = BookmarkManager()
        self.tts_engine = EnhancedTTS()
        
    @property
    def voice_settings(self) -> Dict[str, Any]:
        """Get the voice settings from config manager."""
        return self.config_manager.get_voice_settings()
        
    @property
    def output_settings(self) -> Dict[str, Any]:
        """Get the output settings from config manager."""
        return self.config_manager.get_audio_settings()

    def create_audiobook(self, 
                        input_file: str, 
                        output_dir: str,
                        style_map: Dict[str, Any] = None,
                        max_chapters: int = 30) -> Union[Dict[str, Any], Tuple[str, List[Dict[str, Any]]]]:
        """
        Convert a document to an audiobook.
        
        Args:
            input_file: Path to the input document
            output_dir: Directory to save output files
            style_map: Dictionary of style settings
            max_chapters: Maximum number of chapters to process
            
        Returns:
            Either a dictionary with conversion results or a tuple of (status, output_files)
        """
        try:
            # Get settings from config
            voice_settings = TTSSettings.from_dict(self.voice_settings)
            audio_settings = self.output_settings.copy()  # Make a copy to avoid modifying the original
            
            # Ensure we have the necessary fields for audio processing
            if 'normalize' not in audio_settings:
                audio_settings['normalize'] = True
            if 'compression' not in audio_settings:
                audio_settings['compression'] = False
            
            # Override with style_map if provided
            if style_map:
                for key, value in style_map.items():
                    if hasattr(voice_settings, key):
                        setattr(voice_settings, key, value)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Process document
            text, metadata = self.document_processor.process_document(input_file)
            
            # Log the total document size to verify content
            self.logger.info(f"Processed document with {len(text)} total characters")
            if len(text) > 50000:
                self.logger.info(f"Large document detected ({len(text)} chars) - first 100 chars: {text[:100]}...")
                self.logger.info(f"Large document - last 100 chars: ...{text[-100:]}")
            
            # Detect chapters
            self.logger.info(f"Detecting chapters from text of length {len(text)}")
            chapters = self.chapter_manager.detect_chapters(text, max_chapters=max_chapters)
            
            # Generate audio for each chapter
            output_files = []
            successful_chapters = 0
            
            for i, chapter_tuple in enumerate(chapters):
                try:
                    # Unpack the tuple
                    chapter_title, chapter_text = chapter_tuple
                    
                    # Skip empty chapters
                    if not chapter_text or not chapter_text.strip():
                        self.logger.warning(f"Skipping empty chapter {i+1}")
                        continue
                        
                    self.logger.info(f"Processing chapter {i+1}: {chapter_title} ({len(chapter_text)} chars)")
                
                    # Generate speech
                    audio_path = os.path.join(output_dir, f"chapter_{i+1:03d}_temp.mp3")
                    
                    # Call OpenAI TTS API through our enhanced TTS engine
                    self.logger.info(f"Generating audio for chapter {i+1} with style: {voice_settings.style}")
                    audio = self.tts_engine.generate_audio(chapter_text, voice_settings)
                
                    # Validate audio output
                    if audio is None:
                        self.logger.error("TTS engine returned None")
                        raise ValueError("TTS engine returned None")
                        
                    if not isinstance(audio, AudioSegment):
                        self.logger.error(f"Invalid audio object returned from TTS engine: {type(audio)}")
                        raise ValueError(f"TTS engine returned invalid audio type: {type(audio)}")
                    
                    # Process audio with settings
                    self.logger.info(f"Processing audio with settings: {audio_settings}")
                    processed_audio = self.audio_processor.process_audio(audio, audio_settings)
                    
                    # Save chapter audio
                    chapter_filename = f"chapter_{i+1:03d}.mp3"
                    chapter_path = os.path.join(output_dir, chapter_filename)
                    processed_audio.export(chapter_path, format="mp3")
                    
                    # Get audio duration
                    duration = len(processed_audio) / 1000.0  # milliseconds to seconds
                    
                    # Add to output files
                    output_files.append({
                        'name': chapter_filename,
                        'path': chapter_path,
                        'title': chapter_title,
                        'duration': duration,
                        'size': os.path.getsize(chapter_path)
                    })
                    
                    successful_chapters += 1
                    self.logger.info(f"Successfully processed chapter {i+1}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing chapter {i+1}: {e}")
                    # Continue with next chapter instead of failing the whole process
                
            # Check if we have any successful chapters
            if successful_chapters == 0:
                self.logger.error("No chapters were successfully processed")
                return {
                    "status": "failed",
                    "error": "No chapters were successfully processed",
                    "output_files": []
                }
                
            # Verify we processed a reasonable amount of the original text
            # Calculate approximate content percentage processed
            total_chars_processed = sum(len(chapter_text) for _, chapter_text in chapters[:successful_chapters])
            content_percentage = (total_chars_processed / len(text)) * 100 if text else 0
            self.logger.info(f"Processed approximately {content_percentage:.1f}% of the original text ({total_chars_processed}/{len(text)} chars)")
            
            # For diagnostics: Log the individual chapter lengths
            for i, (title, chapter_text) in enumerate(chapters):
                self.logger.info(f"Chapter {i+1}: '{title}' - {len(chapter_text)} characters")
                
            # Create bookmarks if we have chapters
            try:
                bookmarks = self.bookmark_manager.create_bookmarks(chapters)
                bookmark_path = os.path.join(output_dir, 'bookmarks.json')
                self.bookmark_manager.save_bookmarks(bookmarks, bookmark_path)
                self.logger.info(f"Created bookmarks at {bookmark_path}")
            except Exception as e:
                self.logger.error(f"Error creating bookmarks: {e}")
                # Continue without bookmarks
            
            # Combine all chapter files into a single complete audiobook
            try:
                self.logger.info(f"Combining {successful_chapters} chapters into complete audiobook")
                
                # Get all chapter file paths
                chapter_paths = [file_info['path'] for file_info in output_files]
                
                # Sort chapter paths by chapter number to ensure correct order
                # Extract chapter numbers and sort accordingly
                def get_chapter_number(path):
                    # Extract the chapter number from filenames like chapter_001.mp3, chapter_002.mp3, etc.
                    import re
                    match = re.search(r'chapter_(\d+)', os.path.basename(path))
                    if match:
                        return int(match.group(1))
                    return 0  # Default to 0 if pattern doesn't match
                
                chapter_paths.sort(key=get_chapter_number)
                
                # Set final audiobook path
                final_audiobook_path = os.path.join(output_dir, "complete_audiobook.mp3")
                
                # Combine audio files
                combine_success = self.audio_processor.combine_audio_files(chapter_paths, final_audiobook_path)
                
                if combine_success and os.path.exists(final_audiobook_path):
                    # Get audio info for the complete file
                    audio_info = self.audio_processor.get_audio_info(final_audiobook_path)
                    
                    # Add combined audiobook to output files
                    output_files.append({
                        'name': "complete_audiobook.mp3",
                        'path': final_audiobook_path,
                        'title': "Complete Audiobook",
                        'duration': audio_info['duration'],
                        'size': os.path.getsize(final_audiobook_path)
                    })
                    
                    self.logger.info(f"Successfully created complete audiobook at {final_audiobook_path}")
                    self.logger.info(f"Complete audiobook duration: {audio_info['duration']:.2f} seconds, size: {os.path.getsize(final_audiobook_path)} bytes")
                else:
                    self.logger.error("Failed to create complete audiobook")
            except Exception as e:
                self.logger.error(f"Error combining chapters into complete audiobook: {e}")
                # Continue without complete audiobook
            
            # Create result object
            status = "completed" if successful_chapters == len(chapters) else "partial"
            
            # Add stats to metadata
            metadata.update({
                "total_chapters": len(chapters),
                "successful_chapters": successful_chapters,
                "processing_status": status
            })
            
            result_dict = {
                "status": status,
                "output_files": output_files,
                "metadata": metadata
            }
            
            self.logger.info(f"Conversion completed with status: {status}, {successful_chapters}/{len(chapters)} chapters processed")
            return result_dict
            
        except Exception as e:
            error_handler.log_error(e, {
                'input_file': input_file,
                'output_dir': output_dir,
                'style_map': style_map
            })
            # Return structured failure result
            return {
                "status": "failed",
                "error": str(e),
                "output_files": []
            }
            
    def get_available_voices(self) -> List[str]:
        """Get list of available voices."""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return ["tts-1", "tts-1-hd"]
        
    def get_voice_style_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get voice style presets."""
        return {
            "neutral": {
                "style": "neutral", 
                "emotion": "", 
                "speed": 1.0,
                "equalization": False,
                "compression": False
            },
            "cheerful": {
                "style": "cheerful", 
                "emotion": "happy", 
                "speed": 1.15,  # More pronounced speed increase
                "equalization": True,  # Enable EQ for cheerful tone
                "compression": True    # Enable compression for cheerful tone
            },
            "serious": {
                "style": "serious", 
                "emotion": "serious", 
                "speed": 0.9,
                "equalization": True,
                "compression": False
            },
            "excited": {
                "style": "excited", 
                "emotion": "excited", 
                "speed": 1.25,  # More pronounced speed increase
                "equalization": True,
                "compression": True
            },
            "sad": {
                "style": "sad", 
                "emotion": "sad", 
                "speed": 0.8,  # More pronounced slowdown
                "equalization": True,
                "compression": False
            },
            "dramatic": {
                "style": "dramatic",
                "emotion": "dramatic",
                "speed": 0.95,
                "equalization": True,
                "compression": True
            }
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            self.tts_engine.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}") 