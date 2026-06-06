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


def _client_with_access_cookie(raw_access_token: str = "access-token") -> APIClient:
    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = raw_access_token
    return client


def _valid_payload(**overrides) -> dict:
    payload = {
        "action_code": "silence",
        "client_nonce": "11111111-1111-4111-8111-111111111111",
    }
    payload.update(overrides)
    return payload


def _turn_submit_result() -> dict:
    return {
        "turn_id": "turn_1",
        "turn_number": 1,
        "player_action": {
            "code": "silence",
            "display_name": "침묵",
            "info_target_key": None,
            "timeout_applied": False,
        },
        "opponent_action": {
            "code": "silence",
            "display_name": "침묵",
            "info_target_key": None,
            "timeout_applied": False,
        },
        "public_log": {
            "turn_number": 1,
            "text": "아무 말도 오가지 않았다.",
            "log_key": None,
        },
        "state_delta": {},
        "clue_delta": {
            "added": [],
            "removed_clue_ids": [],
            "revealed": [],
        },
        "match_outcome": "unresolved",
    }


def _match_state() -> dict:
    return {
        "match_id": "match_1",
        "mode": "ai_story",
        "status": "active",
        "case": {"case_id": "mirror_guest", "title": "mirror guest"},
        "turn": {
            "turn_id": "turn_2",
            "turn_number": 2,
            "max_turns": 12,
            "status": "awaiting_player",
            "deadline_at": "2026-06-05T00:00:50Z",
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
                "ritual_power": 4,
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
            "display_name": "mirror guest",
            "public_state": {
                "true_name_fragments_revealed": 0,
                "true_name_fragments_required": 3,
                "seal_available": False,
            },
        },
        "available_actions": [],
        "clues": [],
        "recent_public_logs": [],
    }


def test_turn_submit_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().post(
        "/api/v1/matches/match_1/turns",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_turn_submit_without_csrf_returns_missing_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"

    response = client.post(
        "/api/v1/matches/match_1/turns",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_turn_submit_invalid_client_nonce_returns_validation_error(monkeypatch):
    from backend.apps.matches import services as match_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid payload must not reach turn submit service")

    monkeypatch.setattr(match_services, "submit_match_turn", fail_if_called)

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/turns",
        _valid_payload(client_nonce="not-a-uuid"),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "client_nonce" in body["error"]["details"]


def test_turn_submit_view_returns_turn_result_and_next_match_state(monkeypatch):
    from backend.apps.matches import services as match_services

    expected_turn_result = _turn_submit_result()
    expected_match = _match_state()

    def fake_submit_match_turn(
        *,
        raw_access_token,
        public_match_id,
        action_code,
        info_target_key,
        client_nonce,
    ):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_1"
        assert action_code == "silence"
        assert info_target_key is None
        assert client_nonce == uuid.UUID("11111111-1111-4111-8111-111111111111")
        return SimpleNamespace(
            turn_result=expected_turn_result,
            match=expected_match,
        )

    monkeypatch.setattr(match_services, "submit_match_turn", fake_submit_match_turn)

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/turns",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {
        "turn_result": expected_turn_result,
        "match": expected_match,
    }
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_turn_submit_runtime_errors_use_approved_status_mapping(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    error_cases = {
        "TURN_ALREADY_SUBMITTED": 409,
        "MATCH_ALREADY_FINISHED": 409,
        "ACTION_NOT_AVAILABLE": 400,
        "INFO_TARGET_REQUIRED": 400,
        "INSUFFICIENT_RITUAL_POWER": 400,
        "TURN_DEADLINE_EXPIRED": 400,
    }

    for error_code, status_code in error_cases.items():
        def fake_submit_match_turn(**_kwargs):
            raise ApiErrorResponseException(error_code, status_code=status_code)

        monkeypatch.setattr(match_services, "submit_match_turn", fake_submit_match_turn)

        response = _client_with_access_cookie().post(
            "/api/v1/matches/match_1/turns",
            _valid_payload(),
            format="json",
            HTTP_HOST="localhost",
        )

        assert response.status_code == status_code
        assert response.json()["error"]["code"] == error_code


def test_turn_submit_view_source_uses_csrf_cookie_session_and_service_boundary():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "matches" / "views.py").read_text(
        encoding="utf-8"
    )
    turn_view_source = views_source.split("class TurnSubmitView", maxsplit=1)[1].split(
        "\n\nclass MatchResultView",
        maxsplit=1,
    )[0]

    assert "@method_decorator(csrf_protect, name=\"dispatch\")" in views_source
    assert "match_services.submit_match_turn(" in turn_view_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in turn_view_source
    assert "api_success_response(" in turn_view_source
    assert "matches.turns.submit" not in turn_view_source


def test_turn_submit_decision_constraints_are_encoded_in_source():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    story_constants = (root_dir / "backend" / "apps" / "story" / "constants.py").read_text(
        encoding="utf-8"
    )
    services_source = (root_dir / "backend" / "apps" / "matches" / "services.py").read_text(
        encoding="utf-8"
    )
    turn_submit_source = services_source.split("def submit_match_turn(", maxsplit=1)[1].split(
        "\n\ndef _match_result(",
        maxsplit=1,
    )[0]

    assert "APPROVED_MIRROR_GUEST_TRUE_NAME_FRAGMENTS" in story_constants
    assert "APPROVED_MIRROR_GUEST_FALSE_CLUES" in story_constants
    assert "apply_deterministic_false_clue_detection" in services_source
    assert "false_clue_detection_success_rate" not in turn_submit_source
    assert "random" not in turn_submit_source
    assert "llm" not in turn_submit_source.lower()
    assert "backend.apps.retrieval" not in turn_submit_source
    assert "embedding" not in turn_submit_source.lower()


def test_turn_submit_validation_uses_case_specific_nameless_curse_info_targets():
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    human_participant = SimpleNamespace(
        ritual_power=3,
        true_name_fragments=0,
    )

    match_services._validate_turn_submit_request(
        action_code="insight",
        info_target_key="family_journal",
        human_participant=human_participant,
        case_id="nameless_curse",
    )

    with pytest.raises(ApiErrorResponseException) as exc_info:
        match_services._validate_turn_submit_request(
            action_code="insight",
            info_target_key="family_journal",
            human_participant=human_participant,
            case_id="mirror_guest",
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 400


def test_turn_submit_service_uses_start_request_membership_access_guard():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    services_source = (root_dir / "backend" / "apps" / "matches" / "services.py").read_text(
        encoding="utf-8"
    )

    assert "_assert_match_access(user_id=user_id, match_id=match_id)" in services_source
    assert "def _assert_match_access(" in services_source
    access_guard_source = services_source.split(
        "def _assert_match_access(",
        maxsplit=1,
    )[1].split("\n\ndef ", maxsplit=1)[0]
    assert "MatchStartRequest.objects.filter(" in access_guard_source
    assert "user_id=user_id" in access_guard_source
    assert "match_id=match_id" in access_guard_source
    assert "MATCH_ACCESS_DENIED" in access_guard_source
    assert "status_code=HTTP_403_FORBIDDEN" in access_guard_source
