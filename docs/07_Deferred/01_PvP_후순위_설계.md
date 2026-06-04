---
title: "PvP 확정 후속 설계"
status: "core-roadmap"
type: "deferred-detail"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# PvP 확정 후속 설계

1차 MVP에서 PvP 구현은 제외한다.

하지만 PvP는 선택적 후순위가 아니라 로그인 다음으로 중요한 확정 후속 핵심 기능이다.

1차 MVP의 Auth, Match, Participant, Turn, Action Submission 구조는 PvP 도입을 막지 않아야 한다.

## 보존할 설계

- 실시간 턴제 PvP
- WebSocket 방 생성
- 매칭 대기열
- 상대 연결 종료와 재접속 처리
- 전적, 로그, 부정행위 의심 이벤트 저장
- human vs human participant 구조
- participant 기준 행동 제출과 권한 검증

## 1차 MVP에서 금지할 구조 축소

- AI 스토리 전용 match 구조
- 단일 user 소유 match 구조
- 항상 apparition이 있는 match 구조
- 사용자 1명 제출 즉시 resolve되는 전용 턴 구조
- 약한 로그인/세션 보안

## 구현 전 확정 필요

- PvP 재접속 허용 시간
- 랭크 점수 공식
- 매칭 기준

상세 기준은 [[09_Approved_Contracts/19_PvP_확정_후속_및_구조_보존_계약]]을 따른다.
