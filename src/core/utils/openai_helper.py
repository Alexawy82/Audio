"""
OpenAI Helper Module
Utilities for handling OpenAI API interactions safely
"""

import os
import sys
import logging
import httpx  # Import httpx
from openai import OpenAI  # Import OpenAI at the module level

logger = logging.getLogger(__name__)

def get_openai_client(api_key: str = None) -> OpenAI:
    """
    Get a clean OpenAI client instance with proxy settings disabled.
    
    Args:
        api_key (str, optional): The OpenAI API key. If not provided, will use environment variable.
        
    Returns:
        OpenAI: A configured OpenAI client instance.
    """
    try:
        # Force disable all proxy settings environment variables
        # (Still good practice, though we override the http client below)
        os.environ["HTTP_PROXY"] = ""
        os.environ["HTTPS_PROXY"] = ""
        os.environ["http_proxy"] = ""
        os.environ["https_proxy"] = ""
        os.environ["OPENAI_PROXY"] = ""
        
        # Remove any existing proxy settings from environment
        for key in list(os.environ.keys()):
            if key.lower().endswith('_proxy'):
                try:
                    del os.environ[key]
                except Exception:
                    pass # Ignore if deletion fails
        
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("No API key provided and OPENAI_API_KEY environment variable is not set")
        
        # Create OpenAI client with API key, explicitly without using proxies
        # The new OpenAI client doesn't accept 'proxies' directly anymore
        client = OpenAI(
            api_key=api_key,
            # Configure the underlying httpx client via base_url's transport
            http_client=httpx.Client(transport=httpx.HTTPTransport(proxy=None)),
            timeout=60.0  # Set a reasonable timeout
        )
        
        # Verify client is working with a simple request
        try:
            client.models.list() 
            logger.debug("OpenAI client verified successfully.")
        except Exception as e:
            logger.error(f"Failed to verify OpenAI client after creation: {str(e)}")
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
        
        return client
        
    except ImportError as e:
        logger.error(f"Failed to import required library: {e}")
        raise ImportError(f"Failed to import required library: {e}. Make sure 'openai' and 'httpx' are installed.")
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {e}")
        # Ensure original exception type and message are preserved if possible
        if isinstance(e, ValueError):
             raise
        raise RuntimeError(f"An unexpected error occurred while creating the OpenAI client: {str(e)}") 