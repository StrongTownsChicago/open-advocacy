"""Tests for auth utilities: password hashing and JWT token creation."""

from unittest.mock import patch

from jose import jwt

from app.core.auth import (
    ALGORITHM,
    create_access_token,
    get_password_hash,
    verify_password,
)

TEST_SECRET_KEY = "test-secret-key-for-unit-tests"


class TestPasswordHashing:
    """Tests for bcrypt password hash/verify round-trip."""

    def test_hash_and_verify_correct_password(self):
        """Hashing then verifying the same password should return True."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Verifying a different password against a hash should return False."""
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False


class TestCreateAccessToken:
    """Tests for JWT token creation."""

    def test_token_contains_subject(self):
        """Token should contain the 'sub' claim from input data."""
        with patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY):
            token = create_access_token(data={"sub": "user-123"})
            payload = jwt.decode(token, TEST_SECRET_KEY, algorithms=[ALGORITHM])
            assert payload["sub"] == "user-123"

    def test_token_preserves_extra_claims(self):
        """Extra data in the token payload should be preserved."""
        with patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY):
            token = create_access_token(
                data={"sub": "user-789", "role": "admin", "group_id": "g-1"}
            )
            payload = jwt.decode(token, TEST_SECRET_KEY, algorithms=[ALGORITHM])
            assert payload["role"] == "admin"
            assert payload["group_id"] == "g-1"
