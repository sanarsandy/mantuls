"""
Provider Registry - Manages available OCR providers
"""
from typing import Dict, Type, List
from .base import BaseOCRProvider
from .paddle_ocr import PaddleOCRProvider
from .google_vision import GoogleVisionProvider
from .mistral_ocr import MistralOCRProvider
from .groq_vision import GroqVisionProvider

# Registry of available providers
_providers: Dict[str, Type[BaseOCRProvider]] = {}
_instances: Dict[str, BaseOCRProvider] = {}


def register_provider(provider_class: Type[BaseOCRProvider]):
    """Register a provider class"""
    instance = provider_class()
    _providers[instance.name] = provider_class
    _instances[instance.name] = instance


def get_provider(name: str) -> BaseOCRProvider:
    """Get provider instance by name"""
    if name not in _instances:
        raise ValueError(f"Unknown provider: {name}")
    return _instances[name]


def list_providers() -> List[Dict]:
    """List all available providers"""
    return [
        {
            "name": p.name,
            "display_name": p.display_name,
            "requires_api_key": p.requires_api_key,
            "config_schema": p.get_config_schema()
        }
        for p in _instances.values()
    ]


def get_provider_names() -> List[str]:
    """Get list of provider names"""
    return list(_instances.keys())


# Auto-register all built-in providers
register_provider(PaddleOCRProvider)
register_provider(GoogleVisionProvider)
register_provider(MistralOCRProvider)
register_provider(GroqVisionProvider)

