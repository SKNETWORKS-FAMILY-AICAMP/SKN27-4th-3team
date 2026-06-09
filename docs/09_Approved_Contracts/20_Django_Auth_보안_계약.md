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

## JWT 발급 Runtime

1차 MVP Auth runtime은 A안으로 확정한다.

| 항목 | 확정값 |
|---|---|
| JWT signing secret | `DJANGO_SECRET_KEY`로 주입되는 Django `settings.SECRET_KEY` |
| JWT algorithm | `HS256` |
| access token claim | `token_type=access`, `sub=user_id`, `iat`, `exp` |
| refresh token claim | `token_type=refresh`, `sub=user_id`, `jti`, `family_id`, `iat`, `exp` |
| token body 노출 | 금지. access/refresh token은 response body에 포함하지 않는다. |

`sub`는 user id를 문자열로 직렬화한다.

access token에는 email, nickname, staff/superuser, permission, profile, style 지표를 넣지 않는다.

refresh token에는 원문 token 값, token hash, password, cookie 값을 넣지 않는다.

## Cookie Path

| cookie | path |
|---|---|
| access token cookie | `/api/v1` |
| refresh token cookie | `/api/v1/auth` |

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

refresh rotation service는 `transaction.atomic()` 안에서 제출된 refresh token row를 `select_for_update()`로 잠근다.

제출된 refresh token이 `active`이면 기존 token은 `rotated`가 되고 같은 `family_id`의 새 refresh token을 발급한다.

제출된 refresh token이 `rotated`, `revoked`, `reused`이면 reuse로 판단하고 해당 `family_id` 전체를 revoke한다. grace window는 두지 않는다.

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

### Security Event 저장 정책

1차 MVP Auth runtime은 A안으로 아래 필드를 사용한다.

| 필드 | 확정값 |
|---|---|
| `event_type` | 승인된 security event type |
| `user_id` | nullable user id. 비인증/unknown actor는 `null` |
| `request_id` | nullable server-generated request id |
| `metadata` | JSON object, 기본값 `{}` |
| `created_at` | 생성 시각 |

`metadata`에는 raw token, token hash, password, cookie 값, CSRF token 원문을 저장하지 않는다.

`SecurityEvent`는 actor FK를 사용하지 않는다. user 삭제 생명주기와 event 보존 정책이 별도 확정되지 않았으므로 `user_id` 값만 저장한다.

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

## Logout refresh family revoke 정책

logout에서 current refresh token family를 식별하는 방식은 refresh cookie 기준으로 확정한다.

refresh token cookie path는 `/api/v1/auth`이므로 브라우저는 `/api/v1/auth/logout` 요청에 refresh token cookie를 자동 전송한다.

A안 access token claim에는 `family_id`가 없으므로 access token만으로 refresh token family를 식별하지 않는다.

확정 정책은 아래와 같다.

- 정상 active refresh cookie가 있으면 해당 refresh token family 전체를 revoke한다.
- family revoke 시 `refresh token family revoke` security event를 기록한다.
- `REFRESH_TOKEN_REUSED` 상태가 감지되면 기존 refresh 정책대로 family 전체 revoke, security event 기록, `REFRESH_TOKEN_REUSED` 오류 응답을 유지한다.
- refresh cookie가 없고 access token만 유효하면 family revoke는 수행하지 않고 access/refresh cookie 삭제 후 성공 응답을 반환한다.
- refresh/access가 모두 없거나 모두 유효하지 않으면 access/refresh cookie 삭제 후 `AUTH_REQUIRED` 또는 `SESSION_EXPIRED` 오류 envelope를 반환한다.
- logout 성공과 logout 오류 응답 모두 브라우저의 access/refresh cookie 삭제를 지시한다.
- logout 이후 state-changing 요청은 새 `GET /api/v1/auth/csrf` 흐름을 거친다.

## Password 및 Login 실패 제한 정책

비밀번호와 로그인 실패 제한은 B안 보수적 균형안으로 확정한다.

### Password 정책

| 항목 | 확정값 |
|---|---|
| 최소 길이 | 10자 |
| 최대 길이 | 128자 |
| common password | 차단 |
| 숫자-only password | 차단 |
| 사용자 정보 유사 password | email, nickname과 너무 유사하면 차단 |
| 실패 응답 | `VALIDATION_ERROR` |

회원가입 service는 user 생성 전에 password 정책을 검증한다.

### Login 실패 rate limit 정책

| 항목 | 확정값 |
|---|---|
| 식별 기준 | 정규화된 email + 서버 관측 `REMOTE_ADDR` |
| 실패 집계 창 | 10분 |
| 실패 허용 횟수 | 5회 미만 |
| 차단 조건 | 10분 내 5회 실패 |
| 차단 시간 | 15분 |
| 차단 응답 | HTTP `429`, error code `LOGIN_RATE_LIMITED` |
| 성공 처리 | 로그인 성공 시 같은 email + IP 실패 카운트 초기화 |

계정 존재 여부가 드러나지 않도록 일반 로그인 실패는 기존 `INVALID_CREDENTIALS` 응답을 유지한다.

trusted proxy 정책이 아직 확정되지 않았으므로 `X-Forwarded-For`는 로그인 실패 제한 기준으로 사용하지 않는다.

브라우저 종료/네트워크 끊김과 시간초과 판정 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]에서 확정됐다.

API official 상세 request/response schema는 [[09_Approved_Contracts/22_API_상세_Schema_계약]]에서 확정됐다.
