---
title: "RAG 검색 구조"
status: "approved"
type: "backend-detail"
source: "[[09_Approved_Contracts/09_RAG_도입_기준]], [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# RAG 검색 구조

이 문서는 1차 MVP의 `retrieval` 앱 구현 준비 기준이다.

RAG는 검색과 근거 로그를 담당한다.

RAG는 룰 판정, 승패, 인증, 권한, 진명 조각, 거짓 단서, 괴이 행동 선택을 변경하지 않는다.

## 앱 책임

| 책임 | 설명 |
|---|---|
| 문서 등록 | 승인된 문서 source를 등록한다. |
| chunk 생성 | 문서를 500-900자 단위로 나눈다. |
| embedding 저장 | chunk별 embedding을 저장한다. |
| 검색 | query embedding과 `pgvector` 검색을 수행한다. |
| query log | 검색 요청과 결과 근거를 저장한다. |

## 검색 대상

| source | 포함 여부 |
|---|---|
| `docs/09_Approved_Contracts` | 포함 |
| `docs/05_Story_Mode/02_거울_속의_손님.md` | 포함 |
| 승인된 게임 룰 문서 | 포함 |
| `docs/08_Implementation_Contracts` | 기본 제외 |
| `docs/07_Deferred` | 기본 제외 |
| LLM draft/prompt 초안 | 기본 제외 |

## 대상 테이블 초안

| 테이블 | 주요 필드 |
|---|---|
| retrieval_documents | id, source_path, title, status, content_hash, schema_version, created_at, updated_at |
| retrieval_chunks | id, document_id, chunk_id, content, token_count, char_count, embedding, schema_version, created_at |
| retrieval_query_logs | id, query, caller, top_k, threshold, created_at |
| retrieval_query_log_items | id, query_log_id, document_id, chunk_id, score, rank |

## Chunking 기준

- chunk 크기는 500-900자다.
- 문단 경계를 우선한다.
- overlap은 최대 100자다.
- chunk에는 `document_id`, `chunk_id`, `source_path`, `schema_version`을 저장한다.
- 동일 문서 재색인은 `content_hash`로 변경 여부를 확인한다.

## Embedding 기준

- Vector DB는 PostgreSQL + `pgvector`를 사용한다.
- embedding model id는 환경 설정으로 주입한다.
- 기본 추천값은 `text-embedding-3-small`이다.
- 모델 이름은 코드에 하드코딩하지 않는다.

## 검색 기본값

| 항목 | 확정값 |
|---|---|
| `top_k` | 6 |
| `score_threshold` | 0.72 |

검색 결과는 threshold 미만이면 제외한다.

## Query log

RAG query log는 최소 아래 항목을 저장한다.

- query
- caller
- document_id
- chunk_id
- score
- threshold
- top_k
- created_at

## 구현 금지선

- RAG 결과로 행동 상성표를 바꾸지 않는다.
- RAG 결과로 승패를 바꾸지 않는다.
- RAG 결과로 진명 조각 reveal condition을 바꾸지 않는다.
- RAG 결과로 거짓 단서 trigger condition을 바꾸지 않는다.
- RAG 결과로 괴이 행동 선택을 바꾸지 않는다.
- RAG 결과를 공식 설정 추가 근거로 사용하지 않는다.

## 남은 후속 항목

- query log 보존 기간
- LLM generation log와 retrieval log 연결 방식
