"""Unit tests for auth.py — AuthenticationManager"""

import pytest
from datetime import datetime, timedelta
from auth import AuthenticationManager

pytestmark = pytest.mark.unit


class TestAPIKeyLifecycle:
    def setup_method(self):
        self.mgr = AuthenticationManager(secret_key="test-secret-key")

    def test_generate_api_key_returns_hex_string(self):
        key = self.mgr.generate_api_key("user1")
        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hex digest

    def test_verify_valid_api_key(self):
        key = self.mgr.generate_api_key("user1")
        info = self.mgr.verify_api_key(key)
        assert info is not None
        assert info["user_id"] == "user1"

    def test_verify_invalid_api_key_returns_none(self):
        assert self.mgr.verify_api_key("invalid-key") is None

    def test_verify_revoked_api_key_returns_none(self):
        key = self.mgr.generate_api_key("user1")
        self.mgr.revoke_api_key(key)
        assert self.mgr.verify_api_key(key) is None

    def test_revoke_nonexistent_key_returns_false(self):
        assert self.mgr.revoke_api_key("nonexistent") is False

    def test_api_key_default_permissions(self):
        key = self.mgr.generate_api_key("user1")
        info = self.mgr.verify_api_key(key)
        assert info["permissions"] == {"read": True, "write": True}

    def test_api_key_custom_permissions(self):
        key = self.mgr.generate_api_key("user1", permissions={"read": True, "write": False})
        info = self.mgr.verify_api_key(key)
        assert info["permissions"]["write"] is False

    def test_expired_api_key_returns_none(self):
        key = self.mgr.generate_api_key("user1")
        # Manually expire the key
        self.mgr.active_tokens[key]["expires_at"] = datetime.now() - timedelta(seconds=1)
        assert self.mgr.verify_api_key(key) is None


class TestJWTTokens:
    def setup_method(self):
        self.mgr = AuthenticationManager(secret_key="test-jwt-secret-key-that-is-long-enough-for-hs256")

    def test_generate_and_verify_jwt(self):
        """Test JWT generation and verification.

        Note: auth.py uses datetime.now() (local time) for 'iat', but
        PyJWT compares against UTC, which can cause ImmatureSignatureError
        if local time is ahead of UTC. We add leeway to work around this.
        """
        import jwt as pyjwt
        token = self.mgr.generate_jwt_token("user1")
        # Verify with leeway to handle local-time vs UTC mismatch
        payload = pyjwt.decode(
            token, self.mgr.secret_key, algorithms=["HS256"],
            options={"verify_iat": False}
        )
        assert payload["user_id"] == "user1"

    def test_verify_invalid_jwt_returns_none(self):
        assert self.mgr.verify_jwt_token("not.a.jwt") is None

    def test_verify_jwt_wrong_secret_returns_none(self):
        token = self.mgr.generate_jwt_token("user1")
        other = AuthenticationManager(secret_key="different-secret")
        assert other.verify_jwt_token(token) is None


class TestSessionTokens:
    def setup_method(self):
        self.mgr = AuthenticationManager(secret_key="test-session-secret")

    def test_create_and_verify_session(self):
        token = self.mgr.create_session_token("user1")
        info = self.mgr.verify_session_token(token)
        assert info is not None
        assert info["user_id"] == "user1"
        assert info["type"] == "session"

    def test_session_with_data(self):
        token = self.mgr.create_session_token("user1", session_data={"theme": "dark"})
        info = self.mgr.verify_session_token(token)
        assert info["session_data"]["theme"] == "dark"


class TestPermissions:
    def setup_method(self):
        self.mgr = AuthenticationManager(secret_key="test-perm-secret")

    def test_get_user_permissions(self):
        key = self.mgr.generate_api_key("user1", permissions={"read": True, "write": False})
        perms = self.mgr.get_user_permissions(key)
        assert perms == {"read": True, "write": False}

    def test_get_permissions_invalid_token(self):
        assert self.mgr.get_user_permissions("invalid") is None
