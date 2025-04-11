"""
TTS models module for DocToAudiobook.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class TTSSettings:
    """TTS settings and configurations."""
    
    # Voice settings
    voice: str = "alloy"
    model: str = "tts-1"
    speed: float = 1.0
    style: str = "neutral"
    emotion: str = ""
    language: str = "en"
    
    # Enhancement settings
    enhance: bool = True
    noise_reduction: bool = False
    equalization: bool = False
    compression: bool = False
    normalize: bool = True
    
    # Advanced settings
    max_chunk_size: int = 4000  # Set to 4000 to respect OpenAI's 4096 character limit
    
    def dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary."""
        return {
            "voice": self.voice,
            "model": self.model,
            "speed": self.speed,
            "style": self.style,
            "emotion": self.emotion,
            "language": self.language,
            "enhance": self.enhance,
            "noise_reduction": self.noise_reduction,
            "equalization": self.equalization,
            "compression": self.compression,
            "normalize": self.normalize,
            "max_chunk_size": self.max_chunk_size
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TTSSettings':
        """Create settings from a dictionary."""
        return cls(
            voice=data.get("voice", "alloy"),
            model=data.get("model", "tts-1"),
            speed=data.get("speed", 1.0),
            style=data.get("style", "neutral"),
            emotion=data.get("emotion", ""),
            language=data.get("language", "en"),
            enhance=data.get("enhance", True),
            noise_reduction=data.get("noise_reduction", False),
            equalization=data.get("equalization", False),
            compression=data.get("compression", False),
            normalize=data.get("normalize", True),
            max_chunk_size=data.get("max_chunk_size", 4000)
        )

@dataclass
class AudioFile:
    """Represents an audio file."""
    
    path: str
    name: str
    size: int = 0
    duration: float = 0.0
    format: str = "mp3"
    
    def dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "duration": self.duration,
            "format": self.format
        }

@dataclass
class ConversionResult:
    """Result of a document to audiobook conversion."""
    
    status: str
    output_files: List[AudioFile] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        return {
            "status": self.status,
            "output_files": [f.dict() for f in self.output_files],
            "error": self.error,
            "metadata": self.metadata
        } 