from dataclasses import dataclass
from typing import Iterable

from backend.apps.ai_profile.metrics import ActionEvent, StyleMetrics, calculate_style_metrics
from backend.apps.ai_profile.models import PlayerActionEvent, StyleMetricSnapshot
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


def persist_turn_action_event(event: ActionEvent) -> PlayerActionEvent:
    return PlayerActionEvent.objects.create(
        user_id=int(event.user_id),
        mode=event.mode,
        match_id=int(event.match_id),
        stage_id=int(event.stage_id),
        turn_number=event.turn_number,
        action_code=event.action_code,
        info_target_key=event.info_target_key,
        decision_duration_ms=event.decision_duration_ms,
        sanity_before=event.sanity_before,
        ritual_power_before=event.ritual_power_before,
        curse_marks_before=event.curse_marks_before,
        opponent_action_code=event.opponent_action_code,
        result_code=event.result_code,
        acquired_clue_id=event.acquired_clue_id,
        clue_truth_state=event.clue_truth_state,
        match_outcome=event.match_outcome,
    )


def persist_style_snapshot(*, snapshot: StyleSnapshot) -> StyleMetricSnapshot:
    return StyleMetricSnapshot.objects.create(
        user_id=int(snapshot.user_id),
        aggression=snapshot.metrics.aggression,
        defense=snapshot.metrics.defense,
        insight_focus=snapshot.metrics.insight_focus,
        deception=snapshot.metrics.deception,
        risk_preference=snapshot.metrics.risk_preference,
        silence_reliance=snapshot.metrics.silence_reliance,
        crisis_guard_rate=snapshot.metrics.crisis_guard_rate,
        crisis_contract_rate=snapshot.metrics.crisis_contract_rate,
        late_choice_rate=snapshot.metrics.late_choice_rate,
    )


def persist_final_style_snapshot(*, snapshot: StyleSnapshot) -> StyleMetricSnapshot:
    return persist_style_snapshot(snapshot=snapshot)


def list_action_events_for_match(*, user_id: int, match_id: int) -> tuple[ActionEvent, ...]:
    events = (
        PlayerActionEvent.objects.filter(user_id=user_id, match_id=match_id)
        .order_by("turn_number", "id")
    )
    return tuple(_action_event_from_model(event) for event in events)


def _event_match_outcome(resolution: TurnResolution) -> str | None:
    if resolution.match_outcome.status == OutcomeStatus.IN_PROGRESS:
        return None

    return resolution.match_outcome.status.value


def _action_event_from_model(event: PlayerActionEvent) -> ActionEvent:
    return ActionEvent(
        user_id=str(event.user_id),
        mode=event.mode,
        match_id=str(event.match_id),
        stage_id=str(event.stage_id),
        turn_number=event.turn_number,
        action_code=event.action_code,
        info_target_key=event.info_target_key,
        decision_duration_ms=event.decision_duration_ms,
        sanity_before=event.sanity_before,
        ritual_power_before=event.ritual_power_before,
        curse_marks_before=event.curse_marks_before,
        opponent_action_code=event.opponent_action_code,
        result_code=event.result_code,
        acquired_clue_id=event.acquired_clue_id,
        clue_truth_state=event.clue_truth_state,
        match_outcome=event.match_outcome,
    )
