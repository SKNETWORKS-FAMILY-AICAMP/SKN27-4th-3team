---
title: "PvP 확정 후속 및 구조 보존 계약"
status: "approved"
type: "approved-pvp-roadmap-architecture-contract"
source: "[[01_MVP/02_MVP_포함_제외_범위]], [[03_Backend/03_매치와_턴_저장]], [[07_Deferred/01_PvP_후순위_설계]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# PvP 확정 후속 및 구조 보존 계약

이 문서는 PvP의 제품 우선순위와 1차 MVP 백엔드 구조 제약을 확정한다.

## 결정

PvP는 선택적 후순위 기능이 아니다.

PvP는 로그인 기능 다음으로 중요한 확정 후속 핵심 기능이다.

1차 MVP에서는 실시간 PvP, 매칭 대기열, WebSocket 실시간 대전을 구현하지 않는다.

하지만 Auth, User, Profile, Match, Participant, Turn, Action Submission, Result 구조는 PvP 도입을 막지 않도록 설계한다.

## 1차 MVP 구현 제외

아래 항목은 1차 MVP 구현 범위에서 제외한다.

- 실시간 PvP 매치
- PvP 매칭 대기열
- WebSocket room
- Redis 기반 matchmaking
- reconnect window
- PvP ranking
- PvP abuse/cheat 운영 대응 자동화

## 반드시 보존할 구조

| 영역 | 보존 기준 |
|---|---|
| Auth | PvP를 전제로 한 보수적 계정/세션 보안 기준을 적용한다. |
| User | 사용자 계정은 AI 스토리 전용 구조로 만들지 않는다. |
| Profile | 전적/스타일 요약은 PvP 전적 확장을 막지 않는다. |
| Match | `matches.mode`는 `ai_story`와 future `pvp`를 구분할 수 있어야 한다. |
| Participant | `match_participants`는 두 명 이상의 human 참가자를 표현할 수 있어야 한다. |
| Turn | 턴은 human vs apparition뿐 아니라 human vs human 제출 구조를 수용할 수 있어야 한다. |
| Action Submission | 제출은 user 기준이 아니라 participant 기준으로 저장한다. |
| Result | 결과 스냅샷은 AI 스토리 전용 필드에 종속되지 않는다. |

## 금지할 구현 가정

아래 가정으로 1차 MVP를 구현하지 않는다.

- 매치에는 human 참가자가 항상 1명뿐이다.
- 모든 매치에는 `apparition_id`가 필수다.
- 모든 매치에는 `story_case_id` 또는 `stage_id`가 필수다.
- 턴은 사용자 한 명이 제출하면 즉시 resolve된다.
- 상대 행동은 항상 서버가 생성한다.
- `match.user_id`처럼 단일 소유자만으로 접근 권한을 판단한다.
- 행동 제출 idempotency를 user 단위로만 판단한다.
- 로그인 보안은 AI 스토리 MVP라서 약하게 처리해도 된다.

## PvP-ready Match 기준

| 필드/개념 | 기준 |
|---|---|
| `matches.mode` | `ai_story`, future `pvp`를 분리한다. |
| `match_participants.participant_type` | `human`, `apparition`을 구분한다. |
| `match_participants.user_id` | human 참가자에서 사용한다. |
| `match_participants.apparition_id` | apparition 참가자에서 사용한다. PvP에서는 nullable이다. |
| `action_submissions.participant_id` | 모든 행동 제출은 participant 기준이다. |
| `client_nonce` | participant + turn 범위에서 중복 제출을 막는다. |
| 접근 권한 | 요청 사용자가 해당 match의 human participant인지 확인한다. |

## 보안 기준

PvP는 사람 간 온라인 대전이므로 Auth 보안은 1차 MVP부터 PvP 기준으로 잡는다.

- localStorage/sessionStorage token 저장 금지
- access token과 refresh token 모두 HttpOnly cookie 사용
- 모든 state-changing endpoint에 CSRF 적용
- dev 환경에서도 CSRF 비활성화 금지
- refresh token 원문 저장 금지
- refresh token rotation과 reuse 감지 설계 필수
- reuse 감지 시 token family revoke 설계 필수
- match 접근 권한은 participant membership으로 검증

상세 Auth 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

## 후속 설계 대상

아래 항목은 PvP 구현 전 별도 확정한다.

- PvP 매칭 기준
- PvP 재접속 허용 시간
- WebSocket room lifecycle
- Redis queue 구조
- PvP timeout/reconnect 처리
- PvP ranking 또는 rating 공식
- PvP 부정행위 의심 이벤트 기준

## 관련 문서

- [[03_Backend/03_매치와_턴_저장]]
- [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]
- [[09_Approved_Contracts/10_Auth_토큰_전달_기준]]
- [[09_Approved_Contracts/11_CSRF_정책_기준]]
- [[09_Approved_Contracts/20_Django_Auth_보안_계약]]
