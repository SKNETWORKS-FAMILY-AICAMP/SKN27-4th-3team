import uuid
from datetime import datetime, timezone
from pathlib import Path

import jwt


ROOT_DIR = Path(__file__).resolve().parents[3]
ACCOUNTS_DIR = ROOT_DIR / "backend" / "apps" / "accounts"
OFFICIAL_API_SPEC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"
UNIT_SIGNING_SECRET = "unit-test-secret-32-bytes-minimum-value"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def test_official_schema_records_auth_runtime_option_a_contract():
    import json

    auth_contract = json.loads(OFFICIAL_API_SPEC.read_text(encoding="utf-8"))["api"]["auth"]

    assert auth_contract["jwt_algorithm"] == "HS256"
    assert auth_contract["jwt_signing_secret"] == "Django settings.SECRET_KEY from DJANGO_SECRET_KEY"
    assert auth_contract["access_token_claims"] == ["token_type", "sub", "iat", "exp"]
    assert auth_contract["refresh_token_claims"] == [
        "token_type",
        "sub",
        "jti",
        "family_id",
        "iat",
        "exp",
    ]
    assert auth_contract["refresh_token_reuse_detection"]["concurrency"] == (
        "DB transaction with row lock"
    )
    assert auth_contract["refresh_token_reuse_detection"]["grace_window"] == "none"
    assert auth_contract["security_event_storage"]["fields"] == [
        "event_type",
        "user_id",
        "request_id",
        "metadata",
        "created_at",
    ]


def test_access_jwt_uses_approved_claim_allowlist_and_signing_policy():
    from backend.apps.accounts.tokens import (
        ACCESS_TOKEN_TYPE,
        JWT_ALGORITHM,
        issue_access_token,
    )

    issued_at = datetime(2026, 6, 4, 3, 0, 0, tzinfo=timezone.utc)
    raw_token = issue_access_token(
        user_id=123,
        signing_secret=UNIT_SIGNING_SECRET,
        issued_at=issued_at,
        ttl_seconds=900,
    )
    claims = jwt.decode(
        raw_token,
        UNIT_SIGNING_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"verify_exp": False},
    )

    assert ACCESS_TOKEN_TYPE == "access"
    assert claims["token_type"] == "access"
    assert claims["sub"] == "123"
    assert claims["exp"] - claims["iat"] == 900
    assert set(claims) == {"token_type", "sub", "iat", "exp"}


def test_refresh_jwt_uses_approved_claim_allowlist_and_preserves_family_id():
    from backend.apps.accounts.tokens import (
        JWT_ALGORITHM,
        REFRESH_TOKEN_TYPE,
        RefreshTokenIdentifiers,
        issue_refresh_token,
    )

    identifiers = RefreshTokenIdentifiers(
        jti=uuid.UUID("11111111-1111-4111-8111-111111111111"),
        family_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
    )
    issued_at = datetime(2026, 6, 4, 3, 0, 0, tzinfo=timezone.utc)

    raw_token = issue_refresh_token(
        user_id=123,
        identifiers=identifiers,
        signing_secret=UNIT_SIGNING_SECRET,
        issued_at=issued_at,
        ttl_seconds=14 * 24 * 60 * 60,
    )
    claims = jwt.decode(
        raw_token,
        UNIT_SIGNING_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"verify_exp": False},
    )

    assert REFRESH_TOKEN_TYPE == "refresh"
    assert claims["token_type"] == "refresh"
    assert claims["sub"] == "123"
    assert claims["jti"] == str(identifiers.jti)
    assert claims["family_id"] == str(identifiers.family_id)
    assert claims["exp"] - claims["iat"] == 14 * 24 * 60 * 60
    assert set(claims) == {"token_type", "sub", "jti", "family_id", "iat", "exp"}


def test_refresh_runtime_service_source_enforces_transaction_row_lock_and_reuse_policy():
    service_source = _read(ACCOUNTS_DIR / "services.py")

    assert "transaction.atomic()" in service_source
    assert ".select_for_update()" in service_source
    assert "ROTATED_REFRESH_TOKEN_STATUS" in service_source
    assert "REVOKED_REFRESH_TOKEN_STATUS" in service_source
    assert "REUSED_REFRESH_TOKEN_STATUS" in service_source
    assert "REFRESH_TOKEN_REUSE_ERROR_CODE" in service_source
    assert "revoke_refresh_token_family" in service_source
    assert "grace" not in service_source.lower()
