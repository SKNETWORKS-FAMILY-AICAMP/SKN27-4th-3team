from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta, timezone as datetime_timezone
from math import ceil
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone

from backend.apps.accounts import services as auth_services
from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.game_rules.matchups import ACTION_CODES
from backend.apps.game_rules.resources import (
    MAX_CURSE_MARKS,
    MAX_FALSE_CLUES,
    MAX_RITUAL_POWER,
    MAX_SANITY,
    MAX_SHIELD,
    MAX_SUSPICION,
    MAX_TRUE_NAME_FRAGMENTS,
    ResourceState,
)
from backend.apps.matches.constants import (
    MATCH_MODE_AI_STORY,
    MATCH_STATUS_ACTIVE,
    PARTICIPANT_TYPE_APPARITION,
    PARTICIPANT_TYPE_HUMAN,
    TURN_STATUS_AWAITING_PLAYER,
)
from backend.apps.matches.models import Match, MatchParticipant, MatchStartRequest, Turn
from backend.apps.story.constants import (
    APPROVED_MVP_STORY_CASE_BRIEFINGS,
    APPROVED_MVP_STORY_CASE_SUMMARIES,
    MIRROR_GUEST_CASE_ID,
    MIRROR_GUEST_TITLE,
    MVP_STORY_MAX_TURNS,
)


HTTP_401_UNAUTHORIZED = 401
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
DEFAULT_TURN_SECONDS = 25
MIRROR_GUEST_APPARITION_ID = 1
PLAYER_SIDE = "player"
OPPONENT_SIDE = "opponent"
SEAL_DISABLED_REASON_TRUE_NAME_FRAGMENTS = "TRUE_NAME_FRAGMENTS_NOT_ENOUGH"
STORY_POLICY_SCHEMA_VERSION_FIELD = "schema_version"

ACTION_AVAILABILITY_DEFINITIONS = (
    {
        "code": "curse",
        "display_name": "저주",
        "ritual_power_cost": 2,
        "requires_info_target": False,
    },
    {
        "code": "guard",
        "display_name": "수호",
        "ritual_power_cost": 1,
        "requires_info_target": False,
    },
    {
        "code": "insight",
        "display_name": "간파",
        "ritual_power_cost": 1,
        "requires_info_target": True,
    },
    {
        "code": "trick",
        "display_name": "속임수",
        "ritual_power_cost": 1,
        "requires_info_target": False,
    },
    {
        "code": "silence",
        "display_name": "침묵",
        "ritual_power_cost": 0,
        "requires_info_target": False,
    },
    {
        "code": "contract",
        "display_name": "계약",
        "ritual_power_cost": 3,
        "requires_info_target": True,
    },
    {
        "code": "seal",
        "display_name": "봉인",
        "ritual_power_cost": 2,
        "requires_info_target": True,
    },
)

if tuple(action["code"] for action in ACTION_AVAILABILITY_DEFINITIONS) != ACTION_CODES:
    raise RuntimeError("story action availability definitions must match approved action codes")

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


@dataclass(frozen=True)
class StoryCaseMatchStartResult:
    match: dict[str, Any]


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


def start_story_case_match(
    *,
    raw_access_token: str | None,
    case_id: str,
    client_request_id: UUID,
) -> StoryCaseMatchStartResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)

    try:
        with transaction.atomic():
            return _start_story_case_match_in_transaction(
                session=session,
                user_id=user_id,
                case_id=case_id,
                client_request_id=client_request_id,
            )
    except IntegrityError as exc:
        try:
            with transaction.atomic():
                return _existing_match_start_result(
                    session=session,
                    user_id=user_id,
                    case_id=case_id,
                    client_request_id=client_request_id,
                )
        except MatchStartRequest.DoesNotExist:
            raise exc


def validate_story_policy_payload(payload: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(STORY_POLICY_PAYLOAD_SCHEMA).validate(dict(payload))


def _start_story_case_match_in_transaction(
    *,
    session: auth_services.SessionResult,
    user_id: int,
    case_id: str,
    client_request_id: UUID,
) -> StoryCaseMatchStartResult:
    existing_start_request = (
        MatchStartRequest.objects.select_for_update()
        .filter(user_id=user_id, client_request_id=client_request_id)
        .first()
    )
    if existing_start_request is not None:
        return _match_start_result_from_existing_request(
            session=session,
            case_id=case_id,
            start_request=existing_start_request,
        )

    _assert_supported_story_case(case_id=case_id)

    now = timezone.now()
    initial_state = ResourceState.initial()
    match = Match.objects.create(
        mode=MATCH_MODE_AI_STORY,
        status=MATCH_STATUS_ACTIVE,
        started_at=now,
    )
    human_participant = MatchParticipant.objects.create(
        match_id=match.id,
        participant_type=PARTICIPANT_TYPE_HUMAN,
        user_id=user_id,
        apparition_id=None,
        side=PLAYER_SIDE,
        sanity=initial_state.sanity,
        ritual_power=initial_state.ritual_power,
        curse_marks=initial_state.curse_marks,
        secret_exposure=initial_state.secret_exposure,
        true_name_fragments=initial_state.true_name_fragments,
        incomplete_true_name_fragments=initial_state.incomplete_true_name_fragments,
        false_clues=initial_state.false_clues,
        suspicion=initial_state.suspicion,
        shield=initial_state.shield,
        timeout_count=0,
    )
    apparition_participant = MatchParticipant.objects.create(
        match_id=match.id,
        participant_type=PARTICIPANT_TYPE_APPARITION,
        user_id=None,
        apparition_id=MIRROR_GUEST_APPARITION_ID,
        side=OPPONENT_SIDE,
        sanity=initial_state.sanity,
        ritual_power=initial_state.ritual_power,
        curse_marks=initial_state.curse_marks,
        secret_exposure=initial_state.secret_exposure,
        true_name_fragments=initial_state.true_name_fragments,
        incomplete_true_name_fragments=initial_state.incomplete_true_name_fragments,
        false_clues=initial_state.false_clues,
        suspicion=initial_state.suspicion,
        shield=initial_state.shield,
        timeout_count=0,
    )
    turn = Turn.objects.create(
        match_id=match.id,
        turn_number=1,
        status=TURN_STATUS_AWAITING_PLAYER,
        started_at=now,
        deadline_at=now + timedelta(seconds=DEFAULT_TURN_SECONDS),
    )
    MatchStartRequest.objects.create(
        user_id=user_id,
        client_request_id=client_request_id,
        case_id=case_id,
        match_id=match.id,
    )

    return StoryCaseMatchStartResult(
        match=format_match_state(
            session=session,
            match=match,
            turn=turn,
            human_participant=human_participant,
            apparition_participant=apparition_participant,
            now=now,
        )
    )


def _existing_match_start_result(
    *,
    session: auth_services.SessionResult,
    user_id: int,
    case_id: str,
    client_request_id: UUID,
) -> StoryCaseMatchStartResult:
    start_request = MatchStartRequest.objects.select_for_update().get(
        user_id=user_id,
        client_request_id=client_request_id,
    )
    return _match_start_result_from_existing_request(
        session=session,
        case_id=case_id,
        start_request=start_request,
    )


def _match_start_result_from_existing_request(
    *,
    session: auth_services.SessionResult,
    case_id: str,
    start_request: MatchStartRequest,
) -> StoryCaseMatchStartResult:
    if start_request.case_id != case_id:
        raise ApiErrorResponseException(
            "IDEMPOTENCY_CONFLICT",
            status_code=HTTP_409_CONFLICT,
        )

    _assert_supported_story_case(case_id=case_id)

    match = _get_match(match_id=start_request.match_id)
    return StoryCaseMatchStartResult(
        match=format_match_state(
            session=session,
            match=match,
            turn=_get_initial_turn(match_id=match.id),
            human_participant=_get_participant(
                match_id=match.id,
                participant_type=PARTICIPANT_TYPE_HUMAN,
            ),
            apparition_participant=_get_participant(
                match_id=match.id,
                participant_type=PARTICIPANT_TYPE_APPARITION,
            ),
            now=timezone.now(),
        )
    )


def format_match_state(
    *,
    session: auth_services.SessionResult,
    match: Match,
    turn: Turn,
    human_participant: MatchParticipant,
    apparition_participant: MatchParticipant,
    now,
) -> dict[str, Any]:
    player_state = _resource_state_from_human_participant(human_participant)
    return {
        "match_id": _public_id(prefix="match", value=match.id),
        "mode": match.mode,
        "status": match.status,
        "case": {
            "case_id": MIRROR_GUEST_CASE_ID,
            "title": MIRROR_GUEST_TITLE,
        },
        "turn": {
            "turn_id": _public_id(prefix="turn", value=turn.id),
            "turn_number": turn.turn_number,
            "max_turns": MVP_STORY_MAX_TURNS,
            "status": turn.status,
            "deadline_at": _iso_utc(turn.deadline_at),
            "remaining_seconds": _remaining_seconds(deadline_at=turn.deadline_at, now=now),
            "resolved_at": _iso_utc(turn.resolved_at),
        },
        "player": {
            "participant_id": _public_id(prefix="participant", value=human_participant.id),
            "participant_type": PARTICIPANT_TYPE_HUMAN,
            "display_name": _player_display_name(session=session),
            "resources": _resource_payload(
                player_state,
                timeout_count=human_participant.timeout_count,
            ),
        },
        "opponent": {
            "participant_id": _public_id(prefix="participant", value=apparition_participant.id),
            "participant_type": PARTICIPANT_TYPE_APPARITION,
            "display_name": MIRROR_GUEST_TITLE,
            "public_state": {
                "true_name_fragments_revealed": player_state.true_name_fragments,
                "true_name_fragments_required": MAX_TRUE_NAME_FRAGMENTS,
                "seal_available": player_state.true_name_fragments >= MAX_TRUE_NAME_FRAGMENTS,
            },
        },
        "available_actions": _available_actions(player_state),
        "clues": [],
        "recent_public_logs": [],
    }


def _resource_state_from_human_participant(human_participant: MatchParticipant) -> ResourceState:
    return ResourceState.initial().replace(
        sanity=human_participant.sanity,
        ritual_power=human_participant.ritual_power,
        curse_marks=human_participant.curse_marks,
        secret_exposure=human_participant.secret_exposure,
        true_name_fragments=human_participant.true_name_fragments,
        incomplete_true_name_fragments=human_participant.incomplete_true_name_fragments,
        false_clues=human_participant.false_clues,
        suspicion=human_participant.suspicion,
        shield=human_participant.shield,
    )


def _resource_payload(state: ResourceState, *, timeout_count: int) -> dict[str, int]:
    return {
        "sanity": state.sanity,
        "sanity_max": MAX_SANITY,
        "ritual_power": state.ritual_power,
        "ritual_power_max": MAX_RITUAL_POWER,
        "curse_marks": state.curse_marks,
        "curse_marks_max": MAX_CURSE_MARKS,
        "true_name_fragments": state.true_name_fragments,
        "true_name_fragments_required": MAX_TRUE_NAME_FRAGMENTS,
        "incomplete_true_name_fragments": state.incomplete_true_name_fragments,
        "false_clues": state.false_clues,
        "false_clues_max": MAX_FALSE_CLUES,
        "suspicion": state.suspicion,
        "suspicion_max": MAX_SUSPICION,
        "shield": state.shield,
        "shield_max": MAX_SHIELD,
        "timeout_count": timeout_count,
    }


def _available_actions(state: ResourceState) -> list[dict[str, Any]]:
    seal_enabled = state.true_name_fragments >= MAX_TRUE_NAME_FRAGMENTS
    actions = []
    for definition in ACTION_AVAILABILITY_DEFINITIONS:
        is_seal = definition["code"] == "seal"
        enabled = not is_seal or seal_enabled
        actions.append(
            {
                "code": definition["code"],
                "display_name": definition["display_name"],
                "ritual_power_cost": definition["ritual_power_cost"],
                "enabled": enabled,
                "disabled_reason": (
                    None if enabled else SEAL_DISABLED_REASON_TRUE_NAME_FRAGMENTS
                ),
                "requires_info_target": definition["requires_info_target"],
            }
        )
    return actions


def _get_match(*, match_id: int) -> Match:
    try:
        return Match.objects.get(id=match_id)
    except Match.DoesNotExist as exc:
        raise ApiErrorResponseException(
            "MATCH_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        ) from exc


def _get_initial_turn(*, match_id: int) -> Turn:
    turn = Turn.objects.filter(match_id=match_id, turn_number=1).order_by("id").first()
    if turn is None:
        raise ApiErrorResponseException(
            "MATCH_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        )
    return turn


def _get_participant(*, match_id: int, participant_type: str) -> MatchParticipant:
    participant = (
        MatchParticipant.objects.filter(
            match_id=match_id,
            participant_type=participant_type,
        )
        .order_by("id")
        .first()
    )
    if participant is None:
        raise ApiErrorResponseException(
            "MATCH_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        )
    return participant


def _assert_supported_story_case(*, case_id: str) -> None:
    if case_id != MIRROR_GUEST_CASE_ID:
        raise ApiErrorResponseException(
            "CASE_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        )


def _session_user_id(*, session: auth_services.SessionResult) -> int:
    try:
        user_id = int(session.user["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiErrorResponseException(
            "SESSION_EXPIRED",
            status_code=HTTP_401_UNAUTHORIZED,
        ) from exc

    if user_id <= 0:
        raise ApiErrorResponseException(
            "SESSION_EXPIRED",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    return user_id


def _player_display_name(*, session: auth_services.SessionResult) -> str:
    nickname = session.profile.get("nickname")
    if isinstance(nickname, str) and nickname.strip():
        return nickname
    return str(session.user.get("email") or session.user["id"])


def _public_id(*, prefix: str, value: int) -> str:
    return f"{prefix}_{value}"


def _remaining_seconds(*, deadline_at, now) -> int:
    return max(0, ceil((deadline_at - now).total_seconds()))


def _iso_utc(value) -> str | None:
    if value is None:
        return None
    return value.astimezone(datetime_timezone.utc).isoformat().replace("+00:00", "Z")
