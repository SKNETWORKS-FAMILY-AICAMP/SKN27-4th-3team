---
title: "Django Auth 보안 계약"
status: "approved"
type: "approved-django-auth-security-contract"
source: "[[03_Backend/02_인증과_토큰]], [[09_Approved_Contracts/10_Auth_토큰_전달_기준]], [[09_Approved_Contracts/11_CSRF_정책_기준]], [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]"
created: "2026-06-02"
updated: "2026-06-04"
---

# Django Auth 보안 계약

이 문서는 1차 MVP Django 인증/세션/CSRF 보안 기준이다.

보안은 구현 편의보다 우선한다.

## 결정

일반 웹 서비스 기준의 보수적 Auth 정책을 사용한다.

## 적용 범위

- 로그인
- 로그아웃
- token refresh
- session 확인
- CSRF token 발급
- 모든 state-changing endpoint
- AI 스토리 match 접근 권한과 제출 보안

## Token 전달

| 항목 | 확정값 |
|---|---|
| access token | JWT, 15분, HttpOnly cookie |
| refresh token | JWT, 14일, HttpOnly cookie |
| refresh token claim | `jti`, `family_id` 포함 |
| token 저장 | localStorage/sessionStorage 저장 금지 |
| Authorization header | 프론트에서 Bearer token 직접 구성 금지 |
| SameSite | `Lax` |
| local/dev Secure cookie | `Secure=false` 허용 |
| production Secure cookie | `Secure=true` 필수 |

## Cookie Path

| cookie | path |
|---|---|
| access token cookie | `/api/v1` |
| refresh token cookie | `/api/v1/auth/refresh` |

logout은 refresh cookie path까지 명시해서 cookie를 제거한다.

## Refresh Token Family

| 항목 | 확정값 |
|---|---|
| `family_id` 생성 | 로그인 성공 시 UUIDv4 |
| `jti` 생성 | refresh token 발급마다 UUIDv4 |
| 원문 저장 | 금지 |
| 저장 hash | 서버 secret 기반 HMAC-SHA256 |
| refresh 성공 | 기존 token `rotated`, 새 refresh token 발급 |
| reuse 감지 | `rotated` 또는 `revoked` token 재사용 시 감지 |
| reuse 처리 | 해당 `family_id` 전체 revoke |
| reuse error code | `REFRESH_TOKEN_REUSED` |
| 동시성 제어 | DB transaction + row lock |
| grace window | 없음 |

## Refresh Token 저장 필드

refresh token 저장 모델은 최소 아래 필드를 가진다.

| 필드 | 설명 |
|---|---|
| `id` | 내부 ID |
| `user_id` | token 소유자 |
| `jti` | refresh token 고유 식별자 |
| `family_id` | 로그인 session 계열 ID |
| `token_hash` | HMAC-SHA256 hash |
| `status` | `active`, `rotated`, `revoked`, `reused` |
| `issued_at` | 발급 시각 |
| `expires_at` | 만료 시각 |
| `rotated_at` | rotation 시각 |
| `revoked_at` | 폐기 시각 |
| `reused_at` | 재사용 감지 시각 |
| `replaced_by_jti` | rotation 후 새 token jti |

## Reuse 감지 처리

이미 `rotated`, `revoked`, `reused` 상태인 refresh token이 제출되면 아래 순서로 처리한다.

1. refresh 요청을 실패 처리한다.
2. 해당 `family_id`의 모든 refresh token을 revoke한다.
3. access token cookie와 refresh token cookie를 제거한다.
4. security event log를 저장한다.
5. `REFRESH_TOKEN_REUSED` error code로 응답한다.

## CSRF 기준

| 항목 | 확정값 |
|---|---|
| 적용 범위 | 모든 state-changing endpoint |
| endpoint | `GET /api/v1/auth/csrf` |
| header | `X-CSRFToken` |
| 로그인 시점 | CSRF token rotation |
| refresh 시점 | CSRF token 유지 |
| logout 이후 | 새 `GET /api/v1/auth/csrf` 필요 |
| 프론트 저장 | memory only |
| localStorage/sessionStorage 저장 | 금지 |

Django CSRF middleware를 사용한다.

`CSRF_TRUSTED_ORIGINS`는 명시 allowlist만 허용한다.

CORS origin도 명시 allowlist만 허용한다.

## Security Event Log

아래 이벤트는 최소 security event log로 남긴다.

- refresh token reuse 감지
- refresh token family revoke
- CSRF 실패
- 로그인 실패 반복
- 권한 없는 match 접근 시도
- participant가 아닌 사용자의 행동 제출 시도

## Match 보안 제약

AI 스토리 match에도 아래 기준을 적용한다.

- match 접근 권한은 participant membership으로 검증한다.
- 행동 제출은 participant 기준으로 저장한다.
- `client_nonce`는 participant + turn 범위에서 중복 제출을 막는다.
- 단일 `match.user_id` 소유권으로 접근 권한을 판단하지 않는다.
- weak session 또는 임시 token 저장 방식은 금지한다.

## 구현 금지선

- `csrf_exempt` 사용 금지
- CSRF middleware 비활성화 금지
- dev 환경에서 CSRF 흐름 비활성화 금지
- CORS 전체 허용 금지
- `CSRF_TRUSTED_ORIGINS` 전체 허용 금지
- localStorage/sessionStorage token 저장 금지
- refresh token 원문 저장 금지
- refresh token reuse grace window 금지
- refresh 성공 시 기존 token을 active로 남기는 구현 금지
- 인증/권한 실패를 일반 validation error로 뭉개는 처리 금지

## Django 공식 기준 참고

Django CSRF 문서는 unsafe method 보호, Origin/Trusted Origins 검증, 로그인 시 CSRF secret 변경을 설명한다.

Django Security 문서는 CSRF 보호를 적절히 사용해야 하며, 임의 비활성화는 신중해야 한다는 기준을 둔다.

- https://docs.djangoproject.com/en/5.2/ref/csrf/
- https://docs.djangoproject.com/en/5.2/topics/security/

## 아직 별도 결정할 항목

프론트엔드 구현과 LLM generation 구현을 제외한 백엔드/API 구현 전 남은 오너 결정은 없다.

브라우저 종료/네트워크 끊김과 시간초과 판정 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]에서 확정됐다.

API official 상세 request/response schema는 [[09_Approved_Contracts/22_API_상세_Schema_계약]]에서 확정됐다.
