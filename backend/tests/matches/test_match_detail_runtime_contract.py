import os
import re
import uuid
from datetime import datetime, timezone
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


def _client_with_access_cookie(raw_access_token: str = "access-token") -> APIClient:
    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = raw_access_token
    return client


def _expected_match_state() -> dict:
    return {
        "match_id": "match_1",
        "mode": "ai_story",
        "status": "active",
        "case": {"case_id": "mirror_guest", "title": "mirror guest"},
        "turn": {
            "turn_id": "turn_1",
            "turn_number": 1,
            "max_turns": 12,
            "status": "awaiting_player",
            "deadline_at": "2026-06-05T00:00:25Z",
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


def test_match_detail_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().get(
        "/api/v1/matches/match_1",
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


def test_match_detail_view_returns_success_envelope_from_service(monkeypatch):
    from backend.apps.matches import services as match_services

    expected_match = _expected_match_state()

    def fake_get_match_detail(*, raw_access_token, public_match_id):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_1"
        return SimpleNamespace(match=expected_match)

    monkeypatch.setattr(match_services, "get_match_detail", fake_get_match_detail)

    response = _client_with_access_cookie().get(
        "/api/v1/matches/match_1",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert body["data"] == {"match": expected_match}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_match_detail_unknown_match_returns_match_not_found(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    def fake_get_match_detail(*, raw_access_token, public_match_id):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_404"
        raise ApiErrorResponseException("MATCH_NOT_FOUND", status_code=404)

    monkeypatch.setattr(match_services, "get_match_detail", fake_get_match_detail)

    response = _client_with_access_cookie().get(
        "/api/v1/matches/match_404",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MATCH_NOT_FOUND"


def test_match_detail_other_user_match_returns_access_denied(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    def fake_get_match_detail(*, raw_access_token, public_match_id):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_2"
        raise ApiErrorResponseException("MATCH_ACCESS_DENIED", status_code=403)

    monkeypatch.setattr(match_services, "get_match_detail", fake_get_match_detail)

    response = _client_with_access_cookie().get(
        "/api/v1/matches/match_2",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MATCH_ACCESS_DENIED"


def test_match_detail_service_source_uses_public_id_and_start_request_membership():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    services_source = (root_dir / "backend" / "apps" / "matches" / "services.py").read_text(
        encoding="utf-8"
    )

    assert "def get_match_detail(" in services_source
    assert "def parse_public_match_id(" in services_source
    assert "MatchStartRequest.objects" in services_source
    assert "user_id=user_id" in services_source
    assert "match_id=match_id" in services_source
    assert "MATCH_ACCESS_DENIED" in services_source
    assert "order_by(\"-turn_number\", \"-id\")" in services_source
    assert "Match.objects.get(id=match_id)" in services_source


def test_match_detail_service_resolves_expired_awaiting_turn_before_formatting():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    services_source = (root_dir / "backend" / "apps" / "matches" / "services.py").read_text(
        encoding="utf-8"
    )
    detail_source = services_source.split("def get_match_detail(", maxsplit=1)[1].split(
        "\n\ndef get_match_result(",
        maxsplit=1,
    )[0]
    assert "def _resolve_expired_current_turn_if_needed(" in services_source
    assert "def _resolve_and_persist_turn(" in services_source
    timeout_helper_source = services_source.split(
        "def _resolve_expired_current_turn_if_needed(",
        maxsplit=1,
    )[1].split("\n\ndef ", maxsplit=1)[0]
    persist_helper_source = services_source.split(
        "def _resolve_and_persist_turn(",
        maxsplit=1,
    )[1].split("\n\ndef ", maxsplit=1)[0]
    turn_result_payload_source = services_source.split(
        "def _turn_result_payload(",
        maxsplit=1,
    )[1].split("\n\ndef ", maxsplit=1)[0]

    assert "_resolve_expired_current_turn_if_needed(" in detail_source
    assert detail_source.index("_resolve_expired_current_turn_if_needed(") < (
        detail_source.index("format_match_state(")
    )
    assert "player_action_code=None" in timeout_helper_source
    assert "ActionSubmission.objects.filter(" in timeout_helper_source
    assert "_resolve_and_persist_turn(" in timeout_helper_source
    assert "turn_result" in timeout_helper_source
    assert "current_turn_resolution.turn_result is not None" in detail_source
    assert "realtime.publish_turn_resolved(" in detail_source
    assert "turn.resolved_at = now" in persist_helper_source
    assert "_turn_result_payload(" in persist_helper_source
    assert "TurnResult.objects.create(" in persist_helper_source
    assert "timeout_applied" in turn_result_payload_source


def test_shared_match_state_formatter_uses_persisted_human_resource_fields():
    from backend.apps.matches.constants import (
        MATCH_MODE_AI_STORY,
        MATCH_STATUS_ACTIVE,
        PARTICIPANT_TYPE_APPARITION,
        PARTICIPANT_TYPE_HUMAN,
        TURN_STATUS_AWAITING_PLAYER,
    )
    from backend.apps.story.services import format_match_state

    state = format_match_state(
        session=SimpleNamespace(
            user={"id": "1", "email": "user@example.com"},
            profile={"nickname": "pilot"},
        ),
        match=SimpleNamespace(id=1, mode=MATCH_MODE_AI_STORY, status=MATCH_STATUS_ACTIVE),
        turn=SimpleNamespace(
            id=1,
            turn_number=1,
            status=TURN_STATUS_AWAITING_PLAYER,
            deadline_at=datetime(2026, 6, 5, 0, 0, 25, tzinfo=timezone.utc),
            resolved_at=None,
        ),
        human_participant=SimpleNamespace(
            id=1,
            participant_type=PARTICIPANT_TYPE_HUMAN,
            sanity=7,
            ritual_power=4,
            curse_marks=2,
            secret_exposure=1,
            true_name_fragments=1,
            incomplete_true_name_fragments=1,
            false_clues=1,
            suspicion=2,
            shield=1,
            timeout_count=1,
        ),
        apparition_participant=SimpleNamespace(
            id=2,
            participant_type=PARTICIPANT_TYPE_APPARITION,
        ),
        now=datetime(2026, 6, 5, 0, 0, 0, tzinfo=timezone.utc),
        case_id="mirror_guest",
    )

    assert state["player"]["resources"]["sanity"] == 7
    assert state["player"]["resources"]["ritual_power"] == 4
    assert state["player"]["resources"]["curse_marks"] == 2
    assert state["player"]["resources"]["true_name_fragments"] == 1
    assert state["player"]["resources"]["incomplete_true_name_fragments"] == 1
    assert state["player"]["resources"]["false_clues"] == 1
    assert state["player"]["resources"]["suspicion"] == 2
    assert state["player"]["resources"]["shield"] == 1
    assert state["player"]["resources"]["timeout_count"] == 1


def test_shared_match_state_formatter_prefers_match_start_player_display_name(monkeypatch):
    from backend.apps.matches.constants import (
        MATCH_MODE_AI_STORY,
        MATCH_STATUS_ACTIVE,
        PARTICIPANT_TYPE_APPARITION,
        PARTICIPANT_TYPE_HUMAN,
        TURN_STATUS_AWAITING_PLAYER,
    )
    from backend.apps.story import services as story_services
    from backend.apps.story.services import format_match_state

    monkeypatch.setattr(
        story_services,
        "_stored_match_player_display_name",
        lambda *, match_id: "Yunseo",
        raising=False,
    )
    monkeypatch.setattr(
        story_services,
        "_get_match_case_id",
        lambda *, match_id: "nameless_curse",
    )

    state = format_match_state(
        session=SimpleNamespace(
            user={"id": "1", "email": "user@example.com"},
            profile={"nickname": "profile-nickname"},
        ),
        match=SimpleNamespace(id=1, mode=MATCH_MODE_AI_STORY, status=MATCH_STATUS_ACTIVE),
        turn=SimpleNamespace(
            id=1,
            turn_number=1,
            status=TURN_STATUS_AWAITING_PLAYER,
            deadline_at=datetime(2026, 6, 5, 0, 0, 25, tzinfo=timezone.utc),
            resolved_at=None,
        ),
        human_participant=SimpleNamespace(
            id=1,
            participant_type=PARTICIPANT_TYPE_HUMAN,
            sanity=12,
            ritual_power=3,
            curse_marks=0,
            secret_exposure=0,
            true_name_fragments=0,
            incomplete_true_name_fragments=0,
            false_clues=0,
            suspicion=0,
            shield=0,
            timeout_count=0,
        ),
        apparition_participant=SimpleNamespace(
            id=2,
            participant_type=PARTICIPANT_TYPE_APPARITION,
        ),
        now=datetime(2026, 6, 5, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert state["player"]["display_name"] == "Yunseo"


def test_nameless_curse_match_state_enables_seal_after_two_true_name_fragments():
    from backend.apps.matches.constants import (
        MATCH_MODE_AI_STORY,
        MATCH_STATUS_ACTIVE,
        PARTICIPANT_TYPE_APPARITION,
        PARTICIPANT_TYPE_HUMAN,
        TURN_STATUS_AWAITING_PLAYER,
    )
    from backend.apps.story.services import format_match_state

    state = format_match_state(
        session=SimpleNamespace(
            user={"id": "1", "email": "user@example.com"},
            profile={"nickname": "pilot"},
        ),
        match=SimpleNamespace(id=1, mode=MATCH_MODE_AI_STORY, status=MATCH_STATUS_ACTIVE),
        turn=SimpleNamespace(
            id=1,
            turn_number=1,
            status=TURN_STATUS_AWAITING_PLAYER,
            deadline_at=datetime(2026, 6, 5, 0, 0, 25, tzinfo=timezone.utc),
            resolved_at=None,
        ),
        human_participant=SimpleNamespace(
            id=1,
            participant_type=PARTICIPANT_TYPE_HUMAN,
            sanity=12,
            ritual_power=3,
            curse_marks=0,
            secret_exposure=0,
            true_name_fragments=2,
            incomplete_true_name_fragments=0,
            false_clues=0,
            suspicion=0,
            shield=0,
            timeout_count=0,
        ),
        apparition_participant=SimpleNamespace(
            id=2,
            participant_type=PARTICIPANT_TYPE_APPARITION,
        ),
        now=datetime(2026, 6, 5, 0, 0, 0, tzinfo=timezone.utc),
        case_id="nameless_curse",
    )

    seal_action = next(action for action in state["available_actions"] if action["code"] == "seal")

    assert state["player"]["resources"]["true_name_fragments_required"] == 2
    assert state["opponent"]["display_name"] == "거울 속 목소리"
    assert state["opponent"]["public_state"]["true_name_fragments_required"] == 2
    assert state["opponent"]["public_state"]["seal_available"] is True
    assert seal_action["enabled"] is True
