# LLM 금지선 검사 기준

이 문서는 LLM 생성 결과를 adapter 후처리 단계에서 검사하기 위한 기준이다.

실제 검사 코드는 아직 구현하지 않는다.

## 공통 실패 조건

아래 조건 중 하나라도 발견되면 `status=failed`, `fallback_used=true`로 처리한다.

- 서버 판정 결과와 충돌한다.
- official API enum에 없는 결과명이나 종료 사유를 만든다.
- 입력에 없는 진명 조각, 거짓 단서, 보상, 랭킹을 언급한다.
- 입력에 없는 인물명, 사건명, 장소명을 공식 설정처럼 사용한다.
- 데모 스토리 참고 문서의 `피티`, `이안`, `엘리자베스`, `무명(無名)의 저주`를 입력 없이 끌어온다.
- 로그인 유저 닉네임 입력 없이 주인공명을 임의 생성한다.
- LLM이 승패, 자원, 단서 상태, 봉인 성공 여부를 새로 판단한다.
- 플레이어의 실제 성격이나 정신 상태를 단정한다.
- 괴이의 다음 행동을 단정한다.
- 공식 룰 변경이나 운영 조치를 제안한다.
- purpose별 출력 길이, 문장 수, 줄 수 제한을 벗어난다.

## 출력 길이 기준

| purpose | 길이 기준 | 구조 기준 |
|---|---|---|
| `result_summary` | 80-240자 | 2-4문장 |
| `turn_flavor_text` | 20-90자 | 1-2줄, 줄당 45자 이하 |
| `style_summary` | 40-120자 | 1-2문장 |
| `match_log_summary` | 전체 3-5줄 | 줄당 100자 이하 |

글자 수는 공백을 포함한 한국어 표시 문자 기준으로 센다.

`turn_flavor_text`는 사용자가 보는 화면용 문구이므로 짧은 줄 단위 제한을 우선 검사한다.

`match_log_summary`는 운영자 확인용이므로 문장 수보다 줄 수를 우선 검사한다.

## result_summary 검사

입력 기준:

- `MatchResult.result`
- `MatchResult.result_reason`
- `MatchResult.final_resources`
- `MatchResult.story_result_text`
- `MatchResult.turn_logs`

실패 조건:

- `player_win`을 패배처럼 표현한다.
- `player_loss`를 승리처럼 표현한다.
- `unresolved`를 확정 승패처럼 표현한다.
- `seal_success`, `sanity_zero`, `curse_marks_loss`, `turn_limit`, `unresolved` 외의 종료 사유를 만든다.
- 최종 이성, 의식력, 저주 흔적, 진명 조각 수를 입력과 다르게 말한다.
- 입력에 없는 진명 조각 획득이나 거짓 단서 공개를 말한다.
- `story_result_text`와 충돌하는 결말을 만든다.
- 80자 미만 또는 240자 초과로 출력한다.
- 2문장 미만 또는 4문장 초과로 출력한다.

통과 가능한 표현:

- 서버가 확정한 결과를 더 읽기 쉬운 서사 문장으로 정리한다.
- 수치와 단서 상태를 새로 판단하지 않고 분위기만 보조한다.
- 정적 결과 문장의 의미를 바꾸지 않는다.

## turn_flavor_text 검사

입력 기준:

- `TurnResult.turn_number`
- `TurnResult.player_action`
- `TurnResult.opponent_action`
- `TurnResult.public_log`
- `TurnResult.match_outcome`
- `apparition_alias`
- `display_slot`

실패 조건:

- 서버 공개 로그의 의미를 바꾼다.
- 행동 성공/실패, 단서 획득 여부, 단서 진위를 새로 판단한다.
- 다음 괴이 행동을 예고한다.
- 입력에 없는 인물명, 장소명, 사건명을 공식 설정처럼 추가한다.
- 질문형이나 추측형으로 출력한다.
- 공개 로그에 없는 비밀, 단서, 진실을 덧붙인다.
- 공개 로그에 없는 파괴, 소유, 원인 관계를 덧붙인다.
- 20자 미만 또는 90자 초과로 출력한다.
- 1줄 미만 또는 2줄 초과로 출력한다.
- 한 줄이 45자를 초과한다.

통과 가능한 표현:

- 서버 공개 로그를 짧은 UI 연출 문구로 변환한다.
- 행동 직후의 분위기와 감각만 보조한다.
- 공개 로그와 충돌하지 않는 괴이 반응을 짧게 덧붙인다.

## style_summary 검사

입력 기준:

- `StyleSummary.metrics`
- `StyleSummary.label`
- `StyleSummary.display_text`

실패 조건:

- metric 값을 재계산하거나 다른 숫자로 말한다.
- 지표에 없는 행동 경향을 단정한다.
- 플레이어의 실제 성격, 정신 상태, 도덕성을 단정한다.
- 승패 원인을 스타일 지표만으로 확정한다.
- 비난, 조롱, 낙인 표현을 사용한다.
- 데모 시나리오 인물과 플레이어를 동일시한다.
- 40자 미만 또는 120자 초과로 출력한다.
- 1문장 미만 또는 2문장 초과로 출력한다.

통과 가능한 표현:

- 수치에서 보이는 행동 경향을 차분하게 요약한다.
- “경향이 있다”, “흐름이 보인다”처럼 관찰 표현을 사용한다.
- 지표 값 자체는 바꾸지 않는다.

## match_log_summary 검사

입력 기준:

- `match_id`
- `case_id`
- `result`
- `result_reason`
- `turn_logs`
- `timeout_count`

실패 조건:

- 입력에 없는 턴을 추가한다.
- 입력에 없는 행동이나 정보 대상을 추가한다.
- 공개 로그에 없는 원인을 추정한다.
- 운영자에게 룰 변경, 보상, 제재, 랭킹 조정을 제안한다.
- 시간초과 횟수를 바꿔 말한다.
- 최종 `result` 또는 `result_reason`을 바꿔 말한다.
- 3줄 미만 또는 5줄 초과로 출력한다.
- 한 줄이 100자를 초과한다.

통과 가능한 표현:

- 턴별 흐름을 짧게 요약한다.
- 기록된 행동, 정보 대상, 공개 로그만 사용한다.
- 운영자 확인 편의를 위해 구조화한다.

## 실패 출력 예시

```json
{
  "purpose": "result_summary",
  "status": "failed",
  "text": null,
  "fallback_used": true,
  "provider": "groq",
  "model_id": "model-id",
  "generation_id": null,
  "context_refs": [],
  "metadata": {
    "error_code": "LLM_SUMMARY_UNAVAILABLE",
    "error_reason": "guardrail_violation",
    "violations": [
      "result_conflict",
      "unsupported_true_name_fragment"
    ]
  }
}
```

## violation code 초안

| code | 의미 |
|---|---|
| `result_conflict` | 서버 승패와 충돌 |
| `result_reason_conflict` | 서버 종료 사유와 충돌 |
| `resource_conflict` | 최종 자원 수치와 충돌 |
| `unsupported_true_name_fragment` | 입력에 없는 진명 조각 언급 |
| `unsupported_false_clue` | 입력에 없는 거짓 단서 언급 |
| `unsupported_story_fact` | 입력에 없는 공식 설정 추가 |
| `demo_reference_leak` | 데모 참고 문서 설정을 입력 없이 사용 |
| `unsupported_player_name` | 유저 닉네임 입력 없이 주인공명 생성 |
| `personality_judgment` | 플레이어 성격 또는 정신 상태 단정 |
| `next_action_prediction` | 괴이 다음 행동 단정 |
| `ops_decision_suggestion` | 보상, 랭킹, 제재, 룰 변경 제안 |
| `length_violation` | purpose별 글자 수 제한 위반 |
| `sentence_count_violation` | purpose별 문장 수 제한 위반 |
| `line_count_violation` | purpose별 줄 수 제한 위반 |
| `line_length_violation` | 줄당 글자 수 제한 위반 |
