# LLM 작업 계획

이 문서는 LLM 파트의 purpose, 출력 계약, fallback, provider 후보를 한 곳에 정리한다.

LLM은 게임 판정자가 아니라 서버가 확정한 사건 기록을 세계관 톤에 맞게 정리하는 보조 기록자다.

## 담당 범위

- 결과 화면 보조 서사 요약
- 단일 턴 화면 연출 문구
- 플레이 스타일 요약 문장
- 운영자용 매치 로그 요약
- 승인된 기준 문장의 짧은 변형 후보

## 금지선

- 행동 성공/실패 판정
- 승패 결정
- 이성, 의식력, 저주 흔적 계산
- 진명 조각 획득 판정
- 거짓 단서 생성 또는 진위 판정
- 보상, 랭킹, 매칭
- 공식 설정 추가 또는 룰 변경

## Purpose

| purpose | 목적 | 입력 | 출력 |
|---|---|---|---|
| `result_summary` | 결과 화면 보조 서사 요약 | `MatchResult` | `llm_summary.text` 후보 |
| `turn_flavor_text` | 단일 턴 화면 연출 문구 | `TurnResult` | UI 시스템/반응 문구 후보 |
| `style_summary` | 플레이 스타일 요약 문장 | `StyleSummary.metrics` | `label`, `display_text` 후보 |
| `match_log_summary` | 운영자용 매치 로그 요약 | 공개 턴 로그, 결과 enum | 운영자 확인용 요약 |

## 보류 purpose

| purpose | 보류 이유 |
|---|---|
| `briefing_variant` | 공식 브리핑 문장은 사람이 작성하고 승인한다. |
| `apparition_dialogue` | 괴이 대사는 공식 설정 추가나 판정처럼 보일 위험이 있다. |
| `next_apparition_strategy` | 괴이 행동 선택은 서버 정책이 결정한다. |

## 데모 스토리 참고 경계

`demo_story_reference.md`는 `무명(無名)의 저주` 데모 시나리오를 정리한 본 스토리 후보 참고 문서다.

이 문서는 향후 본 스토리 구성이 될 가능성이 높지만 아직 공식 확정본은 아니다.

PDF 초고의 주인공 이름은 `이안`이지만, 실제 게임에서는 로그인한 유저의 닉네임을 주인공명으로 사용할 예정이다.

현재 괴이 이름 후보는 `피티`다.

따라서 현재 fixture, prompt, expected output의 기준을 대체하지 않는다.

사용 가능:

- 심리 공포와 고딕 호러 톤 참고
- 진명과 해방 중심의 결과 요약 분위기 참고
- 공식 스토리 확정 전 LLM 문장 방향성 검토

사용 금지:

- 공식 사건명, 공식 인물명, 공식 진명 조각으로 확정
- 서버 판정이나 프론트 표시 문구의 근거로 사용
- 입력에 없는 `피티`, `이안`, `엘리자베스`, `무명(無名)의 저주` 설정을 생성 결과에 끌어오기
- 로그인 유저 닉네임 입력 없이 주인공명을 임의 생성하기

## 출력 계약 초안

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

### status 값

| 값 | 의미 |
|---|---|
| `succeeded` | LLM 생성 성공 |
| `failed` | LLM 생성 실패 |
| `skipped` | 정책 또는 설정상 호출하지 않음 |

### 실패 출력

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
    "error_code": "LLM_SUMMARY_UNAVAILABLE"
  }
}
```

## API 연결 기준

`MatchResult.llm_summary`에는 생성된 보조 문장만 연결한다.

LLM이 성공한 경우:

```json
{
  "enabled": true,
  "text": "생성된 보조 요약",
  "generation_id": "llm-generation-log-id"
}
```

LLM이 실패하거나 비활성화된 경우:

```json
{
  "enabled": false,
  "text": null,
  "generation_id": null
}
```

`story_result_text`는 서버가 내려주는 정적 결과 문장이며, LLM 결과로 대체하지 않는다.

## Fallback 정책

### 결과 요약

- 기본 표시 문장은 `MatchResult.story_result_text`를 사용한다.
- LLM 생성 결과는 `MatchResult.llm_summary.text`에만 표시한다.
- LLM 실패 시 `llm_summary.enabled=false`, `text=null`, `generation_id=null`로 둔다.
- 프론트는 `LLM_SUMMARY_UNAVAILABLE` 상황에서 정적 결과 문장을 표시한다.

### 단일 턴 연출 문구

- 기본 표시 문장은 서버가 확정한 `TurnResult.public_log.text`를 사용한다.
- LLM 생성 결과는 화면 연출 후보로만 사용하고 공식 턴 로그를 대체하지 않는다.
- LLM 실패 시 `public_log.text`만으로 턴 화면이 완성되어야 한다.
- LLM은 행동 성공/실패, 단서 획득, 승패, 다음 괴이 행동을 새로 판단하지 않는다.

### 스타일 요약

- 스타일 지표 값은 서버가 계산한 `StyleSummary.metrics`를 따른다.
- LLM은 `label` 또는 `display_text` 후보를 만들 수 있지만, 지표를 수정하지 않는다.
- LLM 실패 시 수치 지표만 표시해도 화면이 완성되어야 한다.

### 운영자용 로그 요약

- 운영자용 요약은 편의 기능이다.
- LLM 실패 시 원본 턴 로그를 그대로 조회할 수 있어야 한다.
- LLM 요약 실패를 매치 실패나 판정 실패로 취급하지 않는다.

## Provider 기준

OpenAI 유료 API를 기본 전제로 두지 않는다.

1차 LLM provider는 Groq로 정리한다.

무료 tier, 모델 목록, rate limit은 자주 바뀌므로 실제 연결 직전에는 공식 문서를 다시 확인한다.

| provider | 사용 방향 | 장점 | 확인 필요 |
|---|---|---|---|
| Groq | 1차 선택 provider | OpenAI-compatible 형태로 붙이기 쉽고 응답 속도가 빠르다. | free plan rate limit, 사용 가능 model id, 한국어 품질 |
| Hugging Face Inference Providers | 대체 후보 | 모델 선택지가 넓고 provider routing 실험이 쉽다. | 월별 무료 credits, provider별 과금 전환 조건, 응답 속도 |
| Google AI Studio / Gemini API | 대체 후보 | 무료 tier가 있고 한국어 품질을 기대할 수 있다. | 무료 tier rate limit, billing 연결 여부, API 응답 형식 |
| OpenRouter | 대체 후보 | 여러 모델을 한 API 형태로 비교하기 쉽다. | free 모델 availability, 모델별 가격 0 여부, rate limit |
| Ollama local | 로컬 실험 후보 | API 비용이 없고 key가 필요 없다. | 팀원 PC 성능, 모델 다운로드 용량, 한국어 품질 |

### 선택 기준

- 무료 또는 저비용으로 MVP 실험이 가능하다.
- API key와 model id를 환경 변수로 주입할 수 있다.
- OpenAI-compatible API 또는 단순 adapter로 연결할 수 있다.
- 한국어 요약 품질이 MVP 결과 화면에 사용할 수 있는 수준이다.
- 짧은 결과 요약에서 지연 시간이 과하지 않다.
- rate limit 초과 시 fallback 처리가 쉽다.
- 장애 시 fallback 문장으로 자연스럽게 대체할 수 있다.
- 게임 판정 로직과 분리해서 사용할 수 있다.

### Provider 결정

1차 provider는 Groq로 둔다.

Groq는 OpenAI-compatible API 형태로 연결하는 것을 기본 방향으로 한다.

Hugging Face, Gemini, OpenRouter는 Groq 사용이 어렵거나 quota 문제가 생길 때 대체 후보로 남긴다.

Ollama는 배포용이 아니라 prompt와 금지선 테스트를 로컬에서 반복하는 용도로 검토한다.

## Env preset

실제 API key는 `.env`에만 넣고 저장소에 커밋하지 않는다.

### Groq 기본 변수

```env
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

`LLM_MODEL_ID`는 실제 연결 직전에 Groq 공식 콘솔 또는 문서에서 사용 가능한 모델을 확인한 뒤 채운다.

### Groq preset

```env
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

### Adapter 호출 형태

```text
generate(purpose, input, options) -> LlmGenerationResult
```

Groq adapter는 내부적으로 OpenAI-compatible chat completion 요청 형태를 사용한다.

상세 input, options, result, 실패 처리 기준은 `../generation/adapter_contract.md`를 따른다.

### Hugging Face 후보

```env
LLM_PROVIDER=huggingface
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=45
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

### Gemini 후보

```env
LLM_PROVIDER=gemini
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

### OpenRouter 후보

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

### Ollama local 후보

```env
LLM_PROVIDER=ollama
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=http://localhost:11434
LLM_TIMEOUT_SECONDS=60
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

## 공식 문서 확인 링크

- Groq rate limits: https://console.groq.com/docs/rate-limits
- Hugging Face Inference Providers: https://huggingface.co/docs/inference-providers
- Hugging Face pricing/rate limits: https://huggingface.co/docs/api-inference/rate-limits
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- OpenRouter model list API: https://openrouter.ai/docs/api/api-reference/models/get-models

## 보류 사항

- 최종 provider
- 기본 model id
- generation log 보존 기간
- LLM 결과를 백엔드에 저장할 schema
