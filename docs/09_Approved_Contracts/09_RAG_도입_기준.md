---
title: "RAG 도입 기준"
status: "approved"
type: "approved-rag-adoption-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# RAG 도입 기준

이 문서는 RAG 도입 단계에 대한 승인된 기준이다.

## 결정

RAG는 `retrieval` 앱 구현 준비 범위에 포함한다.

단, MVP 핵심 게임 흐름은 RAG 없이 완주 가능해야 한다.

## 적용 제약

- 초기 MVP 판정 흐름은 RAG에 의존하지 않는다.
- `retrieval`은 문서, chunk, embedding, 검색, query log 구조를 구현 준비 범위에 포함한다.
- 나중에 LLM 요약이나 세계관 문장 생성에 RAG 근거를 붙일 수 있게 문서 ID, chunk ID, query log 구조를 둔다.
- RAG 검색 결과는 룰, 승패, 인증, 권한, 진명 조각, 거짓 단서, 괴이 행동 선택을 바꾸지 않는다.

## 확정된 구현 기준

| 항목 | 확정값 |
|---|---|
| 검색 대상 | `docs/09_Approved_Contracts`, `docs/05_Story_Mode/02_거울_속의_손님.md`, 승인된 게임 룰 문서 |
| chunking | 500-900자, 문단 경계 우선, overlap 최대 100자 |
| vector DB | PostgreSQL + `pgvector` |
| embedding model | env/config 주입. 기본 추천값 `text-embedding-3-small` |
| `top_k` | 6 |
| `score_threshold` | 0.72 |
| query log | query, caller, document_id, chunk_id, score, threshold, top_k, created_at |

상세 기준은 [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]]을 따른다.

## 후속 설계 대상

- query log 보존 기간
- LLM generation log와 retrieval log 연결 방식
