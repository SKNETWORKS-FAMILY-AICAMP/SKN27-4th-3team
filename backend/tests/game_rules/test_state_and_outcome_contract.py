from backend.apps.game_rules.outcomes import (
    MAX_AI_STORY_TURNS,
    OutcomeReason,
    OutcomeStatus,
    determine_ai_story_outcome,
)
from backend.apps.game_rules.resources import (
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
    consume_shield_against_curse_damage,
    expire_unused_shield_at_turn_end,
    false_clue_detection_success_rate,
    remove_false_clue,
)


def test_resource_state_defaults_follow_mvp_contract():
    state = ResourceState.initial()

    assert state.sanity == 12
    assert state.ritual_power == 3
    assert state.curse_marks == 0
    assert state.secret_exposure == 0
    assert state.true_name_fragments == 0
    assert state.incomplete_true_name_fragments == 0
    assert state.suspicion == 0
    assert state.false_clues == 0
    assert state.shield == 0


def test_resource_caps_are_explicit_contract_values():
    assert MAX_SANITY == 12
    assert MAX_RITUAL_POWER == 5
    assert MAX_TRUE_NAME_FRAGMENTS == 3
    assert MAX_SUSPICION == 3
    assert MAX_FALSE_CLUES == 3
    assert MAX_SHIELD == 1


def test_incomplete_true_name_fragments_convert_to_one_full_fragment_at_two():
    state = ResourceState.initial()

    state = add_incomplete_true_name_fragment(state)
    assert state.true_name_fragments == 0
    assert state.incomplete_true_name_fragments == 1

    state = add_incomplete_true_name_fragment(state)
    assert state.true_name_fragments == 1
    assert state.incomplete_true_name_fragments == 0


def test_incomplete_true_name_conversion_stops_when_full_fragments_are_complete():
    state = ResourceState.initial().replace(
        true_name_fragments=3,
        incomplete_true_name_fragments=1,
    )

    state = add_incomplete_true_name_fragment(state)

    assert state.true_name_fragments == 3
    assert state.incomplete_true_name_fragments == 1


def test_suspicion_and_false_clue_detection_rate_are_capped():
    state = ResourceState.initial()

    state = add_suspicion(state, amount=5)

    assert state.suspicion == 3
    assert false_clue_detection_success_rate(state) == 0.8


def test_false_clues_are_capped_and_can_be_removed_one_at_a_time():
    state = ResourceState.initial()

    state = add_false_clue(add_false_clue(add_false_clue(add_false_clue(state))))
    assert state.false_clues == 3

    state = remove_false_clue(state)
    assert state.false_clues == 2


def test_ritual_power_and_shield_do_not_exceed_contract_caps():
    state = ResourceState.initial()

    state = add_ritual_power(state, amount=10)
    state = add_shield(add_shield(state))

    assert state.ritual_power == 5
    assert state.shield == 1


def test_shield_blocks_next_curse_damage_two_then_is_consumed():
    state = ResourceState.initial().replace(shield=1)

    state, remaining_damage = consume_shield_against_curse_damage(state, damage=2)

    assert remaining_damage == 0
    assert state.shield == 0


def test_unused_shield_expires_at_turn_end():
    state = ResourceState.initial().replace(shield=1)

    assert expire_unused_shield_at_turn_end(state).shield == 0


def test_seal_success_takes_priority_over_simultaneous_loss_conditions():
    outcome = determine_ai_story_outcome(
        seal_succeeded=True,
        player_sanity=0,
        curse_marks_loss_triggered=True,
        turn_number=MAX_AI_STORY_TURNS,
    )

    assert outcome.status == OutcomeStatus.WIN
    assert outcome.reason == OutcomeReason.SEAL_SUCCESS


def test_loss_is_applied_when_no_seal_success_and_player_sanity_reaches_zero():
    outcome = determine_ai_story_outcome(
        seal_succeeded=False,
        player_sanity=0,
        curse_marks_loss_triggered=False,
        turn_number=3,
    )

    assert outcome.status == OutcomeStatus.LOSS
    assert outcome.reason == OutcomeReason.SANITY_ZERO


def test_turn_limit_loss_is_applied_at_end_of_twelfth_turn_without_seal_success():
    outcome = determine_ai_story_outcome(
        seal_succeeded=False,
        player_sanity=8,
        curse_marks_loss_triggered=False,
        turn_number=MAX_AI_STORY_TURNS,
    )

    assert outcome.status == OutcomeStatus.LOSS
    assert outcome.reason == OutcomeReason.TURN_LIMIT
