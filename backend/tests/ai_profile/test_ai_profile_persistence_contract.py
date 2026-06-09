from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.apps.game_rules.resources import ResourceState
from backend.apps.matches.resolution import resolve_ai_story_turn


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
AI_PROFILE_DIR = BACKEND_DIR / "apps" / "ai_profile"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(models.Model):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def test_ai_profile_persistence_modules_exist_for_task_9_contract():
    assert (AI_PROFILE_DIR / "models.py").exists()
    assert (AI_PROFILE_DIR / "services.py").exists()


def test_action_event_model_defines_approved_event_fields_without_json_or_fk_policy():
    source = _read(AI_PROFILE_DIR / "models.py")

    assert "class PlayerActionEvent(models.Model):" in source
    assert "models.JSONField" not in source
    assert "models.ForeignKey" not in source
    assert "on_delete=" not in source
    assert "db_table" not in source

    event_source = _class_source(source, "PlayerActionEvent")
    assert "user_id = models.PositiveBigIntegerField()" in event_source
    assert "mode = models.TextField()" in event_source
    assert "match_id = models.PositiveBigIntegerField()" in event_source
    assert "stage_id = models.PositiveBigIntegerField()" in event_source
    assert "turn_number = models.PositiveIntegerField()" in event_source
    assert "action_code = models.TextField(choices=ACTION_CODE_CHOICES)" in event_source
    assert "info_target_key = models.TextField(null=True, blank=True)" in event_source
    assert "decision_duration_ms = models.PositiveIntegerField()" in event_source
    assert "sanity_before = models.PositiveIntegerField()" in event_source
    assert "ritual_power_before = models.PositiveIntegerField()" in event_source
    assert "curse_marks_before = models.PositiveIntegerField()" in event_source
    assert "opponent_action_code = models.TextField(choices=ACTION_CODE_CHOICES)" in event_source
    assert "result_code = models.TextField()" in event_source
    assert "acquired_clue_id = models.TextField(null=True, blank=True)" in event_source
    assert "clue_truth_state = models.TextField(null=True, blank=True)" in event_source
    assert "match_outcome = models.TextField(null=True, blank=True)" in event_source


def test_style_snapshot_model_stores_approved_metric_fields_without_llm_summary_source():
    source = _read(AI_PROFILE_DIR / "models.py")

    assert "class StyleMetricSnapshot(models.Model):" in source
    assert "style_summary_json" not in source
    assert "llm" not in source.lower()
    assert "summary" not in _class_source(source, "StyleMetricSnapshot").lower()

    snapshot_source = _class_source(source, "StyleMetricSnapshot")
    assert "user_id = models.PositiveBigIntegerField()" in snapshot_source
    assert "aggression = models.FloatField()" in snapshot_source
    assert "defense = models.FloatField()" in snapshot_source
    assert "insight_focus = models.FloatField()" in snapshot_source
    assert "deception = models.FloatField()" in snapshot_source
    assert "risk_preference = models.FloatField()" in snapshot_source
    assert "silence_reliance = models.FloatField()" in snapshot_source
    assert "crisis_guard_rate = models.FloatField()" in snapshot_source
    assert "crisis_contract_rate = models.FloatField()" in snapshot_source
    assert "late_choice_rate = models.FloatField()" in snapshot_source


def test_services_build_action_event_at_turn_resolution_boundary():
    from backend.apps.ai_profile.services import build_action_event_from_turn_resolution

    deadline_at = datetime(2026, 6, 4, 12, 0, 0, tzinfo=UTC)
    player_state = ResourceState.initial()
    resolution = resolve_ai_story_turn(
        turn_id="turn-1",
        turn_number=1,
        deadline_at=deadline_at,
        server_time=deadline_at - timedelta(seconds=1),
        player_action_code="insight",
        opponent_action_code="silence",
        player_timeout_count=0,
        player_state=player_state,
        seal_condition_met=False,
        curse_marks_loss_triggered=False,
    )

    event = build_action_event_from_turn_resolution(
        resolution=resolution,
        user_id="user-1",
        mode="ai_story",
        match_id="match-1",
        stage_id="stage-1",
        info_target_key="mirror_surface",
        decision_duration_ms=12000,
        sanity_before=player_state.sanity,
        ritual_power_before=player_state.ritual_power,
        curse_marks_before=player_state.curse_marks,
        result_code="clue_gain_failed",
        acquired_clue_id=None,
        clue_truth_state=None,
    )

    assert event.user_id == "user-1"
    assert event.turn_number == 1
    assert event.action_code == "insight"
    assert event.opponent_action_code == "silence"
    assert event.match_outcome is None


def test_services_calculate_turn_and_final_style_snapshots_from_metrics_module():
    from backend.apps.ai_profile.metrics import ActionEvent
    from backend.apps.ai_profile.services import (
        AI_PROFILE_PERSONAL_DATA_MODELS,
        calculate_style_snapshot,
        recalculate_final_style_snapshot,
    )

    event = ActionEvent(
        user_id="user-1",
        mode="ai_story",
        match_id="match-1",
        stage_id="stage-1",
        turn_number=1,
        action_code="guard",
        info_target_key=None,
        decision_duration_ms=18000,
        sanity_before=4,
        ritual_power_before=3,
        curse_marks_before=0,
        opponent_action_code="curse",
        result_code="curse_damage_blocked",
        acquired_clue_id=None,
        clue_truth_state=None,
        match_outcome=None,
    )

    turn_snapshot = calculate_style_snapshot(user_id="user-1", events=(event,))
    final_snapshot = recalculate_final_style_snapshot(user_id="user-1", events=(event,))

    assert turn_snapshot.user_id == "user-1"
    assert turn_snapshot.metrics.defense == 1.0
    assert turn_snapshot.metrics.crisis_guard_rate == 1.0
    assert final_snapshot == turn_snapshot
    assert AI_PROFILE_PERSONAL_DATA_MODELS == (
        "PlayerActionEvent",
        "StyleMetricSnapshot",
    )


def test_match_submit_persists_ai_profile_event_from_turn_started_at_boundary():
    matches_source = _read(BACKEND_DIR / "apps" / "matches" / "services.py")
    submit_source = matches_source.split("def submit_match_turn(", maxsplit=1)[1].split(
        "\n\ndef _match_result(",
        maxsplit=1,
    )[0]

    assert "from backend.apps.ai_profile import services as ai_profile_services" in matches_source
    assert "decision_duration_ms=_decision_duration_ms(" in submit_source
    assert "started_at=turn.started_at" in submit_source
    assert "submitted_at=now" in submit_source
    assert "stage_id=1" in submit_source
    assert "ai_profile_services.persist_turn_action_event(" in submit_source
    assert "ai_profile_services.persist_style_snapshot(" in submit_source
    assert "ai_profile_services.persist_final_style_snapshot(" in submit_source


def test_ai_profile_services_define_persistence_helpers_without_llm_dependency():
    services_source = _read(AI_PROFILE_DIR / "services.py")

    assert "def persist_turn_action_event(" in services_source
    assert "def persist_style_snapshot(" in services_source
    assert "def persist_final_style_snapshot(" in services_source
    assert "PlayerActionEvent.objects.create(" in services_source
    assert "StyleMetricSnapshot.objects.create(" in services_source
    assert "llm" not in services_source.lower()
