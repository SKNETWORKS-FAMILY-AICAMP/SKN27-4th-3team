"""LLM purpose별 실제 실행 프롬프트 템플릿."""

from __future__ import annotations

from typing import Any


SUPPORTED_PURPOSES = {"result_summary", "turn_flavor_text", "style_summary", "match_log_summary"}


def join_story_result_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value or "")


# 결과 요약이 입력에 없는 사건을 만들지 않도록 공개 로그를 짧은 근거 목록으로 변환한다.
def format_result_turn_logs(turn_logs: list[dict[str, Any]]) -> str:
    if not turn_logs:
        return "제공된 턴 공개 로그 없음"

    lines = []
    for index, item in enumerate(turn_logs, start=1):
        turn_number = item.get("turn_number", item.get("turn", index))
        text = item.get("text", item.get("message", item.get("public_log", "")))
        log_key = item.get("log_key")
        suffix = f" ({log_key})" if log_key else ""
        lines.append(f"- {turn_number}턴: {text}{suffix}")
    return "\n".join(lines)


def build_generation_input(payload: dict[str, Any]) -> dict[str, Any]:
    purpose = payload["purpose"]
    if purpose == "result_summary":
        return build_result_summary_input(payload)
    if purpose == "turn_flavor_text":
        return build_turn_flavor_text_input(payload)
    if purpose == "style_summary":
        return build_style_summary_input(payload)
    if purpose == "match_log_summary":
        return build_match_log_summary_input(payload)
    raise ValueError(f"지원하지 않는 purpose입니다: {purpose}")


def base_system_prompt(extra: str) -> str:
    return "\n".join(
        [
            "너는 게임 판정자가 아니라 서버 판정 이후의 보조 기록자다.",
            "서버가 확정한 결과만 사용해 한국어로 작성한다.",
            "승패, 수치 변화, 진명 조각 획득, 거짓 단서 판정은 새로 판단하지 않는다.",
            "공식 설정이나 룰을 추가하지 않고, 입력에 없는 사실을 만들지 않는다.",
            "데모 스토리 참고 문서는 분위기 참고용이며 입력에 없는 인물명, 사건명, 과거사를 생성하지 않는다.",
            "출력 문장에 사용할 수 있는 고유명사는 입력에 직접 등장한 것만 사용한다.",
            "출력은 요청된 문구만 작성하고 해설, 사과, 선택지, 제목을 붙이지 않는다.",
            extra,
        ]
    )


def apparition_persona_prompt() -> str:
    return "\n".join(
        [
            "괴이 반응 문구가 필요할 때의 페르소나 기준:",
            "- 피티는 단순한 악당이 아니라 이름과 목소리를 빼앗긴 상처의 잔향처럼 다룬다.",
            "- 말투는 낮고 조용하며, 원망과 외로움이 섞인 속삭임에 가깝다.",
            "- 직접적인 협박보다 거울, 침묵, 먼지, 금속 냄새, 식은 손끝 같은 감각으로 압박한다.",
            "- 아이 같은 여린 감각과 오래된 분노가 함께 느껴지게 하되, 과거사를 새로 설명하지 않는다.",
            "- 피, 살인, 처벌 같은 노골적인 폭력보다 기억, 이름, 입술, 시선, 어둠의 이미지를 우선한다.",
            "- 괴이를 처치 대상처럼 단정하지 말고, 봉인과 해방 사이에 걸린 존재처럼 표현한다.",
        ]
    )


def build_result_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    match_result = payload["match_result"]
    resources = match_result["final_resources"]
    story_result_text = join_story_result_text(match_result.get("story_result_text"))
    turn_logs_text = format_result_turn_logs(match_result.get("turn_logs", []))
    user_prompt = f"""아래 서버 결과를 바탕으로 결과 화면용 서사 요약을 작성해줘.

[사건]
{match_result["case"]["title"]}

[서버 판정]
- 결과: {match_result["result"]}
- 종료 사유: {match_result["result_reason"]}
- 최종 이성: {resources["sanity"]}
- 최종 의식력: {resources["ritual_power"]}
- 최종 저주 흔적: {resources["curse_marks"]}
- 획득한 진명 조각 수: {resources["true_name_fragments"]}
- 턴 수: {len(match_result.get("turn_logs", []))}

[정적 fallback 문장]
{story_result_text}

[서버 공개 로그 근거]
{turn_logs_text}

[금지]
- 승패를 바꾸지 않는다.
- 수치와 단서 상태를 새로 판단하지 않는다.
- 공식 설정을 추가하지 않는다.
- 공개 로그 근거에 없는 행동, 장소, 인물, 원인을 추가하지 않는다.
- fallback 문장의 결말과 반대되는 분위기를 만들지 않는다.

문체 기준:
- 차분한 3인칭 서술로 작성한다.
- 숫자를 반복하지 말고 결과의 정서를 요약한다.
- 과장된 감탄이나 설명문 투를 피한다.

출력은 2~4문장으로 작성한다."""
    return {
        "purpose": "result_summary",
        "system_prompt": base_system_prompt("세계관 톤은 어둡고 절제된 미스터리 분위기를 유지한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


def build_style_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["style_summary"]["metrics"]
    user_prompt = f"""아래 스타일 지표를 바탕으로 플레이 스타일 요약을 작성해줘.

[스타일 지표]
- 공격성: {metrics["aggression"]}
- 방어성: {metrics["defense"]}
- 정보 집중: {metrics["insight_focus"]}
- 기만성: {metrics["deception"]}
- 위험 선호: {metrics["risk_preference"]}
- 침묵 의존: {metrics["silence_reliance"]}
- 위기 방어율: {metrics["crisis_guard_rate"]}
- 위기 계약율: {metrics["crisis_contract_rate"]}
- 늦은 선택률: {metrics["late_choice_rate"]}

[금지]
- 지표를 새로 계산하지 않는다.
- 플레이어의 실제 성격을 단정하지 않는다.
- 승패 원인을 LLM이 판정하지 않는다.
- 입력 지표에 없는 행동명이나 사건명을 새로 만들지 않는다.
- 비난, 조롱, 낙인 표현을 쓰지 않는다.

문체 기준:
- 사람 자체가 아니라 게임 안의 선택 경향만 말한다.
- “경향”, “흐름”, “선택” 같은 관찰 표현을 사용한다.
- 숫자는 출력하지 않는다.

출력은 1~2문장으로 작성한다."""
    return {
        "purpose": "style_summary",
        "system_prompt": base_system_prompt("플레이어를 비난하지 않고, 관찰 가능한 경향만 차분하게 표현한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


def build_turn_flavor_text_input(payload: dict[str, Any]) -> dict[str, Any]:
    turn_result = payload["turn_result"]
    player_action = turn_result["player_action"]
    public_log = turn_result["public_log"]
    user_prompt = f"""아래 서버 턴 결과를 바탕으로 화면에 표시할 짧은 연출 문구를 작성해줘.

[턴 정보]
- turn_number: {turn_result["turn_number"]}
- apparition_alias: {payload.get("apparition_alias")}
- action_code: {player_action["code"]}
- info_target_key: {player_action.get("info_target_key")}
- effect_code: {turn_result.get("effect_code")}
- match_outcome: {turn_result["match_outcome"]}
- timeout_applied: {player_action.get("timeout_applied")}

[서버 공개 로그]
{public_log["text"]}

[표시 위치]
{payload.get("display_slot")}

[금지]
- 서버 공개 로그의 의미를 바꾸지 않는다.
- 행동 성공/실패를 새로 판단하지 않는다.
- 단서 획득 여부나 진위를 새로 말하지 않는다.
- 공개 로그에 없는 고유명사, 장소명, 대상명을 추가하지 않는다.
- 다음 괴이 행동을 예고하지 않는다.
- 안내문처럼 설명하지 않는다.
- 질문형이나 추측형으로 쓰지 않는다.
- 공개 로그에 없는 비밀, 단서, 진실을 덧붙이지 않는다.
- 공개 로그에 없는 파괴, 소유, 원인 관계를 덧붙이지 않는다.

[문체]
- 서버 공개 로그의 핵심 명사와 감각을 유지한다.
- 새 사건을 만들지 말고 빛, 소리, 시선, 냉기 같은 감각만 덧댄다.
- 괴이 이름은 apparition_alias가 있을 때만 짧게 사용할 수 있다.
- display_slot이 괴이 반응 위치이면 피티의 페르소나 기준을 따른다.
- display_slot이 `right_apparition_message`이면 짧은 1인칭/2인칭 속삭임처럼 쓸 수 있다.
- 프론트 화면에서는 `right_apparition_message`가 LLM 우선 적용 위치다.
- display_slot이 시스템 위치이면 괴이가 직접 말하기보다 장면 묘사로 쓴다.
- “발견되었습니다”, “제공합니다” 같은 안내문 투를 쓰지 않는다.
- “드러났다”, “밝혀졌다”처럼 판정처럼 보이는 표현을 남발하지 않는다.
- 반드시 현재 서버 공개 로그에 나온 명사를 중심으로 새로 작성한다.
- 최종 출력에는 `공개 로그`, `출력`, `예시` 같은 라벨을 넣지 않는다.
- `무엇인가`, `누군가`, `보이기 시작했다`처럼 새 존재를 암시하지 않는다.
- “온도에 뜨거움을 더했다”, “온도는 식었다”처럼 추상적인 설명문을 쓰지 않는다.
- “냄새가 났다”처럼 막연한 감각 표현보다 `금속 냄새`, `식은 손끝`처럼 구체적으로 쓴다.
- 가능하면 공개 로그를 간결하게 다시 쓰고, 감각 묘사는 한 가지만 덧댄다.

[나쁜 출력]
- 거울 속 비밀이 드러났다.
- 다음 턴, 피티가 저주를 속삭인다.
- 이 행동은 단서를 제공합니다.
- 예시 문장을 현재 턴과 무관하게 그대로 복사한다.
- 거울 속에 무엇인가가 보이기 시작했다.
- 그것은 온도에 뜨거움을 더했다.
- 온도는 식었다.
- 냄새가 났다.

출력은 1~2줄로 작성한다.
따옴표, 번호, markdown 없이 문구만 출력한다.
전체 10~60자로 작성한다.
각 줄은 40자 이하로 작성한다."""
    return {
        "purpose": "turn_flavor_text",
        "system_prompt": base_system_prompt(
            "\n".join(
                [
                    "문장은 짧고 어둡게, 게임 UI 위에 얹히는 속삭임처럼 작성한다.",
                    apparition_persona_prompt(),
                ]
            )
        ),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


def build_match_log_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    log_lines = []
    for item in payload.get("turn_logs", []):
        log_lines.append(
            "- {turn}턴: player_action={player_action}, info_target_key={info_target_key}, "
            "match_outcome={match_outcome}, public_log={public_log}".format(**item)
        )
    user_prompt = f"""아래 매치 로그를 운영자 확인용으로 요약해줘.

[매치 정보]
- match_id: {payload["match_id"]}
- case_id: {payload["case_id"]}
- 결과: {payload["result"]}
- 종료 사유: {payload["result_reason"]}
- 턴 수: {payload["turn_count"]}
- 시간초과 횟수: {payload["timeout_count"]}

[주요 로그]
{chr(10).join(log_lines)}

[금지]
- 서버 판정을 바꾸지 않는다.
- 로그에 없는 행동이나 원인을 만들지 않는다.
- 로그에 없는 인물명, 장소명, 단서명을 추가하지 않는다.
- result, result_reason enum을 임의로 한국어 번역하지 않는다.
- `seal_success`를 설명해야 하면 입력 공개 로그의 표현을 쓰거나 `seal_success` 그대로 쓴다.
- 보상, 랭킹, 매칭 판단을 하지 않는다.
- 운영 제안이나 개선안을 쓰지 않는다.

문체 기준:
- 각 줄은 관찰된 턴 흐름 하나만 요약한다.
- 추측 대신 공개 로그에 있는 사건만 압축한다.
- 운영자가 빠르게 훑을 수 있게 건조하게 쓴다.

출력은 핵심 흐름 3~5줄로 작성한다."""
    return {
        "purpose": "match_log_summary",
        "system_prompt": base_system_prompt("문장은 간결하고 운영자가 검토하기 쉽게 작성한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }
