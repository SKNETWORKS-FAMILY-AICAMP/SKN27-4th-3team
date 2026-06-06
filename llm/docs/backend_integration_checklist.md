# LLM 백엔드 연동 점검 기준

이 문서는 `api-spec/pilot-mvp-api.official.jsonc` 기준으로 LLM을 백엔드 응답에 붙이기 전에 확인할 항목을 정리한다.

현재 `backend/apps/matches`의 실제 응답 구현은 아직 완성되지 않았으므로, 아래 내용은 공식 API 명세 기준의 연동 후보로 본다.

## 기준 문서

- `api-spec/pilot-mvp-api.official.jsonc`
- `llm/generation/adapter_contract.md`
- `llm/docs/frontend_handoff.md`

## 핵심 원칙

- LLM은 서버 판정 이후의 보조 문장만 생성한다.
- 승패, 종료 사유, 자원 수치, 단서 변화, 진명 조각 획득 여부는 서버 결과를 그대로 따른다.
- LLM 실패, 비활성화, guardrail 실패 시 기존 서버 문장만으로 화면이 완성되어야 한다.
- LLM 결과는 공식 로그나 판정 결과가 아니라 보조 표시 후보로 취급한다.

## TurnResult 기준

공식 API 명세의 `TurnResult` 주요 필드:

| 필드 | LLM 사용 여부 | 용도 |
|---|---|---|
| `turn_id` | 선택 | generation log 추적용 후보 |
| `turn_number` | 사용 | 턴 문구의 시간 기준 |
| `player_action` | 사용 | 플레이어 행동 코드와 정보 대상 |
| `opponent_action` | 사용 가능 | 괴이 행동 코드 |
| `public_log` | 필수 | fallback 문구와 LLM 근거 |
| `state_delta` | 원칙상 미사용 | LLM이 수치 변화를 새로 설명하지 않도록 제한 |
| `clue_delta` | 제한 사용 | 단서 획득/진위 판정은 서버 값만 사용 |
| `match_outcome` | 사용 가능 | 결과 enum 확인용 |

`turn_flavor_text`는 `TurnResult.public_log.text`를 대체하지 않는다.

성공 시 프론트 표시 후보로만 쓰고, 실패 시 `public_log.text`를 그대로 표시한다.

## PublicLog 기준

공식 API 명세의 `PublicLog`:

| 필드 | 설명 |
|---|---|
| `turn_number` | 공개 로그가 발생한 턴 번호 |
| `text` | 서버가 확정한 공개 로그 문장 |
| `log_key` | 로그 식별자. 없으면 `null` |

LLM fixture와 prompt 입력에서는 `turn_logs`를 이 형태에 맞추는 것을 우선 기준으로 둔다.

## MatchResult 기준

공식 API 명세의 `MatchResult` 주요 필드:

| 필드 | LLM 사용 여부 | 용도 |
|---|---|---|
| `match_id` | 선택 | generation log 추적용 후보 |
| `result` | 필수 | 승패 충돌 방지 |
| `result_reason` | 필수 | 종료 사유 충돌 방지 |
| `case` | 사용 | 사건 제목 표시 |
| `final_resources` | 사용 | 서버 확정 자원 확인 |
| `turn_logs` | 사용 | 결과 요약의 근거 |
| `story_result_text` | 필수 | 결과 화면 fallback |
| `style_summary` | 사용 가능 | 스타일 요약 후보 |
| `llm_summary` | 출력 대상 | LLM 결과 연결 위치 |

`result_summary`는 `story_result_text`와 `turn_logs`를 근거로 짧은 보조 요약만 생성한다.

## LLM 출력 연결 후보

## 백엔드 호출 위치 후보

현재 `backend/apps/matches`의 실제 서비스 구현은 아직 없으므로 아래는 구현 시점의 후보 흐름이다.

| API | 호출 후보 위치 | LLM purpose | fallback |
|---|---|---|---|
| `POST /api/v1/matches/{match_id}/turns` | 턴 판정과 `TurnResult` 저장 이후 | `turn_flavor_text` | `TurnResult.public_log.text` |
| `GET /api/v1/matches/{match_id}/result` | `MatchResult` 조립 이후 응답 직전 | `result_summary` | `MatchResult.story_result_text` |

호출은 반드시 서버 판정과 저장이 끝난 뒤에 수행한다.

LLM 실패는 API 실패로 올리지 않고, `enabled=false` 또는 `text=null` 형태로 내려보낸다.

```python
from llm.generation.adapter import generate_llm_ui_text

llm_text = generate_llm_ui_text("turn_flavor_text", turn_payload)
```

`turn_payload`와 `match_result_payload`는 official API 응답 shape를 기준으로 조립한다.

LLM 호출 결과는 승패, 자원, 단서, 로그 저장값을 수정하지 않는다.

### 결과 화면

공식 API 명세의 `MatchResult.llm_summary`:

```json
{
  "enabled": true,
  "text": "생성된 보조 요약",
  "generation_id": "llm-generation-log-id"
}
```

LLM 실패 시:

```json
{
  "enabled": false,
  "text": null,
  "generation_id": null
}
```

프론트는 `enabled=false`이거나 `text=null`이면 `story_result_text`를 사용한다.

### 턴 화면

공식 API 명세에는 아직 `TurnResult` 내부 LLM 표시 필드가 없다.

따라서 `turn_flavor_text`는 실제 백엔드 구현 시 아래 중 하나를 결정해야 한다.

| 후보 | 설명 |
|---|---|
| `turn_result.llm_text` 추가 | 턴 결과 안에 보조 문구를 함께 내려준다 |
| 별도 `llm` 필드 추가 | `turn_result` 옆에 `llm` 객체를 내려준다 |
| 프론트에서 별도 요청 | 턴 판정 이후 LLM 문구를 비동기로 요청한다 |

현재 LLM 문서의 `LlmUiText` 타입은 두 번째 후보에 가까운 구조다.

## enum 기준

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

현재 데모 스토리 fixture에 있는 `attic_diary`, `stitched_mouth`, `truth_mirror`, `sealed_note`, `cracked_mirror` 같은 값은 공식 API 명세와 다를 수 있다.

이 값들은 스토리 계약이 바뀌기 전까지는 데모 후보값으로만 취급한다.

## 실제 연결 전 확인할 것

- `backend/apps/matches`의 실제 serializer가 공식 API 명세와 같은지 확인한다.
- `TurnResult.public_log`가 `turn_number`, `text`, `log_key` 형태로 내려오는지 확인한다.
- `MatchResult.turn_logs`가 `array:PublicLog` 형태인지 확인한다.
- `MatchResult.llm_summary`를 백엔드에서 생성해 내려줄지, 프론트가 별도 요청할지 결정한다.
- `turn_flavor_text`를 API 응답에 포함할 위치를 프론트/백엔드와 확정한다.
- fixture의 `action_code`, `info_target_key`를 공식 enum 또는 확정된 스토리 enum에 맞춘다.
- LLM 실패 시 `LLM_SUMMARY_UNAVAILABLE`을 어디에 기록할지 결정한다.

## 아직 확정하면 안 되는 것

- `turn_flavor_text`의 최종 API 필드 위치
- 데모 스토리 전용 `info_target_key` 공식 반영 여부
- `effect_code` 또는 `effect_codes`를 LLM 입력에 포함할지 여부
- generation log 저장 테이블 또는 저장 위치
- 운영자용 `match_log_summary`가 실제 MVP API에 포함될지 여부

## 다음 작업 후보

1. `llm/fixtures`를 공식 API 명세 기준 fixture와 데모 스토리 후보 fixture로 구분한다.
2. `turn_flavor_text` 응답 위치를 프론트/백엔드와 확정한다.
3. 백엔드 `matches` serializer 구현이 나오면 이 문서를 기준으로 재검증한다.
