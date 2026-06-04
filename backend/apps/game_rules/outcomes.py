from dataclasses import dataclass
from enum import Enum


MAX_AI_STORY_TURNS = 12


class OutcomeStatus(Enum):
    IN_PROGRESS = "in_progress"
    WIN = "win"
    LOSS = "loss"


class OutcomeReason(Enum):
    NONE = "none"
    SEAL_SUCCESS = "seal_success"
    SANITY_ZERO = "sanity_zero"
    CURSE_MARKS_LOSS = "curse_marks_loss"
    TURN_LIMIT = "turn_limit"


@dataclass(frozen=True)
class StoryOutcome:
    status: OutcomeStatus
    reason: OutcomeReason


def determine_ai_story_outcome(
    *,
    seal_succeeded: bool,
    player_sanity: int,
    curse_marks_loss_triggered: bool,
    turn_number: int,
) -> StoryOutcome:
    if seal_succeeded:
        return StoryOutcome(
            status=OutcomeStatus.WIN,
            reason=OutcomeReason.SEAL_SUCCESS,
        )

    if player_sanity <= 0:
        return StoryOutcome(
            status=OutcomeStatus.LOSS,
            reason=OutcomeReason.SANITY_ZERO,
        )

    if curse_marks_loss_triggered:
        return StoryOutcome(
            status=OutcomeStatus.LOSS,
            reason=OutcomeReason.CURSE_MARKS_LOSS,
        )

    if turn_number >= MAX_AI_STORY_TURNS:
        return StoryOutcome(
            status=OutcomeStatus.LOSS,
            reason=OutcomeReason.TURN_LIMIT,
        )

    return StoryOutcome(
        status=OutcomeStatus.IN_PROGRESS,
        reason=OutcomeReason.NONE,
    )

