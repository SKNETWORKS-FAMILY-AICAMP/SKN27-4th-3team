from backend.apps.ai_profile.metrics import (
    DEFAULT_TURN_LIMIT_MS,
    ActionEvent,
    calculate_style_metrics,
)


def test_action_event_contains_approved_storage_fields():
    event = ActionEvent(
        user_id="user-1",
        mode="ai_story",
        match_id="match-1",
        stage_id="stage-1",
        turn_number=1,
        action_code="insight",
        info_target_key="mirror_surface",
        decision_duration_ms=12000,
        sanity_before=12,
        ritual_power_before=3,
        curse_marks_before=0,
        opponent_action_code="silence",
        result_code="clue_gain_failed",
        acquired_clue_id=None,
        clue_truth_state=None,
        match_outcome=None,
    )

    assert event.user_id == "user-1"
    assert event.info_target_key == "mirror_surface"
    assert event.match_outcome is None


def test_style_metrics_follow_approved_action_ratios():
    events = (
        _event(1, "curse"),
        _event(2, "guard"),
        _event(3, "insight"),
        _event(4, "trick"),
        _event(5, "contract"),
        _event(6, "silence"),
    )

    metrics = calculate_style_metrics(events)

    assert metrics.aggression == 1 / 6
    assert metrics.defense == 1 / 6
    assert metrics.insight_focus == 1 / 6
    assert metrics.deception == 1 / 6
    assert metrics.risk_preference == 1 / 6
    assert metrics.silence_reliance == 1 / 6


def test_crisis_and_late_choice_metrics_use_contract_denominators():
    events = (
        _event(1, "guard", sanity_before=4, decision_duration_ms=10000),
        _event(2, "contract", sanity_before=3, decision_duration_ms=17500),
        _event(3, "curse", sanity_before=5, decision_duration_ms=20000),
        _event(4, "silence", sanity_before=2, decision_duration_ms=5000),
    )

    metrics = calculate_style_metrics(events, turn_limit_ms=DEFAULT_TURN_LIMIT_MS)

    assert metrics.crisis_guard_rate == 1 / 3
    assert metrics.crisis_contract_rate == 1 / 3
    assert metrics.late_choice_rate == 2 / 4


def test_style_metrics_return_zero_when_denominator_is_zero():
    metrics = calculate_style_metrics(())

    assert metrics.aggression == 0.0
    assert metrics.defense == 0.0
    assert metrics.insight_focus == 0.0
    assert metrics.deception == 0.0
    assert metrics.risk_preference == 0.0
    assert metrics.silence_reliance == 0.0
    assert metrics.crisis_guard_rate == 0.0
    assert metrics.crisis_contract_rate == 0.0
    assert metrics.late_choice_rate == 0.0


def test_unknown_action_code_is_rejected_at_module_boundary():
    event = _event(1, "unknown")

    try:
        calculate_style_metrics((event,))
    except ValueError as exc:
        assert "Unknown action_code" in str(exc)
        return

    raise AssertionError("unknown action_code should be rejected")


def _event(
    turn_number: int,
    action_code: str,
    *,
    sanity_before: int = 12,
    decision_duration_ms: int = 1000,
) -> ActionEvent:
    return ActionEvent(
        user_id="user-1",
        mode="ai_story",
        match_id="match-1",
        stage_id="stage-1",
        turn_number=turn_number,
        action_code=action_code,
        info_target_key=None,
        decision_duration_ms=decision_duration_ms,
        sanity_before=sanity_before,
        ritual_power_before=3,
        curse_marks_before=0,
        opponent_action_code="silence",
        result_code="resolved",
        acquired_clue_id=None,
        clue_truth_state=None,
        match_outcome=None,
    )
