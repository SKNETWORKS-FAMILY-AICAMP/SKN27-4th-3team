import os
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()


def test_password_reset_request_without_csrf_returns_missing_csrf_error():
    client = APIClient(enforce_csrf_checks=True)

    response = client.post(
        "/api/v1/auth/password-reset/request",
        {"email": "player@example.com"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_password_reset_request_view_returns_accepted_without_token(monkeypatch):
    from backend.apps.accounts import services as auth_services

    calls = []

    def fake_request_password_reset(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(accepted=True)

    monkeypatch.setattr(auth_services, "request_password_reset", fake_request_password_reset)

    response = APIClient().post(
        "/api/v1/auth/password-reset/request",
        {"email": "player@example.com"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"accepted": True}
    assert "token" not in response.content.decode("utf-8")
    assert calls[0]["email"] == "player@example.com"
    assert calls[0]["client_ip"] == "127.0.0.1"


def test_password_reset_confirm_view_returns_success_without_auth_cookies(monkeypatch):
    from backend.apps.accounts import services as auth_services

    monkeypatch.setattr(
        auth_services,
        "confirm_password_reset",
        lambda **kwargs: SimpleNamespace(password_reset=True),
    )

    response = APIClient().post(
        "/api/v1/auth/password-reset/confirm",
        {"token": "reset-token", "new_password": "new-strong-password-123"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"password_reset": True}
    assert "pilot_access" not in response.cookies
    assert "pilot_refresh" not in response.cookies


def test_password_reset_confirm_invalid_payload_stops_before_service(monkeypatch):
    from backend.apps.accounts import services as auth_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid payload must not reach service")

    monkeypatch.setattr(auth_services, "confirm_password_reset", fail_if_called)

    response = APIClient().post(
        "/api/v1/auth/password-reset/confirm",
        {"token": "", "new_password": "short"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
