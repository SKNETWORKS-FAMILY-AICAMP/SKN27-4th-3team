---
title: "PvP 후순위 설계 폐기 기록"
status: "retired"
type: "retired-deferred-detail"
source: "[[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]"
created: "2026-05-30"
updated: "2026-06-04"
superseded_by: "[[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]"
---

# PvP 후순위 설계 폐기 기록

이 문서는 과거 PvP 후순위 설계 기록이다.

현재 구현 기준으로 사용하지 않는다.

## 현재 결정

PvP 모드는 없다.

기존의 실시간 턴제 PvP, WebSocket 방, 매칭 대기열, 상대 연결 종료와 재접속 처리, human vs human participant 구조는 더 이상 후속 구현 후보가 아니다.

현재 기준은 [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]의 PvP 미사용 결정이다.

## 구현 금지

- PvP match
- PvP matchmaking
- PvP reconnect
- PvP ranking
- PvP abuse/cheat 대응
- PvP를 위한 Redis/Channels/WebSocket 도입
