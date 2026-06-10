import hashlib
import hmac
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
ACCOUNTS_DIR = ROOT_DIR / "backend" / "apps" / "accounts"

EXPECTED_PASSWORD_RESET_EVENT_TYPES = (
    "password reset requested",
    "password reset delivery unavailable",
    "password reset succeeded",
    "password reset token expired",
    "password reset token reused",
    "password reset token invalid",
)


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    start = source.index(f"class {class_name}(")
    rest = source[start:]
    next_class = rest.find("\n\nclass ", 1)
    if next_class == -1:
        return rest
    return rest[:next_class]


def test_password_reset_token_model_has_only_approved_storage_fields():
    source = _read(ACCOUNTS_DIR / "models.py")
    reset_source = _class_source(source, "PasswordResetToken")

    assert "class PasswordResetToken(models.Model):" in reset_source
    assert "user_id = models.PositiveBigIntegerField()" in reset_source
    assert "token_hash = models.TextField(unique=True)" in reset_source
    assert "requested_email = models.EmailField()" in reset_source
    assert "request_ip = models.GenericIPAddressField()" in reset_source
    assert "created_at = models.DateTimeField()" in reset_source
    assert "expires_at = models.DateTimeField()" in reset_source
    assert "used_at = models.DateTimeField(null=True, blank=True)" in reset_source
    assert "models.ForeignKey(" not in reset_source

    forbidden_raw_storage_fields = (
        "raw_token",
        "plain_token",
        "reset_token =",
        "password =",
    )
    for field_name in forbidden_raw_storage_fields:
        assert field_name not in reset_source


def test_password_reset_hash_helpers_use_hmac_sha256_without_raw_value_storage():
    from backend.apps.accounts.tokens import (
        hash_password_reset_token,
        password_reset_email_hmac,
    )

    raw_token = "reset-token-value"
    email = "PLAYER@Example.COM "
    server_secret = "server-secret"

    expected_token_hash = hmac.new(
        server_secret.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expected_email_hmac = hmac.new(
        server_secret.encode("utf-8"),
        "player@example.com".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert hash_password_reset_token(raw_token, server_secret) == expected_token_hash
    assert password_reset_email_hmac(email, server_secret) == expected_email_hmac

    with pytest.raises(ValueError, match="raw_token"):
        hash_password_reset_token("", server_secret)
    with pytest.raises(ValueError, match="email"):
        password_reset_email_hmac("", server_secret)


def test_password_reset_token_generator_returns_url_safe_secret():
    from backend.apps.accounts.tokens import new_password_reset_token

    raw_token = new_password_reset_token()

    assert isinstance(raw_token, str)
    assert len(raw_token) >= 32
    assert "\n" not in raw_token
    assert " " not in raw_token


def test_security_event_types_include_password_reset_events():
    from backend.apps.accounts import tokens

    for event_type in EXPECTED_PASSWORD_RESET_EVENT_TYPES:
        assert event_type in tokens.SECURITY_EVENT_TYPES
