# Backend Implementation Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프론트엔드와 LLM generation을 제외하고, 승인 문서 기준의 백엔드 구현 순서와 확인 지점을 단계별로 고정한다.

**Architecture:** 구현은 문서 승인 계약을 source of truth로 삼고, 순수 도메인 규칙 → Django 골격 → Auth/Profile → Match/Turn 저장 → Story 데이터 → AI Profile 저장 → Retrieval 준비 → API 연결 순서로 진행한다. 각 단계는 TDD RED/GREEN, 계약 문서 대조, 전체 테스트 검증을 통과해야 다음 단계로 넘어간다. 미승인 문서나 불명확한 요구가 발견되면 구현하지 않고 오너 확인으로 멈춘다.

**Tech Stack:** Python 3.14, pytest, Django/DRF 예정, PostgreSQL + pgvector 예정, jsonschema 예정, HttpOnly cookie JWT 예정.

---

## 적용 범위

이 문서는 아래 범위만 다룬다.

- `backend/apps/game_rules`
- `backend/apps/ai_profile`
- `backend/config`
- `backend/apps/accounts`
- `backend/apps/profiles`
- `backend/apps/matches`
- `backend/apps/story`
- `backend/apps/retrieval`
- `api-spec/pilot-mvp-api.official.jsonc`
- `ops/docker`, `ops/env`

명시적으로 제외한다.

- `frontend/` 구현
- 최상위 `llm/` 구현
- LLM provider, prompt, generation 구현
- WebSocket/realtime 구현
- PvP 모드 구현
- KAG 구현
- 운영 배포 자동화

이 문서는 승인 문서를 대체하지 않는다. 충돌 시 `docs/09_Approved_Contracts/*`, `docs/02_Game_Rules/*`, `docs/03_Backend/99_Backend_구현_확정.md`, `docs/06_AI_Profile/99_AI_Profile_구현_확정.md`, `api-spec/pilot-mvp-api.official.jsonc`를 우선한다.

---

## 현재 구현 상태

| 영역 | 상태 | 근거 | 확인 명령 |
|---|---|---|---|
| Game Rules 순수 도메인 | 구현됨 | `backend/apps/game_rules/*` | `C:\Python314\python.exe -m pytest backend\tests\game_rules -v` |
| AI Profile 계산 도메인 | 구현됨 | `backend/apps/ai_profile/metrics.py` | `C:\Python314\python.exe -m pytest backend\tests\ai_profile -v` |
| Django project 골격 | 없음 | `manage.py`, settings, dependency file 없음 | `rg --files -g manage.py -g pyproject.toml -g requirements*.txt` |
| Auth/Profile DB/API | 없음 | `backend/apps/accounts`, `backend/apps/profiles` 미구현 | 파일 구조 확인 |
| Match/Turn DB/API | 없음 | `backend/apps/matches` 미구현 | 파일 구조 확인 |
| Story DB/API | 없음 | `backend/apps/story` 미구현 | 파일 구조 확인 |
| Retrieval DB/API | 없음 | `backend/apps/retrieval` 미구현 | 파일 구조 확인 |
| Frontend/LLM | 제외 | 사용자 지시와 승인 문서 | 구현하지 않음 |

---

## 문제 체크표

| 문제 | 영향 | 확인 위치 | 처리 기준 |
|---|---|---|---|
| Django/DRF/simplejwt/jsonschema/pgvector 의존성 버전 미확정 | Django 골격과 Auth 구현 착수 불가 | `memory.md`, dependency file 부재 | 오너 확인 후 dependency file 작성 |
| `05_Story_Mode/02_거울_속의_손님.md` 상태가 `needs-decision` | 공식 문장/단서/트리거 구현 위험 | Story 문서 frontmatter | 구조만 구현하거나, 문장/조건 구현 전 오너 확인 |
| `matches/story` 세부 문서 일부가 `draft` | DB 필드 세부 확정 위험 | `docs/03_Backend/03_매치와_턴_저장.md`, `docs/03_Backend/04_AI_스토리_진행.md` | 승인 계약 17번의 확정 테이블/원칙만 구현 |
| API는 official schema만 승인됨 | draft endpoint 구현 위험 | `api-spec/pilot-mvp-api.official.jsonc` | draft `api-spec/pilot-mvp-api.jsonc` 사용 금지 |
| Auth 보안 요구가 높음 | 잘못 구현 시 구조 재작업 위험 | 계약 20번 | token/CSRF tests 먼저 작성 |
| RAG는 포함이나 판정 권위 없음 | 룰/승패와 결합 위험 | 계약 17번 | retrieval은 검색/로그만, rule 변경 금지 |

---

## 구현 순서 요약

1. 기준선 검증과 문서 대조
2. Django 의존성/프로젝트 골격 확정
3. API envelope와 공통 error contract
4. Accounts/Profile 모델과 Auth 보안 저장 구조
5. Refresh token family/reuse/CSRF cookie 흐름
6. Match/Participant/Turn/Submission/Result 저장 구조
7. Story case/apparition/stage/clue/progress 저장 구조
8. Game Rules resolve service와 Match 저장 연결
9. AI Profile event persistence와 snapshot 계산 연결
10. Retrieval document/chunk/query log 구조
11. Official API endpoint 13개 연결
12. Docker/env 로컬 실행 구성
13. 전체 검증과 남은 리스크 재점검

---

### Task 0: Baseline 확인

**Files:**
- Read: `memory.md`
- Read: `docs/03_Backend/99_Backend_구현_확정.md`
- Read: `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- Read: `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- Read: `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- Read: `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

- [x] **Step 1: 현재 테스트 기준선 실행**

Run: `C:\Python314\python.exe -m pytest backend\tests -v`

Expected: `29 passed`

- [x] **Step 2: 구현 제외 범위 확인**

확인할 금지선:

- `frontend/` 구현 금지
- 최상위 `llm/` 구현 금지
- LLM provider/prompt/generation 구현 금지
- WebSocket/realtime 구현 금지
- PvP 모드 구현 금지
- KAG 구현 금지

- [x] **Step 3: 중단 조건 확인**

아래 중 하나라도 발견되면 구현하지 말고 오너 확인을 요청한다.

- 승인 문서와 draft 문서가 충돌함
- official API schema와 다른 endpoint가 필요함
- dependency 버전 선택이 필요함
- Story 공식 문장/조건이 `needs-decision` 문서에만 있음

---

### Task 1: Django 의존성/프로젝트 골격 확정

**Files:**
- Create after approval: `pyproject.toml` 또는 `requirements.txt`
- Create after approval: `backend/manage.py`
- Create after approval: `backend/config/settings.py`
- Create after approval: `backend/config/urls.py`
- Create after approval: `backend/config/asgi.py`
- Create after approval: `backend/config/wsgi.py`
- Test: `backend/tests/config/test_project_contract.py`

**현재 문제:** Django/DRF/simplejwt/jsonschema/pgvector 의존성 버전이 문서에 고정되어 있지 않다.

- [x] **Step 1: 오너 확인**

확인 질문:

```text
Django/DRF/JWT/jsonschema/pgvector 의존성 버전을 제가 제안해서 고정해도 될까요, 아니면 별도 지정값이 있나요?
```

승인 전에는 dependency file을 만들지 않는다.

2026-06-02에 사용자가 "공식 문서 기준으로 확인해서 제안한 뒤 고정"을 승인했다.

- [x] **Step 2: 실패 테스트 작성**

테스트 목표:

- Django settings module이 존재한다.
- API prefix는 `/api/v1`만 사용한다.
- CSRF middleware가 빠지지 않는다.
- `AUTH_USER_MODEL`은 `accounts.User`다.

Run: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 3: 최소 Django 골격 작성**

구현 기준:

- `backend/config/`는 Django project 설정만 담당한다.
- settings에서 CSRF/CORS 전체 허용 금지.
- Redis, Channels, WebSocket worker 설정 금지.
- LLM emulator 설정 금지.

- [x] **Step 4: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`

Expected: PASS

Run: `C:\Python314\python.exe -m pytest backend\tests -v`

Expected: all tests PASS

---

### Task 2: API envelope와 error contract

**Files:**
- Create: `backend/apps/common/responses.py`
- Create: `backend/apps/common/errors.py`
- Test: `backend/tests/common/test_response_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/06_API_응답_형태_기준.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `api-spec/pilot-mvp-api.official.jsonc`

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 계약:

- 성공 응답은 `{ data, meta }`
- 실패 응답은 `{ error, meta }`
- `meta`에는 `request_id`, `server_time`
- `error`에는 `code`, `message`, `details`

Run: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- response envelope 생성만 담당한다.
- view나 serializer 로직을 섞지 않는다.
- error code 문자열은 official schema의 `error_codes`만 사용한다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`

Expected: PASS

---

### Task 3: Accounts/Profile 모델 계약

**Files:**
- Create: `backend/apps/accounts/models.py`
- Create: `backend/apps/accounts/managers.py`
- Create: `backend/apps/profiles/models.py`
- Test: `backend/tests/accounts/test_user_profile_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 계약:

- `accounts.User`는 custom user model이다.
- base class는 `AbstractBaseUser + PermissionsMixin`.
- 로그인 식별자는 email.
- nickname은 `profiles.Profile`에 저장한다.
- User 모델에 nickname을 직접 저장하지 않는다.

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 모델 구현**

구현 기준:

- `accounts.User`는 인증과 권한만 담당한다.
- `profiles.Profile`은 nickname, 전적 요약, 스타일 요약 표시 데이터를 담당한다.
- profile 생성 side effect는 signal로 숨기지 말고 service 또는 명시 호출로 처리한다. 단, API 구현 시점까지 미뤄도 된다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`

Expected: PASS

---

### Task 4: Refresh token family와 Security Event

**Files:**
- Create: `backend/apps/accounts/tokens.py`
- Modify: `backend/apps/accounts/models.py`
- Test: `backend/tests/accounts/test_refresh_token_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 계약:

- refresh token은 원문 저장 금지.
- `jti`, `family_id`는 UUIDv4.
- 저장 hash는 서버 secret 기반 HMAC-SHA256.
- refresh 성공 시 기존 token은 `rotated`.
- 재사용 감지 시 family 전체 revoke.
- reuse error code는 `REFRESH_TOKEN_REUSED`.

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- token 원문은 모델 필드에 저장하지 않는다.
- DB transaction + row lock은 service 테스트에서 검증한다.
- grace window를 만들지 않는다.
- security event log는 현재 확정된 이벤트 타입과 시각만 모델화한다.
- security event actor/user_id nullable 정책과 metadata schema는 문서 확정 전 구현하지 않는다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`

Expected: PASS

---

### Task 4A: Refresh token/Security Event Review Checkpoint

**Files:**
- Modify: `backend/apps/accounts/tokens.py`
- Modify: `backend/apps/accounts/models.py`
- Modify: `backend/tests/accounts/test_refresh_token_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/03_Backend/99_Backend_구현_확정.md`
- `api-spec/pilot-mvp-api.official.json`

- [x] **Step 1: identifier lifecycle 분리**

검증해야 하는 계약:

- `family_id`는 로그인 성공 시 UUIDv4로 생성한다.
- `jti`는 refresh token 발급마다 UUIDv4로 생성한다.
- refresh rotation에서 helper 오용으로 새 `family_id`를 만들 수 없도록 helper 이름과 역할을 분리한다.

- [x] **Step 2: SecurityEvent actor/metadata 미확정 범위 제거**

검증해야 하는 계약:

- Security Event에는 비인증 이벤트가 포함될 수 있으므로 actor/user_id 정책을 문서 없이 고정하지 않는다.
- SecurityEvent metadata schema가 없으므로 JSONField와 jsonschema helper를 문서 없이 고정하지 않는다.

- [x] **Step 3: 문서에 없는 FK 삭제 정책 제거**

검증해야 하는 계약:

- 승인 문서에 refresh/security event user 삭제 생명주기 정책이 없으므로 `on_delete` 정책을 새로 고정하지 않는다.
- 저장 구조는 현재 확정된 `event_type`, `created_at` 기반으로 좁힌다.

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`

Expected: PASS

---

### Task 5: Auth API와 CSRF 흐름

**Files:**
- Create: `backend/apps/accounts/serializers.py`
- Create: `backend/apps/accounts/views.py`
- Create: `backend/apps/accounts/urls.py`
- Modify: `backend/config/urls.py`
- Test: `backend/tests/accounts/test_auth_api_contract.py`

**Source of truth:**

- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`

- [x] **Step 1: 실패 테스트 작성**

endpoint:

- `GET /api/v1/auth/csrf`
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

검증:

- access/refresh token은 response body에 나오지 않는다.
- access token cookie path는 `/api/v1`.
- refresh token cookie path는 `/api/v1/auth/refresh`.
- state-changing endpoint는 CSRF가 필요하다.
- `csrf_exempt`를 사용하지 않는다.

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- Authorization Bearer header 사용 금지.
- localStorage/sessionStorage를 전제로 한 response 금지.
- login 시 CSRF rotation.
- refresh 시 CSRF 유지.
- logout 후 새 CSRF 필요.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`

Expected: PASS

---

### Task 6: Match/Participant/Turn 저장 구조

**Files:**
- Create: `backend/apps/matches/models.py`
- Create: `backend/apps/matches/services.py`
- Test: `backend/tests/matches/test_match_storage_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 테이블:

- `matches`
- `match_participants`
- `turns`
- `action_submissions`
- `turn_results`

검증:

- 참가자는 `human` 또는 `apparition`.
- 괴이는 Django user가 아니다.
- `user_id`는 human 참가자에서만 사용한다.
- `apparition_id`는 apparition 참가자에서 사용한다.
- 접근 권한은 match user가 아니라 participant membership 기준이다.
- `client_nonce`는 participant + turn 범위에서 중복 금지.

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`

Expected before implementation: FAIL

- [ ] **Step 2: 최소 모델/서비스 구현**

구현 기준:

- AI story 전용 구조로 좁히지 않는다.
- `match.user_id`처럼 단일 소유자만으로 접근 권한을 판단하지 않는다.
- 결과 snapshot JSONField에는 `schema_version` 필수.

- [ ] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`

Expected: PASS

---

### Task 7: Story 저장 구조

**Files:**
- Create: `backend/apps/story/models.py`
- Create: `backend/apps/story/services.py`
- Test: `backend/tests/story/test_story_storage_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/03_Backend/04_AI_스토리_진행.md`

**주의:** `docs/05_Story_Mode/02_거울_속의_손님.md`는 현재 `needs-decision`이다. 공식 문장/단서/트리거 구현은 오너 확인 전까지 하지 않는다.

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 테이블:

- `story_cases`
- `apparitions`
- `stages`
- `true_name_fragments`
- `false_clues`
- `player_story_progress`

검증:

- 사건/괴이/스테이지 FK는 정규화한다.
- 조건 payload JSONField에는 `schema_version` 필수.
- 공식 단서/거짓 단서를 RAG나 LLM 결과로 생성하지 않는다.

Run: `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`

Expected before implementation: FAIL

- [ ] **Step 2: 구조만 최소 구현**

구현 기준:

- 승인 계약 17번의 저장 구조만 구현한다.
- `needs-decision` 상태의 공식 문장/단서 내용은 seed하지 않는다.
- Story API가 내용을 반환해야 하는 시점에는 오너 확인을 먼저 받는다.

- [ ] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`

Expected: PASS

---

### Task 8: Game Rules resolve service 연결

**Files:**
- Create: `backend/apps/matches/resolution.py`
- Modify: `backend/apps/matches/services.py`
- Test: `backend/tests/matches/test_turn_resolution_contract.py`

**Source of truth:**

- `docs/02_Game_Rules/04_상성_규칙.md`
- `docs/02_Game_Rules/05_승패_조건.md`
- `docs/02_Game_Rules/06_시간초과_규칙.md`
- `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`

- [x] **Step 1: 실패 테스트 작성**

테스트해야 하는 계약:

- 제출 마감 이후 요청은 `TURN_DEADLINE_EXPIRED`.
- 제출이 없고 `deadline_at`이 지나면 player action은 `silence`.
- timeout count는 participant 기준으로 증가.
- 결과 계산은 `backend/apps/game_rules`를 사용한다.
- 공개 로그는 문서 확정 문장을 사용한다.
- 같은 턴 승패 동시 발생 시 봉인 성공이 우선한다.

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- LLM/RAG/embedding으로 상성 결과를 바꾸지 않는다.
- 봉인 방해 단계는 상성표 외부에서 임의 가산하지 않는다.
- 공포 상태는 생성하지 않는다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`

Expected: PASS

---

### Task 9: AI Profile persistence 연결

**Files:**
- Create: `backend/apps/ai_profile/models.py`
- Create: `backend/apps/ai_profile/services.py`
- Modify: `backend/apps/matches/resolution.py`
- Test: `backend/tests/ai_profile/test_ai_profile_persistence_contract.py`

**Source of truth:**

- `docs/06_AI_Profile/01_행동_이벤트.md`
- `docs/06_AI_Profile/02_스타일_지표.md`
- `docs/06_AI_Profile/99_AI_Profile_구현_확정.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`

- [x] **Step 1: 실패 테스트 작성**

검증:

- 행동 이벤트는 턴 resolve 시점에 저장한다.
- 스타일 지표는 각 턴 resolve 직후 계산한다.
- 매치 종료 시 최종 재계산한다.
- 분모 0은 `0.0`.
- 개인정보 삭제 시 행동 이벤트와 스타일 스냅샷 삭제.

Run: `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_ai_profile_persistence_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- 기존 `backend/apps/ai_profile/metrics.py` 계산 함수를 재사용한다.
- DB 모델은 저장 책임만 갖는다.
- LLM summary를 스타일 지표 근거로 사용하지 않는다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\ai_profile -v`

Expected: PASS

---

### Task 10: Retrieval 구조

**Files:**
- Create: `backend/apps/retrieval/models.py`
- Create: `backend/apps/retrieval/chunking.py`
- Create: `backend/apps/retrieval/services.py`
- Test: `backend/tests/retrieval/test_retrieval_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/09_RAG_도입_기준.md`

- [x] **Step 1: 실패 테스트 작성**

검증:

- 검색 대상은 승인본 계약, `거울 속의 손님`, 승인된 게임 룰 문서로 제한한다.
- chunk 크기는 500-900자.
- overlap은 최대 100자.
- chunk에는 `document_id`, `chunk_id`, `source_path`, `schema_version`.
- query log에는 query, caller, document_id, chunk_id, score, threshold, top_k, created_at.
- 기본 검색값은 `top_k=6`, `score_threshold=0.72`.
- embedding model id는 env/config 주입이며 코드 하드코딩 금지.

Run: `C:\Python314\python.exe -m pytest backend\tests\retrieval\test_retrieval_contract.py -v`

Expected before implementation: FAIL

- [x] **Step 2: 최소 구현**

구현 기준:

- retrieval 결과로 룰, 승패, 인증/권한, 진명 조각, 거짓 단서를 바꾸지 않는다.
- LLM draft/prompt 초안은 기본 제외한다.
- provider 호출 구현은 하지 않는다.

- [x] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\retrieval -v`

Expected: PASS

---

### Task 11: Official API endpoint 연결

**Files:**
- Modify: `backend/apps/accounts/views.py`
- Create: `backend/apps/story/views.py`
- Create: `backend/apps/matches/views.py`
- Create: `backend/apps/profiles/views.py`
- Modify: `backend/config/urls.py`
- Test: `backend/tests/api/test_official_api_contract.py`

**Source of truth:**

- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`

- [ ] **Step 1: 실패 테스트 작성**

공식 endpoint 13개만 검증한다.

```text
GET  /api/v1/auth/csrf
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
GET  /api/v1/story/cases
GET  /api/v1/story/cases/{case_id}/briefing
POST /api/v1/story/cases/{case_id}/matches
GET  /api/v1/matches/{match_id}
POST /api/v1/matches/{match_id}/turns
GET  /api/v1/matches/{match_id}/result
GET  /api/v1/profile/me
```

금지 endpoint:

```text
/auth/register
/matches/ai-story
/matches/{match_id}/turns/{turn_id}/actions
```

Run: `C:\Python314\python.exe -m pytest backend\tests\api\test_official_api_contract.py -v`

Expected before implementation: FAIL

- [ ] **Step 2: 최소 구현**

구현 기준:

- 모든 응답은 envelope를 따른다.
- access/refresh token을 body에 포함하지 않는다.
- `MATCH_ACCESS_DENIED`는 participant membership 기준이다.
- `INFO_TARGET_REQUIRED`, `INSUFFICIENT_RITUAL_POWER`, `TURN_DEADLINE_EXPIRED`는 validation error로 뭉개지 않는다.

- [ ] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\api\test_official_api_contract.py -v`

Expected: PASS

---

### Task 12: 로컬 Docker/env 구성

**Files:**
- Create: `ops/docker/docker-compose.yml`
- Create: `ops/docker/backend.Dockerfile`
- Create: `ops/env/backend.env.example`
- Test: `backend/tests/ops/test_local_runtime_contract.py`

**Source of truth:**

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

- [ ] **Step 1: 실패 테스트 작성**

검증:

- 로컬 구성은 Django API, PostgreSQL, PostgreSQL `pgvector`만 포함한다.
- Redis 제외.
- WebSocket worker 제외.
- LLM provider emulator 제외.
- KAG 전용 저장소 제외.

Run: `C:\Python314\python.exe -m pytest backend\tests\ops\test_local_runtime_contract.py -v`

Expected before implementation: FAIL

- [ ] **Step 2: 최소 구성 작성**

구현 기준:

- env template에는 secret 실제값을 넣지 않는다.
- production secure cookie는 `Secure=true` 필수, local/dev는 `Secure=false` 허용.
- CORS/CSRF origin은 명시 allowlist만 허용한다.
- `ops/docker/backend.Dockerfile`은 백엔드 이미지 빌드 시작점으로 둔다.
- 현재 Dockerfile entrypoint는 로컬/dev 기준이며 production 배포 entrypoint로 확정하지 않는다.

- [ ] **Step 3: 검증**

Run: `C:\Python314\python.exe -m pytest backend\tests\ops\test_local_runtime_contract.py -v`

Expected: PASS

---

### Task 12C: Dockerfile 이미지 빌드와 Django 배포 준비 문서화

**Files:**
- Read: `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- Read: `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`
- Modify if needed: `docs/03_Backend/99_Backend_구현_확정.md`
- Modify if needed: `README.md`
- Modify if needed: `memory.md`

**Source of truth:**

- 현재 승인 범위: 로컬 Docker Compose와 Dockerfile 기반 이미지 빌드 준비
- 현재 제외 범위: 운영 배포 자동화와 production 배포 구현
- 결정 게이트: `docs/09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약.md`

- [ ] **Step 1: 문서 확인**

확인:

- `ops/docker/`가 Dockerfile과 image build 후보를 담당하는지
- 현재 Dockerfile이 production entrypoint로 확정되어 있지 않음을 문서화했는지
- Django production 배포 전에 확정해야 하는 항목을 남겼는지

- [ ] **Step 2: 후속 배포 계약 전제 기록**

production 배포 전 확정 필요:

- 배포 대상 환경
- image registry와 tag 규칙
- WSGI/ASGI server
- static/media 처리
- secret/env 주입 방식
- migration 실행 전략
- health check
- reverse proxy, TLS, domain
- CI/CD 또는 수동 배포 절차

- [ ] **Step 3: 검증**

Run: `git diff --check`

Expected: PASS

Docker image build는 네트워크/image pull이 필요할 수 있으므로 별도 실행 승인 후 검증한다.

---

### Task 13: 최종 검증과 인수 기준

**Files:**
- Read: all implemented backend files
- Read: `memory.md`
- Modify if needed: `memory.md`

- [ ] **Step 1: 전체 테스트**

Run: `C:\Python314\python.exe -m pytest backend\tests -v`

Expected: all tests PASS

- [ ] **Step 2: 문서 계약 대조**

확인 항목:

- `api-spec/pilot-mvp-api.official.jsonc` 외 draft API를 구현 기준으로 쓰지 않았다.
- LLM/RAG/embedding이 rule outcome을 바꾸지 않는다.
- 프론트 구현이 없다.
- LLM generation 구현이 없다.
- WebSocket/realtime 구현이 없다.
- PvP 모드 구현이 없다.
- KAG 구현이 없다.

- [ ] **Step 3: 남은 리스크 기록**

`memory.md`에 아래를 갱신한다.

- 완료된 구현 범위
- fresh verification command와 결과
- 건너뛴 검증과 이유
- 오너 확인이 필요한 항목

---

## 단계별 완료 기준

각 Task는 아래 조건을 모두 만족해야 완료다.

- RED 테스트를 먼저 실행했고 예상 실패를 확인했다.
- 최소 구현 후 해당 task 테스트가 통과했다.
- 전체 `backend\tests`가 통과했다.
- 승인 문서와 충돌이 없다.
- 구현 제외 범위를 건드리지 않았다.
- 미확정 요구는 추정으로 채우지 않았다.
- `memory.md` 또는 후속 체크 문서에 상태가 기록됐다.

---

## 현재 바로 착수 가능한 범위

현재 승인 문서와 구현 상태 기준으로 바로 착수 가능한 범위:

- `accounts` refresh token family/reuse 정책 테스트 설계
- `matches` participant 중심 권한/nonce 계약 테스트 설계
- `ai_profile` persistence 계약 테스트 설계
- `retrieval` chunk/query log 구조 테스트 설계

착수 전 오너 확인이 필요한 범위:

- Story 공식 문장, 진명 조각 reveal condition, 거짓 단서 trigger condition 구현
- 실제 DB migration까지 포함할지, 순수 모델 계약 테스트부터 진행할지

---

## 추천 다음 작업

가장 안전한 다음 작업은 아래 순서다.

1. Django 의존성 버전 고정 여부 확인
2. `backend/config`와 앱 골격 생성
3. Auth refresh token family/reuse 정책부터 TDD 구현
4. Match participant/turn/nonce 저장 계약 TDD 구현

이 순서가 안전한 이유:

- Auth와 Match 권한 구조가 AI 스토리 API 구조의 기반이다.
- Story 공식 내용은 일부 문서가 `needs-decision`이므로 뒤로 미룬다.
- RAG는 포함 범위지만 rule authority가 아니므로 core 저장/권한 이후에 붙인다.

---

## 진행 기록

### 2026-06-02 Task 0 Baseline 확인

구현/수정한 파일:

- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`

참조한 승인 문서:

- `docs/03_Backend/99_Backend_구현_확정.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

확인한 내용:

- `frontend/`, 최상위 `llm/`, LLM provider/prompt/generation, WebSocket/realtime, PvP 모드, KAG 구현은 현재 범위에서 제외한다.
- `backend/manage.py`, `backend/config/settings.py`, `pyproject.toml`, `requirements*.txt`는 아직 없다.
- Task 1의 Django/DRF/JWT/jsonschema/pgvector 의존성 버전은 구현 전 오너 확인이 필요하다.

검증:

- 실행 위치: `D:\dev\Project\pilot`
- 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 결과: `29 passed`

남은 리스크:

- dependency version이 아직 승인되지 않아 Task 1 구현은 대기 상태다.

### 2026-06-02 Task 1 Django 의존성/프로젝트 골격 확정

구현/수정한 파일:

- 생성: `requirements.txt`
- 생성: `backend/manage.py`
- 생성: `backend/config/__init__.py`
- 생성: `backend/config/settings.py`
- 생성: `backend/config/urls.py`
- 생성: `backend/config/asgi.py`
- 생성: `backend/config/wsgi.py`
- 생성: `backend/apps/accounts/apps.py`
- 생성: `backend/apps/profiles/apps.py`
- 생성: `backend/apps/game_rules/apps.py`
- 생성: `backend/apps/matches/apps.py`
- 생성: `backend/apps/story/apps.py`
- 생성: `backend/apps/ai_profile/apps.py`
- 생성: `backend/apps/retrieval/apps.py`
- 생성/수정: `backend/tests/config/test_project_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서:

- `docs/03_Backend/99_Backend_구현_확정.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

공식 출처 기준 의존성 고정:

- `Django==5.2.14`: 승인 Auth 문서가 Django 5.2 CSRF/Security 문서를 기준으로 삼고, Django 5.2 LTS 최신 패치가 5.2.14이므로 고정.
- `djangorestframework==3.17.1`: DRF release notes 기준 최신 3.17 계열이며 Python 3.14 지원.
- `PyJWT==2.13.0`: refresh token family/reuse 정책을 직접 구현하기 위해 Simple JWT 대신 JWT 라이브러리만 사용.
- `jsonschema==4.26.0`: JSONField payload 검증 계약용.
- `pgvector==0.4.2`: PostgreSQL + pgvector RAG 저장 구조 준비용.
- `psycopg[binary]==3.3.4`: Django PostgreSQL 연결용 현재 최신 Psycopg 3.

확인한 내용:

- API prefix는 `/api/v1`로 고정했다.
- `AUTH_USER_MODEL`은 `accounts.User`로 고정했다.
- Django CSRF middleware를 설정에 포함했다.
- CSRF/CORS origin은 기본 빈 allowlist이며 wildcard를 넣지 않았다.
- access/refresh token cookie path, SameSite, TTL을 승인 문서 값으로 고정했다.
- Redis, Channels, WebSocket worker, LLM emulator, KAG/realtime 앱 설정은 추가하지 않았다.
- endpoint 구현은 Task 11 범위이므로 `backend/config/urls.py`는 빈 `urlpatterns`만 둔다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
- RED 결과: `6 failed`; `requirements.txt`, `backend/manage.py`, `backend/config`, 앱 `apps.py` 누락으로 실패.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
- GREEN 결과: `7 passed`
- 추가 RED 실행 위치: `D:\dev\Project\pilot`
- 추가 RED 명령: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
- 추가 RED 결과: `1 failed, 6 passed`; `backend/manage.py`가 `backend.config.settings` import를 위해 프로젝트 루트를 `sys.path`에 추가하지 않아 실패.
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `36 passed`

건너뛴 검증:

- `pip install -r requirements.txt`는 네트워크/환경 설치 작업이어서 수행하지 않았다.
- `backend/manage.py check`는 Django dependency가 현재 로컬 Python 환경에 설치되어 있지 않아 수행하지 않았다.
- DB 연결, migration, API endpoint 검증은 아직 해당 Task 구현 범위가 아니다.

남은 리스크:

- Django 패키지를 실제 설치한 뒤 `manage.py check`와 DB migration 검증이 필요하다.
- `accounts.User` 모델은 아직 구현되지 않았으므로 Django 전체 앱 로딩은 다음 모델 Task 전까지 완전하지 않다.

### 2026-06-02 Task 1 Review Follow-up

검토한 피드백:

- `backend/config/settings.py`의 `RAG_EMBEDDING_MODEL_ID` 기본값 문자열은 `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`의 "환경 설정으로 주입" 및 "모델 이름 코드 하드코딩 금지"와 충돌한다.
- `AUTH_USER_MODEL = "accounts.User"`는 승인 문서와 맞지만, 실제 모델 미구현으로 `manage.py check` 검증은 Task 3 전까지 남은 리스크다.
- CSRF/CORS allowlist 테스트가 기본값만 확인하고 env wildcard 입력을 막지 못했다.

구현/수정한 파일:

- 수정: `backend/config/settings.py`
- 수정: `backend/tests/config/test_project_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

변경 내용:

- `RAG_EMBEDDING_MODEL_ID`에서 `"text-embedding-3-small"` 코드 기본값을 제거하고 env 값만 읽도록 변경했다.
- `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_CORS_ALLOWED_ORIGINS`에 wildcard가 포함되면 settings load 단계에서 `RuntimeError`가 발생하도록 변경했다.
- RAG embedding model id가 env로만 주입되는지, CSRF/CORS origin wildcard env가 거부되는지 테스트를 추가했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
- RED 결과: `2 failed, 7 passed`; RAG embedding model id 코드 기본값과 CSRF/CORS wildcard env 허용이 실패로 잡힘.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
- GREEN 결과: `9 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `38 passed`

남은 리스크:

- 추천 embedding model id `text-embedding-3-small`은 코드가 아니라 Task 12의 env template 또는 배포 설정 문서에 기록해야 한다.
- 실제 CORS 응답 처리는 아직 CORS 미들웨어/dependency가 없으므로, 프론트 origin 요구가 확정되는 API 연결 단계에서 별도 검증이 필요하다.

### 2026-06-02 Task 1 Runtime Caution Confirmation

검토한 피드백:

- `backend/config/settings.py`의 `CORS_ALLOWED_ORIGINS`는 명시 allowlist 설정값이지만, 현재 `django-cors-headers` dependency 또는 `CorsMiddleware`는 없다.
- `backend/config/settings.py`의 `AUTH_USER_MODEL = "accounts.User"`는 승인 문서와 일치하지만, `backend/apps/accounts/models.py`는 아직 없다.

판단:

- CORS 항목은 현재 단계의 문서 불일치가 아니다. Task 1에서는 전체 허용 금지와 명시 allowlist만 고정했고, 실제 CORS 응답 처리는 아직 완료되지 않았다.
- `accounts.User` 항목도 문서 불일치가 아니다. Task 1은 settings 골격 고정 단계이고, custom user model 구현은 Task 3 범위다.
- 따라서 `manage.py check` 또는 Django runtime check 통과를 Task 1 완료 증거로 사용하지 않는다.

확인한 내용:

- `rg "corsheaders|django-cors|CorsMiddleware" requirements.txt backend` 결과, 실제 CORS middleware/dependency는 없다.
- `Get-ChildItem backend\apps\accounts -Force` 결과, 현재 `apps.py`만 있고 `models.py`는 없다.

후속 처리 기준:

- 실제 CORS 응답 처리는 프론트 origin 요구와 API 연결 단계에서 dependency/middleware 포함 여부를 다시 결정한다.
- `accounts.User` 구현 전까지 Django 전체 앱 로딩, `manage.py check`, migration 검증은 완료로 취급하지 않는다.

### 2026-06-02 Task 2 API envelope와 error contract

구현/수정한 파일:

- 생성: `backend/apps/common/__init__.py`
- 생성: `backend/apps/common/errors.py`
- 생성: `backend/apps/common/responses.py`
- 생성: `backend/tests/common/test_response_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `docs/09_Approved_Contracts/06_API_응답_형태_기준.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `api-spec/pilot-mvp-api.official.json`
- `api-spec/pilot-mvp-api.official.jsonc`

변경 내용:

- 성공 envelope 생성 함수는 `{ data, meta }`만 반환한다.
- 실패 envelope 생성 함수는 `{ error, meta }`만 반환한다.
- `meta`는 `request_id`, `server_time`을 필수로 가진다.
- `meta` 추가 필드는 허용하지만 `request_id`, `server_time` 덮어쓰기는 거부한다.
- `error`는 `code`, `message`, `details`를 필수로 가진다.
- error code catalog는 official schema의 `error_codes`와 일치하도록 고정했고, `MappingProxyType`으로 런타임 수정을 막았다.
- view, serializer, DB, Django/DRF response 객체는 아직 섞지 않았다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
- RED 결과: `7 failed`; `backend.apps.common.errors`, `backend.apps.common.responses` 모듈 누락으로 실패.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
- GREEN 결과: `7 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `45 passed`

남은 리스크:

- 현재 envelope helper는 pure Python dict 생성기다. DRF `Response`, exception handler, middleware/request-id 연동은 API endpoint 구현 단계에서 별도 연결해야 한다.
- official schema가 변경되면 `backend/apps/common/errors.py`의 error code catalog도 함께 갱신해야 하며, 현재 테스트가 그 불일치를 잡는다.

### 2026-06-02 Task 2 Review Follow-up

검토한 피드백:

- `backend/apps/common/errors.py`의 `ApiError` 생성자가 public이고, `message`를 임의 문자열로 받을 수 있어 `make_api_error()`를 우회하면 official schema의 error message 계약을 벗어날 수 있다.
- `API_ERROR_MESSAGES` 문자열 상수 복제는 `backend/tests/common/test_response_contract.py`가 official schema와 완전 일치를 검증하므로 현재는 임의 하드코딩으로 보지 않는다.

구현/수정한 파일:

- 수정: `backend/apps/common/errors.py`
- 수정: `backend/tests/common/test_response_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

변경 내용:

- `ApiError.__post_init__`에서 `message == API_ERROR_MESSAGES[code]`를 강제했다.
- `ApiError(code="MATCH_NOT_FOUND", message="wrong message")` 직접 생성이 실패하는 테스트를 추가했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
- RED 결과: `1 failed, 7 passed`; `ApiError` 직접 생성으로 official message 우회 가능성이 실패로 잡힘.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
- GREEN 결과: `8 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `46 passed`

남은 리스크:

- official schema가 변경되면 `API_ERROR_MESSAGES` 복제 상수를 함께 갱신해야 한다. 현재 테스트가 schema 불일치를 잡지만 자동 생성은 아직 구현하지 않았다.

### 2026-06-02 Task 3 Accounts/Profile 모델 계약

구현/수정한 파일:

- 생성: `backend/apps/accounts/__init__.py`
- 생성: `backend/apps/accounts/managers.py`
- 생성: `backend/apps/accounts/models.py`
- 생성: `backend/apps/profiles/__init__.py`
- 생성: `backend/apps/profiles/models.py`
- 생성: `backend/tests/accounts/test_user_profile_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/03_Backend/02_인증과_토큰.md`
- `api-spec/pilot-mvp-api.official.json`

변경 내용:

- `accounts.User`를 `AbstractBaseUser + PermissionsMixin` 기반 custom user model 소스로 추가했다.
- 로그인 식별자를 `email`로 고정하고, `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`를 설정했다.
- `accounts.User`에는 인증/권한 상태인 `email`, `is_active`, `is_staff`, `created_at`만 두고 nickname/전적/스타일 표시 필드는 넣지 않았다.
- `accounts.UserManager`는 email 정규화, password hashing, superuser 권한 플래그 검증을 담당한다.
- `profiles.Profile`은 `settings.AUTH_USER_MODEL`과 `OneToOneField`로 연결하고, nickname, AI story 전적 요약, style label/display text/update time을 담당한다.
- profile 생성 side effect를 signal로 숨기지 않았다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- RED 결과: `4 failed, 1 passed`; `accounts/models.py`, `accounts/managers.py`, `profiles/models.py` 누락으로 실패.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- GREEN 결과: `5 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `51 passed`

건너뛴 검증:

- 현재 Python 환경에 Django가 설치되어 있지 않아 `manage.py check`, migration 생성/적용, DB runtime 검증은 수행하지 않았다.
- Task 3 테스트는 승인 계약에 맞춘 정적 소스 계약 검증이다.

남은 리스크:

- Django dependency 설치 후 `manage.py check`, migration 검증이 필요하다.
- nickname 길이 제한, nickname 고유성, profile 생성 서비스 호출 시점은 승인 문서에 아직 구체 값이 없어 구현하지 않았다.
- Refresh token 저장 모델과 Security Event Log는 Task 4 범위다.

### 2026-06-02 Task 3 Review Follow-up

검토한 피드백:

- `backend/apps/accounts/models.py`의 `db_table = "accounts_users"`와 `backend/apps/profiles/models.py`의 `db_table = "profiles_profiles"`는 승인 문서에서 확정한 값이 아니다.
- `backend/tests/accounts/test_user_profile_contract.py`도 문서에 없는 테이블명을 계약처럼 강제하고 있었다.

판단:

- 테이블명은 현재 승인 문서의 source of truth에 없다.
- 따라서 구현과 테스트에서 테이블명을 새로 고정하는 것은 문서 기반 구현 원칙과 하드코딩 금지 원칙에 맞지 않는다.

구현/수정한 파일:

- 수정: `backend/apps/accounts/models.py`
- 수정: `backend/apps/profiles/models.py`
- 수정: `backend/tests/accounts/test_user_profile_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

변경 내용:

- `accounts.User`, `profiles.Profile`에서 `Meta.db_table` 지정을 제거했다.
- 테스트는 특정 테이블명을 강제하지 않고, 문서에 없는 `db_table` 고정이 없는지를 검증하도록 변경했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- RED 결과: `2 failed, 3 passed`; 문서에 없는 `db_table` 고정이 실패로 잡힘.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- GREEN 결과: `5 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `51 passed`

남은 리스크:

- 테이블명을 명시해야 한다면 먼저 Obsidian 승인 문서에 확정값을 추가해야 한다.

### 2026-06-02 Task 3 Public Record Default Follow-up

검토한 피드백:

- `api-spec/pilot-mvp-api.official.json`은 `ProfileSummary.public_record`에 `ai_story_matches`, `ai_story_wins`, `ai_story_losses` 필드가 있음을 확정하지만, 신규 profile의 기본값이 `0`이라는 계약은 없다.
- `backend/apps/profiles/models.py`와 `backend/tests/accounts/test_user_profile_contract.py`가 `default=0`을 새 계약처럼 고정하고 있었다.

판단:

- 전적 필드 존재는 문서 기반 계약이다.
- 전적 필드 기본값 `0`은 현재 승인 문서에 없는 값이므로 구현과 테스트에서 강제하지 않는다.

구현/수정한 파일:

- 수정: `backend/apps/profiles/models.py`
- 수정: `backend/tests/accounts/test_user_profile_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

변경 내용:

- `ai_story_matches`, `ai_story_wins`, `ai_story_losses`에서 `default=0`을 제거했다.
- 테스트는 public_record 필드 존재만 확인하고 `default=0`이 없는지 확인하도록 변경했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- RED 결과: `1 failed, 4 passed`; 문서에 없는 `default=0` 고정이 실패로 잡힘.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
- GREEN 결과: `5 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `51 passed`

남은 리스크:

- 신규 profile 전적 기본값을 `0`으로 고정해야 한다면 먼저 Obsidian 승인 문서에 "신규 profile 전적 기본값은 0" 같은 계약을 추가해야 한다.

### 2026-06-02 Task 4 Refresh token family와 Security Event

구현/수정한 파일:

- 생성: `backend/apps/accounts/tokens.py`
- 수정: `backend/apps/accounts/models.py`
- 생성: `backend/tests/accounts/test_refresh_token_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/03_Backend/02_인증과_토큰.md`
- `api-spec/pilot-mvp-api.official.json`

변경 내용:

- `RefreshToken` 모델 소스를 추가하고 승인 문서의 최소 저장 필드인 `user`, `jti`, `family_id`, `token_hash`, `status`, `issued_at`, `expires_at`, `rotated_at`, `revoked_at`, `reused_at`, `replaced_by_jti`를 반영했다.
- refresh token 원문 저장 필드는 만들지 않았다.
- `backend/apps/accounts/tokens.py`에 refresh token status, reuse status, `REFRESH_TOKEN_REUSED` error code, 문서 문구 그대로의 security event type catalog를 추가했다.
- refresh token `jti`, `family_id` UUIDv4 생성 helper를 추가했다.
- 서버 secret 기반 HMAC-SHA256 refresh token hash helper를 추가했다.
- `SecurityEvent` 모델 소스를 추가하고 현재 확정된 event type, created time만 반영했다. actor/user_id와 metadata schema는 문서 확정 전 구현하지 않는다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
- RED 결과: `5 failed`; `RefreshToken`, `SecurityEvent`, `backend.apps.accounts.tokens` 누락으로 실패.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
- GREEN 결과: `5 passed`
- accounts 실행 위치: `D:\dev\Project\pilot`
- accounts 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
- accounts 결과: `10 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `56 passed`
- Django 설치 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django'))"`
- Django 설치 확인 결과: `None`

건너뛴 검증:

- 현재 Python 환경에 Django가 설치되어 있지 않아 `manage.py check`, migration 생성/적용, DB runtime 검증은 수행하지 않았다.
- refresh API, HttpOnly cookie 설정/삭제, 실제 family revoke, DB transaction + row lock은 Task 5 이후 service/API 구현 범위라 아직 검증하지 않았다.

남은 리스크:

- `RefreshToken`/`SecurityEvent`는 현재 승인 계약에 맞춘 정적 소스 구조와 순수 helper 검증까지만 완료됐다. Django dependency 설치 후 runtime model check와 migration 검증이 필요하다.
- security event의 비인증 상황(CSRF 실패, 로그인 실패 반복)에서 user 연결을 어떻게 처리할지는 승인 문서에 구체화되어 있지 않다. 실제 event 저장 service 구현 전에 확인이 필요하다.

### 2026-06-02 Task 4A Refresh token/Security Event Review Checkpoint

검토한 피드백:

- `new_refresh_token_identifiers()`가 `jti`와 `family_id`를 항상 함께 새로 만들어 refresh rotation에서 새 `family_id`를 생성하도록 오용될 수 있었다.
- `SecurityEvent.user_id`는 CSRF 실패/로그인 실패 반복처럼 인증 user가 없을 수 있는 이벤트에 대해 sentinel 하드코딩을 유도할 수 있었다.
- `SecurityEvent.metadata`는 JSONField인데 구체 schema가 없어 `schema_version`과 Python `jsonschema` 검증 계약을 완전히 만족할 수 없었다.
- `RefreshToken.user`, `SecurityEvent.user`의 `on_delete=models.CASCADE`는 승인 문서에서 확정한 삭제 생명주기 정책이 아니었다.

판단:

- `family_id`와 `jti`의 생성 시점은 문서에서 다르게 확정되어 있으므로 helper를 분리해야 한다.
- Security Event actor/user_id nullable 여부와 비인증 이벤트 actor 저장 방식은 승인 문서에 없다.
- SecurityEvent metadata schema가 없으므로 metadata JSONField와 jsonschema 검증 helper를 문서 없이 구현하지 않는다.
- 삭제 생명주기 정책은 승인 문서에 없으므로 `CASCADE`, `PROTECT`, `SET_NULL` 중 하나를 임의로 고정하지 않는다.

구현/수정한 파일:

- 수정: `backend/apps/accounts/tokens.py`
- 수정: `backend/apps/accounts/models.py`
- 수정: `backend/tests/accounts/test_refresh_token_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

변경 내용:

- `new_refresh_token_identifiers()`를 제거하고 `new_refresh_token_jti()`, `new_refresh_token_family_id()`, `new_login_refresh_token_identifiers()`로 분리했다.
- `new_refresh_token_identifiers()`를 제거하고 `new_refresh_token_jti()`, `new_refresh_token_family_id()`, `new_login_refresh_token_identifiers()`로 분리했다.
- `RefreshToken`은 문서에 명시된 token 소유자 `user_id` 저장 필드를 유지하되, FK `on_delete` 정책은 고정하지 않는다.
- `SecurityEvent`에서는 문서 미확정인 `user_id`, actor field, metadata JSONField를 제거했다.
- `validate_security_event_metadata()` helper를 제거했다. metadata schema와 jsonschema 검증은 승인 문서에 schema가 생긴 뒤 구현한다.
- 테스트는 helper lifecycle 분리, SecurityEvent actor/metadata 미구현, `models.ForeignKey`/`on_delete=models.CASCADE` 부재를 검증하도록 변경했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
- RED 결과: `1 failed, 4 passed`; SecurityEvent metadata JSONField와 문서 미확정 필드가 실패로 잡힘.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
- GREEN 결과: `5 passed`
- accounts 실행 위치: `D:\dev\Project\pilot`
- accounts 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
- accounts 결과: `10 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `56 passed`

남은 리스크:

- SecurityEvent actor/user_id nullable 여부, 비인증 event actor 표현 방식, metadata schema가 필요하면 먼저 승인 문서에 확정해야 한다.
- Django dependency가 현재 Python 환경에 설치되어 있지 않아 runtime model check와 migration 검증은 아직 수행하지 않았다.

### 2026-06-03 Task 5 Auth API와 CSRF 흐름 스캐폴딩

구현/수정한 파일:

- 생성: `backend/apps/accounts/serializers.py`
- 생성: `backend/apps/accounts/views.py`
- 생성: `backend/apps/accounts/urls.py`
- 생성: `backend/tests/accounts/test_auth_api_contract.py`
- 수정: `backend/config/urls.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `api-spec/pilot-mvp-api.official.json`
- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/09_Approved_Contracts/10_Auth_토큰_전달_기준.md`
- `docs/09_Approved_Contracts/11_CSRF_정책_기준.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`

변경 내용:

- official schema 기준 Auth endpoint 6개를 `accounts/urls.py`와 `backend/config/urls.py`에 연결했다.
- signup/login/empty request와 csrf/signup/login/logout/refresh/me response serializer 스캐폴딩을 추가했다.
- response serializer에는 access token 또는 refresh token 필드를 두지 않았다.
- view 스캐폴딩에서 `csrf_exempt`, Authorization Bearer, localStorage/sessionStorage 전제 코드를 사용하지 않는다.
- CSRF endpoint에는 `ensure_csrf_cookie`, `get_token(request)`를 명시했다.
- login view에는 CSRF rotation 지점을 `rotate_token(request)`로 명시했다.
- access/refresh cookie helper는 승인된 cookie name/path/TTL/HttpOnly/Secure/SameSite 설정을 사용한다.
- 실제 signup/login/logout/refresh/me DB/JWT/service 로직은 아직 구현하지 않고 `AuthServiceNotImplemented`로 명시했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
- RED 결과: `5 failed, 1 passed`; `accounts/serializers.py`, `accounts/views.py`, `accounts/urls.py` 누락으로 실패.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
- GREEN 결과: `6 passed`
- accounts 실행 위치: `D:\dev\Project\pilot`
- accounts 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
- accounts 결과: `16 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `62 passed`
- Django 설치 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django'))"`
- Django 설치 확인 결과: `None`

건너뛴 검증:

- 현재 Python 환경에 Django가 설치되어 있지 않아 URL resolver, DRF view import, `manage.py check`, cookie response runtime 검증은 수행하지 않았다.
- DB/JWT 발급, password 검증, refresh token rotation, family revoke, request-id envelope 연결은 service/API runtime 구현 범위로 남겼다.

남은 리스크:

- 현재 Auth API는 runtime 동작 구현이 아니라 official schema와 보안 금지선을 고정하는 스캐폴딩이다.
- SecurityEvent actor/user_id와 metadata schema가 미확정이므로 refresh token reuse 감지 시 security event 저장 service는 아직 구현하지 않는다.

### 2026-06-03 Task 5 Auth API schema 재정렬

구현/수정한 파일:

- 수정: `backend/apps/accounts/serializers.py`
- 수정: `backend/tests/accounts/test_auth_api_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `api-spec/pilot-mvp-api.official.json`
- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`

변경 내용:

- `POST /api/v1/auth/login` official schema의 `data.session.authenticated`, `data.session.access_expires_in_seconds` 중첩 구조에 맞춰 `LoginSessionSerializer`를 추가했다.
- `LoginResponseSerializer`의 top-level `authenticated`, `access_expires_in_seconds` 필드를 제거하고 `session = LoginSessionSerializer()`로 고정했다.
- 기존 Auth API 계약 테스트가 필드 문자열 존재만 확인해 중첩 구조 불일치를 잡지 못하던 부분을 보강했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py::test_login_response_serializer_keeps_session_fields_nested_like_official_schema -v`
- RED 결과: `1 failed`; `LoginSessionSerializer` 누락을 assertion failure로 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py::test_login_response_serializer_keeps_session_fields_nested_like_official_schema -v`
- GREEN 결과: `1 passed`
- Auth API 계약 명령: `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
- Auth API 계약 결과: `7 passed`

남은 리스크:

- access/refresh cookie name인 `pilot_access`, `pilot_refresh`는 문서에서 확정값을 확인하지 못했다. 임의 변경하지 않고, 필요하면 Obsidian 승인 문서에 cookie name을 추가하거나 env/config 계약을 먼저 확정해야 한다.
- `CORS_ALLOWED_ORIGINS` 설정은 존재하지만 `django-cors-headers` dependency와 `CorsMiddleware`는 아직 없다. 현재 단계에서는 CORS 구현 완료로 보지 않는다.

### 2026-06-03 Task 6 Match/Participant/Turn 저장 구조

구현/수정한 파일:

- 생성: `backend/apps/matches/constants.py`
- 생성: `backend/apps/matches/models.py`
- 생성: `backend/apps/matches/services.py`
- 생성: `backend/tests/matches/test_match_storage_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `api-spec/pilot-mvp-api.official.json`
- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/03_Backend/03_매치와_턴_저장.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`

변경 내용:

- `matches`, `match_participants`, `turns`, `action_submissions`, `turn_results` 모델 골격을 추가했다.
- 문서에 테이블명이 명시된 Task 6 범위에서는 각 모델 `Meta.db_table`을 문서의 테이블명으로 고정했다.
- 삭제 정책이 승인 문서에 확정되지 않았으므로 `models.ForeignKey`와 `on_delete` 정책을 만들지 않고 문서에 적힌 `*_id` 저장 필드로만 구성했다.
- official schema의 `match_mode`, `match_status`, `turn_status`, `participant_type` 값은 `matches/constants.py`로 분리했다.
- `action_code`는 기존 `game_rules.matchups.ACTION_CODES`를 재사용해 행동 코드 중복 정의를 피했다.
- `client_nonce`는 participant + turn 범위 중복 방지 계약에 맞춰 `turn_id`, `participant_id`, `client_nonce` 복합 unique constraint로 고정했다.
- `TurnResult`의 결과/로그 snapshot은 JSONField로 두고, `schema_version` 필드를 별도 저장 필드로 추가했다.
- `services.py`에는 participant identity 검증과 JSON snapshot payload의 `schema_version` 검증 경계를 추가했다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`
- RED 결과: `5 failed`; `constants.py`, `models.py`, `services.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`
- GREEN 결과: `5 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `68 passed`
- dependency 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
- dependency 확인 결과: `None`, `None`

남은 리스크:

- 현재 Django dependency가 로컬 Python 환경에 설치되어 있지 않아 `manage.py check`, migration 생성/검증, DB constraint runtime 검증은 아직 수행하지 못한다.
- `models.ForeignKey`를 쓰지 않은 것은 삭제 정책을 임의 결정하지 않기 위한 보수적 선택이다. 실제 FK와 `CASCADE`/`PROTECT`/`SET_NULL` 정책이 필요하면 승인 문서에 생명주기 정책을 먼저 확정해야 한다.
- `jsonschema` dependency도 현재 로컬 Python 환경에는 설치되어 있지 않다. `requirements.txt`에는 고정되어 있으므로 dependency 설치 후 `validate_json_snapshot_payload()` runtime 검증을 별도로 수행해야 한다.

### 2026-06-04 Task 7 Story 저장 구조

구현/수정한 파일:

- 생성: `backend/apps/story/models.py`
- 생성: `backend/apps/story/services.py`
- 생성: `backend/tests/story/test_story_storage_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/03_Backend/04_AI_스토리_진행.md`
- `docs/09_Approved_Contracts/03_진명_조각_획득_기준.md`
- `docs/09_Approved_Contracts/04_거짓_단서_생성_기준.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

변경 내용:

- `story_cases`, `apparitions`, `stages`, `true_name_fragments`, `false_clues`, `player_story_progress` 모델 골격을 추가했다.
- 문서에 명시된 주요 필드만 추가했고, `status`, `difficulty`, `attempts` 등의 기본값이나 enum은 문서 확정값이 없어 추가하지 않았다.
- 사건/괴이/스테이지 연결과 사용자 진행도는 JSONField에 숨기지 않고 `case_id`, `apparition_id`, `stage_id`, `user_id` 필드로 정규화했다.
- `base_policy_json`, `victory_condition_json`, `reveal_condition_json`, `trigger_condition_json`은 JSONField로 두었다.
- `services.py`에 Story 정책 payload의 `schema_version` 필수 검증 경계를 추가했다.
- `docs/05_Story_Mode/02_거울_속의_손님.md`가 `needs-decision` 상태이므로 공식 문장, 공식 단서 seed, trigger/reveal 실행 로직은 구현하지 않았다.
- LLM/RAG/embedding으로 진명 조각이나 거짓 단서를 생성하는 코드는 추가하지 않았다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`
- RED 결과: `4 failed`; `story/models.py`, `story/services.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`
- GREEN 결과: `4 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `72 passed`
- dependency 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
- dependency 확인 결과: `None`, `None`

남은 리스크:

- 현재 Django dependency가 로컬 Python 환경에 설치되어 있지 않아 `manage.py check`, migration 생성/검증, DB runtime 검증은 아직 수행하지 못한다.
- `jsonschema` dependency도 현재 로컬 Python 환경에는 설치되어 있지 않다. `requirements.txt`에는 고정되어 있으므로 dependency 설치 후 `validate_story_policy_payload()` runtime 검증을 별도로 수행해야 한다.
- `models.ForeignKey`와 삭제 정책은 승인 문서에 생명주기 정책이 없으므로 구현하지 않았다. 실제 FK와 `CASCADE`/`PROTECT`/`SET_NULL` 정책이 필요하면 문서 확정 후 변경해야 한다.
- Story 공식 콘텐츠 seed와 Story API 응답 구현은 오너 확인 전까지 진행하지 않는다.

### 2026-06-04 Obsidian 문서 Source of Truth 재점검

목적:

- 실제 Obsidian docs의 상태값과 승인 계층을 다시 확인해, 이후 구현에서 `draft`/`needs-decision` 내용을 임의 구현하지 않도록 고정한다.

확인한 문서:

- `docs/00_Project/00_문서_운영_규칙.md`
- `docs/09_Approved_Contracts/00_승인본_목차.md`
- `docs/03_Backend/99_Backend_구현_확정.md`
- `docs/02_Game_Rules/99_Game_Rules_구현_확정.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`
- `docs/05_Story_Mode/02_거울_속의_손님.md`
- `docs/05_Story_Mode/07_거울_속의_손님_오너_확정_워크시트.md`
- `docs/09_Approved_Contracts/02_첫_괴이_문장_LLM_사용_기준.md`
- `docs/09_Approved_Contracts/03_진명_조각_획득_기준.md`
- `docs/09_Approved_Contracts/04_거짓_단서_생성_기준.md`
- `docs/09_Approved_Contracts/09_RAG_도입_기준.md`
- `docs/03_Backend/07_RAG_검색_구조.md`

반영한 판단:

- `draft` 문서는 문서 운영 규칙상 단독 구현 기준으로 사용하지 않는다.
- `needs-decision` 문서는 구현 전 결정이 필요한 항목이 남아 있으므로 단독 구현 기준으로 사용하지 않는다.
- `implementation-ready` 문서와 `09_Approved_Contracts/*` 문서가 현재 가장 강한 구현 기준이다.
- `03_Backend/03_매치와_턴_저장.md`, `03_Backend/04_AI_스토리_진행.md`는 `draft`지만, 승인 계약 17/19/21이 특정 저장 구조와 원칙을 참조하므로 그 참조된 범위만 구현 기준으로 사용한다.
- `05_Story_Mode/02_거울_속의_손님.md`는 파일 status가 `needs-decision`이지만, `05_Story_Mode/07_거울_속의_손님_오너_확정_워크시트.md`와 승인 계약 02/03/04/12에서 확정된 항목은 구현 근거로 사용할 수 있다.
- LLM/RAG는 공식 룰, 승패, 인증/권한, 진명 조각, 거짓 단서, 괴이 행동 선택 권위를 바꾸지 않는다.
- API 구현은 `api-spec/pilot-mvp-api.official.jsonc`와 `api-spec/pilot-mvp-api.official.json`만 기준으로 하며, draft API path는 구현 기준으로 사용하지 않는다.

다음 구현 적용 원칙:

- 다음 Task 8부터는 `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`, `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`, `docs/09_Approved_Contracts/03_진명_조각_획득_기준.md`, `docs/09_Approved_Contracts/04_거짓_단서_생성_기준.md`, `docs/09_Approved_Contracts/12_거울_속의_손님_금기_정의.md`를 우선 대조한다.
- 문서에 없는 기본값, 테이블명, 삭제 정책, FK 정책, cookie name, status enum, seed 데이터는 임의로 만들지 않는다.
- 문서 간 충돌이 보이면 구현하지 않고 오너 확인으로 멈춘다.

### 2026-06-04 Task 8 Game Rules resolve service 연결

구현/수정한 파일:

- 생성: `backend/apps/matches/resolution.py`
- 생성: `backend/tests/matches/test_turn_resolution_contract.py`
- 수정: `backend/apps/matches/services.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

참조한 승인 문서/공식 schema:

- `docs/02_Game_Rules/04_상성_규칙.md`
- `docs/02_Game_Rules/05_승패_조건.md`
- `docs/02_Game_Rules/06_시간초과_규칙.md`
- `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `api-spec/pilot-mvp-api.official.jsonc`

변경 내용:

- `validate_submission_deadline()`을 추가해 `submitted_at > deadline_at`인 제출을 official `TURN_DEADLINE_EXPIRED` `ApiError` 객체로 반환하게 했다.
- 미제출 상태에서 서버 기준 `server_time > deadline_at`이면 플레이어 행동을 문서 확정 기본 행동 `silence`로 resolve한다.
- 시간초과 resolve는 `timeout_applied=True`, `turn_status="timed_out"`, participant 기준 `player_timeout_count + 1`로 반환한다.
- 일반 제출 resolve는 `turn_status="resolved"`로 반환하고 timeout count를 변경하지 않는다.
- 상성 계산과 공개 로그는 `backend/apps/game_rules.matchups.get_matchup_result()` 결과를 그대로 사용한다.
- 승패 계산은 `backend/apps/game_rules.outcomes.determine_ai_story_outcome()`을 사용해 봉인 성공이 동시 패배 조건보다 우선되게 했다.
- 봉인 성공 여부는 상성표 effect code의 `seal_success_if_condition_met`/`seal_failed`와 `seal_condition_met` 입력으로만 판단하며, 상성표 외부의 추가 방해 가산은 넣지 않았다.
- `matches.services`에서 resolution 순수 서비스를 노출하도록 연결했다.
- LLM/RAG/embedding, 공포 상태, Story trigger 실행, DB 저장, API serializer/display name 매핑은 구현하지 않았다.

검증:

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
- RED 결과: `5 failed`; `backend/apps/matches/resolution.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
- GREEN 결과: 최초 `1 failed, 4 passed`; `ApiError`가 예외 클래스가 아니라 official error payload 객체라는 기존 계약을 확인하고 테스트/구현을 반환형으로 정렬했다. 최종 재실행 결과 `5 passed`.
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `77 passed`
- dependency 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
- dependency 확인 결과: `None`, `None`

남은 리스크:

- 현재 Django dependency가 로컬 Python 환경에 설치되어 있지 않아 `manage.py check`, migration 생성/검증, DB 저장 흐름, 실제 API endpoint runtime 검증은 아직 수행하지 못한다.
- `resolve_ai_story_turn()`은 현재 상성표 effect code와 승패 우선순위 연결까지만 담당한다. effect code를 실제 `ResourceState` delta로 적용하는 엔진은 별도 승인 범위와 테스트가 필요하다.
- `ActionView.display_name` 매핑 값은 승인 문서에서 별도로 확정된 값을 찾지 못해 이번 순수 resolve 결과에는 넣지 않았다. API serializer 단계에서 공식 schema와 표시명 출처를 다시 확인해야 한다.
- `ApiError`는 예외가 아니라 응답 payload 객체다. API view/service 경계에서 반환형을 어떻게 HTTP 응답으로 변환할지는 이후 DRF 연결 단계에서 확정해야 한다.
- 시간 비교의 경계값인 `submitted_at == deadline_at`, `server_time == deadline_at`의 처리 문구는 문서에 명시적으로 분리되어 있지 않다. 이번 구현은 문서의 “이후/지났고” 표현에 맞춰 `>`인 경우만 deadline 초과로 처리한다.
