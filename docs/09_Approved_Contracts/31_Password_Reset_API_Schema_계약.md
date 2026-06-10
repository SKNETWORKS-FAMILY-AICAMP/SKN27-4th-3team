---
title: "Password Reset API Schema 계약"
status: "approved"
type: "approved-password-reset-api-schema-contract"
source: "2026-06-10 user decision: B안 이메일 어댑터 기반"
created: "2026-06-10"
updated: "2026-06-10"
---

# Password Reset API Schema 계약

이 문서는 MVP 확장 1차 범위 중 password reset backend endpoint의 API/schema와 보안 기준을 확정한다.

기존 Auth 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

## 결정

B안인 이메일 어댑터 기반 password reset을 사용한다.

local/dev에서는 Django console email backend로 reset link를 출력한다.

production에서는 SMTP 또는 외부 email provider 환경 설정이 없으면 password reset 발송을 수행하지 않는다.

## 적용 범위

포함한다.

- password reset 요청 endpoint
- password reset 확인 endpoint
- reset token 저장 구조
- token TTL과 1회성 사용 정책
- 사용자 존재 여부 미노출 응답
- email + IP 기준 남용 방지
- SecurityEvent 기록 기준
- local/dev console email 동작

제외한다.

- 프론트엔드 화면 구현
- 실제 production email provider 계정 발급
- SMS, OTP, magic link 로그인
- 관리자 강제 비밀번호 변경
- 로그인된 사용자의 비밀번호 변경 화면

## Endpoint

### Password reset request

```text
POST /api/v1/auth/password-reset/request
```

| 항목 | 기준 |
|---|---|
| auth_required | `false` |
| csrf_required | `true` |
| success_status | `200` |
| side_effect | 존재하는 active 사용자에게만 reset email 발송 시도 |

요청 body는 아래와 같다.

```json
{
  "email": "string:email"
}
```

성공 응답 data는 아래와 같다.

```json
{
  "accepted": true
}
```

사용자 존재 여부와 active 여부는 응답으로 노출하지 않는다.

존재하지 않는 email, 비활성 사용자, email 발송 불가 상태도 계정 존재 여부를 추론할 수 없도록 동일한 성공 형태 또는 rate limit 오류만 반환한다.

### Password reset confirm

```text
POST /api/v1/auth/password-reset/confirm
```

| 항목 | 기준 |
|---|---|
| auth_required | `false` |
| csrf_required | `true` |
| success_status | `200` |
| side_effect | 유효한 token이면 사용자 password 변경, token 사용 처리, 기존 refresh token family revoke |

요청 body는 아래와 같다.

```json
{
  "token": "string",
  "new_password": "string"
}
```

성공 응답 data는 아래와 같다.

```json
{
  "password_reset": true
}
```

## Error code

아래 error code를 official API schema에 추가한다.

| code | 사용 지점 |
|---|---|
| `PASSWORD_RESET_TOKEN_INVALID` | token이 존재하지 않거나 형식이 잘못된 경우 |
| `PASSWORD_RESET_TOKEN_EXPIRED` | token TTL이 지난 경우 |
| `PASSWORD_RESET_TOKEN_USED` | 이미 사용된 token을 다시 제출한 경우 |
| `PASSWORD_RESET_DELIVERY_UNAVAILABLE` | production email provider 설정이 없어 발송할 수 없는 경우 |

공통 error code는 기존 기준을 따른다.

- `CSRF_TOKEN_MISSING`
- `CSRF_TOKEN_INVALID`
- `VALIDATION_ERROR`
- `RATE_LIMITED`

## Token 정책

| 항목 | 확정값 |
|---|---|
| token 생성 | 서버 난수 기반 URL-safe token |
| token 원문 저장 | 금지 |
| 저장 hash | 서버 secret 기반 HMAC-SHA256 |
| TTL | 30분 |
| 사용 횟수 | 1회 |
| 사용 처리 | 성공 시 `used_at` 기록 |
| 만료 token 처리 | password 변경 금지, 만료 오류 반환 |
| 재사용 token 처리 | password 변경 금지, 재사용 오류 반환 |

reset token 원문은 email link에만 포함한다.

DB, 로그, SecurityEvent metadata, API response에는 reset token 원문을 저장하거나 노출하지 않는다.

## 저장 구조

password reset token 저장 모델은 최소 아래 필드를 가진다.

| 필드 | 설명 |
|---|---|
| `id` | 내부 ID |
| `user_id` | reset 대상 사용자 id |
| `token_hash` | HMAC-SHA256 hash |
| `requested_email` | 요청에 사용된 정규화 email |
| `request_ip` | 서버가 관측한 IP |
| `created_at` | 생성 시각 |
| `expires_at` | 만료 시각 |
| `used_at` | 사용 시각, 미사용이면 null |

사용자 삭제 생명주기와 FK 정책은 별도 확정 전까지 기존 Auth 저장 정책과 맞춰 `user_id` 값 필드로 시작한다.

## Password 정책

`new_password`는 기존 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]의 password 정책을 그대로 따른다.

| 항목 | 기준 |
|---|---|
| 최소 길이 | 10자 |
| 최대 길이 | 128자 |
| common password | 차단 |
| 숫자-only password | 차단 |
| 사용자 정보 유사 password | email과 너무 유사하면 차단 |
| 실패 응답 | `VALIDATION_ERROR` |

password reset 성공 시 기존 refresh token family는 모두 revoke한다.

브라우저가 보유한 기존 access/refresh cookie가 있더라도 password reset 성공 응답에서 token을 body로 내려주지 않는다.

## Rate limit

password reset request는 email + 서버 관측 IP 기준으로 제한한다.

| 항목 | 확정값 |
|---|---|
| 식별 기준 | 정규화 email + 서버 관측 `REMOTE_ADDR` |
| 집계 창 | 10분 |
| 허용 횟수 | 3회 미만 |
| 차단 조건 | 10분 내 3회 요청 |
| 차단 시간 | 30분 |
| 차단 응답 | HTTP `429`, error code `RATE_LIMITED` |

trusted proxy 정책이 적용되는 production에서는 기존 trusted proxy allowlist 기준으로 계산된 client IP를 사용한다.

allowlist 없는 `X-Forwarded-*` header를 신뢰하지 않는다.

## Email delivery

password reset link에는 reset token 원문을 포함한다.

link base URL은 환경 변수로 주입한다.

| 환경 | 기준 |
|---|---|
| local/dev | Django console email backend 사용 |
| production | SMTP 또는 외부 email provider 설정 필수 |

production에서 email provider 설정이 없으면 reset token을 생성하거나 응답에 노출하지 않는다.

production delivery unavailable 상황은 SecurityEvent에 기록한다.

## SecurityEvent

아래 이벤트를 기록한다.

| 이벤트 | user_id | metadata 기준 |
|---|---|---|
| password reset requested | 존재하는 사용자면 user id, 아니면 null | `email_hmac`만 저장한다. raw email, raw token 저장 금지 |
| password reset delivery unavailable | null 또는 대상 user id | provider 설정 누락 사유만 저장. secret 저장 금지 |
| password reset succeeded | 대상 user id | token hash, raw token, password 저장 금지 |
| password reset token expired | 대상 user id 또는 null | raw token 저장 금지 |
| password reset token reused | 대상 user id 또는 null | raw token 저장 금지 |
| password reset token invalid | null | raw token 저장 금지 |

`email_hmac`은 정규화 email을 서버 secret 기반 HMAC-SHA256으로 변환한 값이다.

metadata에는 raw email, password, reset token 원문, token hash, email 발송 credential, Authorization header, cookie, CSRF token 원문을 저장하지 않는다.

## API schema 반영 기준

구현 전 official API schema에 아래를 반영한다.

- `auth.password_reset.request` endpoint
- `auth.password_reset.confirm` endpoint
- request/response body schema
- 신규 error code 4개
- endpoint count 변경

strict JSON 생성본은 [[09_Approved_Contracts/30_MVP_확장_1차_범위_계약]]의 기준처럼 PowerShell `ConvertFrom-Json`과 Python `json.load`를 모두 통과해야 한다.

## 구현 금지선

- reset token 원문을 DB에 저장하지 않는다.
- reset token 원문을 API response body에 내려주지 않는다.
- 존재하지 않는 email에 대해 다른 success body를 반환하지 않는다.
- reset request에서 계정 존재 여부를 알려주는 error를 반환하지 않는다.
- production에서 email provider 없이 token을 생성해 응답에 노출하지 않는다.
- password reset 성공 후 access/refresh token을 body에 내려주지 않는다.
- CSRF를 비활성화하지 않는다.
- localStorage/sessionStorage token 저장 흐름을 추가하지 않는다.
