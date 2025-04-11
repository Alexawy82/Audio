"""
Bookmark management module for handling audiobook bookmarks.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import mutagen
from mutagen.id3 import ID3, TXXX

class BookmarkManager:
    """Handles audiobook bookmark creation and management."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def create_bookmark_data(self, audiobook_id: str, chapter_info: List[Dict],
                           chapter_times: List[Dict]) -> Dict[str, Any]:
        """
        Create bookmark data structure.
        
        Args:
            audiobook_id: Unique identifier for the audiobook
            chapter_info: List of chapter information dictionaries
            chapter_times: List of chapter timing information
            
        Returns:
            Bookmark data dictionary
        """
        try:
            bookmark_data = {
                'audiobook_id': audiobook_id,
                'created_at': datetime.now().isoformat(),
                'last_position': 0,
                'last_chapter': 0,
                'play_history': [],
                'chapters': []
            }
            
            # Add chapter information
            for i, (chapter, times) in enumerate(zip(chapter_info, chapter_times)):
                bookmark_data['chapters'].append({
                    'index': i,
                    'title': chapter['title'],
                    'start_time': times['start'],
                    'duration': times['end'] - times['start']
                })
                
            return bookmark_data
            
        except Exception as e:
            self.logger.error(f"Error creating bookmark data: {e}")
            raise
            
    def save_bookmark_data(self, bookmark_data: Dict[str, Any], 
                          output_dir: str) -> str:
        """
        Save bookmark data to file and update audio metadata.
        
        Args:
            bookmark_data: Bookmark data dictionary
            output_dir: Output directory path
            
        Returns:
            Path to bookmark file
            
        Raises:
            IOError: If file operations fail
        """
        try:
            # Create bookmark file path
            bookmark_file = Path(output_dir) / f"{bookmark_data['audiobook_id']}_bookmarks.json"
            
            # Save to JSON file
            with open(bookmark_file, 'w') as f:
                json.dump(bookmark_data, f, indent=2)
                
            # Update audio file metadata
            audio_file = Path(output_dir) / "final_audiobook.mp3"
            if audio_file.exists():
                try:
                    audio = ID3(str(audio_file))
                    audio.add(TXXX(encoding=3, desc='BookmarkData',
                                 text=json.dumps(bookmark_data)))
                    audio.save()
                except Exception as e:
                    self.logger.warning(f"Could not update audio metadata: {e}")
                    
            self.logger.info(f"Saved bookmark data to {bookmark_file}")
            return str(bookmark_file)
            
        except Exception as e:
            self.logger.error(f"Error saving bookmark data: {e}")
            raise
            
    def create_bookmarks(self, chapters: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Create bookmarks for a list of chapters.
        
        Args:
            chapters: List of (title, text) tuples for each chapter
            
        Returns:
            Bookmark data dictionary
        """
        try:
            # Generate a unique ID for the audiobook
            audiobook_id = str(uuid.uuid4())
            
            # Create chapter info and timing data
            chapter_info = []
            chapter_times = []
            
            start_time = 0
            for i, (title, text) in enumerate(chapters):
                # Estimate chapter duration: 
                # Average speaking rate is ~150 words per minute, or ~2.5 words per second
                # Average word length is ~5 characters
                char_count = len(text)
                words = char_count / 5
                duration = words / 2.5  # seconds
                
                chapter_info.append({
                    'title': title,
                    'index': i
                })
                
                chapter_times.append({
                    'start': start_time,
                    'end': start_time + duration
                })
                
                start_time += duration
            
            # Create bookmark data using the existing method
            return self.create_bookmark_data(audiobook_id, chapter_info, chapter_times)
            
        except Exception as e:
            self.logger.error(f"Error creating bookmarks: {e}")
            raise
    
    def save_bookmarks(self, bookmark_data: Dict[str, Any], bookmark_file: str) -> None:
        """
        Save bookmarks to a file.
        
        Args:
            bookmark_data: Bookmark data dictionary
            bookmark_file: Path to save the bookmark file
            
        Raises:
            IOError: If file operations fail
        """
        try:
            # Ensure the directory exists
            Path(bookmark_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            with open(bookmark_file, 'w') as f:
                json.dump(bookmark_data, f, indent=2)
            
            self.logger.info(f"Saved bookmarks to {bookmark_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving bookmarks: {e}")
            raise
            
    def update_bookmark(self, bookmark_file: str, position: float,
                       chapter_index: int) -> None:
        """
        Update bookmark with current position and chapter.
        
        Args:
            bookmark_file: Path to bookmark file
            position: Current playback position in seconds
            chapter_index: Current chapter index
            
        Raises:
            FileNotFoundError: If bookmark file doesn't exist
            ValueError: If position or chapter index is invalid
        """
        try:
            if not Path(bookmark_file).exists():
                raise FileNotFoundError(f"Bookmark file not found: {bookmark_file}")
                
            # Load existing bookmark data
            with open(bookmark_file, 'r') as f:
                bookmark_data = json.load(f)
                
            # Update position and chapter
            bookmark_data['last_position'] = position
            bookmark_data['last_chapter'] = chapter_index
            
            # Add to play history
            bookmark_data['play_history'].append({
                'timestamp': datetime.now().isoformat(),
                'position': position,
                'chapter': chapter_index
            })
            
            # Limit play history to last 100 entries
            if len(bookmark_data['play_history']) > 100:
                bookmark_data['play_history'] = bookmark_data['play_history'][-100:]
                
            # Save updated data
            with open(bookmark_file, 'w') as f:
                json.dump(bookmark_data, f, indent=2)
                
            self.logger.info(f"Updated bookmark at position {position}")
            
        except Exception as e:
            self.logger.error(f"Error updating bookmark: {e}")
            raise 