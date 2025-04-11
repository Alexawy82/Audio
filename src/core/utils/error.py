"""
Error handling utilities for DocToAudiobook.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps

class ErrorHandler:
    """Central error handling and logging class."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context information."""
        try:
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
        except Exception as e:
            # Fall back to basic logging if structured logging fails
            self.logger.error(f"Error logging failed: {e}. Original error: {error}")
            
    def wrap_method(self, method: Callable) -> Callable:
        """Decorator for wrapping methods with error handling."""
        @wraps(method)
        def wrapper(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                self.log_error(e, {
                    'method': method.__name__,
                    'args': args,
                    'kwargs': kwargs
                })
                raise
        return wrapper
        
    def handle_errors(self, context: Optional[Dict[str, Any]] = None) -> Callable:
        """Decorator factory for handling errors with specific context."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_context = context.copy() if context else {}
                    error_context.update({
                        'function': func.__name__,
                    })
                    self.log_error(e, error_context)
                    raise
            return wrapper
        return decorator
        
    def handle_api_error(self, error: Exception, status_code: int = 500) -> Dict[str, Any]:
        """Handle API errors and return appropriate response."""
        self.log_error(error)
        return {
            'status': 'error',
            'message': str(error),
            'code': status_code
        }
        
    def api_error_handler(self, func: Callable) -> Callable:
        """Decorator for handling API errors."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = self.handle_api_error(e)
                # This assumes Flask is being used
                from flask import jsonify
                return jsonify(error_response), error_response['code']
        return wrapper

# Create a global instance
error_handler = ErrorHandler() 