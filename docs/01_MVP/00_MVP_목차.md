---
title: "MVP 목차"
status: "draft"
type: "mvp-index"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-04"
---

# MVP 목차

## 1. MVP 목표

- 로그인 가능한 웹 게임을 만든다.
- 첫 괴이 `거울 속의 손님`과 AI 스토리 단일 결투를 제공한다.
- PvP 모드는 제공하지 않는다.
- 괴이 3종은 문서로 확정하되, 1차 MVP 구현은 `거울 속의 손님` 1종으로 제한한다.
- 서버가 모든 턴과 결과를 판정한다.
- 행동 로그를 저장한다.
- 플레이 스타일 지표를 계산한다.
- RAG 검색용 retrieval 구조를 준비한다.
- 결과 화면에서 승패, 턴 로그, 스타일 분석을 보여준다.

## 2. MVP 문서

- [[01_MVP/01_MVP_목표와_범위]]
- [[01_MVP/02_MVP_포함_제외_범위]]
- [[01_MVP/03_MVP_사용자_흐름]]
- [[01_MVP/04_MVP_확정_필요_항목]]
- [[01_MVP/99_MVP_구현_확정_문서]]

## 3. MVP 세부 설계 연결

- 게임 규칙: [[02_Game_Rules/00_Game_Rules_목차]]
- 백엔드: [[03_Backend/00_Backend_목차]]
- 프론트엔드: [[04_Frontend/00_Frontend_목차]]
- AI 스토리: [[05_Story_Mode/00_Story_Mode_목차]]
- 플레이어 스타일: [[06_AI_Profile/00_AI_Profile_목차]]

## 4. MVP 구현 우선순위

1. 백엔드 프로젝트 골격
2. 인증/인가/JWT refresh rotation
3. 기본 프로필과 권한 검증
4. 결정적 game_rules 엔진
5. AI 스토리 단일 매치 저장 구조
6. React 기본 UI와 AI 결투 화면
7. 플레이어 행동 로그와 스타일 지표
8. 괴이 패턴 정책
9. RAG retrieval 앱, 문서 chunk, query log 구조

## 5. MVP 이후 확장

- `우물 밑의 목소리` 구현
- `문밖의 어머니` 구현
- KAG 데이터 모델
- LLM 브리핑/대사/요약
- 운영 로그와 부정행위 의심 로그
- 배포 환경 구성

PvP는 후속 확장 후보가 아니다.

Auth/Match/Participant/Turn 구조는 [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]의 PvP 미사용 결정을 따른다.
