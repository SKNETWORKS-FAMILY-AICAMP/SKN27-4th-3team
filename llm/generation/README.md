# Generation 설계 초안

이 폴더는 LLM provider 교체 가능 구조와 generation 입출력 형식을 관리한다.

상세 출력 계약과 provider env preset은 `../docs/llm_plan.md`에서 통합 관리한다.

백엔드 연결용 adapter 함수는 `adapter.py`에 둔다.

Groq adapter 입출력과 실패 처리 기준은 `adapter_contract.md`를 따른다.

Groq 실제 연결 전 준비 절차는 `groq_setup_checklist.md`를 따른다.

## Provider 방향

OpenAI 유료 API를 기본값으로 두지 않는다.

1차 provider는 Groq로 둔다.

Groq는 OpenAI-compatible API 형태로 연결하는 것을 기본 방향으로 한다.

Hugging Face, Gemini, OpenRouter, Ollama local은 대체 또는 실험 후보로 남긴다.

## 환경 변수

```env
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
```

## 공통 호출 형태 초안

```text
generate(purpose, input, options) -> generation_result
```

상세 input, options, result 구조는 `adapter_contract.md`를 참고한다.

## 백엔드 호출 예시

```python
from llm.generation.adapter import generate_llm_ui_text

llm = generate_llm_ui_text("turn_flavor_text", turn_payload)
```

`generate_llm_ui_text()`는 프론트 전달용 응답 구조를 반환한다.

실험 CLI는 같은 adapter를 호출한다.

## generation_result 초안

```json
{
  "purpose": "result_summary",
  "provider": "groq",
  "model_id": "model-id",
  "generation_id": "string-or-null",
  "text": "생성된 보조 문장",
  "status": "succeeded",
  "fallback_used": false,
  "context_refs": [],
  "metadata": {
    "latency_ms": 0
  }
}
```

LLM 호출 실패 시 화면은 서버 판정 결과와 정적 fallback 문장만으로 완성되어야 한다.

## 프론트 전달용 응답 초안

프론트에는 `enabled`, `text`, `display_slot`, `fallback_used` 중심의 래핑 결과를 전달한다.

```json
{
  "enabled": true,
  "purpose": "turn_flavor_text",
  "text": "거울 속 시선이 더 선명해졌다.",
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

실험 CLI에서는 `--frontend-output` 옵션으로 이 형태를 확인한다.

## MatchResult 연결 초안

official API의 `MatchResult.llm_summary`에는 아래 값만 연결한다.

```json
{
  "enabled": true,
  "text": "생성된 보조 요약",
  "generation_id": "llm-generation-log-id"
}
```

실패하거나 호출하지 않는 경우에는 아래 값을 사용한다.

```json
{
  "enabled": false,
  "text": null,
  "generation_id": null
}
```

`story_result_text`는 서버가 내려주는 정적 결과 문장이며, LLM 결과로 대체하지 않는다.
