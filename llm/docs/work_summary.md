# LLM 작업 요약

이 문서는 현재까지 정리한 LLM 파트 작업 현황과 다음 작업 순서를 기록한다.

## 현재 상태

LLM 파트는 기본 폴더 구조, 실험 전 기준 문서, Groq 실험 CLI 초안이 정리된 상태다.

Groq API 호출 코드는 `llm/generation/scripts/test_groq_generation.py`에 추가했다.

현재 로컬 `.env`의 API key 값은 실제 key 형식이 아니라 placeholder로 감지되어 실제 호출은 `invalid_api_key_format`으로 건너뛴다.

현재 LLM은 게임 판정자가 아니라 서버 판정 이후의 보조 기록자 역할로 제한한다.

## 폴더 구조

```text
llm/
  prompts/
  generation/
  evaluation/
  fixtures/
  docs/
```

| 폴더 | 역할 |
|---|---|
| `prompts/` | purpose별 프롬프트 초안과 조립 규칙 |
| `generation/` | Groq adapter 계약과 연결 준비 체크리스트 |
| `evaluation/` | 기대 출력, 금지 출력, guardrail 기준 |
| `fixtures/` | 테스트용 입력 샘플 |
| `docs/` | LLM 전체 계획, 데모 스토리 참고, 작업 요약 |

## 핵심 원칙

- LLM은 승패를 결정하지 않는다.
- LLM은 행동 성공/실패를 판정하지 않는다.
- LLM은 이성, 의식력, 저주 흔적을 계산하지 않는다.
- LLM은 진명 조각과 거짓 단서를 판정하지 않는다.
- LLM은 보상, 랭킹, 매칭에 관여하지 않는다.
- LLM은 공식 설정이나 룰을 추가하지 않는다.
- LLM 결과가 없어도 `story_result_text`로 결과 화면이 완성되어야 한다.

## Provider 기준

1차 provider는 Groq로 정리했다.

```env
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

`LLM_API_KEY`는 실제 `.env`에만 넣는다.

`LLM_MODEL_ID`는 Groq 공식 콘솔 또는 문서에서 사용 가능한 모델을 확인한 뒤 입력한다.

현재 추천 후보는 `llama-3.3-70b-versatile`이다.

## 스토리 기준

PDF `game_scenario_the_nameless_curse.pdf`를 바탕으로 `무명(無名)의 저주` 참고 문서를 만들었다.

현재 상태:

- `무명(無名)의 저주`는 본 스토리 후보 참고 문서다.
- 아직 공식 확정본은 아니다.
- `피티`는 괴이 이름 후보로 정리했다.
- PDF 초고의 주인공명 `이안`은 실제 게임에서 사용하지 않을 가능성이 높다.
- 실제 게임 주인공명은 로그인한 유저 닉네임을 사용할 예정이다.
- PDF 초고의 원혼명 `엘리자베스`는 피티로 치환될 가능성이 있다.

중요 경계:

- 로그인 유저 닉네임 입력 없이 주인공명을 임의 생성하지 않는다.
- 입력 없이 `피티`, `이안`, `엘리자베스`, `무명(無名)의 저주`를 생성 결과에 끌어오지 않는다.
- 데모 스토리는 톤 참고용이며 fixture 기준을 자동 대체하지 않는다.

## 정리한 주요 문서

| 파일 | 내용 |
|---|---|
| `llm/docs/llm_plan.md` | LLM purpose, 출력 계약, fallback, provider 기준 |
| `llm/docs/demo_story_reference.md` | `무명(無名)의 저주` 본 스토리 후보 참고 |
| `llm/prompts/prompt_assembly.md` | fixture를 prompt로 조립하는 규칙 |
| `llm/generation/adapter_contract.md` | Groq adapter 입출력과 실패 처리 계약 |
| `llm/generation/config_contract.md` | LLM 환경 변수와 key 처리 계약 |
| `llm/generation/scripts/test_groq_generation.py` | fixture 기반 prompt 조립과 Groq 호출 실험 CLI |
| `llm/generation/groq_setup_checklist.md` | Groq 실제 연결 전 체크리스트 |
| `llm/evaluation/guardrail_checklist.md` | LLM 금지선 검사 기준 |
| `ops/env/llm.env.example` | Groq 기준 환경 변수 예시 |

## Purpose

| purpose | 역할 |
|---|---|
| `result_summary` | 결과 화면 보조 서사 요약 |
| `turn_flavor_text` | 단일 턴 화면 연출 문구 |
| `style_summary` | 플레이 스타일 요약 문장 |
| `match_log_summary` | 운영자용 매치 로그 요약 |

보류:

- `briefing_variant`
- `apparition_dialogue`
- `next_apparition_strategy`

보류 이유는 공식 설정 추가나 서버 판정처럼 보일 위험이 있기 때문이다.

## Fixture 상태

현재 fixture는 official API schema 필드명을 유지하되, LLM 실험용 사건 샘플은 `무명(無名)의 저주`와 괴이 후보 `피티` 기준으로 맞춰져 있다.

```text
llm/fixtures/result_summary.sample.json
llm/fixtures/turn_flavor_text.sample.json
llm/fixtures/style_summary.sample.json
llm/fixtures/match_log_summary.sample.json
```

검증 결과:

- JSON 4개 모두 파싱 정상
- `result_summary`, `turn_flavor_text`, `style_summary`, `match_log_summary` dry-run prompt 조립 정상
- placeholder API key는 `status=skipped`, `reason=invalid_api_key_format`으로 처리됨
- `--frontend-output` 옵션으로 프론트 전달용 `enabled`, `text`, `display_slot`, `fallback_used`, `metadata` 구조 출력 가능
- `turn_flavor_text`는 행동별 fixture를 추가했고, 실제 Groq 호출 기준 프론트용 출력 스키마 검증을 완료함

스토리 official 계약이 확정되면 fixture의 `case_id`, `info_target_key`, 공식 문장과 expected output을 다시 맞춰야 한다.

## Evaluation 상태

아래 평가 예시를 만들었다.

```text
llm/evaluation/examples/result_summary.expected.md
llm/evaluation/examples/style_summary.expected.md
llm/evaluation/examples/match_log_summary.expected.md
llm/evaluation/examples/forbidden_outputs.md
```

이 파일들은 공식 스토리 문장이나 프론트 표시 문구가 아니다.

LLM 출력 품질을 사람이 비교하기 위한 초안 예시다.

## Guardrail 핵심

LLM 출력에서 아래가 나오면 실패 처리한다.

- 서버 승패와 다른 결말
- official API enum에 없는 결과명
- 입력에 없는 진명 조각
- 입력에 없는 거짓 단서
- 입력에 없는 보상 또는 랭킹
- 입력에 없는 주인공명
- 데모 스토리 고유명사 무단 사용
- 플레이어 성격 단정
- 괴이 다음 행동 단정
- 룰 변경 또는 운영 조치 제안

실패 시 출력은 아래 기준을 따른다.

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

## 다음 작업 순서

### 1. 로컬 `.env` 설정

현재 `.env` 파일은 존재하지만 비어 있다.

집에서 Groq API key를 발급한 뒤 아래처럼 채운다.

```env
LLM_PROVIDER=groq
LLM_API_KEY=실제_Groq_API_key
LLM_MODEL_ID=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=400
LLM_TEMPERATURE=0.4
```

API key는 커밋하지 않는다.

### 2. 환경 변수 설정 계약 추가

다음으로 만들 문서:

```text
llm/generation/config_contract.md
```

정리할 내용:

- `.env` 변수별 필수/선택 여부
- 기본값
- Python에서 읽는 예시
- API key 로그 출력 금지

추천 커밋명:

```text
LLM 환경 변수 설정 계약 추가
```

### 3. Groq 실험 스크립트 추가

추가 완료:

```text
llm/generation/scripts/test_groq_generation.py
```

역할:

- `.env` 읽기
- fixture 읽기
- prompt 조립
- Groq 호출
- 결과 출력
- 실패 시 fallback 구조 출력
- API key placeholder 형식 검사

추천 커밋명:

```text
LLM Groq 실험 스크립트 추가
```

### 4. 간단 guardrail 검사 구현

처음에는 정교한 AI 검사가 아니라 문자열과 enum 기반으로 시작한다.

검사 예:

- `player_win`인데 패배 표현이 있는지 확인
- 입력 없이 `이안`, `피티`, `엘리자베스`가 나왔는지 확인
- 보상, 랭킹, 제재 같은 금지어가 있는지 확인

추천 커밋명:

```text
LLM 금지선 검사 초안 구현
```

### 5. 스토리 확정 후 fixture 업데이트

스토리가 `무명(無名)의 저주`와 `피티` 기준으로 확정되면 아래를 업데이트한다.

- fixture
- expected output
- prompt 예시
- guardrail 고유명사 기준

추천 커밋명:

```text
LLM 스토리 확정 기준 fixture 업데이트
```

## 지금 추천 커밋명

현재까지 정리한 작업을 묶는다면:

```text
LLM 기본 구조와 Groq 실험 준비 정리
```
