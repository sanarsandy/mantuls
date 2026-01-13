"""
Mistral OCR Provider - AI-powered OCR using Mistral's Pixtral vision model
"""
import base64
import logging
import requests
from typing import Dict, Any, List

from .base import BaseOCRProvider, OCRResult, OCRTextBlock
from utils.image import load_image_from_bytes, resize_for_ocr

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

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


class MistralOCRProvider(BaseOCRProvider):
    """Mistral Pixtral AI-powered OCR - Good for complex documents"""
    
    @property
    def name(self) -> str:
        return "mistral_ocr"
    
    @property
    def display_name(self) -> str:
        return "Mistral AI (Pixtral)"
    
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
                    "description": "Mistral AI API Key",
                    "format": "password"
                },
                "model": {
                    "type": "string",
                    "title": "Model",
                    "description": "Pixtral model to use",
                    "enum": ["pixtral-12b-2409", "pixtral-large-latest"],
                    "default": "pixtral-12b-2409"
                },
                "prompt": {
                    "type": "string",
                    "title": "Custom Prompt",
                    "description": "Custom instruction for text extraction",
                    "default": "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any explanations."
                }
            },
            "required": ["api_key"]
        }
    
    def process(self, file_bytes: bytes, config: Dict[str, Any] = None) -> OCRResult:
        """Process image using Mistral Pixtral API"""
        config = config or {}
        api_key = config.get("api_key", "")
        
        if not api_key:
            return OCRResult(
                status="failed",
                raw_text="",
                details=[],
                provider=self.name,
                error="Mistral API key is required"
            )
        
        try:
            # Load and resize image for faster transmission
            img = load_image_from_bytes(file_bytes)
            img = resize_for_ocr(img, max_width=1600, max_height=1600)
            
            # Use JPEG encoding for smaller file size
            import cv2
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            model = config.get("model", "pixtral-12b-2409")
            prompt = config.get("prompt", "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any explanations.")
            
            # Prepare request
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        ]
                    }
                ],
                "max_tokens": 4096
            }
            
            # Use connection pooling for faster repeated requests
            session = _get_session()
            response = session.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("message", "Unknown error")
                raise Exception(f"Mistral API error: {error_msg}")
            
            result = response.json()
            
            # Parse response
            extracted_text = ""
            if "choices" in result and result["choices"]:
                message = result["choices"][0].get("message", {})
                extracted_text = message.get("content", "")
            
            # Mistral returns full text, not individual blocks
            details = [OCRTextBlock(
                text=extracted_text,
                confidence=0.9,
                box=None
            )] if extracted_text else []
            
            return OCRResult(
                status="success",
                raw_text=extracted_text,
                details=details,
                provider=self.name
            )
            
        except Exception as e:
            logger.error(f"Mistral OCR Error: {str(e)}")
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
