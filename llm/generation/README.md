# Generation 설계 초안

이 폴더는 LLM provider 교체 가능 구조와 generation 입출력 형식을 관리한다.

## Provider 방향

OpenAI 유료 API를 기본값으로 두지 않는다.

우선 검토 대상:

- Hugging Face Inference API
- Groq API
- 기타 무료 또는 저비용 LLM provider

## 환경 변수

```env
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
```

## 공통 호출 형태 초안

```text
generate(purpose, system_prompt, user_prompt, context_refs) -> generation_result
```

## generation_result 초안

```json
{
  "purpose": "result_summary",
  "provider": "huggingface",
  "model_id": "model-id",
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
