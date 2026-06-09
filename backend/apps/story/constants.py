MVP_STORY_MAX_TURNS = 12
PLAYER_DISPLAY_NAME_MAX_LENGTH = 24
DEFAULT_REQUIRED_TRUE_NAME_FRAGMENTS_FOR_SEAL = 3
NAMELESS_CURSE_REQUIRED_TRUE_NAME_FRAGMENTS_FOR_SEAL = 2
MIRROR_GUEST_DUEL_WIN_CONDITION = "seal_apparition"
NAMELESS_CURSE_DUEL_WIN_CONDITION = "recover_piti_true_name"

MIRROR_GUEST_CASE_ID = "mirror_guest"
MIRROR_GUEST_TITLE = "거울 속의 손님"
MIRROR_GUEST_SUMMARY = "거울을 통해 사람의 기억을 훔치는 괴이."
MIRROR_GUEST_APPARITION_ID = 1

NAMELESS_CURSE_CASE_ID = "nameless_curse"
NAMELESS_CURSE_TITLE = "무명(無名)의 저주"
NAMELESS_CURSE_SUMMARY = "이름을 빼앗긴 원혼과 진실의 거울을 마주하는 사건."
NAMELESS_CURSE_APPARITION_ALIAS = "피티"
NAMELESS_CURSE_PUBLIC_APPARITION_DISPLAY_NAME = "거울 속 목소리"
NAMELESS_CURSE_APPARITION_ID = 2

APPROVED_MVP_STORY_CASE_SUMMARIES = (
    {
        "case_id": MIRROR_GUEST_CASE_ID,
        "title": MIRROR_GUEST_TITLE,
        "summary": MIRROR_GUEST_SUMMARY,
        "difficulty": "mvp_01",
        "mvp_available": True,
        "estimated_turns": MVP_STORY_MAX_TURNS,
    },
    {
        "case_id": NAMELESS_CURSE_CASE_ID,
        "title": NAMELESS_CURSE_TITLE,
        "summary": NAMELESS_CURSE_SUMMARY,
        "difficulty": "mvp_02",
        "mvp_available": True,
        "estimated_turns": MVP_STORY_MAX_TURNS,
    },
)

APPROVED_MIRROR_GUEST_BRIEFING = {
    "case_id": MIRROR_GUEST_CASE_ID,
    "title": MIRROR_GUEST_TITLE,
    "apparition_alias": MIRROR_GUEST_TITLE,
    "briefing_text": [
        "사건 파일 01. 거울 속의 손님.",
        "오래된 방의 거울은 얼굴을 비추지 않는다.",
        "그 안에는 잊힌 기억, 사라진 목소리, 그리고 네가 잃어버린 방 번호가 남아 있다.",
        "같은 것을 두 번 묻지 마라.",
        "첫 번째 대답은 단서일 수 있다.",
        "두 번째 대답은 함정이다.",
        "흩어진 진명 조각을 모아라.",
        "이름을 완성하기 전에는, 거울 너머의 것을 봉인할 수 없다.",
    ],
    "taboo": {
        "title": "같은 질문 반복 금지",
        "description": "같은 정보 대상을 연속으로 조사하면 금기 위반으로 판정한다.",
    },
    "info_targets": [
        {"key": "mirror_surface", "display_name": "거울 표면"},
        {"key": "mirror_back", "display_name": "깨진 거울 뒷면"},
        {"key": "missing_child_voice", "display_name": "사라진 아이의 목소리"},
        {"key": "forgotten_room", "display_name": "잊어버린 방 번호"},
        {"key": "self_reflection", "display_name": "플레이어의 비친 얼굴"},
    ],
    "max_turns": MVP_STORY_MAX_TURNS,
}

APPROVED_NAMELESS_CURSE_BRIEFING = {
    "case_id": NAMELESS_CURSE_CASE_ID,
    "title": NAMELESS_CURSE_TITLE,
    "apparition_alias": NAMELESS_CURSE_PUBLIC_APPARITION_DISPLAY_NAME,
    "briefing_text": [
        "사건 파일 02. 무명(無名)의 저주.",
        "안개가 걷히지 않는 저택에는 이름을 빼앗긴 목소리가 남아 있다.",
        "진실의 거울은 얼굴이 아니라, 숨겨진 이름과 상처를 되비춘다.",
        "거울 속 목소리를 처치 대상으로 단정하지 마라.",
        "그 이름을 되찾게 해야 저주의 사슬을 끊을 수 있다.",
    ],
    "taboo": {
        "title": "같은 상처 반복 금지",
        "description": "같은 정보 대상을 연속으로 조사하면 금기 위반으로 판정한다.",
    },
    "info_targets": [
        {"key": "truth_mirror", "display_name": "진실의 거울"},
        {"key": "family_journal", "display_name": "가죽 장정 일기장"},
        {"key": "nameless_thread", "display_name": "무명실"},
        {"key": "basement_wall", "display_name": "지하실 벽"},
        {"key": "self_reflection", "display_name": "플레이어의 비친 얼굴"},
    ],
    "max_turns": MVP_STORY_MAX_TURNS,
}

APPROVED_MVP_STORY_CASE_BRIEFINGS = {
    MIRROR_GUEST_CASE_ID: APPROVED_MIRROR_GUEST_BRIEFING,
    NAMELESS_CURSE_CASE_ID: APPROVED_NAMELESS_CURSE_BRIEFING,
}

APPROVED_MIRROR_GUEST_TRUE_NAME_FRAGMENTS = (
    {
        "id": 1,
        "clue_id": "true_name_fragment_1",
        "text": "깨진 거울의 뒷면에 남은 이름",
        "primary_info_target_key": "mirror_back",
        "required_action_codes": ("insight",),
    },
    {
        "id": 2,
        "clue_id": "true_name_fragment_2",
        "text": "사라진 아이의 마지막 목소리",
        "primary_info_target_key": "missing_child_voice",
        "required_action_codes": ("contract",),
    },
    {
        "id": 3,
        "clue_id": "true_name_fragment_3",
        "text": "플레이어가 잊어버린 자기 방 번호",
        "primary_info_target_key": "forgotten_room",
        "required_action_codes": ("insight", "contract"),
        "minimum_true_name_fragments": 2,
    },
)

APPROVED_MIRROR_GUEST_FALSE_CLUES = (
    {
        "id": 1,
        "clue_id": "false_clue_1",
        "text": "거울을 깨면 끝난다.",
        "trigger_info_target_keys": ("mirror_surface", "mirror_back"),
    },
    {
        "id": 2,
        "clue_id": "false_clue_2",
        "text": "불을 끄면 안전하다.",
        "trigger_info_target_keys": ("missing_child_voice",),
    },
    {
        "id": 3,
        "clue_id": "false_clue_3",
        "text": "이름을 부르면 괴이가 약해진다.",
        "trigger_info_target_keys": ("forgotten_room", "self_reflection"),
        "minimum_true_name_fragments": 2,
    },
)

APPROVED_NAMELESS_CURSE_TRUE_NAME_FRAGMENTS = (
    {
        "id": 1,
        "clue_id": "true_name_fragment_1",
        "text": "일기장에 남은 지워진 이름의 첫 획",
        "primary_info_target_key": "family_journal",
        "required_action_codes": ("insight",),
    },
    {
        "id": 2,
        "clue_id": "true_name_fragment_2",
        "text": "무명실 너머에서 되돌아온 마지막 목소리",
        "primary_info_target_key": "nameless_thread",
        "required_action_codes": ("contract",),
    },
    {
        "id": 3,
        "clue_id": "true_name_fragment_3",
        "text": "진실의 거울이 되돌려 준 피티의 이름",
        "primary_info_target_key": "truth_mirror",
        "required_action_codes": ("insight", "contract"),
        "minimum_true_name_fragments": 2,
    },
)

APPROVED_NAMELESS_CURSE_FALSE_CLUES = (
    {
        "id": 1,
        "clue_id": "false_clue_1",
        "text": "거울을 깨면 끝난다.",
        "trigger_info_target_keys": ("truth_mirror", "self_reflection"),
    },
    {
        "id": 2,
        "clue_id": "false_clue_2",
        "text": "피티는 플레이어의 이름을 빼앗으려 한다.",
        "trigger_info_target_keys": ("nameless_thread", "self_reflection"),
    },
    {
        "id": 3,
        "clue_id": "false_clue_3",
        "text": "피티를 처치해야 저주가 끝난다.",
        "trigger_info_target_keys": ("basement_wall", "family_journal"),
        "minimum_true_name_fragments": 2,
    },
)

APPROVED_MIRROR_GUEST_INFO_TARGET_KEYS = tuple(
    target["key"] for target in APPROVED_MIRROR_GUEST_BRIEFING["info_targets"]
)
APPROVED_NAMELESS_CURSE_INFO_TARGET_KEYS = tuple(
    target["key"] for target in APPROVED_NAMELESS_CURSE_BRIEFING["info_targets"]
)

APPROVED_MIRROR_GUEST_RESULT_TEXT_BY_REASON = {
    "seal_success": (
        "진명 조각이 하나의 이름으로 맞물리자, 거울 속 방은 더 이상 문을 열지 못했다.",
        "피티는 마지막으로 낯선 표정을 남긴 채 유리 안쪽의 어둠으로 밀려났다.",
        "사건 파일은 봉인 완료로 기록된다.",
    ),
    "sanity_zero": (
        "거울은 끝내 당신의 시선을 놓아주지 않았다.",
        "방 안의 소리는 사라졌지만, 유리 너머에서는 여전히 같은 숨이 되돌아왔다.",
        "사건 파일은 정신 붕괴로 인한 봉인 실패로 기록된다.",
    ),
    "curse_marks_loss": (
        "저주의 표식이 모두 새겨진 순간, 거울은 당신의 윤곽을 제 것으로 삼았다.",
        "피티의 이름은 완성되지 못했고, 방은 다시 조용한 기다림으로 돌아갔다.",
        "사건 파일은 저주 침식으로 인한 봉인 실패로 기록된다.",
    ),
    "turn_limit": (
        "마지막 기회가 지나가자 거울 표면은 평범한 어둠처럼 굳어졌다.",
        "그러나 방 한쪽에서는 아직 끝나지 않은 목소리가 아주 낮게 남아 있었다.",
        "사건 파일은 시간 초과로 인한 봉인 실패로 기록된다.",
    ),
    "unresolved": (
        "사건은 아직 결말에 도달하지 않았다.",
        "결과 화면은 매치가 종료된 뒤에만 확정된다.",
    ),
}

APPROVED_NAMELESS_CURSE_RESULT_TEXT_BY_REASON = {
    "seal_success": (
        "피티의 이름이 진실의 거울 앞에서 완성되자, 무명실은 더는 입술을 묶지 못했다.",
        "거울은 깨지지 않았지만, 그 안쪽의 시선은 처음으로 자기 이름을 알아들었다.",
        "사건 파일은 진명 회복과 봉인 완료로 기록된다.",
    ),
    "sanity_zero": (
        "거울은 당신의 이름과 피티의 이름을 같은 숨결로 겹쳐 놓았다.",
        "마지막 호명은 끝내 누구를 위한 것인지 구분되지 않았다.",
        "사건 파일은 자기 인식 붕괴로 인한 봉인 실패로 기록된다.",
    ),
    "curse_marks_loss": (
        "저주의 흔적은 살갗이 아니라 이름의 가장자리에 붙어 번졌다.",
        "피티의 이름은 완성되지 못했고, 거울은 다시 낯선 얼굴을 조용히 받아들였다.",
        "사건 파일은 저주 침식으로 인한 봉인 실패로 기록된다.",
    ),
    "turn_limit": (
        "자정의 마지막 소리가 지나가자 진실의 거울은 은빛 표면을 닫았다.",
        "부르지 못한 이름은 무명실 끝에 매달린 채 방 안에 남았다.",
        "사건 파일은 시간 초과로 인한 봉인 실패로 기록된다.",
    ),
    "unresolved": (
        "사건은 아직 결말에 도달하지 않았다.",
        "결과 화면은 매치가 종료된 뒤에만 확정된다.",
    ),
}

APPROVED_STORY_CASE_DEFINITIONS = {
    MIRROR_GUEST_CASE_ID: {
        "case_id": MIRROR_GUEST_CASE_ID,
        "title": MIRROR_GUEST_TITLE,
        "apparition_alias": MIRROR_GUEST_TITLE,
        "public_apparition_display_name": MIRROR_GUEST_TITLE,
        "apparition_id": MIRROR_GUEST_APPARITION_ID,
        "info_target_keys": APPROVED_MIRROR_GUEST_INFO_TARGET_KEYS,
        "true_name_fragments": APPROVED_MIRROR_GUEST_TRUE_NAME_FRAGMENTS,
        "false_clues": APPROVED_MIRROR_GUEST_FALSE_CLUES,
        "result_text_by_reason": APPROVED_MIRROR_GUEST_RESULT_TEXT_BY_REASON,
        "required_true_name_fragments_for_seal": DEFAULT_REQUIRED_TRUE_NAME_FRAGMENTS_FOR_SEAL,
        "duel_win_condition": MIRROR_GUEST_DUEL_WIN_CONDITION,
    },
    NAMELESS_CURSE_CASE_ID: {
        "case_id": NAMELESS_CURSE_CASE_ID,
        "title": NAMELESS_CURSE_TITLE,
        "apparition_alias": NAMELESS_CURSE_APPARITION_ALIAS,
        "public_apparition_display_name": NAMELESS_CURSE_PUBLIC_APPARITION_DISPLAY_NAME,
        "apparition_id": NAMELESS_CURSE_APPARITION_ID,
        "info_target_keys": APPROVED_NAMELESS_CURSE_INFO_TARGET_KEYS,
        "true_name_fragments": APPROVED_NAMELESS_CURSE_TRUE_NAME_FRAGMENTS,
        "false_clues": APPROVED_NAMELESS_CURSE_FALSE_CLUES,
        "result_text_by_reason": APPROVED_NAMELESS_CURSE_RESULT_TEXT_BY_REASON,
        "required_true_name_fragments_for_seal": NAMELESS_CURSE_REQUIRED_TRUE_NAME_FRAGMENTS_FOR_SEAL,
        "duel_win_condition": NAMELESS_CURSE_DUEL_WIN_CONDITION,
    },
}
