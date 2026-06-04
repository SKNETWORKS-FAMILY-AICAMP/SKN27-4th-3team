from itertools import product
from dataclasses import FrozenInstanceError

from backend.apps.game_rules.matchups import (
    ACTION_CODES,
    MATCHUP_TABLE,
    REPEAT_PREVENTION_HISTORY_SIZE,
    REVEALED_CANDIDATE_COUNT,
    SEAL_INTERFERENCE_BY_OPPONENT_ACTION,
    build_revealed_action_candidates,
    get_matchup_result,
)
from backend.apps.game_rules.policies import (
    MIRROR_GUEST_BASE_WEIGHTS,
    MIRROR_GUEST_STYLE_ADJUSTMENT_RULES,
)


def test_matchup_table_defines_every_approved_7_by_7_combination():
    assert ACTION_CODES == (
        "curse",
        "guard",
        "insight",
        "trick",
        "silence",
        "contract",
        "seal",
    )

    expected_pairs = set(product(ACTION_CODES, ACTION_CODES))

    assert set(MATCHUP_TABLE) == expected_pairs
    for result in MATCHUP_TABLE.values():
        assert result.public_log
        assert result.effect_codes


def test_curse_collision_uses_d6_snapshot_contract():
    result = get_matchup_result("curse", "curse")

    assert result.effect_codes == (
        "actor_sanity:-1",
        "opponent_sanity:-1",
    )
    assert result.random_check == "curse_collision_d6"
    assert result.public_log == (
        "두 저주가 정면으로 부딪혔다. 주사위 결과가 의식의 방향을 갈랐다."
    )


def test_insight_vs_silence_reveals_next_two_apparition_action_candidates():
    result = get_matchup_result("insight", "silence")

    assert result.reveals_next_apparition_candidates is True
    assert result.effect_codes == (
        "clue_gain_failed",
        "reveal_next_apparition_candidates:2",
    )
    assert result.public_log == (
        "침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다."
    )


def test_curse_vs_seal_uses_directional_public_log_from_curse_row():
    result = get_matchup_result("curse", "seal")

    assert result.public_log == (
        "봉인의 문장이 흔들렸다. 저주가 의식의 틈을 물고 늘어졌다."
    )


def test_insight_vs_seal_uses_directional_public_log_from_insight_row():
    result = get_matchup_result("insight", "seal")

    assert result.public_log == (
        "간파가 봉인의 문장을 흔들었다. 의식의 약한 획이 드러났다."
    )


def test_revealed_candidates_use_weights_and_tie_break_without_seal():
    candidates = build_revealed_action_candidates(
        base_weights=MIRROR_GUEST_BASE_WEIGHTS,
        recent_player_actions=(),
        recent_apparition_actions=(),
        completed_turns=0,
        timeout_count=0,
    )

    assert REVEALED_CANDIDATE_COUNT == 2
    assert len(candidates) == REVEALED_CANDIDATE_COUNT
    assert candidates == ("silence", "trick")


def test_revealed_candidates_apply_style_correction_after_three_completed_turns():
    candidates = build_revealed_action_candidates(
        base_weights=MIRROR_GUEST_BASE_WEIGHTS,
        recent_player_actions=("guard", "insight", "insight"),
        recent_apparition_actions=(),
        completed_turns=3,
        timeout_count=0,
    )

    assert candidates == ("trick", "silence")


def test_revealed_candidates_prevent_three_consecutive_apparition_actions():
    candidates = build_revealed_action_candidates(
        base_weights=MIRROR_GUEST_BASE_WEIGHTS,
        recent_player_actions=(),
        recent_apparition_actions=("silence", "silence"),
        completed_turns=0,
        timeout_count=0,
    )

    assert REPEAT_PREVENTION_HISTORY_SIZE == 2
    assert candidates == ("trick", "contract")


def test_timeout_strong_pattern_prioritizes_silence_over_weight_scale():
    base_weights = {
        **MIRROR_GUEST_BASE_WEIGHTS,
        "curse": 2_000,
    }

    candidates = build_revealed_action_candidates(
        base_weights=base_weights,
        recent_player_actions=(),
        recent_apparition_actions=(),
        completed_turns=0,
        timeout_count=3,
    )

    assert candidates[0] == "silence"


def test_timeout_strong_pattern_prioritizes_trick_after_previous_silence():
    base_weights = {
        **MIRROR_GUEST_BASE_WEIGHTS,
        "curse": 2_000,
    }

    candidates = build_revealed_action_candidates(
        base_weights=base_weights,
        recent_player_actions=(),
        recent_apparition_actions=("silence",),
        completed_turns=0,
        timeout_count=3,
    )

    assert candidates[0] == "trick"


def test_seal_interference_contract_is_fixed_by_opponent_action():
    assert SEAL_INTERFERENCE_BY_OPPONENT_ACTION == {
        "trick": 2,
        "contract": 2,
        "curse": 1,
        "insight": 1,
        "silence": 1,
        "guard": 0,
    }


def test_mirror_guest_policy_constants_are_immutable():
    try:
        MIRROR_GUEST_BASE_WEIGHTS["curse"] = 999
    except TypeError:
        pass
    else:
        raise AssertionError("base weight contract should be immutable")

    try:
        MIRROR_GUEST_STYLE_ADJUSTMENT_RULES[0].window = 99
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("style adjustment rule should be immutable")

    try:
        MIRROR_GUEST_STYLE_ADJUSTMENT_RULES[0].adjustments[0].amount = 999
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("style adjustment amount should be immutable")
