import os
import re
import uuid
from types import SimpleNamespace


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from django.conf import settings
from rest_framework.test import APIClient

django.setup()

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{32}$")


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def test_profile_me_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().get(
        "/api/v1/profile/me",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 401
    body = response.json()

    assert set(body) == {"error", "meta"}
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_profile_me_with_access_cookie_returns_success_envelope(monkeypatch):
    from backend.apps.profiles import services as profile_services

    expected_user = {
        "id": "1",
        "email": "user@example.com",
        "created_at": "2026-06-04T00:00:00Z",
    }
    expected_profile = {
        "nickname": "pilot",
        "public_record": {
            "ai_story_matches": 2,
            "ai_story_wins": 1,
            "ai_story_losses": 1,
        },
        "style_summary": {
            "label": None,
            "display_text": None,
            "metrics": {
                "aggression": 0.0,
                "defense": 0.0,
                "insight_focus": 0.0,
                "deception": 0.0,
                "risk_preference": 0.0,
                "silence_reliance": 0.0,
                "crisis_guard_rate": 0.0,
                "crisis_contract_rate": 0.0,
                "late_choice_rate": 0.0,
            },
            "updated_at": None,
        },
    }

    def fake_get_profile_me(*, raw_access_token):
        assert raw_access_token == "access-token"
        return SimpleNamespace(user=expected_user, profile=expected_profile)

    monkeypatch.setattr(profile_services, "get_profile_me", fake_get_profile_me)

    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"
    response = client.get(
        "/api/v1/profile/me",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert body["data"] == {
        "user": expected_user,
        "profile": expected_profile,
    }
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_profile_view_uses_profile_service_and_no_longer_returns_501():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "profiles" / "views.py").read_text(
        encoding="utf-8"
    )

    assert "profile_services.get_profile_me(" in views_source
    assert "api_success_response(" in views_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in views_source
    assert "ProfileAPIServiceNotImplemented" not in views_source
    assert "profile.me" not in views_source
