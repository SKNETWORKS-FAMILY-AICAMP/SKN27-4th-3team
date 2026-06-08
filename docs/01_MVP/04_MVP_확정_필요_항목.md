---
title: "MVP 확정 필요 항목"
status: "needs-decision"
type: "decision-log"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-04"
---

# MVP 확정 필요 항목

이 문서는 구현 전 비어 있는 결정을 모아두는 문서다. 아래 항목은 확정 전까지 구현하지 않는다.

## 최신성 메모

이 문서는 `needs-decision` 상태의 결정 로그다.

현재 승인된 최신 구현 기준은 [[09_Approved_Contracts/00_승인본_목차]]를 우선한다.

특히 아래 항목은 이후 승인본으로 보강되었다.

- LLM runtime 범위: [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]
- `nameless_curse` 별도 사건: [[09_Approved_Contracts/26_무명의_저주_사건_계약]]
- 플레이어 표시 이름, 사건별 결전 조건, RAG source plan: [[09_Approved_Contracts/27_플레이어_이름_무명의_저주_결전_RAG_계약]]

따라서 이 문서의 오래된 `프론트엔드 구현과 LLM generation 구현 제외`, `거울 속의 손님 1종만 구현` 표현은 당시 결정 로그로 보고, 현재 구현 기준 판단은 승인본 목차의 D-940, D-950, D-960을 따른다.

## 제품 결정

- 게임 제목의 최종 이름
- 첫 MVP 괴이 3종의 최종 문장

## 확정된 제품 결정

| 결정 | 확정값 |
|---|---|
| 괴이 범위 | 괴이 3종은 문서로 확정한다. |
| 1차 MVP 구현 괴이 | `거울 속의 손님` 1종만 구현한다. |
| 1차 MVP 구현 제외 괴이 | `우물 밑의 목소리`, `문밖의 어머니` |
| `거울 속의 손님` 공식 브리핑 | [[05_Story_Mode/02_거울_속의_손님]]의 확정된 공식 문장을 따른다. |

## 게임 규칙 결정

- 현재 남은 게임 규칙 결정 없음

## 확정된 게임 규칙 결정

| 결정 | 확정값 |
|---|---|
| 1차 MVP AI 스토리 제한 턴 수 | 12턴 |
| 2차 업데이트 제한 턴 수 후보 | 15턴 |
| 행동 상성표 범위 | 기본 처리로 넘기지 않고 전체 7x7 조합을 문서로 확정한다. |
| 행동 상성표 작성 형식 | 각 조합마다 수치/상태 결과와 화면 공개 로그 문장을 함께 확정한다. |
| 전체 7x7 행동 상성표 | [[02_Game_Rules/04_상성_규칙]]을 따른다. |
| `저주` vs `저주` | 양쪽 이성 -1 후 1d6 대결. 높은 쪽이 추가 이성 -1을 준다. 동률이면 추가 피해 없음. |
| `저주` vs `간파` | 간파자 이성 -2, 단서 획득 실패, 간파자 의심 +1 |
| 의심 기본 효과 | 의심 1당 다음 `간파` vs `속임수` 성공률 +10%, 간파 판정 후 0으로 초기화 |
| 봉인 방해 기준 | 봉인은 단일 턴 행동이다. 방해 단계 2 이상이면 실패, 0-1이면 성공 |
| `수호` vs `수호` | 양쪽 효과 없음 |
| `수호` vs `계약` | 계약자 저주 흔적 +1, 계약자 불완전한 진명 조각 +1 |
| 불완전한 진명 조각 | 2개가 되면 진명 조각 +1로 변환하고 0으로 초기화 |
| `간파` vs `간파` | 양쪽 단서 획득 실패, 양쪽 의심 +1 |
| `간파` vs `속임수` | 기본 성공률 50%, 의심 1당 +10%, 의심 최대 3, 최종 상한 80%. 성공 시 이번 속임수 차단 및 기존 거짓 단서 1개 제거, 실패 시 거짓 단서 +1. 판정 후 의심 0 초기화 |
| 거짓 단서 최대 보유 수 | 3개 |
| `간파` vs `침묵` | 단서 획득 실패, 상대의 다음 행동 후보 2개 공개. 1차 MVP에서 AI는 다음 턴에 후보 중 하나만 선택 |
| `간파` vs `계약` | 계약 실패, 계약자 저주 흔적 +2, 간파자 불완전한 진명 조각 +1 |
| `간파` vs `봉인` | 봉인 방해 단계 +1, 단독으로는 봉인 실패 불가 |
| `속임수` 행 | [[02_Game_Rules/04_상성_규칙]]의 확정된 속임수 행을 따른다. |
| `침묵` 행 | [[02_Game_Rules/04_상성_규칙]]의 확정된 침묵 행을 따른다. |
| `계약` 행 | [[02_Game_Rules/04_상성_규칙]]의 확정된 계약 행을 따른다. |
| `봉인` 행 | [[02_Game_Rules/04_상성_규칙]]의 확정된 봉인 행을 따른다. |
| `간파` vs `침묵` 다음 행동 후보 2개 생성 | 괴이 행동 정책 가중치 적용 후 상위 2개 공개. 동률은 `침묵 > 속임수 > 계약 > 간파 > 저주 > 수호` 순서 |
| 공포 | 1차 MVP에서 생성하거나 적용하지 않음 |
| 금기 위반 | 지속 상태가 아니라 즉시 이벤트로 저장 |
| 보호막 | 최대 1. 다음 저주 피해 2를 막고 소모. 다음 턴 종료까지 미사용이면 사라짐 |
| 동시 승패 우선순위 | 봉인 성공이 있으면 승리 우선. 봉인 성공이 없으면 패배 조건 적용 |
| `거울 속의 손님` 괴이 행동 정책 | [[09_Approved_Contracts/16_거울_속의_손님_괴이_행동_정책]]을 따른다. |
| AI 스토리 시간초과 3회 이상 강한 패턴 | `거울 속의 손님`은 `침묵` 우선, 직전 괴이 행동이 이미 `침묵`이면 `속임수` 우선. 별도 특수 피해 없음. |
| 브라우저 종료/네트워크 끊김 | 즉시 시간초과로 보지 않음. 서버 `deadline_at`까지 유효 제출이 없으면 시간초과 처리 |
| 시간초과 판정 기준 | [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]을 따른다. |

## 백엔드 결정

- 프론트엔드 구현과 LLM generation 구현을 제외한 백엔드/API 구현 전 남은 오너 결정 없음

## Dockerfile 이미지 빌드와 배포 결정

백엔드/API 구현과 로컬 Docker 준비는 진행할 수 있다.

production 배포 구현은 아래 항목이 확정되기 전까지 진행하지 않는다.

결정 타이밍과 구현 게이트는 [[09_Approved_Contracts/24_Dockerfile_이미지_빌드_배포_준비_계약]]을 따른다.

### 지금 확정할 항목

- WSGI/ASGI 방향
- env 변수 이름과 secret 주입 원칙
- health check endpoint 형태
- migration 실행 원칙
- static/media 처리 책임

### 첫 컨테이너 배포 테스트 전 확정할 항목

- image tag 규칙
- DB 연결 방식
- `collectstatic` 실행 여부
- migration 실행 방식
- health check 실패 기준
- 로그 출력 기준

### production 공개 전 확정할 항목

- 배포 대상 환경
- image registry
- reverse proxy
- TLS/domain
- CI/CD 또는 수동 배포 절차
- rollback 방식
- 운영 secret 관리
- backup/restore
- monitoring/log retention

## RAG 결정

- 프론트엔드 구현과 LLM generation 구현을 제외한 RAG 구현 전 남은 오너 결정 없음

LLM generation log와 retrieval log 연결 방식은 LLM generation 구현 담당 범위에서 별도 확정한다.

## 확정된 API/Auth/프론트 기술 결정

| 결정 | 확정값 |
|---|---|
| API URL prefix | `/api/v1` |
| API 응답 형태 | 성공 `{ data, meta }`, 실패 `{ error, meta }` |
| access token 전달 | HttpOnly cookie |
| refresh token 전달 | HttpOnly cookie |
| CSRF 적용 범위 | 모든 state-changing endpoint |
| CSRF token endpoint | `GET /api/v1/auth/csrf` |
| CSRF header | `X-CSRFToken` |
| CSRF rotation | 로그인 시 rotation, refresh 시 유지, logout 후 새 token 필요 |
| CSRF/CORS origin | 명시 allowlist만 허용 |
| refresh token family id | 로그인 성공 시 UUIDv4 |
| refresh token jti | refresh token 발급마다 UUIDv4 |
| refresh token 저장 | 원문 저장 금지, 서버 secret 기반 HMAC-SHA256 hash 저장 |
| refresh token reuse error code | `REFRESH_TOKEN_REUSED` |
| refresh token reuse 처리 | 해당 family 전체 revoke, cookie 제거, security event log 저장 |
| refresh 동시성 | DB transaction + row lock |
| refresh grace window | 없음 |
| access cookie path | `/api/v1` |
| refresh cookie path | `/api/v1/auth/refresh` |
| 프론트 스택 | React + TypeScript + Vite |
| 프론트 라우팅 | React Router |
| 프론트 스타일 | CSS Modules |
| 프론트 API client | `fetch` 기반 wrapper |
| 프론트 상태 관리 | React local state와 Context, 화면/feature 단위 API hook |
| 프론트 route slug | `mirror-guest` |
| 서버 `case_id` | `mirror_guest` |
| 요청 중복 방지 | `client_request_id`, `client_nonce` UUID 문자열 |
| API 상세 request/response schema | [[09_Approved_Contracts/22_API_상세_Schema_계약]]과 `api-spec/pilot-mvp-api.official.jsonc`를 따른다. |

세부 기준은 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]], [[09_Approved_Contracts/20_Django_Auth_보안_계약]], [[09_Approved_Contracts/22_API_상세_Schema_계약]]을 따른다.

## 확정된 백엔드/RAG/AI Profile 결정

| 결정 | 확정값 |
|---|---|
| Django user model | `accounts.User` custom user model |
| User base class | `AbstractBaseUser + PermissionsMixin` |
| 로그인 식별자 | email |
| nickname 저장 | `profiles.Profile` |
| AI participant | `participant_type = human/apparition`, `user_id` nullable, `apparition_id` nullable |
| JSONField 사용 | 결과 스냅샷, 로그 스냅샷, 룰/정책 스냅샷, 작은 정책 데이터에 제한 |
| JSONField schema | 모든 payload에 `schema_version`, Python `jsonschema` 검증 |
| 로컬 Docker Compose | Django API + PostgreSQL + `pgvector` |
| 로컬 Docker Compose 제외 | Redis, WebSocket worker, LLM provider emulator, KAG 전용 저장소 |
| local/dev Secure cookie | `Secure=false` 허용 |
| production Secure cookie | `Secure=true` 필수 |
| SameSite | `Lax` |
| RAG 포함 범위 | `retrieval` 앱, 문서/chunk/embedding/search/query log 구조 |
| RAG 검색 대상 | 승인본 계약, `거울 속의 손님`, 승인된 게임 룰 문서 |
| RAG chunking | 500-900자, 문단 경계 우선, overlap 최대 100자 |
| RAG vector DB | PostgreSQL + `pgvector` |
| RAG embedding model | env/config 주입, 기본 추천값 `text-embedding-3-small` |
| RAG 검색 기본값 | `top_k=6`, `score_threshold=0.72` |
| RAG query log | query, caller, document_id, chunk_id, score, threshold, top_k, created_at 저장 |
| AI Profile 저장 시점 | 턴 resolve 시 행동 이벤트 저장 |
| AI Profile 계산 시점 | 각 턴 resolve 직후 계산, 매치 종료 시 최종 재계산 |
| 0 분모 기본값 | `0.0` |
| 개인정보 삭제 기본 정책 | 행동 이벤트와 스타일 스냅샷 삭제 |
| PvP 모드 | 없음 |
| Match 구조 | human player와 apparition 참가자 기준의 AI 스토리 매치 구조 |

세부 기준은 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]을 따른다.

## 프론트엔드 결정

- 결투 화면의 최소 시각 표현 수준
- 모바일 대응 범위
- 정적 이미지, 아이콘, 폰트, 사운드 허용 범위

## AI/LLM 결정

- LLM 실패 시 표시할 정적 결과 문장
- 결과 화면에서 LLM 요약을 어떤 시각 구역에 표시할지 여부

## 후순위 결정

- LLM provider
- 운영 배포 서비스
- 랭크 점수 공식
