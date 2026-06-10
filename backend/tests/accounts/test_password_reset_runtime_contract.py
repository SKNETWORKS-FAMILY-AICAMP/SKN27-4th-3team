import os
from contextlib import nullcontext
from datetime import timedelta
from types import SimpleNamespace

import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()


def test_request_password_reset_accepts_unknown_email_without_token_creation(monkeypatch):
    from backend.apps.accounts import services as auth_services

    reset_tokens = []
    security_events = []

    monkeypatch.setattr(auth_services.User.objects, "filter", lambda **kwargs: [])
    monkeypatch.setattr(auth_services, "_assert_password_reset_not_limited", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "_record_password_reset_request", lambda **_kwargs: None)
    monkeypatch.setattr(
        auth_services.PasswordResetToken.objects,
        "create",
        lambda **kwargs: reset_tokens.append(kwargs),
    )
    monkeypatch.setattr(
        auth_services,
        "record_security_event",
        lambda **kwargs: security_events.append(kwargs),
    )

    result = auth_services.request_password_reset(
        email="missing@example.com",
        request_id="req_test",
        client_ip="203.0.113.10",
    )

    assert result.accepted is True
    assert reset_tokens == []
    assert security_events == [
        {
            "event_type": "password reset requested",
            "user_id": None,
            "request_id": "req_test",
            "metadata": {
                "email_hmac": auth_services.password_reset_email_hmac(
                    "missing@example.com",
                    auth_services.settings.SECRET_KEY,
                )
            },
        }
    ]


def test_request_password_reset_creates_hash_only_token_and_sends_email(monkeypatch):
    from backend.apps.accounts import services as auth_services

    now = auth_services.timezone.now()
    user = SimpleNamespace(id=7, email="player@example.com", is_active=True)
    created_tokens = []
    sent_emails = []

    monkeypatch.setattr(auth_services.timezone, "now", lambda: now)
    monkeypatch.setattr(auth_services.User.objects, "filter", lambda **kwargs: [user])
    monkeypatch.setattr(auth_services, "_assert_password_reset_not_limited", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "_record_password_reset_request", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "new_password_reset_token", lambda: "raw-reset-token")
    monkeypatch.setattr(
        auth_services.PasswordResetToken.objects,
        "create",
        lambda **kwargs: created_tokens.append(kwargs) or SimpleNamespace(**kwargs),
    )
    monkeypatch.setattr(
        auth_services,
        "_send_password_reset_email",
        lambda **kwargs: sent_emails.append(kwargs),
    )
    monkeypatch.setattr(auth_services, "record_security_event", lambda **_kwargs: None)

    result = auth_services.request_password_reset(
        email="PLAYER@example.com",
        request_id="req_test",
        client_ip="203.0.113.10",
    )

    assert result.accepted is True
    assert created_tokens == [
        {
            "user_id": 7,
            "token_hash": auth_services.hash_password_reset_token(
                "raw-reset-token",
                auth_services.settings.SECRET_KEY,
            ),
            "requested_email": "player@example.com",
            "request_ip": "203.0.113.10",
            "created_at": now,
            "expires_at": now + timedelta(seconds=auth_services.settings.PASSWORD_RESET_TOKEN_TTL_SECONDS),
        }
    ]
    assert "raw-reset-token" not in repr(created_tokens)
    assert sent_emails == [
        {
            "user": user,
            "raw_token": "raw-reset-token",
            "requested_email": "player@example.com",
        }
    ]


def test_request_password_reset_delivery_unavailable_does_not_lookup_user(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    security_events = []

    monkeypatch.setattr(auth_services.settings, "PASSWORD_RESET_DELIVERY_ENABLED", False)
    monkeypatch.setattr(auth_services, "_assert_password_reset_not_limited", lambda **_kwargs: None)
    monkeypatch.setattr(auth_services, "_record_password_reset_request", lambda **_kwargs: None)
    monkeypatch.setattr(
        auth_services.User.objects,
        "filter",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not look up user")),
    )
    monkeypatch.setattr(
        auth_services,
        "record_security_event",
        lambda **kwargs: security_events.append(kwargs),
    )

    with pytest.raises(ApiErrorResponseException) as error:
        auth_services.request_password_reset(
            email="player@example.com",
            request_id="req_test",
            client_ip="203.0.113.10",
        )

    assert error.value.code == "PASSWORD_RESET_DELIVERY_UNAVAILABLE"
    assert security_events == [
        {
            "event_type": "password reset delivery unavailable",
            "user_id": None,
            "request_id": "req_test",
            "metadata": {"reason": "email_provider_unavailable"},
        }
    ]


def test_confirm_password_reset_rejects_invalid_token(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    class EmptyQuery:
        def first(self):
            return None

    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(auth_services.PasswordResetToken.objects, "filter", lambda **kwargs: EmptyQuery())
    monkeypatch.setattr(auth_services, "record_security_event", lambda **_kwargs: None)

    with pytest.raises(ApiErrorResponseException) as error:
        auth_services.confirm_password_reset(
            token="missing-token",
            new_password="new-strong-password-123",
            request_id="req_test",
        )

    assert error.value.code == "PASSWORD_RESET_TOKEN_INVALID"
    assert error.value.status_code == 400


def test_confirm_password_reset_changes_password_marks_token_used_and_revokes_sessions(monkeypatch):
    from backend.apps.accounts import services as auth_services

    now = auth_services.timezone.now()
    user = SimpleNamespace(
        id=7,
        email="player@example.com",
        set_password=lambda password: setattr(user, "password_set_to", password),
        save=lambda update_fields: setattr(user, "saved_update_fields", update_fields),
    )
    reset_token = SimpleNamespace(
        user_id=7,
        token_hash=auth_services.hash_password_reset_token(
            "raw-reset-token",
            auth_services.settings.SECRET_KEY,
        ),
        expires_at=now + timedelta(minutes=5),
        used_at=None,
        save=lambda update_fields: setattr(reset_token, "saved_update_fields", update_fields),
    )
    revoked = []

    class Query:
        def first(self):
            return reset_token

    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(auth_services.timezone, "now", lambda: now)
    monkeypatch.setattr(auth_services.PasswordResetToken.objects, "select_for_update", lambda: auth_services.PasswordResetToken.objects)
    monkeypatch.setattr(auth_services.PasswordResetToken.objects, "filter", lambda **kwargs: Query())
    monkeypatch.setattr(auth_services.User.objects, "get", lambda **kwargs: user)
    monkeypatch.setattr(auth_services, "_validate_signup_password", lambda **_kwargs: None)
    monkeypatch.setattr(
        auth_services.RefreshToken.objects,
        "filter",
        lambda **kwargs: SimpleNamespace(update=lambda **update_kwargs: revoked.append((kwargs, update_kwargs))),
    )
    monkeypatch.setattr(auth_services, "record_security_event", lambda **_kwargs: None)

    result = auth_services.confirm_password_reset(
        token="raw-reset-token",
        new_password="new-strong-password-123",
        request_id="req_test",
    )

    assert result.password_reset is True
    assert user.password_set_to == "new-strong-password-123"
    assert user.saved_update_fields == ["password"]
    assert reset_token.used_at == now
    assert reset_token.saved_update_fields == ["used_at"]
    assert revoked == [
        (
            {"user_id": 7},
            {
                "status": auth_services.REVOKED_REFRESH_TOKEN_STATUS,
                "revoked_at": now,
            },
        )
    ]
