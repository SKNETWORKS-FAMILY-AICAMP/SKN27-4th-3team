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


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def _valid_payload(client_request_id: str | None = None) -> dict[str, str]:
    return {
        "client_request_id": client_request_id
        or "11111111-1111-4111-8111-111111111111",
    }


def _client_with_access_cookie(raw_access_token: str = "access-token") -> APIClient:
    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = raw_access_token
    return client


def test_story_match_start_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().post(
        "/api/v1/story/cases/mirror_guest/matches",
        _valid_payload(),
        format="json",
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


def test_story_match_start_without_csrf_returns_missing_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"

    response = client.post(
        "/api/v1/story/cases/mirror_guest/matches",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 403
    body = response.json()

    assert body["error"]["code"] == "CSRF_TOKEN_MISSING"
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_story_match_start_with_invalid_csrf_returns_invalid_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)
    csrf_response = client.get("/api/v1/auth/csrf", HTTP_HOST="localhost")
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"

    response = client.post(
        "/api/v1/story/cases/mirror_guest/matches",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
        HTTP_X_CSRFTOKEN="invalid-token",
    )

    assert csrf_response.status_code == 200
    assert response.status_code == 403
    body = response.json()

    assert body["error"]["code"] == "CSRF_TOKEN_INVALID"
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_story_match_start_unknown_case_returns_case_not_found(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.story import services as story_services

    def fake_start_story_case_match(*, raw_access_token, case_id, client_request_id):
        assert raw_access_token == "access-token"
        assert case_id == "unknown_case"
        raise ApiErrorResponseException("CASE_NOT_FOUND", status_code=404)

    monkeypatch.setattr(
        story_services,
        "start_story_case_match",
        fake_start_story_case_match,
    )

    response = _client_with_access_cookie().post(
        "/api/v1/story/cases/unknown_case/matches",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_story_match_start_invalid_client_request_id_returns_validation_error(monkeypatch):
    from backend.apps.story import services as story_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid payload must not reach story match start service")

    monkeypatch.setattr(story_services, "start_story_case_match", fail_if_called)

    response = _client_with_access_cookie().post(
        "/api/v1/story/cases/mirror_guest/matches",
        {"client_request_id": "not-a-uuid"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "client_request_id" in body["error"]["details"]


def test_story_match_start_view_returns_created_match_state_from_service(monkeypatch):
    from backend.apps.story import services as story_services

    expected_match = {
        "match_id": "match_1",
        "mode": "ai_story",
        "status": "active",
        "case": {"case_id": "mirror_guest", "title": "거울 속의 손님"},
        "turn": {
            "turn_id": "turn_1",
            "turn_number": 1,
            "max_turns": 12,
            "status": "awaiting_player",
            "deadline_at": "2026-06-04T00:00:25Z",
            "remaining_seconds": 25,
            "resolved_at": None,
        },
        "player": {
            "participant_id": "participant_1",
            "participant_type": "human",
            "display_name": "pilot",
            "resources": {
                "sanity": 12,
                "sanity_max": 12,
                "ritual_power": 3,
                "ritual_power_max": 5,
                "curse_marks": 0,
                "curse_marks_max": 5,
                "true_name_fragments": 0,
                "true_name_fragments_required": 3,
                "incomplete_true_name_fragments": 0,
                "false_clues": 0,
                "false_clues_max": 3,
                "suspicion": 0,
                "suspicion_max": 3,
                "shield": 0,
                "shield_max": 1,
                "timeout_count": 0,
            },
        },
        "opponent": {
            "participant_id": "participant_2",
            "participant_type": "apparition",
            "display_name": "거울 속의 손님",
            "public_state": {
                "true_name_fragments_revealed": 0,
                "true_name_fragments_required": 3,
                "seal_available": False,
            },
        },
        "available_actions": [
            {
                "code": "curse",
                "display_name": "저주",
                "ritual_power_cost": 2,
                "enabled": True,
                "disabled_reason": None,
                "requires_info_target": False,
            },
            {
                "code": "seal",
                "display_name": "봉인",
                "ritual_power_cost": 2,
                "enabled": False,
                "disabled_reason": "TRUE_NAME_FRAGMENTS_NOT_ENOUGH",
                "requires_info_target": True,
            },
        ],
        "clues": [],
        "recent_public_logs": [],
    }

    def fake_start_story_case_match(*, raw_access_token, case_id, client_request_id):
        assert raw_access_token == "access-token"
        assert case_id == "mirror_guest"
        assert client_request_id == uuid.UUID("11111111-1111-4111-8111-111111111111")
        return SimpleNamespace(match=expected_match)

    monkeypatch.setattr(
        story_services,
        "start_story_case_match",
        fake_start_story_case_match,
    )

    response = _client_with_access_cookie().post(
        "/api/v1/story/cases/mirror_guest/matches",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["data"] == {"match": expected_match}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_story_match_start_service_source_uses_idempotency_table_and_initial_match_rows():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    services_source = (root_dir / "backend" / "apps" / "story" / "services.py").read_text(
        encoding="utf-8"
    )

    assert "def start_story_case_match(" in services_source
    assert "transaction.atomic()" in services_source
    assert "MatchStartRequest.objects.select_for_update()" in services_source
    assert "Match.objects.create(" in services_source
    assert "MatchParticipant.objects.create(" in services_source
    assert "Turn.objects.create(" in services_source
    assert "IDEMPOTENCY_CONFLICT" in services_source
    assert "deadline_at=now + timedelta(seconds=DEFAULT_TURN_SECONDS)" in services_source


def test_story_match_start_service_checks_idempotency_before_case_allowlist():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    services_source = (root_dir / "backend" / "apps" / "story" / "services.py").read_text(
        encoding="utf-8"
    )
    transaction_source = services_source.split(
        "def _start_story_case_match_in_transaction(",
        maxsplit=1,
    )[1].split("\n\ndef _existing_match_start_result(", maxsplit=1)[0]

    assert transaction_source.index("MatchStartRequest.objects.select_for_update()") < (
        transaction_source.index("_assert_supported_story_case(case_id=case_id)")
    )


def test_story_match_start_match_detail_and_turn_submit_no_longer_return_501():
    match_start_response = _client_with_access_cookie().post(
        "/api/v1/story/cases/mirror_guest/matches",
        _valid_payload("not-a-uuid"),
        format="json",
        HTTP_HOST="localhost",
    )

    assert match_start_response.status_code != 501

    client = APIClient()
    assert client.get("/api/v1/matches/match_1", HTTP_HOST="localhost").status_code != 501
    assert (
        client.post(
            "/api/v1/matches/match_1/turns",
            {"action_code": "silence", "client_nonce": str(uuid.uuid4())},
            format="json",
            HTTP_HOST="localhost",
        ).status_code
        != 501
    )
    assert (
        client.get("/api/v1/matches/match_1/result", HTTP_HOST="localhost").status_code
        != 501
    )
