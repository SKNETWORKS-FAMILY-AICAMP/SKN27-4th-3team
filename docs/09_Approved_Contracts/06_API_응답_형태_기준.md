---
title: "API 응답 형태 기준"
status: "approved"
type: "approved-api-response-envelope-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# API 응답 형태 기준

이 문서는 API 응답 envelope에 대한 승인된 기준이다.

## 결정

모든 API 응답은 성공 시 `{ data, meta }`, 실패 시 `{ error, meta }` 형태로 감싼다.

## 성공 응답

```json
{
  "data": {},
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

## 실패 응답

```json
{
  "error": {
    "code": "MATCH_NOT_FOUND",
    "message": "Match was not found.",
    "details": {}
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

## 적용 제약

- 성공 응답 payload는 `data` 아래에 둔다.
- 요청 추적, 서버 시간, pagination 등 보조 정보는 `meta` 아래에 둔다.
- 실패 응답은 `error.code`, `error.message`, `error.details`를 사용한다.
- 프론트는 사용자 표시 문구를 `error.code` 기준으로 매핑할 수 있다.
- endpoint마다 응답 형태를 임의로 바꾸지 않는다.

## request_id 생성 및 전파 정책

`meta.request_id`는 백엔드 서버가 매 요청마다 생성한다.

- 형식은 `req_` + UUIDv4 hex 문자열이다.
- 클라이언트가 보낸 `X-Request-ID`는 1차 MVP에서 사용하지 않는다.
- Django middleware가 요청 진입 시점에 `request.request_id`를 설정한다.
- request id middleware는 `SecurityMiddleware`보다 앞에서 실행한다.
- 모든 API envelope는 `request.request_id`를 사용한다.
- middleware 밖에서 생성된 예외 상황만 fallback으로 새 `request_id`를 만든다.
- HTTP 응답 header에는 `X-Request-ID`를 포함한다.
- `request_id`는 `client_request_id`, `client_nonce`와 혼용하지 않는다.

## 미구현 service 응답 정책

공식 endpoint는 라우팅 상태를 유지한다.

실제 service가 아직 구현되지 않은 endpoint는 HTTP `501`과 실패 envelope를 반환한다.

```json
{
  "error": {
    "code": "SERVICE_NOT_IMPLEMENTED",
    "message": "Service is not implemented yet.",
    "details": {
      "service": "auth.login"
    }
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-04T00:00:00Z"
  }
}
```

- `SERVICE_NOT_IMPLEMENTED`는 단계적 구현 중인 runtime scaffold 상태를 나타낸다.
- `details.service`에는 view class명이 아니라 안정적인 service key를 넣는다.
- 예시 service key는 `auth.login`, `story.cases.list`, `matches.detail`, `profile.me` 형식이다.
- mock 성공 응답을 만들지 않는다.
- 실제 service가 구현된 endpoint는 정상 success envelope를 반환한다.
- `GET /api/v1/auth/csrf`처럼 DB/JWT service가 필요 없는 endpoint는 실제 success envelope로 구현할 수 있다.
