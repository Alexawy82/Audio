"""
Text extraction module for DocToAudiobook.
"""

import logging
from typing import Optional, List, Dict, Any
import re
from ..utils.error import ErrorHandler

class TextExtractor:
    """Handles text extraction and processing."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize text extractor."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
    def extract_chapters(self, text: str) -> List[Dict[str, Any]]:
        """Extract chapters from text."""
        try:
            # Common chapter patterns
            patterns = [
                r'^Chapter\s+\d+.*$',  # Chapter 1, Chapter 2, etc.
                r'^\d+\.\s+.*$',       # 1. Title, 2. Title, etc.
                r'^[IVX]+\.\s+.*$',    # I. Title, II. Title, etc.
                r'^[A-Z]+\s+.*$'       # CHAPTER TITLE, SECTION TITLE, etc.
            ]
            
            chapters = []
            current_chapter = {'title': 'Introduction', 'text': ''}
            
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line matches any chapter pattern
                is_chapter = any(re.match(pattern, line, re.IGNORECASE) for pattern in patterns)
                
                if is_chapter:
                    # Save previous chapter if it has content
                    if current_chapter['text'].strip():
                        chapters.append(current_chapter)
                        
                    # Start new chapter
                    current_chapter = {
                        'title': line,
                        'text': ''
                    }
                else:
                    # Add line to current chapter
                    current_chapter['text'] += line + '\n'
                    
            # Add last chapter if it has content
            if current_chapter['text'].strip():
                chapters.append(current_chapter)
                
            return chapters
            
        except Exception as e:
            self.error_handler.log_error(e, {'text_length': len(text)})
            return [{'title': 'Full Text', 'text': text}]
            
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        try:
            # Remove multiple spaces
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep punctuation
            text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
            
            # Normalize quotes
            text = text.replace('"', '"').replace('"', '"')
            text = text.replace(''', "'").replace(''', "'")
            
            # Normalize dashes
            text = text.replace('–', '-').replace('—', '-')
            
            return text.strip()
            
        except Exception as e:
            self.error_handler.log_error(e, {'text_length': len(text)})
            return text
            
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text."""
        try:
            metadata = {
                'title': None,
                'author': None,
                'date': None,
                'language': None
            }
            
            # Look for title in first few lines
            lines = text.split('\n')[:10]
            for line in lines:
                line = line.strip()
                if not metadata['title'] and len(line) > 10 and len(line) < 100:
                    metadata['title'] = line
                    
            # Look for author in first few lines
            author_patterns = [
                r'by\s+([A-Za-z\s.]+)',
                r'author:\s*([A-Za-z\s.]+)',
                r'written by\s+([A-Za-z\s.]+)'
            ]
            
            for line in lines:
                for pattern in author_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        metadata['author'] = match.group(1).strip()
                        break
                        
            return metadata
            
        except Exception as e:
            self.error_handler.log_error(e, {'text_length': len(text)})
            return {} 