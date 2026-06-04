# Backend Implementation Report

> 목적: Obsidian 전체 문서를 먼저 스캔하되, 구현은 승인된 source of truth 범위만 진행한다. 이 파일은 각 구현 Task의 근거, 변경 파일, 검증 결과, 보류 사유를 누적 기록한다.

## 적용 원칙

- 구현 기준은 `docs/09_Approved_Contracts/*`, `99_*_구현_확정`, `implementation-ready` 문서, `api-spec/pilot-mvp-api.official.jsonc`, `api-spec/pilot-mvp-api.official.json`이다.
- `draft` 문서는 승인 계약이 특정 범위를 참조한 경우에만 제한적으로 사용한다.
- `needs-decision` 문서는 단독 구현 근거로 사용하지 않는다.
- 문서에 없는 기본값, 테이블명, 삭제 정책, FK 정책, cookie name, status enum, seed 데이터는 임의로 만들지 않는다.
- 문서 간 충돌, 누락, 애매함이 있으면 구현하지 않고 체크포인트에 기록한다.
- 프론트엔드와 LLM generation 구현은 현재 범위에서 제외한다.
- RAG/LLM은 룰 판정, 승패, 인증/권한, 진명 조각, 거짓 단서, 괴이 행동 선택 권위를 바꾸지 않는다.

## 구현 리포트 작성 규칙

각 Task는 아래 항목을 반드시 기록한다.

- 참조한 승인 문서/공식 schema
- 구현/수정한 파일
- 구현 내용
- 의도적으로 구현하지 않은 범위
- RED 검증 명령과 결과
- GREEN 검증 명령과 결과
- 전체 회귀 검증 명령과 결과
- dependency/runtime 검증 가능 여부
- 남은 리스크와 다음 확인 지점

## 현재 검증 상태

- 최종 확인 일시: 2026-06-04
- 실행 위치: `D:\dev\Project\SKN27-4th-3team`
- 전체 테스트 명령: `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
- 전체 테스트 결과: `88 passed`
- Django check 명령: `.\.venv\Scripts\python.exe backend\manage.py check`
- Django check 결과: `System check identified no issues (0 silenced).`
- migration check 명령: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval --dry-run --check`
- migration check 결과: `No changes detected in apps 'accounts', 'matches', 'profiles', 'story', 'ai_profile', 'retrieval'`
- dependency 확인 명령: `.\.venv\Scripts\python.exe -c "import django, jsonschema, rest_framework; print(django.get_version()); print(jsonschema.__version__); print(rest_framework.VERSION)"`
- dependency 확인 결과: `5.2.14`, `4.26.0`, `3.17.1`
- 상태: PARTIALLY VERIFIED

## 완료된 구현 요약

| Task | 범위 | 상태 | 주요 파일 |
|---|---|---|---|
| Task 1 | Django backend scaffold/dependency contract | 완료, 정적 검증 | `requirements.txt`, `backend/manage.py`, `backend/config/*` |
| Task 2 | API response/error envelope | 완료, 순수 테스트 검증 | `backend/apps/common/errors.py`, `backend/apps/common/responses.py` |
| Task 3 | User/Profile storage skeleton | 완료, 정적 검증 | `backend/apps/accounts/models.py`, `backend/apps/profiles/models.py` |
| Task 4 | Refresh token/security event skeleton | 완료, 정적/순수 검증 | `backend/apps/accounts/models.py`, `backend/apps/accounts/tokens.py` |
| Task 5 | Auth API scaffold | 완료, 정적 schema 검증 | `backend/apps/accounts/serializers.py`, `backend/apps/accounts/views.py`, `backend/apps/accounts/urls.py` |
| Task 6 | Match storage skeleton | 완료, 정적 검증 | `backend/apps/matches/constants.py`, `backend/apps/matches/models.py`, `backend/apps/matches/services.py` |
| Task 7 | Story storage skeleton | 완료, 정적 검증 | `backend/apps/story/models.py`, `backend/apps/story/services.py` |
| Task 8 | Game rules resolve service 연결 | 완료, 순수 테스트 검증 | `backend/apps/matches/resolution.py`, `backend/apps/matches/services.py` |
| Task 9 | AI Profile persistence 연결 | 완료, 정적/순수 테스트 검증 | `backend/apps/ai_profile/models.py`, `backend/apps/ai_profile/services.py` |
| Task 10 | Retrieval 구조 | 완료, Django check/정적/순수 테스트 검증 | `backend/apps/retrieval/models.py`, `backend/apps/retrieval/chunking.py`, `backend/apps/retrieval/services.py` |
| Task 11 | Django initial migrations | 완료, migration check/Django check/전체 테스트 검증 | `backend/apps/*/migrations/0001_initial.py` |

## Task 8 상세 기록

### 참조한 승인 문서/공식 schema

- `docs/02_Game_Rules/04_상성_규칙.md`
- `docs/02_Game_Rules/05_승패_조건.md`
- `docs/02_Game_Rules/06_시간초과_규칙.md`
- `docs/09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약.md`
- `docs/09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약.md`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`
- `api-spec/pilot-mvp-api.official.jsonc`

### 구현/수정한 파일

- 생성: `backend/apps/matches/resolution.py`
- 생성: `backend/tests/matches/test_turn_resolution_contract.py`
- 수정: `backend/apps/matches/services.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `memory.md`

### 구현 내용

- `validate_submission_deadline()`을 추가했다.
- `submitted_at > deadline_at`이면 official `TURN_DEADLINE_EXPIRED` `ApiError` 객체를 반환한다.
- 제출이 없고 서버 기준 `server_time > deadline_at`이면 player action을 `silence`로 resolve한다.
- 시간초과 resolve 결과는 `timeout_applied=True`, `turn_status="timed_out"`, `player_timeout_count + 1`로 반환한다.
- 정상 제출 resolve 결과는 `turn_status="resolved"`로 반환한다.
- 공개 로그와 effect code는 `backend.apps.game_rules.matchups.get_matchup_result()` 결과를 그대로 사용한다.
- 승패는 `backend.apps.game_rules.outcomes.determine_ai_story_outcome()`을 사용한다.
- 봉인 성공은 `seal_condition_met`과 상성표 effect code의 `seal_success_if_condition_met`/`seal_failed`만으로 판단한다.

### 의도적으로 구현하지 않은 범위

- LLM/RAG/embedding 기반 판정 변경
- 공포 상태 생성
- 상성표 외부 봉인 방해 가산
- Story trigger/reveal 실행
- DB 저장 및 transaction 처리
- DRF response 변환
- `ActionView.display_name` 매핑

### 검증

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
- RED 결과: `5 failed`; `backend/apps/matches/resolution.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\matches\test_turn_resolution_contract.py -v`
- GREEN 결과: `5 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `77 passed`
- dependency 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
- dependency 확인 결과: `None`, `None`

### 남은 리스크

- Django/jsonschema가 현재 로컬 Python 환경에 없어 `manage.py check`, migration, DB 저장, 실제 API runtime 검증은 아직 수행하지 못한다.
- effect code를 실제 `ResourceState` delta로 적용하는 엔진은 별도 승인 범위와 테스트가 필요하다.
- `ActionView.display_name` 매핑은 공식 출처 확인 후 API serializer 단계에서 구현해야 한다.
- `ApiError`는 예외가 아니라 official response payload 객체다. DRF 경계에서 HTTP response로 변환하는 방식은 이후 구현해야 한다.
- `submitted_at == deadline_at`, `server_time == deadline_at` 경계값은 문서에 별도 문구가 없어 현재는 `>`인 경우만 deadline 초과로 본다.

## 다음 구현 후보

### Task 9: AI Profile persistence 연결

상태: 완료, 정적/순수 테스트 검증

#### 참조한 승인 문서/공식 schema

- `docs/06_AI_Profile/01_행동_이벤트.md`
- `docs/06_AI_Profile/02_스타일_지표.md`
- `docs/06_AI_Profile/99_AI_Profile_구현_확정.md`
- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/07_백엔드_앱_경계_기준.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`

#### 구현/수정한 파일

- 생성: `backend/apps/ai_profile/models.py`
- 생성: `backend/apps/ai_profile/services.py`
- 생성: `backend/tests/ai_profile/test_ai_profile_persistence_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `docs/superpowers/reports/2026-06-04-backend-implementation-report.md`
- 수정: `memory.md`

#### 구현 내용

- `PlayerActionEvent` 모델 골격을 추가했다.
- 행동 이벤트 모델은 승인 문서의 저장 항목만 필드로 둔다.
- `StyleMetricSnapshot` 모델 골격을 추가했다.
- 스타일 스냅샷 모델은 승인된 9개 지표 필드와 `user_id`만 둔다.
- 테이블명, FK, 삭제 cascade, JSONField, created/updated timestamp, result/clue enum은 문서 확정값이 없어 추가하지 않았다.
- `build_action_event_from_turn_resolution()`을 추가해 `TurnResolution` 결과와 명시 입력값으로 `metrics.ActionEvent`를 만든다.
- `calculate_style_snapshot()`은 기존 `calculate_style_metrics()`를 재사용한다.
- `recalculate_final_style_snapshot()`은 매치 종료 시 최종 재계산 진입점으로 같은 계산 함수를 재사용한다.
- 개인정보 삭제 대상은 `AI_PROFILE_PERSONAL_DATA_MODELS = ("PlayerActionEvent", "StyleMetricSnapshot")`로 고정했다.

#### 의도적으로 구현하지 않은 범위

- 실제 DB `save()`, transaction, bulk delete 실행
- `profiles.Profile` 스타일 표시 필드 업데이트
- LLM summary 기반 스타일 판단
- 스타일 라벨/표시 문구 생성
- 테이블명과 FK/on_delete 정책
- `result_code`, `clue_truth_state`, `match_outcome` enum

#### 검증

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_ai_profile_persistence_contract.py -v`
- RED 결과: `5 failed`; `backend/apps/ai_profile/models.py`, `backend/apps/ai_profile/services.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `C:\Python314\python.exe -m pytest backend\tests\ai_profile\test_ai_profile_persistence_contract.py -v`
- GREEN 결과: `5 passed`
- AI Profile 범위 실행 위치: `D:\dev\Project\pilot`
- AI Profile 범위 명령: `C:\Python314\python.exe -m pytest backend\tests\ai_profile -v`
- AI Profile 범위 결과: `10 passed`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `C:\Python314\python.exe -m pytest backend\tests -v`
- 전체 결과: `82 passed`
- dependency 확인 명령: `C:\Python314\python.exe -c "import importlib.util; print(importlib.util.find_spec('django')); print(importlib.util.find_spec('jsonschema'))"`
- dependency 확인 결과: `None`, `None`

#### 남은 리스크

- Django/jsonschema가 현재 로컬 Python 환경에 없어 `manage.py check`, migration, DB 저장, 실제 삭제 쿼리 runtime 검증은 아직 수행하지 못한다.
- 행동 이벤트 저장 시점은 순수 service 경계로만 연결했다. 실제 `matches` DB transaction 안에서 저장하는 호출 위치는 DRF/DB service 구현 단계에서 확정해야 한다.
- `profiles.Profile`의 style summary 표시 필드 업데이트는 이번 범위에서 제외했다. 공식 schema와 저장 위치는 확인됐지만, 업데이트 트리거와 라벨 생성 규칙은 별도 구현 범위가 필요하다.
- style snapshot 테이블명이 승인 문서에 없으므로 `db_table`을 지정하지 않았다. 필요하면 Obsidian 승인 문서에 먼저 확정해야 한다.
- 개인정보 삭제는 대상 모델 목록만 고정했다. 실제 cascade/delete 실행 정책은 DB service 단계에서 검증해야 한다.

## 다음 구현 후보

### Task 10: Retrieval 구조

상태: 완료, Django check/정적/순수 테스트 검증

#### 참조한 승인 문서/공식 schema

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/09_RAG_도입_기준.md`
- `docs/02_Game_Rules/99_Game_Rules_구현_확정.md`

#### 구현/수정한 파일

- 생성: `backend/apps/retrieval/models.py`
- 생성: `backend/apps/retrieval/chunking.py`
- 생성: `backend/apps/retrieval/services.py`
- 생성: `backend/tests/retrieval/test_retrieval_contract.py`
- 수정: `docs/superpowers/plans/2026-06-02-backend-implementation-order.md`
- 수정: `docs/superpowers/reports/2026-06-04-backend-implementation-report.md`
- 수정: `memory.md`

#### 구현 내용

- `RetrievalDocument`, `RetrievalChunk`, `RetrievalQueryLog` 모델 골격을 추가했다.
- chunk에는 `document_id`, `chunk_id`, `source_path`, `schema_version`, `content`, `embedding`을 둔다.
- embedding 저장 필드는 PostgreSQL + `pgvector` 기준에 맞춰 `pgvector.django.VectorField`를 사용한다.
- query log에는 `query`, `caller`, `document_id`, `chunk_id`, `score`, `threshold`, `top_k`, `created_at`을 둔다.
- 검색 대상 allowlist를 추가했다.
- allowlist는 `docs/09_Approved_Contracts/*`, `docs/05_Story_Mode/02_거울_속의_손님.md`, 승인/implementation-ready 게임 룰 문서만 허용한다.
- `docs/02_Game_Rules/02_행동_정의.md` 같은 draft와 `docs/02_Game_Rules/07_확률_판정.md` 같은 needs-decision 문서는 기본 제외한다.
- chunking 상수는 `500`, `900`, `100`으로 분리했다.
- `build_document_chunks()`는 문단 경계를 우선해 `RetrievalChunkPayload`를 생성한다.
- 검색 기본값은 `backend.config.settings`의 `RAG_DEFAULT_TOP_K`, `RAG_DEFAULT_SCORE_THRESHOLD`에서 읽는다.
- embedding model id는 `RAG_EMBEDDING_MODEL_ID` config에서만 읽고, 코드 기본값은 두지 않았다.

#### 의도적으로 구현하지 않은 범위

- embedding provider 호출
- RAG 실제 검색 쿼리
- LLM generation
- retrieval 결과로 룰/승패/인증/권한/진명 조각/거짓 단서/괴이 행동을 바꾸는 로직
- DB migration 파일 생성
- query log 보존 기간
- LLM generation log와 retrieval log 연결
- VectorField dimension 고정

#### 검증

- RED 실행 위치: `D:\dev\Project\pilot`
- RED 명령: `.\.venv\Scripts\python.exe -m pytest backend\tests\retrieval\test_retrieval_contract.py -v`
- RED 결과: `5 failed, 1 passed`; `backend/apps/retrieval/models.py`, `chunking.py`, `services.py` 누락 확인.
- GREEN 실행 위치: `D:\dev\Project\pilot`
- GREEN 명령: `.\.venv\Scripts\python.exe -m pytest backend\tests\retrieval\test_retrieval_contract.py -v`
- GREEN 결과: `6 passed`
- Django check 실행 위치: `D:\dev\Project\pilot`
- Django check 명령: `.\.venv\Scripts\python.exe backend\manage.py check`
- Django check 결과: `System check identified no issues (0 silenced).`
- 전체 실행 위치: `D:\dev\Project\pilot`
- 전체 명령: `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
- 전체 결과: `88 passed`

#### 남은 리스크

- Task 11에서 initial migration을 생성했다. 실제 DB schema 적용 검증은 PostgreSQL 연결 후 별도로 수행해야 한다.
- `VectorField` dimension은 문서에 확정값이 없어 지정하지 않았다. embedding provider와 모델 차원이 확정되면 migration 영향이 있으므로 문서 확정 후 결정해야 한다.
- `docs/02_Game_Rules/07_확률_판정.md`는 `99_Game_Rules_구현_확정.md`가 일부 규칙을 참조하지만 파일 status가 `needs-decision`이라 retrieval allowlist에서는 제외했다. 포함하려면 승인 문서에서 범위를 명확히 해야 한다.
- query log 보존 기간과 LLM generation log 연결 방식은 승인 문서의 후속 설계 대상으로 남아 있어 구현하지 않았다.
- retrieval service는 구조 준비까지만 구현했다. 실제 embedding 생성, vector search, query logging write path는 provider/API 연결 단계에서 별도 구현해야 한다.

## 다음 구현 후보

### Task 11: Django initial migrations

상태: 완료, migration check/Django check/전체 테스트 검증

#### 참조한 승인 문서/공식 schema

- `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`
- `docs/09_Approved_Contracts/23_프로젝트_폴더_구조_계약.md`
- 기존 Task 3-10에서 검증된 Django model scaffold

#### 구현/수정한 파일

- 생성: `backend/apps/accounts/migrations/__init__.py`
- 생성: `backend/apps/accounts/migrations/0001_initial.py`
- 생성: `backend/apps/profiles/migrations/__init__.py`
- 생성: `backend/apps/profiles/migrations/0001_initial.py`
- 생성: `backend/apps/matches/migrations/__init__.py`
- 생성: `backend/apps/matches/migrations/0001_initial.py`
- 생성: `backend/apps/story/migrations/__init__.py`
- 생성: `backend/apps/story/migrations/0001_initial.py`
- 생성: `backend/apps/ai_profile/migrations/__init__.py`
- 생성: `backend/apps/ai_profile/migrations/0001_initial.py`
- 생성: `backend/apps/retrieval/migrations/__init__.py`
- 생성: `backend/apps/retrieval/migrations/0001_initial.py`
- 수정: `.gitignore`

#### 구현 내용

- 승인 계약 테스트를 통과한 현재 Django model scaffold 기준으로 initial migration을 생성했다.
- 앱별 migrations package를 생성했다.
- workspace 내부 `.venv/`가 git에 포함되지 않도록 `.gitignore`에 추가했다.

#### 의도적으로 구현하지 않은 범위

- 실제 PostgreSQL DB에 migration 적용
- seed 데이터 생성
- migration에 없는 신규 필드/기본값/FK 정책 추가
- GraphDB, KAG, LLM, realtime app migration 생성

#### 검증

- RED 실행 위치: `D:\dev\Project\SKN27-4th-3team`
- RED 명령: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval --dry-run --check -v 2`
- RED 결과: exit code `1`; 6개 app의 `0001_initial.py` 생성 필요 확인.
- GREEN 실행 위치: `D:\dev\Project\SKN27-4th-3team`
- GREEN 명령: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval`
- GREEN 결과: 6개 app initial migration 생성.
- migration check 명령: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts profiles matches story ai_profile retrieval --dry-run --check`
- migration check 결과: `No changes detected in apps 'accounts', 'matches', 'profiles', 'story', 'ai_profile', 'retrieval'`
- Django check 명령: `.\.venv\Scripts\python.exe backend\manage.py check`
- Django check 결과: `System check identified no issues (0 silenced).`
- 전체 테스트 명령: `.\.venv\Scripts\python.exe -m pytest backend\tests -v`
- 전체 테스트 결과: `88 passed`

#### 남은 리스크

- `makemigrations`는 로컬 PostgreSQL 연결을 시도하며 `pilot` 사용자 인증 실패 warning을 냈다. migration 생성과 check는 통과했지만 실제 DB apply는 검증하지 못했다.
- PostgreSQL `pgvector` extension 생성과 migration 적용은 DB 실행 구성이 확정된 뒤 별도 검증해야 한다.
- `VectorField` dimension은 문서에 확정값이 없어 migration에도 지정하지 않았다.

## 다음 구현 후보

### Task 12: Official API endpoint 연결

예정 source of truth:

- `api-spec/pilot-mvp-api.official.jsonc`
- `docs/09_Approved_Contracts/22_API_상세_Schema_계약.md`

진행 전 확인할 점:

- official endpoint 13개와 현재 auth scaffold route 차이
- draft endpoint 경로 제외 여부
- API response envelope와 official schema mapping
- 실제 DB service가 미구현인 endpoint의 placeholder/501 처리 기준
- CSRF/cookie/auth runtime 연결 범위
