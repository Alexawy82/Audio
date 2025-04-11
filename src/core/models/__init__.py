"""
Data models package for DocToAudiobook.

This package provides data models for the application including:
- TTS settings and configurations
- Conversion result models
- Audio file representations
"""

from .tts import TTSSettings, AudioFile, ConversionResult

__all__ = [
    'TTSSettings',
    'AudioFile',
    'ConversionResult'
] 