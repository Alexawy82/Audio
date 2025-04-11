"""
Audio formats module for DocToAudiobook.
"""

from enum import Enum
from typing import Dict, Any

class AudioFormat(Enum):
    """Supported audio formats."""
    MP3 = 'mp3'
    WAV = 'wav'
    OGG = 'ogg'
    M4A = 'm4a'
    FLAC = 'flac'

class AudioFormats:
    """Handles audio format operations."""
    
    @staticmethod
    def get_format_info(format: AudioFormat) -> Dict[str, Any]:
        """Get information about an audio format."""
        format_info = {
            AudioFormat.MP3: {
                'extension': 'mp3',
                'mime_type': 'audio/mpeg',
                'description': 'MPEG-1 Audio Layer III',
                'compressed': True
            },
            AudioFormat.WAV: {
                'extension': 'wav',
                'mime_type': 'audio/wav',
                'description': 'Waveform Audio File Format',
                'compressed': False
            },
            AudioFormat.OGG: {
                'extension': 'ogg',
                'mime_type': 'audio/ogg',
                'description': 'Ogg Vorbis',
                'compressed': True
            },
            AudioFormat.M4A: {
                'extension': 'm4a',
                'mime_type': 'audio/mp4',
                'description': 'MPEG-4 Audio',
                'compressed': True
            },
            AudioFormat.FLAC: {
                'extension': 'flac',
                'mime_type': 'audio/flac',
                'description': 'Free Lossless Audio Codec',
                'compressed': True
            }
        }
        return format_info.get(format, {})
        
    @staticmethod
    def get_supported_formats() -> list:
        """Get list of supported audio formats."""
        return [format.value for format in AudioFormat]
        
    @staticmethod
    def is_format_supported(format: str) -> bool:
        """Check if a format is supported."""
        return format.lower() in AudioFormats.get_supported_formats() 