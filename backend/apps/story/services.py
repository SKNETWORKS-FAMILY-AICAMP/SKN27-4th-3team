from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from backend.apps.accounts import services as auth_services
from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.story.constants import (
    APPROVED_MVP_STORY_CASE_BRIEFINGS,
    APPROVED_MVP_STORY_CASE_SUMMARIES,
)


HTTP_404_NOT_FOUND = 404
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


@dataclass(frozen=True)
class StoryCaseBriefingResult:
    case: dict[str, Any]


def list_story_cases(*, raw_access_token: str | None) -> StoryCaseListResult:
    auth_services.get_current_session(raw_access_token=raw_access_token)
    return StoryCaseListResult(cases=[dict(case) for case in APPROVED_MVP_STORY_CASE_SUMMARIES])


def get_story_case_briefing(
    *,
    raw_access_token: str | None,
    case_id: str,
) -> StoryCaseBriefingResult:
    auth_services.get_current_session(raw_access_token=raw_access_token)
    if case_id not in APPROVED_MVP_STORY_CASE_BRIEFINGS:
        raise ApiErrorResponseException(
            "CASE_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        )

    return StoryCaseBriefingResult(case=deepcopy(APPROVED_MVP_STORY_CASE_BRIEFINGS[case_id]))


def validate_story_policy_payload(payload: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(STORY_POLICY_PAYLOAD_SCHEMA).validate(dict(payload))
