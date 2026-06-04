---
title: "Auth 토큰 전달 기준"
status: "approved"
type: "approved-auth-token-delivery-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# Auth 토큰 전달 기준

이 문서는 access token과 refresh token 전달 방식에 대한 승인된 기준이다.

## 결정

access token과 refresh token을 모두 HttpOnly cookie로 전달한다.

## 적용 제약

- 프론트는 access token과 refresh token을 직접 저장하거나 읽지 않는다.
- localStorage/sessionStorage에 token을 저장하지 않는다.
- 인증 요청은 cookie 기반으로 처리한다.
- cookie 기반 인증이므로 CSRF 정책을 별도로 적용한다.
- 로컬 개발 환경에서는 `Secure=false`를 허용한다.
- production 환경에서는 `Secure=true`를 필수로 한다.
- SameSite는 `Lax`를 사용한다.

## 프론트 영향

- 프론트 API client는 `credentials: "include"` 또는 동등한 설정을 사용해야 한다.
- 프론트는 Authorization header에 Bearer token을 직접 붙이지 않는다.
- 로그인 성공 여부는 응답 body의 user/session 상태와 후속 `/me` 조회로 판단한다.
- 401 응답을 받으면 refresh endpoint 또는 session 확인 흐름을 따른다.
- refresh 요청은 single-flight로 처리한다.

## 백엔드 영향

- 로그인 시 access token cookie와 refresh token cookie를 설정한다.
- refresh 시 두 cookie의 유효성과 회전을 처리한다.
- logout 시 관련 cookie를 제거하고 refresh token family 정책을 적용한다.
- SameSite, Secure, HttpOnly, Path, Max-Age 정책을 명확히 정한다.
- access token cookie path는 `/api/v1`이다.
- refresh token cookie path는 `/api/v1/auth/refresh`다.
- refresh token family id는 로그인 성공 시 UUIDv4로 생성한다.
- refresh token 재사용 감지 시 `REFRESH_TOKEN_REUSED`로 응답한다.
- 재사용 감지 시 해당 family 전체를 revoke한다.
- refresh token 원문은 저장하지 않는다.

## 구현 금지선

- localStorage/sessionStorage token 저장 금지
- Authorization header 직접 구성 금지
- refresh token 원문 저장 금지
- refresh token reuse grace window 금지
- refresh 성공 시 기존 token을 active로 남기는 구현 금지

CSRF endpoint와 header는 [[09_Approved_Contracts/11_CSRF_정책_기준]]과 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]을 따른다.

상세 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.
