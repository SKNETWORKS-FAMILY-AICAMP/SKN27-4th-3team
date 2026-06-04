---
title: "API 명세 관리 기준"
status: "approved"
type: "approved-api-spec-management-policy"
source: "[[08_Implementation_Contracts/03_오너_결정_워크시트]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# API 명세 관리 기준

이 문서는 API 명세 포맷과 관리 방식에 대한 승인된 기준이다.

## 결정

API 명세는 설명용 JSONC 원본과 도구용 strict JSON 생성본을 함께 관리한다.

## 파일 역할

| 파일 종류 | 역할 | 수정 방식 |
|---|---|---|
| `.jsonc` | 사람이 읽고 논의하는 원본. 상세 주석과 설명을 포함한다. | 사람이 직접 수정한다. |
| `.json` | 프론트 타입 생성, mock server, validation 등 도구 연동용 생성본. | JSONC 원본에서 생성한다. 직접 수정하지 않는다. |

## 적용 제약

- JSONC 원본에는 필드 의미, 호출 시점, 서버 책임, 프론트 주의사항을 충분히 설명한다.
- strict JSON 생성본에는 주석을 넣지 않는다.
- 생성본 JSON을 사람이 직접 수정하지 않는다.
- API 내용이 확정되기 전까지 생성본도 proposal/review 상태임을 표시한다.
- API 확정 후에는 승인본 명세를 별도 파일로 만든다.

## 확정된 파일명

| 파일 | 역할 |
|---|---|
| `api-spec/pilot-mvp-api.jsonc` | 논의용 draft |
| `api-spec/pilot-mvp-api.official.jsonc` | 승인된 API 원본 |
| `api-spec/pilot-mvp-api.official.json` | 도구용 strict JSON 생성본 |

## 아직 정해야 할 것

- JSONC에서 strict JSON을 생성하는 스크립트 위치와 명령어
- OpenAPI 변환 여부
