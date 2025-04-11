"""
Utility modules for DocToAudiobook.

This package provides utility functions and classes including:
- Error handling
- Logging setup
- File format helpers
- Text processing utilities
"""

from .error import ErrorHandler, error_handler
from .openai_helper import get_openai_client
# Remove import of non-existent modules
# from .config import ConfigManager
# from .logging import setup_logging
# from .validation import validate_input
# from .formatting import format_duration, format_file_size

__all__ = [
    'ErrorHandler',
    'error_handler',
    'get_openai_client'
    # Remove references to non-existent modules
    # 'ConfigManager',
    # 'setup_logging',
    # 'validate_input',
    # 'format_duration',
    # 'format_file_size'
] 