---
title: "백엔드 LLM RAG 통합 문서 대조 보고"
status: "implementation-audit"
type: "backend-llm-rag-doc-audit"
source: "[[09_Approved_Contracts/08_LLM_도입_기준]], [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]], [[09_Approved_Contracts/20_Django_Auth_보안_계약]], [[09_Approved_Contracts/22_API_상세_Schema_계약]], [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]"
created: "2026-06-06"
updated: "2026-06-06"
---

# 백엔드 LLM RAG 통합 문서 대조 보고

작업 브랜치: `feature-backend-structure`

이 문서는 프론트엔드 구현을 제외하고, 현재 백엔드/LLM/RAG 구현이 승인 문서 의도와 얼마나 맞는지 대조한 결과다.

## 최신성 메모

이 문서는 [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]], [[09_Approved_Contracts/26_무명의_저주_사건_계약]], [[09_Approved_Contracts/27_플레이어_이름_무명의_저주_결전_RAG_계약]] 승인 이전의 중간 대조 보고다.

LLM runtime, `nameless_curse`, 플레이어 표시 이름, 결전 LLM payload, RAG source plan의 최신 구현 대조는 [[08_Implementation_Contracts/08_LLM_Runtime_구현_대조_보고]]를 우선한다.

따라서 이 문서의 LLM generation log, `turn_flavor_text` endpoint, AI Profile 연동, `무명의 저주` 분리 여부 관련 보류/결정 필요 항목은 현재 기준에서는 이후 승인본과 구현 대조 보고로 해소된 이력으로 본다.

## 이번 반영

| 영역 | 반영 |
|---|---|
| `auth.signup` | 501 stub 제거. 회원 생성과 프로필 초기 row 생성을 service transaction으로 구현했다. 응답 body에는 official schema대로 `user`만 반환한다. |
| Auth CSRF | `signup`, `login`, `logout`, `refresh` state-changing view에 CSRF 보호 decorator를 붙였다. |
| `matches.result` | 501 stub 제거. resolved match 결과를 official `MatchResult` shape로 반환한다. |
| LLM backend boundary | `backend/apps/llm/services.py`에 `llm_summary.enabled=false` fallback helper를 추가했다. Provider 호출은 연결하지 않았다. |
| 결과 fallback 문구 | `story_result_text` 정적 문구를 추가해 LLM 비활성 상태에서도 결과 화면을 구성할 수 있게 했다. |
| DB migration | `matches.0003_match_state_and_clue_ownership` 적용 상태를 확인했다. |

## 문서 의도와 맞는 항목

| 문서 기준 | 현재 구현 평가 |
|---|---|
| official API schema는 `{ data, meta }` envelope를 유지한다. | 일치. `auth.signup`, `matches.result` 모두 `api_success_response`를 사용한다. |
| access/refresh token은 signup 응답 body에 넣지 않는다. | 일치. signup은 cookie도 설정하지 않고 `user`만 반환한다. |
| logout은 승인된 refresh family revoke 정책을 따른다. | 현재 기준 일치. `auth.logout`은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]의 logout 정책에 따라 refresh family revoke와 cookie 삭제를 수행한다. |
| LLM은 서버 판정 이후 보조 요약에만 사용한다. | 일치. `matches.result`는 서버 판정 값을 먼저 조립하고 LLM fallback만 붙인다. |
| LLM 실패/비활성 시 정적 문구로 화면이 완성돼야 한다. | 일치. `story_result_text`와 `llm_summary.enabled=false`가 반환된다. |
| LLM provider/prompt/generation 구현은 top-level `llm/`에 둔다. | 일치. backend는 `llm.generation`을 직접 import하지 않는다. |
| RAG 검색 결과로 룰, 승패, 단서, 진명 조각을 바꾸지 않는다. | 일치. 이번 변경은 retrieval을 match 판정에 연결하지 않았다. |

## 위배로 판단한 항목

현재 이번 백엔드 변경에서 승인 문서를 직접 위배한 항목은 확인되지 않았다.

## 부분 반영 또는 보류

| 항목 | 상태 | 이유 |
|---|---|---|
| `turn_flavor_text` API 응답 위치 | 보류 | official `TurnResult`에는 LLM 표시 필드가 없다. 필드 추가, 별도 객체, 별도 endpoint 중 오너 결정이 필요하다. |
| LLM generation log 저장 | 보류 | `generation_id`를 어떤 테이블 생명주기로 저장할지 아직 확정되지 않았다. |
| 실제 Groq/provider backend 호출 | 보류 | 문서상 provider 구현은 제외 범위이며, backend 연결은 `backend/apps/llm` 계약 확정 후 진행해야 한다. |
| AI Profile 이벤트 저장 연동 | 부분 반영 | 모델/계산 함수는 있으나 `submit_match_turn`에서 `PlayerActionEvent` 저장과 최종 snapshot 갱신은 아직 없다. `stage_id` 출처와 `decision_duration_ms` 계산 기준을 명확히 해야 안전하게 구현할 수 있다. |
| RAG ingestion/search 실행 | 부분 반영 | 모델, chunking, allowlist, 기본값은 구현됐다. 실제 embedding 생성/검색 실행은 embedding provider와 ingest 실행 방식 확정 후 진행해야 한다. |
| `auth.signup` 중복 email error code | 부분 반영 | official signup error 목록에는 별도 중복 email code가 없어서 `VALIDATION_ERROR`로 매핑했다. |

## 구현하지 않은 이유가 명확한 항목

- `auth.logout`: 당시에는 미구현 유지가 맞았으나, 현재는 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]의 logout refresh family revoke 정책으로 구현됐다.
- 프론트엔드 연결: 현재 프론트 작업이 별도 진행 중이므로 이번 작업에서는 건드리지 않았다.
- RAG를 결과 판정에 연결: RAG가 승패/룰/단서에 영향을 주면 계약 위반이다.

## 검증 기록

실행 위치: `D:\dev\Project\SKN27-4th-3team`

| 명령 | 결과 |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest backend\tests\matches\test_match_result_runtime_contract.py backend\tests\story\test_story_match_start_runtime_contract.py::test_story_match_start_match_detail_and_turn_submit_no_longer_return_501 -q` | PASS, 7 passed |
| `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_signup_runtime_contract.py backend\tests\accounts\test_auth_api_contract.py::test_auth_views_delegate_runtime_to_service_layer_without_response_body_tokens backend\tests\api\test_api_runtime_envelope_contract.py::test_unimplemented_service_returns_501_error_envelope_with_stable_service_key -q` | PASS, 8 passed |
| `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts backend\tests\api -q` | PASS, 35 passed |
| `.\.venv\Scripts\python.exe backend\manage.py check` | PASS, system check identified no issues |
| `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | PASS, 158 passed |
| `.\.venv\Scripts\python.exe -m unittest discover llm\tests -v` | PASS, 8 tests OK |
| `$env:POSTGRES_HOST='127.0.0.1'; $env:POSTGRES_PORT='5432'; $env:POSTGRES_PASSWORD='change-me-local-db-password'; .\.venv\Scripts\python.exe backend\manage.py migrate --check` | PASS, exit code 0 |

## 최신 기준에서 해소/남은 결정

이 섹션은 위 검증 기록 작성 이후의 승인본을 반영해 갱신한다.

| 항목 | 현재 상태 | 기준 |
|---|---|---|
| `turn_flavor_text` 위치 | 해소. 별도 endpoint `POST /api/v1/matches/{match_id}/turns/{turn_id}/llm-text`를 사용한다. | [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]] |
| LLM generation log 저장 테이블 | 해소. `llm_generations`를 사용한다. | [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]] |
| LLM generation log 보존 기간 | 남음. 별도 운영/보존 정책 계약이 필요하다. | 운영 정책 미확정 |
| AI Profile `stage_id`, `decision_duration_ms` | 해소. MVP `stage_id`는 `1`, `decision_duration_ms`는 `Turn.started_at` 기준으로 계산한다. | [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]] |
| RAG ingest 실행 방식과 embedding provider 연결 시점 | 남음. RAG는 자동 ingest하지 않고, embedding provider/ingest 실행 방식은 후속 구현 계약이 필요하다. | [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]] |
| `무명의 저주` 사건 처리 | 해소. `nameless_curse` 별도 사건으로 둔다. | [[09_Approved_Contracts/26_무명의_저주_사건_계약]] |
