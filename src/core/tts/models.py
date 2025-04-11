"""
TTS models module for DocToAudiobook.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TTSSettings(BaseModel):
    """TTS settings and configurations."""
    
    # Voice settings
    voice: str = Field(default="alloy", description="Voice to use for TTS")
    model: str = Field(default="tts-1", description="TTS model to use")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    
    # Audio enhancement settings
    noise_reduction: bool = Field(default=False, description="Apply noise reduction")
    equalization: bool = Field(default=False, description="Apply equalization")
    compression: bool = Field(default=False, description="Apply compression")
    normalize: bool = Field(default=True, description="Normalize audio levels")
    
    # Advanced settings
    chunk_size: int = Field(default=4096, description="Maximum text chunk size")
    max_retries: int = Field(default=3, description="Maximum API retry attempts")
    timeout: int = Field(default=30, description="API timeout in seconds")
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "voice": "alloy",
                "model": "tts-1",
                "speed": 1.0,
                "noise_reduction": False,
                "equalization": False,
                "compression": False,
                "normalize": True,
                "chunk_size": 4096,
                "max_retries": 3,
                "timeout": 30
            }
        }

class TTSResponse(BaseModel):
    """TTS API response model."""
    
    success: bool = Field(description="Whether the TTS request was successful")
    audio_path: Optional[str] = Field(description="Path to generated audio file")
    error: Optional[str] = Field(description="Error message if request failed")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata about the request")
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "audio_path": "/path/to/audio.mp3",
                "error": None,
                "metadata": {
                    "duration": 120.5,
                    "size": 1024000,
                    "format": "mp3"
                }
            }
        } 