---
title: "pilot"
status: "concept-and-technical-blueprint"
created: "2026-05-30"
updated: "2026-05-30"
tags:
  - game-design
  - technical-design
  - django
  - react
  - ai
  - rag
  - kag
  - pvp
---

# pilot

> 이 문서는 실제 구현 착수를 확정하는 문서가 아니다.  
> 목적은 **게임 디테일과 세부 기술 선택을 구현 직전 수준까지 구체화**해서, 나중에 진행 여부를 판단할 수 있게 만드는 것이다.

## 0. 현재 결론

**프로젝트 방향:** 초자연 공포 스릴러 미스터리 기반 1대1 실시간 턴제 심리전 웹 게임

**핵심 한 줄:**

> 저주받은 생존자가 괴이와 마주 앉아, 심문·의식·속임수·계약으로 괴이의 진명을 파헤치고 살아남는 1대1 심리전 게임.

**기술 한 줄:**

> React 웹 클라이언트, Django API/ASGI 서버, PostgreSQL, Redis, Django Channels, JWT access token + refresh token rotation, RDB 기반 KAG, PostgreSQL pgvector 기반 RAG, LLM 어댑터를 사용한다.

**중요 원칙:**

- 실제 현금, 환금성 재화, 사행성 결제는 넣지 않는다.
- LLM은 전투 판정, 승패, 랭킹, 보상 계산을 하지 않는다.
- 서버가 게임 상태와 턴 결과의 최종 권위자다.
- AI는 플레이어의 스타일을 학습하지만, 학습 결과는 정해진 룰과 패턴 선택 안에서만 사용한다.
- 온라인 모드는 실시간 턴제 PvP다.

---

## 1. 제품 정체성

### 1.1 장르

- 메인 장르: 1대1 실시간 턴제 심리전
- 서브 장르: 초자연 공포, 미스터리, 블러핑, 추리, 전략
- 플랫폼: 웹
- 클라이언트: React
- 백엔드: Django

### 1.2 플레이어 판타지

플레이어는 영웅이 아니다. 이미 저주에 걸린 생존자다.  
살아남기 위해 매일 밤 다른 괴이와 의식 결투를 벌인다.  
괴이는 죽여야 하는 몬스터가 아니라, 정체와 약점과 진명을 숨긴 초자연적 상대다.

플레이어는 다음 감정을 반복해서 느껴야 한다.

- 지금 괴이가 나를 속이고 있는가?
- 이 단서는 진짜인가, 함정인가?
- 지금 안전하게 방어해야 하는가, 위험한 계약을 해야 하는가?
- 내 플레이 습관을 괴이가 읽고 있는가?
- 이번 턴에 손해를 보더라도 진명 조각을 얻는 게 맞는가?

### 1.3 톤

- 공포 방향: 초자연 공포
- 표현 방식: 심리적 압박, 의식, 금기, 기억 왜곡, 불길한 대사
- 지양: 과도한 고어, 실제 도박 연출, 현금성 베팅, 선정적 연출
- 참고 감각:
  - 1대1 테이블 긴장감: Buckshot Roulette
  - 블러핑과 콜의 압박감: Liar's Bar
  - 어두운 1대1 테이블 연출: Inscryption
  - 괴이와 저주 중심 세계관: WORLD OF HORROR
  - 숨은 정보 2인 심리전: Good & Bad Ghosts

---

## 2. 게임 모드

### 2.1 AI 스토리 모드

AI 스토리 모드는 이 게임의 핵심 모드다.

플레이어는 스테이지마다 다른 괴이를 상대한다.  
각 괴이는 고유한 금기, 거짓 단서, 진명 조각, 카운터 패턴을 가진다.

목표는 단순히 괴이의 체력을 깎는 것이 아니다.

**AI 스토리 모드 승리 조건:**

- 괴이의 `진명 조각` 3개를 확보한다.
- 다음 턴에 조건부 행동 `봉인`을 선언한다.
- 봉인 턴에서 괴이의 방해를 넘기면 승리한다.

**AI 스토리 모드 패배 조건:**

- 플레이어의 `이성`이 0이 된다.
- `저주 흔적`이 5가 된 상태에서 계약 실패 또는 괴이의 저주를 맞는다.
- 제한 턴 안에 진명 조각을 확보하지 못한다.

AI 스토리 모드의 재미는 “괴이를 이긴다”보다 “괴이가 나를 점점 더 잘 읽는다”에 있다.

### 2.2 온라인 배틀 모드

온라인 배틀 모드는 실시간 턴제 PvP다.

두 플레이어는 서로 다른 저주받은 생존자로 매칭된다.  
세계관상 같은 의식장에 갇힌 생존자들이 서로의 비밀을 드러내거나 이성을 무너뜨려 탈출권을 얻는 구조다.

**PvP 승리 조건:**

- 상대의 `이성`을 0으로 만든다.
- 상대의 `비밀 노출도`를 3까지 올린다.
- 상대가 항복한다.
- 상대가 연결 종료 후 허용된 재접속 시간 안에 돌아오지 않는다.

**PvP 금지 방향:**

- 게임 내 재화를 실제 돈과 연결하지 않는다.
- 랭크 점수, cosmetic 보상, 기록 외에 경제적 가치를 주지 않는다.
- 블러핑의 스릴만 가져오고 도박 구조는 만들지 않는다.

---

## 3. 핵심 게임 루프

### 3.1 AI 스토리 루프

1. 플레이어가 사건을 선택한다.
2. 사건 브리핑을 받는다.
3. 괴이의 첫 단서와 금기 일부가 공개된다.
4. 1대1 의식 결투가 시작된다.
5. 매 턴 행동을 비공개 선택한다.
6. 서버가 양쪽 행동을 동시에 공개하고 결과를 계산한다.
7. 플레이어는 진짜 단서와 거짓 단서를 구분한다.
8. 진명 조각 3개를 모으면 봉인을 시도한다.
9. 승패 결과와 플레이 스타일 분석이 저장된다.
10. 다음 괴이는 저장된 플레이 스타일을 일부 반영한다.

### 3.2 PvP 루프

1. 로그인한 유저가 PvP 대기열에 입장한다.
2. 서버가 실력 또는 대기 시간 기준으로 상대를 매칭한다.
3. WebSocket 방이 생성된다.
4. 양쪽 플레이어가 초기 비밀을 받는다.
5. 매 턴 제한 시간 안에 행동을 선택한다.
6. 서버가 제출 상태를 검증한다.
7. 둘 다 제출하거나 시간이 끝나면 동시에 공개한다.
8. 서버가 결과를 계산하고 양쪽에 전송한다.
9. 승패 조건에 도달하면 매치가 종료된다.
10. 전적, 로그, 부정행위 의심 이벤트를 저장한다.

---

## 4. 기본 자원

### 4.1 공통 자원

| 자원 | 기본값 | 범위 | 설명 |
|---|---:|---:|---|
| 이성 | 12 | 0-12 | 0이 되면 패배한다. |
| 의식력 | 3 | 0-5 | 행동 비용으로 사용한다. 매 턴 시작 시 2 회복한다. |
| 저주 흔적 | 0 | 0-5 | 강한 행동 실패, 계약 실패, 괴이 공격으로 증가한다. |
| 비밀 노출도 | 0 | 0-3 | PvP에서 3이 되면 패배한다. |
| 진명 조각 | 0 | 0-3 | AI 스토리에서 3개를 모아야 봉인을 시도할 수 있다. |

### 4.2 보조 상태

| 상태 | 설명 |
|---|---|
| 공포 | 다음 턴 선택 시간이 줄거나 특정 행동 비용이 오른다. |
| 의심 | 상대의 간파 성공률이 오른다. |
| 금기 위반 | 괴이의 특수 패턴이 발동하는 조건이다. |
| 거짓 단서 | 단서처럼 보이지만 봉인에 도움이 되지 않는 정보다. |
| 보호막 | 다음 저주 피해를 줄인다. |

---

## 5. 턴 구조

### 5.1 턴 단계

한 턴은 서버 기준으로 다음 순서로 진행된다.

1. 턴 시작
   - 의식력 2 회복
   - 지속 상태 감소
   - 제한 시간 시작
2. 행동 선택
   - 각 플레이어 또는 괴이가 행동 1개를 비공개 선택
   - 제한 시간은 기본 25초
3. 제출 검증
   - 서버가 권한, 턴 번호, 비용, 상태, 중복 제출 여부를 검증
4. 동시 공개
   - 양쪽 행동을 공개
5. 결과 계산
   - 결정적 룰 엔진이 결과 계산
6. 로그 저장
   - 행동, 상태 변화, 단서 변화, 타임스탬프 저장
7. 승패 검사
   - 이성, 비밀 노출도, 진명 조각, 저주 흔적 검사
8. 다음 턴 또는 종료

### 5.2 시간 초과

시간 초과 시 기본 행동은 `침묵`이다.

단, 같은 매치에서 시간 초과가 2회 발생하면 다음 패널티를 적용한다.

- PvP: 이성 1 감소
- AI 스토리: 저주 흔적 1 증가

3회 이상 반복하면 다음을 적용한다.

- PvP: 항복 처리
- AI 스토리: 괴이가 즉시 강한 패턴을 사용

---

## 6. 기본 행동

초기 기본 행동은 6개다. `봉인`은 AI 스토리에서 조건을 만족했을 때만 열리는 특수 행동이다.

### 6.1 행동표 v0.1

| 행동 | 비용 | 기본 효과 | 강점 | 약점 |
|---|---:|---|---|---|
| 저주 | 2 | 상대 이성 2 감소 | 침묵, 계약을 압박 | 수호에 막힘, 속임수에 역이용 가능 |
| 수호 | 1 | 저주 피해 2 감소, 보호막 1 획득 | 저주 대응 | 침묵 상대로 손해, 간파에 정보 제공 |
| 간파 | 1 | 단서 판별 또는 상대 행동 성향 일부 확인 | 속임수 탐지, 진명 확보 | 속임수에 실패하면 거짓 단서 획득 |
| 속임수 | 1 | 거짓 단서 생성, 간파 방해 | 간파 카운터 | 저주에 취약 |
| 침묵 | 0 | 정보 공개 차단, 다음 턴 의식력 +1 | 수호 낭비 유도 | 저주에 취약 |
| 계약 | 3 | 성공 시 진명 조각 또는 비밀 노출도 +1 | 역전 가능 | 간파 또는 저주에 읽히면 큰 손해 |
| 봉인 | 2 | AI 스토리에서 괴이 봉인 시도 | 승리 조건 | 진명 3개 없으면 선택 불가 |

### 6.2 상성 규칙 v0.1

| 내 행동 | 상대 행동 | 결과 |
|---|---|---|
| 저주 | 수호 | 피해 0, 수호자 보호막 +1 |
| 저주 | 침묵 | 침묵자 이성 -2 |
| 저주 | 계약 | 계약자 이성 -2, 계약 실패 |
| 저주 | 속임수 | 속임수 사용자는 이성 -1, 공격자는 의심 +1 |
| 수호 | 간파 | 간파자가 수호 사용 사실을 확인, 진명 조각은 얻지 못함 |
| 간파 | 속임수 | 50% 확률로 거짓 단서 제거, 실패 시 거짓 단서 획득 |
| 간파 | 침묵 | 단서 획득 실패, 침묵자의 다음 행동 후보 2개 확인 |
| 속임수 | 간파 | 간파 실패 시 거짓 단서 1개 생성 |
| 침묵 | 수호 | 침묵자 의식력 +1, 수호자는 효과 없음 |
| 계약 | 침묵 | 계약 성공, 진명 조각 또는 비밀 노출도 +1 |
| 계약 | 간파 | 계약 실패, 계약자 저주 흔적 +2 |
| 계약 | 수호 | 계약 부분 성공, 계약자 저주 흔적 +1, 목표 진척 +1 |

### 6.3 확률 사용 원칙

확률은 최소화한다.  
심리전의 핵심은 운이 아니라 상대 의도를 읽는 데 있어야 한다.

허용되는 확률은 다음뿐이다.

- `간파` vs `속임수`의 거짓 단서 판별 확률
- 괴이별 특수 패턴의 발동 확률

모든 확률은 서버에서 계산하고, seed와 결과를 로그에 저장한다.

---

## 7. AI 스토리 모드 상세

### 7.1 스테이지 구조

각 스테이지는 하나의 괴이 사건이다.

스테이지 데이터는 다음을 가진다.

- 사건 제목
- 괴이 이름 또는 가칭
- 괴이 분류
- 의식장
- 금기
- 진짜 단서 3개
- 거짓 단서 2-4개
- 괴이 기본 행동 성향
- 플레이어 성향 카운터 규칙
- 시작 브리핑 문서
- 승리 후 기록 문서

### 7.2 괴이 예시 1: 거울 속의 손님

**컨셉:** 거울을 통해 사람의 기억을 훔치는 괴이.

**금기:** 같은 질문을 두 번 반복하면 안 된다.

**진명 조각:**

1. 깨진 거울의 뒷면에 남은 이름
2. 사라진 아이의 마지막 목소리
3. 플레이어가 잊어버린 자기 방 번호

**거짓 단서:**

- 거울을 깨면 끝난다.
- 불을 끄면 안전하다.
- 이름을 부르면 괴이가 약해진다.

**패턴:**

- 플레이어가 간파를 자주 쓰면 속임수 빈도 증가
- 플레이어가 방어적이면 침묵 후 계약 사용
- 플레이어가 계약을 자주 쓰면 간파 카운터 사용

### 7.3 괴이 예시 2: 우물 밑의 목소리

**컨셉:** 잃어버린 사람의 목소리로 유혹하는 괴이.

**금기:** 대답하면 안 되는 질문이 있다.

**진명 조각:**

1. 우물 벽에 거꾸로 새겨진 성
2. 물 위에 뜨는 검은 머리카락
3. 대답하지 않은 질문의 원문

**패턴:**

- 침묵을 자주 쓰는 플레이어에게 공포 누적
- 저주 위주 플레이어에게 수호 후 계약
- 속임수 위주 플레이어에게 간파 강화

### 7.4 괴이 예시 3: 문밖의 어머니

**컨셉:** 가족의 목소리와 기억을 모방해 문을 열게 만드는 괴이.

**금기:** 문밖의 존재에게 이름을 알려주면 안 된다.

**진명 조각:**

1. 문틈으로 들어온 손톱 조각
2. 어머니가 절대 쓰지 않던 말투
3. 오래전 사라진 집 주소

**패턴:**

- 플레이어가 위기 때 수호를 반복하면 침묵으로 턴 압박
- 플레이어가 빠르게 저주하면 가짜 약점 생성
- 플레이어가 늦게 선택하면 제한 시간 압박 강화

---

## 8. 플레이어 스타일 학습

### 8.1 저장할 행동 이벤트

매 턴 다음 정보를 저장한다.

- 유저 ID
- 모드
- 매치 ID
- 스테이지 ID
- 턴 번호
- 선택 행동
- 선택까지 걸린 시간
- 선택 당시 이성
- 선택 당시 의식력
- 선택 당시 저주 흔적
- 상대 행동
- 결과
- 획득 단서
- 단서가 진짜였는지 여부
- 승패

### 8.2 스타일 지표

| 지표 | 계산 방식 | 의미 |
|---|---|---|
| 공격성 | 저주 선택 수 / 전체 턴 수 | 직접 압박 선호도 |
| 방어성 | 수호 선택 수 / 전체 턴 수 | 안전 운영 선호도 |
| 정보 집착 | 간파 선택 수 / 전체 턴 수 | 단서 확인 선호도 |
| 기만성 | 속임수 선택 수 / 전체 턴 수 | 블러핑 선호도 |
| 위험 선호 | 계약 선택 수 / 전체 턴 수 | 고위험 선택 선호도 |
| 침묵 의존 | 침묵 선택 수 / 전체 턴 수 | 지연과 관망 선호도 |
| 위기 방어율 | 이성 4 이하에서 수호 선택 수 / 위기 턴 수 | 불리할 때 버티는 성향 |
| 위기 계약율 | 이성 4 이하에서 계약 선택 수 / 위기 턴 수 | 불리할 때 역전 시도 성향 |
| 늦은 선택률 | 제한 시간 70% 이후 제출 수 / 전체 턴 수 | 고민형 또는 시간 압박 취약성 |

### 8.3 AI 대응 방식

AI 괴이는 LLM이 자유롭게 행동하지 않는다.  
서버가 계산한 스타일 지표를 기반으로 행동 가중치를 조정한다.

예시:

| 플레이어 성향 | 괴이 대응 |
|---|---|
| 간파 과다 | 속임수와 거짓 단서 증가 |
| 계약 과다 | 간파와 저주 카운터 증가 |
| 수호 과다 | 침묵, 계약, 턴 제한 압박 증가 |
| 저주 과다 | 수호 후 반격 패턴 증가 |
| 속임수 과다 | 간파 성공률 증가 |
| 늦은 선택 많음 | 시간 압박형 괴이 등장 |

### 8.4 학습 데이터 보존 원칙

- 행동 로그는 RDB에 영구 저장한다.
- 스타일 지표는 원본 로그에서 재계산 가능해야 한다.
- LLM 요약은 보조 데이터로만 저장한다.
- 유저가 계정을 삭제하면 개인 식별 가능한 행동 로그도 삭제 대상이 된다.

---

## 9. 기술 아키텍처 결정

### 9.1 전체 구성

| 영역 | 결정 |
|---|---|
| 프론트엔드 | React + TypeScript + Vite |
| 백엔드 HTTP API | Django + Django REST Framework |
| 백엔드 실시간 | Django Channels + ASGI |
| RDB | PostgreSQL 18 |
| Vector 검색 | PostgreSQL + pgvector |
| 캐시/실시간 보조 | Redis 8 |
| 백그라운드 작업 | Celery + Redis broker |
| 인증 | JWT access token + refresh token rotation |
| 토큰 저장 | HttpOnly Secure SameSite 쿠키 |
| 배포 기본형 | Docker Compose 기반 시작, 이후 클라우드 분리 가능 |

### 9.2 선택 이유

**Django**  
인증, ORM, 보안, 관리자 기능, 마이그레이션, 테스트 인프라가 강하다. 게임 서버의 모든 판정이 서버 중심이어야 하므로 안정적인 백엔드 프레임워크가 필요하다.

**React**  
실시간 상태 변화가 많은 결투 화면, 로비, 매칭 대기 UI에 적합하다.

**Django Channels**  
HTTP만으로는 실시간 턴제 PvP를 처리하기 어렵다. WebSocket 연결, 방 단위 브로드캐스트, 연결 종료 처리가 필요하다.

**PostgreSQL**  
유저, 매치, 턴 로그, AI 학습 로그, KAG 관계, RAG 문서 청크를 일관성 있게 저장해야 한다.

**pgvector**  
별도 벡터 DB를 바로 도입하지 않고 PostgreSQL 안에서 RAG 검색을 시작할 수 있다. 초기 운영 복잡도를 줄인다.

**Redis**  
WebSocket channel layer, 매칭 대기열, rate limit, 턴 타이머, 임시 락에 필요하다.

**Celery**  
LLM 요약, 임베딩 생성, 플레이어 스타일 재계산 같은 비동기 작업을 HTTP 요청과 분리한다.

---

## 10. 인증과 보안

### 10.1 인증 방식

처음부터 JWT access token + refresh token rotation을 사용한다.

- access token 만료: 15분
- refresh token 만료: 14일
- refresh 요청마다 새 refresh token 발급
- 이전 refresh token은 즉시 폐기
- 재사용 감지 시 token family 전체 폐기
- refresh token은 DB에 원문 저장 금지
- refresh token은 해시로만 저장
- 토큰은 localStorage/sessionStorage에 저장하지 않음
- 쿠키는 HttpOnly, Secure, SameSite=Lax 또는 Strict

### 10.2 필수 보안 기능

- 회원가입
- 로그인
- 로그아웃
- 비밀번호 재설정
- 로그인 실패 rate limit
- refresh rate limit
- API rate limit
- CSRF 보호
- CORS 허용 origin 명시
- 인증 이벤트 로그
- 유저별 데이터 소유권 검증
- 매치 참가 권한 검증
- WebSocket 연결 인증
- 중복 행동 제출 방지
- 서버 권위형 판정

### 10.3 WebSocket 보안

- WebSocket 연결 시 access token 쿠키를 검증한다.
- 매치 참가자가 아니면 방 연결을 거부한다.
- 클라이언트는 행동 의도만 제출한다.
- 서버는 행동 비용, 턴 번호, 제출 가능 여부를 검증한다.
- 클라이언트가 보낸 결과 계산값은 무시한다.

---

## 11. 백엔드 모듈 설계

### 11.1 Django 앱 경계

| 앱 | 책임 |
|---|---|
| accounts | 회원가입, 로그인, JWT, refresh rotation, 비밀번호 재설정, 인증 이벤트 |
| profiles | 닉네임, 전적 요약, 공개 프로필 |
| game_rules | 행동, 자원, 상성, 승패 조건의 결정적 규칙 |
| matches | 매치, 참가자, 턴, 행동 제출, 결과 스냅샷 |
| realtime | WebSocket consumer, 방 관리, 매칭 대기열, 턴 타이머 |
| story | AI 스토리 스테이지, 괴이, 사건 진행도 |
| ai_profile | 플레이어 스타일 지표 계산과 저장 |
| knowledge | KAG 노드와 관계 관리 |
| retrieval | RAG 문서, 청크, embedding, 검색 |
| llm | LLM provider adapter, 프롬프트 템플릿, 생성 로그 |
| audit | 보안 이벤트, 부정행위 의심 로그, 운영 로그 |

### 11.2 핵심 원칙

- `game_rules`는 다른 앱의 DB 모델에 직접 강하게 묶이지 않도록 순수 함수 중심으로 둔다.
- `matches`는 `game_rules`의 결과를 저장한다.
- `realtime`은 상태를 직접 판정하지 않고 `matches` 서비스에 위임한다.
- `llm`은 `game_rules`를 호출하거나 수정하지 않는다.
- `retrieval`은 LLM 입력 컨텍스트를 제공하지만 판정에는 관여하지 않는다.

---

## 12. 데이터 모델 초안

### 12.1 인증

| 테이블 | 주요 필드 |
|---|---|
| users | id, username, email, password_hash, is_active, created_at |
| profiles | user_id, nickname, avatar_key, rating, wins, losses |
| refresh_token_families | id, user_id, family_id, revoked_at, created_at |
| refresh_tokens | id, family_id, jti, token_hash, expires_at, used_at, revoked_at |
| password_reset_tokens | id, user_id, token_hash, expires_at, used_at |
| auth_events | id, user_id, event_type, ip, user_agent, metadata, created_at |

### 12.2 매치

| 테이블 | 주요 필드 |
|---|---|
| matches | id, mode, status, winner_id, started_at, ended_at |
| match_participants | id, match_id, user_id, side, sanity, ritual_power, curse_marks, secret_exposure |
| turns | id, match_id, turn_number, status, deadline_at, resolved_at |
| action_submissions | id, turn_id, participant_id, action_code, submitted_at, client_nonce |
| turn_results | id, turn_id, result_json, public_log_json, private_log_json |

### 12.3 AI 스토리

| 테이블 | 주요 필드 |
|---|---|
| story_cases | id, title, summary, difficulty, status |
| apparitions | id, name, category, description, taboo, base_policy_json |
| stages | id, case_id, apparition_id, order, victory_condition_json |
| true_name_fragments | id, apparition_id, label, content, reveal_condition_json |
| false_clues | id, apparition_id, content, trigger_condition_json |
| player_story_progress | id, user_id, stage_id, status, attempts, completed_at |

### 12.4 AI 학습

| 테이블 | 주요 필드 |
|---|---|
| player_behavior_events | id, user_id, match_id, turn_id, action_code, context_json, result_json |
| player_style_profiles | id, user_id, aggression, defense, insight, deception, risk, silence, updated_at |
| ai_counter_profiles | id, user_id, apparition_id, counter_policy_json, generated_summary |

### 12.5 KAG

| 테이블 | 주요 필드 |
|---|---|
| knowledge_nodes | id, node_type, slug, title, body, metadata_json |
| knowledge_edges | id, source_id, target_id, relation_type, weight, metadata_json |

노드 타입:

- apparition
- curse
- taboo
- ritual_site
- incident
- memory
- true_name
- clue
- character

관계 타입:

- haunts
- bound_to
- reveals
- contradicts
- requires
- forbids
- mimics
- caused_by
- counters

### 12.6 RAG

| 테이블 | 주요 필드 |
|---|---|
| source_documents | id, title, document_type, source_path, checksum, created_at |
| document_chunks | id, document_id, chunk_index, content, metadata_json |
| chunk_embeddings | id, chunk_id, embedding, model_name, created_at |
| retrieval_logs | id, user_id, query, selected_chunk_ids, created_at |
| llm_generation_logs | id, user_id, purpose, prompt_hash, model_name, input_refs_json, output_text, created_at |

---

## 13. RAG 설계

### 13.1 목적

RAG는 LLM이 세계관을 즉흥적으로 지어내지 않게 하는 장치다.

사용처:

- 스테이지 시작 브리핑 생성
- 괴이 대사 생성
- 승리/패배 후 사건 기록 생성
- 플레이어 스타일 요약 생성
- 다음 괴이의 대응 설명 생성

### 13.2 검색 대상 문서

- 괴이 설정 문서
- 사건 문서
- 의식 규칙 문서
- 금기 문서
- 진명 조각 문서
- 과거 플레이 요약

### 13.3 검색 방식

- 문서를 500-900자 단위 chunk로 분리한다.
- chunk마다 embedding을 저장한다.
- PostgreSQL pgvector로 유사도 검색한다.
- KAG 필터를 먼저 적용하고, 그 결과 안에서 vector 검색한다.
- 기본 top_k는 6이다.
- LLM에는 source id와 chunk id를 함께 전달한다.

### 13.4 환각 방지

LLM 출력은 다음 규칙을 따른다.

- 검색된 문서에 없는 괴이 약점은 만들 수 없다.
- 승패 결과를 바꿀 수 없다.
- 플레이어에게 실제 판정 수치를 숨기거나 바꾸면 안 된다.
- 괴이 대사는 분위기를 만들 수 있지만, 룰 설명은 서버 데이터와 일치해야 한다.

---

## 14. KAG 설계

### 14.1 목적

KAG는 세계관의 관계를 명시적으로 관리한다.

예시:

- `거울 속의 손님`은 `깨진 거울`에 묶여 있다.
- `깨진 거울`은 `응시 금기`와 연결된다.
- `응시 금기`를 어기면 `기억 탈취`가 발동한다.
- `기억 탈취`는 `진명 조각 2`를 숨긴다.

### 14.2 RAG와의 관계

KAG는 검색 범위를 좁힌다.  
RAG는 좁혀진 범위 안에서 관련 문장을 찾는다.

예:

1. 현재 상대가 `거울 속의 손님`이다.
2. KAG에서 연결된 금기, 단서, 사건을 찾는다.
3. 관련 문서 chunk만 RAG 후보로 넘긴다.
4. vector 검색으로 가장 가까운 텍스트를 찾는다.
5. LLM이 해당 컨텍스트 안에서 대사나 브리핑을 만든다.

---

## 15. LLM 사용 설계

### 15.1 LLM이 하는 일

- 스테이지 브리핑 문장 생성
- 괴이 대사 생성
- 전투 결과 기록 문장 생성
- 플레이어 스타일 요약
- 다음 괴이가 플레이어를 어떻게 노릴지 설명

### 15.2 LLM이 하지 않는 일

- 행동 성공 여부 결정
- 피해량 계산
- 진명 조각 획득 여부 결정
- PvP 승패 결정
- 랭크 점수 계산
- 보상 지급
- 인증/권한 판단
- 매칭 판단

### 15.3 LLM 어댑터

초기에는 provider 독립 인터페이스를 둔다.

```text
LlmClient.generate(purpose, system_prompt, user_prompt, context_refs) -> LlmResult
```

저장할 로그:

- purpose
- model_name
- prompt_hash
- context_refs
- output_text
- latency_ms
- error_code

LLM 호출 실패 시:

- 게임 진행은 멈추지 않는다.
- 서버는 미리 작성된 fallback 문구를 사용한다.
- 실패 로그를 저장한다.

---

## 16. 실시간 PvP 설계

### 16.1 WebSocket 이벤트

클라이언트가 받는 이벤트:

| 이벤트 | 설명 |
|---|---|
| match.found | 매치 생성 완료 |
| match.state | 현재 공개 상태 전달 |
| turn.started | 새 턴 시작 |
| action.accepted | 내 행동 제출 인정 |
| action.locked | 양쪽 행동 제출 완료 |
| turn.resolved | 턴 결과 공개 |
| match.ended | 매치 종료 |
| opponent.disconnected | 상대 연결 끊김 |
| opponent.reconnected | 상대 재접속 |
| error | 검증 실패 또는 서버 오류 |

클라이언트가 보내는 이벤트:

| 이벤트 | 설명 |
|---|---|
| queue.join | 매칭 대기열 입장 |
| queue.leave | 매칭 대기열 이탈 |
| match.join | 매치 방 입장 |
| action.submit | 현재 턴 행동 제출 |
| match.surrender | 항복 |
| ping | 연결 유지 |

### 16.2 서버 검증

`action.submit` 수신 시 서버는 다음을 검증한다.

- 인증된 유저인가
- 매치 참가자인가
- 현재 턴이 맞는가
- 이미 제출하지 않았는가
- 선택 가능한 행동인가
- 의식력이 충분한가
- 제한 시간이 지나지 않았는가
- client_nonce가 중복되지 않았는가

---

## 17. 프론트엔드 화면 설계

### 17.1 MVP 화면

| 화면 | 목적 |
|---|---|
| 로그인 | 계정 인증 |
| 회원가입 | 신규 계정 생성 |
| 비밀번호 재설정 | 계정 복구 |
| 로비 | 모드 선택 |
| AI 사건 선택 | 스토리 모드 진입 |
| 브리핑 | 괴이와 사건 소개 |
| 의식 결투 | 핵심 플레이 화면 |
| PvP 매칭 | 실시간 상대 찾기 |
| 결과 | 승패, 로그, 스타일 분석 표시 |
| 프로필 | 전적과 기본 성향 확인 |

### 17.2 의식 결투 화면

화면 구성:

- 중앙: 괴이 또는 상대 실루엣
- 하단: 내 행동 선택 패널
- 좌측: 내 이성, 의식력, 저주 흔적
- 우측: 상대 공개 상태
- 상단: 턴 번호와 제한 시간
- 중앙 하단: 이번 턴 공개 로그
- 별도 패널: 획득 단서와 의심 단서

### 17.3 UI 톤

- 어두운 배경
- 고대 종이, 거울, 촛불, 붉은 실, 낡은 문 같은 소재
- 과도한 애니메이션보다 느린 긴장감
- 중요한 턴 결과는 짧고 강한 문장으로 표시
- 버튼은 명확하게 읽혀야 한다.

---

## 18. 운영과 배포 설계

### 18.1 로컬 개발 구성

- frontend: Vite dev server
- backend: Django ASGI server
- postgres: Docker container
- redis: Docker container
- worker: Celery worker

### 18.2 운영 기본 구성

- reverse proxy: Nginx 또는 cloud load balancer
- app server: ASGI server
- worker: Celery worker
- database: managed PostgreSQL
- redis: managed Redis
- static assets: CDN 또는 object storage

### 18.3 관측성

필수 로그:

- 로그인 성공/실패
- refresh token 재사용 감지
- WebSocket 연결/해제
- 매치 생성/종료
- 턴 제출/해결
- LLM 호출 성공/실패
- RAG 검색 결과
- 권한 없는 접근 시도

지표:

- 평균 매칭 시간
- 턴 시간 초과율
- WebSocket 연결 실패율
- LLM 평균 지연
- RAG 검색 지연
- PvP 중도 이탈률
- AI 스토리 클리어율

---

## 19. 개발 순서 제안

실제 구현을 진행한다면 순서는 다음이 안전하다.

1. 백엔드 프로젝트 골격
2. 인증/인가/JWT refresh rotation
3. 기본 프로필과 권한 검증
4. 결정적 game_rules 엔진
5. AI 스토리 단일 매치 저장 구조
6. React 기본 UI와 AI 결투 화면
7. 플레이어 행동 로그와 스타일 지표
8. 괴이 패턴 정책
9. WebSocket 기반 PvP 매치
10. Redis 매칭 대기열과 턴 타이머
11. KAG 데이터 모델
12. RAG 문서 검색
13. LLM 브리핑/대사/요약
14. 운영 로그와 부정행위 의심 로그
15. 배포 환경 구성

---

## 20. 구현 전 확정해야 할 마지막 항목

아래 항목은 구현 착수 직전에만 확정하면 된다.

- 게임 제목의 최종 이름
- 첫 MVP 괴이 3종의 최종 문장
- React UI 스타일 시스템
- LLM provider
- embedding model
- 운영 배포 서비스
- 랭크 점수 공식
- PvP 재접속 허용 시간

현재 문서 기준으로는 위 항목이 없어도 설계 검토는 가능하다.  
하지만 실제 구현 시에는 해당 항목을 별도 결정 문서로 고정해야 한다.

---

## 21. 공식 참고 자료

- Django 5.2 release notes: https://docs.djangoproject.com/en/dev/releases/5.2/
- Django installation FAQ: https://docs.djangoproject.com/en/dev/faq/install/
- React installation: https://react.dev/learn/installation
- Django Channels documentation: https://channels.readthedocs.io/en/stable/
- Channels channel layers: https://channels.readthedocs.io/en/2.x/topics/channel_layers.html
- Django REST Framework: https://www.django-rest-framework.org/
- PostgreSQL documentation: https://www.postgresql.org/docs/
- Redis 8.0 documentation: https://redis.io/docs/latest/develop/whats-new/8-0/
- pgvector: https://github.com/pgvector/pgvector
- Celery backends and brokers: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html

---

## 22. 최종 판정

이 기획은 구현 가능성이 있다.  
다만 성공 조건은 명확하다.

1. 전투 판정을 LLM에 맡기지 않는다.
2. 첫 버전은 룰을 작게 유지한다.
3. 공포 분위기보다 심리전의 읽기/속이기 구조를 먼저 검증한다.
4. 온라인 PvP보다 AI 스토리 단일 매치를 먼저 완성한다.
5. RAG/KAG/LLM은 핵심 룰이 작동한 뒤 붙인다.

가장 안전한 MVP는 다음이다.

> 로그인 가능한 웹사이트에서, 저주받은 생존자가 첫 괴이 `거울 속의 손님`과 1대1 의식 결투를 벌이고, 서버가 모든 턴을 판정하며, 행동 로그를 저장하고, 플레이 스타일 요약을 생성하는 버전.

이 MVP가 재미있으면 PvP와 RAG/KAG/LLM 확장을 진행할 가치가 있다.
