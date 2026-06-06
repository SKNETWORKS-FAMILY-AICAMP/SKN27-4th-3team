from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone

from backend.apps.accounts import services as auth_services
from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.game_rules.matchups import (
    ACTION_CODES,
    build_revealed_action_candidates,
)
from backend.apps.game_rules.outcomes import (
    OutcomeReason,
    OutcomeStatus,
    determine_ai_story_outcome,
)
from backend.apps.game_rules.policies import MIRROR_GUEST_BASE_WEIGHTS
from backend.apps.game_rules.resources import (
    MAX_CURSE_MARKS,
    MAX_FALSE_CLUES,
    MAX_RITUAL_POWER,
    MAX_SANITY,
    MAX_SHIELD,
    MAX_SUSPICION,
    MAX_TRUE_NAME_FRAGMENTS,
    ResourceState,
    add_false_clue,
    add_incomplete_true_name_fragment,
    add_ritual_power,
    add_shield,
    add_suspicion,
    remove_false_clue,
)
from backend.apps.matches.constants import (
    CLUE_TRUTH_STATE_FALSE_REVEALED,
    CLUE_TRUTH_STATE_UNKNOWN,
    MATCH_MODE_AI_STORY,
    MATCH_STORAGE_SCHEMA_VERSION_FIELD,
    MATCH_STATUS_ACTIVE,
    MATCH_STATUS_RESOLVED,
    PARTICIPANT_TYPE_APPARITION,
    PARTICIPANT_TYPE_HUMAN,
    PARTICIPANT_TYPES,
    TURN_STATUS_AWAITING_PLAYER,
)
from backend.apps.matches.resolution import (
    TurnResolution,
    resolve_ai_story_turn,
    validate_submission_deadline,
)
from backend.apps.matches.models import (
    ActionSubmission,
    Match,
    MatchFalseClueOwnership,
    MatchParticipant,
    MatchStartRequest,
    MatchTrueNameFragmentOwnership,
    Turn,
    TurnResult,
)
from backend.apps.llm import services as llm_services
from backend.apps.story.constants import (
    APPROVED_MIRROR_GUEST_FALSE_CLUES,
    APPROVED_MIRROR_GUEST_INFO_TARGET_KEYS,
    APPROVED_MIRROR_GUEST_RESULT_TEXT_BY_REASON,
    APPROVED_MIRROR_GUEST_TRUE_NAME_FRAGMENTS,
    MIRROR_GUEST_CASE_ID,
    MIRROR_GUEST_TITLE,
    MVP_STORY_MAX_TURNS,
)


__all__ = (
    "MATCH_STORAGE_JSON_PAYLOAD_SCHEMA",
    "MatchDetailResult",
    "MatchResultResult",
    "TurnSubmitResult",
    "apply_deterministic_false_clue_detection",
    "TurnResolution",
    "get_match_detail",
    "get_match_result",
    "parse_public_match_id",
    "resolve_ai_story_turn",
    "submit_match_turn",
    "validate_json_snapshot_payload",
    "validate_participant_identity",
    "validate_submission_deadline",
)

HTTP_401_UNAUTHORIZED = 401
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
MATCH_PUBLIC_ID_PREFIX = "match_"
TURN_RESULT_SCHEMA_VERSION = "turn_result.v1"
NEXT_TURN_SECONDS = 25
INFORMATION_ACTION_CODES = frozenset({"insight", "contract", "seal"})
TRUE_NAME_REVEAL_ACTION_CODES = frozenset({"insight", "contract"})
SEAL_ACTION_CODE = "seal"
FALSE_CLUE_EFFECT_CODE = "false_clue:+1"
FALSE_CLUE_DETECTION_EFFECT_CODE = "false_clue_detection_check"
TRUE_NAME_CANDIDATE_EFFECT_CODE = "true_name_fragment_candidate:+1_or_secret_exposure:+1"
ACTOR_INCOMPLETE_TRUE_NAME_EFFECT_CODE = "actor_incomplete_true_name_fragment:+1"
OUTCOME_RESULT_BY_STATUS = {
    OutcomeStatus.IN_PROGRESS: "unresolved",
    OutcomeStatus.WIN: "player_win",
    OutcomeStatus.LOSS: "player_loss",
}
MATCH_RESULT_PLAYER_WIN = "player_win"
MATCH_RESULT_PLAYER_LOSS = "player_loss"
RESULT_REASON_UNRESOLVED = "unresolved"
ACTION_DISPLAY_NAMES = {
    "curse": "저주",
    "guard": "수호",
    "insight": "간파",
    "trick": "속임수",
    "silence": "침묵",
    "contract": "계약",
    "seal": "봉인",
}
ACTION_RITUAL_POWER_COSTS = {
    "curse": 2,
    "guard": 1,
    "insight": 1,
    "trick": 1,
    "silence": 0,
    "contract": 3,
    "seal": 2,
}

MATCH_STORAGE_JSON_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": [MATCH_STORAGE_SCHEMA_VERSION_FIELD],
    "properties": {
        MATCH_STORAGE_SCHEMA_VERSION_FIELD: {"type": "string", "minLength": 1},
    },
}


@dataclass(frozen=True)
class MatchDetailResult:
    match: dict[str, Any]


@dataclass(frozen=True)
class MatchResultResult:
    result: dict[str, Any]


@dataclass(frozen=True)
class TurnSubmitResult:
    turn_result: dict[str, Any]
    match: dict[str, Any]


@dataclass(frozen=True)
class TurnEffectResult:
    player_state_after: ResourceState
    state_delta: dict[str, Any]
    clue_delta: dict[str, Any]
    match_outcome: Any


def get_match_detail(
    *,
    raw_access_token: str | None,
    public_match_id: str,
) -> MatchDetailResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)
    match_id = parse_public_match_id(public_match_id)
    match = _get_match(match_id=match_id)
    start_request = (
        MatchStartRequest.objects.filter(user_id=user_id, match_id=match_id)
        .order_by("id")
        .first()
    )
    if start_request is None:
        raise ApiErrorResponseException(
            "MATCH_ACCESS_DENIED",
            status_code=HTTP_403_FORBIDDEN,
        )

    from backend.apps.story.services import format_match_state

    return MatchDetailResult(
        match=format_match_state(
            session=session,
            match=match,
            turn=_get_current_turn(match_id=match_id),
            human_participant=_get_participant(
                match_id=match_id,
                participant_type=PARTICIPANT_TYPE_HUMAN,
            ),
            apparition_participant=_get_participant(
                match_id=match_id,
                participant_type=PARTICIPANT_TYPE_APPARITION,
            ),
            now=timezone.now(),
        )
    )


def get_match_result(
    *,
    raw_access_token: str | None,
    public_match_id: str,
) -> MatchResultResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)
    match_id = parse_public_match_id(public_match_id)
    match = _get_match(match_id=match_id)
    _assert_match_access(user_id=user_id, match_id=match_id)

    if match.status != MATCH_STATUS_RESOLVED:
        raise ApiErrorResponseException(
            "MATCH_NOT_RESOLVED",
            status_code=HTTP_409_CONFLICT,
        )

    human_participant = _get_participant(
        match_id=match_id,
        participant_type=PARTICIPANT_TYPE_HUMAN,
    )
    _get_participant(
        match_id=match_id,
        participant_type=PARTICIPANT_TYPE_APPARITION,
    )
    last_turn = _get_current_turn(match_id=match_id)
    result_reason = _match_result_reason(
        match=match,
        human_participant=human_participant,
        last_turn=last_turn,
    )

    return MatchResultResult(
        result={
            "match_id": _public_id(prefix="match", value=match.id),
            "result": _match_result(match=match, human_participant=human_participant),
            "result_reason": result_reason,
            "case": {
                "case_id": MIRROR_GUEST_CASE_ID,
                "title": MIRROR_GUEST_TITLE,
            },
            "final_resources": _final_resource_payload(human_participant),
            "turn_logs": _get_match_turn_logs(match_id=match_id),
            "story_result_text": list(
                APPROVED_MIRROR_GUEST_RESULT_TEXT_BY_REASON.get(
                    result_reason,
                    APPROVED_MIRROR_GUEST_RESULT_TEXT_BY_REASON[RESULT_REASON_UNRESOLVED],
                )
            ),
            "style_summary": _style_summary_payload(session=session),
            "llm_summary": llm_services.build_disabled_llm_summary(),
        }
    )


def submit_match_turn(
    *,
    raw_access_token: str | None,
    public_match_id: str,
    action_code: str,
    info_target_key: str | None,
    client_nonce: UUID,
) -> TurnSubmitResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)
    match_id = parse_public_match_id(public_match_id)

    with transaction.atomic():
        match = _get_match(match_id=match_id)
        if match.status != MATCH_STATUS_ACTIVE:
            raise ApiErrorResponseException(
                "MATCH_ALREADY_FINISHED",
                status_code=HTTP_409_CONFLICT,
            )

        _assert_match_access(user_id=user_id, match_id=match_id)
        human_participant = _get_participant(
            match_id=match_id,
            participant_type=PARTICIPANT_TYPE_HUMAN,
        )
        apparition_participant = _get_participant(
            match_id=match_id,
            participant_type=PARTICIPANT_TYPE_APPARITION,
        )
        turn = _get_current_turn(match_id=match_id)
        if turn.status != TURN_STATUS_AWAITING_PLAYER:
            raise ApiErrorResponseException(
                "TURN_ALREADY_SUBMITTED",
                status_code=HTTP_409_CONFLICT,
            )

        _validate_turn_submit_request(
            action_code=action_code,
            info_target_key=info_target_key,
            human_participant=human_participant,
        )

        now = timezone.now()
        deadline_error = validate_submission_deadline(
            deadline_at=turn.deadline_at,
            submitted_at=now,
        )
        if deadline_error is not None:
            raise ApiErrorResponseException(
                deadline_error.code,
                status_code=HTTP_400_BAD_REQUEST,
            )

        if ActionSubmission.objects.filter(
            turn_id=turn.id,
            participant_id=human_participant.id,
        ).exists():
            raise ApiErrorResponseException(
                "TURN_ALREADY_SUBMITTED",
                status_code=HTTP_409_CONFLICT,
            )

        opponent_action_code = _choose_apparition_action(
            match_id=match_id,
            human_participant=human_participant,
        )
        try:
            submission = ActionSubmission.objects.create(
                turn_id=turn.id,
                participant_id=human_participant.id,
                action_code=action_code,
                info_target_key=info_target_key,
                submitted_at=now,
                client_nonce=client_nonce,
            )
        except IntegrityError as exc:
            raise ApiErrorResponseException(
                "TURN_ALREADY_SUBMITTED",
                status_code=HTTP_409_CONFLICT,
            ) from exc

        player_state_before = _resource_state_from_participant(human_participant)
        resolution = resolve_ai_story_turn(
            turn_id=_public_id(prefix="turn", value=turn.id),
            turn_number=turn.turn_number,
            deadline_at=turn.deadline_at,
            server_time=now,
            player_action_code=action_code,
            opponent_action_code=opponent_action_code,
            player_timeout_count=human_participant.timeout_count,
            player_state=player_state_before,
            seal_condition_met=(
                human_participant.true_name_fragments >= MAX_TRUE_NAME_FRAGMENTS
            ),
            curse_marks_loss_triggered=False,
        )

        effect_result = _apply_turn_effects(
            match=match,
            turn=turn,
            submission=submission,
            resolution=resolution,
            human_participant=human_participant,
            apparition_participant=apparition_participant,
            info_target_key=info_target_key,
        )
        resolution = replace(resolution, match_outcome=effect_result.match_outcome)

        turn.status = resolution.turn_status
        turn.resolved_at = now
        turn.save(update_fields=("status", "resolved_at"))

        next_turn = _finish_match_or_create_next_turn(
            match=match,
            turn=turn,
            human_participant=human_participant,
            resolution=resolution,
            now=now,
        )
        turn_result = _turn_result_payload(
            resolution=resolution,
            info_target_key=info_target_key,
            state_delta=effect_result.state_delta,
            clue_delta=effect_result.clue_delta,
        )
        TurnResult.objects.create(
            turn_id=turn.id,
            result_json={
                "schema_version": TURN_RESULT_SCHEMA_VERSION,
                "turn_result": turn_result,
            },
            public_log_json={
                "schema_version": TURN_RESULT_SCHEMA_VERSION,
                "logs": [turn_result["public_log"]],
            },
            private_log_json={
                "schema_version": TURN_RESULT_SCHEMA_VERSION,
                "effect_codes": list(resolution.effect_codes),
            },
            schema_version=TURN_RESULT_SCHEMA_VERSION,
        )

        from backend.apps.story.services import format_match_state

        return TurnSubmitResult(
            turn_result=turn_result,
            match=format_match_state(
                session=session,
                match=match,
                turn=next_turn,
                human_participant=human_participant,
                apparition_participant=apparition_participant,
                now=now,
            ),
        )


def _match_result(*, match: Match, human_participant: MatchParticipant) -> str:
    if match.winner_participant_id == human_participant.id:
        return MATCH_RESULT_PLAYER_WIN

    return MATCH_RESULT_PLAYER_LOSS


def _match_result_reason(
    *,
    match: Match,
    human_participant: MatchParticipant,
    last_turn: Turn,
) -> str:
    if match.winner_participant_id == human_participant.id:
        return OutcomeReason.SEAL_SUCCESS.value

    final_state = _resource_state_from_participant(human_participant)
    outcome = determine_ai_story_outcome(
        seal_succeeded=False,
        player_sanity=final_state.sanity,
        curse_marks_loss_triggered=_curse_marks_loss_triggered(final_state),
        turn_number=last_turn.turn_number,
    )
    if outcome.reason == OutcomeReason.NONE:
        return RESULT_REASON_UNRESOLVED

    return outcome.reason.value


def _final_resource_payload(participant: MatchParticipant) -> dict[str, int]:
    return {
        "sanity": participant.sanity,
        "sanity_max": MAX_SANITY,
        "ritual_power": participant.ritual_power,
        "ritual_power_max": MAX_RITUAL_POWER,
        "curse_marks": participant.curse_marks,
        "curse_marks_max": MAX_CURSE_MARKS,
        "true_name_fragments": participant.true_name_fragments,
        "true_name_fragments_required": MAX_TRUE_NAME_FRAGMENTS,
        "incomplete_true_name_fragments": participant.incomplete_true_name_fragments,
        "false_clues": participant.false_clues,
        "false_clues_max": MAX_FALSE_CLUES,
        "suspicion": participant.suspicion,
        "suspicion_max": MAX_SUSPICION,
        "shield": participant.shield,
        "shield_max": MAX_SHIELD,
        "timeout_count": participant.timeout_count,
    }


def _get_match_turn_logs(*, match_id: int) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    turn_ids = Turn.objects.filter(match_id=match_id).values("id")
    for turn_result in TurnResult.objects.filter(turn_id__in=turn_ids).order_by(
        "turn_id",
        "id",
    ):
        raw_logs = turn_result.public_log_json.get("logs", ())
        for raw_log in raw_logs:
            public_log = _public_log_payload(raw_log)
            if public_log is not None:
                logs.append(public_log)

    return logs


def _public_log_payload(raw_log: Any) -> dict[str, Any] | None:
    if not isinstance(raw_log, Mapping):
        return None

    turn_number = raw_log.get("turn_number")
    text = raw_log.get("text")
    if not isinstance(turn_number, int) or not isinstance(text, str):
        return None

    return {
        "turn_number": turn_number,
        "text": text,
        "log_key": raw_log.get("log_key"),
    }


def _style_summary_payload(*, session: auth_services.SessionResult) -> dict[str, Any]:
    style_summary = session.profile.get("style_summary")
    if isinstance(style_summary, Mapping):
        return dict(style_summary)

    return {
        "label": None,
        "display_text": None,
        "metrics": {field: 0.0 for field in auth_services.STYLE_METRIC_FIELDS},
        "updated_at": None,
    }


def parse_public_match_id(public_match_id: str) -> int:
    if not isinstance(public_match_id, str):
        raise _match_not_found()
    if not public_match_id.startswith(MATCH_PUBLIC_ID_PREFIX):
        raise _match_not_found()

    raw_id = public_match_id.removeprefix(MATCH_PUBLIC_ID_PREFIX)
    try:
        match_id = int(raw_id)
    except ValueError as exc:
        raise _match_not_found() from exc

    if match_id <= 0:
        raise _match_not_found()
    return match_id


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


def apply_deterministic_false_clue_detection(
    *,
    match_id: int,
    participant_id: int,
    turn_number: int,
) -> dict[str, list[dict[str, Any]] | list[str]]:
    false_clue = (
        MatchFalseClueOwnership.objects.filter(
            match_id=match_id,
            participant_id=participant_id,
            truth_state=CLUE_TRUTH_STATE_UNKNOWN,
        )
        .order_by("id")
        .first()
    )
    if false_clue is None:
        return {"added": [], "removed_clue_ids": [], "revealed": []}

    false_clue.truth_state = CLUE_TRUTH_STATE_FALSE_REVEALED
    false_clue.save(update_fields=("truth_state",))
    clue = _false_clue_payload(
        false_clue_id=false_clue.false_clue_id,
        truth_state=CLUE_TRUTH_STATE_FALSE_REVEALED,
        source_turn_number=turn_number,
    )
    return {
        "added": [],
        "removed_clue_ids": [clue["clue_id"]],
        "revealed": [clue],
    }


def _validate_turn_submit_request(
    *,
    action_code: str,
    info_target_key: str | None,
    human_participant: MatchParticipant,
) -> None:
    if action_code not in ACTION_CODES:
        raise ApiErrorResponseException(
            "ACTION_NOT_AVAILABLE",
            status_code=HTTP_400_BAD_REQUEST,
        )
    if action_code in INFORMATION_ACTION_CODES and not info_target_key:
        raise ApiErrorResponseException(
            "INFO_TARGET_REQUIRED",
            status_code=HTTP_400_BAD_REQUEST,
        )
    if (
        info_target_key is not None
        and info_target_key not in APPROVED_MIRROR_GUEST_INFO_TARGET_KEYS
    ):
        raise ApiErrorResponseException(
            "VALIDATION_ERROR",
            status_code=HTTP_400_BAD_REQUEST,
            details={"info_target_key": ["Unknown info target."]},
        )
    if (
        action_code == SEAL_ACTION_CODE
        and human_participant.true_name_fragments < MAX_TRUE_NAME_FRAGMENTS
    ):
        raise ApiErrorResponseException(
            "ACTION_NOT_AVAILABLE",
            status_code=HTTP_400_BAD_REQUEST,
        )
    if human_participant.ritual_power < ACTION_RITUAL_POWER_COSTS[action_code]:
        raise ApiErrorResponseException(
            "INSUFFICIENT_RITUAL_POWER",
            status_code=HTTP_400_BAD_REQUEST,
        )


def _choose_apparition_action(*, match_id: int, human_participant: MatchParticipant) -> str:
    recent_player_actions = tuple(
        ActionSubmission.objects.filter(participant_id=human_participant.id)
        .order_by("id")
        .values_list("action_code", flat=True)
    )
    recent_apparition_actions = tuple(
        action
        for action in (
            result.result_json.get("turn_result", {})
            .get("opponent_action", {})
            .get("code")
            for result in TurnResult.objects.filter(
                turn_id__in=Turn.objects.filter(match_id=match_id).values("id")
            ).order_by("id")
        )
        if action in ACTION_CODES
    )
    candidates = build_revealed_action_candidates(
        base_weights=MIRROR_GUEST_BASE_WEIGHTS,
        recent_player_actions=recent_player_actions,
        recent_apparition_actions=recent_apparition_actions,
        completed_turns=len(recent_player_actions),
        timeout_count=human_participant.timeout_count,
    )
    return candidates[0]


def _apply_turn_effects(
    *,
    match: Match,
    turn: Turn,
    submission: ActionSubmission,
    resolution: TurnResolution,
    human_participant: MatchParticipant,
    apparition_participant: MatchParticipant,
    info_target_key: str | None,
) -> TurnEffectResult:
    state_before = _resource_state_from_participant(human_participant)
    state_after = _consume_action_cost(
        state_before,
        action_code=resolution.player_action_code,
    )
    apparition_state = _resource_state_from_participant(apparition_participant)
    clue_delta = {"added": [], "removed_clue_ids": [], "revealed": []}

    for effect_code in resolution.effect_codes:
        state_after, apparition_state = _apply_resource_effect_code(
            effect_code=effect_code,
            player_state=state_after,
            apparition_state=apparition_state,
        )

    if FALSE_CLUE_EFFECT_CODE in resolution.effect_codes:
        added_false_clue = _add_false_clue_from_trigger(
            match=match,
            turn=turn,
            participant=human_participant,
            info_target_key=info_target_key,
            current_true_name_fragments=state_after.true_name_fragments,
        )
        if added_false_clue is not None:
            state_after = add_false_clue(state_after)
            clue_delta["added"].append(added_false_clue)

    if FALSE_CLUE_DETECTION_EFFECT_CODE in resolution.effect_codes:
        detection_delta = apply_deterministic_false_clue_detection(
            match_id=match.id,
            participant_id=human_participant.id,
            turn_number=turn.turn_number,
        )
        if detection_delta["revealed"]:
            state_after = remove_false_clue(state_after)
        _merge_clue_delta(clue_delta, detection_delta)

    if _should_add_true_name_fragment(
        resolution=resolution,
        info_target_key=info_target_key,
        state=state_after,
    ):
        added_true_fragment = _add_true_name_fragment_from_reveal(
            match=match,
            turn=turn,
            participant=human_participant,
            action_code=resolution.player_action_code,
            info_target_key=info_target_key,
            current_true_name_fragments=state_after.true_name_fragments,
        )
        if added_true_fragment is not None:
            state_after = state_after.replace(
                true_name_fragments=min(
                    state_after.true_name_fragments + 1,
                    MAX_TRUE_NAME_FRAGMENTS,
                ),
                incomplete_true_name_fragments=0,
            )
            clue_delta["added"].append(added_true_fragment)
        elif ACTOR_INCOMPLETE_TRUE_NAME_EFFECT_CODE in resolution.effect_codes:
            state_after = add_incomplete_true_name_fragment(state_after)

    _persist_resource_state(human_participant, state_after)
    _persist_resource_state(apparition_participant, apparition_state)
    human_participant.timeout_count = resolution.player_timeout_count
    human_participant.save(update_fields=("timeout_count",))
    match_outcome = determine_ai_story_outcome(
        seal_succeeded=resolution.seal_succeeded,
        player_sanity=state_after.sanity,
        curse_marks_loss_triggered=_curse_marks_loss_triggered(state_after),
        turn_number=turn.turn_number,
    )
    return TurnEffectResult(
        player_state_after=state_after,
        state_delta=_state_delta(before=state_before, after=state_after),
        clue_delta=clue_delta,
        match_outcome=match_outcome,
    )


def _apply_resource_effect_code(
    *,
    effect_code: str,
    player_state: ResourceState,
    apparition_state: ResourceState,
) -> tuple[ResourceState, ResourceState]:
    if effect_code.startswith("actor_sanity:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "sanity",
            True,
        )
    if effect_code.startswith("opponent_sanity:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "sanity",
            False,
        )
    if effect_code.startswith("actor_ritual_power:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "ritual_power",
            True,
        )
    if effect_code.startswith("opponent_ritual_power:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "ritual_power",
            False,
        )
    if effect_code.startswith("actor_curse_mark:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "curse_marks",
            True,
        )
    if effect_code.startswith("opponent_curse_mark:"):
        return _apply_numeric_effect(
            player_state,
            apparition_state,
            effect_code,
            "curse_marks",
            False,
        )
    if effect_code == "actor_suspicion:+1":
        return add_suspicion(player_state), apparition_state
    if effect_code == "opponent_suspicion:+1":
        return player_state, add_suspicion(apparition_state)
    if effect_code == "actor_suspicion_reset:0":
        return player_state.replace(suspicion=0), apparition_state
    if effect_code == "opponent_suspicion_reset:0":
        return player_state, apparition_state.replace(suspicion=0)
    if effect_code == "actor_shield:+1":
        return add_shield(player_state), apparition_state
    if effect_code == "opponent_shield:+1":
        return player_state, add_shield(apparition_state)
    if effect_code == ACTOR_INCOMPLETE_TRUE_NAME_EFFECT_CODE:
        return add_incomplete_true_name_fragment(player_state), apparition_state

    return player_state, apparition_state


def _apply_numeric_effect(
    player_state: ResourceState,
    apparition_state: ResourceState,
    effect_code: str,
    field: str,
    applies_to_player: bool,
) -> tuple[ResourceState, ResourceState]:
    target_state = player_state if applies_to_player else apparition_state
    value = getattr(target_state, field) + _effect_amount(effect_code)
    next_state = target_state.replace(
        **{field: _clamp_resource_value(field=field, value=value)}
    )
    if applies_to_player:
        return next_state, apparition_state
    return player_state, next_state


def _effect_amount(effect_code: str) -> int:
    raw_amount = effect_code.split(":", maxsplit=1)[1]
    return int(raw_amount)


def _clamp_resource_value(*, field: str, value: int) -> int:
    maximum_by_field = {
        "sanity": MAX_SANITY,
        "ritual_power": MAX_RITUAL_POWER,
        "curse_marks": MAX_CURSE_MARKS,
    }
    return max(0, min(value, maximum_by_field[field]))


def _consume_action_cost(state: ResourceState, *, action_code: str) -> ResourceState:
    return state.replace(
        ritual_power=max(0, state.ritual_power - ACTION_RITUAL_POWER_COSTS[action_code])
    )


def _should_add_true_name_fragment(
    *,
    resolution: TurnResolution,
    info_target_key: str | None,
    state: ResourceState,
) -> bool:
    if info_target_key is None:
        return False
    if resolution.player_action_code not in TRUE_NAME_REVEAL_ACTION_CODES:
        return False
    if TRUE_NAME_CANDIDATE_EFFECT_CODE not in resolution.effect_codes:
        return ACTOR_INCOMPLETE_TRUE_NAME_EFFECT_CODE in resolution.effect_codes
    return state.true_name_fragments < MAX_TRUE_NAME_FRAGMENTS


def _add_true_name_fragment_from_reveal(
    *,
    match: Match,
    turn: Turn,
    participant: MatchParticipant,
    action_code: str,
    info_target_key: str | None,
    current_true_name_fragments: int,
) -> dict[str, Any] | None:
    definition = _matching_true_name_fragment_definition(
        action_code=action_code,
        info_target_key=info_target_key,
        current_true_name_fragments=current_true_name_fragments,
    )
    if definition is None:
        return None

    _, created = MatchTrueNameFragmentOwnership.objects.get_or_create(
        match_id=match.id,
        participant_id=participant.id,
        true_name_fragment_id=definition["id"],
        defaults={
            "source_turn_id": turn.id,
            "source_turn_number": turn.turn_number,
        },
    )
    if not created:
        return None

    return _true_name_fragment_payload(
        definition=definition,
        source_turn_number=turn.turn_number,
    )


def _matching_true_name_fragment_definition(
    *,
    action_code: str,
    info_target_key: str | None,
    current_true_name_fragments: int,
) -> dict[str, Any] | None:
    for definition in APPROVED_MIRROR_GUEST_TRUE_NAME_FRAGMENTS:
        if definition["primary_info_target_key"] != info_target_key:
            continue
        if action_code not in definition["required_action_codes"]:
            continue
        if current_true_name_fragments < definition.get("minimum_true_name_fragments", 0):
            continue
        return dict(definition)
    return None


def _add_false_clue_from_trigger(
    *,
    match: Match,
    turn: Turn,
    participant: MatchParticipant,
    info_target_key: str | None,
    current_true_name_fragments: int,
) -> dict[str, Any] | None:
    definition = _matching_false_clue_definition(
        info_target_key=info_target_key,
        current_true_name_fragments=current_true_name_fragments,
    )
    if definition is None:
        return None

    _, created = MatchFalseClueOwnership.objects.get_or_create(
        match_id=match.id,
        participant_id=participant.id,
        false_clue_id=definition["id"],
        defaults={
            "truth_state": CLUE_TRUTH_STATE_UNKNOWN,
            "source_turn_id": turn.id,
            "source_turn_number": turn.turn_number,
        },
    )
    if not created:
        return None

    return _false_clue_payload(
        false_clue_id=definition["id"],
        truth_state=CLUE_TRUTH_STATE_UNKNOWN,
        source_turn_number=turn.turn_number,
    )


def _matching_false_clue_definition(
    *,
    info_target_key: str | None,
    current_true_name_fragments: int,
) -> dict[str, Any] | None:
    for definition in APPROVED_MIRROR_GUEST_FALSE_CLUES:
        if info_target_key not in definition["trigger_info_target_keys"]:
            continue
        if current_true_name_fragments < definition.get("minimum_true_name_fragments", 0):
            continue
        return dict(definition)
    return None


def _true_name_fragment_payload(
    *,
    definition: Mapping[str, Any],
    source_turn_number: int,
) -> dict[str, Any]:
    return {
        "clue_id": definition["clue_id"],
        "text": definition["text"],
        "truth_state": "true_revealed",
        "source_turn_number": source_turn_number,
    }


def _false_clue_payload(
    *,
    false_clue_id: int,
    truth_state: str,
    source_turn_number: int,
) -> dict[str, Any]:
    definition = _false_clue_definition_by_id(false_clue_id)
    return {
        "clue_id": definition["clue_id"],
        "text": definition["text"],
        "truth_state": truth_state,
        "source_turn_number": source_turn_number,
    }


def _false_clue_definition_by_id(false_clue_id: int) -> dict[str, Any]:
    for definition in APPROVED_MIRROR_GUEST_FALSE_CLUES:
        if definition["id"] == false_clue_id:
            return dict(definition)
    raise ValueError(f"unknown false clue id: {false_clue_id}")


def _merge_clue_delta(
    target: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    target["added"].extend(source["added"])
    target["removed_clue_ids"].extend(source["removed_clue_ids"])
    target["revealed"].extend(source["revealed"])


def _resource_state_from_participant(participant: MatchParticipant) -> ResourceState:
    return ResourceState(
        sanity=participant.sanity,
        ritual_power=participant.ritual_power,
        curse_marks=participant.curse_marks,
        secret_exposure=participant.secret_exposure,
        true_name_fragments=participant.true_name_fragments,
        incomplete_true_name_fragments=participant.incomplete_true_name_fragments,
        false_clues=participant.false_clues,
        suspicion=participant.suspicion,
        shield=participant.shield,
    )


def _persist_resource_state(participant: MatchParticipant, state: ResourceState) -> None:
    participant.sanity = state.sanity
    participant.ritual_power = state.ritual_power
    participant.curse_marks = state.curse_marks
    participant.secret_exposure = state.secret_exposure
    participant.true_name_fragments = state.true_name_fragments
    participant.incomplete_true_name_fragments = state.incomplete_true_name_fragments
    participant.false_clues = state.false_clues
    participant.suspicion = state.suspicion
    participant.shield = state.shield
    participant.save(
        update_fields=(
            "sanity",
            "ritual_power",
            "curse_marks",
            "secret_exposure",
            "true_name_fragments",
            "incomplete_true_name_fragments",
            "false_clues",
            "suspicion",
            "shield",
        )
    )


def _state_delta(*, before: ResourceState, after: ResourceState) -> dict[str, Any]:
    result = {}
    for field in (
        "sanity",
        "ritual_power",
        "curse_marks",
        "true_name_fragments",
        "incomplete_true_name_fragments",
        "false_clues",
        "suspicion",
        "shield",
    ):
        before_value = getattr(before, field)
        after_value = getattr(after, field)
        if before_value != after_value:
            result[field] = {
                "before": before_value,
                "after": after_value,
                "delta": after_value - before_value,
            }
    return result


def _finish_match_or_create_next_turn(
    *,
    match: Match,
    turn: Turn,
    human_participant: MatchParticipant,
    resolution: TurnResolution,
    now,
) -> Turn:
    if resolution.match_outcome.status != OutcomeStatus.IN_PROGRESS:
        match.status = MATCH_STATUS_RESOLVED
        match.ended_at = now
        match.winner_participant_id = (
            human_participant.id
            if resolution.match_outcome.status == OutcomeStatus.WIN
            else None
        )
        match.save(update_fields=("status", "ended_at", "winner_participant_id"))
        return turn

    human_state = _resource_state_from_participant(human_participant)
    next_state = add_ritual_power(human_state, amount=2)
    _persist_resource_state(human_participant, next_state)
    return Turn.objects.create(
        match_id=match.id,
        turn_number=turn.turn_number + 1,
        status=TURN_STATUS_AWAITING_PLAYER,
        deadline_at=now + timedelta(seconds=NEXT_TURN_SECONDS),
    )


def _turn_result_payload(
    *,
    resolution: TurnResolution,
    info_target_key: str | None,
    state_delta: dict[str, Any],
    clue_delta: dict[str, Any],
) -> dict[str, Any]:
    return {
        "turn_id": resolution.turn_id,
        "turn_number": resolution.turn_number,
        "player_action": _action_view(
            action_code=resolution.player_action_code,
            info_target_key=info_target_key,
            timeout_applied=resolution.timeout_applied,
        ),
        "opponent_action": _action_view(
            action_code=resolution.opponent_action_code,
            info_target_key=None,
            timeout_applied=False,
        ),
        "public_log": {
            "turn_number": resolution.turn_number,
            "text": resolution.public_log,
            "log_key": None,
        },
        "state_delta": state_delta,
        "clue_delta": clue_delta,
        "match_outcome": OUTCOME_RESULT_BY_STATUS[resolution.match_outcome.status],
    }


def _action_view(
    *,
    action_code: str,
    info_target_key: str | None,
    timeout_applied: bool,
) -> dict[str, Any]:
    return {
        "code": action_code,
        "display_name": ACTION_DISPLAY_NAMES[action_code],
        "info_target_key": info_target_key,
        "timeout_applied": timeout_applied,
    }


def _curse_marks_loss_triggered(state: ResourceState) -> bool:
    return state.curse_marks >= MAX_CURSE_MARKS


def _public_id(*, prefix: str, value: int) -> str:
    return f"{prefix}_{value}"


def _get_match(*, match_id: int) -> Match:
    try:
        return Match.objects.get(id=match_id)
    except Match.DoesNotExist as exc:
        raise _match_not_found() from exc


def _assert_match_access(*, user_id: int, match_id: int) -> None:
    has_start_request = MatchStartRequest.objects.filter(
        user_id=user_id,
        match_id=match_id,
    ).exists()
    if has_start_request:
        return

    raise ApiErrorResponseException(
        "MATCH_ACCESS_DENIED",
        status_code=HTTP_403_FORBIDDEN,
    )


def _get_current_turn(*, match_id: int) -> Turn:
    turn = Turn.objects.filter(match_id=match_id).order_by("-turn_number", "-id").first()
    if turn is None:
        raise _match_not_found()
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
        raise _match_not_found()
    return participant


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


def _match_not_found() -> ApiErrorResponseException:
    return ApiErrorResponseException(
        "MATCH_NOT_FOUND",
        status_code=HTTP_404_NOT_FOUND,
    )
