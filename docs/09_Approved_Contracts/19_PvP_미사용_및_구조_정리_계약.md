---
title: "PvP 미사용 및 구조 정리 계약"
status: "approved"
type: "approved-no-pvp-contract"
source: "[[01_MVP/02_MVP_포함_제외_범위]], [[03_Backend/03_매치와_턴_저장]]"
created: "2026-06-02"
updated: "2026-06-04"
supersedes: "PvP 확정 후속 및 구조 보존 계약"
---

# PvP 미사용 및 구조 정리 계약

이 문서는 PvP 모드가 없다는 최종 결정을 기록한다.

기존의 `PvP 확정 후속 핵심 기능`, `PvP-ready 구조 보존`, `human vs human 확장 전제`는 더 이상 구현 기준이 아니다.

## 결정

PvP 모드는 없다.

1차 MVP와 후속 구현 계획에서 아래 기능은 제외한다.

- 실시간 PvP 매치
- PvP 매칭 대기열
- WebSocket room
- Redis 기반 matchmaking
- reconnect window
- PvP ranking
- PvP abuse/cheat 운영 대응 자동화
- human vs human match 확장 전제

## 구현 기준

| 영역 | 기준 |
|---|---|
| Match | AI 스토리 매치 기준으로 설계한다. |
| Participant | human player와 apparition 참가자 표현까지만 구현 기준으로 둔다. |
| Turn | player submission과 apparition/server action을 기준으로 resolve한다. |
| Action Submission | MVP에서는 player participant의 제출 중복 방지에 집중한다. |
| Auth | PvP 전제가 아니라 일반 웹 서비스 보안 기준으로 보수적으로 유지한다. |
| Realtime | 1차 MVP와 후속 범위 모두 구현하지 않는다. |
| Redis/Channels/WebSocket | PvP 목적으로 도입하지 않는다. |

## 유지할 보안 기준

PvP가 없어도 아래 보안 기준은 유지한다.

- localStorage/sessionStorage token 저장 금지
- access token과 refresh token 모두 HttpOnly cookie 사용
- 모든 state-changing endpoint에 CSRF 적용
- dev 환경에서도 CSRF 비활성화 금지
- refresh token 원문 저장 금지
- refresh token rotation과 reuse 감지 설계 필수
- reuse 감지 시 token family revoke 설계 필수

상세 Auth 보안 기준은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

## 제거할 문서 표현

아래 표현은 더 이상 사용하지 않는다.

- PvP-ready
- 확정 후속 핵심 PvP
- human vs human 확장 보존
- WebSocket 기반 PvP
- Redis matchmaking
- PvP 재접속 허용 시간
- PvP ranking 또는 rating

## 남은 정리 대상

아래 항목은 별도 구현/문서 정리 작업에서 제거하거나 범위를 재확정한다.

- `backend/apps/realtime/` placeholder 제거 완료
- 문서 내 PvP 확장 메모
- 화면 설계 문서의 PvP 매칭/대전 항목
- Match schema의 `mode` 값이 AI story 외 값을 가져야 하는지 여부
- `participant_type`에서 `human`, `apparition` 외 확장이 필요한지 여부

## 관련 문서

- [[03_Backend/03_매치와_턴_저장]]
- [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]
- [[09_Approved_Contracts/20_Django_Auth_보안_계약]]
- [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]
