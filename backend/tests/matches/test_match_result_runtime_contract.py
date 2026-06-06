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


def _style_summary() -> dict:
    return {
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
    }


def _expected_result() -> dict:
    return {
        "match_id": "match_1",
        "result": "player_win",
        "result_reason": "seal_success",
        "case": {"case_id": "mirror_guest", "title": "mirror guest"},
        "final_resources": {
            "sanity": 5,
            "sanity_max": 12,
            "ritual_power": 1,
            "ritual_power_max": 5,
            "curse_marks": 2,
            "curse_marks_max": 5,
            "true_name_fragments": 3,
            "true_name_fragments_required": 3,
            "incomplete_true_name_fragments": 0,
            "false_clues": 1,
            "false_clues_max": 3,
            "suspicion": 0,
            "suspicion_max": 3,
            "shield": 0,
            "shield_max": 1,
            "timeout_count": 0,
        },
        "turn_logs": [
            {
                "turn_number": 1,
                "text": "The mirror surface briefly held its shape.",
                "log_key": None,
            }
        ],
        "story_result_text": [
            "The name fragments align, and the room releases the mirror's hold."
        ],
        "style_summary": _style_summary(),
        "llm_summary": {"enabled": False, "text": None, "generation_id": None},
    }


def test_match_result_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().get(
        "/api/v1/matches/match_1/result",
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


def test_match_result_view_returns_success_envelope_from_service(monkeypatch):
    from backend.apps.matches import services as match_services

    expected_result = _expected_result()

    def fake_get_match_result(*, raw_access_token, public_match_id):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_1"
        return SimpleNamespace(result=expected_result)

    monkeypatch.setattr(match_services, "get_match_result", fake_get_match_result)

    response = _client_with_access_cookie().get(
        "/api/v1/matches/match_1/result",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert body["data"] == {"result": expected_result}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_match_result_runtime_errors_use_approved_status_mapping(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    error_cases = {
        "MATCH_NOT_FOUND": 404,
        "MATCH_ACCESS_DENIED": 403,
        "MATCH_NOT_RESOLVED": 409,
    }

    for error_code, status_code in error_cases.items():

        def fake_get_match_result(**_kwargs):
            raise ApiErrorResponseException(error_code, status_code=status_code)

        monkeypatch.setattr(match_services, "get_match_result", fake_get_match_result)

        response = _client_with_access_cookie().get(
            "/api/v1/matches/match_1/result",
            HTTP_HOST="localhost",
        )

        assert response.status_code == status_code
        assert response.json()["error"]["code"] == error_code


def test_match_result_service_builds_official_payload_from_resolved_match(monkeypatch):
    from backend.apps.matches import services as match_services
    from backend.apps.matches.constants import (
        MATCH_MODE_AI_STORY,
        MATCH_STATUS_RESOLVED,
        PARTICIPANT_TYPE_APPARITION,
        PARTICIPANT_TYPE_HUMAN,
    )

    style_summary = _style_summary()
    session = SimpleNamespace(
        user={"id": "10", "email": "player@example.com"},
        profile={"nickname": "pilot", "style_summary": style_summary},
    )
    match = SimpleNamespace(
        id=1,
        mode=MATCH_MODE_AI_STORY,
        status=MATCH_STATUS_RESOLVED,
        winner_participant_id=7,
    )
    human_participant = SimpleNamespace(
        id=7,
        sanity=5,
        ritual_power=1,
        curse_marks=2,
        secret_exposure=0,
        true_name_fragments=3,
        incomplete_true_name_fragments=0,
        false_clues=1,
        suspicion=0,
        shield=0,
        timeout_count=0,
    )
    apparition_participant = SimpleNamespace(id=8)
    last_turn = SimpleNamespace(id=3, turn_number=3)
    turn_logs = [
        {
            "turn_number": 1,
            "text": "The mirror surface briefly held its shape.",
            "log_key": None,
        }
    ]

    def fake_get_current_session(*, raw_access_token):
        assert raw_access_token == "access-token"
        return session

    def fake_get_participant(*, match_id, participant_type):
        assert match_id == 1
        if participant_type == PARTICIPANT_TYPE_HUMAN:
            return human_participant
        if participant_type == PARTICIPANT_TYPE_APPARITION:
            return apparition_participant
        raise AssertionError(f"unexpected participant_type: {participant_type}")

    monkeypatch.setattr(
        match_services.auth_services,
        "get_current_session",
        fake_get_current_session,
    )
    monkeypatch.setattr(match_services, "_get_match", lambda *, match_id: match)
    monkeypatch.setattr(match_services, "_assert_match_access", lambda **_kwargs: None)
    monkeypatch.setattr(match_services, "_get_participant", fake_get_participant)
    monkeypatch.setattr(match_services, "_get_current_turn", lambda *, match_id: last_turn)
    monkeypatch.setattr(
        match_services,
        "_get_match_case_id",
        lambda *, match_id: "mirror_guest",
        raising=False,
    )
    monkeypatch.setattr(
        match_services,
        "_get_match_turn_logs",
        lambda *, match_id: turn_logs,
        raising=False,
    )
    monkeypatch.setattr(
        match_services.llm_services,
        "generate_result_summary",
        lambda **_kwargs: {"enabled": False, "text": None, "generation_id": None},
    )

    result = match_services.get_match_result(
        raw_access_token="access-token",
        public_match_id="match_1",
    )

    assert result.result["match_id"] == "match_1"
    assert result.result["result"] == "player_win"
    assert result.result["result_reason"] == "seal_success"
    assert result.result["case"]["case_id"] == "mirror_guest"
    assert result.result["final_resources"] == _expected_result()["final_resources"]
    assert result.result["turn_logs"] == turn_logs
    assert result.result["style_summary"] == style_summary
    assert result.result["llm_summary"] == {
        "enabled": False,
        "text": None,
        "generation_id": None,
    }
    assert result.result["story_result_text"]


def test_match_result_service_uses_nameless_curse_case_and_result_text(monkeypatch):
    from backend.apps.matches import services as match_services
    from backend.apps.matches.constants import (
        MATCH_MODE_AI_STORY,
        MATCH_STATUS_RESOLVED,
        PARTICIPANT_TYPE_APPARITION,
        PARTICIPANT_TYPE_HUMAN,
    )

    session = SimpleNamespace(
        user={"id": "10", "email": "player@example.com"},
        profile={"nickname": "pilot", "style_summary": _style_summary()},
    )
    match = SimpleNamespace(
        id=1,
        mode=MATCH_MODE_AI_STORY,
        status=MATCH_STATUS_RESOLVED,
        winner_participant_id=7,
    )
    human_participant = SimpleNamespace(
        id=7,
        sanity=6,
        ritual_power=1,
        curse_marks=1,
        secret_exposure=0,
        true_name_fragments=3,
        incomplete_true_name_fragments=0,
        false_clues=0,
        suspicion=0,
        shield=0,
        timeout_count=0,
    )

    def fake_get_participant(*, match_id, participant_type):
        assert match_id == 1
        if participant_type == PARTICIPANT_TYPE_HUMAN:
            return human_participant
        if participant_type == PARTICIPANT_TYPE_APPARITION:
            return SimpleNamespace(id=8)
        raise AssertionError(f"unexpected participant_type: {participant_type}")

    monkeypatch.setattr(
        match_services.auth_services,
        "get_current_session",
        lambda *, raw_access_token: session,
    )
    monkeypatch.setattr(match_services, "_get_match", lambda *, match_id: match)
    monkeypatch.setattr(match_services, "_assert_match_access", lambda **_kwargs: None)
    monkeypatch.setattr(match_services, "_get_participant", fake_get_participant)
    monkeypatch.setattr(
        match_services,
        "_get_current_turn",
        lambda *, match_id: SimpleNamespace(id=3, turn_number=3),
    )
    monkeypatch.setattr(match_services, "_get_match_case_id", lambda *, match_id: "nameless_curse", raising=False)
    monkeypatch.setattr(match_services, "_get_match_turn_logs", lambda *, match_id: [], raising=False)
    monkeypatch.setattr(
        match_services.llm_services,
        "generate_result_summary",
        lambda **_kwargs: {"enabled": False, "text": None, "generation_id": None},
    )

    result = match_services.get_match_result(
        raw_access_token="access-token",
        public_match_id="match_1",
    )

    assert result.result["case"] == {
        "case_id": "nameless_curse",
        "title": "무명(無名)의 저주",
    }
    assert any("피티" in line for line in result.result["story_result_text"])


def test_match_result_service_rejects_unresolved_match(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services
    from backend.apps.matches.constants import MATCH_MODE_AI_STORY, MATCH_STATUS_ACTIVE

    monkeypatch.setattr(
        match_services.auth_services,
        "get_current_session",
        lambda *, raw_access_token: SimpleNamespace(
            user={"id": "10"},
            profile={"nickname": "pilot", "style_summary": _style_summary()},
        ),
    )
    monkeypatch.setattr(
        match_services,
        "_get_match",
        lambda *, match_id: SimpleNamespace(
            id=1,
            mode=MATCH_MODE_AI_STORY,
            status=MATCH_STATUS_ACTIVE,
            winner_participant_id=None,
        ),
    )
    monkeypatch.setattr(match_services, "_assert_match_access", lambda **_kwargs: None)

    with pytest.raises(ApiErrorResponseException) as error:
        match_services.get_match_result(
            raw_access_token="access-token",
            public_match_id="match_1",
        )

    assert error.value.code == "MATCH_NOT_RESOLVED"
    assert error.value.status_code == 409


def test_match_result_llm_boundary_generates_summary_after_server_result_payload():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    llm_services_path = root_dir / "backend" / "apps" / "llm" / "services.py"
    matches_source = (root_dir / "backend" / "apps" / "matches" / "services.py").read_text(
        encoding="utf-8"
    )

    assert llm_services_path.exists()
    llm_services_source = llm_services_path.read_text(encoding="utf-8")
    result_source = matches_source.split("def get_match_result(", maxsplit=1)[1].split(
        "\n\ndef parse_public_match_id",
        maxsplit=1,
    )[0]

    assert "def generate_result_summary(" in llm_services_source
    assert "llm_services.generate_result_summary(" in result_source
    assert "llm_summary = llm_services.generate_result_summary(" in result_source
    assert "result_payload[\"llm_summary\"] = llm_summary" in result_source
    assert result_source.index("\"story_result_text\"") < result_source.index(
        "llm_services.generate_result_summary("
    )
