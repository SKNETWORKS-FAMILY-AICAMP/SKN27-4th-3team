import hashlib
import hmac
import uuid
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
ACCOUNTS_DIR = ROOT_DIR / "backend" / "apps" / "accounts"

EXPECTED_REFRESH_TOKEN_STATUSES = ("active", "rotated", "revoked", "reused")
EXPECTED_REUSE_STATUSES = ("rotated", "revoked", "reused")
EXPECTED_SECURITY_EVENT_TYPES = (
    "refresh token reuse 감지",
    "refresh token family revoke",
    "CSRF 실패",
    "로그인 실패 반복",
    "권한 없는 match 접근 시도",
    "participant가 아닌 사용자의 행동 제출 시도",
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


def test_refresh_token_model_has_only_approved_storage_fields():
    source = _read(ACCOUNTS_DIR / "models.py")
    refresh_token_source = _class_source(source, "RefreshToken")

    assert "class RefreshToken(models.Model):" in refresh_token_source
    assert "user_id = models.PositiveBigIntegerField()" in refresh_token_source
    assert "jti = models.UUIDField(" in refresh_token_source
    assert "family_id = models.UUIDField(" in refresh_token_source
    assert "token_hash = models.TextField()" in refresh_token_source
    assert "status = models.TextField(" in refresh_token_source
    assert "issued_at = models.DateTimeField()" in refresh_token_source
    assert "expires_at = models.DateTimeField()" in refresh_token_source
    assert "rotated_at = models.DateTimeField(null=True, blank=True)" in refresh_token_source
    assert "revoked_at = models.DateTimeField(null=True, blank=True)" in refresh_token_source
    assert "reused_at = models.DateTimeField(null=True, blank=True)" in refresh_token_source
    assert "replaced_by_jti = models.UUIDField(null=True, blank=True)" in refresh_token_source
    assert "models.ForeignKey(" not in refresh_token_source
    assert "on_delete=models.CASCADE" not in refresh_token_source
    assert "db_table" not in source

    forbidden_raw_storage_fields = (
        "raw_token =",
        "token_value =",
        "refresh_token =",
        "plain_token =",
    )
    for field_name in forbidden_raw_storage_fields:
        assert field_name not in source


def test_refresh_token_status_policy_matches_auth_security_contract():
    from backend.apps.accounts import tokens

    assert tokens.REFRESH_TOKEN_STATUSES == EXPECTED_REFRESH_TOKEN_STATUSES
    assert tokens.REFRESH_TOKEN_REUSE_STATUSES == EXPECTED_REUSE_STATUSES
    assert tokens.REFRESH_TOKEN_REUSE_ERROR_CODE == "REFRESH_TOKEN_REUSED"
    assert tokens.ROTATED_REFRESH_TOKEN_STATUS == "rotated"
    assert tokens.REVOKED_REFRESH_TOKEN_STATUS == "revoked"

    assert tokens.is_refresh_token_reuse_status("active") is False
    assert tokens.is_refresh_token_reuse_status("rotated") is True
    assert tokens.is_refresh_token_reuse_status("revoked") is True
    assert tokens.is_refresh_token_reuse_status("reused") is True

    with pytest.raises(ValueError, match="unknown"):
        tokens.is_refresh_token_reuse_status("unknown")


def test_refresh_token_identifier_helpers_keep_family_and_jti_lifecycles_separate():
    source = _read(ACCOUNTS_DIR / "tokens.py")

    assert "def new_refresh_token_identifiers(" not in source

    from backend.apps.accounts.tokens import (
        new_login_refresh_token_identifiers,
        new_refresh_token_family_id,
        new_refresh_token_jti,
    )

    jti = new_refresh_token_jti()
    family_id = new_refresh_token_family_id()
    login_identifiers = new_login_refresh_token_identifiers()

    assert isinstance(jti, uuid.UUID)
    assert isinstance(family_id, uuid.UUID)
    assert isinstance(login_identifiers.jti, uuid.UUID)
    assert isinstance(login_identifiers.family_id, uuid.UUID)
    assert jti.version == 4
    assert family_id.version == 4
    assert login_identifiers.jti.version == 4
    assert login_identifiers.family_id.version == 4


def test_refresh_token_hash_uses_server_secret_hmac_sha256_only():
    from backend.apps.accounts.tokens import hash_refresh_token

    raw_token = "refresh-token-jwt"
    server_secret = "server-secret"
    expected_hash = hmac.new(
        server_secret.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert hash_refresh_token(raw_token, server_secret) == expected_hash
    assert hash_refresh_token(raw_token, server_secret) != raw_token

    with pytest.raises(ValueError, match="raw_token"):
        hash_refresh_token("", server_secret)
    with pytest.raises(ValueError, match="server_secret"):
        hash_refresh_token(raw_token, "")


def test_security_event_model_keeps_only_approved_log_fields_until_actor_contract_exists():
    source = _read(ACCOUNTS_DIR / "models.py")
    security_event_source = _class_source(source, "SecurityEvent")

    assert "class SecurityEvent(models.Model):" in security_event_source
    assert "event_type = models.TextField(" in security_event_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in security_event_source
    assert "metadata = models.JSONField()" not in security_event_source
    assert "user_id = models.PositiveBigIntegerField()" not in security_event_source
    assert "actor" not in security_event_source
    assert "models.ForeignKey(" not in security_event_source
    assert "on_delete=models.CASCADE" not in security_event_source
    assert "db_table" not in source

    from backend.apps.accounts import tokens

    assert tokens.SECURITY_EVENT_TYPES == EXPECTED_SECURITY_EVENT_TYPES
    assert "def validate_security_event_metadata(" not in _read(ACCOUNTS_DIR / "tokens.py")
