---
title: "RAG 후순위 설계"
status: "superseded"
type: "deferred-detail"
source: "[[pilot]]"
created: "2026-05-30"
updated: "2026-06-02"
---

# RAG 후순위 설계

이 문서는 과거 후순위 검토안이다.

RAG는 더 이상 1차 MVP에서 완전히 제외하지 않는다.

현재 승인 기준은 [[09_Approved_Contracts/09_RAG_도입_기준]], [[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]], [[03_Backend/07_RAG_검색_구조]]를 따른다.

## 승인본으로 이동된 설계

- 문서를 500-900자 단위 chunk로 분리한다.
- chunk마다 embedding을 저장한다.
- PostgreSQL pgvector로 유사도 검색한다.
- 기본 top_k는 6이다.
- LLM에는 source id와 chunk id를 함께 전달한다.

## 현재 후속 항목

- query log 보존 기간
- LLM generation log와 retrieval log 연결 방식
