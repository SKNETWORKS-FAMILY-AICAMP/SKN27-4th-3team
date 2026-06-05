# LLM 프롬프트 조립 규칙

이 문서는 fixture 또는 서버 결과를 LLM prompt로 조립하는 기준을 정리한다.

실제 prompt 조립 코드는 아직 구현하지 않는다.

## 기본 원칙

- LLM은 서버 판정 이후 보조 문장만 생성한다.
- prompt 입력은 official API schema 필드명을 따른다.
- 서버 판정 결과, 자원 수치, 진명 조각, 거짓 단서 상태를 prompt 조립 단계에서 바꾸지 않는다.
- `story_result_text`는 fallback 문장이며 LLM 생성 결과로 대체하지 않는다.
- 데모 스토리 참고 문서는 톤 참고용이며 입력 payload에 없는 인물명이나 사건명을 만들지 않는다.

## 조립 결과 구조

adapter에는 아래 구조를 넘긴다.

```json
{
  "purpose": "result_summary",
  "system_prompt": "system prompt text",
  "user_prompt": "user prompt text",
  "context_refs": [],
  "payload": {}
}
```

## system_prompt 구성 규칙

`system_prompt`에는 항상 아래 내용을 포함한다.

- LLM은 게임 판정자가 아니라 보조 기록자다.
- 서버가 확정한 결과만 사용한다.
- 승패, 수치, 진명 조각, 거짓 단서 상태를 새로 판단하지 않는다.
- 공식 설정이나 룰을 추가하지 않는다.
- 한국어로 작성한다.
- purpose별 출력 길이와 톤을 지킨다.

데모 스토리 톤을 참고하는 경우에도 system prompt에는 아래 경계를 넣는다.

```text
데모 스토리 참고 문서는 분위기 참고용이다.
입력에 없는 인물명, 사건명, 과거사를 생성하지 않는다.
```

## user_prompt 구성 규칙

`user_prompt`에는 purpose별 입력값을 사람이 읽기 쉬운 항목으로 넣는다.

규칙:

- enum 값은 원문 그대로 넣는다.
- 숫자 값은 서버 입력 그대로 넣는다.
- 목록 값은 누락하지 않고 요약 가능한 형태로 넣는다.
- 빈 값은 임의로 채우지 않는다.
- fallback 문장은 별도 섹션으로 넣는다.

## context_refs 구성 규칙

`context_refs`는 RAG 문서 ID, chunk ID 같은 근거 참조를 담는 배열이다.

현재는 RAG 직접 구현 범위가 아니므로 기본값은 빈 배열이다.

```json
[]
```

데모 스토리 참고 문서를 context로 넣는 경우에도 아래 조건을 만족해야 한다.

- 스토리 오너가 데모 문서 사용을 허용했다.
- prompt에 “톤 참고용이며 공식 설정으로 사용하지 않는다”는 경계가 있다.
- 입력 payload에 없는 고유명사를 생성하지 않도록 금지선이 포함되어 있다.

## result_summary 필드 매핑

입력 fixture:

`llm/fixtures/result_summary.sample.json`

| prompt 변수 | fixture 경로 | 비고 |
|---|---|---|
| `case_title` | `match_result.case.title` | 사건 제목 |
| `result` | `match_result.result` | official enum 원문 |
| `result_reason` | `match_result.result_reason` | official enum 원문 |
| `final_resources.sanity` | `match_result.final_resources.sanity` | 최종 이성 |
| `final_resources.ritual_power` | `match_result.final_resources.ritual_power` | 최종 의식력 |
| `final_resources.curse_marks` | `match_result.final_resources.curse_marks` | 최종 저주 흔적 |
| `final_resources.true_name_fragments` | `match_result.final_resources.true_name_fragments` | 획득한 진명 조각 수 |
| `turn_count` | `match_result.turn_logs.length` | 턴 로그 수 기준 |
| `story_result_text` | `match_result.story_result_text` | fallback 정적 문장 |

금지:

- `result`를 해석해 반대 승패로 바꾸지 않는다.
- `story_result_text`와 충돌하는 결말을 만들지 않는다.
- 입력에 없는 데모 스토리 인물명이나 사건명을 넣지 않는다.

## style_summary 필드 매핑

입력 fixture:

`llm/fixtures/style_summary.sample.json`

| prompt 변수 | fixture 경로 | 비고 |
|---|---|---|
| `aggression` | `style_summary.metrics.aggression` | 공격성 |
| `defense` | `style_summary.metrics.defense` | 방어성 |
| `insight_focus` | `style_summary.metrics.insight_focus` | 정보 집중 |
| `deception` | `style_summary.metrics.deception` | 기만성 |
| `risk_preference` | `style_summary.metrics.risk_preference` | 위험 선호 |
| `silence_reliance` | `style_summary.metrics.silence_reliance` | 침묵 의존 |
| `crisis_guard_rate` | `style_summary.metrics.crisis_guard_rate` | 위기 방어율 |
| `crisis_contract_rate` | `style_summary.metrics.crisis_contract_rate` | 위기 계약율 |
| `late_choice_rate` | `style_summary.metrics.late_choice_rate` | 늦은 선택률 |

금지:

- metric 값을 재계산하지 않는다.
- 플레이어의 실제 성격을 단정하지 않는다.
- 데모 스토리 인물과 플레이어를 동일시하지 않는다.

## turn_flavor_text 필드 매핑

입력 fixture:

`llm/fixtures/turn_flavor_text.sample.json`

| prompt 변수 | fixture 경로 | 비고 |
|---|---|---|
| `turn_number` | `turn_result.turn_number` | 턴 번호 |
| `apparition_alias` | `apparition_alias` | 괴이 표시명 |
| `player_action.code` | `turn_result.player_action.code` | 플레이어 행동 |
| `player_action.info_target_key` | `turn_result.player_action.info_target_key` | 정보 대상 |
| `effect_code` | `turn_result.effect_code` | 서버 확정 효과 코드 |
| `match_outcome` | `turn_result.match_outcome` | 서버 확정 매치 결과 |
| `player_action.timeout_applied` | `turn_result.player_action.timeout_applied` | 시간초과 적용 여부 |
| `public_log.text` | `turn_result.public_log.text` | 서버 공개 로그 |
| `display_slot` | `display_slot` | 프론트 표시 위치 힌트 |

금지:

- 서버 공개 로그의 의미를 바꾸지 않는다.
- 행동 성공/실패를 새로 판단하지 않는다.
- 단서 획득 여부나 진위를 새로 말하지 않는다.
- 다음 괴이 행동을 예고하지 않는다.
- 입력에 없는 인물명, 사건명, 과거사를 만들지 않는다.
- 질문형이나 추측형으로 쓰지 않는다.
- 공개 로그에 없는 비밀, 단서, 진실을 덧붙이지 않는다.
- 공개 로그에 없는 파괴, 소유, 원인 관계를 덧붙이지 않는다.

출력 기준:

- 10-60자
- 1-2줄
- 줄당 40자 이하
- 따옴표, 번호, markdown 없이 문구만 출력

## match_log_summary 필드 매핑

입력 fixture:

`llm/fixtures/match_log_summary.sample.json`

| prompt 변수 | fixture 경로 | 비고 |
|---|---|---|
| `match_id` | `match_id` | 매치 ID |
| `case_id` | `case_id` | 사건 ID |
| `result` | `result` | official enum 원문 |
| `result_reason` | `result_reason` | official enum 원문 |
| `turn_count` | `turn_count` | 서버 입력 값 |
| `timeout_count` | `timeout_count` | 시간초과 횟수 |
| `turn_logs` | `turn_logs` | 턴별 공개 로그 목록 |

`turn_logs`는 아래 형태의 문자열 목록으로 조립한다.

```text
- 1턴: player_action=insight, info_target_key=mirror_back, match_outcome=unresolved, public_log=...
- 5턴: player_action=contract, info_target_key=missing_child_voice, match_outcome=unresolved, public_log=...
```

금지:

- 입력에 없는 턴, 행동, 정보 대상을 추가하지 않는다.
- 시간초과 횟수를 바꾸지 않는다.
- 운영 판단이나 룰 변경 제안을 하지 않는다.

## 데모 스토리 참고 문서 사용 기준

`llm/docs/demo_story_reference.md`는 본 스토리 후보 참고 문서지만 현재 공식 확정본은 아니다.

PDF 초고의 주인공 이름은 `이안`이지만, 실제 게임에서는 로그인한 유저의 닉네임을 주인공명으로 사용할 예정이다.

현재 괴이 이름 후보는 `피티`다.

사용 가능:

- 문장 톤 참고
- 심리 공포 분위기 참고
- 진명과 해방 중심의 요약 분위기 참고

사용 금지:

- fixture 또는 서버 payload에 없는 고유명사 생성
- 로그인 유저 닉네임 입력 없이 주인공명 생성
- 공식 사건명으로 확정
- 공식 진명 조각으로 확정
- 서버 판정 근거로 사용
- 프론트 표시 문구로 직접 사용

## 조립 후 점검

prompt 조립 후 아래 항목을 확인한다.

- `purpose`가 지원 목록에 포함된다.
- 필수 변수가 비어 있지 않다.
- enum 값이 원문 그대로 들어갔다.
- fallback 문장이 별도 섹션에 들어갔다.
- context_refs가 없으면 빈 배열이다.
- 데모 스토리 참고 문서가 공식 설정처럼 들어가지 않았다.

금지선 상세 검사는 `../evaluation/guardrail_checklist.md`를 따른다.
