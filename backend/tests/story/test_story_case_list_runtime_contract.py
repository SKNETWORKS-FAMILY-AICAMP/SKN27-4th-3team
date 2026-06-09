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
EXPECTED_APPROVED_CASES = [
    {
        "case_id": "mirror_guest",
        "title": "거울 속의 손님",
        "summary": "거울을 통해 사람의 기억을 훔치는 괴이.",
        "difficulty": "mvp_01",
        "mvp_available": True,
        "estimated_turns": 12,
    },
    {
        "case_id": "nameless_curse",
        "title": "무명(無名)의 저주",
        "summary": "이름을 빼앗긴 원혼과 진실의 거울을 마주하는 사건.",
        "difficulty": "mvp_02",
        "mvp_available": True,
        "estimated_turns": 12,
    },
]


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def test_story_case_list_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().get(
        "/api/v1/story/cases",
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


def test_story_case_list_with_access_cookie_returns_success_envelope(monkeypatch):
    from backend.apps.story import services as story_services

    def fake_list_story_cases(*, raw_access_token):
        assert raw_access_token == "access-token"
        return SimpleNamespace(cases=EXPECTED_APPROVED_CASES)

    monkeypatch.setattr(story_services, "list_story_cases", fake_list_story_cases)

    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"
    response = client.get(
        "/api/v1/story/cases",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert body["data"] == {"cases": EXPECTED_APPROVED_CASES}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_story_case_list_service_returns_mirror_guest_and_nameless_curse(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.story.services import list_story_cases

    captured_tokens = []

    def fake_get_current_session(*, raw_access_token):
        captured_tokens.append(raw_access_token)
        return SimpleNamespace(authenticated=True)

    monkeypatch.setattr(auth_services, "get_current_session", fake_get_current_session)

    result = list_story_cases(raw_access_token="access-token")

    assert captured_tokens == ["access-token"]
    assert result.cases == EXPECTED_APPROVED_CASES


def test_story_case_list_view_no_longer_returns_501():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "story" / "views.py").read_text(
        encoding="utf-8"
    )
    list_view_source = views_source.split("class StoryCaseListView", maxsplit=1)[1].split(
        "\n\nclass StoryCaseBriefingView",
        maxsplit=1,
    )[0]

    assert "story_services.list_story_cases(" in list_view_source
    assert "api_success_response(" in list_view_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in list_view_source
    assert "StoryAPIServiceNotImplemented" not in list_view_source
    assert "story.cases.list" not in list_view_source
