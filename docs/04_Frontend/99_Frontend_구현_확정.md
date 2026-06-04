---
title: "Frontend 구현 확정"
status: "needs-decision"
type: "implementation-confirmation"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-05-30"
---

# Frontend 구현 확정

이 문서는 프론트엔드 구현 착수 전 승인받는 최종 기준 문서다.

## 확정 전 조건

- 의식 결투 화면의 최소 시각 표현 확정
- 모바일 대응 범위 확정

## 확정된 기술 조건

| 결정 | 확정값 |
|---|---|
| 프론트 스택 | React + TypeScript + Vite |
| 라우팅 | React Router |
| 스타일 | CSS Modules |
| API client | `fetch` 기반 wrapper |
| 상태 관리 | React local state와 Context, 화면/feature 단위 API hook |
| 폴더 구조 | [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]의 구조를 따른다. |
| 프로젝트 최상위 폴더 구조 | [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]을 따른다. |
| 인증 연결 | HttpOnly cookie + `credentials: "include"` |
| CSRF 연결 | `GET /api/v1/auth/csrf`, `X-CSRFToken` |
