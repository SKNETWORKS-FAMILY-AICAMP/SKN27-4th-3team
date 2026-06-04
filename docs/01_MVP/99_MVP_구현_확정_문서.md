---
title: "MVP 구현 확정 문서"
status: "needs-decision"
type: "implementation-confirmation"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# MVP 구현 확정 문서

이 문서는 MVP 구현 착수 직전에 승인받는 최종 기준 문서다.

현재 상태는 `needs-decision`이다. [[01_MVP/04_MVP_확정_필요_항목]]이 확정되기 전까지 구현 기준으로 사용하지 않는다.

프론트엔드 구현과 LLM generation 구현은 별도 팀 범위로 분리한다.

RAG는 제외하지 않는다. 1차 MVP에서는 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]에 따라 `retrieval` 앱, 문서 chunk, embedding, 검색, query log 구조를 구현 준비 범위에 포함한다.

Django Auth 보안은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]을 따른다.

## 확정 대상 문서

- [[01_MVP/01_MVP_목표와_범위]]
- [[01_MVP/02_MVP_포함_제외_범위]]
- [[01_MVP/03_MVP_사용자_흐름]]
- [[02_Game_Rules/99_Game_Rules_구현_확정]]
- [[03_Backend/99_Backend_구현_확정]]
- [[04_Frontend/99_Frontend_구현_확정]]
- [[05_Story_Mode/99_Story_Mode_구현_확정]]
- [[06_AI_Profile/99_AI_Profile_구현_확정]]

## 구현 착수 조건

- MVP 포함/제외 범위가 확정되어야 한다.
- 게임 규칙 미확정 항목이 없어야 한다.
- 백엔드 앱 경계와 데이터 모델이 확정되어야 한다.
- 프론트엔드 MVP 화면 범위가 확정되어야 한다.
- 첫 괴이 `거울 속의 손님`의 문장과 패턴이 확정되어야 한다.
- 검증 명령과 완료 기준이 확정되어야 한다.

## 현재 남은 구현 전 결정

- 프론트엔드 구현과 LLM generation 구현을 제외한 백엔드/API 구현 전 남은 오너 결정 없음
