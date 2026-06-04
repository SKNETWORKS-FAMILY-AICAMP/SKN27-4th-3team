from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from backend.apps.accounts import services as auth_services
from backend.apps.story.constants import APPROVED_MVP_STORY_CASE_SUMMARIES


STORY_POLICY_SCHEMA_VERSION_FIELD = "schema_version"

STORY_POLICY_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": [STORY_POLICY_SCHEMA_VERSION_FIELD],
    "properties": {
        STORY_POLICY_SCHEMA_VERSION_FIELD: {"type": "string", "minLength": 1},
    },
}


@dataclass(frozen=True)
class StoryCaseListResult:
    cases: list[dict[str, Any]]


def list_story_cases(*, raw_access_token: str | None) -> StoryCaseListResult:
    auth_services.get_current_session(raw_access_token=raw_access_token)
    return StoryCaseListResult(cases=[dict(case) for case in APPROVED_MVP_STORY_CASE_SUMMARIES])


def validate_story_policy_payload(payload: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(STORY_POLICY_PAYLOAD_SCHEMA).validate(dict(payload))
