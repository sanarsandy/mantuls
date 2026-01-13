"""
Google Vision API Provider - Cloud-based OCR using Google Cloud Vision
"""
import base64
import logging
import requests
from typing import Dict, Any, List

from .base import BaseOCRProvider, OCRResult, OCRTextBlock
from utils.image import load_image_from_bytes, resize_for_ocr

logger = logging.getLogger(__name__)

GOOGLE_VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"

# Connection pooling for faster repeated requests
_session: requests.Session = None

def _get_session() -> requests.Session:
    """Get or create a reusable session for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10)
        _session.mount('https://', adapter)
    return _session


class GoogleVisionProvider(BaseOCRProvider):
    """Google Cloud Vision API implementation - Excellent accuracy, cloud-based"""
    
    @property
    def name(self) -> str:
        return "google_vision"
    
    @property
    def display_name(self) -> str:
        return "Google Vision API"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Google Cloud Vision API Key",
                    "format": "password"
                },
                "language_hints": {
                    "type": "array",
                    "title": "Language Hints",
                    "description": "Hint languages for better detection",
                    "items": {"type": "string"},
                    "default": ["id", "en"]
                }
            },
            "required": ["api_key"]
        }
    
    def process(self, file_bytes: bytes, config: Dict[str, Any] = None) -> OCRResult:
        """Process image using Google Vision API"""
        config = config or {}
        api_key = config.get("api_key", "")
        
        if not api_key:
            return OCRResult(
                status="failed",
                raw_text="",
                details=[],
                provider=self.name,
                error="Google Vision API key is required"
            )
        
        try:
            # Load and resize image for faster transmission
            img = load_image_from_bytes(file_bytes)
            img = resize_for_ocr(img, max_width=1600, max_height=1600)
            
            # Use JPEG encoding for smaller file size
            import cv2
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare request
            payload = {
                "requests": [{
                    "image": {"content": image_base64},
                    "features": [{"type": "TEXT_DETECTION"}],
                    "imageContext": {
                        "languageHints": config.get("language_hints", ["id", "en"])
                    }
                }]
            }
            
            # Use connection pooling for faster repeated requests
            session = _get_session()
            response = session.post(
                f"{GOOGLE_VISION_API_URL}?key={api_key}",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"Google Vision API error: {error_msg}")
            
            result = response.json()
            
            # Parse response
            details: List[OCRTextBlock] = []
            full_text = ""
            
            if "responses" in result and result["responses"]:
                annotations = result["responses"][0].get("textAnnotations", [])
                
                if annotations:
                    # First annotation is the full text
                    full_text = annotations[0].get("description", "")
                    
                    # Rest are individual words/blocks
                    for ann in annotations[1:]:
                        vertices = ann.get("boundingPoly", {}).get("vertices", [])
                        box = [[v.get("x", 0), v.get("y", 0)] for v in vertices]
                        details.append(OCRTextBlock(
                            text=ann.get("description", ""),
                            confidence=0.95,  # Google Vision doesn't return confidence per word
                            box=box
                        ))
            
            return OCRResult(
                status="success",
                raw_text=full_text,
                details=details,
                provider=self.name
            )
            
        except Exception as e:
            logger.error(f"Google Vision Error: {str(e)}")
            return OCRResult(
                status="failed",
                raw_text="",
                details=[],
                provider=self.name,
                error=str(e)
            )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate API key is present"""
        return bool(config.get("api_key"))
