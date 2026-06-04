---
title: "MVP 포함 제외 범위"
status: "draft"
type: "mvp-boundary"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# MVP 포함 제외 범위

## 포함 범위

- 회원가입
- 로그인
- 로그아웃
- 기본 프로필
- AI 사건 선택
- 괴이 3종 문서 확정
- `거울 속의 손님` 구현
- 브리핑
- 의식 결투
- 턴 제출
- 룰 엔진 판정
- 턴 결과 저장
- 승패 처리
- 결과/로그 표시
- 스타일 지표 계산
- RAG 검색용 `retrieval` 앱 구조
- RAG 문서 chunk 저장
- RAG query log 저장
- PostgreSQL `pgvector` 기반 검색 준비
- PvP-ready Auth/Match/Participant/Turn 구조 보존

## 제외 범위

- `우물 밑의 목소리` 구현
- `문밖의 어머니` 구현
- 실시간 PvP
- 매칭 대기열
- WebSocket 실시간 대전
- KAG
- 실제 LLM 생성
- 랭크 시스템
- cosmetic 보상
- 운영 배포 자동화

## 제외 이유

첫 버전은 공포 연출이나 AI 생성보다, 결정적 룰 엔진과 AI 스토리 단일 매치의 재미를 검증하는 것이 우선이다.

RAG는 검색 구조와 로그를 준비하지만, 룰 판정과 승패에는 관여하지 않는다.

PvP는 1차 MVP 구현 범위에서 제외하지만 선택적 후순위가 아니다.

PvP는 확정 후속 핵심 기능이므로 Auth/Match/Participant/Turn 구조는 [[09_Approved_Contracts/19_PvP_확정_후속_및_구조_보존_계약]]을 따른다.
