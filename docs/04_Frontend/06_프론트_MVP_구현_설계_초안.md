---
title: "프론트 MVP 구현 설계 초안"
status: "needs-decision"
type: "frontend-implementation-draft"
source: "[[09_Approved_Contracts/13_프론트팀_전달_기준]], [[09_Approved_Contracts/14_프론트팀_전달_패키지]], [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]"
created: "2026-06-02"
updated: "2026-06-02"
---

# 프론트 MVP 구현 설계 초안

이 문서는 프론트엔드 구현 착수 전 검토할 설계 초안이다.

현재 상태는 `needs-decision`이다. 아래 항목은 오너 승인 전까지 구현 확정 기준으로 사용하지 않는다.

프론트 기술 스택, route 기준, 폴더 구조, API client 기준, 인증/CSRF 연결 기준은 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]을 따른다.

## 설계 목표

1차 MVP 프론트는 사용자가 로그인한 뒤 `거울 속의 손님` 사건에 들어가고, 브리핑을 확인하고, 서버 판정형 의식 결투를 진행한 뒤, 결과를 확인할 수 있게 한다.

프론트는 화면 흐름과 표현을 담당한다. 룰, 수치, 단서, 봉인, 승패의 최종 권위는 서버에 있다.

## 기술 전제

기존 문서상 프론트 기술 후보는 `React + TypeScript + Vite`다.

아래 항목은 아직 확정이 필요하다.

| 항목 | 추천 후보 | 상태 |
|---|---|---|
| 라우팅 | React Router | approved |
| 서버 상태 관리 | 화면/feature 단위 API hook | approved |
| 클라이언트 UI 상태 | React local state와 Context | approved |
| 스타일 시스템 | CSS Modules | approved |
| API client | `fetch` 기반 wrapper | approved |
| 타입 생성 | 승인된 API 명세 이후 생성 검토 | decision_required |

## 화면 범위

MVP 프론트 화면 범위는 아래와 같다.

| 화면 | MVP | 목적 |
|---|---|---|
| 로그인 | 포함 | 계정 인증 |
| 회원가입 | 포함 | 신규 계정 생성 |
| 비밀번호 재설정 | 포함 | 계정 복구 |
| 로비 | 포함 | 모드 선택 |
| AI 사건 선택 | 포함 | `거울 속의 손님` 사건 진입 |
| 브리핑 | 포함 | 사건, 금기, 목표 안내 |
| 의식 결투 | 포함 | 행동 선택과 턴 결과 확인 |
| 결과 | 포함 | 승패, 최종 상태, 로그, 스타일 요약 표시 |
| 프로필 | 포함 | 전적과 기본 성향 확인 |
| PvP 매칭 | 제외 | 2차 이후 확장 |

## 추천 route 후보

아래 route는 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]에서 승인된 프론트 MVP route 기준이다.

| route | 화면 | 인증 |
|---|---|---|
| `/login` | 로그인 | 비로그인 |
| `/signup` | 회원가입 | 비로그인 |
| `/password-reset` | 비밀번호 재설정 | 비로그인 |
| `/lobby` | 로비 | 로그인 |
| `/story-cases` | AI 사건 선택 | 로그인 |
| `/story-cases/mirror-guest/briefing` | 브리핑 | 로그인 |
| `/matches/:matchId` | 의식 결투 | 로그인 |
| `/matches/:matchId/result` | 결과 | 로그인 |
| `/profile` | 프로필 | 로그인 |

`mirror-guest`는 1차 MVP의 프론트 route slug로 사용한다.

서버의 `case_id`는 `mirror_guest` 문자열을 사용한다.

## 추천 폴더 구조 후보

아래 구조는 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]에서 승인된 프론트 내부 책임 분리 기준이다.

```text
frontend/
  src/
    app/
      providers/
      router/
    routes/
      login/
      signup/
      password-reset/
      lobby/
      story-cases/
      briefing/
      match/
      result/
      profile/
    features/
      auth/
      story/
      match/
      result/
      profile/
    shared/
      api/
      types/
      ui/
      constants/
      errors/
```

구현 시 이 구조를 기준으로 한다.

## 화면별 설계 기준

### 로그인/회원가입

프론트는 cookie 기반 인증을 전제로 한다.

- access token과 refresh token을 직접 저장하거나 읽지 않는다.
- localStorage/sessionStorage에 token을 저장하지 않는다.
- 인증 요청은 `credentials: "include"` 또는 동등한 설정을 사용한다.
- state-changing request에는 CSRF header를 포함해야 한다.

확정 필요:

- CSRF token 발급 endpoint
- CSRF header 이름
- 401 응답 후 refresh 또는 session 확인 흐름
- 로그인 실패 error code와 사용자 문구

### 로비

로비는 로그인 후 사용자가 AI 스토리 모드로 진입하는 화면이다.

프론트팀 설계 대상:

- 모드 선택 표현 방식
- 프로필/전적 요약 진입 위치
- AI 사건 선택으로 이동하는 흐름

확정 필요:

- 로비에서 표시할 사용자 요약 데이터
- 프로필 요약 API 여부

### AI 사건 선택

MVP에서는 `거울 속의 손님`만 선택 가능하다.

프론트팀 설계 대상:

- 사건 제목, 요약, 상태 표시 방식
- 잠긴 사건 또는 제외 사건을 보여줄지 여부
- 브리핑 진입 CTA

확정 필요:

- 사건 목록 API 여부
- `거울 속의 손님` case id 또는 slug

### 브리핑

브리핑은 사건, 괴이 가칭, 금기, 목표를 전달한다.

프론트팀 설계 대상:

- 브리핑 화면 구성
- 금기 강조 방식
- 정보 대상 5개의 소개 방식
- 결투 시작 CTA

확정 필요:

- 브리핑 API 또는 정적 데이터 제공 방식
- 결투 시작 endpoint

### 의식 결투

의식 결투는 핵심 플레이 화면이다.

필수 표시 후보:

- 턴 번호와 제한 시간
- 현재 이성, 의식력, 저주 흔적
- 선택 가능한 행동
- 정보 행동에서 선택할 `info_target_key`
- 괴이 공개 상태
- 공개 로그
- 획득한 진명 조각
- 의심 단서 또는 거짓 단서 표시 영역
- 봉인 가능 상태

프론트팀 설계 대상:

- 행동 선택 패널
- 정보 대상 선택 UI
- 공개 로그 위치
- 단서 패널 접기/펼치기
- 서버 응답 대기 상태
- 제출 중 중복 클릭 방지 표현
- 턴 결과 반영 애니메이션

확정 필요:

- 전체 7x7 공개 로그
- 행동별 API request schema
- `info_target_key` 필수 행동 정책
- duplicate submit 처리 정책

확정된 timeout 정책:

- 브라우저 종료/네트워크 끊김은 즉시 시간초과로 확정하지 않는다.
- 서버 `deadline_at`까지 유효 제출이 없으면 시간초과로 처리한다.
- 재접속 또는 새로고침 후에는 최신 매치 상태를 조회한다.
- 상세 기준은 [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]을 따른다.

### 결과

결과 화면은 서버 판정 결과를 기준으로 표시한다.

필수 표시 후보:

- 승패
- 최종 이성
- 최종 저주 흔적
- 획득한 진명 조각
- 턴별 공개 로그
- 플레이 스타일 지표
- 정적 결과 문장
- LLM 요약 영역

LLM 요약은 없어도 화면이 완성되어야 한다.

확정 필요:

- 스타일 지표 표시 범위
- LLM 요약 표시 여부와 schema

## 상태 관리 경계

프론트가 직접 관리해도 되는 상태:

- 현재 route
- modal, panel, tab, accordion 같은 UI 상태
- 제출 버튼 disabled의 낙관적 표시
- 로딩, 에러, 재시도 UI
- 아직 서버에 제출하지 않은 form 입력값

프론트가 서버 응답으로만 확정해야 하는 상태:

- 현재 이성, 의식력, 저주 흔적
- 행동 가능 여부
- 턴 결과
- 단서 획득 여부
- 거짓 단서 공개 여부
- 봉인 가능 여부
- 승패
- 스타일 지표 최종값

## API client 기준 후보

프론트 API client는 아래 기능을 가져야 한다.

- 모든 request에 base URL 적용
- `credentials: "include"` 기본 적용
- state-changing request에 CSRF header 자동 포함
- `{ data, meta }` / `{ error, meta }` envelope 처리
- `error.code` 기반 사용자 문구 매핑
- 401, CSRF 실패, 중복 제출 실패를 구분 처리

확정 필요:

- API prefix
- CSRF token 저장 방식
- refresh 흐름
- error code 목록

## 오류 처리 기준 후보

| 상황 | 프론트 처리 후보 | 확정 필요 |
|---|---|---|
| 인증 만료 | session 확인 또는 refresh 후 재시도 | refresh endpoint |
| CSRF 실패 | token 재획득 후 사용자에게 재시도 안내 | CSRF error code |
| 중복 제출 | 같은 턴 제출 중임을 표시 | duplicate error code |
| 행동 불가 | 서버가 내려준 disabled reason 표시 | action error code |
| 매치 종료 | 결과 화면으로 이동 | match status |
| LLM 요약 실패 | 정적 결과 문장 표시 | llm summary schema |

## 모바일 대응 후보

모바일은 MVP 포함 여부와 최소 대응 수준을 확정해야 한다.

추천 후보:

- 모바일에서도 로그인, 사건 선택, 브리핑, 결투, 결과를 사용할 수 있게 한다.
- 결투 화면은 단서/로그 패널을 접기/펼치기 구조로 둔다.
- 행동 선택과 정보 대상 선택은 한 손 조작 가능한 영역에 둔다.
- 데스크톱 전용 hover 정보는 모바일에서 대체 표시를 제공한다.

decision_required:

- 최소 지원 viewport
- 가로/세로 모드 정책
- 모바일에서 동시 표시해야 하는 상태 항목

## 구현 착수 전 결정 목록

- React UI 스타일 시스템
- 라우팅 방식
- API client 방식
- 서버 상태 관리 방식
- 모바일 대응 범위
- 의식 결투 화면 최소 시각 표현
- error code 목록
- CSRF token 흐름
- 전체 7x7 공개 로그

API endpoint와 schema는 [[09_Approved_Contracts/15_프론트_기술_계약_오너_확정안]]과 [[09_Approved_Contracts/22_API_상세_Schema_계약]]에서 제공된다.

## 구현 착수 판단

이 문서는 프론트 구현 착수 기준이 아니다.

위 결정 목록이 승인되고 [[04_Frontend/99_Frontend_구현_확정]] 문서가 `implementation-ready`로 승격되어야 구현 기준으로 사용할 수 있다.
