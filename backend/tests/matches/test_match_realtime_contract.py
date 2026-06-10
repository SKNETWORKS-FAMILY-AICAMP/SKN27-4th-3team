from unittest.mock import Mock
import os
from pathlib import Path

import django
import pytest
from django.conf import settings
from django.test import override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.matches import realtime


ROOT_DIR = Path(__file__).resolve().parents[3]
MATCHES_DIR = ROOT_DIR / "backend" / "apps" / "matches"


def test_match_realtime_group_name_uses_public_match_id_without_raw_token():
    assert realtime.match_group_name(public_match_id="match_2") == "match.match_2"


def test_match_realtime_group_name_rejects_invalid_match_id():
    with pytest.raises(ValueError, match="public_match_id"):
        realtime.match_group_name(public_match_id="2")


def test_match_realtime_route_is_under_access_cookie_path_for_browser_cookie_auth():
    routing_source = (MATCHES_DIR / "routing.py").read_text(encoding="utf-8")
    expected_route = f'{settings.ACCESS_TOKEN_COOKIE_PATH.lstrip("/")}/ws/matches/<str:match_id>'

    assert expected_route in routing_source


def test_match_snapshot_event_reuses_rest_match_shape():
    event = realtime.build_match_snapshot_event(match={"match_id": "match_2"})

    assert event == {
        "type": "match.snapshot",
        "match": {"match_id": "match_2"},
    }


def test_turn_resolved_event_reuses_rest_turn_result_and_match_shapes():
    event = realtime.build_turn_resolved_event(
        turn_result={"turn_id": "turn_7"},
        match={"match_id": "match_2"},
    )

    assert event == {
        "type": "turn.resolved",
        "turn_result": {"turn_id": "turn_7"},
        "match": {"match_id": "match_2"},
    }


@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
def test_publish_turn_resolved_event_defers_delivery_until_transaction_commit(monkeypatch):
    on_commit = Mock()
    monkeypatch.setattr(realtime.transaction, "on_commit", on_commit)

    realtime.publish_turn_resolved(
        match_id="match_2",
        turn_result={"turn_id": "turn_7"},
        match={"match_id": "match_2"},
    )

    on_commit.assert_called_once()
    callback = on_commit.call_args.args[0]

    assert callable(callback)


def test_realtime_auth_uses_existing_http_only_access_cookie(monkeypatch):
    get_current_session = Mock(return_value=Mock(authenticated=True, user={"id": 1}))
    monkeypatch.setattr(realtime.auth_services, "get_current_session", get_current_session)

    session = realtime.authenticate_scope(
        scope={"cookies": {settings.ACCESS_TOKEN_COOKIE_NAME: "access-cookie-value"}}
    )

    assert session.authenticated is True
    get_current_session.assert_called_once_with(raw_access_token="access-cookie-value")


def test_realtime_auth_rejects_missing_access_cookie():
    with pytest.raises(ApiErrorResponseException):
        realtime.authenticate_scope(scope={"cookies": {}})


def test_match_realtime_consumer_sends_configured_heartbeat_without_client_state_change():
    consumer_source = (MATCHES_DIR / "consumers.py").read_text(encoding="utf-8")

    assert "asyncio.create_task(" in consumer_source
    assert "WEBSOCKET_HEARTBEAT_SECONDS" in consumer_source
    assert "EVENT_HEARTBEAT" in consumer_source
    assert "state-changing actions must use REST API" in consumer_source
