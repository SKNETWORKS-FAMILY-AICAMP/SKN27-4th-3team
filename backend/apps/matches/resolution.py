from dataclasses import dataclass
from datetime import datetime

from backend.apps.common.errors import ApiError, make_api_error
from backend.apps.game_rules.matchups import ACTION_CODES, MatchupResult, get_matchup_result
from backend.apps.game_rules.outcomes import StoryOutcome, determine_ai_story_outcome
from backend.apps.game_rules.resources import ResourceState
from backend.apps.matches.constants import TURN_STATUS_RESOLVED, TURN_STATUS_TIMED_OUT


TURN_DEADLINE_EXPIRED_ERROR_CODE = "TURN_DEADLINE_EXPIRED"
TIMEOUT_PLAYER_ACTION_CODE = "silence"
SEAL_ACTION_CODE = "seal"
SEAL_SUCCESS_EFFECT_CODE = "seal_success_if_condition_met"
SEAL_FAILURE_EFFECT_CODE = "seal_failed"


@dataclass(frozen=True)
class TurnResolution:
    turn_id: str
    turn_number: int
    player_action_code: str
    opponent_action_code: str
    matchup_result: MatchupResult
    effect_codes: tuple[str, ...]
    public_log: str
    turn_status: str
    timeout_applied: bool
    player_timeout_count: int
    seal_succeeded: bool
    match_outcome: StoryOutcome


def validate_submission_deadline(
    *,
    deadline_at: datetime,
    submitted_at: datetime,
) -> ApiError | None:
    if submitted_at > deadline_at:
        return make_api_error(TURN_DEADLINE_EXPIRED_ERROR_CODE)

    return None


def resolve_ai_story_turn(
    *,
    turn_id: str,
    turn_number: int,
    deadline_at: datetime,
    server_time: datetime,
    player_action_code: str | None,
    opponent_action_code: str,
    player_timeout_count: int,
    player_state: ResourceState,
    seal_condition_met: bool,
    curse_marks_loss_triggered: bool,
) -> TurnResolution:
    resolved_player_action, timeout_applied = _resolve_player_action(
        player_action_code=player_action_code,
        deadline_at=deadline_at,
        server_time=server_time,
    )
    _validate_action_code(resolved_player_action)
    _validate_action_code(opponent_action_code)

    matchup_result = get_matchup_result(resolved_player_action, opponent_action_code)
    next_timeout_count = player_timeout_count + int(timeout_applied)
    seal_succeeded = _determine_seal_success(
        player_action_code=resolved_player_action,
        matchup_result=matchup_result,
        seal_condition_met=seal_condition_met,
    )
    match_outcome = determine_ai_story_outcome(
        seal_succeeded=seal_succeeded,
        player_sanity=player_state.sanity,
        curse_marks_loss_triggered=curse_marks_loss_triggered,
        turn_number=turn_number,
    )

    return TurnResolution(
        turn_id=turn_id,
        turn_number=turn_number,
        player_action_code=resolved_player_action,
        opponent_action_code=opponent_action_code,
        matchup_result=matchup_result,
        effect_codes=matchup_result.effect_codes,
        public_log=matchup_result.public_log,
        turn_status=TURN_STATUS_TIMED_OUT if timeout_applied else TURN_STATUS_RESOLVED,
        timeout_applied=timeout_applied,
        player_timeout_count=next_timeout_count,
        seal_succeeded=seal_succeeded,
        match_outcome=match_outcome,
    )


def _resolve_player_action(
    *,
    player_action_code: str | None,
    deadline_at: datetime,
    server_time: datetime,
) -> tuple[str, bool]:
    if player_action_code is not None:
        return player_action_code, False

    if server_time > deadline_at:
        return TIMEOUT_PLAYER_ACTION_CODE, True

    raise ValueError("player action is required before deadline")


def _validate_action_code(action_code: str) -> None:
    if action_code not in ACTION_CODES:
        raise ValueError(f"unknown action_code: {action_code}")


def _determine_seal_success(
    *,
    player_action_code: str,
    matchup_result: MatchupResult,
    seal_condition_met: bool,
) -> bool:
    if player_action_code != SEAL_ACTION_CODE:
        return False
    if not seal_condition_met:
        return False
    if SEAL_FAILURE_EFFECT_CODE in matchup_result.effect_codes:
        return False

    return SEAL_SUCCESS_EFFECT_CODE in matchup_result.effect_codes
