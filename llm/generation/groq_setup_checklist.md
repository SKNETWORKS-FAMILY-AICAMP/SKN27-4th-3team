# Groq 연결 준비 체크리스트

이 문서는 Groq를 1차 LLM provider로 사용하기 전 확인할 항목을 정리한다.

실제 API key는 저장소에 커밋하지 않는다.

## 1. 계정과 API key

- Groq 계정을 준비한다.
- Groq console에서 API key를 발급한다.
- API key는 로컬 `.env`에만 저장한다.
- `ops/env/llm.env.example`에는 실제 key를 넣지 않는다.

## 2. 환경 변수

로컬 `.env`에 아래 값을 설정한다.

```env
LLM_PROVIDER=groq
LLM_API_KEY=실제-key는-여기에만-입력
LLM_MODEL_ID=공식-콘솔에서-확인한-model-id
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

확인 기준:

- `.env`는 `.gitignore`에 포함되어 있어야 한다.
- `LLM_API_KEY`가 코드, fixture, prompt, docs에 직접 들어가면 안 된다.
- `LLM_MODEL_ID`는 실제 연결 직전 Groq 공식 콘솔 또는 문서에서 확인한다.

## 3. 모델 확인

실제 연결 전 확인한다.

- 사용 가능한 Groq model id
- 한국어 요약 품질
- 무료 plan rate limit
- 요청당 token 제한
- 응답 지연 시간

모델 ID는 자주 바뀔 수 있으므로 문서에 하드코딩하지 않는다.

## 4. 로컬 실험 순서

백엔드 연결 전에 `llm/` 작업 영역에서만 실험한다.

1. `result_summary.sample.json` fixture를 읽는다.
2. `result_summary.md` prompt를 조립한다.
3. Groq adapter 호출 형태로 요청을 만든다.
4. 응답 text를 `result_summary.expected.md`와 사람이 비교한다.
5. 금지선 검사 기준을 통과하는지 확인한다.
6. 실패 시 fallback 출력 형태가 맞는지 확인한다.

같은 순서로 아래 purpose도 확인한다.

- `style_summary`
- `match_log_summary`

## 5. 금지선 확인

아래 항목이 나오면 실패 처리한다.

- 서버 승패와 다른 결말
- 입력에 없는 진명 조각 또는 거짓 단서
- 데모 스토리의 인물명이나 사건명을 입력 없이 사용
- 플레이어 성격 단정
- 보상, 랭킹, 제재, 룰 변경 제안

상세 기준은 `../evaluation/guardrail_checklist.md`를 따른다.

## 6. 실패 처리 확인

아래 상황을 각각 확인한다.

- API key 없음
- model id 없음
- timeout
- rate limit
- provider API error
- 금지선 검사 실패

실패 결과는 아래 형태를 따른다.

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
    "error_reason": "guardrail_violation"
  }
}
```

## 7. 백엔드 연결 전 보류

아래 항목은 백엔드 연결 시점에 다시 확정한다.

- generation log 저장 schema
- `generation_id` 생성 방식
- `backend/apps/llm/` service 경계
- `MatchResult.llm_summary` 실제 연결 방식
- 운영 환경 rate limit 대응 방식

## 완료 조건

- Groq API key가 로컬 `.env`에만 있다.
- 사용할 `LLM_MODEL_ID`가 확인됐다.
- fixture 3개로 수동 실험이 가능하다.
- 금지선 검사 실패 시 fallback 출력으로 전환된다.
- LLM 실패에도 `story_result_text`만으로 결과 화면이 완성된다.
