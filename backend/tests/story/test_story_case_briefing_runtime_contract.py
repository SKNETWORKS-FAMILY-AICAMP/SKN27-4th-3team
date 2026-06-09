import os
import re
import uuid
from types import SimpleNamespace

import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from django.conf import settings
from rest_framework.test import APIClient

django.setup()

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{32}$")

EXPECTED_MIRROR_GUEST_BRIEFING = {
    "case_id": "mirror_guest",
    "title": "거울 속의 손님",
    "apparition_alias": "거울 속의 손님",
    "briefing_text": [
        "사건 파일 01. 거울 속의 손님.",
        "오래된 방의 거울은 얼굴을 비추지 않는다.",
        "그 안에는 잊힌 기억, 사라진 목소리, 그리고 네가 잃어버린 방 번호가 남아 있다.",
        "같은 것을 두 번 묻지 마라.",
        "첫 번째 대답은 단서일 수 있다.",
        "두 번째 대답은 함정이다.",
        "흩어진 진명 조각을 모아라.",
        "이름을 완성하기 전에는, 거울 너머의 것을 봉인할 수 없다.",
    ],
    "taboo": {
        "title": "같은 질문 반복 금지",
        "description": "같은 정보 대상을 연속으로 조사하면 금기 위반으로 판정한다.",
    },
    "info_targets": [
        {"key": "mirror_surface", "display_name": "거울 표면"},
        {"key": "mirror_back", "display_name": "깨진 거울 뒷면"},
        {"key": "missing_child_voice", "display_name": "사라진 아이의 목소리"},
        {"key": "forgotten_room", "display_name": "잊어버린 방 번호"},
        {"key": "self_reflection", "display_name": "플레이어의 비친 얼굴"},
    ],
    "max_turns": 12,
}
EXPECTED_NAMELESS_CURSE_BRIEFING = {
    "case_id": "nameless_curse",
    "title": "무명(無名)의 저주",
    "apparition_alias": "거울 속 목소리",
    "briefing_text": [
        "사건 파일 02. 무명(無名)의 저주.",
        "안개가 걷히지 않는 저택에는 이름을 빼앗긴 목소리가 남아 있다.",
        "진실의 거울은 얼굴이 아니라, 숨겨진 이름과 상처를 되비춘다.",
        "거울 속 목소리를 처치 대상으로 단정하지 마라.",
        "그 이름을 되찾게 해야 저주의 사슬을 끊을 수 있다.",
    ],
    "taboo": {
        "title": "같은 상처 반복 금지",
        "description": "같은 정보 대상을 연속으로 조사하면 금기 위반으로 판정한다.",
    },
    "info_targets": [
        {"key": "truth_mirror", "display_name": "진실의 거울"},
        {"key": "family_journal", "display_name": "가죽 장정 일기장"},
        {"key": "nameless_thread", "display_name": "무명실"},
        {"key": "basement_wall", "display_name": "지하실 벽"},
        {"key": "self_reflection", "display_name": "플레이어의 비친 얼굴"},
    ],
    "max_turns": 12,
}


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def test_story_case_briefing_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().get(
        "/api/v1/story/cases/mirror_guest/briefing",
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


def test_story_case_briefing_with_access_cookie_returns_success_envelope(monkeypatch):
    from backend.apps.story import services as story_services

    def fake_get_story_case_briefing(*, raw_access_token, case_id):
        assert raw_access_token == "access-token"
        assert case_id == "mirror_guest"
        return SimpleNamespace(case=EXPECTED_MIRROR_GUEST_BRIEFING)

    monkeypatch.setattr(
        story_services,
        "get_story_case_briefing",
        fake_get_story_case_briefing,
    )

    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"
    response = client.get(
        "/api/v1/story/cases/mirror_guest/briefing",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert body["data"] == {"case": EXPECTED_MIRROR_GUEST_BRIEFING}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_story_case_briefing_service_returns_only_approved_mirror_guest_case(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.story.services import get_story_case_briefing

    captured_tokens = []

    def fake_get_current_session(*, raw_access_token):
        captured_tokens.append(raw_access_token)
        return SimpleNamespace(authenticated=True)

    monkeypatch.setattr(auth_services, "get_current_session", fake_get_current_session)

    result = get_story_case_briefing(
        raw_access_token="access-token",
        case_id="mirror_guest",
    )

    assert captured_tokens == ["access-token"]
    assert result.case == EXPECTED_MIRROR_GUEST_BRIEFING


def test_story_case_briefing_service_returns_nameless_curse_pdf_concept_case(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.story.services import get_story_case_briefing

    captured_tokens = []

    def fake_get_current_session(*, raw_access_token):
        captured_tokens.append(raw_access_token)
        return SimpleNamespace(authenticated=True)

    monkeypatch.setattr(auth_services, "get_current_session", fake_get_current_session)

    result = get_story_case_briefing(
        raw_access_token="access-token",
        case_id="nameless_curse",
    )

    assert captured_tokens == ["access-token"]
    assert result.case == EXPECTED_NAMELESS_CURSE_BRIEFING


def test_story_case_briefing_service_returns_case_not_found_for_unknown_case(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.story.services import get_story_case_briefing

    monkeypatch.setattr(
        auth_services,
        "get_current_session",
        lambda *, raw_access_token: SimpleNamespace(authenticated=True),
    )

    with pytest.raises(ApiErrorResponseException) as exc_info:
        get_story_case_briefing(
            raw_access_token="access-token",
            case_id="unknown_case",
        )

    assert exc_info.value.code == "CASE_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_story_case_briefing_view_no_longer_returns_501():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "story" / "views.py").read_text(
        encoding="utf-8"
    )
    briefing_view_source = views_source.split(
        "class StoryCaseBriefingView",
        maxsplit=1,
    )[1].split("\n\nclass StoryCaseMatchStartView", maxsplit=1)[0]

    assert "story_services.get_story_case_briefing(" in briefing_view_source
    assert "api_success_response(" in briefing_view_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in briefing_view_source
    assert "StoryAPIServiceNotImplemented" not in briefing_view_source
    assert "story.cases.briefing" not in briefing_view_source
