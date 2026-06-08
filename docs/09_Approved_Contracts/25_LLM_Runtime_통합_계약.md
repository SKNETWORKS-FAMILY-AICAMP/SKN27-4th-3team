---
title: "LLM Runtime 통합 계약"
status: "approved"
type: "approved-llm-runtime-integration-contract"
source: "2026-06-06 owner decision"
created: "2026-06-06"
updated: "2026-06-06"
---

# LLM Runtime 통합 계약

이 문서는 `feature-backend-structure` 브랜치의 백엔드 LLM runtime 구현 기준이다.

## 적용 범위

포함한다.

- 결과 화면 보조 요약 `result_summary`
- 턴 연출 문구 `turn_flavor_text`
- 플레이어와 괴이의 결전 대화 `final_duel_dialogue`
- LLM 생성 로그 저장
- AI Profile 행동 이벤트 저장을 위한 `Turn.started_at`
- refresh cookie path 확대

제외한다.

- 프론트엔드 구현
- LLM이 승패, 행동 성공/실패, 자원, 진명 조각, 거짓 단서, 괴이 행동 선택을 결정하는 기능
- RAG 검색 결과가 룰 또는 게임 상태를 변경하는 기능
- 승인 문서 없이 사건 seed 데이터를 임의 생성하는 기능

`nameless_curse` 사건 seed는 [[09_Approved_Contracts/26_무명의_저주_사건_계약]]의 승인값만 사용한다.

## 공통 금지선

LLM은 서버 판정 이후의 보조 문장만 생성한다.

LLM은 아래 항목에 대한 권위를 갖지 않는다.

- 승패
- 종료 사유
- 행동 성공/실패
- 자원 수치
- 진명 조각 획득
- 거짓 단서 생성 또는 진위 판정
- 괴이 행동 선택
- 보상, 퀘스트, 매칭, 운영 조치

LLM 실패, 비활성화, API key 누락, provider 오류, guardrail 실패는 API 실패로 전파하지 않는다.

## Provider 기본값

provider는 `groq`를 사용한다.

| purpose | model_id | timeout_seconds | temperature | max_output_tokens |
|---|---:|---:|---:|---:|
| `turn_flavor_text` | `llama-3.1-8b-instant` | 3 | 0.4 | 160 |
| `final_duel_dialogue` | `llama-3.3-70b-versatile` | 5 | 0.5 | 400 |
| `result_summary` | `llama-3.3-70b-versatile` | 5 | 0.4 | 500 |

실제 provider 호출에는 `LLM_API_KEY`가 필요하다.

## LLM 생성 로그

별도 테이블 `llm_generations`에 생성 시도 결과를 저장한다.

저장한다.

- purpose
- provider
- model_id
- status
- fallback_used
- generated_text
- match_id
- turn_id
- user_id
- metadata_json
- context_refs_json
- created_at

저장하지 않는다.

- prompt 원문
- provider raw response
- API key
- Authorization header
- cookie
- CSRF token

## 결과 요약

`GET /api/v1/matches/{match_id}/result`는 서버 판정 결과를 먼저 조립한 뒤 `result_summary`를 시도할 수 있다.

`MatchResult.llm_summary`는 아래 형태를 유지한다.

```json
{
  "enabled": true,
  "text": "LLM 보조 요약",
  "generation_id": "llm_generation_1"
}
```

실패 또는 비활성화 시에는 아래 형태를 유지한다.

```json
{
  "enabled": false,
  "text": null,
  "generation_id": null
}
```

화면 fallback은 `story_result_text`다.

## 턴 연출 문구 endpoint

별도 endpoint로 분리한다.

```text
POST /api/v1/matches/{match_id}/turns/{turn_id}/llm-text
```

성공 응답 data는 아래 형태다.

```json
{
  "llm_text": {
    "enabled": true,
    "purpose": "turn_flavor_text",
    "text": "짧은 연출 문구",
    "display_slot": "right_apparition_message",
    "fallback_used": false,
    "generation_id": "llm_generation_1",
    "context_refs": [],
    "metadata": {
      "status": "succeeded",
      "provider": "groq",
      "model_id": "llama-3.1-8b-instant"
    }
  }
}
```

LLM 실패 시 API는 성공시키고 `llm_text.enabled=false`, `llm_text.text=null`로 응답한다.

## 결전 대화 endpoint

별도 endpoint로 분리한다.

```text
POST /api/v1/matches/{match_id}/duel/dialogues
```

요청 body는 아래 필드를 사용한다.

```json
{
  "message": "플레이어 입력",
  "client_nonce": "uuid"
}
```

제약은 아래와 같다.

- `message`는 1자 이상 300자 이하
- match당 결전 대화 생성은 최대 8회
- 같은 match, 같은 사용자, 같은 `client_nonce` 요청은 기존 결과를 재사용
- 결전 대화는 별도 테이블 `duel_dialogues`에 저장
- 결전 대화는 게임 상태를 변경하지 않음

## Turn.started_at

`turns` 테이블에 `started_at`을 추가한다.

사용 목적은 `decision_duration_ms = action_submitted_at - turn.started_at` 계산이다.

기존 row migration 기본값은 `deadline_at - 25초`로 둔다.

API 응답에 `started_at`을 새로 노출하지 않는다.

## AI Profile

행동 이벤트는 매 턴 resolve 직후 저장한다.

MVP의 `stage_id`는 `1`로 고정한다.

`decision_duration_ms`는 서버가 계산한다.

스타일 스냅샷은 매 턴 resolve 직후 계산해 저장하고, 매치 종료 시 최종 재계산 결과를 다시 저장한다.

## RAG

RAG는 LLM context 보조로만 사용할 수 있다.

RAG는 서버 시작 시 자동 ingest하지 않는다.

RAG 검색 결과는 룰, 승패, 인증, 권한, 공식 단서, 진명 조각, 거짓 단서, 괴이 행동 선택을 바꿀 수 없다.

## Auth cookie path

`auth.logout`이 refresh cookie를 받을 수 있도록 refresh cookie path는 아래로 확대한다.

```text
/api/v1/auth
```

`auth.logout` 구현은 [[09_Approved_Contracts/20_Django_Auth_보안_계약]]의 logout refresh family revoke 정책을 따른다.
