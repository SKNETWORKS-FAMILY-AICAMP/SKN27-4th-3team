import hashlib
import hmac
import uuid
from dataclasses import dataclass


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

SECURITY_EVENT_TYPES = (
    SECURITY_EVENT_REFRESH_TOKEN_REUSE_DETECTED,
    SECURITY_EVENT_REFRESH_TOKEN_FAMILY_REVOKED,
    SECURITY_EVENT_CSRF_FAILED,
    SECURITY_EVENT_LOGIN_FAILED_REPEATED,
    SECURITY_EVENT_UNAUTHORIZED_MATCH_ACCESS_ATTEMPTED,
    SECURITY_EVENT_NON_PARTICIPANT_ACTION_SUBMIT_ATTEMPTED,
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


def is_refresh_token_reuse_status(status: str) -> bool:
    if status not in REFRESH_TOKEN_STATUSES:
        raise ValueError(f"unknown refresh token status: {status}")

    return status in REFRESH_TOKEN_REUSE_STATUSES
