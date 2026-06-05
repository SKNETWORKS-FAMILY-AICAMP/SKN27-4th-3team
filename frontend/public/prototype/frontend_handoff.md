# 프론트 전달용 LLM 연동 메모

이 문서는 React 프론트 팀원과 LLM 응답 표시 방식을 맞추기 위한 공유 문서다.

현재 LLM은 게임 판정자가 아니라 서버 판정 이후의 보조 문구 생성기다.

LLM 응답이 실패해도 게임 판정, 턴 로그, 결과 화면은 깨지지 않아야 한다.

## 프론트에 전달할 타입

```ts
type LlmUiText = {
  enabled: boolean;
  purpose:
    | "turn_flavor_text"
    | "result_summary"
    | "style_summary"
    | "match_log_summary";
  text: string | null;
  display_slot: string | null;
  fallback_used: boolean;
  generation_id: string | null;
  context_refs: string[];
  metadata: {
    status: "succeeded" | "failed" | "skipped";
    provider?: string;
    model_id?: string | null;
    latency_ms?: number;
    error_code?: string;
    error_reason?: string;
    reason?: string;
  };
};
```

## turn_flavor_text 표시 규칙

`turn_flavor_text`는 사용자가 게임 안에서 특정 행동을 했을 때 화면에 짧게 띄우는 연출 문구다.

공식 턴 로그를 대체하지 않고, 화면 연출 후보로만 사용한다.

```ts
const displayText =
  llm?.enabled && llm.text
    ? llm.text
    : publicLog.text;
```

`llm.enabled === true`이고 `llm.text`가 있으면 LLM 문구를 표시한다.

그 외에는 서버가 내려준 `publicLog.text`를 표시한다.

## 응답 예시

### LLM 성공

```json
{
  "enabled": true,
  "purpose": "turn_flavor_text",
  "text": "거울 속 시선이 더 선명해졌다.\n피티는 말없이 너를 바라본다.",
  "display_slot": "right_apparition_message",
  "fallback_used": false,
  "generation_id": null,
  "context_refs": [],
  "metadata": {
    "status": "succeeded",
    "provider": "groq",
    "model_id": "llama-3.1-8b-instant",
    "latency_ms": 480
  }
}
```

### LLM 실패 또는 비활성화

```json
{
  "enabled": false,
  "purpose": "turn_flavor_text",
  "text": null,
  "display_slot": "right_apparition_message",
  "fallback_used": true,
  "generation_id": null,
  "context_refs": [],
  "metadata": {
    "status": "failed",
    "provider": "groq",
    "model_id": "llama-3.1-8b-instant",
    "error_code": "LLM_SUMMARY_UNAVAILABLE",
    "error_reason": "provider_error"
  }
}
```

실패 시 프론트는 새 문장을 만들지 않고 서버의 `publicLog.text`를 사용한다.

## 현재 LLM 문구 길이 기준

`turn_flavor_text` 기준:

| 항목 | 기준 |
|---|---|
| 전체 길이 | 20-90자 |
| 줄 수 | 1-2줄 |
| 줄당 길이 | 45자 이하 |
| 줄바꿈 | `\n` 포함 가능 |

프론트 UI에서 이 기준이 너무 길거나 짧으면 LLM 쪽 기준을 조정할 수 있다.

## display_slot 후보

현재 LLM fixture에서 사용하는 후보:

| display_slot | 용도 후보 |
|---|---|
| `left_system_message` | 플레이어 쪽 시스템 문구 |
| `right_apparition_message` | 괴이 반응 문구 |
| `center_system_message` | 중앙 강조 문구 |

프론트 실제 컴포넌트 이름이나 위치 정책에 맞춰 값은 변경 가능하다.

## 프론트 팀원에게 확인받을 것

1. 실제 사용할 `display_slot` 값 목록
2. `turn_flavor_text` 최대 글자 수와 줄 수가 UI에 맞는지
3. `\n` 줄바꿈을 그대로 렌더링할지
4. `llm.enabled=false`일 때 LLM 영역을 숨길지, `publicLog.text`를 같은 위치에 보여줄지
5. LLM 응답이 턴 결과와 같이 내려올지, 늦게 따로 도착할지
6. 로딩 UI가 필요한지
7. 개발 중 `fallback_used`, `metadata.error_reason`을 화면에서 확인할 필요가 있는지

## LLM 팀에 전달해주면 좋은 것

프론트 구현 후 아래 정보를 LLM 쪽에 공유하면 문구 기준을 더 정확히 맞출 수 있다.

- 실제 메시지 박스 너비와 높이
- 모바일/데스크톱에서 허용 가능한 최대 줄 수
- `display_slot`별 글자 수 제한
- 괴이 대사와 시스템 문구를 시각적으로 구분하는 방식
- 실패 시 보여줄 기본 로그 위치
- 줄바꿈이 어색하게 보이는 사례