---
title: "LLM Runtime 구현 대조 보고"
status: "implementation-audit"
type: "backend-llm-runtime-doc-audit"
source: "[[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]"
created: "2026-06-06"
updated: "2026-06-06"
---

# LLM Runtime 구현 대조 보고

작업 브랜치: `feature-backend-structure`

이 문서는 2026-06-06 오너 결정과 현재 백엔드 구현을 대조한 결과다.

## 기준 문서

- [[09_Approved_Contracts/08_LLM_도입_기준]]
- [[09_Approved_Contracts/09_RAG_도입_기준]]
- [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]
- [[09_Approved_Contracts/20_Django_Auth_보안_계약]]
- [[09_Approved_Contracts/22_API_상세_Schema_계약]]
- [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]

## 반영 완료

| 영역 | 구현 | 문서 의도 대조 |
|---|---|---|
| LLM 앱 경계 | `backend/apps/llm`를 Django app으로 등록하고 `LlmGeneration` 모델을 추가했다. | LLM backend 연결 경계가 `backend/apps/llm`이어야 한다는 기준과 일치한다. |
| LLM 로그 | `llm_generations` 테이블을 추가했다. | 생성 결과와 최소 metadata 저장 의도와 일치한다. prompt 원문, provider raw response, API key는 저장하지 않는다. |
| result summary | `GET /api/v1/matches/{match_id}/result`가 서버 결과 payload를 먼저 만든 뒤 `generate_result_summary()`를 호출한다. | LLM이 서버 판정 이후 보조 요약만 담당한다는 기준과 일치한다. |
| turn flavor text | `POST /api/v1/matches/{match_id}/turns/{turn_id}/llm-text` endpoint를 추가했다. | turn text를 별도 endpoint로 분리한다는 결정과 일치한다. |
| final duel dialogue | `POST /api/v1/matches/{match_id}/duel/dialogues` endpoint와 `duel_dialogues` 테이블을 추가했다. | 결전 대화를 별도 저장 구조로 관리한다는 결정과 일치한다. |
| Turn.started_at | `turns.started_at`을 추가했고 기존 row는 `deadline_at - 25초`로 backfill한다. 새 턴은 `started_at=now`로 생성한다. | `decision_duration_ms`를 서버 기준으로 계산한다는 기준과 일치한다. |
| AI Profile | `submit_match_turn`에서 turn resolve 직후 `PlayerActionEvent`를 저장하고 style snapshot을 저장한다. match 종료 시 final snapshot도 저장한다. | 행동 이벤트는 매 턴 resolve 시점에 저장하고, 최종 재계산을 수행한다는 기준과 일치한다. |
| Groq 기본값 | purpose별 model/timeout/temperature/max token 기본값을 `backend/apps/llm/services.py`에 고정하고 env override를 허용한다. | 2026-06-06 오너 결정과 일치한다. |
| refresh cookie path | refresh cookie path를 `/api/v1/auth`로 확대했다. | logout endpoint가 refresh cookie를 받을 수 있어야 한다는 결정과 일치한다. |
| LLM 실패 처리 | API는 LLM 실패/비활성화 시 성공 응답을 유지하고 `enabled=false`, `text=null`을 반환한다. | fallback 기준과 일치한다. |

## 위배 없음으로 확인한 항목

- LLM 생성 결과는 승패, 종료 사유, 행동 성공/실패, 자원, 진명 조각, 거짓 단서, 괴이 행동 선택을 변경하지 않는다.
- RAG는 이번 구현에서도 룰/승패/단서 계산에 연결하지 않았다.
- frontend 파일은 이번 작업에서 수정하지 않았다.
- `auth.logout`은 현재 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]의 logout refresh family revoke 정책에 따라 구현한다.

## 보류 또는 미구현

| 항목 | 상태 | 이유 |
|---|---|---|
| `nameless_curse` 사건 seed | 반영 | [[09_Approved_Contracts/26_무명의_저주_사건_계약]]의 승인값 기준으로 별도 case, info_targets, 진명 조각, 거짓 단서, 결과 문구를 추가했다. |
| RAG ingest management command | 보류 | embedding provider 호출 방식, 저장할 vector 차원, ingest 대상 파일 목록의 실행 방식이 아직 구현 계약으로 충분히 좁혀지지 않았다. |
| `auth.logout` 실제 revoke | 보류 | refresh family revoke 실패 정책, 보안 이벤트 metadata, access-only/logout 요청 처리 방식이 아직 별도 확정되지 않았다. |

## 검증 기록

실행 위치: `D:\dev\Project\SKN27-4th-3team`

| 명령 | 결과 |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | PASS, 174 passed |
| `.\.venv\Scripts\python.exe -m unittest discover llm\tests -v` | PASS, 9 tests OK |
| `.\.venv\Scripts\python.exe backend\manage.py check` | PASS, system check identified no issues |
| `.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run` | PASS, no model/migration changes detected. 기본 DB env에서는 password warning이 있었다. |
| `$env:POSTGRES_HOST='127.0.0.1'; $env:POSTGRES_PORT='5432'; $env:POSTGRES_PASSWORD='change-me-local-db-password'; .\.venv\Scripts\python.exe backend\manage.py migrate` | PASS, `llm.0001_initial`, `matches.0004_turn_started_at_and_duel_dialogue` 적용 |
| `$env:POSTGRES_HOST='127.0.0.1'; $env:POSTGRES_PORT='5432'; $env:POSTGRES_PASSWORD='change-me-local-db-password'; .\.venv\Scripts\python.exe backend\manage.py migrate --check` | PASS, exit code 0 |
