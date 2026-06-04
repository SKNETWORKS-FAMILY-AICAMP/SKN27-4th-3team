---
title: "AI Profile 구현 확정"
status: "approved"
type: "implementation-confirmation"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# AI Profile 구현 확정

이 문서는 플레이어 스타일 지표 구현 착수 전 승인받는 최종 기준 문서다.

## 확정된 구현 기준

| 항목 | 확정값 |
|---|---|
| 행동 이벤트 저장 schema | [[06_AI_Profile/01_행동_이벤트]]를 따른다. |
| 이벤트 저장 시점 | 턴 resolve 시점 |
| 스타일 지표 계산 방식 | [[06_AI_Profile/02_스타일_지표]]를 따른다. |
| 스타일 지표 계산 시점 | 각 턴 resolve 직후 |
| 최종 재계산 | 매치 종료 시 수행 |
| 0으로 나누는 경우 | `0.0` |
| 개인정보 삭제 | 행동 이벤트와 스타일 스냅샷 삭제 |
| 괴이 행동 반영 | [[06_AI_Profile/03_AI_대응_정책]]을 따른다. |

상세 기준은 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]을 따른다.
