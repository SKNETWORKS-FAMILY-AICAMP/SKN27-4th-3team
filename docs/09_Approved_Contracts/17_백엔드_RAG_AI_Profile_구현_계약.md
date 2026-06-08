---
title: "백엔드 RAG AI Profile 구현 계약"
status: "approved"
type: "approved-backend-rag-ai-profile-implementation-contract"
source: "[[01_MVP/04_MVP_확정_필요_항목]], [[03_Backend/99_Backend_구현_확정]], [[06_AI_Profile/99_AI_Profile_구현_확정]], [[09_Approved_Contracts/09_RAG_도입_기준]]"
created: "2026-06-02"
updated: "2026-06-04"
---

# 백엔드 RAG AI Profile 구현 계약

이 문서는 프론트엔드 구현과 LLM 생성 구현을 제외한 1차 MVP 백엔드 구현 준비 기준이다.

## 적용 범위

포함한다.

- Django 백엔드 앱 경계
- 사용자/프로필 모델 기준
- 매치/턴/제출/결과 저장 구조
- AI 스토리 서버 데이터 구조
- JSONField 사용 범위와 검증 방식
- API 명세 관리 방식
- 로컬 실행 구성
- AI Profile 행동 이벤트와 스타일 지표 계산 기준
- RAG 검색용 `retrieval` 앱, 문서/청크/검색 로그 구조
- AI 스토리 매치 상태 동기화를 위한 Redis/Channels/WebSocket runtime

프로젝트 최상위 폴더 구조는 [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]을 따른다.

제외한다.

- 프론트엔드 구현
- LLM provider, prompt, generation 구현
- LLM 생성 문장 품질 정책
- KAG 구현
- PvP realtime 구현
- 운영 배포 자동화

AI 스토리 매치 상태 동기화를 위한 Redis/Channels/WebSocket 구현은 [[09_Approved_Contracts/29_MVP_Realtime_Redis_WebSocket_계약]]을 따른다.

단, Dockerfile을 이용한 백엔드 이미지 빌드와 Django 배포 준비는 후속 작업 후보로 둔다.

이 문서에서 현재 확정된 범위는 로컬 실행 구성과 배포 준비 경계까지다.

Dockerfile 이미지 빌드와 배포 결정 타이밍은 [[09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약]]을 따른다.

production 배포 구현은 아래 항목이 별도 계약으로 확정되기 전까지 진행하지 않는다.

- 배포 대상 환경
- image registry와 image tag 규칙
- Django production entrypoint
- WSGI/ASGI server 선택
- static/media 처리 방식
- secret/env 주입 방식
- migration 실행 전략
- health check 기준
- reverse proxy, TLS, domain 구성
- CI/CD 또는 운영 배포 자동화 방식

위 production 배포 기준은 [[09_Approved_Contracts/28_Production_배포_계약]]과 [[09_Approved_Contracts/29_MVP_Realtime_Redis_WebSocket_계약]]에서 확정되었다.

PvP 모드는 없다.

Auth/Match/Participant/Turn 구조는 [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]에 따라 AI 스토리 매치 기준으로 정리한다.

## 사용자 모델

| 항목 | 확정값 |
|---|---|
| Django user model | `accounts.User` custom user model |
| base class | `AbstractBaseUser + PermissionsMixin` |
| 로그인 식별자 | email |
| nickname 저장 위치 | `profiles.Profile` |

`accounts.User`는 인증과 권한에 집중한다.

`profiles.Profile`은 nickname, 전적 요약, 공개 프로필, 스타일 요약 표시 데이터를 담당한다.

## AI 참가자 표현

괴이는 Django user가 아니다.

`match_participants`는 아래 구분값을 가진다.

| 필드 | 기준 |
|---|---|
| `participant_type` | `human` 또는 `apparition` |
| `user_id` | human 참가자에서만 사용한다. apparition 참가자에서는 nullable이다. |
| `apparition_id` | apparition 참가자에서 사용한다. human 참가자에서는 nullable이다. |

매치 권한과 행동 제출은 human player participant와 apparition participant 기준으로 처리한다.

## 핵심 저장 구조

| 영역 | 테이블 |
|---|---|
| 매치 | `matches` |
| 참가자 | `match_participants` |
| 턴 | `turns` |
| 행동 제출 | `action_submissions` |
| 턴 결과 | `turn_results` |
| 사건 | `story_cases` |
| 괴이 | `apparitions` |
| 스테이지 | `stages` |
| 진명 조각 | `true_name_fragments` |
| 거짓 단서 | `false_clues` |
| 사용자 진행도 | `player_story_progress` |

## JSONField 기준

JSONField는 아래 용도로만 사용한다.

- 결과 스냅샷
- 공개/비공개 로그 스냅샷
- 룰/정책 스냅샷
- 괴이별 조건처럼 승인 문서와 함께 버전 관리되는 작은 정책 데이터

아래 항목은 JSONField에 숨기지 않고 정규화한다.

- 사용자
- 매치
- 참가자
- 턴
- 행동 제출
- 핵심 자원 수치
- 승패 상태
- 사건/괴이/스테이지 FK
- 진명 조각/거짓 단서 소유 상태

모든 JSONField payload에는 `schema_version`을 포함한다.

JSONField 검증은 Python `jsonschema`로 수행한다.

검증 위치는 model boundary, serializer boundary, service boundary 중 해당 payload가 생성되거나 외부 입력으로 들어오는 지점이다.

## API 명세 기준

기존 `api-spec/pilot-mvp-api.jsonc`는 결정 전 draft로 유지한다.

승인된 API는 별도 official JSONC와 strict JSON 생성본으로 분리한다.

| 파일 | 역할 |
|---|---|
| `api-spec/pilot-mvp-api.jsonc` | 논의용 draft |
| `api-spec/pilot-mvp-api.official.jsonc` | 승인된 API 원본 |
| `api-spec/pilot-mvp-api.official.json` | 도구용 strict JSON 생성본 |

official 명세는 [[09_Approved_Contracts/05_API_명세_관리_기준]], [[09_Approved_Contracts/06_API_응답_형태_기준]], [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]을 따른다.

상세 request/response schema는 official 명세에만 구현 기준으로 기록한다.

## 로컬 실행 구성

1차 MVP 로컬 Docker Compose 범위는 아래로 제한한다.

- Django API
- PostgreSQL
- PostgreSQL `pgvector`
- Redis channel layer

아래 컨테이너는 1차 MVP 로컬 실행 구성에서 제외한다.

- LLM provider emulator
- KAG 전용 저장소

`ops/docker/backend.Dockerfile`은 백엔드 이미지 빌드의 시작점으로 둘 수 있다.

다만 현재 로컬/dev 기준 entrypoint는 WebSocket을 처리할 수 있는 Django ASGI runtime이며, production 배포 entrypoint는 [[09_Approved_Contracts/28_Production_배포_계약]]과 [[09_Approved_Contracts/29_MVP_Realtime_Redis_WebSocket_계약]]을 따른다.

production 배포용 이미지는 별도 배포 계약에서 WSGI/ASGI server, process model, static 처리, health check, migration 전략을 확정한 뒤 조정한다.

이미지 빌드 검증은 후속 작업에서 아래 중 하나로 수행한다.

- `docker build -f ops/docker/backend.Dockerfile -t skn27-backend:local .`
- `docker compose -f ops/docker/docker-compose.yml build api`

상세 결정 게이트는 [[09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약]]을 따른다.

## Cookie와 CSRF

| 항목 | 확정값 |
|---|---|
| access token 전달 | HttpOnly cookie |
| refresh token 전달 | HttpOnly cookie |
| local/dev Secure cookie | `Secure=false` 허용 |
| production Secure cookie | `Secure=true` 필수 |
| SameSite | `Lax` |
| CSRF 적용 범위 | 모든 state-changing endpoint |
| CSRF endpoint | `GET /api/v1/auth/csrf` |
| CSRF header | `X-CSRFToken` |

로컬 환경에서도 CSRF 흐름은 비활성화하지 않는다.

## AI Profile 기준

행동 이벤트는 턴 resolve 시점에 저장한다.

스타일 지표는 각 턴 resolve 직후 계산한다.

매치 종료 시 최종 재계산을 수행한다.

분모가 0인 지표는 `0.0`으로 저장한다.

개인정보 삭제 시 기본 정책은 아래와 같다.

- 행동 이벤트 삭제
- 스타일 스냅샷 삭제
- 전적 요약은 사용자 삭제 정책에 맞춰 삭제 또는 익명화한다.

## RAG 구현 기준

RAG는 1차 MVP에서 `retrieval` 앱 구현 준비 범위에 포함한다.

단, RAG 검색 결과는 룰, 승패, 인증, 권한, 진명 조각, 거짓 단서, 괴이 행동 선택을 변경할 수 없다.

### 검색 대상

| 대상 | 포함 여부 |
|---|---|
| `docs/09_Approved_Contracts` | 포함 |
| `docs/05_Story_Mode/02_거울_속의_손님.md` | 포함 |
| 승인된 게임 룰 문서 | 포함 |
| 결정 전 검토안 | 기본 제외 |
| LLM draft/prompt 초안 | 기본 제외 |

### Chunking

- 기본 chunk 크기: 500-900자
- 문단 경계를 우선한다.
- overlap은 최대 100자다.
- chunk에는 `document_id`, `chunk_id`, `source_path`, `schema_version`을 저장한다.

### Vector DB

PostgreSQL + `pgvector`를 사용한다.

embedding model id는 환경 설정으로 주입한다.

기본 추천값은 `text-embedding-3-small`이다.

모델 이름은 코드에 하드코딩하지 않는다.

### 검색 기본값

| 항목 | 확정값 |
|---|---|
| `top_k` | 6 |
| `score_threshold` | 0.72 |

### 검색 로그

RAG query log는 최소 아래 항목을 저장한다.

- query
- caller
- document_id
- chunk_id
- score
- threshold
- top_k
- created_at

## 구현 금지선

- RAG 검색 결과로 룰을 수정하지 않는다.
- RAG 검색 결과로 승패를 바꾸지 않는다.
- RAG 검색 결과로 인증/권한 정책을 바꾸지 않는다.
- RAG 검색 결과로 공식 단서, 진명 조각, 거짓 단서를 새로 만들지 않는다.
- LLM 생성 결과를 서버 판정 근거로 저장하지 않는다.
- 프론트가 API, DB, 룰 계약을 임의 확정하지 않는다.

## 남은 오너 결정

프론트엔드 구현과 LLM generation 구현을 제외한 백엔드/RAG/AI Profile 구현 전 남은 오너 결정은 없다.

전체 7x7 행동 상성표와 `간파` vs `침묵` 후보 2개 생성 방식은 [[09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약]]에서 확정되었다.

refresh token family, reuse 감지, CSRF rotation은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]에서 확정되었다.

브라우저 종료/네트워크 끊김과 시간초과 판정 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]에서 확정되었다.

API official 상세 request/response schema는 [[09_Approved_Contracts/22_API_상세_Schema_계약]]에서 확정되었다.

프로젝트 폴더 구조는 [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]에서 확정되었다.
