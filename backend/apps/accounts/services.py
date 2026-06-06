import uuid
from dataclasses import dataclass
from datetime import timedelta, timezone as datetime_timezone
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils import timezone

from backend.apps.accounts.models import RefreshToken, SecurityEvent, User
from backend.apps.accounts.tokens import (
    ACTIVE_REFRESH_TOKEN_STATUS,
    REFRESH_TOKEN_REUSE_ERROR_CODE,
    REFRESH_TOKEN_TYPE,
    REUSED_REFRESH_TOKEN_STATUS,
    REVOKED_REFRESH_TOKEN_STATUS,
    ROTATED_REFRESH_TOKEN_STATUS,
    SECURITY_EVENT_REFRESH_TOKEN_FAMILY_REVOKED,
    SECURITY_EVENT_REFRESH_TOKEN_REUSE_DETECTED,
    RefreshTokenIdentifiers,
    decode_jwt_token,
    hash_refresh_token,
    is_refresh_token_reuse_status,
    issue_access_token,
    issue_refresh_token,
    new_refresh_token_jti,
    new_login_refresh_token_identifiers,
)
from backend.apps.accounts.tokens import ACCESS_TOKEN_TYPE
from backend.apps.ai_profile.models import StyleMetricSnapshot
from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.profiles.models import Profile


HTTP_401_UNAUTHORIZED = 401
HTTP_400_BAD_REQUEST = 400
HTTP_500_INTERNAL_SERVER_ERROR = 500
FORBIDDEN_SECURITY_METADATA_KEYS = (
    "raw_token",
    "token_hash",
    "password",
    "cookie",
    "csrf_token",
)
STYLE_METRIC_FIELDS = (
    "aggression",
    "defense",
    "insight_focus",
    "deception",
    "risk_preference",
    "silence_reliance",
    "crisis_guard_rate",
    "crisis_contract_rate",
    "late_choice_rate",
)


@dataclass(frozen=True)
class SignupResult:
    user: dict[str, Any]


@dataclass(frozen=True)
class LoginResult:
    user: dict[str, Any]
    profile: dict[str, Any]
    access_token: str
    refresh_token: str
    access_expires_in_seconds: int


@dataclass(frozen=True)
class RefreshResult:
    access_token: str
    refresh_token: str
    access_expires_in_seconds: int


@dataclass(frozen=True)
class SessionResult:
    authenticated: bool
    user: dict[str, Any]
    profile: dict[str, Any]


def login(
    *,
    email: str,
    password: str,
    request_id: str | None,
) -> LoginResult:
    user = authenticate(username=email, password=password)
    if user is None:
        raise ApiErrorResponseException(
            "INVALID_CREDENTIALS",
            status_code=HTTP_401_UNAUTHORIZED,
        )

    issued_at = timezone.now()
    identifiers = new_login_refresh_token_identifiers()
    refresh_token = _create_refresh_token(
        user_id=user.id,
        identifiers=identifiers,
        issued_at=issued_at,
    )
    access_token = issue_access_token(
        user_id=user.id,
        signing_secret=settings.SECRET_KEY,
        issued_at=issued_at,
        ttl_seconds=settings.ACCESS_TOKEN_TTL_SECONDS,
    )

    session = _session_for_user_id(user.id)
    return LoginResult(
        user=session.user,
        profile=session.profile,
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_in_seconds=settings.ACCESS_TOKEN_TTL_SECONDS,
    )


def signup(
    *,
    email: str,
    nickname: str,
    password: str,
) -> SignupResult:
    try:
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password)
            Profile.objects.create(
                user=user,
                nickname=nickname,
                ai_story_matches=0,
                ai_story_wins=0,
                ai_story_losses=0,
                style_label=None,
                style_display_text=None,
                style_summary_updated_at=None,
            )
    except IntegrityError as exc:
        raise ApiErrorResponseException(
            "VALIDATION_ERROR",
            status_code=HTTP_400_BAD_REQUEST,
            details={"email": ["A user with this email already exists."]},
        ) from exc

    return SignupResult(user=_format_user(user))


def refresh(
    *,
    raw_refresh_token: str | None,
    request_id: str | None,
) -> RefreshResult:
    if not raw_refresh_token:
        raise _session_expired()

    claims = _decode_token_or_expire(raw_refresh_token, expected_token_type=REFRESH_TOKEN_TYPE)
    submitted_jti = _claim_uuid(claims, "jti")
    submitted_family_id = _claim_uuid(claims, "family_id")
    submitted_user_id = _claim_user_id(claims)
    submitted_hash = hash_refresh_token(raw_refresh_token, settings.SECRET_KEY)
    issued_at = timezone.now()

    with transaction.atomic():
        token = _locked_refresh_token(submitted_jti)
        _assert_submitted_refresh_token_matches(
            token=token,
            submitted_hash=submitted_hash,
            submitted_family_id=submitted_family_id,
            submitted_user_id=submitted_user_id,
        )

        if is_refresh_token_reuse_status(token.status):
            _handle_refresh_token_reuse(token=token, request_id=request_id, now=issued_at)

        if token.status != ACTIVE_REFRESH_TOKEN_STATUS:
            raise _session_expired()

        if token.expires_at <= issued_at:
            token.status = REVOKED_REFRESH_TOKEN_STATUS
            token.revoked_at = issued_at
            token.save(update_fields=("status", "revoked_at"))
            raise _session_expired()

        new_identifiers = RefreshTokenIdentifiers(
            jti=new_refresh_token_jti(),
            family_id=token.family_id,
        )
        new_refresh_token = _create_refresh_token(
            user_id=token.user_id,
            identifiers=new_identifiers,
            issued_at=issued_at,
        )

        token.status = ROTATED_REFRESH_TOKEN_STATUS
        token.rotated_at = issued_at
        token.replaced_by_jti = new_identifiers.jti
        token.save(update_fields=("status", "rotated_at", "replaced_by_jti"))

    access_token = issue_access_token(
        user_id=submitted_user_id,
        signing_secret=settings.SECRET_KEY,
        issued_at=issued_at,
        ttl_seconds=settings.ACCESS_TOKEN_TTL_SECONDS,
    )
    return RefreshResult(
        access_token=access_token,
        refresh_token=new_refresh_token,
        access_expires_in_seconds=settings.ACCESS_TOKEN_TTL_SECONDS,
    )


def get_current_session(*, raw_access_token: str | None) -> SessionResult:
    if not raw_access_token:
        raise ApiErrorResponseException("AUTH_REQUIRED", status_code=HTTP_401_UNAUTHORIZED)

    claims = _decode_token_or_expire(raw_access_token, expected_token_type=ACCESS_TOKEN_TYPE)
    return _session_for_user_id(_claim_user_id(claims))


def revoke_refresh_token_family(
    *,
    family_id: uuid.UUID,
    now,
    exclude_jti: uuid.UUID | None = None,
) -> None:
    tokens = RefreshToken.objects.filter(family_id=family_id)
    if exclude_jti is not None:
        tokens = tokens.exclude(jti=exclude_jti)

    tokens.update(
        status=REVOKED_REFRESH_TOKEN_STATUS,
        revoked_at=now,
    )


def record_security_event(
    *,
    event_type: str,
    user_id: int | None,
    request_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    safe_metadata = _safe_security_metadata({} if metadata is None else metadata)
    SecurityEvent.objects.create(
        event_type=event_type,
        user_id=user_id,
        request_id=request_id,
        metadata=safe_metadata,
    )


def _create_refresh_token(
    *,
    user_id: int,
    identifiers: RefreshTokenIdentifiers,
    issued_at,
) -> str:
    raw_refresh_token = issue_refresh_token(
        user_id=user_id,
        identifiers=identifiers,
        signing_secret=settings.SECRET_KEY,
        issued_at=issued_at,
        ttl_seconds=settings.REFRESH_TOKEN_TTL_SECONDS,
    )
    RefreshToken.objects.create(
        user_id=user_id,
        jti=identifiers.jti,
        family_id=identifiers.family_id,
        token_hash=hash_refresh_token(raw_refresh_token, settings.SECRET_KEY),
        status=ACTIVE_REFRESH_TOKEN_STATUS,
        issued_at=issued_at,
        expires_at=issued_at + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS),
    )
    return raw_refresh_token


def _locked_refresh_token(jti: uuid.UUID) -> RefreshToken:
    try:
        return RefreshToken.objects.select_for_update().get(jti=jti)
    except RefreshToken.DoesNotExist as exc:
        raise _session_expired() from exc


def _assert_submitted_refresh_token_matches(
    *,
    token: RefreshToken,
    submitted_hash: str,
    submitted_family_id: uuid.UUID,
    submitted_user_id: int,
) -> None:
    if token.token_hash != submitted_hash:
        raise _session_expired()
    if token.family_id != submitted_family_id:
        raise _session_expired()
    if token.user_id != submitted_user_id:
        raise _session_expired()


def _handle_refresh_token_reuse(
    *,
    token: RefreshToken,
    request_id: str | None,
    now,
) -> None:
    revoke_refresh_token_family(family_id=token.family_id, now=now, exclude_jti=token.jti)
    token.status = REUSED_REFRESH_TOKEN_STATUS
    token.reused_at = now
    token.revoked_at = now
    token.save(update_fields=("status", "reused_at", "revoked_at"))
    record_security_event(
        event_type=SECURITY_EVENT_REFRESH_TOKEN_REUSE_DETECTED,
        user_id=token.user_id,
        request_id=request_id,
        metadata={"family_id": str(token.family_id), "jti": str(token.jti)},
    )
    record_security_event(
        event_type=SECURITY_EVENT_REFRESH_TOKEN_FAMILY_REVOKED,
        user_id=token.user_id,
        request_id=request_id,
        metadata={"family_id": str(token.family_id)},
    )
    raise ApiErrorResponseException(
        REFRESH_TOKEN_REUSE_ERROR_CODE,
        status_code=HTTP_401_UNAUTHORIZED,
    )


def _decode_token_or_expire(raw_token: str, *, expected_token_type: str) -> dict[str, Any]:
    try:
        return decode_jwt_token(
            raw_token,
            signing_secret=settings.SECRET_KEY,
            expected_token_type=expected_token_type,
        )
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise _session_expired() from exc


def _claim_uuid(claims: dict[str, Any], key: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(claims[key]))
    except (KeyError, TypeError, ValueError) as exc:
        raise _session_expired() from exc


def _claim_user_id(claims: dict[str, Any]) -> int:
    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _session_expired() from exc

    if user_id <= 0:
        raise _session_expired()

    return user_id


def _session_for_user_id(user_id: int) -> SessionResult:
    try:
        user = User.objects.get(id=user_id, is_active=True)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist) as exc:
        raise ApiErrorResponseException(
            "SESSION_EXPIRED",
            status_code=HTTP_401_UNAUTHORIZED,
        ) from exc

    return SessionResult(
        authenticated=True,
        user=_format_user(user),
        profile=_format_profile(user=user, profile=profile),
    )


def _format_user(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": _iso_utc(user.created_at),
    }


def _format_profile(*, user: User, profile: Profile) -> dict[str, Any]:
    snapshot = StyleMetricSnapshot.objects.filter(user_id=user.id).order_by("-id").first()
    return {
        "nickname": profile.nickname,
        "public_record": {
            "ai_story_matches": profile.ai_story_matches,
            "ai_story_wins": profile.ai_story_wins,
            "ai_story_losses": profile.ai_story_losses,
        },
        "style_summary": {
            "label": profile.style_label,
            "display_text": profile.style_display_text,
            "metrics": _style_metrics(snapshot),
            "updated_at": _iso_utc(profile.style_summary_updated_at),
        },
    }


def _style_metrics(snapshot: StyleMetricSnapshot | None) -> dict[str, float]:
    if snapshot is None:
        return {field: 0.0 for field in STYLE_METRIC_FIELDS}

    return {field: getattr(snapshot, field) for field in STYLE_METRIC_FIELDS}


def _iso_utc(value) -> str | None:
    if value is None:
        return None

    return value.astimezone(datetime_timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_security_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    for key in metadata:
        lowered_key = str(key).lower()
        if any(forbidden_key in lowered_key for forbidden_key in FORBIDDEN_SECURITY_METADATA_KEYS):
            raise ValueError(f"forbidden security event metadata key: {key}")

    return dict(metadata)


def _session_expired() -> ApiErrorResponseException:
    return ApiErrorResponseException(
        "SESSION_EXPIRED",
        status_code=HTTP_401_UNAUTHORIZED,
    )
