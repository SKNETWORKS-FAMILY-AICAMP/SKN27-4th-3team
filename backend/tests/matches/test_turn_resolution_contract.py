from datetime import UTC, datetime, timedelta
import importlib
import importlib.util
from pathlib import Path

from backend.apps.common.errors import API_ERROR_MESSAGES, ApiError
from backend.apps.game_rules.matchups import get_matchup_result
from backend.apps.game_rules.outcomes import OutcomeReason, OutcomeStatus
from backend.apps.game_rules.resources import ResourceState


ROOT_DIR = Path(__file__).resolve().parents[3]
RESOLUTION_MODULE_PATH = ROOT_DIR / "backend" / "apps" / "matches" / "resolution.py"


def _resolution_module():
    spec = importlib.util.find_spec("backend.apps.matches.resolution")
    assert spec is not None, "matches resolution service module must exist"
    return importlib.import_module("backend.apps.matches.resolution")


def _deadline_pair():
    deadline_at = datetime(2026, 6, 4, 12, 0, 0, tzinfo=UTC)
    return deadline_at, deadline_at + timedelta(seconds=1)


def test_submission_after_deadline_returns_official_turn_deadline_error():
    resolution = _resolution_module()
    deadline_at, submitted_at = _deadline_pair()

    error = resolution.validate_submission_deadline(
        deadline_at=deadline_at,
        submitted_at=submitted_at,
    )

    assert isinstance(error, ApiError)
    assert error.code == "TURN_DEADLINE_EXPIRED"
    assert error.message == API_ERROR_MESSAGES["TURN_DEADLINE_EXPIRED"]


def test_missing_submission_after_deadline_resolves_player_action_as_silence():
    resolution = _resolution_module()
    deadline_at, server_time = _deadline_pair()

    result = resolution.resolve_ai_story_turn(
        turn_id="turn-1",
        turn_number=2,
        deadline_at=deadline_at,
        server_time=server_time,
        player_action_code=None,
        opponent_action_code="trick",
        player_timeout_count=2,
        player_state=ResourceState.initial(),
        seal_condition_met=False,
        curse_marks_loss_triggered=False,
    )

    assert result.player_action_code == "silence"
    assert result.timeout_applied is True
    assert result.player_timeout_count == 3
    assert result.turn_status == "timed_out"
    assert result.public_log == get_matchup_result("silence", "trick").public_log


def test_turn_resolution_uses_game_rules_matchup_result_and_public_log():
    resolution = _resolution_module()
    deadline_at, _server_time = _deadline_pair()
    expected_matchup = get_matchup_result("curse", "guard")

    result = resolution.resolve_ai_story_turn(
        turn_id="turn-2",
        turn_number=3,
        deadline_at=deadline_at,
        server_time=deadline_at - timedelta(seconds=1),
        player_action_code="curse",
        opponent_action_code="guard",
        player_timeout_count=0,
        player_state=ResourceState.initial(),
        seal_condition_met=False,
        curse_marks_loss_triggered=False,
    )

    assert result.timeout_applied is False
    assert result.turn_status == "resolved"
    assert result.matchup_result == expected_matchup
    assert result.effect_codes == expected_matchup.effect_codes
    assert result.public_log == expected_matchup.public_log


def test_seal_success_takes_priority_over_simultaneous_loss_in_resolution():
    resolution = _resolution_module()
    deadline_at, _server_time = _deadline_pair()

    result = resolution.resolve_ai_story_turn(
        turn_id="turn-3",
        turn_number=12,
        deadline_at=deadline_at,
        server_time=deadline_at - timedelta(seconds=1),
        player_action_code="seal",
        opponent_action_code="curse",
        player_timeout_count=0,
        player_state=ResourceState.initial().replace(sanity=0),
        seal_condition_met=True,
        curse_marks_loss_triggered=True,
    )

    assert result.seal_succeeded is True
    assert result.match_outcome.status == OutcomeStatus.WIN
    assert result.match_outcome.reason == OutcomeReason.SEAL_SUCCESS


def test_resolution_module_does_not_add_unapproved_llm_rag_or_fear_logic():
    assert RESOLUTION_MODULE_PATH.exists()
    source = RESOLUTION_MODULE_PATH.read_text(encoding="utf-8").lower()

    assert "llm" not in source
    assert "rag" not in source
    assert "embedding" not in source
    assert "fear" not in source
    assert "공포" not in source
