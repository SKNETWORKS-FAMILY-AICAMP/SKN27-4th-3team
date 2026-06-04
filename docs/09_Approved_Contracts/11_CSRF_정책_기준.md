---
title: "CSRF 정책 기준"
status: "approved"
type: "approved-csrf-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# CSRF 정책 기준

이 문서는 CSRF 적용 범위에 대한 승인된 기준이다.

## 결정

모든 state-changing endpoint에 CSRF를 적용한다.

## 선택 이유

- access token과 refresh token을 모두 HttpOnly cookie로 전달하기로 했으므로 cookie 기반 요청 보호가 중요하다.
- 본사 평가에서 상품성뿐 아니라 시스템 완성도와 보안 설계 일관성이 중요하다.
- MVP라도 인증/권한/상태 변경 요청의 보안 기준을 보수적으로 잡는다.

## 적용 범위

아래처럼 서버 상태를 바꾸는 요청은 CSRF token을 요구한다.

- `POST`
- `PATCH`
- `PUT`
- `DELETE`

예시:

- 로그인
- 로그아웃
- token refresh
- AI story match 시작
- 행동 제출
- 프로필 수정
- 기타 상태 변경 API

## 프론트 영향

- 프론트 API client는 state-changing request에 CSRF header를 자동으로 포함한다.
- CSRF token은 `GET /api/v1/auth/csrf`로 획득한다.
- CSRF header 이름은 `X-CSRFToken`이다.
- CSRF 실패 응답을 인증 실패와 구분해서 처리한다.
- CSRF token은 memory에만 보관한다.
- localStorage/sessionStorage에 CSRF token을 저장하지 않는다.

## 백엔드 영향

- 백엔드는 CSRF 실패와 인증 실패를 구분된 error code로 응답한다.
- SameSite cookie 정책은 CSRF token의 대체물이 아니라 보조 방어선으로 취급한다.
- 로컬 개발 환경에서도 CSRF 흐름을 비활성화하지 않고, 개발용 token 발급 흐름을 제공한다.
- 로그인 시 CSRF token을 rotation한다.
- refresh 시 CSRF token은 유지한다.
- logout 후에는 새 `GET /api/v1/auth/csrf`가 필요하다.
- `CSRF_TRUSTED_ORIGINS`는 명시 allowlist만 허용한다.
- CORS origin도 명시 allowlist만 허용한다.

## 확정된 오류 기준

| code | 의미 |
|---|---|
| `CSRF_TOKEN_MISSING` | CSRF token 없음 |
| `CSRF_TOKEN_INVALID` | CSRF token invalid |

로그인 전 CSRF token도 `GET /api/v1/auth/csrf`로 받는다.

## 구현 금지선

- `csrf_exempt` 사용 금지
- CSRF middleware 비활성화 금지
- dev 환경에서 CSRF 흐름 비활성화 금지
- CORS 전체 허용 금지
- `CSRF_TRUSTED_ORIGINS` 전체 허용 금지

상세 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.
