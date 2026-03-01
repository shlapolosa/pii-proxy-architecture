"""
Authentication Module for PII Proxy
Secure access control for the backend proxy
"""

import hashlib
import hmac
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """
    Authentication manager for secure access control
    """

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.active_tokens = {}
        self.revoked_tokens = set()

    def generate_api_key(self, user_id: str, permissions: Dict[str, Any] = None) -> str:
        """
        Generate an API key for a user

        Args:
            user_id (str): User identifier
            permissions (Dict[str, Any], optional): User permissions

        Returns:
            str: Generated API key
        """
        # Create a unique API key using HMAC
        timestamp = str(datetime.now().timestamp())
        message = f"{user_id}:{timestamp}"
        api_key = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Store API key metadata
        self.active_tokens[api_key] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "permissions": permissions or {"read": True, "write": True},
            "expires_at": datetime.now() + timedelta(days=365)  # 1 year expiry
        }

        logger.info(f"Generated API key for user {user_id}")
        return api_key

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an API key

        Args:
            api_key (str): API key to verify

        Returns:
            Optional[Dict[str, Any]]: User info if valid, None if invalid
        """
        # Check if token is revoked
        if api_key in self.revoked_tokens:
            logger.warning("Attempt to use revoked API key")
            return None

        # Check if token exists
        if api_key not in self.active_tokens:
            logger.warning("Invalid API key provided")
            return None

        # Check if token is expired
        token_info = self.active_tokens[api_key]
        if datetime.now() > token_info["expires_at"]:
            logger.warning("Expired API key used")
            del self.active_tokens[api_key]
            return None

        logger.info(f"Valid API key for user {token_info['user_id']}")
        return token_info

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key

        Args:
            api_key (str): API key to revoke

        Returns:
            bool: True if revoked, False if not found
        """
        if api_key in self.active_tokens:
            self.revoked_tokens.add(api_key)
            del self.active_tokens[api_key]
            logger.info("API key revoked")
            return True
        return False

    def generate_jwt_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """
        Generate a JWT token for user authentication

        Args:
            user_id (str): User identifier
            expires_in_hours (int): Hours until expiration

        Returns:
            str: JWT token
        """
        payload = {
            "user_id": user_id,
            "exp": datetime.now() + timedelta(hours=expires_in_hours),
            "iat": datetime.now()
        }

        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        logger.info(f"Generated JWT token for user {user_id}")
        return token

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token

        Args:
            token (str): JWT token to verify

        Returns:
            Optional[Dict[str, Any]]: Payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            logger.info(f"Valid JWT token for user {payload['user_id']}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token used")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token provided")
            return None

    def create_session_token(self, user_id: str, session_data: Dict[str, Any] = None) -> str:
        """
        Create a session token for web UI authentication

        Args:
            user_id (str): User identifier
            session_data (Dict[str, Any], optional): Additional session data

        Returns:
            str: Session token
        """
        session_token = secrets.token_urlsafe(32)

        self.active_tokens[session_token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "session_data": session_data or {},
            "type": "session",
            "expires_at": datetime.now() + timedelta(hours=8)  # 8 hour sessions
        }

        logger.info(f"Created session token for user {user_id}")
        return session_token

    def verify_session_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a session token

        Args:
            session_token (str): Session token to verify

        Returns:
            Optional[Dict[str, Any]]: Session info if valid, None if invalid
        """
        return self.verify_api_key(session_token)

    def get_user_permissions(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user permissions from token

        Args:
            token (str): API key or session token

        Returns:
            Optional[Dict[str, Any]]: User permissions if valid, None if invalid
        """
        token_info = self.verify_api_key(token)
        if token_info:
            return token_info.get("permissions", {"read": True, "write": True})
        return None

# Global instance
auth_manager = AuthenticationManager()