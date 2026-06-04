from collections.abc import Mapping
from typing import Any

from backend.apps.matches.constants import (
    MATCH_STORAGE_SCHEMA_VERSION_FIELD,
    PARTICIPANT_TYPE_APPARITION,
    PARTICIPANT_TYPE_HUMAN,
    PARTICIPANT_TYPES,
)
from backend.apps.matches.resolution import (
    TurnResolution,
    resolve_ai_story_turn,
    validate_submission_deadline,
)


__all__ = (
    "MATCH_STORAGE_JSON_PAYLOAD_SCHEMA",
    "TurnResolution",
    "resolve_ai_story_turn",
    "validate_json_snapshot_payload",
    "validate_participant_identity",
    "validate_submission_deadline",
)


MATCH_STORAGE_JSON_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": [MATCH_STORAGE_SCHEMA_VERSION_FIELD],
    "properties": {
        MATCH_STORAGE_SCHEMA_VERSION_FIELD: {"type": "string", "minLength": 1},
    },
}


def validate_participant_identity(
    *,
    participant_type: str,
    user_id: int | None,
    apparition_id: int | None,
) -> None:
    if participant_type not in PARTICIPANT_TYPES:
        raise ValueError(f"unknown participant_type: {participant_type}")

    if participant_type == PARTICIPANT_TYPE_HUMAN:
        if user_id is None:
            raise ValueError("human participant requires user_id")
        if apparition_id is not None:
            raise ValueError("human participant cannot have apparition_id")
        return

    if participant_type == PARTICIPANT_TYPE_APPARITION:
        if apparition_id is None:
            raise ValueError("apparition participant requires apparition_id")
        if user_id is not None:
            raise ValueError("apparition participant cannot have user_id")


def validate_json_snapshot_payload(payload: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(MATCH_STORAGE_JSON_PAYLOAD_SCHEMA).validate(dict(payload))
