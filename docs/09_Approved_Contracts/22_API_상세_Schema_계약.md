---
title: "API 상세 Schema 계약"
status: "approved"
type: "approved-api-detail-schema-contract"
source: "[[03_Backend/06_API_계약]], [[09_Approved_Contracts/05_API_명세_관리_기준]], [[09_Approved_Contracts/06_API_응답_형태_기준]], [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# API 상세 Schema 계약

이 문서는 1차 MVP API request/response schema에 대한 승인 기준이다.

## 결정

A안인 구현 직전용 최소 완성 schema를 사용한다.

OpenAPI급 전체 세부 타입 생성까지 확장하지 않고, 프론트와 백엔드가 구현 착수에 사용할 수 있는 endpoint별 request, response, error code를 확정한다.

## 공식 파일

| 파일 | 역할 |
|---|---|
| `api-spec/pilot-mvp-api.official.jsonc` | 사람이 읽고 관리하는 공식 API schema 원본 |
| `api-spec/pilot-mvp-api.official.json` | 도구가 읽는 strict JSON 생성본 |

두 파일의 `schema_status`는 `approved`다.

## 적용 범위

- 승인된 MVP endpoint 13개
- `{ data, meta }` / `{ error, meta }` envelope
- 공통 schema: `User`, `ProfileSummary`, `StyleSummary`, `StoryCaseSummary`, `StoryCaseBriefing`, `MatchState`, `TurnResult`, `MatchResult`
- endpoint별 request body, path params, response data, error code
- Auth/CSRF/cookie/refresh token 보안 기준
- AI 스토리 시간초과와 `TURN_DEADLINE_EXPIRED`
- `meta.request_id`는 서버 생성 전용 추적 ID로 사용한다.

## 구현 금지선

- `api-spec/pilot-mvp-api.jsonc`의 오래된 draft 경로를 구현 기준으로 사용하지 않는다.
- `/auth/register`, `/matches/ai-story`, `/matches/{match_id}/turns/{turn_id}/actions`를 공식 endpoint로 사용하지 않는다.
- access token 또는 refresh token을 response body schema에 포함하지 않는다.
- 프론트가 Authorization Bearer token을 직접 구성하도록 schema를 바꾸지 않는다.
- endpoint별 envelope를 임의로 바꾸지 않는다.
- `client_request_id` 또는 `client_nonce`를 `meta.request_id`로 재사용하지 않는다.

## 남은 오너 결정

프론트엔드 구현과 LLM generation 구현을 제외한 백엔드/API 구현 전 남은 오너 결정은 없다.
