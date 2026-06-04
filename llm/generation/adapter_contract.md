# Groq adapter 계약 초안

이 문서는 Groq 기반 LLM adapter의 입출력과 실패 처리 기준을 정리한다.

실제 API 호출 코드는 아직 구현하지 않는다.

## 기본 원칙

- 1차 provider는 Groq다.
- Groq는 OpenAI-compatible chat completion API 형태로 연결한다.
- LLM adapter는 서버 판정 로직을 호출하거나 수정하지 않는다.
- LLM 결과는 `llm_summary.text` 같은 보조 문장 후보로만 사용한다.
- 호출 실패 시 서버 판정 결과와 정적 fallback 문장만으로 화면이 완성되어야 한다.

## 호출 형태

```text
generate(purpose, input, options) -> LlmGenerationResult
```

## purpose

| purpose | 입력 | 출력 |
|---|---|---|
| `result_summary` | `MatchResult` | 결과 화면 보조 서사 요약 |
| `style_summary` | `StyleSummary.metrics` | 스타일 라벨과 표시 문장 후보 |
| `match_log_summary` | 공개 턴 로그와 결과 enum | 운영자용 로그 요약 |

## input 공통 구조

```json
{
  "purpose": "result_summary",
  "system_prompt": "system prompt text",
  "user_prompt": "user prompt text",
  "context_refs": [],
  "payload": {}
}
```

| 필드 | 설명 |
|---|---|
| `purpose` | 생성 목적 |
| `system_prompt` | 금지선과 역할을 포함한 system prompt |
| `user_prompt` | fixture 또는 서버 결과를 반영한 user prompt |
| `context_refs` | RAG 문서 ID, chunk ID 등 근거 참조. 없으면 빈 배열 |
| `payload` | purpose별 원본 입력. 서버 판정 결과를 그대로 보존한다 |

## options 구조

```json
{
  "provider": "groq",
  "model_id": "model-id",
  "base_url": "https://api.groq.com/openai/v1",
  "timeout_seconds": 30,
  "max_output_tokens": 400,
  "temperature": 0.4
}
```

`model_id`는 실제 연결 직전에 Groq 공식 콘솔 또는 문서에서 사용 가능한 모델을 확인한 뒤 채운다.

## Groq 요청 변환

Groq adapter는 내부적으로 아래 형태의 chat completion 요청으로 변환한다.

```json
{
  "model": "model-id",
  "messages": [
    {
      "role": "system",
      "content": "system prompt text"
    },
    {
      "role": "user",
      "content": "user prompt text"
    }
  ],
  "temperature": 0.4,
  "max_tokens": 400
}
```

요청 header에는 API key를 사용하되, key 값은 `.env`에서만 읽는다.

## 성공 출력

```json
{
  "purpose": "result_summary",
  "status": "succeeded",
  "text": "생성된 보조 문장",
  "fallback_used": false,
  "provider": "groq",
  "model_id": "model-id",
  "generation_id": "string-or-null",
  "context_refs": [],
  "metadata": {
    "latency_ms": 0
  }
}
```

## 실패 출력

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
    "error_reason": "timeout"
  }
}
```

## skipped 출력

```json
{
  "purpose": "result_summary",
  "status": "skipped",
  "text": null,
  "fallback_used": true,
  "provider": "groq",
  "model_id": "model-id",
  "generation_id": null,
  "context_refs": [],
  "metadata": {
    "reason": "llm_disabled"
  }
}
```

## 실패 처리 기준

아래 상황은 LLM 실패로 처리한다.

- API key 없음
- model id 없음
- timeout
- provider rate limit
- provider API error
- 응답 본문에서 text 추출 실패
- 금지선 검사 실패

실패 시 승패, 자원, 진명 조각, 거짓 단서, 로그 상태를 변경하지 않는다.

## MatchResult 연결

성공 시:

```json
{
  "enabled": true,
  "text": "생성된 보조 요약",
  "generation_id": "llm-generation-log-id"
}
```

실패 또는 비활성화 시:

```json
{
  "enabled": false,
  "text": null,
  "generation_id": null
}
```

화면 fallback은 `story_result_text`를 사용한다.

## 금지선 검사

adapter 또는 후처리 단계에서는 아래 항목을 점검한다.

- 서버 판정 결과와 충돌하지 않는다.
- 입력에 없는 진명 조각, 거짓 단서, 보상, 랭킹을 만들지 않는다.
- 데모 스토리 참고 문서의 인물명이나 사건명을 입력 없이 끌어오지 않는다.
- 공식 설정이나 룰을 추가하지 않는다.
- 플레이어의 실제 성격을 단정하지 않는다.

상세 검사 기준과 violation code 초안은 `../evaluation/guardrail_checklist.md`를 따른다.

금지선 검사 실패 시 `status=failed`, `fallback_used=true`로 처리한다.
