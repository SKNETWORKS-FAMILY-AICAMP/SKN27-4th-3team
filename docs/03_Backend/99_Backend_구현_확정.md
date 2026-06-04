---
title: "Backend 구현 확정"
status: "implementation-ready"
type: "implementation-confirmation"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-04"
---

# Backend 구현 확정

이 문서는 백엔드 구현 착수 전 승인받는 최종 기준 문서다.

## 확정 전 조건

- 현재 남은 백엔드/RAG/AI Profile 구현 전 결정 없음
- Dockerfile 기반 이미지 빌드와 Django 배포는 후속 배포 작업 전 별도 계약 확정 필요

## 확정된 API/Auth 조건

| 결정 | 확정값 |
|---|---|
| API prefix | `/api/v1` |
| API 응답 형태 | 성공 `{ data, meta }`, 실패 `{ error, meta }` |
| access token 전달 | HttpOnly cookie |
| refresh token 전달 | HttpOnly cookie |
| access token | JWT, 15분 |
| refresh token | JWT, 14일, `jti`, `family_id` 포함 |
| refresh token family id | 로그인 성공 시 UUIDv4 |
| refresh token jti | refresh token 발급마다 UUIDv4 |
| refresh token 저장 | 원문 저장 금지, 서버 secret 기반 HMAC-SHA256 hash 저장 |
| refresh token reuse error code | `REFRESH_TOKEN_REUSED` |
| refresh token reuse 처리 | 해당 family 전체 revoke, cookie 제거, security event log 저장 |
| refresh 동시성 | DB transaction + row lock |
| refresh grace window | 없음 |
| access cookie path | `/api/v1` |
| refresh cookie path | `/api/v1/auth/refresh` |
| CSRF 적용 범위 | 모든 state-changing endpoint |
| CSRF token endpoint | `GET /api/v1/auth/csrf` |
| CSRF header | `X-CSRFToken` |
| CSRF rotation | 로그인 시 rotation, refresh 시 유지, logout 후 새 token 필요 |
| CSRF/CORS origin | 명시 allowlist만 허용 |
| 프론트 MVP endpoint 목록 | [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]을 따른다. |
| API 상세 request/response schema | `api-spec/pilot-mvp-api.official.jsonc`와 `api-spec/pilot-mvp-api.official.json`을 따른다. |
| 프로젝트 폴더 구조 | [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]을 따른다. |

## 확정된 Backend/RAG/AI Profile 조건

| 결정 | 확정값 |
|---|---|
| Django user model | `accounts.User` custom user model |
| User base class | `AbstractBaseUser + PermissionsMixin` |
| 로그인 식별자 | email |
| nickname 저장 | `profiles.Profile` |
| AI participant | `participant_type = human/apparition`, `user_id` nullable, `apparition_id` nullable |
| JSONField 사용 범위 | 결과 스냅샷, 로그 스냅샷, 룰/정책 스냅샷, 작은 정책 데이터 |
| JSONField 검증 | `schema_version` 필수, Python `jsonschema` |
| 로컬 Docker Compose | Django API + PostgreSQL + `pgvector` |
| 로컬 Docker Compose 제외 | Redis, WebSocket worker, LLM provider emulator, KAG 전용 저장소 |
| Dockerfile 이미지 빌드 | 후속 배포 준비 후보. 로컬/dev 이미지 빌드 검증부터 진행 |
| Django production 배포 | 배포 대상, WSGI/ASGI server, static/media, secret, migration, health check 확정 전 구현 보류 |
| local/dev Secure cookie | `Secure=false` 허용 |
| production Secure cookie | `Secure=true` 필수 |
| SameSite | `Lax` |
| RAG 앱 | `retrieval` 포함 |
| RAG vector DB | PostgreSQL + `pgvector` |
| RAG chunking | 500-900자, 문단 경계 우선, overlap 최대 100자 |
| RAG embedding model | env/config 주입, 기본 추천값 `text-embedding-3-small` |
| RAG 검색 기본값 | `top_k=6`, `score_threshold=0.72` |
| AI Profile 이벤트 저장 | 턴 resolve 시점 |
| AI Profile 계산 | 각 턴 resolve 직후, 매치 종료 시 최종 재계산 |
| 0 분모 기본값 | `0.0` |
| 개인정보 삭제 기본 정책 | 행동 이벤트와 스타일 스냅샷 삭제 |
| 전체 7x7 행동 상성표 | [[02_Game_Rules/04_상성_규칙]]을 따른다. |
| `간파` vs `침묵` 다음 행동 후보 2개 | [[09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약]]을 따른다. |
| AI 스토리 시간초과 판정 | 브라우저 종료/네트워크 끊김이 아니라 서버 `deadline_at` 기준으로 판정한다. |
| 시간초과 상세 기준 | [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]을 따른다. |

백엔드/RAG/AI Profile 상세 기준은 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]을 따른다.

게임 규칙 상세 기준은 [[09_Approved_Contracts/18_게임_규칙_상성표_상태_승패_계약]]을 따른다.

Auth 보안 상세 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

시간초과 판정 상세 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]을 따른다.

API 상세 schema 기준은 [[09_Approved_Contracts/22_API_상세_Schema_계약]]을 따른다.

프로젝트 폴더 구조 기준은 [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]을 따른다.

## Dockerfile 기반 배포 준비 메모

`ops/docker/backend.Dockerfile`은 백엔드 이미지 빌드 시작점으로 둔다.

현재 로컬/dev entrypoint는 Django `runserver`이며 production entrypoint로 확정하지 않는다.

Dockerfile 이미지 빌드와 Django 배포 결정 타이밍은 [[09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약]]을 따른다.

후속 배포 작업에서 먼저 검증할 명령 후보는 아래와 같다.

- `docker build -f ops/docker/backend.Dockerfile -t skn27-backend:local .`
- `docker compose -f ops/docker/docker-compose.yml build api`

운영 배포를 실제 구현하려면 아래 항목을 먼저 확정한다.

- 배포 대상 환경
- image registry와 tag 규칙
- WSGI/ASGI server
- static/media 처리
- secret/env 주입 방식
- migration 실행 전략
- health check
- reverse proxy, TLS, domain
- CI/CD 또는 수동 배포 절차
