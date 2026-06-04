---
title: "API Auth DB LLM RAG 결정 전 검토안"
status: "draft"
type: "backend-ai-pre-decision-review"
source: "[[pilot]], [[03_Backend/01_백엔드_앱_경계]], [[03_Backend/06_API_계약]], [[07_Deferred/02_RAG_후순위_설계]], [[07_Deferred/04_LLM_후순위_설계]]"
created: "2026-06-01"
updated: "2026-06-01"
---

# API Auth DB LLM RAG 결정 전 검토안

이 문서는 백엔드, 프론트엔드, LLM/RAG 작업자가 논의할 수 있도록 만든 결정 전 검토안이다.

상세 API 예시는 `api-spec/pilot-mvp-api.jsonc`에 있다. 이 예시는 확정 명세가 아니라 설명이 붙은 검토용 템플릿이다.

## 상태

- 이 문서는 구현 착수 기준이 아니다.
- 아래 구조, API, Auth, DB, LLM/RAG 항목은 모두 후보안이다.
- 사용자가 승인한 항목만 이후 공식 `docs` 문서와 `99_*_구현_확정` 문서로 옮긴다.
- 팀원이 바로 구현해야 하는 확정값으로 해석하면 안 된다.

## 핵심 원칙

- 서버가 게임 상태와 턴 결과의 최종 권위자다.
- 프론트엔드는 행동 의도만 제출한다.
- 백엔드는 비용, 턴 번호, 제출 가능 여부, 중복 제출, 승패, 로그를 검증한다.
- LLM은 전투 판정, 승패, 랭킹, 보상 계산을 하지 않는다.
- RAG는 세계관/사건 문서 검색과 문장 생성 보조로 제한하는 방안을 검토한다.
- MVP에서는 RAG/LLM 없이도 게임이 완주 가능해야 한다.

## 폴더 구조 후보

초기 구현 시 검토할 수 있는 한 가지 후보 구조다. 실제 폴더 구조는 백엔드/프론트 담당자가 검토한 뒤 확정한다.

```text
backend/
  config/
    settings/
    urls.py
    asgi.py
    wsgi.py
  apps/
    accounts/
    profiles/
    game_rules/
    matches/
    story/
    ai_profile/
    llm/
    retrieval/
    knowledge/
  tests/

frontend/
  src/
    app/
    routes/
    features/
      auth/
      lobby/
      story/
      match/
      result/
      profile/
    shared/
      api/
      types/
      ui/
      constants/

api-spec/
  pilot-mvp-api.jsonc
```

MVP 백엔드에서 실제 구현 우선순위가 높을 수 있는 앱 후보:

| 앱 | MVP | 책임 |
|---|---|---|
| accounts | 포함 | 회원가입, 로그인, 로그아웃, 토큰 갱신, refresh rotation |
| profiles | 포함 | 닉네임, 전적 요약, 스타일 요약 |
| game_rules | 포함 | 행동, 자원, 상성, 승패 조건의 결정적 규칙 |
| matches | 포함 | 매치, 참가자, 턴, 행동 제출, 결과 저장 |
| story | 포함 | AI 스토리 사건, 괴이, 단서, 금기, 브리핑 |
| ai_profile | 포함 | 행동 이벤트 저장, 스타일 지표 계산 |
| llm | 인터페이스 우선 | LLM adapter, 정적 fallback, 생성 로그 |
| retrieval | 인터페이스 우선 | RAG 검색 adapter, 문서 chunk 검색 |
| knowledge | 후순위 | KAG 노드/엣지 |

## API 기본 규칙 후보

prefix 후보:

```text
/api/v1
```

응답 형태 후보:

성공:

```json
{
  "data": {},
  "meta": {}
}
```

실패:

```json
{
  "error": {
    "code": "MATCH_NOT_FOUND",
    "message": "Match was not found.",
    "details": {}
  },
  "meta": {
    "request_id": "req_..."
  }
}
```

프론트 표시 문구는 `message`를 그대로 노출하지 않아도 된다. `code`를 기준으로 프론트 친화 문구를 매핑해도 된다.

## Auth 후보

MVP 인증 방식으로 검토할 후보:

- JWT access token + refresh token rotation
- access token 만료: 15분
- refresh token 만료: 14일
- refresh 요청마다 새 refresh token 발급
- 이전 refresh token은 즉시 폐기
- refresh token 재사용 감지 시 token family 전체 폐기
- refresh token 원문을 저장하지 않고 해시만 저장하는 방안
- localStorage/sessionStorage 저장을 피하는 방안

검토 후보:

| 항목 | 후보값 | 검토 이유 |
|---|---|---|
| refresh token 저장 | HttpOnly cookie | JS 접근을 막기 위함 |
| access token 전달 | 응답 body + 메모리 저장 | 프론트 개발 초기 단순화. localStorage/sessionStorage 저장은 피하는 방향 |
| CSRF | refresh/logout 등 cookie 의존 endpoint에 CSRF 적용 | cookie 기반 요청 보호 |
| 개발 환경 Secure cookie | 로컬 HTTP에서는 Secure 비활성 가능, 운영은 필수 | 로컬 개발 편의와 운영 보안 분리 |
| custom user model | 사용 후보 | 초기 결정 비용은 있지만 장기 확장에 안전할 수 있음 |

`decision_required`:

- access token을 body로 내려줄지, HttpOnly cookie로만 둘지 최종 확정 필요
- CSRF header 이름과 발급 endpoint 확정 필요

## DB 모델 경계 후보

아래는 논의용 모델 경계 후보다. 정확한 필드, 제약, 인덱스, 앱 분리는 후속 DB 설계에서 확정한다.

### accounts

- User
- RefreshTokenFamily
- RefreshToken
- AuthEvent

### profiles

- PlayerProfile
- PlayerMatchSummary

### story

- StoryCase
- Apparition
- Stage
- TrueNameFragment
- FalseClue
- StoryText

### matches

- Match
- MatchParticipant
- Turn
- ActionSubmission
- TurnResult
- MatchClueState

### game_rules

DB 저장보다 순수 함수와 룰 데이터 중심이다.

- action definitions
- matchup table
- resource constraints
- win/loss checkers
- probability calculators

### ai_profile

- PlayerBehaviorEvent
- PlayerStyleProfile
- AIStyleCounterPolicy

### llm

- LLMGenerationRequest
- LLMGenerationLog
- PromptTemplate
- StaticFallbackText

### retrieval

- RetrievalDocument
- RetrievalChunk
- RetrievalQueryLog

## 룰 엔진 후보 경계

`game_rules`를 외부 API나 DB에 직접 의존하지 않는 순수 함수 중심으로 둘지 검토한다.

입력:

- match state snapshot
- actor action
- opponent action
- random seed
- story rule context

출력:

- state delta
- public log
- private/debug log
- probability result
- clue delta
- win/loss candidate

`matches` 앱은 이 결과를 저장한다.

## LLM 사용 후보

LLM을 아래 작업에 사용하는 방안을 검토한다.

- 브리핑 변형 문장 생성
- 괴이 대사 후보 생성
- 결과 화면용 서사 요약
- 플레이 스타일 요약 문장
- 운영자용 사건 로그 요약

LLM을 아래 작업에 사용하지 않는 방안을 우선 검토한다.

- 행동 성공/실패 판정
- 이성/의식력/저주 흔적 계산
- 승패 결정
- 랭킹/보상 계산
- 플레이어에게 유리하거나 불리한 숨은 룰 변경
- RAG 검색 결과에 없는 사실을 공식 설정처럼 추가

MVP 검토 후보:

1. 정적 문구와 룰 기반 로그로 전체 게임 완주 가능하게 만든다.
2. `llm` 앱은 adapter interface와 fallback 구조만 준비한다.
3. 실제 LLM 호출은 `result_summary`, `style_summary`, `flavor_text`처럼 판정 이후 보조 텍스트부터 붙인다.

## RAG 사용 후보

RAG는 세계관 문서와 사건 문서를 검색해서 LLM에 근거를 제공하는 보조 시스템으로 검토한다.

RAG 검색 대상 후보:

- 세계관 기준 문서
- 사건 브리핑
- 괴이 설정
- 금기와 단서 설명
- 결과 문장 후보
- 공개 로그 문장 후보

RAG 검색 결과가 바꾸면 안 되는 것으로 검토할 항목:

- 서버 룰 판정 결과
- 승패 조건
- 행동 비용
- 상성표 결과
- 인증/권한 정책

MVP 검토 후보:

- 초기에는 RAG 없이 정적 데이터로 진행한다.
- `retrieval` 앱에는 나중에 붙일 interface만 설계한다.
- LLM 호출이 필요한 경우에도 검색 근거 문서 ID와 chunk ID를 로그에 남긴다.

## 프론트와 백엔드 연결 원칙 후보

프론트가 직접 계산해도 되는 것:

- 버튼 활성화의 낙관적 표시
- 타이머 UI
- 애니메이션
- 정적 카피 표시
- 서버 응답 기반 상태 렌더링

프론트가 직접 계산하지 않는 방향으로 검토할 것:

- 행동 비용 최종 검증
- 현재 턴 유효성
- 행동 중복 제출 여부
- 단서 획득 여부
- 봉인 가능 여부
- 승패
- 스타일 지표 최종 계산

## 미확정 항목

- 전체 7x7 행동 상성표 공식 통합본
- `거울 속의 손님` reveal/trigger condition
- API error code 전체 목록
- DB exact field list
- JSONField schema validation 방식
- access token 전달 최종 방식
- CSRF 세부 정책
- LLM provider
- embedding model
- RAG chunking 세부 규칙
