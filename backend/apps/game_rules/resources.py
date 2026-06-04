from dataclasses import dataclass, replace


DEFAULT_SANITY = 12
DEFAULT_RITUAL_POWER = 3
DEFAULT_CURSE_MARKS = 0
DEFAULT_SECRET_EXPOSURE = 0
DEFAULT_TRUE_NAME_FRAGMENTS = 0
DEFAULT_INCOMPLETE_TRUE_NAME_FRAGMENTS = 0
DEFAULT_SUSPICION = 0
DEFAULT_FALSE_CLUES = 0
DEFAULT_SHIELD = 0

MAX_SANITY = 12
MAX_RITUAL_POWER = 5
MAX_CURSE_MARKS = 5
MAX_SECRET_EXPOSURE = 3
MAX_TRUE_NAME_FRAGMENTS = 3
MAX_INCOMPLETE_TRUE_NAME_FRAGMENTS = 1
MAX_SUSPICION = 3
MAX_FALSE_CLUES = 3
MAX_SHIELD = 1

FALSE_CLUE_BASE_SUCCESS_RATE = 0.5
FALSE_CLUE_SUSPICION_BONUS = 0.1
FALSE_CLUE_MAX_SUCCESS_RATE = 0.8
SHIELD_CURSE_DAMAGE_BLOCK = 2
INCOMPLETE_FRAGMENTS_PER_TRUE_NAME = 2


@dataclass(frozen=True)
class ResourceState:
    sanity: int
    ritual_power: int
    curse_marks: int
    secret_exposure: int
    true_name_fragments: int
    incomplete_true_name_fragments: int
    suspicion: int
    false_clues: int
    shield: int

    @classmethod
    def initial(cls) -> "ResourceState":
        return cls(
            sanity=DEFAULT_SANITY,
            ritual_power=DEFAULT_RITUAL_POWER,
            curse_marks=DEFAULT_CURSE_MARKS,
            secret_exposure=DEFAULT_SECRET_EXPOSURE,
            true_name_fragments=DEFAULT_TRUE_NAME_FRAGMENTS,
            incomplete_true_name_fragments=DEFAULT_INCOMPLETE_TRUE_NAME_FRAGMENTS,
            suspicion=DEFAULT_SUSPICION,
            false_clues=DEFAULT_FALSE_CLUES,
            shield=DEFAULT_SHIELD,
        )

    def replace(self, **changes: int) -> "ResourceState":
        return replace(self, **changes)


def add_incomplete_true_name_fragment(state: ResourceState) -> ResourceState:
    if state.true_name_fragments >= MAX_TRUE_NAME_FRAGMENTS:
        return state

    next_incomplete = state.incomplete_true_name_fragments + 1
    if next_incomplete < INCOMPLETE_FRAGMENTS_PER_TRUE_NAME:
        return state.replace(
            incomplete_true_name_fragments=min(
                next_incomplete,
                MAX_INCOMPLETE_TRUE_NAME_FRAGMENTS,
            ),
        )

    return state.replace(
        true_name_fragments=min(
            state.true_name_fragments + 1,
            MAX_TRUE_NAME_FRAGMENTS,
        ),
        incomplete_true_name_fragments=0,
    )


def add_suspicion(state: ResourceState, *, amount: int = 1) -> ResourceState:
    return state.replace(
        suspicion=_clamp(state.suspicion + amount, minimum=0, maximum=MAX_SUSPICION),
    )


def false_clue_detection_success_rate(state: ResourceState) -> float:
    rate = FALSE_CLUE_BASE_SUCCESS_RATE + (
        min(state.suspicion, MAX_SUSPICION) * FALSE_CLUE_SUSPICION_BONUS
    )
    return min(rate, FALSE_CLUE_MAX_SUCCESS_RATE)


def add_false_clue(state: ResourceState) -> ResourceState:
    return state.replace(
        false_clues=_clamp(
            state.false_clues + 1,
            minimum=0,
            maximum=MAX_FALSE_CLUES,
        ),
    )


def remove_false_clue(state: ResourceState) -> ResourceState:
    return state.replace(
        false_clues=_clamp(
            state.false_clues - 1,
            minimum=0,
            maximum=MAX_FALSE_CLUES,
        ),
    )


def add_ritual_power(state: ResourceState, *, amount: int = 1) -> ResourceState:
    return state.replace(
        ritual_power=_clamp(
            state.ritual_power + amount,
            minimum=0,
            maximum=MAX_RITUAL_POWER,
        ),
    )


def add_shield(state: ResourceState) -> ResourceState:
    return state.replace(
        shield=_clamp(state.shield + 1, minimum=0, maximum=MAX_SHIELD),
    )


def consume_shield_against_curse_damage(
    state: ResourceState,
    *,
    damage: int,
) -> tuple[ResourceState, int]:
    if state.shield <= 0:
        return state, damage

    remaining_damage = max(damage - SHIELD_CURSE_DAMAGE_BLOCK, 0)
    return state.replace(shield=0), remaining_damage


def expire_unused_shield_at_turn_end(state: ResourceState) -> ResourceState:
    return state.replace(shield=0)


def _clamp(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))
