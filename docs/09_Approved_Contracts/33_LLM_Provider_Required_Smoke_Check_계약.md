---
title: "LLM Provider Required Smoke Check 계약"
status: "approved"
type: "approved-llm-provider-required-smoke-check-contract"
source: "2026-06-10 user decision: 추천 확정안"
created: "2026-06-10"
updated: "2026-06-10"
---

# LLM Provider Required Smoke Check 계약

이 문서는 [[09_Approved_Contracts/30_MVP_확장_1차_범위_계약]]의 LLM provider 검증 모드 구현 기준을 고정한다.

기존 [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]의 fallback/disabled 정책과 LLM 금지선은 계속 유효하다.

## 결정

기본 runtime은 기존처럼 LLM 실패, 비활성화, API key 누락, provider 오류, guardrail 실패를 API 실패로 전파하지 않는다.

운영 검증용 강제 모드는 별도 smoke check로만 제공한다.

`/healthz`는 [[09_Approved_Contracts/28_Production_배포_계약]]에 따라 Django process와 DB connection 확인 용도로 유지한다.

## 설정

| 설정 | 기본값 | 기준 |
|---|---|---|
| `LLM_REQUIRED` | `false` | `true`일 때 smoke check 실패를 배포 검증 실패로 본다. |
| `LLM_PROVIDER` | `groq` | 기존 LLM runtime provider 기본값을 따른다. |
| `LLM_API_KEY` | 빈 값 | `LLM_REQUIRED=true`일 때 필수다. |
| purpose | `turn_flavor_text` | smoke check용 최소 provider 호출 목적이다. |

## Smoke Check

관리 명령은 아래 이름을 사용한다.

```text
python backend/manage.py llm_smoke_check
```

`LLM_REQUIRED=false`이면 provider 호출을 수행하지 않고 성공 종료한다.

`LLM_REQUIRED=true`이면 아래를 수행한다.

1. `turn_flavor_text` 목적의 최소 승인 payload를 구성한다.
2. 기존 LLM adapter를 사용해 실제 provider 호출을 시도한다.
3. provider 호출 결과가 `succeeded`이고 text가 존재하면 성공 종료한다.
4. API key 누락, disabled, unsupported provider, timeout, provider 오류, provider 응답 형식 오류, guardrail 실패는 실패 종료한다.

## 실패 기준

아래 상황은 smoke check 실패다.

- `LLM_API_KEY` 누락
- `LLM_DISABLED=true`
- unsupported provider
- model id 누락
- provider timeout
- provider connection/status 오류
- provider 응답 형식 오류
- 빈 응답
- guardrail violation

## 로그/저장 금지

Smoke check는 아래 값을 저장하거나 출력하지 않는다.

- provider secret
- raw prompt
- raw response
- Authorization header
- cookie
- CSRF token

Smoke check는 `llm_generations` 테이블에 행을 만들지 않는다.

## 구현 금지선

- `LLM_REQUIRED=true`는 LLM이 게임 판정 권위를 가진다는 뜻이 아니다.
- LLM은 룰, 승패, 인증, 권한, 공식 단서, 진명 조각, 거짓 단서, 괴이 행동 선택을 결정하지 않는다.
- 기본 API runtime fallback/disabled 동작을 바꾸지 않는다.
- `/healthz`의 DB/process health 기준을 바꾸지 않는다.
