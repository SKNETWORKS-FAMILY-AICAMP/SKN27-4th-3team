from dataclasses import dataclass
from typing import Mapping

from backend.apps.game_rules.policies import (
    MIRROR_GUEST_STYLE_ADJUSTMENT_RULES,
    MIRROR_GUEST_STYLE_START_COMPLETED_TURNS,
    MIRROR_GUEST_TIE_BREAK_ORDER,
    MIRROR_GUEST_TIMEOUT_AFTER_SILENCE_PRIORITY_ACTION,
    MIRROR_GUEST_TIMEOUT_DEFAULT_PRIORITY_ACTION,
    MIRROR_GUEST_TIMEOUT_STRONG_PATTERN_THRESHOLD,
)


ACTION_CODES = (
    "curse",
    "guard",
    "insight",
    "trick",
    "silence",
    "contract",
    "seal",
)
REVEALED_CANDIDATE_COUNT = 2
REPEAT_PREVENTION_HISTORY_SIZE = 2
REVEAL_NEXT_APPARITION_CANDIDATES_EFFECT = (
    f"reveal_next_apparition_candidates:{REVEALED_CANDIDATE_COUNT}"
)

SEAL_INTERFERENCE_BY_OPPONENT_ACTION = {
    "trick": 2,
    "contract": 2,
    "curse": 1,
    "insight": 1,
    "silence": 1,
    "guard": 0,
}

_SEAL_EXCLUDED_ACTIONS = frozenset({"seal"})


@dataclass(frozen=True)
class MatchupResult:
    actor_action: str
    opponent_action: str
    effect_codes: tuple[str, ...]
    public_log: str
    random_check: str | None = None
    reveals_next_apparition_candidates: bool = False


def get_matchup_result(actor_action: str, opponent_action: str) -> MatchupResult:
    try:
        return MATCHUP_TABLE[(actor_action, opponent_action)]
    except KeyError as exc:
        raise ValueError(
            f"Unknown approved action matchup: {actor_action!r} vs {opponent_action!r}"
        ) from exc


def build_revealed_action_candidates(
    *,
    base_weights: Mapping[str, int],
    recent_player_actions: tuple[str, ...],
    recent_apparition_actions: tuple[str, ...],
    completed_turns: int,
    timeout_count: int,
) -> tuple[str, str]:
    weights = _candidate_weights(base_weights)
    _apply_style_adjustments(
        weights=weights,
        recent_player_actions=recent_player_actions,
        completed_turns=completed_turns,
    )
    priority_action = _timeout_priority_action(
        recent_apparition_actions=recent_apparition_actions,
        timeout_count=timeout_count,
    )

    excluded_actions = set(_SEAL_EXCLUDED_ACTIONS)
    repeated_action = _three_turn_repeat_candidate(recent_apparition_actions)
    if repeated_action is not None:
        excluded_actions.add(repeated_action)

    ranked_actions = sorted(
        (
            (action, weight)
            for action, weight in weights.items()
            if action not in excluded_actions
        ),
        key=lambda item: (
            item[0] != priority_action,
            -item[1],
            _tie_break_index(item[0]),
        ),
    )

    if len(ranked_actions) < REVEALED_CANDIDATE_COUNT:
        raise ValueError(
            f"At least {REVEALED_CANDIDATE_COUNT} apparition action candidates are required."
        )

    return tuple(
        action
        for action, _weight in ranked_actions[:REVEALED_CANDIDATE_COUNT]
    )


def _candidate_weights(base_weights: Mapping[str, int]) -> dict[str, int]:
    missing_actions = set(ACTION_CODES) - set(base_weights)
    if missing_actions:
        raise ValueError(f"Missing base weights for actions: {sorted(missing_actions)}")

    return {
        action: int(weight)
        for action, weight in base_weights.items()
        if action in ACTION_CODES
    }


def _apply_style_adjustments(
    *,
    weights: dict[str, int],
    recent_player_actions: tuple[str, ...],
    completed_turns: int,
) -> None:
    if completed_turns < MIRROR_GUEST_STYLE_START_COMPLETED_TURNS:
        return

    for rule in MIRROR_GUEST_STYLE_ADJUSTMENT_RULES:
        recent_actions = recent_player_actions[-rule.window :]
        matched_action_count = sum(
            recent_actions.count(action)
            for action in rule.actions
        )
        if matched_action_count < rule.minimum_count:
            continue

        for adjustment in rule.adjustments:
            weights[adjustment.action] += adjustment.amount


def _timeout_priority_action(
    *,
    recent_apparition_actions: tuple[str, ...],
    timeout_count: int,
) -> str | None:
    if timeout_count < MIRROR_GUEST_TIMEOUT_STRONG_PATTERN_THRESHOLD:
        return None

    previous_action = recent_apparition_actions[-1] if recent_apparition_actions else None
    if previous_action == MIRROR_GUEST_TIMEOUT_DEFAULT_PRIORITY_ACTION:
        return MIRROR_GUEST_TIMEOUT_AFTER_SILENCE_PRIORITY_ACTION

    return MIRROR_GUEST_TIMEOUT_DEFAULT_PRIORITY_ACTION


def _three_turn_repeat_candidate(
    recent_apparition_actions: tuple[str, ...],
) -> str | None:
    if len(recent_apparition_actions) < REPEAT_PREVENTION_HISTORY_SIZE:
        return None

    recent_actions = recent_apparition_actions[-REPEAT_PREVENTION_HISTORY_SIZE:]
    if len(set(recent_actions)) == 1:
        return recent_actions[0]

    return None


def _tie_break_index(action: str) -> int:
    try:
        return MIRROR_GUEST_TIE_BREAK_ORDER.index(action)
    except ValueError:
        return len(MIRROR_GUEST_TIE_BREAK_ORDER)


def _result(
    actor_action: str,
    opponent_action: str,
    effect_codes: tuple[str, ...],
    public_log: str,
    *,
    random_check: str | None = None,
    reveals_next_apparition_candidates: bool = False,
) -> MatchupResult:
    return MatchupResult(
        actor_action=actor_action,
        opponent_action=opponent_action,
        effect_codes=effect_codes,
        public_log=public_log,
        random_check=random_check,
        reveals_next_apparition_candidates=reveals_next_apparition_candidates,
    )


MATCHUP_TABLE = {
    ("curse", "curse"): _result(
        "curse",
        "curse",
        ("actor_sanity:-1", "opponent_sanity:-1"),
        "두 저주가 정면으로 부딪혔다. 주사위 결과가 의식의 방향을 갈랐다.",
        random_check="curse_collision_d6",
    ),
    ("curse", "guard"): _result(
        "curse",
        "guard",
        ("curse_damage_blocked", "opponent_shield:+1"),
        "수호가 저주를 받아냈다. 방어자의 주변에 옅은 막이 남았다.",
    ),
    ("curse", "insight"): _result(
        "curse",
        "insight",
        ("opponent_sanity:-2", "clue_gain_failed", "opponent_suspicion:+1"),
        "간파가 완성되기 전에 저주가 파고들었다. 단서는 흐려졌지만 저주의 흔적은 남았다.",
    ),
    ("curse", "trick"): _result(
        "curse",
        "trick",
        ("opponent_sanity:-1", "actor_suspicion:+1"),
        "거짓 기척 사이로 저주가 스쳤다. 완전히 꿰뚫지는 못했지만 흔적은 남았다.",
    ),
    ("curse", "silence"): _result(
        "curse",
        "silence",
        ("opponent_sanity:-2",),
        "침묵은 저주를 막지 못했다. 조용한 의식장에 균열이 번졌다.",
    ),
    ("curse", "contract"): _result(
        "curse",
        "contract",
        ("opponent_sanity:-2", "contract_failed"),
        "계약이 맺어지기 전에 저주가 끼어들었다. 대가는 허공으로 흩어졌다.",
    ),
    ("curse", "seal"): _result(
        "curse",
        "seal",
        ("opponent_sanity:-2", "seal_interference:+1", "seal_success_if_condition_met"),
        "봉인의 문장이 흔들렸다. 저주가 의식의 틈을 물고 늘어졌다.",
    ),
    ("guard", "curse"): _result(
        "guard",
        "curse",
        ("curse_damage_blocked", "actor_shield:+1"),
        "수호가 저주를 받아냈다. 방어자의 주변에 옅은 막이 남았다.",
    ),
    ("guard", "guard"): _result(
        "guard",
        "guard",
        ("no_effect",),
        "두 수호가 빈 의식장을 감쌌지만, 막아낼 저주는 오지 않았다.",
    ),
    ("guard", "insight"): _result(
        "guard",
        "insight",
        ("actor_action_revealed:guard", "true_name_fragment_gain_failed", "actor_no_effect"),
        "간파는 방어의 흔적만 읽어냈다. 진명은 드러나지 않았다.",
    ),
    ("guard", "trick"): _result(
        "guard",
        "trick",
        ("trick_success", "false_clue:+1", "actor_no_effect"),
        "수호는 잘못된 위협을 향했다. 그 틈에 거짓 단서가 의식장에 섞였다.",
    ),
    ("guard", "silence"): _result(
        "guard",
        "silence",
        ("opponent_ritual_power:+1", "actor_no_effect"),
        "수호는 허공을 지켰고, 침묵은 다음 의식을 준비했다.",
    ),
    ("guard", "contract"): _result(
        "guard",
        "contract",
        ("opponent_curse_mark:+1", "opponent_incomplete_true_name_fragment:+1"),
        "수호는 계약을 완전히 막지 못했다. 그러나 새겨진 이름은 아직 온전하지 않았다.",
    ),
    ("guard", "seal"): _result(
        "guard",
        "seal",
        ("seal_interference:+0", "actor_no_effect", "seal_success_if_condition_met"),
        "수호의 막은 봉인의 문장을 막지 못했다. 의식은 계속 이어졌다.",
    ),
    ("insight", "curse"): _result(
        "insight",
        "curse",
        ("actor_sanity:-2", "clue_gain_failed", "actor_suspicion:+1"),
        "간파가 완성되기 전에 저주가 파고들었다. 단서는 흐려졌지만 저주의 흔적은 남았다.",
    ),
    ("insight", "guard"): _result(
        "insight",
        "guard",
        ("opponent_action_revealed:guard", "true_name_fragment_gain_failed", "opponent_no_effect"),
        "간파는 방어의 흔적만 읽어냈다. 진명은 드러나지 않았다.",
    ),
    ("insight", "insight"): _result(
        "insight",
        "insight",
        ("clue_gain_failed:both", "actor_suspicion:+1", "opponent_suspicion:+1"),
        "서로가 서로를 읽으려 했다. 답은 나오지 않았지만 의심만 짙어졌다.",
    ),
    ("insight", "trick"): _result(
        "insight",
        "trick",
        ("false_clue_detection_check", "actor_suspicion_reset:0"),
        "간파가 거짓 기척을 더듬었다. 진실과 속임수 중 하나가 모습을 드러냈다.",
        random_check="false_clue_detection",
    ),
    ("insight", "silence"): _result(
        "insight",
        "silence",
        ("clue_gain_failed", REVEAL_NEXT_APPARITION_CANDIDATES_EFFECT),
        "침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다.",
        reveals_next_apparition_candidates=True,
    ),
    ("insight", "contract"): _result(
        "insight",
        "contract",
        ("contract_failed", "opponent_curse_mark:+2", "actor_incomplete_true_name_fragment:+1"),
        "계약의 빈틈이 드러났다. 맺어지지 못한 대가가 계약자에게 되돌아갔다.",
    ),
    ("insight", "seal"): _result(
        "insight",
        "seal",
        ("seal_interference:+1", "seal_attempt_revealed", "seal_success_if_condition_met"),
        "간파가 봉인의 문장을 흔들었다. 의식의 약한 획이 드러났다.",
    ),
    ("trick", "curse"): _result(
        "trick",
        "curse",
        ("actor_sanity:-1", "opponent_suspicion:+1"),
        "거짓 기척 사이로 저주가 스쳤다. 완전히 꿰뚫지는 못했지만 흔적은 남았다.",
    ),
    ("trick", "guard"): _result(
        "trick",
        "guard",
        ("trick_success", "false_clue:+1", "opponent_no_effect"),
        "수호는 잘못된 위협을 향했다. 그 틈에 거짓 단서가 의식장에 섞였다.",
    ),
    ("trick", "insight"): _result(
        "trick",
        "insight",
        ("false_clue_detection_check", "opponent_suspicion_reset:0"),
        "간파가 거짓 기척을 더듬었다. 진실과 속임수 중 하나가 모습을 드러냈다.",
        random_check="false_clue_detection",
    ),
    ("trick", "trick"): _result(
        "trick",
        "trick",
        ("trick_collision", "false_clue_not_added", "actor_suspicion:+1", "opponent_suspicion:+1"),
        "거짓과 거짓이 겹쳤다. 아무 단서도 남지 않았지만 서로를 향한 의심은 짙어졌다.",
    ),
    ("trick", "silence"): _result(
        "trick",
        "silence",
        ("opponent_ritual_power:+1", "trick_failed", "false_clue_not_added"),
        "속임수는 침묵 속에서 방향을 잃었다. 조용한 쪽만 다음 의식을 준비했다.",
    ),
    ("trick", "contract"): _result(
        "trick",
        "contract",
        ("contract_failed", "opponent_curse_mark:+1", "false_clue:+1"),
        "거짓된 조건이 계약을 더럽혔다. 대가는 맺어지지 않았고 흔적만 남았다.",
    ),
    ("trick", "seal"): _result(
        "trick",
        "seal",
        ("seal_interference:+2", "seal_failed", "false_clue:+1"),
        "거짓 단서가 봉인의 문장을 비틀었다. 의식은 잘못된 이름을 붙잡고 무너졌다.",
    ),
    ("silence", "curse"): _result(
        "silence",
        "curse",
        ("actor_sanity:-2",),
        "침묵은 저주를 막지 못했다. 조용한 의식장에 균열이 번졌다.",
    ),
    ("silence", "guard"): _result(
        "silence",
        "guard",
        ("actor_ritual_power:+1", "opponent_no_effect"),
        "수호는 허공을 지켰고, 침묵은 다음 의식을 준비했다.",
    ),
    ("silence", "insight"): _result(
        "silence",
        "insight",
        ("clue_gain_failed", REVEAL_NEXT_APPARITION_CANDIDATES_EFFECT),
        "침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다.",
        reveals_next_apparition_candidates=True,
    ),
    ("silence", "trick"): _result(
        "silence",
        "trick",
        ("actor_ritual_power:+1", "trick_failed", "false_clue_not_added"),
        "속임수는 침묵 속에서 방향을 잃었다. 조용한 쪽만 다음 의식을 준비했다.",
    ),
    ("silence", "silence"): _result(
        "silence",
        "silence",
        ("actor_ritual_power:+1", "opponent_ritual_power:+1"),
        "아무 말도 오가지 않았다. 그러나 양쪽 모두 다음 의식을 위한 힘을 모았다.",
    ),
    ("silence", "contract"): _result(
        "silence",
        "contract",
        ("contract_success", "true_name_fragment_candidate:+1_or_secret_exposure:+1"),
        "침묵은 계약을 방해하지 못했다. 말 없는 대가가 의식장에 새겨졌다.",
    ),
    ("silence", "seal"): _result(
        "silence",
        "seal",
        ("seal_interference:+1", "seal_success_if_condition_met"),
        "침묵이 봉인의 마지막 음절을 삼켰다. 그래도 문장은 아직 이어질 수 있었다.",
    ),
    ("contract", "curse"): _result(
        "contract",
        "curse",
        ("actor_sanity:-2", "contract_failed"),
        "계약이 맺어지기 전에 저주가 끼어들었다. 대가는 허공으로 흩어졌다.",
    ),
    ("contract", "guard"): _result(
        "contract",
        "guard",
        ("actor_curse_mark:+1", "actor_incomplete_true_name_fragment:+1"),
        "수호는 계약을 완전히 막지 못했다. 그러나 새겨진 이름은 아직 온전하지 않았다.",
    ),
    ("contract", "insight"): _result(
        "contract",
        "insight",
        ("contract_failed", "actor_curse_mark:+2", "opponent_incomplete_true_name_fragment:+1"),
        "계약의 빈틈이 드러났다. 맺어지지 못한 대가가 계약자에게 되돌아갔다.",
    ),
    ("contract", "trick"): _result(
        "contract",
        "trick",
        ("contract_failed", "actor_curse_mark:+1", "false_clue:+1"),
        "거짓된 조건이 계약을 더럽혔다. 대가는 맺어지지 않았고 흔적만 남았다.",
    ),
    ("contract", "silence"): _result(
        "contract",
        "silence",
        ("contract_success", "true_name_fragment_candidate:+1_or_secret_exposure:+1"),
        "침묵은 계약을 방해하지 못했다. 말 없는 대가가 의식장에 새겨졌다.",
    ),
    ("contract", "contract"): _result(
        "contract",
        "contract",
        (
            "partial_contract_success:both",
            "actor_curse_mark:+1",
            "opponent_curse_mark:+1",
            "actor_incomplete_true_name_fragment:+1",
            "opponent_incomplete_true_name_fragment:+1",
        ),
        "두 계약이 서로의 대가를 갉아먹었다. 이름은 완성되지 않았고 흔적만 깊어졌다.",
    ),
    ("contract", "seal"): _result(
        "contract",
        "seal",
        ("seal_interference:+2", "seal_failed", "actor_curse_mark:+1"),
        "계약의 대가가 봉인보다 먼저 도착했다. 문장은 끊어졌고 계약자에게 흔적이 남았다.",
    ),
    ("seal", "curse"): _result(
        "seal",
        "curse",
        ("actor_sanity:-2", "seal_interference:+1", "seal_success_if_condition_met"),
        "저주가 봉인의 문장을 흔들었다. 그러나 이름이 충분하다면 의식은 닫힐 수 있었다.",
    ),
    ("seal", "guard"): _result(
        "seal",
        "guard",
        ("seal_interference:+0", "seal_success_if_condition_met"),
        "수호의 막은 봉인의 문장을 막지 못했다. 의식은 계속 이어졌다.",
    ),
    ("seal", "insight"): _result(
        "seal",
        "insight",
        ("seal_interference:+1", "seal_success_if_condition_met"),
        "간파가 봉인의 약한 획을 건드렸다. 그래도 문장은 아직 완성될 수 있었다.",
    ),
    ("seal", "trick"): _result(
        "seal",
        "trick",
        ("seal_interference:+2", "seal_failed", "false_clue:+1"),
        "거짓 단서가 봉인의 문장을 비틀었다. 의식은 잘못된 이름을 붙잡고 무너졌다.",
    ),
    ("seal", "silence"): _result(
        "seal",
        "silence",
        ("seal_interference:+1", "seal_success_if_condition_met"),
        "침묵이 봉인의 마지막 음절을 삼켰다. 그래도 문장은 아직 이어질 수 있었다.",
    ),
    ("seal", "contract"): _result(
        "seal",
        "contract",
        ("seal_interference:+2", "seal_failed", "opponent_curse_mark:+1"),
        "계약의 대가가 봉인보다 먼저 도착했다. 문장은 끊어졌고 계약자에게 흔적이 남았다.",
    ),
    ("seal", "seal"): _result(
        "seal",
        "seal",
        ("seal_success_if_condition_met", "apparition_seal_unavailable_mvp"),
        "두 봉인의 문장이 동시에 떠올랐다. 조건을 갖춘 쪽의 의식만 완성된다.",
    ),
}
