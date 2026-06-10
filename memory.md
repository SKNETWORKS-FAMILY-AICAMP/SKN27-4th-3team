# Project Memory

Updated: 2026-06-10

## LLM Provider Required Smoke Check Decision And Implementation 2026-06-10

- Decision: 사용자는 추천 기준인 별도 LLM provider smoke check를 승인했다.
- Approved contract: `docs/09_Approved_Contracts/33_LLM_Provider_Required_Smoke_Check_계약.md`.
- Management command: `python backend/manage.py llm_smoke_check`.
- Constraints:
  - Normal API runtime still follows fallback/disabled behavior from `docs/09_Approved_Contracts/25_LLM_Runtime_통합_계약.md`.
  - `/healthz` remains DB/process health only and is not expanded to LLM provider checks.
  - `LLM_REQUIRED=false` is the default and skips provider calls in smoke check.
  - `LLM_REQUIRED=true` makes missing API key, disabled mode, unsupported provider, missing model id, timeout, provider error, response parse error, empty response, and guardrail violation fail smoke verification.
  - Smoke check must not store `llm_generations` rows and must not output provider secret, raw prompt, raw response, Authorization header, cookie, or CSRF token.
- Implemented:
  - Added `LLM_REQUIRED` settings/env template value.
  - Added `run_required_provider_smoke_check()` in `backend.apps.llm.services`.
  - Added Django management command `llm_smoke_check`.

## RAG Manual Ingest/Search API Decision And Implementation 2026-06-10

- Decision: 사용자는 추천 기준인 staff-only 수동 RAG ingest/search API를 승인했다.
- Approved contract: `docs/09_Approved_Contracts/32_RAG_Manual_Ingest_Search_API_계약.md`.
- Endpoints:
  - `POST /api/v1/retrieval/ingest`
  - `POST /api/v1/retrieval/search`
- Constraints:
  - Both endpoints require access cookie auth, CSRF, and `accounts.User.is_staff=True`.
  - Server startup, import, migration, and health check must not run automatic ingest.
  - Ingest source paths must pass the existing RAG allowlist and stay under the project root.
  - Search results are only LLM context support or operations evidence; they cannot change rules, win/loss, auth/permission, official clues, true-name fragments, false clues, or apparition action selection.
  - `RAG_EMBEDDING_PROVIDER` defaults to `disabled`; `deterministic` is allowed only for local/test validation and is rejected in production.
  - External embedding provider calls remain excluded from this 1st implementation.
- Implemented:
  - Official API schema and strict ASCII JSON were extended with retrieval endpoints and RAG error codes.
  - Added `backend.apps.retrieval` serializers, views, URLs, staff authorization boundary, manual ingest service, deterministic embedding adapter, pgvector search service, and query log writes.
  - Local env template sets `RAG_EMBEDDING_PROVIDER=deterministic`; production env template sets `RAG_EMBEDDING_PROVIDER=disabled`.

## MVP Extension Phase 1 Scope Decision 2026-06-10

- Decision: 사용자는 추천 확정안 A를 승인했다.
- Approved contract: `docs/09_Approved_Contracts/30_MVP_확장_1차_범위_계약.md`.
- Phase 1 includes strict JSON artifact cleanup, password reset contract/implementation after API/schema contract, manual RAG ingest/search API, and optional LLM provider required validation mode.
- Phase 1 excludes RAG server-start auto ingest, production CI/CD, image registry push, automatic backups, monitoring/alerting, and actual production deployment proof until infrastructure/access and a separate operations contract are approved.
- Constraints:
  - Do not implement password reset runtime until request/confirm API schema, token TTL, one-time token policy, user enumeration prevention, rate limiting, raw token storage prohibition, SecurityEvent scope, CSRF, and local/dev email behavior are approved.
  - Do not run RAG ingest during server startup, import, migration, or health check.
  - Keep LLM fallback/disabled as default; only fail health/smoke checks when an explicit required mode is enabled.
  - Do not let RAG or LLM change rule resolution, win/loss, auth/permission, official clues, true-name fragments, false clues, or apparition action selection.

## Password Reset API Schema Decision 2026-06-10

- Decision: 사용자는 B안 이메일 어댑터 기반 password reset을 승인했다.
- Approved contract: `docs/09_Approved_Contracts/31_Password_Reset_API_Schema_계약.md`.
- Endpoints: `POST /api/v1/auth/password-reset/request`, `POST /api/v1/auth/password-reset/confirm`.
- Constraints:
  - Both endpoints are unauthenticated but CSRF-protected.
  - Request endpoint must not reveal account existence and returns `{ accepted: true }` on accepted requests.
  - Reset token TTL is 30 minutes, single-use, URL-safe random, and stored only as HMAC-SHA256 hash.
  - SecurityEvent metadata stores only `email_hmac` for reset-request email correlation; raw email must not be stored.
  - Raw reset token, token hash, password, provider credential, cookie, Authorization header, and CSRF token must not be stored in API responses, DB logs, or SecurityEvent metadata.
  - local/dev uses Django console email backend; production requires SMTP/provider configuration and must not expose reset tokens when delivery is unavailable.
  - New password follows the existing Auth password policy, and successful reset revokes existing refresh token families.

## Password Reset Backend Implementation 2026-06-10

- Implemented official API schema updates for `auth.password_reset.request` and `auth.password_reset.confirm`, including strict ASCII JSON regeneration.
- Implemented backend `accounts` runtime for password reset:
  - `PasswordResetToken` stores only user id, token hash, requested email, request IP, created/expiry/used timestamps.
  - `PasswordResetThrottle` applies email + observed IP request limiting.
  - reset token helper uses URL-safe random token and HMAC-SHA256 hash.
  - SecurityEvent metadata uses `email_hmac` for request correlation and does not store raw email/token/password.
  - request endpoint returns `{ accepted: true }` without exposing account existence.
  - delivery unavailable is checked before user lookup to avoid account enumeration.
  - confirm endpoint enforces invalid/expired/used token errors, changes password, marks token used, and revokes existing refresh token rows for the user.
  - local/dev email backend defaults to Django console email backend; production env template includes SMTP/provider variables.
- Added implementation plan: `docs/superpowers/plans/2026-06-10-password-reset-backend.md`.
- Fresh verification:
  - `.\.venv\Scripts\python.exe backend\manage.py check` -> no issues.
  - `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts --dry-run --check` -> no model changes; local PostgreSQL migration-history warning remains because the local `pilot` DB credentials fail.
  - `Get-Content -Raw api-spec\pilot-mvp-api.official.json | ConvertFrom-Json` -> ok.
  - `.\.venv\Scripts\python.exe -m pytest backend\tests -q` -> `238 passed`.

## Design Implementation Audit 2026-06-10

- 기준 문서는 `docs/09_Approved_Contracts/00_승인본_목차.md`와 승인 계약 01-29번이다. `docs/01_MVP/99_MVP_구현_확정_문서.md`는 여전히 `needs-decision`이므로 단독 구현 기준이 아니라 승인본을 우선한다.
- 현재 구현은 백엔드 핵심 MVP, 프론트 공식 API 연결, Redis/Channels/WebSocket 상태 동기화, AC-2A production 수동 배포 준비까지 반영되어 있다.
- 신선 검증 결과: `.\.venv\Scripts\python.exe -m pytest backend\tests -q`는 `222 passed`, 프론트 `npm run test:contracts`, `npm run test:api-client`, `npm run test:nameless-flow`, `npm run test:realtime-contract`, `npm run build`는 모두 통과했다.
- 주요 구현 완료 영역: Auth/CSRF/HttpOnly cookie/JWT refresh rotation, Match/Turn/ActionSubmission/TurnResult 저장, AI story server-side rule resolution, result 조회, LLM 보조 문구 runtime/log, AI Profile event/style metric 저장, RAG model/source-plan 준비, `mirror_guest`와 `nameless_curse` 사건 seed, React route/API client/prototype duel bridge, WebSocket read-only match event channel, local one-command dev start, production Compose/Caddy/Gunicorn ASGI 구성.
- 부분 구현 영역: RAG는 ingest/search API가 아니라 모델, chunking, source allowlist, source plan, query log 준비 상태다. LLM은 provider key가 없거나 실패하면 fallback/disabled payload로 동작하는 보조 runtime이며 판정 권위는 없다. Production은 수동 배포 준비 상태이고 CI/CD, registry push, backup, monitoring은 제외 범위다.
- 미구현 또는 제외 영역: PvP, Redis matchmaking, WebSocket action submit, KAG/GraphDB, password reset backend endpoint, production 배포 자동화, RAG 서버 시작 자동 ingest, 운영 backup/monitoring, LLM이 룰/승패/단서/괴이 행동을 결정하는 기능.
- 문서 품질 리스크: `api-spec/pilot-mvp-api.official.json`은 현재 PowerShell `ConvertFrom-Json` 기준 파싱에 실패했다. 테스트가 schema/endpoint 계약을 보완하고 있지만, strict JSON 산출물은 별도 정리가 필요하다.
- 워크트리 리스크: 현재 브랜치에는 README, docs, realtime, production, frontend prototype 관련 수정과 runtime screenshot/dev-start 신규 파일이 남아 있다. 감사 결과 보고 시 기존 변경을 되돌리지 않는다.

## AC-2A Production Deployment Decision 2026-06-08

- Options considered:
  - A: MVP runtime 완성, frontend official API 연결, Auth 보안, stale 문서 정리.
  - C local/dev: Docker build와 local/dev container 검증까지만 수행.
  - AC-2A: 단일 VM + Docker Compose + Gunicorn + reverse proxy + PostgreSQL production 배포까지 진행.
  - AC-2B: managed platform/container platform 배포.
  - AC-2C: Kubernetes/cloud native 배포.
- Decision: AC-2A.
- Constraints:
  - Production 배포는 단일 VM + Docker Compose + Gunicorn WSGI + Caddy reverse proxy + PostgreSQL `pgvector/pgvector:pg17` 기준으로 진행한다.
  - Caddy만 외부 포트 `80/443`에 노출하고, Django `8000`과 PostgreSQL `5432`는 Docker 내부 네트워크에서만 사용한다.
  - Production image tag는 VM 내부 local tag인 `skn27-api:${SKN27_IMAGE_TAG}`, `skn27-web:${SKN27_IMAGE_TAG}`를 사용하고, registry push는 이번 범위에서 제외한다.
  - Frontend는 Vite build 결과를 Caddy가 정적 서빙한다.
  - `runserver`는 local/dev 전용이며 production에서 사용하지 않는다.
  - Migration은 container startup에서 자동 실행하지 않고, 배포 절차에서 명시적으로 실행한다.
  - 실제 secret 값은 repository에 저장하지 않고, production env template만 repository에 둔다.
  - Trusted proxy는 Caddy allowlist 기준으로만 `X-Forwarded-*`를 신뢰한다. 기본 production compose는 Caddy 내부 IP `172.28.0.2`, `DJANGO_TRUSTED_PROXY_IPS=172.28.0.2`를 사용한다. local/dev는 기존 `REMOTE_ADDR` 기준을 유지한다.
  - Kubernetes, managed DB, image registry push, CI/CD 자동화, backup 자동화, monitoring platform, PvP, KAG, Redis, WebSocket, RAG 서버 시작 자동 ingest는 이번 구현 범위에서 제외한다.

## Status Check 2026-06-05

- `docs/superpowers/plans/2026-06-02-backend-implementation-order.md` 1665행 기준 진행 현황을 현재 코드와 대조했다.
- 현재 브랜치는 `feature-backend-structure`, 최신 커밋은 `012761a 기록한 내용`, working tree에는 backend match/story 구현 WIP 변경이 있다.
- Official API runtime 기준 endpoint는 13개이며, 실제 응답 구현은 10개다: `auth.csrf`, `auth.login`, `auth.refresh`, `auth.me`, `profile.me`, `story.cases.list`, `story.cases.briefing`, `story.cases.matches.start`, `matches.detail`, `matches.turns.submit`.
- 남은 stub endpoint는 3개다: `auth.signup`, `auth.logout`, `matches.result`.
- AI Story 플레이 흐름은 매치 시작, 매치 조회, 행동 제출, 턴 resolve 결과 저장까지 열려 있고, 결과 조회는 아직 남아 있다.
- 신선 검증 결과: `.\.venv\Scripts\python.exe -m pytest backend\tests -q`는 `146 passed`, `.\.venv\Scripts\python.exe backend\manage.py check`는 `System check identified no issues (0 silenced).` 실제 PostgreSQL migration 적용 검증은 연결 타임아웃으로 미완료다.

## LLM Approval Scope Decision 2026-06-05

- Options considered:
  - A: 결과 요약만 승인.
  - B: 결과 요약, 스타일 문장, 운영자용 매치 로그 요약 승인.
  - C: B안에 승인된 기준 문장의 짧은 변형 후보까지 포함.
- Decision: B안.
- Constraints:
  - LLM 승인 기준은 `결과 화면 요약`, `플레이 스타일 요약 문장`, `운영자용 매치 로그 요약`에만 적용한다.
  - LLM은 턴/전투 판정, 승패, 자원 계산, 진명 조각 획득, 거짓 단서 진위, 공식 설정 추가, 룰 변경에 관여하지 않는다.
  - 승인된 기준 문장의 짧은 변형 후보 생성은 이번 LLM 승인 기준 범위에 포함하지 않는다.
  - LLM 실패 시 정적 `story_result_text`와 서버 판정 결과만으로 화면이 완성되어야 한다.

## Turn Submit State Decision 2026-06-05

- Options considered:
  - A: `match_participants`에 resource scalar field를 확장하고, clue ownership table을 별도로 둔다.
  - B: `TurnResult.result_json` snapshot만으로 current state를 재구성한다.
  - C: 별도 current-state table과 clue ownership table을 둔다.
- Decision: A안.
- Constraints:
  - 핵심 자원 수치는 JSONField에 숨기지 않고 `match_participants` scalar field로 저장한다.
  - 진명 조각/거짓 단서 보유 상태는 match별 ownership table에 저장한다.
  - `true_name_fragments`, `false_clues`, `suspicion`, `shield`, `timeout_count`는 `MatchState` 재구성에 사용할 수 있어야 한다.
  - Story clue definition은 DB seed가 아니라 승인 상수로 시작한다.
  - `false_clue_detection_check`는 확률 없이 결정적으로 처리한다.
  - 중복/종료 충돌은 HTTP 409, 행동 불가/정보 대상/의식력/deadline 오류는 HTTP 400으로 처리한다.

## Branch Integration And Audit 2026-06-06

- `origin/feature-llm`의 최상위 `llm/` 산출물과 `ops/env/llm.env.example`을 현재 브랜치에 반영했다.
- `origin/feature-frontend-game-screen`의 `frontend/` 산출물을 현재 브랜치에 반영했다.
- React frontend는 현재 `frontend/public/prototype/game-background.html`을 iframe으로 띄우는 wrapper 구조다. 실제 Django API fetch는 아직 없다.
- Frontend prototype 내부 키는 일부 demo key를 유지하지만, API 제출 경계에서는 `buildTurnSubmitPayload()`로 official enum payload를 만든다.
  - `deceive` -> `trick`
  - `attic_diary` -> `mirror_back`
  - `truth_mirror` -> `mirror_surface`
  - `stitched_mouth` -> `missing_child_voice`
  - `bloodied_teddy` -> `forgotten_room`
  - `ian_reflection` -> `self_reflection`
- `frontend/scripts/verify-official-enums.mjs`와 `npm run test:contracts`를 추가해 official API payload boundary를 검증한다.
- LLM은 최상위 `llm/` 실험/프롬프트/평가/guardrail 영역으로만 반영했다. `backend/apps/llm/`, backend runtime LLM 연결, generation log 저장은 추가하지 않았다.
- 루트 `requirements.txt`에는 `groq`를 추가하지 않았다. backend dependency lock은 승인된 백엔드 의존성만 유지한다.
- 문서 대비 감사 리포트: `docs/superpowers/reports/2026-06-06-branch-integration-doc-audit.md`.
- 주요 감사 결론:
  - Monorepo 폴더 구조, 최상위 LLM 작업 영역, backend LLM/PvP/realtime 금지선은 대체로 문서 의도와 맞다.
  - Frontend는 prototype 단계이며 full API-connected React app은 아니다.
  - `turn_flavor_text` official API 응답 위치, `generation_id` 저장 방식, `matches.result` runtime 조립은 아직 미확정/미구현이다.
  - Frontend prototype 내부 문서와 demo fixture에는 official enum과 다른 demo key가 남아 있어 API 연결 시 혼동 위험이 있다.

## Current State

- 이 workspace는 `docs/` 옵시디언 문서, official API schema, 백엔드 MVP scaffold가 함께 있는 초기 monorepo다.
- Git 저장소이며 현재 작업 브랜치는 `feature-backend-structure`다.
- 구현 문서의 source of truth는 `docs/09_Approved_Contracts/*`, `docs/02_Game_Rules/*`, `docs/03_Backend/99_Backend_구현_확정.md`, `docs/06_AI_Profile/99_AI_Profile_구현_확정.md`, `api-spec/pilot-mvp-api.official.jsonc/json`이다.
- 프론트엔드와 LLM generation 구현은 현재 작업 범위에서 제외한다.
- `backend/apps/game_rules`는 전체 7x7 상성표, 자원/상태 일부, AI 스토리 승패 판정을 순수 Python 도메인 모듈로 구현했다.
- `backend/apps/ai_profile/metrics.py`는 승인된 행동 이벤트 필드와 스타일 지표 계산식을 순수 Python 도메인 모듈로 구현했다.
- Django project 최소 설정, 의존성 lock, 백엔드 MVP 앱 `AppConfig` 골격은 생성됐다.
- Auth user/profile/refresh token/security event 저장 구조 일부는 구현됐다.
- Auth API endpoint/serializer/view/cookie helper 스캐폴딩은 official schema와 보안 금지선 기준으로 추가됐다.
- Match/Story/Retrieval DB 모델 scaffold와 턴 resolve, RAG chunking/allowlist 구조가 추가됐다.
- 실제 Auth token 발급/JWT/cookie runtime/rotation service, full official endpoint runtime 연결, 실제 PostgreSQL migration 적용 검증은 아직 남아 있다.
- 로컬 실행용 `ops/docker/docker-compose.yml`, `ops/docker/backend.Dockerfile`, `ops/env/backend.env.example`가 추가되어 Django API + PostgreSQL + `pgvector` 구성까지 정적 검증됐다.
- Dockerfile 기반 백엔드 이미지 빌드와 Django 배포 의도는 문서에 반영됐다. 현재 Dockerfile은 로컬/dev 이미지 빌드 시작점이며 production entrypoint나 운영 배포 자동화로 확정하지 않는다.
- Dockerfile 이미지 빌드와 Django 배포 결정 타이밍은 `docs/09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약.md`에 정리됐다.
- PvP 모드는 없다. 기존 PvP-ready 구조 보존과 확정 후속 PvP 전제는 폐기됐고, 기준 문서는 `docs/09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약.md`의 PvP 미사용 계약이다.
- `meta.request_id` 정책은 A안으로 확정했다. 서버가 매 요청마다 `req_<uuid4_hex>`를 생성하고, 1차 MVP에서는 외부 `X-Request-ID`를 무시하며, 응답 header에는 `X-Request-ID`를 내려준다.
- 실제 service가 아직 구현되지 않은 공식 endpoint는 A안으로 확정했다. HTTP 501 + `SERVICE_NOT_IMPLEMENTED` 실패 envelope를 반환하고, mock success data는 만들지 않는다.
- Auth runtime 정책은 A안으로 확정했다. JWT는 `HS256`으로 `DJANGO_SECRET_KEY` 기반 Django `settings.SECRET_KEY`를 사용해 발급하고, access claim은 `token_type=access`, `sub`, `iat`, `exp`, refresh claim은 `token_type=refresh`, `sub`, `jti`, `family_id`, `iat`, `exp`만 사용한다.
- Refresh rotation은 `transaction.atomic()` + 제출 refresh token row `select_for_update()`로 처리한다. `active` token은 `rotated`로 전환하고 같은 `family_id`의 새 refresh token을 발급하며, `rotated`/`revoked`/`reused` token 제출은 reuse로 감지해 family 전체를 revoke한다. grace window는 없다.
- SecurityEvent actor/metadata 정책은 A안으로 확정했다. `user_id`는 nullable 값 필드, `request_id`는 nullable server request id, `metadata`는 기본 `{}` JSON object이며 raw token/token hash/password/cookie/CSRF token 원문은 저장하지 않는다. actor FK는 사용하지 않는다.
- README는 Obsidian 문서 기준으로 현재 사용 기술, 계약만 있는 기술, 후순위/미사용 기술을 분리한다.
- ERD에 들어갈 RDB 테이블 구성은 문서와 Django model scaffold 수준에서 존재하지만, 별도 시각적 ERD 산출물은 아직 없다.

## Operating Context

- 승인된 목표 구조는 `backend/`, `frontend/`, `llm/`, `api-spec/`, `docs/`, `tools/`, `output/`, `ops/`를 포함하는 monorepo다.
- 백엔드 목표 스택은 Django API, PostgreSQL, `pgvector`, HttpOnly JWT cookie, refresh token rotation, Django CSRF middleware다.
- 1차 MVP 로컬 실행 구성은 Django API + PostgreSQL + PostgreSQL `pgvector`로 제한한다.
- 현재 로컬 Docker 구성도 Django API + PostgreSQL `pgvector`만 포함한다.
- Dockerfile 기반 image build 검증은 후속 작업에서 `docker build -f ops/docker/backend.Dockerfile -t skn27-backend:local .` 또는 `docker compose -f ops/docker/docker-compose.yml build api`로 수행할 후보 상태다.
- Redis, WebSocket worker, PvP 모드, LLM provider emulator, KAG 전용 저장소, 프론트엔드 구현, LLM provider/prompt/generation 구현은 제외한다.
- GraphDB는 사용하지 않는다. KAG도 1차 MVP 제외이며, 후속 후보는 RDB 기반 구조다.

## Source Documents

- `docs/03_Backend/99_Backend_구현_확정.md`: backend 구현은 `implementation-ready`.
- `docs/02_Game_Rules/99_Game_Rules_구현_확정.md`: game rules 구현은 `implementation-ready`.
- `docs/06_AI_Profile/99_AI_Profile_구현_확정.md`: AI Profile 구현 기준은 `approved`.
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`: 프론트/LLM 제외 백엔드, RAG, AI Profile 구현 준비 기준.
- `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`: 7x7 상성표, 상태, 봉인, 동시 승패 우선순위.
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`: HttpOnly cookie JWT, refresh token family/reuse, CSRF 보안 기준.
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`: 서버 `deadline_at` 기준 시간초과.
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`: official API schema 기준.
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`: 팀별 폴더 경계.
- `docs/09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약.md`: Dockerfile 이미지 빌드와 Django 배포 준비의 결정 타이밍과 구현 게이트.
- `docs/09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약.md`: PvP 미사용 결정, PvP-ready 전제 폐기, realtime/Redis/WebSocket 도입 금지 기준.

## Implemented Structure

- `backend/apps/game_rules/resources.py`
  - `ResourceState`, 자원 기본값/상한, 의심/거짓 단서/보호막/불완전 진명 조각 처리.
- `backend/apps/game_rules/matchups.py`
  - 승인된 7x7 행동 상성표, 방향별 공개 로그, 봉인 방해 단계, `간파` vs `침묵` 다음 행동 후보 생성.
- `backend/apps/game_rules/outcomes.py`
  - 12턴 AI 스토리 제한과 봉인 성공 우선 승패 판정.
- `backend/apps/game_rules/policies.py`
  - `거울 속의 손님` 기본 가중치와 tie-break 순서.
- `backend/apps/ai_profile/metrics.py`
  - `ActionEvent`, `StyleMetrics`, 승인 산식 기반 스타일 지표 계산.
- `requirements.txt`
  - 공식 출처 기준 backend dependency lock: `Django==5.2.14`, `djangorestframework==3.17.1`, `PyJWT==2.13.0`, `jsonschema==4.26.0`, `pgvector==0.4.2`, `psycopg[binary]==3.3.4`.
- `backend/config/settings.py`
  - API prefix `/api/v1`, `AUTH_USER_MODEL = "accounts.User"`, CSRF middleware, explicit CSRF/CORS allowlist, HttpOnly cookie path/TTL/SameSite 계약값.
  - `RAG_EMBEDDING_MODEL_ID`는 코드 기본값 없이 env에서만 읽는다. 추천값 `text-embedding-3-small`은 코드가 아니라 env template 또는 운영 설정에서 주입해야 한다.
  - `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_CORS_ALLOWED_ORIGINS`에 wildcard가 포함되면 settings load 단계에서 실패한다.
- `backend/config/urls.py`, `backend/config/asgi.py`, `backend/config/wsgi.py`, `backend/manage.py`
  - Django project entrypoint 골격. `backend/manage.py`는 `backend.config.settings` import를 위해 project root를 `sys.path`에 추가한다. `backend/config/urls.py`는 `api/v1/auth/`를 accounts URLConf에 연결한다.
- `backend/apps/*/apps.py`
  - `accounts`, `profiles`, `game_rules`, `matches`, `story`, `ai_profile`, `retrieval` 최소 Django app config.
- `backend/apps/common/errors.py`
  - official API schema의 `error_codes` catalog, immutable `API_ERROR_MESSAGES`, `ApiError`, `make_api_error`.
  - `ApiError` 직접 생성 시에도 `message`가 `API_ERROR_MESSAGES[code]`와 같아야 하므로 official message 계약을 우회할 수 없다.
- `backend/apps/common/responses.py`
  - 성공 `{ data, meta }`, 실패 `{ error, meta }` envelope 생성 helper. `meta.request_id`, `meta.server_time` 필수.
- `backend/apps/accounts/models.py`
  - `AbstractBaseUser + PermissionsMixin` 기반 `accounts.User` custom user model. 로그인 식별자는 email. nickname/전적/스타일 표시 필드는 없다. 승인 문서에 테이블명이 없으므로 `db_table`은 지정하지 않는다.
  - `RefreshToken`은 승인 문서의 최소 저장 필드인 `user_id`, `jti`, `family_id`, `token_hash`, `status`, `issued_at`, `expires_at`, `rotated_at`, `revoked_at`, `reused_at`, `replaced_by_jti`를 가진다. 원문 refresh token 필드는 없다.
  - `SecurityEvent`는 A안 Auth runtime 정책에 따라 event type, nullable `user_id`, nullable `request_id`, `metadata`, created time을 가진다. actor FK와 raw secret성 metadata는 사용하지 않는다.
- `backend/apps/accounts/tokens.py`
  - refresh token status/reuse status, `REFRESH_TOKEN_REUSED`, 문서 문구 기반 security event type catalog, `jti`/`family_id` lifecycle별 UUIDv4 생성 helper, 서버 secret 기반 HMAC-SHA256 hash helper.
  - A안 Auth runtime 기준 JWT 발급 helper는 access/refresh token claim allowlist와 `HS256` signing policy를 따른다.
- `backend/apps/accounts/serializers.py`
  - official schema 기준 Auth request/response serializer 스캐폴딩. access/refresh token을 response body field로 두지 않는다.
- `backend/apps/accounts/views.py`
  - Auth endpoint view 스캐폴딩, CSRF success envelope, CSRF cookie/get token/rotation 지점, access/refresh cookie set/delete helper. 실제 DB/JWT/service 로직은 `AuthServiceNotImplemented`로 명시한다.
- `backend/apps/accounts/urls.py`
  - official schema 기준 Auth endpoint 6개: `csrf`, `signup`, `login`, `logout`, `refresh`, `me`.
- `backend/apps/accounts/managers.py`
  - email 정규화, password hashing, superuser 권한 플래그 검증을 담당하는 `UserManager`.
- `backend/apps/profiles/models.py`
  - `profiles.Profile`은 `settings.AUTH_USER_MODEL`과 1:1 연결되며 nickname, AI story 전적 요약, style label/display text/update time을 담당한다. 승인 문서에 테이블명과 신규 전적 기본값이 없으므로 `db_table`과 `default=0`은 지정하지 않는다.
- `ops/docker/docker-compose.yml`
  - 로컬 MVP 실행 서비스를 Django API와 PostgreSQL `pgvector`로 제한한다. Redis, WebSocket/Channels, LLM provider emulator, KAG store, GraphDB/Neo4j는 포함하지 않는다.
- `ops/docker/backend.Dockerfile`
  - `python:3.14-slim` 기반으로 `requirements.txt`를 설치하고 `backend/manage.py runserver 0.0.0.0:8000`을 실행한다.
- `ops/env/backend.env.example`
  - 로컬 개발용 Django/PostgreSQL/RAG embedding 설정 예시다. 실제 secret은 포함하지 않고, 추천 embedding model id `text-embedding-3-small`은 코드가 아니라 env 값으로 주입한다.

## Verification

- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 29 passed.
- AI Profile TDD RED
  - `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_style_metrics_contract.py -v`
  - Result before implementation: `ModuleNotFoundError: No module named 'backend.apps.ai_profile.metrics'`.
- AI Profile GREEN
  - same command
  - Result after implementation: 5 passed.
- Game Rules review RED
  - `C:\Python314\python.exe -m pytest backend\tests\game_rules\test_matchup_contract.py -v`
  - Result before fix: 4 failed, 7 passed. Failures covered `저주`/`간파` vs `봉인` directional logs and timeout strong-pattern priority.
- Game Rules review GREEN
  - same command
  - Result after fix: 11 passed.
- Game Rules policy immutability GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\game_rules\test_matchup_contract.py -v`
  - Result after constants/immutability hardening: 12 passed.
- Django config Task 1 RED
  - `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
  - Result before implementation: 6 failed. Missing `requirements.txt`, `backend/manage.py`, `backend/config`, and MVP app `apps.py` files.
- Django config Task 1 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
  - Result after implementation: 7 passed.
- Django config Task 1 manage.py path RED
  - `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
  - Result before fix: 1 failed, 6 passed. `backend/manage.py` did not add project root to `sys.path`.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 36 passed.
- Django config review follow-up RED
  - `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
  - Result before fix: 2 failed, 7 passed. Failures covered hardcoded `text-embedding-3-small` in settings and wildcard CSRF/CORS origin env acceptance.
- Django config review follow-up GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py -v`
  - Result after fix: 9 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 38 passed.
- API envelope Task 2 RED
  - `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
  - Result before implementation: 7 failed. Missing `backend.apps.common.errors` and `backend.apps.common.responses`.
- API envelope Task 2 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
  - Result after implementation: 7 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 45 passed.
- API envelope Task 2 review RED
  - `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
  - Result before fix: 1 failed, 7 passed. `ApiError` direct construction could override official message.
- API envelope Task 2 review GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\common\test_response_contract.py -v`
  - Result after fix: 8 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 46 passed.
- Accounts/Profile Task 3 RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result before implementation: 4 failed, 1 passed. Missing `accounts/models.py`, `accounts/managers.py`, `profiles/models.py`.
- Accounts/Profile Task 3 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result after implementation: 5 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 51 passed.
- Refresh token/Security Event Task 4 RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
  - Result before implementation: 5 failed. Missing `RefreshToken`, `SecurityEvent`, and `backend.apps.accounts.tokens`.
- Refresh token/Security Event Task 4 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
  - Result after implementation: 5 passed.
- Accounts contract after Task 4
  - `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
  - Result: 10 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 56 passed.
- Django install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django'))"`
  - Result: `None`.
- Refresh token/Security Event Task 4A review RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
  - Result before fix: 1 failed, 4 passed. Tests caught document-unapproved SecurityEvent actor/metadata fields.
- Refresh token/Security Event Task 4A review GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_refresh_token_contract.py -v`
  - Result after fix: 5 passed.
- Accounts contract after Task 4A
  - `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
  - Result: 10 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 56 passed.
- Accounts/Profile Task 3 public-record default RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result before fix: 1 failed, 4 passed. Tests caught document-unapproved `default=0` values for profile public record counters.
- Accounts/Profile Task 3 public-record default GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result after fix: 5 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 51 passed.
- Accounts/Profile Task 3 table-name review RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result before fix: 2 failed, 3 passed. Tests caught document-unapproved `db_table` values.
- Accounts/Profile Task 3 table-name review GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_user_profile_contract.py -v`
  - Result after fix: 5 passed.
- 2026-06-02, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 51 passed.
- Auth API/CSRF Task 5 RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
  - Result before implementation: 5 failed, 1 passed. Missing `accounts/serializers.py`, `accounts/views.py`, `accounts/urls.py`.
- Auth API/CSRF Task 5 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
  - Result after implementation: 6 passed.
- Accounts contract after Task 5
  - `C:\Python314\python.exe -m pytest backend\tests\accounts -v`
  - Result: 16 passed.
- 2026-06-03, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 62 passed.
- Django install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django'))"`
  - Result: `None`.
- Auth API schema realignment RED
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py::test_login_response_serializer_keeps_session_fields_nested_like_official_schema -v`
  - Result before fix: 1 failed. The test caught the missing nested `LoginSessionSerializer`.
- Auth API schema realignment GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py::test_login_response_serializer_keeps_session_fields_nested_like_official_schema -v`
  - Result after fix: 1 passed.
- Auth API contract after schema realignment
  - `C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_api_contract.py -v`
  - Result: 7 passed.
- Match storage Task 6 RED
  - `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`
  - Result before implementation: 5 failed. Missing `matches/constants.py`, `matches/models.py`, `matches/services.py`.
- Match storage Task 6 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_storage_contract.py -v`
  - Result after implementation: 5 passed.
- 2026-06-03, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 68 passed.
- Django/jsonschema install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
  - Result: `None`, `None`.
- Dependency install
  - Created local virtualenv: `.venv`.
  - Installed runtime requirements with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
  - Installed test runner in `.venv`: `pytest==9.0.3`.
  - Import check with `.venv`: Django `5.2.14`, jsonschema `4.26.0`, DRF `3.17.1`.
- Django runtime check
  - `.\.venv\Scripts\python.exe backend\manage.py check`
  - Result: `System check identified no issues (0 silenced).`
- Implementation report file
  - Created: `docs/superpowers/reports/2026-06-04-backend-implementation-report.md`.
  - Purpose: record source-of-truth checks, changed files, verification, skipped runtime checks, and remaining risks for each backend implementation task.
- AI Profile persistence Task 9 RED
  - `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_ai_profile_persistence_contract.py -v`
  - Result before implementation: 5 failed. Missing `backend/apps/ai_profile/models.py` and `backend/apps/ai_profile/services.py`.
- AI Profile persistence Task 9 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_ai_profile_persistence_contract.py -v`
  - Result after implementation: 5 passed.
- AI Profile test scope
  - `C:\Python314\python.exe -m pytest backend\tests\ai_profile -v`
  - Result: 10 passed.
- 2026-06-04, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 82 passed.
- Django/jsonschema install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
  - Result: `None`, `None`.
- Retrieval Task 10 RED
  - `.\.venv\Scripts\python.exe -m pytest backend\tests\retrieval\test_retrieval_contract.py -v`
  - Result before implementation: 5 failed, 1 passed. Missing `backend/apps/retrieval/models.py`, `chunking.py`, `services.py`.
- Retrieval Task 10 GREEN
  - `.\.venv\Scripts\python.exe -m pytest backend\tests\retrieval\test_retrieval_contract.py -v`
  - Result after implementation: 6 passed.
- 2026-06-04, `D:\dev\Project\pilot`
  - `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
  - Result: 88 passed.
- Django runtime check
  - `.\.venv\Scripts\python.exe backend\manage.py check`
  - Result: `System check identified no issues (0 silenced).`
- Story storage Task 7 RED
  - `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`
  - Result before implementation: 4 failed. Missing `story/models.py` and `story/services.py`.
- Story storage Task 7 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\story\test_story_storage_contract.py -v`
  - Result after implementation: 4 passed.
- 2026-06-04, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 72 passed.
- Django/jsonschema install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
  - Result: `None`, `None`.
- Obsidian docs source-of-truth audit
  - Checked: `docs/00_Project/00_문서_운영_규칙.md`, `docs/09_Approved_Contracts/00_승인본_목차.md`, `docs/03_Backend/99_Backend_구현_확정.md`, `docs/02_Game_Rules/99_Game_Rules_구현_확정.md`, approved contracts 02/03/04/09/12/17/18/20/22/23, and Story Mode docs.
  - Result: implementation must prioritize `09_Approved_Contracts/*` and `99_*_구현_확정` documents; `draft` and `needs-decision` documents are not standalone implementation authority.
- Turn resolution Task 8 RED
  - `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
  - Result before implementation: 5 failed. Missing `backend/apps/matches/resolution.py`.
- Turn resolution Task 8 GREEN
  - `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
  - Result after implementation: 5 passed.
- 2026-06-04, `D:\dev\Project\pilot`
  - `C:\Python314\python.exe -m pytest backend\tests -v`
  - Result: 77 passed.
- Django/jsonschema install check
  - `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
  - Result: `None`, `None`.
- Local Docker/env Task 12B RED
  - `.\.venv\Scripts\python.exe -m pytest backend\tests\ops\test_local_runtime_contract.py -v`
  - Result before implementation: 3 failed. Missing `ops/docker/docker-compose.yml`, `ops/docker/backend.Dockerfile`, `ops/env/backend.env.example`.
- Local Docker/env Task 12B GREEN
  - `.\.venv\Scripts\python.exe -m pytest backend\tests\ops\test_local_runtime_contract.py -v`
  - Result after implementation and test alignment: 3 passed.
- 2026-06-04, `D:\dev\Project\SKN27-4th-3team`
  - `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
  - Result: 95 passed.
- Django runtime check
  - `.\.venv\Scripts\python.exe backend\manage.py check`
  - Result: `System check identified no issues (0 silenced).`
- Migration dry-run check
  - `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval --dry-run --check`
  - Result: no model changes detected; local `pilot` PostgreSQL authentication warning remains.
- Auth runtime A안 RED
  - `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_auth_runtime_contract.py backend\tests\accounts\test_refresh_token_contract.py backend\tests\accounts\test_auth_api_contract.py backend\tests\api\test_api_runtime_envelope_contract.py -v`
  - Result before implementation: 5 failed, 14 passed. Missing JWT helper, `accounts/services.py`, A안 `SecurityEvent` fields, and Auth view service delegation.
- Auth runtime A안 GREEN
  - same command
  - Result after implementation: 19 passed.
- 2026-06-04, `D:\dev\Project\SKN27-4th-3team`
  - `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
  - Result: 107 passed.
- Django runtime check after Auth runtime A안
  - `.\.venv\Scripts\python.exe backend\manage.py check`
  - Result: `System check identified no issues (0 silenced).`
- Accounts migration dry-run check after Auth runtime A안
  - `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts --dry-run --check`
  - Result: `No changes detected in app 'accounts'`; local `pilot` PostgreSQL authentication warning remains.
- Official API schema parse check after Auth runtime A안
  - `.\.venv\Scripts\python.exe -c "import json; json.load(open(r'api-spec\pilot-mvp-api.official.json', encoding='utf-8')); print('api-spec/pilot-mvp-api.official.json valid')"`
  - Result: valid.
  - `.\.venv\Scripts\python.exe -c "import json; json.load(open(r'api-spec\pilot-mvp-api.official.jsonc', encoding='utf-8')); print('api-spec/pilot-mvp-api.official.jsonc valid JSON')"`
  - Result: valid JSON.

## Known Gaps And Risks

- Obsidian document hierarchy is now treated as follows: `09_Approved_Contracts/*` and `99_*_구현_확정`/`implementation-ready` documents are implementation authority; `draft` documents are only usable when an approved contract explicitly references a bounded part; `needs-decision` content must not be implemented without owner confirmation.
- `docs/05_Story_Mode/02_거울_속의_손님.md` has `needs-decision` status, but some content is backed by approved contracts and the approved owner worksheet. Use approved contracts 02/03/04/12 and `docs/05_Story_Mode/07_거울_속의_손님_오너_확정_워크시트.md` for specific story rules, not the needs-decision document as a standalone source.
- API implementation authority is `api-spec/pilot-mvp-api.official.jsonc` and `api-spec/pilot-mvp-api.official.json`; draft API paths must not be implemented.
- RAG/LLM must not change rule resolution, win/loss, auth/permission policy, true-name fragments, false clues, or apparition action selection.
- Django dependency file은 생성됐지만, 현재 로컬 Python 환경에 설치 검증은 하지 않았다.
- `.venv`에 backend requirements와 pytest를 설치했고, `manage.py check`, migration check, 전체 테스트를 통과했다. 실제 PostgreSQL 연결과 migration 적용 검증은 아직 남아 있다.
- 추천 RAG embedding model id는 코드에서 제거했고, 로컬 env template `ops/env/backend.env.example`에 명시했다.
- 로컬 Docker Compose 구성은 정적 계약 테스트로 검증했지만, `docker compose up`과 컨테이너 내부 DB migration apply는 아직 실행하지 않았다.
- Docker image build와 Django production 배포는 아직 검증하지 않았다. production 배포 전 결정 타이밍과 구현 게이트는 승인 계약 24번을 따른다.
- PvP 관련 기존 문서 표현은 핵심 source-of-truth에서 정리했고, `backend/apps/realtime/` placeholder도 제거했다. 발표용/generated 문서에 남은 PvP 표현은 폐기 기록으로만 취급하며, 구현 기준은 승인 계약 19번의 PvP 미사용 결정이다.
- 실제 CORS 응답 처리는 아직 dependency/middleware가 없으므로, 프론트 origin 요구가 확정되는 API 연결 단계에서 다시 검증해야 한다.
- request id 생성/전파는 `backend.apps.common.request_ids.RequestIdMiddleware`로 settings에 연결했다. API envelope helper는 `backend.apps.common.runtime`을 통해 DRF `Response`와 `SERVICE_NOT_IMPLEMENTED` exception handler에 연결했다.
- Auth API view는 official schema와 보안 금지선을 따른다. `login`, `refresh`, `me`는 A안 JWT/cookie runtime service로 연결했고, `signup`, `logout`은 아직 501 envelope로 유지한다.
- official API schema가 변경되면 `backend/apps/common/errors.py`의 error code catalog도 함께 갱신해야 한다.
- `API_ERROR_MESSAGES`는 official schema와 테스트로 동기화하지만, schema에서 자동 생성하는 파이프라인은 아직 없다.
- Accounts/Profile 모델 검증은 정적 소스 계약 테스트와 Django migration check를 통과했다. DB runtime 검증은 아직 필요하다.
- nickname 길이 제한, nickname 고유성, profile 생성 서비스 호출 시점은 승인 문서에 구체 값이 없어 구현하지 않았다.
- Accounts/Profile 테이블명을 명시해야 한다면 먼저 Obsidian 승인 문서에 확정값을 추가해야 한다.
- 신규 profile 전적 기본값을 `0`으로 고정해야 한다면 먼저 Obsidian 승인 문서에 확정값을 추가해야 한다.
- Refresh token 저장 구조와 Security Event 모델은 정적 소스 계약, 순수 helper 테스트, Django migration check를 통과했다. DB runtime 검증은 아직 필요하다.
- `RefreshToken`은 문서에 명시된 token 소유자 `user_id` 저장 필드를 가진다. 실제 FK, `CASCADE`/`PROTECT`/`SET_NULL` 정책이 필요하면 먼저 Obsidian 승인 문서에 확정해야 한다.
- 실제 JWT 발급과 refresh API service는 A안 기준으로 구현했다. refresh rotation은 `transaction.atomic()` + `select_for_update()`를 사용한다. 실제 DB migration 적용과 PostgreSQL runtime 검증은 아직 남아 있다.
- security event의 비인증 상황(CSRF 실패, 로그인 실패 반복)은 A안에 따라 `user_id = null`로 저장한다. metadata는 `{}` 기본 JSON object이며 raw token/token hash/password/cookie/CSRF token 원문 저장은 금지한다.
- Auth login response serializer는 official schema의 nested `session` 구조에 맞췄다. Cookie name `pilot_access`, `pilot_refresh`는 아직 승인 문서 확정값을 찾지 못했으므로 임의 변경하지 않았다.
- `auth.logout`은 refresh token family 식별 방식이 미확정이라 501로 유지한다. refresh cookie path가 `/api/v1/auth/refresh`라서 `/api/v1/auth/logout` 요청에 refresh cookie가 자동 전송되지 않고, A안 access token claim에는 `family_id`가 없다.
- `auth.signup`은 신규 profile public record 초기값/생성 정책이 별도 확정되지 않아 501로 유지한다.
- Auth `login`, `refresh`, `me` service는 구현됐지만 실제 PostgreSQL migration 적용과 DB runtime flow 검증은 아직 수행하지 못했다.
- Auth response의 `profile.style_summary.metrics`는 snapshot이 없으면 0.0 metrics를 반환한다. 이 값은 AI Profile empty metrics 계산과 맞지만, Auth response default 표시 정책으로 별도 승인된 것은 아니므로 UI/서비스 연동 전 재확인이 필요하다.
- Match storage Task 6은 `matches`, `match_participants`, `turns`, `action_submissions`, `turn_results` 모델 골격과 participant/json snapshot 검증 helper까지 구현했다.
- Match storage 모델은 삭제 정책을 임의 결정하지 않기 위해 `ForeignKey(on_delete=...)`를 쓰지 않고 문서의 `*_id` 필드로 구성했다. 실제 FK 정책이 필요하면 승인 문서 확정 후 변경해야 한다.
- `jsonschema`는 `requirements.txt`에 고정되어 있지만 현재 로컬 Python 환경에는 설치되어 있지 않아 `validate_json_snapshot_payload()` runtime 검증은 아직 수행하지 못한다.
- `matches/story` 세부 문서는 `draft`지만, 승인 계약 17번에서 핵심 테이블과 JSONField 원칙은 확정되어 있다.
- Story storage Task 7은 `story_cases`, `apparitions`, `stages`, `true_name_fragments`, `false_clues`, `player_story_progress` 모델 골격과 `schema_version` 검증 helper까지만 구현했다.
- Story 공식 콘텐츠 seed, 공식 단서/거짓 단서 텍스트 생성, trigger/reveal 실행 로직은 `needs-decision` 문서가 섞여 있어 구현하지 않았다.
- Story 모델도 삭제 정책을 임의 결정하지 않기 위해 `ForeignKey(on_delete=...)`를 쓰지 않고 문서의 `*_id` 필드로 구성했다.
- `jsonschema`는 현재 로컬 Python 환경에 설치되어 있지 않아 `validate_story_policy_payload()` runtime 검증은 아직 수행하지 못한다.
- Turn resolution Task 8은 `backend/apps/matches/resolution.py`에 순수 resolve service로 구현됐다. Deadline 초과 제출은 official `TURN_DEADLINE_EXPIRED` `ApiError` 객체를 반환하고, 미제출 deadline 초과는 player action `silence`, `timed_out`, timeout count +1로 resolve한다.
- Task 8 resolve는 `game_rules.matchups.get_matchup_result()`와 `game_rules.outcomes.determine_ai_story_outcome()`을 사용한다. LLM/RAG/embedding, 공포 상태, 상성표 외부 봉인 방해 가산, Story trigger 실행, DB 저장은 추가하지 않았다.
- `ApiError`는 예외가 아니라 official response payload 객체다. API view/service 경계에서 이를 HTTP error response로 바꾸는 방식은 이후 DRF 연결 단계에서 확정해야 한다.
- `ActionView.display_name` 매핑 값은 승인 문서에서 별도 확정값을 찾지 못했으므로 Task 8에서는 구현하지 않았다.
- `submitted_at == deadline_at`, `server_time == deadline_at` 경계값은 문서에 별도 문구가 없어 현재 구현은 `>`인 경우만 deadline 초과로 본다.
- AI Profile Task 9은 `PlayerActionEvent`와 `StyleMetricSnapshot` 모델 골격, `build_action_event_from_turn_resolution()`, `calculate_style_snapshot()`, `recalculate_final_style_snapshot()` 순수 service까지 구현했다.
- AI Profile 모델에는 문서에 없는 `db_table`, `ForeignKey`, `on_delete`, JSONField, timestamp, result/clue enum을 추가하지 않았다.
- AI Profile 실제 DB save/delete, transaction 연결, `profiles.Profile` style summary 표시 필드 업데이트는 Django/DRF service 단계에서 별도 구현해야 한다.
- Retrieval Task 10은 `RetrievalDocument`, `RetrievalChunk`, `RetrievalQueryLog`, chunking 순수 함수, source allowlist, config 기반 search default/embedding model getter까지 구현했다.
- Retrieval allowlist는 `docs/09_Approved_Contracts/*`, `docs/05_Story_Mode/02_거울_속의_손님.md`, approved/implementation-ready game rule docs only로 제한했다. `docs/02_Game_Rules/07_확률_판정.md`는 needs-decision 상태라 제외했다.
- Task 11로 `accounts`, `profiles`, `matches`, `story`, `ai_profile`, `retrieval`의 initial migration을 생성했다.
- Task 12로 official API endpoint 13개를 Django URL resolver에 연결했다. `story`, `matches`, `profiles` view/serializer/urls scaffold를 추가했으며, 실제 service 미구현 endpoint는 `SERVICE_NOT_IMPLEMENTED` 501 envelope로 응답한다.
- Retrieval provider 호출, vector search, query log write path, LLM generation log 연결은 아직 구현하지 않았다.
- Auth 구현은 보안 요구가 높으므로 Django project scaffolding, dependency contract, token model, CSRF/cookie test가 선행되어야 한다.
- RAG는 구현 범위에 포함되지만 검색 결과가 룰/승패/인증/단서를 바꾸면 안 된다.

## Recommended Next Actions

1. Task 13 `API response envelope runtime boundary`는 확정된 A안 request_id 정책과 A안 501 service-not-implemented 정책을 따른다.
2. Auth runtime 구현은 확정된 A안 JWT 발급 service, refresh rotation DB transaction, SecurityEvent actor/metadata 정책을 기준으로 진행한다.
3. Dockerfile 배포 준비는 승인 계약 24번의 Gate A 문서 정렬 이후 Gate B 이미지 빌드 검증으로 진행한다.
4. Dockerfile 이미지 빌드 검증을 수행하려면 승인 후 `docker build -f ops/docker/backend.Dockerfile -t skn27-backend:local .` 또는 `docker compose -f ops/docker/docker-compose.yml build api`를 실행한다.
5. DB runtime 검증을 수행하려면 `ops/docker/docker-compose.yml` 기준으로 PostgreSQL `pgvector` 컨테이너를 기동한 뒤 `backend/manage.py migrate`를 실행한다.
