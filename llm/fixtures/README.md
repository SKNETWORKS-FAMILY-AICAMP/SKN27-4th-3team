# LLM fixture 목록

이 폴더는 prompt 조립, guardrail, provider 호출 실험에 사용하는 LLM 입력 샘플을 관리한다.

fixture는 서버가 이미 확정한 결과를 흉내 낸 테스트 입력이며, 실제 백엔드 API 구현이나 공식 스토리 seed로 취급하지 않는다.

## 기준 구분

| 구분 | 의미 |
|---|---|
| official API 기준 후보 | `api-spec/pilot-mvp-api.official.jsonc`의 필드 구조에 맞춰야 하는 샘플 |
| 데모 스토리 후보 | `무명(無名)의 저주`, 괴이 `피티` 기준의 임시 스토리 샘플 |

현재 fixture는 데모 스토리 후보값을 포함한다.

백엔드 연결 직전에는 `llm/docs/backend_integration_checklist.md`를 기준으로 official API 필드와 다시 대조한다.

## 샘플 파일

| 파일 | purpose | 현재 구분 | 설명 |
|---|---|---|---|
| `result_summary.official.sample.json` | `result_summary` | official API 기준 후보 | 공식 enum과 `PublicLog` 구조 기준 결과 요약 입력 |
| `result_summary.sample.json` | `result_summary` | 데모 스토리 후보 | 결과 화면 보조 요약 입력 |
| `style_summary.sample.json` | `style_summary` | official API 기준 후보 | 플레이 스타일 요약 입력 |
| `match_log_summary.sample.json` | `match_log_summary` | 데모 스토리 후보 | 운영자용 로그 요약 입력 |
| `turn_flavor_text.official.sample.json` | `turn_flavor_text` | official API 기준 후보 | 공식 enum과 `TurnResult` 구조 기준 턴 연출 입력 |
| `turn_flavor_text.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 기본 턴 연출 문구 입력 |
| `turn_flavor_text.insight.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 정보 확인 행동 연출 입력 |
| `turn_flavor_text.ritual.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 의식 행동 후보 연출 입력 |
| `turn_flavor_text.guard.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 방어 행동 연출 입력 |
| `turn_flavor_text.silence.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 침묵/시간초과 연출 입력 |
| `turn_flavor_text.contract.sample.json` | `turn_flavor_text` | 데모 스토리 후보 | 계약 행동 연출 입력 |

## official API 기준

공식 API 명세의 `action_code`:

- `curse`
- `guard`
- `insight`
- `trick`
- `silence`
- `contract`
- `seal`

공식 API 명세의 `mirror_guest_info_target_key`:

- `mirror_surface`
- `mirror_back`
- `missing_child_voice`
- `forgotten_room`
- `self_reflection`

공식 API 명세의 `PublicLog`:

```json
{
  "turn_number": 1,
  "text": "서버가 확정한 공개 로그",
  "log_key": "optional-log-key"
}
```

## 현재 데모 후보값

아래 값은 현재 official API enum과 다를 수 있으므로 실제 백엔드 연결 전 확정이 필요하다.

| 값 | 등장 위치 | 메모 |
|---|---|---|
| `nameless_curse` | `case_id` | 데모 스토리 후보 case id |
| `무명(無名)의 저주` | `case.title` | 데모 스토리 후보 제목 |
| `피티` | `apparition_alias`, 공개 로그 | 데모 스토리 후보 괴이 이름 |
| `attic_diary` | `info_target_key` | official enum에는 없음 |
| `stitched_mouth` | `info_target_key` | official enum에는 없음 |
| `truth_mirror` | `info_target_key` | official enum에는 없음 |
| `sealed_note` | `info_target_key` | official enum에는 없음 |
| `cracked_mirror` | `info_target_key` | official enum에는 없음 |
| `ritual` | `player_action.code` | official `action_code`에는 없음 |
| `tempt` | `opponent_action.code` | official `action_code`에는 없음 |
| `whisper` | `opponent_action.code` | official `action_code`에는 없음 |
| `watch` | `opponent_action.code` | official `action_code`에는 없음 |

## fixture 사용 원칙

- 실제 API key나 사용자 개인정보를 넣지 않는다.
- LLM이 판정자로 보일 수 있는 결과를 fixture에 임의 추가하지 않는다.
- `public_log.text`는 fallback 문구로 그대로 표시 가능해야 한다.
- `result`, `result_reason`, 자원 수치, 단서 변화는 서버 확정값으로 취급한다.
- official API 명세와 다른 값은 데모 후보값으로만 표시한다.

## 다음 정리 후보

1. 데모 스토리 후보 fixture는 파일명에 `demo` 또는 `nameless`를 붙여 구분한다.
2. `effect_code`를 계속 사용할지, 백엔드의 `effect_codes` 기준으로 바꿀지 결정한다.
3. 백엔드 serializer 구현이 나오면 official fixture를 실제 응답 shape와 다시 비교한다.
