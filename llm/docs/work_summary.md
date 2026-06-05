# LLM 작업 요약

이 문서는 현재까지 정리한 LLM 파트 작업 현황과 다음 작업 순서를 기록한다.

## 현재 상태

LLM 파트는 Groq 호출, 프롬프트 템플릿, guardrail, fallback, 프론트 전달용 응답 계약, 백엔드 import용 adapter 함수까지 정리된 상태다.

백엔드 연결용 핵심 코드는 `llm/generation/adapter.py`에 있고, 실제 실행 프롬프트는 `llm/prompts/prompt_templates.py`에 있다.

로컬 실험 CLI는 `llm/generation/scripts/test_groq_generation.py`에 있으며, fixture 기반 dry-run과 실제 Groq 호출을 모두 지원한다.

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
- LLM 실패 시 `enabled=false`, `text=null`, `fallback_used=true`로 내려보내고 서버 기본 문장을 사용한다.

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

현재 로컬 실험에서는 `llama-3.1-8b-instant`로 실제 호출을 확인했다.

모델은 팀 상황과 Groq 사용 가능 목록에 따라 변경할 수 있다.

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
| `llm/docs/frontend_handoff.md` | React 프론트 팀원 전달용 LLM 응답 계약과 확인 사항 |
| `llm/docs/backend_integration_checklist.md` | official API 기준 백엔드 연동 전 점검 항목 |
| `llm/prompts/prompt_templates.py` | 실제 Groq 호출에 사용하는 프롬프트 조립 코드 |
| `llm/prompts/prompt_assembly.md` | fixture를 prompt로 조립하는 규칙 |
| `llm/generation/adapter_contract.md` | Groq adapter 입출력과 실패 처리 계약 |
| `llm/generation/config_contract.md` | LLM 환경 변수와 key 처리 계약 |
| `llm/generation/adapter.py` | 백엔드 import용 LLM adapter 함수 |
| `llm/generation/scripts/test_groq_generation.py` | fixture 기반 prompt 조립과 Groq 호출 실험 CLI |
| `llm/generation/groq_setup_checklist.md` | Groq 실제 연결 전 체크리스트 |
| `llm/evaluation/guardrail_checklist.md` | LLM 금지선 검사 기준 |
| `llm/tests/` | guardrail과 official fixture dry-run 계약 테스트 |
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
- `LLM_DISABLED=true` 또는 API key/model id 누락 시 fallback 구조로 처리됨
- `--frontend-output` 옵션으로 프론트 전달용 `enabled`, `text`, `display_slot`, `fallback_used`, `metadata` 구조 출력 가능
- `turn_flavor_text`는 행동별 fixture를 추가했고, 실제 Groq 호출 기준 프론트용 출력 스키마 검증을 완료함
- `generate_llm_ui_text(purpose, payload)` 함수로 백엔드에서 adapter를 직접 호출할 수 있음
- `turn_flavor_text` 괴이 반응 문구는 PDF 서사 참고에 맞춰 피티 페르소나 기준을 추가함
- 피티는 단순 악역이 아니라 이름과 목소리를 빼앗긴 상처의 잔향처럼 표현하도록 조정함
- 노골적 협박보다 거울, 침묵, 이름, 시선, 금속 냄새, 식은 손끝 같은 감각 이미지를 우선하도록 프롬프트를 보강함

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
- `turn_flavor_text`에서 공개 로그에 없는 비밀, 진실, 파괴, 소유, 원인 관계를 덧붙이는 표현
- `turn_flavor_text`에서 `공개 로그`, `출력:`, `예시` 같은 라벨을 그대로 출력하는 경우
- `turn_flavor_text`에서 `무엇인가`, `누군가`, `보이기 시작`, `온도에`, `냄새가 났다`처럼 모호하거나 추상적인 표현

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

## 내일 이어서 할 일

### 1. 프론트 팀원과 display_slot 확정

공유 문서:

```text
llm/docs/frontend_handoff.md
```

확인할 것:

- 실제 사용할 `display_slot` 값 목록
- `turn_flavor_text` 20-90자, 1-2줄, 줄당 45자 기준이 UI에 맞는지
- `\n` 줄바꿈을 그대로 렌더링할지
- `enabled=false`일 때 LLM 영역을 숨길지, `publicLog.text`를 같은 위치에 보여줄지
- LLM 응답이 턴 결과와 같이 내려올지, 늦게 따로 도착할지

### 2. 백엔드 실제 payload와 adapter 연결

현재 백엔드에서 사용할 함수:

```python
from llm.generation.adapter import generate_llm_ui_text

llm = generate_llm_ui_text("turn_flavor_text", turn_payload)
```

확인할 것:

- 실제 `TurnResult` 필드명이 fixture와 맞는지
- 실제 `MatchResult` 필드명이 fixture와 맞는지
- API 응답에서 `llm` 필드를 어디에 붙일지
- LLM 호출을 동기 처리할지, 지연/비동기 처리할지

### 3. 프롬프트 품질 추가 점검

오늘 보강한 내용:

- 피티 페르소나 기준 추가
- 시스템 위치와 괴이 반응 위치 문체 분리
- 막연한 감각 표현과 예시 라벨 출력 guardrail 보강

내일 확인할 것:

- 실제 프론트 화면에서 괴이 반응 문구가 너무 길거나 겹치지 않는지
- `right_apparition_message`에서 피티 목소리가 충분히 살아나는지
- `left_system_message`, `center_system_message`에서 괴이 직접 발화가 과하지 않은지
- Groq 호출 결과가 guardrail 실패로 자주 떨어지는 케이스가 있는지

### 4. 스토리 확정 후 fixture 업데이트

스토리가 `무명(無名)의 저주`와 `피티` 기준으로 확정되면 아래를 업데이트한다.

- fixture
- expected output
- prompt 문서
- guardrail 고유명사 기준
- 프론트 결과/턴 화면 공식 문장

## 최근 추천 커밋명

```text
refactor: 피티 괴이 페르소나 프롬프트 보강
```
