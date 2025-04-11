"""
Core functionality package for DocToAudiobook.

This package provides the core components for converting 
documents to audiobooks including:
- Document processing
- Text-to-Speech conversion
- Audio processing
- Chapter detection and management
- Bookmark generation
- Configuration management
- Error handling
- Job management
"""

# Import modules directly rather than importing all classes
# to avoid circular dependencies

__all__ = [
    'config_manager',
    'utils',
    'tts',
    'models',
    'document_processor',
    'audio_processor',
    'chapter_manager',
    'bookmark_manager',
    'job_manager',
    'doc2audiobook'
]