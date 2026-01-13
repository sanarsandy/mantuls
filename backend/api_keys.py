"""
API Key Management for OCR Service with Custom Prompts
"""
import secrets
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

API_KEYS_FILE = Path(__file__).parent / "api_keys.json"

# Default prompt for OCR extraction
DEFAULT_PROMPT = "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any explanations."


def _generate_api_key() -> str:
    """Generate a new API key with prefix"""
    return f"sk-{secrets.token_urlsafe(32)}"


def _hash_key(api_key: str) -> str:
    """Hash API key for storage (we don't store plain keys)"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def _load_api_keys() -> Dict[str, Any]:
    """Load API keys from file"""
    if API_KEYS_FILE.exists():
        try:
            with open(API_KEYS_FILE, "r") as f:
                data = json.load(f)
                # Handle case where user initialized with [] (List) instead of Dict
                if isinstance(data, list):
                    return {"keys": data, "enabled": True}
                return data
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
    return {"keys": [], "enabled": True}


def _save_api_keys(data: Dict[str, Any]) -> bool:
    """Save API keys to file"""
    try:
        with open(API_KEYS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving API keys: {e}")
        return False


def create_api_key(name: str, description: str = "", custom_prompt: str = "", output_format: str = "text", provider: str = "") -> Dict[str, Any]:
    """
    Create a new API key with optional custom prompt and provider
    
    Args:
        name: Name identifier for the key
        description: Optional description
        custom_prompt: Custom prompt for AI providers (empty = use default)
        output_format: "text" or "json"
        provider: Specific provider for this key (empty = use global active provider)
    """
    api_key = _generate_api_key()
    key_hash = _hash_key(api_key)
    
    key_data = {
        "id": secrets.token_hex(8),
        "name": name,
        "description": description,
        "key_hash": key_hash,
        "key_prefix": api_key[:10] + "...",
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "is_active": True,
        "custom_prompt": custom_prompt,
        "output_format": output_format,
        "provider": provider,
        "request_count": 0  # Usage tracking
    }
    
    data = _load_api_keys()
    data["keys"].append(key_data)
    _save_api_keys(data)
    
    return {
        **key_data,
        "api_key": api_key
    }


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate an API key
    Returns key metadata including custom_prompt if valid
    """
    if not api_key or not api_key.startswith("sk-"):
        return None
    
    key_hash = _hash_key(api_key)
    data = _load_api_keys()
    
    # Check if auth is disabled (for development)
    if not data.get("enabled", True):
        return {"name": "auth_disabled", "is_active": True, "custom_prompt": "", "output_format": "text"}
    
    for key_data in data.get("keys", []):
        if key_data.get("key_hash") == key_hash and key_data.get("is_active"):
            key_data["last_used"] = datetime.utcnow().isoformat()
            # Increment request count
            key_data["request_count"] = key_data.get("request_count", 0) + 1
            _save_api_keys(data)
            return key_data
    
    return None


def list_api_keys() -> List[Dict[str, Any]]:
    """List all API keys (without hashes)"""
    data = _load_api_keys()
    keys = []
    for key in data.get("keys", []):
        keys.append({
            "id": key.get("id"),
            "name": key.get("name"),
            "description": key.get("description"),
            "key_prefix": key.get("key_prefix"),
            "created_at": key.get("created_at"),
            "last_used": key.get("last_used"),
            "is_active": key.get("is_active"),
            "custom_prompt": key.get("custom_prompt", ""),
            "output_format": key.get("output_format", "text"),
            "provider": key.get("provider", ""),
            "request_count": key.get("request_count", 0)
        })
    return keys


def get_api_key_by_id(key_id: str) -> Optional[Dict[str, Any]]:
    """Get a single API key by ID"""
    data = _load_api_keys()
    for key in data.get("keys", []):
        if key.get("id") == key_id:
            return {
                "id": key.get("id"),
                "name": key.get("name"),
                "description": key.get("description"),
                "key_prefix": key.get("key_prefix"),
                "created_at": key.get("created_at"),
                "last_used": key.get("last_used"),
                "is_active": key.get("is_active"),
                "custom_prompt": key.get("custom_prompt", ""),
                "output_format": key.get("output_format", "text"),
                "provider": key.get("provider", ""),
                "request_count": key.get("request_count", 0)
            }
    return None


def update_api_key(key_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update an API key's settings (custom_prompt, output_format, description, provider)
    """
    data = _load_api_keys()
    for key in data.get("keys", []):
        if key.get("id") == key_id:
            # Only allow updating certain fields
            if "custom_prompt" in updates:
                key["custom_prompt"] = updates["custom_prompt"]
            if "output_format" in updates:
                key["output_format"] = updates["output_format"]
            if "description" in updates:
                key["description"] = updates["description"]
            if "provider" in updates:
                key["provider"] = updates["provider"]
            return _save_api_keys(data)
    return False


def increment_usage(key_id: str) -> bool:
    """Increment the request count for an API key by ID"""
    data = _load_api_keys()
    for key in data.get("keys", []):
        if key.get("id") == key_id:
            key["request_count"] = key.get("request_count", 0) + 1
            key["last_used"] = datetime.utcnow().isoformat()
            return _save_api_keys(data)
    return False


def revoke_api_key(key_id: str) -> bool:
    """Revoke (deactivate) an API key"""
    data = _load_api_keys()
    for key in data.get("keys", []):
        if key.get("id") == key_id:
            key["is_active"] = False
            return _save_api_keys(data)
    return False


def delete_api_key(key_id: str) -> bool:
    """Permanently delete an API key"""
    data = _load_api_keys()
    original_count = len(data.get("keys", []))
    data["keys"] = [k for k in data.get("keys", []) if k.get("id") != key_id]
    if len(data["keys"]) < original_count:
        return _save_api_keys(data)
    return False


def is_auth_enabled() -> bool:
    """Check if API key authentication is enabled"""
    data = _load_api_keys()
    return data.get("enabled", True)


def set_auth_enabled(enabled: bool) -> bool:
    """Enable or disable API key authentication"""
    data = _load_api_keys()
    data["enabled"] = enabled
    return _save_api_keys(data)
