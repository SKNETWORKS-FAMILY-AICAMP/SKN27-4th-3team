import os
import re
import uuid
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from django.db import IntegrityError


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from rest_framework.test import APIClient

django.setup()

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{32}$")


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def _valid_payload(**overrides) -> dict[str, str]:
    payload = {
        "email": "player@example.com",
        "nickname": "pilot",
        "password": "password1234",
    }
    payload.update(overrides)
    return payload


def test_signup_without_csrf_returns_missing_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)

    response = client.post(
        "/api/v1/auth/signup",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_signup_invalid_payload_returns_validation_error_without_service_call(monkeypatch):
    from backend.apps.accounts import services as auth_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid signup payload must not reach auth service")

    monkeypatch.setattr(auth_services, "signup", fail_if_called, raising=False)

    response = APIClient().post(
        "/api/v1/auth/signup",
        _valid_payload(email="not-an-email"),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "email" in body["error"]["details"]


def test_signup_view_returns_created_user_without_auth_cookies(monkeypatch):
    from backend.apps.accounts import services as auth_services

    expected_user = {
        "id": "1",
        "email": "player@example.com",
        "created_at": "2026-06-06T00:00:00Z",
    }

    def fake_signup(*, email, nickname, password):
        assert email == "player@example.com"
        assert nickname == "pilot"
        assert password == "password1234"
        return SimpleNamespace(user=expected_user)

    monkeypatch.setattr(auth_services, "signup", fake_signup, raising=False)

    response = APIClient().post(
        "/api/v1/auth/signup",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["data"] == {"user": expected_user}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])
    assert "pilot_access" not in response.cookies
    assert "pilot_refresh" not in response.cookies


def test_signup_service_creates_user_and_profile_with_explicit_initial_public_record(
    monkeypatch,
):
    from backend.apps.accounts import services as auth_services

    created_profiles = []
    user = SimpleNamespace(
        id=1,
        email="player@example.com",
        created_at=auth_services.timezone.now(),
    )

    def fake_create_user(*, email, password):
        assert email == "player@example.com"
        assert password == "password1234"
        return user

    def fake_profile_create(**kwargs):
        created_profiles.append(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(auth_services.User.objects, "create_user", fake_create_user)
    monkeypatch.setattr(auth_services.Profile.objects, "create", fake_profile_create)
    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)

    result = auth_services.signup(
        email="player@example.com",
        nickname="pilot",
        password="password1234",
    )

    assert result.user["id"] == "1"
    assert result.user["email"] == "player@example.com"
    assert created_profiles == [
        {
            "user": user,
            "nickname": "pilot",
            "ai_story_matches": 0,
            "ai_story_wins": 0,
            "ai_story_losses": 0,
            "style_label": None,
            "style_display_text": None,
            "style_summary_updated_at": None,
        }
    ]


def test_signup_service_maps_duplicate_email_to_validation_error(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException

    def fake_create_user(*, email, password):
        raise IntegrityError("duplicate email")

    monkeypatch.setattr(auth_services.User.objects, "create_user", fake_create_user)
    monkeypatch.setattr(auth_services.transaction, "atomic", nullcontext)

    with pytest.raises(ApiErrorResponseException) as error:
        auth_services.signup(
            email="player@example.com",
            nickname="pilot",
            password="password1234",
        )

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 400
    assert "email" in error.value.details


def test_signup_view_delegates_to_service_and_logout_stays_unimplemented():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "accounts" / "views.py").read_text(
        encoding="utf-8"
    )
    signup_source = views_source.split("class SignupView", maxsplit=1)[1].split(
        "\n\nclass LoginView",
        maxsplit=1,
    )[0]
    logout_source = views_source.split("class LogoutView", maxsplit=1)[1].split(
        "\n\nclass RefreshView",
        maxsplit=1,
    )[0]

    assert "@method_decorator(csrf_protect, name=\"dispatch\")" in views_source
    assert "auth_services.signup(" in signup_source
    assert "api_success_response(" in signup_source
    assert "status_code=status.HTTP_201_CREATED" in signup_source
    assert '"access_token":' not in signup_source
    assert '"refresh_token":' not in signup_source
    assert "raise AuthServiceNotImplemented(\"auth.logout\")" in logout_source
