"""
Document formats module for DocToAudiobook.
"""

from enum import Enum
from typing import Dict, Any, Optional

class DocumentFormat(Enum):
    """Supported document formats."""
    DOCX = 'docx'
    PDF = 'pdf'
    TXT = 'txt'
    RTF = 'rtf'
    ODT = 'odt'

class DocumentFormats:
    """Handles document format operations."""
    
    @staticmethod
    def get_format_info(format: DocumentFormat) -> Dict[str, Any]:
        """Get information about a document format."""
        format_info = {
            DocumentFormat.DOCX: {
                'extension': 'docx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'description': 'Microsoft Word Document',
                'supports_metadata': True
            },
            DocumentFormat.PDF: {
                'extension': 'pdf',
                'mime_type': 'application/pdf',
                'description': 'Portable Document Format',
                'supports_metadata': True
            },
            DocumentFormat.TXT: {
                'extension': 'txt',
                'mime_type': 'text/plain',
                'description': 'Plain Text',
                'supports_metadata': False
            },
            DocumentFormat.RTF: {
                'extension': 'rtf',
                'mime_type': 'application/rtf',
                'description': 'Rich Text Format',
                'supports_metadata': False
            },
            DocumentFormat.ODT: {
                'extension': 'odt',
                'mime_type': 'application/vnd.oasis.opendocument.text',
                'description': 'OpenDocument Text',
                'supports_metadata': True
            }
        }
        return format_info.get(format, {})
        
    @staticmethod
    def get_supported_formats() -> list:
        """Get list of supported document formats."""
        return [format.value for format in DocumentFormat]
        
    @staticmethod
    def is_format_supported(format: str) -> bool:
        """Check if a format is supported."""
        return format.lower() in DocumentFormats.get_supported_formats()
        
    @staticmethod
    def get_format_from_extension(extension: str) -> Optional[DocumentFormat]:
        """Get document format from file extension."""
        extension = extension.lower().lstrip('.')
        for format in DocumentFormat:
            if format.value == extension:
                return format
        return None 