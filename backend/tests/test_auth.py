"""Tests for JWT authentication and demo user store."""

from datetime import datetime, timedelta, timezone

import pytest

from app.auth import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    DEMO_USERS,
)
from app.config import Settings


@pytest.fixture()
def settings() -> Settings:
    """Minimal settings for JWT tests (no real API key needed)."""
    return Settings(
        google_api_key="test-key-not-used",
        jwt_secret_key="test-secret-for-unit-tests",
        jwt_algorithm="HS256",
        jwt_expire_minutes=30,
    )


class TestAuthenticateUser:
    """Verify demo user authentication logic."""

    def test_should_authenticate_withValidCredentials_returnUserDict(self) -> None:
        result = authenticate_user("dr.mehta", "doctor")
        assert result is not None
        assert result["username"] == "dr.mehta"
        assert result["role"] == "doctor"
        assert result["full_name"] == "Dr. Anil Mehta"

    def test_should_authenticate_withAllDemoUsers_returnCorrectRoles(self) -> None:
        demo_accounts = [
            ("dr.mehta", "doctor", "doctor"),
            ("nurse.priya", "nurse", "nurse"),
            ("billing.ravi", "billing", "billing_executive"),
            ("tech.anand", "technician", "technician"),
            ("admin.sys", "admin", "admin"),
        ]
        for username, password, expected_role in demo_accounts:
            result = authenticate_user(username, password)
            assert result is not None, f"Failed for {username}"
            assert result["role"] == expected_role

    def test_should_rejectAuth_withWrongPassword_returnNone(self) -> None:
        result = authenticate_user("dr.mehta", "wrong-password")
        assert result is None

    def test_should_rejectAuth_withUnknownUser_returnNone(self) -> None:
        result = authenticate_user("nonexistent", "password")
        assert result is None

    def test_should_rejectAuth_withEmptyCredentials_returnNone(self) -> None:
        result = authenticate_user("", "")
        assert result is None

    def test_should_haveFiveDemoUsers(self) -> None:
        assert len(DEMO_USERS) == 5


class TestJWTTokens:
    """Verify JWT creation and decoding."""

    def test_should_createAndDecode_withValidData_returnPayload(
        self, settings: Settings
    ) -> None:
        token = create_access_token(
            data={"sub": "dr.mehta", "role": "doctor"}, settings=settings
        )
        payload = decode_access_token(token, settings)
        assert payload is not None
        assert payload["sub"] == "dr.mehta"
        assert payload["role"] == "doctor"

    def test_should_includeExpiry_inToken(self, settings: Settings) -> None:
        token = create_access_token(
            data={"sub": "test", "role": "admin"}, settings=settings
        )
        payload = decode_access_token(token, settings)
        assert "exp" in payload

    def test_should_rejectDecode_withWrongSecret_returnNone(
        self, settings: Settings
    ) -> None:
        token = create_access_token(
            data={"sub": "test", "role": "admin"}, settings=settings
        )
        wrong_settings = Settings(
            google_api_key="test-key-not-used",
            jwt_secret_key="different-secret",
        )
        payload = decode_access_token(token, wrong_settings)
        assert payload is None

    def test_should_rejectDecode_withGarbageToken_returnNone(
        self, settings: Settings
    ) -> None:
        payload = decode_access_token("not.a.valid.jwt", settings)
        assert payload is None

    def test_should_rejectDecode_withEmptyToken_returnNone(
        self, settings: Settings
    ) -> None:
        payload = decode_access_token("", settings)
        assert payload is None
