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
