"""
Centralized error handling and logging module.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from functools import wraps
from flask import jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ErrorHandler:
    """Handles application errors and logging."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.logger.error(
            "Error occurred: %s\nContext: %s\nTraceback: %s",
            error_info['error'],
            error_info['context'],
            error_info['traceback']
        )
        
    def handle_api_error(self, error: Exception, status_code: int = 500) -> Dict[str, Any]:
        """Handle API errors and return appropriate response."""
        self.log_error(error)
        return {
            'status': 'error',
            'message': str(error),
            'code': status_code
        }
        
    def api_error_handler(self, func):
        """Decorator for handling API errors."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = self.handle_api_error(e)
                return jsonify(error_response), error_response['code']
        return wrapper
        
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message with context."""
        self.logger.info("%s\nContext: %s", message, context or {})
        
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message with context."""
        self.logger.warning("%s\nContext: %s", message, context or {})
        
    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message with context."""
        self.logger.debug("%s\nContext: %s", message, context or {})

# Create global error handler instance
error_handler = ErrorHandler() 