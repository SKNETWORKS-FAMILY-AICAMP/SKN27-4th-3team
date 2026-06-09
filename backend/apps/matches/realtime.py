from __future__ import annotations

import logging
import re
from http.cookies import SimpleCookie
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction

from backend.apps.accounts import services as auth_services
from backend.apps.common.exceptions import ApiErrorResponseException


LOGGER = logging.getLogger(__name__)

HTTP_401_UNAUTHORIZED = 401
MATCH_PUBLIC_ID_PATTERN = re.compile(r"^match_[1-9][0-9]*$")
TURN_PUBLIC_ID_PATTERN = re.compile(r"^turn_[1-9][0-9]*$")
MATCH_GROUP_PREFIX = "match."
CHANNEL_EVENT_TYPE = "match.event"

EVENT_MATCH_SNAPSHOT = "match.snapshot"
EVENT_TURN_RESOLVED = "turn.resolved"
EVENT_LLM_TEXT_READY = "llm.text.ready"
EVENT_RESULT_READY = "result.ready"
EVENT_HEARTBEAT = "heartbeat"
EVENT_ERROR = "error"


def match_group_name(*, public_match_id: str) -> str:
    normalized_match_id = _normalize_match_id(public_match_id)
    return f"{MATCH_GROUP_PREFIX}{normalized_match_id}"


def build_match_snapshot_event(*, match: dict[str, Any]) -> dict[str, Any]:
    return {"type": EVENT_MATCH_SNAPSHOT, "match": dict(match)}


def build_turn_resolved_event(
    *,
    turn_result: dict[str, Any],
    match: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": EVENT_TURN_RESOLVED,
        "turn_result": dict(turn_result),
        "match": dict(match),
    }


def build_llm_text_ready_event(
    *,
    match_id: str,
    turn_id: str,
    llm_text: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": EVENT_LLM_TEXT_READY,
        "match_id": _normalize_match_id(match_id),
        "turn_id": _normalize_turn_id(turn_id),
        "llm_text": dict(llm_text),
    }


def build_result_ready_event(*, match: dict[str, Any]) -> dict[str, Any]:
    return {"type": EVENT_RESULT_READY, "match": dict(match)}


def build_error_event(*, code: str, message: str) -> dict[str, Any]:
    return {
        "type": EVENT_ERROR,
        "error": {
            "code": code,
            "message": message,
        },
    }


def publish_turn_resolved(
    *,
    match_id: str,
    turn_result: dict[str, Any],
    match: dict[str, Any],
) -> None:
    normalized_match_id = _normalize_match_id(match_id)
    turn_event = build_turn_resolved_event(turn_result=turn_result, match=match)

    def send_events() -> None:
        _safe_group_send(public_match_id=normalized_match_id, payload=turn_event)
        if match.get("status") == "resolved":
            _safe_group_send(
                public_match_id=normalized_match_id,
                payload=build_result_ready_event(match=match),
            )

    transaction.on_commit(send_events)


def publish_llm_text_ready(
    *,
    match_id: str,
    turn_id: str,
    llm_text: dict[str, Any],
) -> None:
    normalized_match_id = _normalize_match_id(match_id)
    event = build_llm_text_ready_event(
        match_id=normalized_match_id,
        turn_id=turn_id,
        llm_text=llm_text,
    )
    transaction.on_commit(lambda: _safe_group_send(public_match_id=normalized_match_id, payload=event))


def authenticate_scope(*, scope: dict[str, Any]) -> auth_services.SessionResult:
    return auth_services.get_current_session(raw_access_token=access_token_from_scope(scope=scope))


def access_token_from_scope(*, scope: dict[str, Any]) -> str | None:
    cookies = dict(scope.get("cookies") or {})
    if cookies:
        return cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)

    headers = scope.get("headers") or ()
    for raw_name, raw_value in headers:
        if raw_name.lower() != b"cookie":
            continue
        parsed_cookie = SimpleCookie(raw_value.decode("latin1"))
        morsel = parsed_cookie.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        return None if morsel is None else morsel.value
    return None


def current_match_snapshot(*, raw_access_token: str | None, public_match_id: str) -> dict[str, Any]:
    from backend.apps.matches import services as match_services

    result = match_services.get_match_detail(
        raw_access_token=raw_access_token,
        public_match_id=public_match_id,
    )
    return result.match


def _safe_group_send(*, public_match_id: str, payload: dict[str, Any]) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        LOGGER.warning("WebSocket channel layer is not configured")
        return

    try:
        async_to_sync(channel_layer.group_send)(
            match_group_name(public_match_id=public_match_id),
            {"type": CHANNEL_EVENT_TYPE, "payload": payload},
        )
    except Exception:
        LOGGER.exception("Failed to publish match realtime event")


def _normalize_match_id(public_match_id: str) -> str:
    if not isinstance(public_match_id, str) or not MATCH_PUBLIC_ID_PATTERN.fullmatch(
        public_match_id
    ):
        raise ValueError("public_match_id must use match_<positive integer> format")
    return public_match_id


def _normalize_turn_id(public_turn_id: str) -> str:
    if not isinstance(public_turn_id, str) or not TURN_PUBLIC_ID_PATTERN.fullmatch(public_turn_id):
        raise ValueError("public_turn_id must use turn_<positive integer> format")
    return public_turn_id


def websocket_close_code_for_error(error: ApiErrorResponseException) -> int:
    if error.status_code == HTTP_401_UNAUTHORIZED:
        return 4401
    if error.status_code == 403:
        return 4403
    if error.status_code == 404:
        return 4404
    return 4500
