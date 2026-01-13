from paddleocr import PaddleOCR
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload():
    logger.info("Preloading PaddleOCR models...")
    # Initialize PaddleOCR to trigger download of default models
    try:
        PaddleOCR(use_angle_cls=True, lang='en')
        logger.info("PaddleOCR models downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download PaddleOCR models: {e}")
        # Non-fatal during build, but good to know
        pass

if __name__ == "__main__":
    preload()
