---
title: "MVP 포함 제외 범위"
status: "draft"
type: "mvp-boundary"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-04"
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
- AI 스토리 기준 Auth/Match/Participant/Turn 구조

## 제외 범위

- `우물 밑의 목소리` 구현
- `문밖의 어머니` 구현
- PvP 모드
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

PvP는 후속 확장 후보가 아니다.

Auth/Match/Participant/Turn 구조는 [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]의 PvP 미사용 결정을 따른다.
