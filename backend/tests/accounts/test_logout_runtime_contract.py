import os
import uuid
from contextlib import nullcontext
from datetime import timedelta
from types import SimpleNamespace

import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from rest_framework.test import APIClient

django.setup()


def test_logout_service_revokes_active_refresh_family_and_records_event(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.accounts.tokens import ACTIVE_REFRESH_TOKEN_STATUS, REFRESH_TOKEN_TYPE

    family_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
    jti = uuid.UUID("22222222-2222-4222-8222-222222222222")
    now = auth_services.timezone.now()
    token = SimpleNamespace(
        jti=jti,
        family_id=family_id,
        user_id=7,
        token_hash="submitted-hash",
        status=ACTIVE_REFRESH_TOKEN_STATUS,
        expires_at=now + timedelta(minutes=5),
    )
    revoked_families = []
    security_events = []

    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(auth_services.timezone, "now", lambda: now)
    monkeypatch.setattr(
        auth_services,
        "_decode_token_or_expire",
        lambda raw_token, *, expected_token_type: {
            "token_type": REFRESH_TOKEN_TYPE,
            "sub": "7",
            "jti": str(jti),
            "family_id": str(family_id),
        },
    )
    monkeypatch.setattr(auth_services, "hash_refresh_token", lambda raw_token, secret: "submitted-hash")
    monkeypatch.setattr(auth_services, "_locked_refresh_token", lambda submitted_jti: token)
    monkeypatch.setattr(
        auth_services,
        "revoke_refresh_token_family",
        lambda **kwargs: revoked_families.append(kwargs),
    )
    monkeypatch.setattr(
        auth_services,
        "record_security_event",
        lambda **kwargs: security_events.append(kwargs),
    )

    result = auth_services.logout(
        raw_refresh_token="raw-refresh",
        raw_access_token=None,
        request_id="req_test",
    )

    assert result.logged_out is True
    assert revoked_families == [{"family_id": family_id, "now": now}]
    assert security_events == [
        {
            "event_type": "refresh token family revoke",
            "user_id": 7,
            "request_id": "req_test",
            "metadata": {"family_id": str(family_id)},
        }
    ]


def test_logout_service_allows_access_only_logout_without_family_revoke(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.accounts.tokens import ACCESS_TOKEN_TYPE

    revoked_families = []

    def fake_decode(raw_token, *, expected_token_type):
        assert raw_token == "raw-access"
        assert expected_token_type == ACCESS_TOKEN_TYPE
        return {"token_type": ACCESS_TOKEN_TYPE, "sub": "7"}

    monkeypatch.setattr(auth_services, "_decode_token_or_expire", fake_decode)
    monkeypatch.setattr(
        auth_services,
        "revoke_refresh_token_family",
        lambda **kwargs: revoked_families.append(kwargs),
    )

    result = auth_services.logout(
        raw_refresh_token=None,
        raw_access_token="raw-access",
        request_id="req_test",
    )

    assert result.logged_out is True
    assert revoked_families == []


def test_logout_view_clears_auth_cookies_on_success(monkeypatch):
    from backend.apps.accounts import services as auth_services

    monkeypatch.setattr(
        auth_services,
        "logout",
        lambda **kwargs: SimpleNamespace(logged_out=True),
    )

    response = APIClient().post(
        "/api/v1/auth/logout",
        {},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"logged_out": True}
    assert response.cookies["pilot_access"]["max-age"] == 0
    assert response.cookies["pilot_refresh"]["max-age"] == 0


def test_refresh_view_clears_auth_cookies_on_refresh_token_reuse(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    def raise_reuse(**_kwargs):
        raise ApiErrorResponseException("REFRESH_TOKEN_REUSED", status_code=401)

    monkeypatch.setattr(auth_services, "refresh", raise_reuse)

    response = APIClient().post(
        "/api/v1/auth/refresh",
        {},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    assert response.cookies["pilot_access"]["max-age"] == 0
    assert response.cookies["pilot_refresh"]["max-age"] == 0


def test_login_checks_session_before_issuing_tokens(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    user = SimpleNamespace(id=7)
    token_creation_attempts = []

    monkeypatch.setattr(auth_services, "_assert_login_not_limited", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "_reset_login_failure_count", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "authenticate", lambda username, password: user)
    monkeypatch.setattr(
        auth_services,
        "_session_for_user_id",
        lambda user_id: (_ for _ in ()).throw(
            ApiErrorResponseException("SESSION_EXPIRED", status_code=401)
        ),
    )
    monkeypatch.setattr(
        auth_services,
        "_create_refresh_token",
        lambda **kwargs: token_creation_attempts.append(("refresh", kwargs)),
    )
    monkeypatch.setattr(
        auth_services,
        "issue_access_token",
        lambda **kwargs: token_creation_attempts.append(("access", kwargs)),
    )

    with pytest.raises(ApiErrorResponseException) as error:
        auth_services.login(
            email="player@example.com",
            password="password1234",
            request_id="req_test",
            client_ip="203.0.113.10",
        )

    assert error.value.code == "SESSION_EXPIRED"
    assert token_creation_attempts == []
