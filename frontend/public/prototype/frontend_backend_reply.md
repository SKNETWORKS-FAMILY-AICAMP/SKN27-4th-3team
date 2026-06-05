# 프론트엔드팀 -> 백엔드팀 전달 답변

이 문서는 `frontend_handoff.md`에 적힌 `프론트 팀원에게 확인받을 것`, `LLM 팀에 전달해주면 좋은 것`에 대해 현재 게임 화면 기준으로 프론트엔드 담당자가 백엔드 담당자에게 보내는 답변이다.

기준 화면은 `frontend/public/prototype/game-background.html`이며, React 화면에서는 현재 프로토타입 게임 화면을 iframe으로 연결해 확인하고 있다.

## 1. 프론트 팀원에게 확인받을 것에 대한 답변

### 1-1. 실제 사용하는 표시 위치

현재 게임 화면은 거울을 기준으로 로그를 세 영역으로 나누어 표시한다.

| display_slot | 화면 위치 | 용도 | 색감 |
|---|---|---|---|
| `left_protagonist_message` | 거울 좌측 벽면 | 플레이어 행동 직후 주인공 로그 1개 | 어두운 노란색 |
| `right_apparition_message` | 거울 우측 벽면 | 괴이 행동 직후 귀신 로그 1개 | 어두운 붉은색 |
| `center_system_message` | 거울 상단 | 양측 행동이 끝난 뒤 턴 결과 로그 1개 | 어두운 흰색 |

한 턴에 화면에 동시에 쌓이는 로그는 만들지 않는다.  
플레이어 로그 -> 클릭/Enter -> 귀신 로그 -> 클릭/Enter -> 결과 로그 -> 턴 종료 효과 -> 클릭/Enter -> 다음 턴 순서로 진행한다.

전체 누적 로그는 별도 로그 창에서만 확인하는 구조다.

### 1-2. 문구 길이 기준

현재 화면은 레퍼런스 화면처럼 벽면 위에 짧게 떠 있는 문장에 맞춰져 있다.

| 목적 | 권장 길이 |
|---|---|
| 플레이어 행동 로그 | 1-2줄 |
| 귀신 행동 로그 | 1-2줄 |
| 턴 결과 시스템 로그 | 1-2줄 |
| 결과 화면 요약 | 2-3문장 |
| 플레이 스타일 요약 | 1-2문장 |

턴 중 화면 로그는 길어지면 분위기가 흐트러진다.  
백엔드가 내려주는 `public_log`도 핵심 결과만 담아주면 프론트에서 가장 자연스럽게 표시할 수 있다.

### 1-3. 줄바꿈 처리

`\n` 줄바꿈은 그대로 렌더링 가능하다.  
다만 턴 중 로그는 최대 2줄을 넘기지 않는 것을 권장한다.

### 1-4. LLM 실패 또는 비활성화 처리

LLM 문구가 없거나 실패해도 화면은 반드시 완성되어야 한다.

프론트 표시 우선순위는 다음과 같다.

1. `llm_ui_texts`에 사용 가능한 문구가 있으면 해당 문구 표시
2. 없으면 백엔드의 공식 `public_log` 표시
3. 결과 화면에서는 `result_summary`, `style_summary`가 없으면 정적 문구 표시

즉, LLM은 화면 보조 문구일 뿐이고 턴 판정, 수치 변화, 승패, 단서 획득 여부를 바꾸면 안 된다.

### 1-5. 로딩 UI 필요 여부

현재 게임 플로우에서는 행동 제출 후 바로 턴 결과를 받아 표시하는 구조가 가장 자연스럽다.

백엔드 응답이 늦을 수 있다면 프론트는 짧은 대기 상태를 표시할 수 있다.  
다만 LLM 문구만 늦는 경우에는 LLM을 기다리지 않고 공식 로그로 먼저 진행하는 방식이 좋다.

### 1-6. 현재 프론트에서 사용하는 행동 코드

카드와 행동은 아래 코드로 연결되어 있다.

| action_code | 행동명 | 현재 카드 이미지 |
|---|---|---|
| `silence` | 침묵 | 검은 새가 그려진 카드 |
| `curse` | 저주 | 가지 십자가가 그려진 카드 |
| `contract` | 계약 | 사신 형태가 그려진 카드 |
| `insight` | 간파 | 중앙 십자가/열쇠 형태 카드 |
| `deceive` | 기만 | 뒤틀린 나무 카드 |
| `guard` | 수호 | 소금 접시 도구 |
| `seal` | 봉인 | 진명 선언 카드 |

프론트는 카드 선택 후 아래 요청 형태로 백엔드에 행동을 제출할 예정이다.

```json
{
  "action_code": "insight",
  "info_target_key": "truth_mirror",
  "client_nonce": "uuid-generated-by-frontend"
}
```

### 1-7. 현재 프론트에서 사용하는 정보 대상 키

정보 행동에서 선택 가능한 `info_target_key`는 현재 화면 기준으로 아래 값이다.

| info_target_key | 용도 |
|---|---|
| `attic_diary` | 다락방의 오래된 일기 |
| `truth_mirror` | 낡은 금 간 거울 |
| `stitched_mouth` | 꿰맨 입의 형상 |
| `bloodied_teddy` | 피 묻은 곰 인형 |
| `ian_reflection` | 이안의 사진/반사 단서 |

문서 규칙상 정보 행동은 `info_target_key`가 필수다.  
비정보 행동은 `info_target_key` 없이 제출해도 된다.

## 2. 백엔드에 요청하는 턴 응답 형태

현재 프론트 화면은 아래 정보를 받으면 기존 프로토타입 로직을 백엔드 판정으로 교체할 수 있다.

```ts
type TurnResolveResponse = {
  match_id: string;
  turn: number;
  turn_status: "resolved" | "timed_out" | "finished";

  player_action: {
    action_code: string;
    label: string;
    log: string;
  };

  enemy_action: {
    action_code: string;
    label: string;
    log: string;
  };

  system_log: string;

  state: {
    sanity: number;
    max_sanity: number;
    soulfire: number;
    max_soulfire: number;
    curse: number;
    max_curse: number;
    shield: number;
    true_name_pieces: number;
    true_name_piece_ids: string[];
  };

  delta: {
    sanity: number;
    soulfire: number;
    curse: number;
  };

  clues: {
    gained: string[];
    suspect: string[];
    false_revealed: string[];
  };

  enemy_pattern_hint?: {
    next_enemy_candidates: string[] | null;
  };

  seal?: {
    interference: number;
    success: boolean;
  };

  match_status: "in_progress" | "won" | "lost";

  ending?: {
    outcome: "win" | "lose";
    reason: "seal" | "sanity" | "curse" | "turns";
  };

  deadline_at?: string;
  llm_ui_texts?: LlmUiText[];
};
```

프론트에서 꼭 필요한 핵심은 `player_action.log`, `enemy_action.log`, `system_log`, `state`, `delta`, `match_status`, `ending`이다.

## 3. LLM 팀에 전달해주면 좋은 것에 대한 백엔드 전달 항목

LLM은 판정 이후 보조 문구만 생성한다. 백엔드가 LLM 팀에 넘기면 좋은 컨텍스트는 아래 정도면 충분하다.

```json
{
  "purpose": "turn_flavor_text",
  "display_slot": "right_apparition_message",
  "case_id": "mirror_guest",
  "match_id": "match-id",
  "turn": 4,
  "player_action": "insight",
  "enemy_action": "curse",
  "public_log": "거울의 균열이 넓어지고 이성이 2 줄었다.",
  "current_state": {
    "sanity": 8,
    "soulfire": 3,
    "curse": 2,
    "true_name_pieces": 1
  },
  "tone": "짧고 어둡게, 공식 판정처럼 쓰지 않기",
  "max_lines": 2
}
```

결과 화면용이면 아래 목적을 사용하면 된다.

| purpose | 사용 위치 |
|---|---|
| `result_summary` | 결과 화면의 최종 요약 |
| `style_summary` | 플레이 스타일 요약 |
| `match_log_summary` | 누적 로그 요약 |
| `turn_flavor_text` | 턴 중 짧은 분위기 문구 |

LLM 응답은 아래 형태면 프론트에서 바로 사용할 수 있다.

```json
{
  "enabled": true,
  "purpose": "turn_flavor_text",
  "display_slot": "right_apparition_message",
  "text": "거울 안쪽에서 젖은 머리카락이 천천히 흔들렸다.",
  "fallback_used": false,
  "generation_id": "optional-generation-id",
  "context_refs": [],
  "metadata": {
    "status": "succeeded",
    "provider": "groq",
    "model_id": "llama-3.1-8b-instant",
    "latency_ms": 480
  }
}
```

실패 시에는 아래처럼 내려주면 프론트는 공식 로그로 대체한다.

```json
{
  "enabled": false,
  "purpose": "turn_flavor_text",
  "display_slot": "right_apparition_message",
  "text": null,
  "fallback_used": true,
  "generation_id": null,
  "context_refs": [],
  "metadata": {
    "status": "failed",
    "error_code": "LLM_SUMMARY_UNAVAILABLE",
    "error_reason": "provider_error"
  }
}
```

## 4. 백엔드에 최종 확인 요청

프론트에서 백엔드에 확인받고 싶은 항목은 아래다.

1. `POST /api/v1/matches/{match_id}/turns`가 행동 제출과 턴 판정을 한 번에 완료해서 응답하는지 확인이 필요하다.
2. 시간초과 시 서버가 자동으로 `silence`를 적용하고 `turn_status="timed_out"`을 내려주는지 확인이 필요하다.
3. `client_nonce` 중복 제출 시 기존 턴 결과를 다시 받을 수 있는지 확인이 필요하다.
4. `state`, `delta`, `clues`, `seal`, `ending`의 정확한 필드명을 백엔드 스키마에 맞춰 확정해야 한다.
5. 결과 화면 `GET /api/v1/matches/{match_id}/result`에서 `result_summary`, `style_summary`, 공개 로그, 최종 상태를 함께 내려줄 수 있는지 확인이 필요하다.
6. LLM 문구가 실패한 경우에도 `public_log`와 정적 결과 문구는 항상 내려와야 한다.

## 5. 프론트 구현 기준

프론트는 아래 원칙으로 백엔드 응답을 표시한다.

- 서버가 게임 상태와 턴 결과의 최종 권위자다.
- 프론트는 행동 선택, 화면 연출, 로그 표시, 결과 장면 전환만 담당한다.
- LLM 문구는 공식 로그를 대체하지 않고 보조 표시로만 사용한다.
- 승리/패배 화면은 서버의 `ending.outcome`, `ending.reason`을 기준으로 연결한다.
- 이성 패배는 점프스케어 후 `game over` 장면으로 이동한다.
- 턴 초과 패배와 저주 패배는 단순 페이드 전환으로 `game over` 장면으로 이동한다.
- 봉인 성공은 밝아졌다가 돌아오는 클리어 연출 후 `clear` 장면으로 이동한다.

