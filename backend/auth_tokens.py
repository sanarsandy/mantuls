"""
Secure token generation for frontend authentication
Uses HMAC-signed tokens that expire after a short time
"""
import hmac
import hashlib
import base64
import time
import json
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Secret key from environment (same as encryption key for simplicity)
SECRET_KEY = os.environ.get("OCR_SECRET_KEY", "dev-secret-key-change-in-production")

# Token validity in seconds (1 hour)
TOKEN_VALIDITY = 3600


def generate_frontend_token(key_id: str) -> str:
    """
    Generate a signed token for frontend use
    Format: base64(key_id:timestamp:signature)
    """
    timestamp = int(time.time())
    payload = f"{key_id}:{timestamp}"
    
    # Create HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # Use first 16 chars for shorter token
    
    # Combine and base64 encode
    token_data = f"{payload}:{signature}"
    token = base64.urlsafe_b64encode(token_data.encode()).decode()
    
    return token


def verify_frontend_token(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify a frontend token and return the key_id if valid
    Returns: (is_valid, key_id)
    """
    try:
        # Decode token
        token_data = base64.urlsafe_b64decode(token.encode()).decode()
        parts = token_data.split(":")
        
        if len(parts) != 3:
            return False, None
        
        key_id, timestamp_str, provided_signature = parts
        timestamp = int(timestamp_str)
        
        # Check if token is expired
        if time.time() - timestamp > TOKEN_VALIDITY:
            logger.warning(f"Token expired for key_id: {key_id}")
            return False, None
        
        # Verify signature
        payload = f"{key_id}:{timestamp_str}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning(f"Invalid signature for key_id: {key_id}")
            return False, None
        
        return True, key_id
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return False, None
