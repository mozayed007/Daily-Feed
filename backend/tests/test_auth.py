"""Tests for authentication routes and token management."""

import pytest
from datetime import timedelta

from app.core.auth import (
    create_access_token, create_refresh_token, decode_token,
    create_password_reset_token, verify_password_reset_token,
    get_password_hash, verify_password, create_tokens
)


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password(self):
        """Test that password hashing works."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$2")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "securepassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False


class TestTokenCreation:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self):
        """Test token decoding."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"

    def test_token_has_expiry(self):
        """Test that tokens have expiry."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_token_has_jti(self):
        """Test that tokens have unique identifier."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert "jti" in decoded
        assert len(decoded["jti"]) > 0

    def test_create_tokens_returns_both(self):
        """Test that create_tokens returns both tokens."""
        result = create_tokens("user-123", "test@example.com")
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"


class TestPasswordResetToken:
    """Tests for password reset token flow."""

    def test_create_password_reset_token(self):
        """Test reset token creation."""
        token = create_password_reset_token("test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_password_reset_token_valid(self):
        """Test verifying a valid reset token."""
        token = create_password_reset_token("test@example.com")
        email = verify_password_reset_token(token)
        assert email == "test@example.com"

    def test_verify_password_reset_token_invalid(self):
        """Test verifying an invalid token."""
        email = verify_password_reset_token("invalid-token")
        assert email is None

    def test_reset_token_has_correct_type(self):
        """Test that reset token has correct type claim."""
        token = create_password_reset_token("test@example.com")
        decoded = decode_token(token)
        assert decoded["type"] == "reset"


class TestTokenBlacklist:
    """Tests for token blacklisting."""

    def test_blacklist_token(self):
        """Test adding token to blacklist."""
        from app.core.auth import blacklist_token, is_token_blacklisted
        token = create_access_token({"sub": "user-123"})
        blacklist_token(token)
        assert is_token_blacklisted(token) is True

    def test_non_blacklisted_token(self):
        """Test that non-blacklisted token is valid."""
        from app.core.auth import is_token_blacklisted
        token = create_access_token({"sub": "user-123"})
        assert is_token_blacklisted(token) is False
