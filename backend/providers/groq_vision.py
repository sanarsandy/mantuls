"""
Groq AI Vision Provider - Fast AI-powered OCR using Groq's Llama 4 vision models
"""
import base64
import logging
import requests
from typing import Dict, Any, List

from .base import BaseOCRProvider, OCRResult, OCRTextBlock
from utils.image import load_image_from_bytes, resize_for_ocr

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Connection pooling for faster repeated requests
_session: requests.Session = None

def _get_session() -> requests.Session:
    """Get or create a reusable session for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Set connection pool size
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10)
        _session.mount('https://', adapter)
    return _session


class GroqVisionProvider(BaseOCRProvider):
    """Groq AI Vision - Ultra-fast OCR using Llama 4 vision models"""
    
    @property
    def name(self) -> str:
        return "groq_vision"
    
    @property
    def display_name(self) -> str:
        return "Groq AI (Llama 4 Vision)"
    
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
                    "description": "Groq API Key (get from console.groq.com)",
                    "format": "password"
                },
                "model": {
                    "type": "string",
                    "title": "Model",
                    "description": "Llama 4 vision model to use",
                    "enum": [
                        "meta-llama/llama-4-scout-17b-16e-instruct",
                        "meta-llama/llama-4-maverick-17b-128e-instruct"
                    ],
                    "default": "meta-llama/llama-4-scout-17b-16e-instruct"
                },
                "prompt": {
                    "type": "string",
                    "title": "Custom Prompt",
                    "description": "Custom instruction for text extraction",
                    "default": "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any explanations or commentary."
                }
            },
            "required": ["api_key"]
        }
    
    def process(self, file_bytes: bytes, config: Dict[str, Any] = None) -> OCRResult:
        """Process image using Groq Vision API"""
        config = config or {}
        api_key = config.get("api_key", "")
        
        if not api_key:
            return OCRResult(
                status="failed",
                raw_text="",
                details=[],
                provider=self.name,
                error="Groq API key is required"
            )
        
        try:
            # Load and resize image for faster transmission
            img = load_image_from_bytes(file_bytes)
            img = resize_for_ocr(img, max_width=1600, max_height=1600)
            
            # Use JPEG encoding for smaller file size (~50% smaller than PNG)
            import cv2
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            model = config.get("model", "meta-llama/llama-4-scout-17b-16e-instruct")
            prompt = config.get("prompt", "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any explanations or commentary.")
            
            # Prepare request (OpenAI-compatible format)
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
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.1  # Low temperature for consistent OCR output
            }
            
            # Use connection pooling for faster repeated requests
            session = _get_session()
            response = session.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Groq API error: {error_msg}")
            
            result = response.json()
            
            # Parse response
            extracted_text = ""
            if "choices" in result and result["choices"]:
                message = result["choices"][0].get("message", {})
                extracted_text = message.get("content", "")
            
            # Groq returns full text, not individual blocks
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
            logger.error(f"Groq Vision Error: {str(e)}")
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
