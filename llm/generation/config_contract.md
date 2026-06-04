# LLM 환경 변수 설정 계약

이 문서는 LLM 실험 스크립트와 provider adapter가 읽는 환경 변수 기준을 정리한다.

실제 API key는 로컬 `.env`에만 넣고 저장소에 커밋하지 않는다.

## 적용 범위

- `llm/generation/scripts/test_groq_generation.py`
- 향후 `backend/apps/llm/` 연결 전 로컬 provider 실험
- Groq OpenAI-compatible chat completion 호출

## 기본 원칙

- API key는 로그에 출력하지 않는다.
- API key는 prompt, fixture, 생성 결과 파일에 넣지 않는다.
- provider, model id, base URL은 환경 변수로 주입한다.
- key 또는 model id가 없으면 실제 호출하지 않고 `status=skipped`로 처리한다.
- LLM 실패 또는 비활성화는 게임 판정 실패가 아니다.

## 변수 목록

| 변수 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `LLM_PROVIDER` | 선택 | `groq` | 현재 실험 provider. |
| `LLM_API_KEY` | 실제 호출 시 필수 | 없음 | provider API key. 로그 출력 금지. |
| `LLM_MODEL_ID` | 실제 호출 시 필수 | 없음 | Groq 콘솔 또는 공식 문서에서 확인한 model id. |
| `LLM_BASE_URL` | 선택 | `https://api.groq.com/openai/v1` | OpenAI-compatible base URL. |
| `LLM_TIMEOUT_SECONDS` | 선택 | `30` | HTTP timeout 초. |
| `LLM_MAX_OUTPUT_TOKENS` | 선택 | `400` | 생성 최대 token 수. |
| `LLM_TEMPERATURE` | 선택 | `0.4` | 생성 temperature. |
| `LLM_DISABLED` | 선택 | `false` | `true`이면 provider 호출을 건너뛴다. |

## 로컬 `.env` 예시

```env
LLM_PROVIDER=groq
LLM_API_KEY=실제-key는-여기에만-입력
LLM_MODEL_ID=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

## Python 로딩 기준

실험 스크립트는 아래 순서로 값을 읽는다.

1. 현재 프로세스 환경 변수
2. repository root의 `.env`
3. 기본값

`.env` 값은 프로세스 환경 변수보다 우선하지 않는다.

## 실패 처리

아래 경우에는 provider 호출을 하지 않거나 실패 결과를 반환한다.

| 상황 | 처리 |
|---|---|
| `LLM_DISABLED=true` | `status=skipped`, `reason=llm_disabled` |
| `LLM_API_KEY` 없음 | `status=skipped`, `reason=missing_api_key` |
| `LLM_API_KEY`가 placeholder 또는 비 ASCII 값 | `status=skipped`, `reason=invalid_api_key_format` |
| `LLM_MODEL_ID` 없음 | `status=skipped`, `reason=missing_model_id` |
| provider timeout | `status=failed`, `error_reason=timeout` |
| provider API error | `status=failed`, `error_reason=provider_error` |
| 응답 text 추출 실패 | `status=failed`, `error_reason=response_parse_error` |
| guardrail 실패 | `status=failed`, `error_reason=guardrail_violation` |

## 보안 점검

- `.gitignore`는 `.env`, `.env.*`를 제외해야 한다.
- `ops/env/llm.env.example`에는 실제 key를 넣지 않는다.
- 오류 메시지에 Authorization header 또는 key 원문을 포함하지 않는다.
- 생성 결과 metadata에는 provider, model id, latency만 남기고 key는 남기지 않는다.
- 예시 문구인 `실제-key는-여기에만-입력` 같은 placeholder를 실제 key처럼 호출하지 않는다.
