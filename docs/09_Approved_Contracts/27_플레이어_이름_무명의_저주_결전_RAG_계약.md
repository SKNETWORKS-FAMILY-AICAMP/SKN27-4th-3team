---
title: "플레이어 이름 무명의 저주 결전 RAG 계약"
status: "approved"
type: "approved-player-name-nameless-duel-rag-contract"
source: "2026-06-06 owner approval of recommended next-step implementation"
created: "2026-06-06"
updated: "2026-06-06"
---

# 플레이어 이름 무명의 저주 결전 RAG 계약

이 문서는 `nameless_curse` 다음 구현 단계의 기준이다.

## 적용 범위

포함한다.

- `match_start` 요청의 플레이어 표시 이름
- 사건별 결전 가능 조건
- `nameless_curse` 결전 LLM payload 보강
- RAG 검색 소스 plan과 로그 기준

제외한다.

- 프론트엔드 구현
- LLM이 승패를 직접 판정하는 기능
- RAG 결과가 룰, 단서, 승패를 변경하는 기능
- 별도 profile/session 이름 변경 API

## 플레이어 표시 이름

`POST /api/v1/story/cases/{case_id}/matches` 요청은 선택 필드 `player_display_name`을 받을 수 있다.

| 항목 | 기준 |
|---|---|
| field | `player_display_name` |
| required | false |
| type | string |
| trim | 앞뒤 공백 제거 |
| length | 1-24자 |
| blank string | 금지 |
| 저장 위치 | `match_start_requests.player_display_name` |
| fallback | 요청값이 없으면 기존 profile nickname, 그다음 email 또는 user id |

같은 `client_request_id` 재시도는 처음 저장한 `player_display_name`과 같은 값이어야 한다.

다른 값으로 재시도하면 `IDEMPOTENCY_CONFLICT`를 반환한다.

LLM prompt에는 표시 이름만 전달한다.

`llm_generations.metadata_json`에는 플레이어 이름 원문을 저장하지 않는다.

## 사건별 결전 가능 조건

`seal` 행동은 기존 API action code를 유지하되, 의미는 사건별 결전/봉인 시도로 해석한다.

| case_id | 결전 가능 조건 | 성공 의미 |
|---|---:|---|
| `mirror_guest` | 진명 조각 3개 | 거울 속 손님 봉인 |
| `nameless_curse` | 진명 조각 2개 이상 | 피티의 이름 회복 |

`nameless_curse`에서 진명 조각 2개 이상을 확보하면 `seal_available=true`가 된다.

`nameless_curse`에서 `seal` 성공은 피티를 처치하는 것이 아니라 이름을 되찾게 하는 결말로 기록한다.

거짓 단서 2개 이상은 결전 LLM payload에 `false_clue_pressure=true`로 전달한다.

거짓 단서 2개 이상 자체가 승패를 직접 바꾸지는 않는다.

## 결전 LLM 기준

`final_duel_dialogue`는 대사와 분위기만 만든다.

서버의 승패, 자원, 진명 조각, 거짓 단서, 괴이 행동 선택은 LLM 출력으로 바뀌지 않는다.

`nameless_curse` 결전 payload에는 아래 항목을 포함한다.

- `player.display_name`
- `case.case_id`
- `case.title`
- `apparition_alias`
- `duel_rules.required_true_name_fragments`
- `duel_rules.win_condition`
- `duel_rules.false_clue_pressure`
- `public_context.true_name_fragments`
- `public_context.false_clues`
- `public_context.recent_public_logs`

`nameless_curse`의 `duel_rules.win_condition`은 `recover_piti_true_name`이다.

`mirror_guest`의 `duel_rules.win_condition`은 `seal_apparition`이다.

## RAG 기준

RAG는 LLM context 보조로만 사용한다.

RAG source plan은 사건별 우선 문서를 반환할 수 있다.

`nameless_curse`의 우선 문서는 아래 순서다.

1. `docs/09_Approved_Contracts/27_플레이어_이름_무명의_저주_결전_RAG_계약.md`
2. `docs/09_Approved_Contracts/26_무명의_저주_사건_계약.md`
3. `docs/09_Approved_Contracts/25_LLM_Runtime_통합_계약.md`
4. `docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md`

RAG query log는 기존 `retrieval_query_logs` 기준을 유지한다.

RAG source plan은 룰 판정 결과를 바꾸지 않는다.

## 금지선

- LLM은 피티의 진짜 이름을 새로 발명하지 않는다.
- LLM은 플레이어 이름을 저장 로그 metadata에 남기지 않는다.
- LLM은 `seal` 성공 여부를 판정하지 않는다.
- RAG는 공식 단서, 진명 조각, 거짓 단서를 새로 만들지 않는다.
- 프론트엔드 파일은 이 계약 구현 범위에서 수정하지 않는다.
