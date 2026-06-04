from dataclasses import dataclass
from typing import Iterable

from backend.apps.ai_profile.metrics import ActionEvent, StyleMetrics, calculate_style_metrics
from backend.apps.game_rules.outcomes import OutcomeStatus
from backend.apps.matches.resolution import TurnResolution


AI_PROFILE_PERSONAL_DATA_MODELS = (
    "PlayerActionEvent",
    "StyleMetricSnapshot",
)


@dataclass(frozen=True)
class StyleSnapshot:
    user_id: str
    metrics: StyleMetrics


def build_action_event_from_turn_resolution(
    *,
    resolution: TurnResolution,
    user_id: str,
    mode: str,
    match_id: str,
    stage_id: str,
    info_target_key: str | None,
    decision_duration_ms: int,
    sanity_before: int,
    ritual_power_before: int,
    curse_marks_before: int,
    result_code: str,
    acquired_clue_id: str | None,
    clue_truth_state: str | None,
) -> ActionEvent:
    return ActionEvent(
        user_id=user_id,
        mode=mode,
        match_id=match_id,
        stage_id=stage_id,
        turn_number=resolution.turn_number,
        action_code=resolution.player_action_code,
        info_target_key=info_target_key,
        decision_duration_ms=decision_duration_ms,
        sanity_before=sanity_before,
        ritual_power_before=ritual_power_before,
        curse_marks_before=curse_marks_before,
        opponent_action_code=resolution.opponent_action_code,
        result_code=result_code,
        acquired_clue_id=acquired_clue_id,
        clue_truth_state=clue_truth_state,
        match_outcome=_event_match_outcome(resolution),
    )


def calculate_style_snapshot(
    *,
    user_id: str,
    events: Iterable[ActionEvent],
) -> StyleSnapshot:
    return StyleSnapshot(
        user_id=user_id,
        metrics=calculate_style_metrics(events),
    )


def recalculate_final_style_snapshot(
    *,
    user_id: str,
    events: Iterable[ActionEvent],
) -> StyleSnapshot:
    return calculate_style_snapshot(user_id=user_id, events=events)


def _event_match_outcome(resolution: TurnResolution) -> str | None:
    if resolution.match_outcome.status == OutcomeStatus.IN_PROGRESS:
        return None

    return resolution.match_outcome.status.value
