MVP_STORY_MAX_TURNS = 12

MIRROR_GUEST_CASE_ID = "mirror_guest"
MIRROR_GUEST_TITLE = "거울 속의 손님"
MIRROR_GUEST_SUMMARY = "거울을 통해 사람의 기억을 훔치는 괴이."

APPROVED_MVP_STORY_CASE_SUMMARIES = (
    {
        "case_id": MIRROR_GUEST_CASE_ID,
        "title": MIRROR_GUEST_TITLE,
        "summary": MIRROR_GUEST_SUMMARY,
        "difficulty": "mvp_01",
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

APPROVED_MVP_STORY_CASE_BRIEFINGS = {
    MIRROR_GUEST_CASE_ID: APPROVED_MIRROR_GUEST_BRIEFING,
}
