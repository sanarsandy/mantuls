"""
SSO Authentication Module with JWT Support
Integrates with LMAN SSO at https://lman.id/sso/
"""
import logging
import requests
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

SSO_ENDPOINT = "https://lman.id/sso/"
JWT_SECRET = os.environ.get("JWT_SECRET", "mantuls-jwt-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def sso_login(user: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user via LMAN SSO.
    
    Args:
        user: Email or NIP/NPP
        password: User password
        
    Returns:
        User data dict on success, None on failure
    """
    try:
        response = requests.post(
            f"{SSO_ENDPOINT}login",
            data={
                "user": user,
                "password": password
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                user_data = result.get("data", {})
                logger.info(f"SSO login success for user: {user_data.get('email', user)}")
                return user_data
            else:
                logger.warning(f"SSO login failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            logger.error(f"SSO request failed with status: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("SSO request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"SSO request error: {e}")
        return None
    except Exception as e:
        logger.error(f"SSO login error: {e}")
        return None


def generate_jwt_token(user_data: Dict[str, Any]) -> str:
    """
    Generate JWT token for authenticated user.
    
    Args:
        user_data: User data from SSO response
        
    Returns:
        JWT token string
    """
    payload = {
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "nip": user_data.get("nip_npp"),
        "is_admin": bool(user_data.get("is_admin", 0)),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload on success, None on failure
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
