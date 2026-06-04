---
title: "LLM 후순위 설계"
status: "draft"
type: "deferred-detail"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-05-30"
---

# LLM 후순위 설계

MVP에서 실제 LLM 호출은 제외한다.

## 보존할 설계

```text
LlmClient.generate(purpose, system_prompt, user_prompt, context_refs) -> LlmResult
```

## LLM이 하는 일

- 스테이지 브리핑 문장 생성
- 괴이 대사 생성
- 전투 결과 기록 문장 생성
- 플레이어 스타일 요약
- 다음 괴이가 플레이어를 어떻게 노릴지 설명

## LLM이 하지 않는 일

- 행동 성공 여부 결정
- 피해량 계산
- 진명 조각 획득 여부 결정
- PvP 승패 결정
- 랭크 점수 계산
- 보상 지급
- 인증/권한 판단
- 매칭 판단

## 구현 전 확정 필요

- LLM provider
- fallback 문구 관리 방식
- generation log 보존 기간

