from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class WeightAdjustment:
    action: str
    amount: int


@dataclass(frozen=True)
class StyleAdjustmentRule:
    window: int
    actions: tuple[str, ...]
    minimum_count: int
    adjustments: tuple[WeightAdjustment, ...]


MIRROR_GUEST_BASE_WEIGHTS = {
    "trick": 25,
    "silence": 25,
    "insight": 15,
    "contract": 15,
    "curse": 10,
    "guard": 10,
    "seal": 0,
}
MIRROR_GUEST_BASE_WEIGHTS = MappingProxyType(MIRROR_GUEST_BASE_WEIGHTS)

MIRROR_GUEST_TIE_BREAK_ORDER = (
    "silence",
    "trick",
    "contract",
    "insight",
    "curse",
    "guard",
)

MIRROR_GUEST_STYLE_START_COMPLETED_TURNS = 3

MIRROR_GUEST_STYLE_ADJUSTMENT_RULES = (
    StyleAdjustmentRule(
        window=3,
        actions=("insight",),
        minimum_count=2,
        adjustments=(
            WeightAdjustment(action="trick", amount=20),
            WeightAdjustment(action="curse", amount=5),
        ),
    ),
    StyleAdjustmentRule(
        window=3,
        actions=("guard", "silence"),
        minimum_count=2,
        adjustments=(
            WeightAdjustment(action="silence", amount=15),
            WeightAdjustment(action="contract", amount=15),
        ),
    ),
    StyleAdjustmentRule(
        window=4,
        actions=("contract",),
        minimum_count=2,
        adjustments=(
            WeightAdjustment(action="insight", amount=25),
            WeightAdjustment(action="curse", amount=5),
        ),
    ),
)

MIRROR_GUEST_TIMEOUT_STRONG_PATTERN_THRESHOLD = 3
MIRROR_GUEST_TIMEOUT_DEFAULT_PRIORITY_ACTION = "silence"
MIRROR_GUEST_TIMEOUT_AFTER_SILENCE_PRIORITY_ACTION = "trick"
