# Branch Integration And Document Audit Report

작성일: 2026-06-06
작업 브랜치: `feature-backend-structure`

## 범위

- `origin/feature-llm`의 최상위 `llm/` 산출물과 `ops/env/llm.env.example`을 현재 브랜치에 반영했다.
- `origin/feature-frontend-game-screen`의 `frontend/` 산출물을 현재 브랜치에 반영했다.
- 프론트 프로토타입은 내부 데모 키를 유지하되, Django API 제출 경계에서 official enum payload를 만들도록 `buildTurnSubmitPayload()`를 추가했다.
- official API에 없는 `turn_result.llm_text`, `llm_ui_texts` 백엔드 응답 필드는 추가하지 않았다.
- `backend/apps/llm/` 서버 연결 앱, generation log 저장, 실제 LLM provider 호출의 백엔드 연결은 구현하지 않았다.

## 구현 반영 요약

### LLM

- 추가된 구조:
  - `llm/prompts/`
  - `llm/generation/`
  - `llm/fixtures/`
  - `llm/evaluation/`
  - `llm/tests/`
  - `llm/docs/`
- 핵심 구현:
  - `llm/generation/adapter.py`
  - `llm/prompts/prompt_templates.py`
  - `llm/tests/test_guardrail_contract.py`
  - `llm/tests/test_official_fixture_contract.py`
- 성격:
  - 최상위 `llm/` 실험/프롬프트/평가 영역이다.
  - 백엔드 runtime dependency lock에는 `groq`를 추가하지 않았다.
  - SDK가 없으면 `urllib` fallback 경로가 있고, 테스트는 provider 호출 없이 dry-run/guardrail 중심으로 동작한다.

### Frontend

- 추가된 구조:
  - `frontend/package.json`
  - `frontend/vite.config.ts`
  - `frontend/src/app/router/AppRouter.tsx`
  - `frontend/src/features/match/RitualDuelScreen.tsx`
  - `frontend/public/prototype/*`
- 현재 React 앱은 프로토타입 HTML을 iframe으로 띄우는 wrapper다.
- `frontend/public/prototype/game-background.js`에 official API payload builder를 추가했다.
  - `deceive` 내부 UI 키는 API 제출 시 `trick`으로 변환된다.
  - 데모 정보 대상 키는 API 제출 시 official `mirror_*`, `missing_child_voice`, `forgotten_room`, `self_reflection` 키로 변환된다.
- `frontend/scripts/verify-official-enums.mjs`와 `npm run test:contracts`를 추가했다.

## 문서 의도와 잘 맞는 부분

### 1. Monorepo 최상위 폴더 구조

문서:
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`
- `docs/09_Approved_Contracts/00_승인본_목차.md`

판정: 정렬됨.

근거:
- `frontend/`와 `llm/`가 최상위 폴더로 존재한다.
- `llm/`는 prompt, generation, evaluation, fixtures, docs 중심으로 구성됐다.
- `frontend/`는 React + TypeScript + Vite 프로젝트로 구성됐다.

### 2. LLM 서버 연결 경계

문서:
- `docs/09_Approved_Contracts/08_LLM_도입_기준.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

판정: 현재 반영분은 정렬됨.

근거:
- 최상위 `llm/`에 prompt 실험, 평가 샘플, provider adapter 실험을 둔 것은 문서 의도와 맞다.
- `backend/apps/llm/`은 만들지 않았다.
- 백엔드 API 응답이나 저장 로직에 LLM 결과를 연결하지 않았다.

주의:
- `llm/generation/adapter.py`는 실제 provider 호출 함수까지 포함한다. 최상위 `llm/` 실험 범위로는 허용 가능하지만, 이를 backend runtime에 직접 import해서 연결하면 `backend/apps/llm/` 경계 원칙을 다시 확인해야 한다.

### 3. LLM은 서버 판정을 바꾸지 않음

문서:
- `docs/09_Approved_Contracts/08_LLM_도입_기준.md`
- `docs/09_Approved_Contracts/13_프론트팀_전달_기준.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

판정: 정렬됨.

근거:
- LLM adapter는 `result_summary`, `turn_flavor_text`, `style_summary`, `match_log_summary` 목적의 텍스트 후보만 만든다.
- guardrail은 승패 충돌, 단서/진실 임의 생성, 다음 행동 예측, 플레이어 성격 낙인을 막는다.
- official fixture dry-run 테스트가 있다.

### 4. 백엔드 LLM/PvP/Realtime 금지선

문서:
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`

판정: 정렬됨.

근거:
- `backend/apps/realtime/`을 추가하지 않았다.
- `channels`, `redis`, `corsheaders`, `simplejwt`를 runtime dependency로 추가하지 않았다.
- 프론트에서도 WebSocket, token storage, Bearer token 저장 구조가 검색되지 않았다.

### 5. official enum 경계

문서:
- `api-spec/pilot-mvp-api.official.json`
- `api-spec/pilot-mvp-api.official.jsonc`

판정: API 제출 경계는 정렬됨.

근거:
- backend는 `trick`, `mirror_surface`, `mirror_back`, `missing_child_voice`, `forgotten_room`, `self_reflection`을 사용한다.
- frontend prototype은 `buildTurnSubmitPayload()`에서 official payload를 만든다.
- `npm run test:contracts`로 이 경계를 검증한다.

## 부분적으로 맞는 부분

### 1. Frontend 구현 상태

문서:
- `docs/09_Approved_Contracts/15_프론트_기술_계약_오너_확정안.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

판정: 부분 정렬.

근거:
- React + TypeScript + Vite app은 있다.
- 하지만 실제 화면 대부분은 `public/prototype`의 HTML/CSS/JS이고, React는 iframe wrapper 역할만 한다.
- 로그인, 로비, 사건 선택, 브리핑, 프로필 등 route 구현은 아직 없다.
- 실제 Django API fetch는 없다.

영향:
- 화면 시연은 가능하지만, official API 연결형 프론트 구현으로 보기는 이르다.

### 2. LLM result summary

문서:
- `api-spec/pilot-mvp-api.official.json`
- `docs/09_Approved_Contracts/08_LLM_도입_기준.md`

판정: 부분 정렬.

근거:
- official `MatchResult.llm_summary` schema는 존재한다.
- LLM 쪽에는 `result_summary` fixture와 prompt가 있다.
- 하지만 `GET /api/v1/matches/{match_id}/result`는 아직 501이다.
- 따라서 `llm_summary` runtime 연결은 아직 없다.

### 3. `turn_flavor_text`

문서:
- `llm/docs/backend_integration_checklist.md`
- `llm/docs/frontend_handoff.md`

판정: 의도는 정리됐지만 API 계약은 미확정.

근거:
- LLM 문서도 `turn_flavor_text`의 official API 필드 위치가 아직 확정되지 않았다고 명시한다.
- official `TurnResult`에는 `llm_text`나 `llm_ui_texts`가 없다.
- 백엔드는 official schema 밖 필드를 추가하지 않았다.

영향:
- 현재 프론트 prototype은 `llm_ui_texts` 후보를 받을 수 있지만, 백엔드 official API는 아직 이 값을 내려줄 수 없다.

### 4. backend API endpoint 진행률

문서:
- `api-spec/pilot-mvp-api.official.json`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`

판정: 부분 정렬.

근거:
- official endpoint 13개 중 실제 runtime 구현은 10개다.
- 남은 501 stub:
  - `auth.signup`
  - `auth.logout`
  - `matches.result`
- 미구현 service가 `SERVICE_NOT_IMPLEMENTED` envelope를 쓰는 것은 문서 의도와 맞지만, MVP 완료 상태는 아니다.

## 위배 또는 위험 항목

### 1. frontend prototype 내부 키와 문서가 official enum과 다름

판정: 위험. API 경계에서는 보정했지만 내부 문서/프로토타입은 혼재 상태다.

근거:
- `frontend/public/prototype/game-background.js` 내부 로직은 여전히 `deceive`를 UI action key로 사용한다.
- `frontend/public/prototype/frontend_backend_reply.md`는 `deceive`, `truth_mirror`, `attic_diary`, `stitched_mouth`, `bloodied_teddy`, `ian_reflection`을 백엔드 요청 후보처럼 적고 있다.
- official schema는 `trick`, `mirror_surface`, `mirror_back`, `missing_child_voice`, `forgotten_room`, `self_reflection`이다.

현재 완화:
- `buildTurnSubmitPayload()`가 API 제출 payload를 official enum으로 변환한다.
- `frontend/scripts/verify-official-enums.mjs`가 이 경계를 검증한다.

남은 위험:
- 개발자가 내부 prototype 키를 그대로 API 요청에 쓰면 official API와 충돌한다.
- 프로토타입 문서가 백엔드 계약 문서처럼 오해될 수 있다.

### 2. LLM demo fixture가 official enum과 섞여 있음

판정: 위험. README에서 demo 후보로 구분하지만, 샘플 파일명만 보면 official처럼 오해할 수 있다.

근거:
- `llm/fixtures/turn_flavor_text.sample.json`
- `llm/fixtures/turn_flavor_text.insight.sample.json`
- `llm/fixtures/match_log_summary.sample.json`

이 파일들은 `attic_diary`, `stitched_mouth`, `truth_mirror` 같은 demo key를 사용한다.

완화:
- `llm/fixtures/README.md`가 official enum과 demo enum 차이를 기록한다.
- `turn_flavor_text.official.sample.json`, `result_summary.official.sample.json`이 따로 존재한다.

남은 위험:
- backend 연결 테스트에는 `.official.sample.json`만 사용해야 한다.

### 3. LLM 길이 기준 문서가 서로 다름

판정: 불일치.

근거:
- `llm/generation/adapter.py`와 `llm/evaluation/guardrail_checklist.md`는 `turn_flavor_text`를 10-60자, 1-2줄, 줄당 40자 이하로 제한한다.
- `llm/docs/frontend_handoff.md` 일부는 20-90자, 줄당 45자 이하 기준을 언급한다.
- `frontend/public/prototype/frontend_to_backend_llm_display_answers.md`는 권장 40자, 절대 상한 60자를 제시한다.

권장:
- 최종 기준은 프론트 답변과 adapter 구현에 맞춰 10-60자, 1-2줄, 줄당 40자 이하로 통일하는 것이 안전하다.

### 4. 실제 DB migration 적용 검증 미완료

판정: 검증 미완료.

근거:
- `makemigrations --dry-run --check`는 model diff 없음.
- `migrate --check`는 PostgreSQL connection timeout으로 실패했다.

영향:
- migration 파일 자체는 생성됐지만 실제 DB 적용 여부는 아직 증명되지 않았다.

## 제대로 확정되지 않은 항목

1. `turn_flavor_text`를 official API 응답 어디에 둘지 미확정이다.
2. `generation_id`를 어떤 테이블/식별자로 저장할지 미확정이다.
3. `LLM_SUMMARY_UNAVAILABLE`을 runtime에서 error envelope로 남길지, metadata로만 남길지 미확정이다.
4. `matches.result`의 `result_reason`, `story_result_text`, `style_summary`, `llm_summary` 조립 방식은 아직 구현 전이다.
5. `auth.signup` profile 생성 정책과 초기값은 아직 확정되지 않았다.
6. `auth.logout` refresh family 식별 정책은 문서상 미확정이라 501 유지가 맞다.
7. 프론트 prototype 내부 demo story key를 official story key로 전면 교체할지, 내부 UI key로 유지하고 API 경계에서만 변환할지 최종 결정이 필요하다.
8. 실제 Groq model id, rate limit, API key 운영 방식은 아직 실제 호출 검증 전이다.

## 진행률 추정

| 영역 | 문서 의도 대비 상태 |
|---|---|
| backend official API | 13개 endpoint 중 10개 runtime 구현. `signup`, `logout`, `result` 남음 |
| backend game/story turn flow | 매치 시작, 조회, 턴 제출, 턴 결과 저장까지 구현. 결과 조회 남음 |
| LLM standalone workspace | prompt, adapter, fixture, guardrail 테스트까지 구현. backend runtime 연결은 없음 |
| frontend game/result 화면 | 프로토타입 화면과 Vite build 가능. API 연결형 React 구현은 아직 초기 |
| 문서 경계 준수 | 큰 경계는 준수. demo enum과 LLM 응답 위치는 혼재/미확정 |

## 검증 기록

실행 위치: `D:\dev\Project\SKN27-4th-3team`

- `npm run test:contracts`
  - 위치: `frontend`
  - 결과: PASS
- `npm run build`
  - 위치: `frontend`
  - 결과: PASS, Vite build succeeded
- `.\.venv\Scripts\python.exe -m unittest discover llm\tests -v`
  - 결과: PASS, 8 tests OK
- `.\.venv\Scripts\python.exe -m pytest backend\tests -q`
  - 결과: PASS, 146 passed
- `.\.venv\Scripts\python.exe backend\manage.py check`
  - 결과: PASS, no issues
- `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval --dry-run --check --noinput -v 2`
  - 결과: PASS for model diff, `No changes detected`
  - 경고: DB migration history check에서 PostgreSQL connection timeout
- `.\.venv\Scripts\python.exe backend\manage.py migrate --check --noinput`
  - 결과: FAIL
  - 원인: PostgreSQL connection timeout
- `git diff --check`
  - 결과: PASS, CRLF warning only

## 결론

현재 반영은 문서의 큰 구조 의도와 대체로 맞다.

다만 "완성"이라고 보기는 어렵다. LLM은 최상위 실험/계약/guardrail 단계이고, frontend는 prototype 화면 단계이며, backend와의 runtime 연결은 아직 제한적이다. 가장 큰 정리 대상은 `turn_flavor_text` official API 위치, frontend prototype demo enum, `matches.result` 구현이다.
