---
title: "RAG 수동 Ingest/Search API 계약"
status: "approved"
type: "approved-rag-manual-ingest-search-api-contract"
source: "2026-06-10 user decision: 추천 확정안"
created: "2026-06-10"
updated: "2026-06-10"
---

# RAG 수동 Ingest/Search API 계약

이 문서는 [[09_Approved_Contracts/30_MVP_확장_1차_범위_계약]]의 RAG 수동 ingest/search API 구현 기준을 고정한다.

기존 [[09_Approved_Contracts/09_RAG_도입_기준]], [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]], [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]의 RAG 금지선은 계속 유효하다.

## 결정

RAG는 1차 확장에서 관리자 수동 API로만 ingest/search를 제공한다.

서버 시작, app import, migration, health check 중 자동 ingest는 구현하지 않는다.

검색 결과는 LLM context 보조 또는 운영 확인용 근거로만 사용한다. 검색 결과는 룰, 승패, 인증, 권한, 공식 단서, 진명 조각, 거짓 단서, 괴이 행동 선택을 변경할 수 없다.

## API

| 항목 | 값 |
|---|---|
| ingest endpoint | `POST /api/v1/retrieval/ingest` |
| search endpoint | `POST /api/v1/retrieval/search` |
| auth | access token HttpOnly cookie |
| 권한 | `accounts.User.is_staff=True` 사용자만 호출 가능 |
| CSRF | 두 endpoint 모두 필요 |
| response envelope | `{ data, meta }` / `{ error, meta }` |

권한 확인은 기존 `accounts.services.get_current_session()` 흐름을 재사용한다.

인증되지 않은 요청은 `AUTH_REQUIRED` 또는 `SESSION_EXPIRED`를 반환한다.

인증되었지만 staff가 아닌 요청은 `RAG_ACCESS_DENIED`를 반환한다.

## Ingest Request

```json
{
  "source_paths": ["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"],
  "force": false
}
```

| 필드 | 기준 |
|---|---|
| `source_paths` | 필수. 1개 이상 20개 이하 문자열 배열 |
| `force` | 선택. 기본값 `false` |

`source_paths`는 `/` 기준 상대 경로로 정규화한다.

상대 경로가 프로젝트 루트 밖으로 벗어나면 실패한다.

대상 파일은 기존 RAG allowlist를 통과해야 한다.

파일이 없거나 allowlist 밖이면 전체 ingest 요청을 실패시킨다.

`force=false`일 때 같은 `source_path`와 같은 `schema_version`의 문서가 이미 있으면 해당 문서는 skip한다.

`force=true`일 때 같은 `source_path`의 기존 document/chunk를 삭제하고 다시 생성한다.

## Ingest Response

```json
{
  "ingested_documents": 1,
  "ingested_chunks": 3,
  "skipped_documents": 0
}
```

## Search Request

```json
{
  "query": "결전 조건",
  "caller": "manual_admin",
  "top_k": 6,
  "score_threshold": 0.72
}
```

| 필드 | 기준 |
|---|---|
| `query` | 필수. trim 후 1자 이상 300자 이하 |
| `caller` | 필수. trim 후 1자 이상 80자 이하 |
| `top_k` | 선택. 기본값 `6`, 허용 범위 `1-20` |
| `score_threshold` | 선택. 기본값 `0.72`, 허용 범위 `0.0-1.0` |

## Search Response

```json
{
  "results": [
    {
      "document_id": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
      "chunk_id": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md:1",
      "source_path": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
      "score": 0.81,
      "text_excerpt": "..."
    }
  ],
  "top_k": 6,
  "score_threshold": 0.72
}
```

검색 결과가 없으면 `results`는 빈 배열이다.

검색 결과 payload는 공식 문서 경로와 chunk reference를 포함해야 한다.

반환된 각 결과는 `RetrievalQueryLog`에 기록한다.

## Embedding Adapter

`RAG_EMBEDDING_MODEL_ID`는 embedding 실행 시 필수다.

`RAG_EMBEDDING_PROVIDER` 기본값은 `disabled`다.

`RAG_EMBEDDING_PROVIDER=deterministic`은 local/test 검증용 adapter다.

`deterministic` adapter는 production 환경에서 사용할 수 없다.

외부 embedding provider 실호출은 이 계약의 1차 구현 범위에 포함하지 않는다.

provider가 `disabled`이거나 필수 설정이 없거나 production에서 `deterministic`을 사용하려 하면 `RAG_EMBEDDING_UNAVAILABLE`을 반환한다.

## Error Code

| code | status | 기준 |
|---|---:|---|
| `AUTH_REQUIRED` | 401 | access cookie 없음 |
| `SESSION_EXPIRED` | 401 | access token 만료 또는 user 조회 실패 |
| `CSRF_TOKEN_MISSING` | 403 | state-changing request에서 CSRF 누락 |
| `CSRF_TOKEN_INVALID` | 403 | CSRF 불일치 |
| `VALIDATION_ERROR` | 400 | request schema 검증 실패 |
| `RAG_ACCESS_DENIED` | 403 | staff가 아닌 사용자 |
| `RAG_SOURCE_NOT_ALLOWED` | 400 | allowlist 밖 source path |
| `RAG_SOURCE_NOT_FOUND` | 400 | source file 없음 |
| `RAG_EMBEDDING_UNAVAILABLE` | 503 | embedding provider/model 설정 사용 불가 |

## 구현 금지선

- RAG ingest/search는 서버 시작 중 자동 실행하지 않는다.
- RAG 검색 결과로 게임 판정 결과를 바꾸지 않는다.
- RAG 검색 결과로 공식 단서, 진명 조각, 거짓 단서를 생성하지 않는다.
- RAG 검색 결과로 인증/권한 정책을 변경하지 않는다.
- 이 계약에서는 외부 embedding provider 실호출을 구현하지 않는다.
