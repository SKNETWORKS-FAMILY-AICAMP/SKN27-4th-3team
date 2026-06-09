import os
from contextlib import nullcontext
from datetime import timedelta
from types import SimpleNamespace

import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from rest_framework.test import APIClient

django.setup()


def _valid_signup_payload(**overrides):
    payload = {
        "email": "player@example.com",
        "nickname": "pilot",
        "password": "strong-password-123",
    }
    payload.update(overrides)
    return payload


def test_official_auth_policy_records_option_b_password_and_login_rate_limit_contract():
    import json
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    spec = json.loads((root_dir / "api-spec" / "pilot-mvp-api.official.json").read_text(
        encoding="utf-8"
    ))
    auth_contract = spec["api"]["auth"]
    login_endpoint = next(
        endpoint for endpoint in spec["endpoints"] if endpoint["id"] == "auth.login"
    )

    assert auth_contract["password_policy"] == {
        "min_length": 10,
        "max_length": 128,
        "common_password_blocked": True,
        "numeric_only_blocked": True,
        "similar_to_email_or_nickname_blocked": True,
        "validation_error_code": "VALIDATION_ERROR",
    }
    assert auth_contract["login_failure_rate_limit"] == {
        "identity": "normalized email + server observed REMOTE_ADDR",
        "trusted_proxy_headers": "not used until a trusted proxy policy is approved",
        "window_seconds": 600,
        "failure_limit": 5,
        "lockout_seconds": 900,
        "http_status": 429,
        "error_code": "LOGIN_RATE_LIMITED",
        "reset_on_success": True,
        "invalid_credentials_response_hides_account_existence": True,
    }
    assert "LOGIN_RATE_LIMITED" in login_endpoint["errors"]


@pytest.mark.parametrize(
    ("password", "expected_fragment"),
    [
        ("short123", "10"),
        ("password123", "common"),
        ("1234567890", "숫자"),
        ("player@example.com", "유사"),
    ],
)
def test_signup_service_rejects_passwords_that_violate_option_b_policy(
    monkeypatch,
    password,
    expected_fragment,
):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    def fail_if_called(**_kwargs):
        raise AssertionError("password policy must reject before user creation")

    monkeypatch.setattr(auth_services.User.objects, "create_user", fail_if_called)
    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)

    with pytest.raises(ApiErrorResponseException) as error:
        auth_services.signup(
            email="player@example.com",
            nickname="pilot",
            password=password,
        )

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 400
    assert "password" in error.value.details
    assert expected_fragment in " ".join(error.value.details["password"])


def test_login_view_passes_server_observed_remote_addr_without_trusting_x_forwarded_for(
    monkeypatch,
):
    from backend.apps.accounts import services as auth_services

    def fake_login(*, email, password, request_id, client_ip):
        assert email == "player@example.com"
        assert password == "strong-password-123"
        assert request_id.startswith("req_")
        assert client_ip == "203.0.113.9"
        return SimpleNamespace(
            user={"id": "1", "email": email, "created_at": "2026-06-06T00:00:00Z"},
            profile={
                "nickname": "pilot",
                "public_record": {
                    "ai_story_matches": 0,
                    "ai_story_wins": 0,
                    "ai_story_losses": 0,
                },
                "style_summary": {
                    "label": None,
                    "display_text": None,
                    "metrics": {},
                    "updated_at": None,
                },
            },
            access_token="access-token",
            refresh_token="refresh-token",
            access_expires_in_seconds=900,
        )

    monkeypatch.setattr(auth_services, "login", fake_login)

    response = APIClient().post(
        "/api/v1/auth/login",
        {"email": "player@example.com", "password": "strong-password-123"},
        format="json",
        REMOTE_ADDR="203.0.113.9",
        HTTP_X_FORWARDED_FOR="198.51.100.1",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200


class _FakeThrottleRow:
    def __init__(self, *, email, ip_address, failure_count, first_failed_at, last_failed_at):
        self.email = email
        self.ip_address = ip_address
        self.failure_count = failure_count
        self.first_failed_at = first_failed_at
        self.last_failed_at = last_failed_at
        self.blocked_until = None
        self.saved_update_fields = []

    def save(self, *, update_fields):
        self.saved_update_fields.append(tuple(update_fields))


class _FakeThrottleQuery:
    def __init__(self, manager, *, email, ip_address):
        self.manager = manager
        self.email = email
        self.ip_address = ip_address

    def delete(self):
        self.manager.deleted_identities.append((self.email, self.ip_address))
        self.manager.rows.pop((self.email, self.ip_address), None)


class _FakeThrottleManager:
    def __init__(self):
        self.rows = {}
        self.deleted_identities = []

    def select_for_update(self):
        return self

    def get_or_create(self, *, email, ip_address, defaults):
        identity = (email, ip_address)
        if identity in self.rows:
            return self.rows[identity], False

        row = _FakeThrottleRow(
            email=email,
            ip_address=ip_address,
            failure_count=defaults["failure_count"],
            first_failed_at=defaults["first_failed_at"],
            last_failed_at=defaults["last_failed_at"],
        )
        self.rows[identity] = row
        return row, True

    def filter(self, *, email, ip_address):
        return _FakeThrottleQuery(self, email=email, ip_address=ip_address)


def test_login_service_blocks_email_ip_identity_on_fifth_failed_attempt(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    now = auth_services.timezone.now()
    throttle_manager = _FakeThrottleManager()

    monkeypatch.setattr(
        auth_services,
        "LoginFailureThrottle",
        SimpleNamespace(objects=throttle_manager),
        raising=False,
    )
    monkeypatch.setattr(auth_services.timezone, "now", lambda: now)
    monkeypatch.setattr(auth_services, "authenticate", lambda username, password: None)
    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(auth_services, "record_security_event", lambda **_kwargs: None)

    for attempt_number in range(1, 5):
        with pytest.raises(ApiErrorResponseException) as error:
            auth_services.login(
                email="Player@Example.com",
                password="wrong-password",
                request_id=f"req_{attempt_number}",
                client_ip="203.0.113.10",
            )

        assert error.value.code == "INVALID_CREDENTIALS"

    with pytest.raises(ApiErrorResponseException) as blocked_error:
        auth_services.login(
            email="Player@Example.com",
            password="wrong-password",
            request_id="req_5",
            client_ip="203.0.113.10",
        )

    row = throttle_manager.rows[("player@example.com", "203.0.113.10")]
    assert blocked_error.value.code == "LOGIN_RATE_LIMITED"
    assert blocked_error.value.status_code == 429
    assert row.failure_count == 5
    assert row.blocked_until == now + timedelta(seconds=900)


def test_login_success_resets_email_ip_failure_count_before_issuing_tokens(monkeypatch):
    from backend.apps.accounts import services as auth_services

    now = auth_services.timezone.now()
    throttle_manager = _FakeThrottleManager()
    throttle_manager.rows[("player@example.com", "203.0.113.10")] = _FakeThrottleRow(
        email="player@example.com",
        ip_address="203.0.113.10",
        failure_count=4,
        first_failed_at=now,
        last_failed_at=now,
    )
    user = SimpleNamespace(id=7)
    session = SimpleNamespace(
        user={"id": "7", "email": "player@example.com", "created_at": "2026-06-06T00:00:00Z"},
        profile={
            "nickname": "pilot",
            "public_record": {
                "ai_story_matches": 0,
                "ai_story_wins": 0,
                "ai_story_losses": 0,
            },
            "style_summary": {
                "label": None,
                "display_text": None,
                "metrics": {},
                "updated_at": None,
            },
        },
    )

    monkeypatch.setattr(
        auth_services,
        "LoginFailureThrottle",
        SimpleNamespace(objects=throttle_manager),
        raising=False,
    )
    monkeypatch.setattr(auth_services.timezone, "now", lambda: now)
    monkeypatch.setattr(auth_services, "authenticate", lambda username, password: user)
    monkeypatch.setattr(auth_services, "_session_for_user_id", lambda user_id: session)
    monkeypatch.setattr(auth_services, "new_login_refresh_token_identifiers", lambda: "ids")
    monkeypatch.setattr(auth_services, "_create_refresh_token", lambda **_kwargs: "refresh")
    monkeypatch.setattr(auth_services, "issue_access_token", lambda **_kwargs: "access")
    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)

    result = auth_services.login(
        email="player@example.com",
        password="strong-password-123",
        request_id="req_success",
        client_ip="203.0.113.10",
    )

    assert result.access_token == "access"
    assert throttle_manager.deleted_identities == [("player@example.com", "203.0.113.10")]
