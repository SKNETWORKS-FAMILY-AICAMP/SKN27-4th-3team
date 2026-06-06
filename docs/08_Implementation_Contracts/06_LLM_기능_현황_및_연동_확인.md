---
title: "LLM 기능 현황 및 연동 확인"
status: "needs-decision"
type: "llm-current-state-review"
source: "[[09_Approved_Contracts/08_LLM_도입_기준]], [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]], llm/"
created: "2026-06-06"
updated: "2026-06-06"
---

# LLM 기능 현황 및 연동 확인

이 문서는 현재 브랜치에 들어온 LLM 작업물을 기준으로, 이미 구현된 기능과 아직 백엔드 런타임에 연결되지 않은 영역을 구분한다.

현재 문서는 구현 착수 기준이 아니라 결정 전 검토안이다.

## 승인된 경계

LLM 도입 기준은 [[09_Approved_Contracts/08_LLM_도입_기준]]을 따른다.

핵심 원칙은 아래와 같다.

- LLM은 판정 이후 요약부터 사용한다.
- LLM은 게임 판정자가 아니다.
- LLM은 승패, 행동 성공/실패, 자원 수치, 진명 조각 획득, 거짓 단서 진위 판정에 관여하지 않는다.
- LLM 실패 시 정적 문구와 서버 판정만으로 화면이 완성되어야 한다.
- LLM prompt, fixture, provider 실험은 최상위 `llm/`에서 관리한다.
- 서버 API와 저장 로직 연결은 `backend/apps/llm/` 경계를 통해서만 진행한다.

## 현재 들어와 있는 기능

| 영역 | 현재 상태 |
|---|---|
| `llm/prompts/` | purpose별 프롬프트 템플릿과 조립 규칙 존재 |
| `llm/generation/adapter.py` | Groq 기반 adapter와 fallback 처리 존재 |
| `llm/fixtures/` | official fixture와 데모 스토리 후보 fixture 존재 |
| `llm/evaluation/` | guardrail 기준과 expected output 샘플 존재 |
| `llm/tests/` | guardrail, official fixture dry-run 테스트 존재 |
| `ops/env/llm.env.example` | LLM provider 환경 변수 예시 존재 |

## 지원 purpose

| purpose | 역할 | 현재 사용 가능 상태 |
|---|---|---|
| `result_summary` | 결과 화면 보조 서사 요약 | prompt 조립 및 adapter 호출 가능 |
| `turn_flavor_text` | 단일 턴 화면 연출 문구 | prompt 조립 및 프론트 전달용 래핑 가능 |
| `style_summary` | 플레이 스타일 요약 문장 | prompt 조립 및 guardrail 검증 가능 |
| `match_log_summary` | 운영자용 매치 로그 요약 | prompt 조립 및 guardrail 검증 가능 |

## adapter 동작

`llm/generation/adapter.py`는 아래 함수를 제공한다.

| 함수 | 용도 |
|---|---|
| `generate_llm_result(purpose, payload, options, dry_run)` | 내부 generation result 반환 |
| `generate_llm_ui_text(purpose, payload, options, dry_run)` | 프론트 전달용 래핑 결과 반환 |

반환 상태는 `succeeded`, `failed`, `skipped`로 구분된다.

`LLM_DISABLED=true`, API key 누락, model id 누락, unsupported provider 상황에서는 provider 호출 없이 `skipped`로 처리한다.

provider 오류, timeout, 응답 파싱 실패, guardrail 위반은 `failed`와 `fallback_used=true`로 처리한다.

## guardrail

현재 guardrail은 아래 유형을 막는다.

- 입력에 없는 데모 스토리 고유명사 유출
- 행동 성공/실패를 LLM이 새로 판정하는 문장
- 단서 획득 또는 거짓 단서 진위 판정처럼 보이는 문장
- 승패와 반대되는 결과 요약
- 다음 괴이 행동 예고
- 보상, 랭킹, 매칭, 운영 조치 제안
- 플레이어 성격 낙인
- 프론트 표시 길이를 넘는 턴 연출 문구

## 아직 백엔드에 없는 것

| 항목 | 현재 상태 |
|---|---|
| `backend/apps/llm` 앱 구현 | `.gitkeep`만 존재 |
| Django `INSTALLED_APPS` 등록 | 없음 |
| LLM generation result 저장 모델 | 없음 |
| LLM 호출 서비스 경계 | 없음 |
| `matches.result` 응답 내 실제 LLM 호출 | 없음 |
| `turn_flavor_text` API 응답 위치 | 미확정 |
| generation log 보존 기간 | 미확정 |
| 기본 Groq model id | 미확정 |
| 실제 API key 운용 방식 | `.env` 주입 원칙만 존재 |

따라서 현재 LLM 기능은 독립 실험 및 계약 테스트 단계다.

백엔드 API 런타임에서 자동으로 LLM 문구를 생성하거나 저장하는 상태가 아니다.

## 현재 백엔드와 연결할 때 필요한 결정

- `MatchResult.llm_summary`를 백엔드에서 생성해 내려줄지, 프론트가 별도 요청할지 결정해야 한다.
- `turn_flavor_text`를 `TurnResult` 내부 필드로 넣을지, 형제 `llm` 객체로 넣을지, 별도 endpoint로 분리할지 결정해야 한다.
- generation result를 저장할 DB schema와 보존 기간을 결정해야 한다.
- 실패한 LLM 호출을 어떤 로그 테이블 또는 request id와 연결할지 결정해야 한다.
- Groq 기본 model id를 공식 문서 확인 후 확정해야 한다.
- provider 호출이 API latency에 미치는 영향을 제한할 timeout과 fallback 기준을 확정해야 한다.

## PDF 스토리와 LLM 문서의 정리 필요

이번에 제공된 `무명의_저주_게임설정문서.pdf` 기준으로는 원혼의 진짜 이름이 `피티`로 정리되어 있다.

기존 LLM 참고 문서에는 이전 초고 기반으로 `엘리자베스` 언급이 남아 있다.

현재는 `피티`를 최신 PDF 기준 후보로 보고, `엘리자베스`는 재확인이 필요한 이전 초고 흔적으로 취급한다.

이 항목이 확정되기 전까지 LLM은 입력에 없는 `피티`, `이안`, `엘리자베스`, `무명(無名)의 저주`를 생성 결과에 끌어오면 안 된다.

## 현재 권장 상태

현 시점의 권장 운영 상태는 아래와 같다.

- 백엔드 판정과 API 구현은 정적 문구 기반으로 유지한다.
- LLM은 `llm/` 단위 테스트와 dry-run으로 검증한다.
- 실제 provider 호출은 `.env`와 API key가 준비된 로컬 실험으로 제한한다.
- 백엔드 연결은 `backend/apps/llm` 서비스와 저장 계약이 확정된 뒤 진행한다.
- `무명(無名)의 저주` 설정은 LLM 톤 참고 후보로만 두고, 공식 사건 설정으로 사용하지 않는다.
