---
title: "프론트 API 연결 계약 초안"
status: "needs-decision"
type: "frontend-api-contract-draft"
source: "[[09_Approved_Contracts/05_API_명세_관리_기준]], [[09_Approved_Contracts/06_API_응답_형태_기준]], [[09_Approved_Contracts/10_Auth_토큰_전달_기준]], [[09_Approved_Contracts/11_CSRF_정책_기준]], [[09_Approved_Contracts/12_거울_속의_손님_금기_정의]], [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# 프론트 API 연결 계약 초안

이 문서는 프론트엔드가 MVP 화면을 구현하기 위해 필요한 API 연결 계약 초안이다.

현재 상태는 `needs-decision`이다. 상세 request/response schema, field name, HTTP status 매핑은 오너 승인 전까지 확정 계약으로 사용하지 않는다.

API prefix, 프론트 MVP endpoint 목록, 인증/CSRF 연결 기준, 요청 ID 기준, 공통 error code 기준은 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]을 따른다.

## 승인된 상위 기준

아래 기준은 승인본을 따른다.

- API 응답은 성공 시 `{ data, meta }`, 실패 시 `{ error, meta }` 형태를 사용한다.
- access token과 refresh token은 모두 HttpOnly cookie로 전달한다.
- 프론트는 token을 localStorage/sessionStorage에 저장하지 않는다.
- 프론트 API client는 cookie 기반 요청을 위해 `credentials: "include"` 또는 동등한 설정을 사용한다.
- 모든 state-changing endpoint에는 CSRF를 적용한다.
- `거울 속의 손님`의 같은 질문 반복은 `info_target_key` 반복 기반으로 판정한다.
- 정보 행동은 `info_target_key`가 필수다.

## 공통 응답 envelope

성공 응답:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

실패 응답:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message.",
    "details": {}
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

프론트는 사용자 표시 문구를 `error.code` 기준으로 매핑할 수 있다.

## API prefix 후보

API prefix는 아직 확정되지 않았다.

추천 후보:

```text
/api/v1
```

decision_required:

- API prefix 최종값
- frontend dev server와 backend server의 local origin 구성
- CORS/CSRF trusted origin 구성

## 인증 흐름 후보

프론트 인증 흐름 후보:

1. 앱 초기화 시 CSRF token을 확보한다.
2. 로그인/회원가입 같은 state-changing request에 CSRF header를 포함한다.
3. 로그인 성공 시 서버가 HttpOnly access/refresh cookie를 설정한다.
4. 프론트는 token을 읽지 않고 `/auth/me` 또는 동등한 endpoint로 세션 상태를 확인한다.
5. 401 응답을 받으면 refresh 또는 session 확인 흐름을 따른다.
6. refresh 실패 시 로그인 화면으로 보낸다.

decision_required:

- CSRF token 발급 endpoint
- CSRF header 이름
- CSRF token rotation 시점
- access cookie와 refresh cookie의 path 분리 여부
- refresh token family 재사용 감지 시 error code

## 승인된 endpoint 목록

아래 endpoint는 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]에서 승인된 프론트 MVP endpoint 목록이다.

| method | path | 목적 | 상태 |
|---|---|---|---|
| `GET` | `/api/v1/auth/csrf` | CSRF token 발급 | approved |
| `POST` | `/api/v1/auth/signup` | 회원가입 | approved |
| `POST` | `/api/v1/auth/login` | 로그인 | approved |
| `POST` | `/api/v1/auth/logout` | 로그아웃 | approved |
| `POST` | `/api/v1/auth/refresh` | token refresh | approved |
| `GET` | `/api/v1/auth/me` | 현재 사용자/session 확인 | approved |
| `GET` | `/api/v1/story/cases` | AI 사건 목록 | approved |
| `GET` | `/api/v1/story/cases/{case_id}/briefing` | 브리핑 조회 | approved |
| `POST` | `/api/v1/story/cases/{case_id}/matches` | AI 스토리 매치 시작 | approved |
| `GET` | `/api/v1/matches/{match_id}` | 현재 매치 상태 조회 | approved |
| `POST` | `/api/v1/matches/{match_id}/turns` | 행동 제출 | approved |
| `GET` | `/api/v1/matches/{match_id}/result` | 결과 조회 | approved |
| `GET` | `/api/v1/profile/me` | 내 프로필과 요약 조회 | approved |

## 프론트 주요 요청 후보

### 로그인

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

응답 후보:

```json
{
  "data": {
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "nickname": "nickname"
    }
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

### 매치 시작

```json
{
  "client_request_id": "uuid-generated-by-frontend"
}
```

응답 후보:

```json
{
  "data": {
    "match_id": "match_id",
    "case_id": "mirror_guest",
    "status": "in_progress",
    "current_turn": 1
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

decision_required:

- `client_request_id` 필수 여부
- 중복 매치 시작 요청 처리 방식
- `case_id` 형식

### 행동 제출

```json
{
  "action_code": "insight",
  "info_target_key": "mirror_back",
  "client_nonce": "uuid-generated-by-frontend"
}
```

승인된 정보 대상:

| info_target_key | 의미 |
|---|---|
| `mirror_surface` | 거울 표면 |
| `mirror_back` | 깨진 거울 뒷면 |
| `missing_child_voice` | 사라진 아이의 목소리 |
| `forgotten_room` | 잊어버린 방 번호 |
| `self_reflection` | 플레이어의 비친 얼굴 |

정보 행동:

- `insight`
- `contract`
- `seal`

정보 행동은 `info_target_key`가 필수다.

decision_required:

- `client_nonce` 필수 여부와 재사용 처리
- 비정보 행동에 `info_target_key`가 포함될 때 저장 여부
- action code 최종 목록과 display name

## 매치 상태 응답 후보

프론트가 의식 결투 화면을 렌더링하려면 아래 정보가 필요하다.

```json
{
  "data": {
    "match_id": "match_id",
    "case_id": "mirror_guest",
    "status": "in_progress",
    "turn": {
      "current_turn": 1,
      "turn_limit": 12,
      "deadline_at": "2026-06-02T00:00:00Z"
    },
    "player_state": {
      "sanity": 10,
      "ritual_power": 5,
      "curse_marks": 0
    },
    "available_actions": [
      {
        "action_code": "insight",
        "display_name": "간파",
        "cost": 1,
        "enabled": true,
        "disabled_reason": null,
        "requires_info_target": true
      }
    ],
    "info_targets": [
      {
        "key": "mirror_back",
        "label": "깨진 거울 뒷면"
      }
    ],
    "clue_state": {
      "true_name_fragments": [],
      "false_clues": []
    },
    "public_logs": []
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

decision_required:

- 최종 field name
- `deadline_at` 사용 여부
- 단서 상태 schema
- 공개 로그 schema
- 행동 disabled reason code 목록

## 결과 응답 후보

```json
{
  "data": {
    "match_id": "match_id",
    "result": "win",
    "final_resources": {
      "sanity": 4,
      "curse_marks": 1
    },
    "true_name_fragments": [],
    "public_logs": [],
    "story_result_text": "static approved text",
    "style_summary": {
      "labels": [],
      "metrics": {}
    },
    "llm_summary": {
      "enabled": false,
      "text": null,
      "fallback_used": true
    }
  },
  "meta": {
    "request_id": "req_...",
    "server_time": "2026-06-02T00:00:00Z"
  }
}
```

LLM 요약은 결과를 바꾸지 않는다.

decision_required:

- `result` enum
- style summary 표시 범위
- LLM summary schema
- 정적 결과 문장 source

## 승인된 error code 기본 목록

아래는 프론트 오류 표시 설계를 위한 기본 error code 목록이다. HTTP status 매핑과 field validation 세부 shape는 아직 후속 확정이 필요하다.

| code 후보 | 의미 | 프론트 처리 후보 |
|---|---|---|
| `AUTH_REQUIRED` | 인증 필요 | 로그인 화면 이동 |
| `SESSION_EXPIRED` | 세션 만료 | refresh 또는 재로그인 안내 |
| `CSRF_TOKEN_MISSING` | CSRF token 없음 | token 재획득 후 재시도 |
| `CSRF_TOKEN_INVALID` | CSRF token invalid | token 재획득 후 재시도 |
| `VALIDATION_ERROR` | 요청 검증 실패 | field error 표시 |
| `MATCH_NOT_FOUND` | 매치 없음 | 로비 또는 사건 선택으로 이동 |
| `MATCH_ALREADY_FINISHED` | 이미 종료된 매치 | 결과 화면 이동 |
| `TURN_ALREADY_SUBMITTED` | 중복 제출 | 현재 턴 결과 조회 또는 대기 |
| `ACTION_NOT_AVAILABLE` | 행동 불가 | disabled reason 표시 |
| `INFO_TARGET_REQUIRED` | 정보 대상 누락 | 정보 대상 선택 유도 |
| `RATE_LIMITED` | 요청 제한 | 잠시 후 재시도 |
| `LLM_SUMMARY_UNAVAILABLE` | LLM 요약 실패 | 정적 결과 문장 표시 |

decision_required:

- error code 최종 목록
- HTTP status와 error code 매핑
- field validation error shape

## 프론트 API client 요구사항

프론트 API client는 아래 기능을 제공해야 한다.

- base URL 관리
- `credentials: "include"` 기본 적용
- state-changing request에 CSRF header 자동 포함
- response envelope unwrap
- error envelope 정규화
- `error.code` 기반 분기
- 401, CSRF 실패, 중복 제출 실패 구분
- 요청 중복 클릭 방지와 재시도 제어

## 구현 착수 전 결정 목록

- API prefix
- endpoint 최종 목록
- request/response schema
- error code 최종 목록
- CSRF token 발급 endpoint
- CSRF header 이름
- refresh 흐름
- `client_request_id` / `client_nonce` 정책
- `case_id`, `match_id`, `turn_id` 형식
- 공개 로그 schema
- 단서 상태 schema
- 결과 화면 schema

## 구현 착수 판단

이 문서는 구현 착수 기준이 아니다.

API 명세가 승인본으로 승격되고, 프론트 구현 확정 문서가 `implementation-ready`가 된 뒤에 구현 기준으로 사용할 수 있다.
