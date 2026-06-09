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


def _llm_text_payload(**overrides) -> dict:
    payload = {
        "enabled": False,
        "purpose": "turn_flavor_text",
        "text": None,
        "display_slot": "right_apparition_message",
        "fallback_used": True,
        "generation_id": None,
        "context_refs": [],
        "metadata": {
            "status": "skipped",
            "provider": "groq",
            "model_id": "llama-3.1-8b-instant",
            "reason": "missing_api_key",
        },
    }
    payload.update(overrides)
    return payload


def test_turn_llm_text_without_access_cookie_returns_auth_required_error_envelope():
    response = APIClient().post(
        "/api/v1/matches/match_1/turns/turn_1/llm-text",
        {"display_slot": "right_apparition_message"},
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


def test_turn_llm_text_without_csrf_returns_missing_csrf_error_envelope():
    client = APIClient(enforce_csrf_checks=True)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = "access-token"

    response = client.post(
        "/api/v1/matches/match_1/turns/turn_1/llm-text",
        {"display_slot": "right_apparition_message"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_turn_llm_text_view_returns_success_envelope_from_service(monkeypatch):
    from backend.apps.matches import services as match_services

    expected_llm_text = _llm_text_payload(
        enabled=True,
        text="거울 아래에서 낮은 숨이 돌아온다.",
        fallback_used=False,
        generation_id="llm_generation_1",
        metadata={
            "status": "succeeded",
            "provider": "groq",
            "model_id": "llama-3.1-8b-instant",
        },
    )

    def fake_generate_turn_llm_text(
        *,
        raw_access_token,
        public_match_id,
        public_turn_id,
        display_slot,
    ):
        assert raw_access_token == "access-token"
        assert public_match_id == "match_1"
        assert public_turn_id == "turn_1"
        assert display_slot == "right_apparition_message"
        return SimpleNamespace(llm_text=expected_llm_text)

    monkeypatch.setattr(
        match_services,
        "generate_turn_llm_text",
        fake_generate_turn_llm_text,
    )

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/turns/turn_1/llm-text",
        {"display_slot": "right_apparition_message"},
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"llm_text": expected_llm_text}
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])


def test_turn_llm_text_invalid_display_slot_returns_validation_error(monkeypatch):
    from backend.apps.matches import services as match_services

    def fail_if_called(**_kwargs):
        raise AssertionError("invalid payload must not reach service")

    monkeypatch.setattr(match_services, "generate_turn_llm_text", fail_if_called)

    response = _client_with_access_cookie().post(
        "/api/v1/matches/match_1/turns/turn_1/llm-text",
        {"display_slot": ""},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_turn_llm_text_view_source_uses_csrf_cookie_session_and_service_boundary():
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[3]
    views_source = (root_dir / "backend" / "apps" / "matches" / "views.py").read_text(
        encoding="utf-8"
    )
    turn_llm_source = views_source.split("class TurnLlmTextView", maxsplit=1)[1].split(
        "\n\nclass ",
        maxsplit=1,
    )[0]

    assert "@method_decorator(csrf_protect, name=\"dispatch\")" in views_source
    assert "match_services.generate_turn_llm_text(" in turn_llm_source
    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in turn_llm_source
    assert "api_success_response(" in turn_llm_source
    assert "llm.generation" not in turn_llm_source
