"""
Base OCR Provider - Abstract class for all OCR providers
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class OCRTextBlock:
    """Represents a single detected text block"""
    text: str
    confidence: float
    box: Optional[List[List[float]]] = None  # Bounding box coordinates


@dataclass
class OCRResult:
    """Standardized OCR result across all providers"""
    status: str  # "success" or "failed"
    raw_text: str
    details: List[OCRTextBlock]
    provider: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "raw_text": self.raw_text,
            "details": [
                {"text": d.text, "confidence": d.confidence, "box": d.box}
                for d in self.details
            ],
            "provider": self.provider,
            "error": self.error
        }


class BaseOCRProvider(ABC):
    """Abstract base class for OCR providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the provider"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI"""
        pass
    
    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for provider-specific configuration"""
        pass
    
    @abstractmethod
    def process(self, file_bytes: bytes, config: Dict[str, Any] = None) -> OCRResult:
        """
        Process image/PDF bytes and return OCR result
        
        Args:
            file_bytes: Raw bytes of the file (image or PDF)
            config: Provider-specific configuration options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider configuration (e.g., API key)"""
        pass
