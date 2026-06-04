from collections.abc import Mapping
from typing import Any


STORY_POLICY_SCHEMA_VERSION_FIELD = "schema_version"

STORY_POLICY_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": [STORY_POLICY_SCHEMA_VERSION_FIELD],
    "properties": {
        STORY_POLICY_SCHEMA_VERSION_FIELD: {"type": "string", "minLength": 1},
    },
}


def validate_story_policy_payload(payload: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(STORY_POLICY_PAYLOAD_SCHEMA).validate(dict(payload))
