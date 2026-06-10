import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

ACTIVE_REFRESH_TOKEN_STATUS = "active"
ROTATED_REFRESH_TOKEN_STATUS = "rotated"
REVOKED_REFRESH_TOKEN_STATUS = "revoked"
REUSED_REFRESH_TOKEN_STATUS = "reused"

REFRESH_TOKEN_STATUSES = (
    ACTIVE_REFRESH_TOKEN_STATUS,
    ROTATED_REFRESH_TOKEN_STATUS,
    REVOKED_REFRESH_TOKEN_STATUS,
    REUSED_REFRESH_TOKEN_STATUS,
)
REFRESH_TOKEN_REUSE_STATUSES = (
    ROTATED_REFRESH_TOKEN_STATUS,
    REVOKED_REFRESH_TOKEN_STATUS,
    REUSED_REFRESH_TOKEN_STATUS,
)
REFRESH_TOKEN_REUSE_ERROR_CODE = "REFRESH_TOKEN_REUSED"

SECURITY_EVENT_REFRESH_TOKEN_REUSE_DETECTED = "refresh token reuse 감지"
SECURITY_EVENT_REFRESH_TOKEN_FAMILY_REVOKED = "refresh token family revoke"
SECURITY_EVENT_CSRF_FAILED = "CSRF 실패"
SECURITY_EVENT_LOGIN_FAILED_REPEATED = "로그인 실패 반복"
SECURITY_EVENT_UNAUTHORIZED_MATCH_ACCESS_ATTEMPTED = "권한 없는 match 접근 시도"
SECURITY_EVENT_NON_PARTICIPANT_ACTION_SUBMIT_ATTEMPTED = (
    "participant가 아닌 사용자의 행동 제출 시도"
)

SECURITY_EVENT_PASSWORD_RESET_REQUESTED = "password reset requested"
SECURITY_EVENT_PASSWORD_RESET_DELIVERY_UNAVAILABLE = "password reset delivery unavailable"
SECURITY_EVENT_PASSWORD_RESET_SUCCEEDED = "password reset succeeded"
SECURITY_EVENT_PASSWORD_RESET_TOKEN_EXPIRED = "password reset token expired"
SECURITY_EVENT_PASSWORD_RESET_TOKEN_REUSED = "password reset token reused"
SECURITY_EVENT_PASSWORD_RESET_TOKEN_INVALID = "password reset token invalid"

SECURITY_EVENT_TYPES = (
    SECURITY_EVENT_REFRESH_TOKEN_REUSE_DETECTED,
    SECURITY_EVENT_REFRESH_TOKEN_FAMILY_REVOKED,
    SECURITY_EVENT_CSRF_FAILED,
    SECURITY_EVENT_LOGIN_FAILED_REPEATED,
    SECURITY_EVENT_UNAUTHORIZED_MATCH_ACCESS_ATTEMPTED,
    SECURITY_EVENT_NON_PARTICIPANT_ACTION_SUBMIT_ATTEMPTED,
    SECURITY_EVENT_PASSWORD_RESET_REQUESTED,
    SECURITY_EVENT_PASSWORD_RESET_DELIVERY_UNAVAILABLE,
    SECURITY_EVENT_PASSWORD_RESET_SUCCEEDED,
    SECURITY_EVENT_PASSWORD_RESET_TOKEN_EXPIRED,
    SECURITY_EVENT_PASSWORD_RESET_TOKEN_REUSED,
    SECURITY_EVENT_PASSWORD_RESET_TOKEN_INVALID,
)


@dataclass(frozen=True)
class RefreshTokenIdentifiers:
    jti: uuid.UUID
    family_id: uuid.UUID


def new_refresh_token_jti() -> uuid.UUID:
    return uuid.uuid4()


def new_refresh_token_family_id() -> uuid.UUID:
    return uuid.uuid4()


def new_login_refresh_token_identifiers() -> RefreshTokenIdentifiers:
    return RefreshTokenIdentifiers(
        jti=new_refresh_token_jti(),
        family_id=new_refresh_token_family_id(),
    )


def hash_refresh_token(raw_token: str, server_secret: str) -> str:
    if not raw_token:
        raise ValueError("raw_token is required")
    if not server_secret:
        raise ValueError("server_secret is required")

    return hmac.new(
        server_secret.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def new_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password_reset_token(raw_token: str, server_secret: str) -> str:
    if not raw_token:
        raise ValueError("raw_token is required")
    if not server_secret:
        raise ValueError("server_secret is required")

    return hmac.new(
        server_secret.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def password_reset_email_hmac(email: str, server_secret: str) -> str:
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("email is required")
    if not server_secret:
        raise ValueError("server_secret is required")

    return hmac.new(
        server_secret.encode("utf-8"),
        normalized_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_refresh_token_reuse_status(status: str) -> bool:
    if status not in REFRESH_TOKEN_STATUSES:
        raise ValueError(f"unknown refresh token status: {status}")

    return status in REFRESH_TOKEN_REUSE_STATUSES


def issue_access_token(
    *,
    user_id: int,
    signing_secret: str,
    issued_at: datetime | None = None,
    ttl_seconds: int,
) -> str:
    issued_at_value = _issued_at(issued_at)
    payload = {
        "token_type": ACCESS_TOKEN_TYPE,
        "sub": _subject(user_id),
        "iat": _timestamp(issued_at_value),
        "exp": _timestamp(issued_at_value + timedelta(seconds=ttl_seconds)),
    }
    return _encode(payload, signing_secret)


def issue_refresh_token(
    *,
    user_id: int,
    identifiers: RefreshTokenIdentifiers,
    signing_secret: str,
    issued_at: datetime | None = None,
    ttl_seconds: int,
) -> str:
    issued_at_value = _issued_at(issued_at)
    payload = {
        "token_type": REFRESH_TOKEN_TYPE,
        "sub": _subject(user_id),
        "jti": str(identifiers.jti),
        "family_id": str(identifiers.family_id),
        "iat": _timestamp(issued_at_value),
        "exp": _timestamp(issued_at_value + timedelta(seconds=ttl_seconds)),
    }
    return _encode(payload, signing_secret)


def decode_jwt_token(
    raw_token: str,
    *,
    signing_secret: str,
    expected_token_type: str,
) -> dict[str, Any]:
    if not raw_token:
        raise ValueError("raw_token is required")
    if not signing_secret:
        raise ValueError("signing_secret is required")

    claims = jwt.decode(raw_token, signing_secret, algorithms=[JWT_ALGORITHM])
    if claims.get("token_type") != expected_token_type:
        raise ValueError("unexpected token_type")

    return dict(claims)


def _encode(payload: dict[str, Any], signing_secret: str) -> str:
    if not signing_secret:
        raise ValueError("signing_secret is required")

    return jwt.encode(payload, signing_secret, algorithm=JWT_ALGORITHM)


def _issued_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("issued_at must be timezone-aware")

    return value.astimezone(timezone.utc)


def _subject(user_id: int) -> str:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    return str(user_id)


def _timestamp(value: datetime) -> int:
    return int(value.timestamp())
