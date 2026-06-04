---
title: "LLM 도입 기준"
status: "approved"
type: "approved-llm-adoption-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# LLM 도입 기준

이 문서는 LLM 도입 단계에 대한 승인된 기준이다.

## 결정

LLM은 판정 이후 요약부터 사용한다.

## 우선 사용처

- 결과 화면 요약
- 플레이 스타일 요약 문장
- 운영자용 매치 로그 요약

## 폴더 경계

LLM 팀 작업 영역은 최상위 `llm/` 폴더다.

```text
llm/
  prompts/
  generation/
  evaluation/
  fixtures/
  docs/
```

서버 연결 경계는 `backend/apps/llm/`이다.

LLM prompt 실험, 평가 샘플, provider 비교는 `llm/`에서 관리하고, 서버 API와 저장 로직 연결은 `backend/apps/llm/`을 통해서만 진행한다.

상세 폴더 구조는 [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]을 따른다.

## 금지선

LLM은 아래 항목에 관여하지 않는다.

- 행동 성공/실패
- 승패
- 이성, 의식력, 저주 흔적 계산
- 진명 조각 획득 판정
- 거짓 단서 진위 판정
- 보상, 랭킹, 매칭

## fallback

LLM 호출이 실패해도 정적 문구와 서버 판정 결과만으로 화면을 완성할 수 있어야 한다.

LLM 생성 결과는 공식 설정이나 룰 변경으로 취급하지 않는다.
