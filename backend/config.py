"""
Configuration Management for OCR Service with Encrypted API Keys
"""
import json
import os
import base64
import logging
from typing import Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "config.json"

# Secret key from environment variable (MUST be set in production)
# If not set, uses a default key for development only
SECRET_KEY = os.environ.get("OCR_SECRET_KEY", "dev-secret-key-change-in-production")

# Fields that should be encrypted
SENSITIVE_FIELDS = ["api_key"]


def _get_fernet() -> Fernet:
    """Get Fernet cipher using derived key from SECRET_KEY"""
    # Use PBKDF2 to derive a proper key from the secret
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ocr-service-salt",  # Static salt (could be made dynamic per-install)
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return Fernet(key)


def _encrypt_value(value: str) -> str:
    """Encrypt a string value"""
    if not value:
        return value
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(value.encode())
        return f"ENC:{base64.urlsafe_b64encode(encrypted).decode()}"
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return value


def _decrypt_value(value: str) -> str:
    """Decrypt an encrypted string value"""
    if not value or not value.startswith("ENC:"):
        return value  # Not encrypted, return as-is
    try:
        fernet = _get_fernet()
        encrypted_data = base64.urlsafe_b64decode(value[4:])  # Remove "ENC:" prefix
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return ""  # Return empty on decryption failure


def _encrypt_sensitive_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields in config before saving"""
    encrypted_config = config.copy()
    if "providers" in encrypted_config:
        encrypted_config["providers"] = {}
        for provider_name, provider_config in config.get("providers", {}).items():
            encrypted_provider = provider_config.copy()
            for field in SENSITIVE_FIELDS:
                if field in encrypted_provider and encrypted_provider[field]:
                    # Only encrypt if not already encrypted
                    if not encrypted_provider[field].startswith("ENC:"):
                        encrypted_provider[field] = _encrypt_value(encrypted_provider[field])
            encrypted_config["providers"][provider_name] = encrypted_provider
    return encrypted_config


def _decrypt_sensitive_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields in config after loading"""
    decrypted_config = config.copy()
    if "providers" in decrypted_config:
        decrypted_config["providers"] = {}
        for provider_name, provider_config in config.get("providers", {}).items():
            decrypted_provider = provider_config.copy()
            for field in SENSITIVE_FIELDS:
                if field in decrypted_provider and decrypted_provider[field]:
                    decrypted_provider[field] = _decrypt_value(decrypted_provider[field])
            decrypted_config["providers"][provider_name] = decrypted_provider
    return decrypted_config


DEFAULT_CONFIG = {
    "active_provider": "paddle_ocr",
    "providers": {
        "paddle_ocr": {
            "enabled": True,
            "lang": "latin",
            "use_angle_cls": True,
            "use_gpu": False
        },
        "google_vision": {
            "enabled": False,
            "api_key": ""
        },
        "mistral_ocr": {
            "enabled": False,
            "api_key": "",
            "model": "pixtral-12b-2409"
        },
        "groq_vision": {
            "enabled": False,
            "api_key": "",
            "model": "meta-llama/llama-4-scout-17b-16e-instruct"
        }
    }
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file and decrypt sensitive fields"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            # Decrypt sensitive fields
            return _decrypt_sensitive_fields(config)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Encrypt sensitive fields and save configuration to file"""
    try:
        # Encrypt sensitive fields before saving
        encrypted_config = _encrypt_sensitive_fields(config)
        with open(CONFIG_FILE, "w") as f:
            json.dump(encrypted_config, f, indent=2)
        logger.info("Config saved with encrypted API keys")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def get_active_provider() -> str:
    """Get the name of the currently active provider"""
    config = load_config()
    return config.get("active_provider", "paddle_ocr")


def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get configuration for a specific provider (decrypted)"""
    config = load_config()
    return config.get("providers", {}).get(provider_name, {})


def set_active_provider(provider_name: str) -> bool:
    """Set the active provider"""
    config = load_config()
    config["active_provider"] = provider_name
    return save_config(config)


def update_provider_config(provider_name: str, provider_config: Dict[str, Any]) -> bool:
    """Update configuration for a specific provider"""
    config = load_config()
    if "providers" not in config:
        config["providers"] = {}
    config["providers"][provider_name] = provider_config
    return save_config(config)
