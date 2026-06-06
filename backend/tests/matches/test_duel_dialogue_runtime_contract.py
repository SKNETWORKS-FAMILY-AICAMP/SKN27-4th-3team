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


def _client_with_access_cookie(raw_access_token: str = "access-token") -> APIClient:
    client = APIClient()
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = raw_access_token
    return client


def _valid_payload(**overrides) -> dict:
    payload = {
        "message": "네 이름을 알고 있어. 피티.",
        "client_nonce": "11111111-1111-4111-8111-111111111111",
    }
    payload.update(overrides)
    return payload


def _dialogue_payload(**overrides) -> dict:
    payload = {
        "dialogue_id": "duel_dialogue_1",
        "match_id": "match_1",
        "player_message": "네 이름을 알고 있어. 피티.",
        "apparition_message": None,
        "llm_text": {
            "enabled": False,
            "purpose": "final_duel_dialogue",
            "text": None,
            "display_slot": "duel_dialogue",
            "fallback_used": True,
            "generation_id": None,
            "context_refs": [],
            "metadata": {
                "status": "skipped",
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "reason": "missing_api_key",
            },
        },
        "created_at": "2026-06-06T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def test_duel_dialogue_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().post(
        "/api/v1/matches/match_1/duel/dialogues",
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


def test_duel_dialogue_without_csrf_returns_missing_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"

    response = client.post(
        "/api/v1/matches/match_1/duel/dialogues",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_duel_dialogue_invalid_payload_returns_validation_error(monkeypatch):
    from backend.apps.matches import services as match_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid payload must not reach service")

    monkeypatch.setattr(match_services, "create_duel_dialogue", fail_if_called)

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/duel/dialogues",
        _valid_payload(message="", client_nonce="not-a-uuid"),
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in body["error"]["details"]
    assert "client_nonce" in body["error"]["details"]


def test_duel_dialogue_view_returns_success_envelope_from_service(monkeypatch):
    from backend.apps.matches import services as match_services

    expected_dialogue = _dialogue_payload(
        apparition_message="그 이름은 아직 네 입에 남아 있구나.",
        llm_text={
            "enabled": True,
            "purpose": "final_duel_dialogue",
            "text": "그 이름은 아직 네 입에 남아 있구나.",
            "display_slot": "duel_dialogue",
            "fallback_used": False,
            "generation_id": "llm_generation_1",
            "context_refs": [],
            "metadata": {
                "status": "succeeded",
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
            },
        },
    )

    def fake_create_duel_dialogue(
        *,
        raw_access_token,
        public_match_id,
        message,
        client_nonce,
    ):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_1"
        assert message == "네 이름을 알고 있어. 피티."
        assert client_nonce == uuid.UUID("11111111-1111-4111-8111-111111111111")
        return SimpleNamespace(dialogue=expected_dialogue)

    monkeypatch.setattr(match_services, "create_duel_dialogue", fake_create_duel_dialogue)

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/duel/dialogues",
        _valid_payload(),
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"dialogue": expected_dialogue}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_duel_dialogue_runtime_errors_use_approved_status_mapping(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.matches import services as match_services

    error_cases = {
        "MATCH_NOT_FOUND": 404,
        "MATCH_ACCESS_DENIED": 403,
        "DUEL_DIALOGUE_LIMIT_EXCEEDED": 409,
    }

    for error_code, status_code in error_cases.items():

        def fake_create_duel_dialogue(**_kwargs):
            raise ApiErrorResponseException(error_code, status_code=status_code)

        monkeypatch.setattr(match_services, "create_duel_dialogue", fake_create_duel_dialogue)

        response = _client_with_access_cookie().post(
            "/api/v1/matches/match_1/duel/dialogues",
            _valid_payload(client_nonce=str(uuid.uuid4())),
            format="json",
            HTTP_HOST="localhost",
        )

        assert response.status_code == status_code
        assert response.json()["error"]["code"] == error_code


def test_duel_dialogue_view_source_uses_csrf_cookie_session_and_service_boundary():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "matches" / "views.py").read_text(
        encoding="utf-8"
    )
    duel_source = views_source.split("class DuelDialogueView", maxsplit=1)[1].split(
        "\n\nclass ",
        maxsplit=1,
    )[0]

    assert "@method_decorator(csrf_protect, name=\"dispatch\")" in views_source
    assert "match_services.create_duel_dialogue(" in duel_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in duel_source
    assert "api_success_response(" in duel_source
    assert "llm.generation" not in duel_source
