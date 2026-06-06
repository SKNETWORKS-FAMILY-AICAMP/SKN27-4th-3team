from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import timedelta, timezone as datetime_timezone
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone

from backend.apps.ai_profile import services as ai_profile_services
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
    DuelDialogue,
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
    APPROVED_STORY_CASE_DEFINITIONS,
    MIRROR_GUEST_CASE_ID,
    MVP_STORY_MAX_TURNS,
)


__all__ = (
    "MATCH_STORAGE_JSON_PAYLOAD_SCHEMA",
    "MatchDetailResult",
    "DuelDialogueResult",
    "MatchResultResult",
    "TurnLlmTextResult",
    "TurnSubmitResult",
    "apply_deterministic_false_clue_detection",
    "TurnResolution",
    "get_match_detail",
    "get_match_result",
    "create_duel_dialogue",
    "generate_turn_llm_text",
    "parse_public_match_id",
    "parse_public_turn_id",
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
TURN_PUBLIC_ID_PREFIX = "turn_"
TURN_RESULT_SCHEMA_VERSION = "turn_result.v1"
NEXT_TURN_SECONDS = 25
DUEL_DIALOGUE_LIMIT_PER_MATCH = 8
DEFAULT_TURN_LLM_DISPLAY_SLOT = "right_apparition_message"
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
class TurnLlmTextResult:
    llm_text: dict[str, Any]


@dataclass(frozen=True)
class DuelDialogueResult:
    dialogue: dict[str, Any]


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
    case_definition = _get_match_case_definition(match_id=match_id)
    result_reason = _match_result_reason(
        match=match,
        human_participant=human_participant,
        last_turn=last_turn,
    )
    result_text_by_reason = case_definition["result_text_by_reason"]

    result_payload = {
        "match_id": _public_id(prefix="match", value=match.id),
        "result": _match_result(match=match, human_participant=human_participant),
        "result_reason": result_reason,
        "case": {
            "case_id": case_definition["case_id"],
            "title": case_definition["title"],
        },
        "final_resources": _final_resource_payload(human_participant),
        "turn_logs": _get_match_turn_logs(match_id=match_id),
        "story_result_text": list(
            result_text_by_reason.get(
                result_reason,
                result_text_by_reason[RESULT_REASON_UNRESOLVED],
            )
        ),
        "style_summary": _style_summary_payload(session=session),
    }
    llm_summary = llm_services.generate_result_summary(
        match_result={**result_payload, "llm_summary": llm_services.build_disabled_llm_summary()},
        match_id=match.id,
        user_id=user_id,
    )
    result_payload["llm_summary"] = llm_summary

    return MatchResultResult(result=result_payload)


def generate_turn_llm_text(
    *,
    raw_access_token: str | None,
    public_match_id: str,
    public_turn_id: str,
    display_slot: str | None,
) -> TurnLlmTextResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)
    match_id = parse_public_match_id(public_match_id)
    turn_id = parse_public_turn_id(public_turn_id)

    _get_match(match_id=match_id)
    _assert_match_access(user_id=user_id, match_id=match_id)
    turn = _get_turn(turn_id=turn_id)
    if turn.match_id != match_id:
        raise _match_not_found()

    turn_result = _get_turn_result_payload(turn_id=turn.id)
    case_definition = _get_match_case_definition(match_id=match_id)
    llm_text = llm_services.generate_turn_flavor_text(
        turn_result=turn_result,
        match_id=match_id,
        turn_id=turn.id,
        user_id=user_id,
        display_slot=display_slot or DEFAULT_TURN_LLM_DISPLAY_SLOT,
        apparition_alias=case_definition["apparition_alias"],
    )
    return TurnLlmTextResult(llm_text=llm_text)


def create_duel_dialogue(
    *,
    raw_access_token: str | None,
    public_match_id: str,
    message: str,
    client_nonce: UUID,
) -> DuelDialogueResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    user_id = _session_user_id(session=session)
    match_id = parse_public_match_id(public_match_id)
    match = _get_match(match_id=match_id)
    _assert_match_access(user_id=user_id, match_id=match_id)

    existing_dialogue = (
        DuelDialogue.objects.filter(
            match_id=match_id,
            user_id=user_id,
            client_nonce=client_nonce,
        )
        .order_by("id")
        .first()
    )
    if existing_dialogue is not None:
        return DuelDialogueResult(dialogue=_duel_dialogue_payload(existing_dialogue))

    if _duel_dialogue_count(match_id=match_id, user_id=user_id) >= DUEL_DIALOGUE_LIMIT_PER_MATCH:
        raise ApiErrorResponseException(
            "DUEL_DIALOGUE_LIMIT_EXCEEDED",
            status_code=HTTP_409_CONFLICT,
        )

    llm_text = llm_services.generate_final_duel_dialogue(
        match_payload=_duel_match_payload(
            match=match,
            match_id=match_id,
            user_id=user_id,
        ),
        player_message=message,
        match_id=match_id,
        user_id=user_id,
    )
    generation_id = _parse_public_llm_generation_id(llm_text.get("generation_id"))
    try:
        dialogue = DuelDialogue.objects.create(
            match_id=match_id,
            user_id=user_id,
            client_nonce=client_nonce,
            player_message=message,
            apparition_message=llm_text["text"] if llm_text["enabled"] else None,
            generation_id=generation_id,
        )
    except IntegrityError:
        existing_dialogue = DuelDialogue.objects.get(
            match_id=match_id,
            user_id=user_id,
            client_nonce=client_nonce,
        )
        return DuelDialogueResult(dialogue=_duel_dialogue_payload(existing_dialogue))

    return DuelDialogueResult(
        dialogue=_duel_dialogue_payload(
            dialogue,
            llm_text=llm_text,
        )
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
        case_id = _get_match_case_id(match_id=match_id)
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
            case_id=case_id,
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
            case_id=case_id,
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

        acquired_clue_id, clue_truth_state = _first_clue_event(effect_result.clue_delta)
        ai_profile_event = ai_profile_services.build_action_event_from_turn_resolution(
            resolution=resolution,
            user_id=str(user_id),
            mode=match.mode,
            match_id=str(match.id),
            stage_id=1,
            info_target_key=info_target_key,
            decision_duration_ms=_decision_duration_ms(
                started_at=turn.started_at,
                submitted_at=now,
            ),
            sanity_before=player_state_before.sanity,
            ritual_power_before=player_state_before.ritual_power,
            curse_marks_before=player_state_before.curse_marks,
            result_code=_result_code_from_resolution(resolution),
            acquired_clue_id=acquired_clue_id,
            clue_truth_state=clue_truth_state,
        )
        ai_profile_services.persist_turn_action_event(ai_profile_event)
        ai_profile_events = ai_profile_services.list_action_events_for_match(
            user_id=user_id,
            match_id=match.id,
        )
        ai_profile_services.persist_style_snapshot(
            snapshot=ai_profile_services.calculate_style_snapshot(
                user_id=str(user_id),
                events=ai_profile_events,
            )
        )
        if match.status == MATCH_STATUS_RESOLVED:
            ai_profile_services.persist_final_style_snapshot(
                snapshot=ai_profile_services.recalculate_final_style_snapshot(
                    user_id=str(user_id),
                    events=ai_profile_events,
                )
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


def _get_turn_result_payload(*, turn_id: int) -> dict[str, Any]:
    turn_result = TurnResult.objects.filter(turn_id=turn_id).order_by("-id").first()
    if turn_result is None:
        raise _match_not_found()

    payload = turn_result.result_json.get("turn_result")
    if not isinstance(payload, Mapping):
        raise _match_not_found()

    return dict(payload)


def _duel_match_payload(
    *,
    match: Match,
    match_id: int,
    user_id: int,
) -> dict[str, Any]:
    human_participant = _get_participant(
        match_id=match_id,
        participant_type=PARTICIPANT_TYPE_HUMAN,
    )
    current_turn = _get_current_turn(match_id=match_id)
    recent_public_logs = _get_match_turn_logs(match_id=match_id)[-3:]
    case_definition = _get_match_case_definition(match_id=match_id)
    return {
        "case": {
            "case_id": case_definition["case_id"],
            "title": case_definition["title"],
        },
        "match": {
            "match_id": _public_id(prefix="match", value=match.id),
            "turn_number": current_turn.turn_number,
            "result": _match_result_for_duel(match=match, human_participant=human_participant),
        },
        "apparition_alias": case_definition["apparition_alias"],
        "public_context": {
            "true_name_fragments": human_participant.true_name_fragments,
            "curse_marks": human_participant.curse_marks,
            "sanity": human_participant.sanity,
            "recent_public_logs": recent_public_logs,
        },
    }


def _match_result_for_duel(*, match: Match, human_participant: MatchParticipant) -> str:
    if match.status != MATCH_STATUS_RESOLVED:
        return RESULT_REASON_UNRESOLVED

    return _match_result(match=match, human_participant=human_participant)


def _duel_dialogue_payload(
    dialogue: DuelDialogue,
    *,
    llm_text: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dialogue_id": _public_id(prefix="duel_dialogue", value=dialogue.id),
        "match_id": _public_id(prefix="match", value=dialogue.match_id),
        "player_message": dialogue.player_message,
        "apparition_message": dialogue.apparition_message,
        "llm_text": llm_text or _stored_duel_llm_text(dialogue),
        "created_at": _iso_utc(dialogue.created_at),
    }


def _stored_duel_llm_text(dialogue: DuelDialogue) -> dict[str, Any]:
    enabled = dialogue.apparition_message is not None
    generation_id = (
        _public_id(prefix="llm_generation", value=dialogue.generation_id)
        if enabled and dialogue.generation_id is not None
        else None
    )
    return {
        "enabled": enabled,
        "purpose": llm_services.PURPOSE_FINAL_DUEL_DIALOGUE,
        "text": dialogue.apparition_message,
        "display_slot": llm_services.DISPLAY_SLOT_DUEL_DIALOGUE,
        "fallback_used": not enabled,
        "generation_id": generation_id,
        "context_refs": [],
        "metadata": {},
    }


def _duel_dialogue_count(*, match_id: int, user_id: int) -> int:
    return DuelDialogue.objects.filter(match_id=match_id, user_id=user_id).count()


def _parse_public_llm_generation_id(public_generation_id: Any) -> int | None:
    if public_generation_id is None:
        return None
    if not isinstance(public_generation_id, str):
        return None
    prefix = "llm_generation_"
    if not public_generation_id.startswith(prefix):
        return None

    raw_id = public_generation_id.removeprefix(prefix)
    try:
        value = int(raw_id)
    except ValueError:
        return None

    return value if value > 0 else None


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


def _get_match_case_id(*, match_id: int) -> str:
    start_request = (
        MatchStartRequest.objects.filter(match_id=match_id)
        .order_by("id")
        .first()
    )
    if start_request is None:
        return MIRROR_GUEST_CASE_ID
    return start_request.case_id


def _get_match_case_definition(*, match_id: int) -> dict[str, Any]:
    return _story_case_definition(case_id=_get_match_case_id(match_id=match_id))


def _story_case_definition(*, case_id: str) -> dict[str, Any]:
    try:
        return dict(APPROVED_STORY_CASE_DEFINITIONS[case_id])
    except KeyError as exc:
        raise ApiErrorResponseException(
            "CASE_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
        ) from exc


def parse_public_match_id(public_match_id: str) -> int:
    return _parse_public_id(public_match_id, prefix=MATCH_PUBLIC_ID_PREFIX)


def parse_public_turn_id(public_turn_id: str) -> int:
    return _parse_public_id(public_turn_id, prefix=TURN_PUBLIC_ID_PREFIX)


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
    case_id: str | None = None,
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
        case_id=case_id or _get_match_case_id(match_id=match_id),
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
    case_id: str = MIRROR_GUEST_CASE_ID,
) -> None:
    case_definition = _story_case_definition(case_id=case_id)
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
        and info_target_key not in case_definition["info_target_keys"]
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
    case_id: str,
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
            case_id=case_id,
        )
        if added_false_clue is not None:
            state_after = add_false_clue(state_after)
            clue_delta["added"].append(added_false_clue)

    if FALSE_CLUE_DETECTION_EFFECT_CODE in resolution.effect_codes:
        detection_delta = apply_deterministic_false_clue_detection(
            match_id=match.id,
            participant_id=human_participant.id,
            turn_number=turn.turn_number,
            case_id=case_id,
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
            case_id=case_id,
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
    case_id: str,
) -> dict[str, Any] | None:
    definition = _matching_true_name_fragment_definition(
        action_code=action_code,
        info_target_key=info_target_key,
        current_true_name_fragments=current_true_name_fragments,
        case_id=case_id,
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
    case_id: str = MIRROR_GUEST_CASE_ID,
) -> dict[str, Any] | None:
    for definition in _story_case_definition(case_id=case_id)["true_name_fragments"]:
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
    case_id: str,
) -> dict[str, Any] | None:
    definition = _matching_false_clue_definition(
        info_target_key=info_target_key,
        current_true_name_fragments=current_true_name_fragments,
        case_id=case_id,
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
        case_id=case_id,
    )


def _matching_false_clue_definition(
    *,
    info_target_key: str | None,
    current_true_name_fragments: int,
    case_id: str = MIRROR_GUEST_CASE_ID,
) -> dict[str, Any] | None:
    for definition in _story_case_definition(case_id=case_id)["false_clues"]:
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
    case_id: str = MIRROR_GUEST_CASE_ID,
) -> dict[str, Any]:
    definition = _false_clue_definition_by_id(false_clue_id, case_id=case_id)
    return {
        "clue_id": definition["clue_id"],
        "text": definition["text"],
        "truth_state": truth_state,
        "source_turn_number": source_turn_number,
    }


def _false_clue_definition_by_id(false_clue_id: int, *, case_id: str = MIRROR_GUEST_CASE_ID) -> dict[str, Any]:
    for definition in _story_case_definition(case_id=case_id)["false_clues"]:
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


def _first_clue_event(clue_delta: Mapping[str, Any]) -> tuple[str | None, str | None]:
    for bucket_name in ("added", "revealed"):
        raw_items = clue_delta.get(bucket_name, ())
        if not isinstance(raw_items, list):
            continue
        for raw_item in raw_items:
            if not isinstance(raw_item, Mapping):
                continue
            clue_id = raw_item.get("clue_id")
            truth_state = raw_item.get("truth_state")
            return (
                str(clue_id) if clue_id is not None else None,
                str(truth_state) if truth_state is not None else None,
            )

    return None, None


def _decision_duration_ms(*, started_at, submitted_at) -> int:
    elapsed_seconds = max(0.0, (submitted_at - started_at).total_seconds())
    return int(elapsed_seconds * 1000)


def _result_code_from_resolution(resolution: TurnResolution) -> str:
    if not resolution.effect_codes:
        return "no_effect"
    return resolution.effect_codes[0]


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
        started_at=now,
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


def _parse_public_id(public_id: str, *, prefix: str) -> int:
    if not isinstance(public_id, str):
        raise _match_not_found()
    if not public_id.startswith(prefix):
        raise _match_not_found()

    raw_id = public_id.removeprefix(prefix)
    try:
        value = int(raw_id)
    except ValueError as exc:
        raise _match_not_found() from exc

    if value <= 0:
        raise _match_not_found()
    return value


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


def _get_turn(*, turn_id: int) -> Turn:
    try:
        return Turn.objects.get(id=turn_id)
    except Turn.DoesNotExist as exc:
        raise _match_not_found() from exc


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


def _iso_utc(value) -> str | None:
    if value is None:
        return None
    return value.astimezone(datetime_timezone.utc).isoformat().replace("+00:00", "Z")


def _match_not_found() -> ApiErrorResponseException:
    return ApiErrorResponseException(
        "MATCH_NOT_FOUND",
        status_code=HTTP_404_NOT_FOUND,
    )
