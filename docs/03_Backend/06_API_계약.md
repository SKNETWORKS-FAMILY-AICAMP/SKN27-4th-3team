---
title: "API 계약"
status: "approved"
type: "backend-detail"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# API 계약

이 문서는 MVP HTTP API endpoint, request, response를 확정하는 문서다.

## 확정된 기본 계약

| 항목 | 확정값 |
|---|---|
| API prefix | `/api/v1` |
| 성공 응답 | `{ data, meta }` |
| 실패 응답 | `{ error, meta }` |
| access token 전달 | HttpOnly cookie |
| refresh token 전달 | HttpOnly cookie |
| CSRF endpoint | `GET /api/v1/auth/csrf` |
| CSRF header | `X-CSRFToken` |
| CSRF rotation | login 성공 시 rotation, refresh 시 유지, logout 이후 재발급 필요 |
| refresh token family | login 성공 시 `family_id` UUIDv4, token 발급마다 `jti` UUIDv4 |
| refresh token reuse error | `REFRESH_TOKEN_REUSED` |
| access cookie path | `/api/v1` |
| refresh cookie path | `/api/v1/auth/refresh` |
| 매치 시작 중복 방지 | `client_request_id` |
| 행동 제출 중복 방지 | `client_nonce` |
| AI 스토리 시간초과 판정 | 서버 `deadline_at` 기준 |
| 브라우저 종료/네트워크 끊김 | 즉시 시간초과로 보지 않음 |

## MVP API endpoint

| method | path | 목적 |
|---|---|---|
| `GET` | `/api/v1/auth/csrf` | CSRF token 발급 |
| `POST` | `/api/v1/auth/signup` | 회원가입 |
| `POST` | `/api/v1/auth/login` | 로그인 |
| `POST` | `/api/v1/auth/logout` | 로그아웃 |
| `POST` | `/api/v1/auth/refresh` | token refresh |
| `GET` | `/api/v1/auth/me` | 현재 사용자/session 확인 |
| `GET` | `/api/v1/story/cases` | AI 사건 목록 |
| `GET` | `/api/v1/story/cases/{case_id}/briefing` | 브리핑 조회 |
| `POST` | `/api/v1/story/cases/{case_id}/matches` | AI 스토리 매치 시작 |
| `GET` | `/api/v1/matches/{match_id}` | 현재 매치 상태 조회 |
| `POST` | `/api/v1/matches/{match_id}/turns` | 행동 제출 |
| `GET` | `/api/v1/matches/{match_id}/result` | 결과 조회 |
| `GET` | `/api/v1/profile/me` | 내 프로필과 요약 조회 |

## 상세 schema

request/response schema와 API official JSONC 생성본의 상세 필드는 아래 파일을 따른다.

| 파일 | 상태 |
|---|---|
| `api-spec/pilot-mvp-api.official.jsonc` | approved |
| `api-spec/pilot-mvp-api.official.json` | approved |

API 명세 관리는 [[09_Approved_Contracts/05_API_명세_관리_기준]]을 따른다.

응답 envelope는 [[09_Approved_Contracts/06_API_응답_형태_기준]]을 따른다.

프론트 연결 기준은 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]을 따른다.

Django Auth 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

AI 스토리 시간초과 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]을 따른다.

API 상세 schema 기준은 [[09_Approved_Contracts/22_API_상세_Schema_계약]]을 따른다.
