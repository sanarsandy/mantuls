"""
PaddleOCR Provider - Local OCR using PaddlePaddle
"""
import logging
from typing import Dict, Any, List
from paddleocr import PaddleOCR

from .base import BaseOCRProvider, OCRResult, OCRTextBlock
from utils.image import load_image_from_bytes, preprocess_for_ocr, resize_for_ocr

logger = logging.getLogger(__name__)


class PaddleOCRProvider(BaseOCRProvider):
    """PaddleOCR implementation - Free, local OCR"""
    
    def __init__(self):
        self._ocr_engine = None
        self._current_lang = None
    
    @property
    def name(self) -> str:
        return "paddle_ocr"
    
    @property
    def display_name(self) -> str:
        return "PaddleOCR (Local)"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lang": {
                    "type": "string",
                    "title": "Language",
                    "description": "OCR language model",
                    "enum": ["en", "latin", "ch", "japan", "korean"],
                    "default": "latin"
                },
                "use_angle_cls": {
                    "type": "boolean",
                    "title": "Detect Rotation",
                    "description": "Enable text rotation detection",
                    "default": True
                },
                "use_gpu": {
                    "type": "boolean",
                    "title": "Use GPU",
                    "description": "Enable GPU acceleration",
                    "default": False
                }
            }
        }
    
    def _get_engine(self, config: Dict[str, Any]) -> PaddleOCR:
        """Get or create PaddleOCR engine with specified config"""
        lang = config.get("lang", "latin")
        
        # Reinitialize if language changed
        if self._ocr_engine is None or self._current_lang != lang:
            logger.info(f"Initializing PaddleOCR with lang='{lang}'...")
            self._ocr_engine = PaddleOCR(
                use_angle_cls=config.get("use_angle_cls", True),
                lang=lang,
                show_log=False,
                use_gpu=config.get("use_gpu", False)
            )
            self._current_lang = lang
            logger.info("PaddleOCR initialized successfully.")
        
        return self._ocr_engine
    
    def process(self, file_bytes: bytes, config: Dict[str, Any] = None) -> OCRResult:
        """Process image using PaddleOCR"""
        config = config or {}
        
        try:
            # Load, resize, and preprocess image
            img = load_image_from_bytes(file_bytes)
            img = resize_for_ocr(img)  # Resize for faster processing
            img_processed = preprocess_for_ocr(img, grayscale=True)
            
            # Get OCR engine
            ocr = self._get_engine(config)
            
            # Run OCR - use angle classification from config (default False for speed)
            use_angle_cls = config.get("use_angle_cls", False)
            result = ocr.ocr(img_processed, cls=use_angle_cls)
            
            # Parse results
            details: List[OCRTextBlock] = []
            full_text: List[str] = []
            
            if result and result[0]:
                for line in result[0]:
                    coords = line[0]
                    text, conf = line[1]
                    details.append(OCRTextBlock(
                        text=text,
                        confidence=float(conf),
                        box=coords
                    ))
                    full_text.append(text)
            
            return OCRResult(
                status="success",
                raw_text="\n".join(full_text),
                details=details,
                provider=self.name
            )
            
        except Exception as e:
            logger.error(f"PaddleOCR Error: {str(e)}")
            return OCRResult(
                status="failed",
                raw_text="",
                details=[],
                provider=self.name,
                error=str(e)
            )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """PaddleOCR doesn't require API key, always valid"""
        return True
