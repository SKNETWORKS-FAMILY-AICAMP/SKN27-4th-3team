from dataclasses import dataclass
from typing import Iterable

from backend.apps.game_rules.matchups import ACTION_CODES


DEFAULT_TURN_LIMIT_MS = 25_000
CRISIS_SANITY_THRESHOLD = 4
LATE_CHOICE_THRESHOLD_RATIO = 0.7


@dataclass(frozen=True)
class ActionEvent:
    user_id: str
    mode: str
    match_id: str
    stage_id: str
    turn_number: int
    action_code: str
    info_target_key: str | None
    decision_duration_ms: int
    sanity_before: int
    ritual_power_before: int
    curse_marks_before: int
    opponent_action_code: str
    result_code: str
    acquired_clue_id: str | None
    clue_truth_state: str | None
    match_outcome: str | None


@dataclass(frozen=True)
class StyleMetrics:
    aggression: float
    defense: float
    insight_focus: float
    deception: float
    risk_preference: float
    silence_reliance: float
    crisis_guard_rate: float
    crisis_contract_rate: float
    late_choice_rate: float


def calculate_style_metrics(
    events: Iterable[ActionEvent],
    *,
    turn_limit_ms: int = DEFAULT_TURN_LIMIT_MS,
) -> StyleMetrics:
    event_list = tuple(events)
    _validate_events(event_list)

    total_turns = len(event_list)
    crisis_events = tuple(
        event
        for event in event_list
        if event.sanity_before <= CRISIS_SANITY_THRESHOLD
    )

    return StyleMetrics(
        aggression=_action_rate(event_list, total_turns, "curse"),
        defense=_action_rate(event_list, total_turns, "guard"),
        insight_focus=_action_rate(event_list, total_turns, "insight"),
        deception=_action_rate(event_list, total_turns, "trick"),
        risk_preference=_action_rate(event_list, total_turns, "contract"),
        silence_reliance=_action_rate(event_list, total_turns, "silence"),
        crisis_guard_rate=_action_rate(crisis_events, len(crisis_events), "guard"),
        crisis_contract_rate=_action_rate(
            crisis_events,
            len(crisis_events),
            "contract",
        ),
        late_choice_rate=_late_choice_rate(event_list, total_turns, turn_limit_ms),
    )


def _validate_events(events: tuple[ActionEvent, ...]) -> None:
    approved_actions = set(ACTION_CODES)
    for event in events:
        if event.action_code not in approved_actions:
            raise ValueError(f"Unknown action_code: {event.action_code!r}")


def _action_rate(
    events: tuple[ActionEvent, ...],
    denominator: int,
    action_code: str,
) -> float:
    if denominator == 0:
        return 0.0

    return _count_action(events, action_code) / denominator


def _late_choice_rate(
    events: tuple[ActionEvent, ...],
    total_turns: int,
    turn_limit_ms: int,
) -> float:
    if total_turns == 0:
        return 0.0

    late_threshold_ms = turn_limit_ms * LATE_CHOICE_THRESHOLD_RATIO
    late_choices = sum(
        1
        for event in events
        if event.decision_duration_ms >= late_threshold_ms
    )
    return late_choices / total_turns


def _count_action(events: tuple[ActionEvent, ...], action_code: str) -> int:
    return sum(1 for event in events if event.action_code == action_code)
