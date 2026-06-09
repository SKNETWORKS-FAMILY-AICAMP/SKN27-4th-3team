---
title: "MVP Realtime Redis WebSocket 계약"
status: "approved"
type: "approved-mvp-realtime-redis-websocket-contract"
source: "2026-06-08 user decision: 1차 MVP WebSocket/Redis 포함, 미정 항목은 추천안 적용"
created: "2026-06-08"
updated: "2026-06-08"
supersedes: "Redis/WebSocket 1차 MVP 제외 기준 중 AI 스토리 상태 동기화 범위"
---

# MVP Realtime Redis WebSocket 계약

이 문서는 1차 MVP에 Redis와 WebSocket을 포함하기 위한 승인 기준이다.

기존 PvP 미사용 결정은 유지한다.

## 결정

1차 MVP에 Redis와 WebSocket을 포함한다.

단, 목적은 PvP가 아니라 AI 스토리 매치 화면의 상태 동기화와 사용자 체감 대기 시간 감소다.

| 항목 | 확정값 |
|---|---|
| WebSocket 목적 | AI 스토리 매치 상태 갱신 알림 |
| Redis 목적 | Django Channels channel layer |
| 권위 있는 상태 저장소 | PostgreSQL |
| 권위 있는 상태 변경 | 기존 REST API |
| PvP realtime | 제외 |
| Redis matchmaking | 제외 |
| WebSocket action submit | 제외 |
| token 저장 방식 | 기존 HttpOnly cookie 유지 |

## 핵심 원칙

WebSocket은 서버 판정 결과를 더 빨리 전달하기 위한 보조 경로다.

룰, 승패, 인증, 권한, 단서, 진명 조각, 거짓 단서, 괴이 행동 선택의 권위는 기존 서버 서비스와 PostgreSQL에만 있다.

Redis는 일시적인 이벤트 전달 계층이며 영구 저장소가 아니다.

Redis 장애가 발생해도 REST API로 매치 상세를 다시 조회하면 게임 진행은 복구 가능해야 한다.

## Backend 경계

별도 `backend.apps.realtime` 앱은 만들지 않는다.

AI 스토리 매치 상태 동기화는 `matches` 앱의 runtime 보조 기능으로 둔다.

| 파일 책임 | 기준 |
|---|---|
| WebSocket route | match 단위 endpoint만 제공 |
| Consumer | 인증, 참가자 권한 확인, group join, snapshot/event 전송 |
| Event publisher | turn resolve 이후 DB commit 완료 시 group event 전송 |
| Payload builder | REST 응답의 match/turn_result 구조를 재사용 |

## WebSocket Endpoint

1차 MVP WebSocket endpoint는 아래 하나만 둔다.

```text
GET /ws/matches/{match_id}
```

`match_id`는 REST API와 같은 public id 형식인 `match_<number>`를 사용한다.

인증은 기존 access token HttpOnly cookie를 사용한다.

URL query string, localStorage, sessionStorage, JavaScript 변수에 access token 또는 refresh token을 저장하거나 전달하지 않는다.

## Event Type

1차 MVP WebSocket event type은 아래로 제한한다.

| type | 방향 | 의미 |
|---|---|---|
| `match.snapshot` | server to client | 연결 직후 현재 match 상태 |
| `turn.resolved` | server to client | 턴 판정과 다음 match 상태 |
| `llm.text.ready` | server to client | 턴 연출 문구 생성 결과 |
| `result.ready` | server to client | 결말 조회 가능 상태 |
| `heartbeat` | server to client | 연결 유지 확인 |
| `error` | server to client | 인증, 권한, payload 오류 |

클라이언트가 WebSocket으로 행동 제출, 결전 제출, LLM 생성 요청을 보내는 기능은 1차 MVP에서 제외한다.

## Frontend 동작

프론트엔드는 match route 진입 시 WebSocket 연결을 시도한다.

WebSocket 연결이 성공하면 `match.snapshot`, `turn.resolved`, `llm.text.ready`, `result.ready` 이벤트로 화면 상태를 갱신한다.

WebSocket 연결이 실패하거나 끊기면 기존 REST API 조회와 수동 재시도 흐름으로 fallback한다.

프론트엔드는 WebSocket이 없어도 게임을 완주할 수 있어야 한다.

## Production 배포 기준

AC-2A 단일 VM + Docker Compose + Caddy + PostgreSQL 기준을 유지하고 Redis를 추가한다.

Backend runtime은 WebSocket을 처리할 수 있는 ASGI runtime이어야 한다.

기존 Gunicorn 운영 기준은 유지하되 WSGI app이 아니라 ASGI app을 실행한다.

```text
gunicorn backend.config.asgi:application --worker-class uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000
```

Caddy는 `/ws/*`, `/api/*`, `/healthz`를 내부 `api:8000`으로 proxy한다.

외부에 노출되는 포트는 계속 `web` 서비스의 `80`, `443`뿐이다.

`api`, `postgres`, `redis`는 Docker 내부 네트워크에서만 접근한다.

## Redis 운영 기준

| 항목 | 기준 |
|---|---|
| image | official Redis image |
| persistence | 1차 MVP 기본 비활성 또는 ephemeral |
| 외부 포트 노출 | 금지 |
| password | production에서는 환경변수로 주입 |
| source of truth | 금지 |

Redis에는 개인정보, refresh token, access token, 공식 게임 판정 원본을 저장하지 않는다.

## Env 기준

아래 환경 변수를 추가한다.

| 변수 | 기준 |
|---|---|
| `REDIS_URL` | Channels channel layer 접속 URL |
| `REDIS_PASSWORD` | production Redis password, repository 저장 금지 |
| `WEBSOCKET_HEARTBEAT_SECONDS` | heartbeat 주기 |
| `WEBSOCKET_CONNECT_TIMEOUT_SECONDS` | backend/runtime 기준 WebSocket 연결 대기 시간 기본값 |
| `VITE_WEBSOCKET_BASE_URL` | 선택값. 프론트 WebSocket origin override. 같은 origin 배포에서는 비워 둠 |
| `VITE_WEBSOCKET_CONNECT_TIMEOUT_SECONDS` | 프론트 WebSocket 연결 대기 시간 |

모든 값은 설정 또는 env로 주입한다.

코드에 Redis host, password, WebSocket URL, timeout 숫자를 magic number로 하드코딩하지 않는다.

프론트엔드는 같은 origin 배포를 기본값으로 삼고, API와 WebSocket origin이 분리되는 경우에만 `VITE_WEBSOCKET_BASE_URL`을 빌드 환경변수로 주입한다.

## 시간초과 계약과의 관계

AI 스토리 시간초과 판정은 계속 서버 `deadline_at` 기준이다.

WebSocket heartbeat, 브라우저 연결 상태, reconnect 여부는 승패나 시간초과 판정 근거가 아니다.

## 구현 금지선

- PvP 매칭 대기열을 만들지 않는다.
- Redis matchmaking을 만들지 않는다.
- WebSocket room을 PvP 대전 용도로 만들지 않는다.
- WebSocket message로 authoritative action submit을 처리하지 않는다.
- Redis를 DB 대체 저장소로 사용하지 않는다.
- Redis에 token 원문, token hash, 개인정보, 공식 판정 원본을 저장하지 않는다.
- WebSocket 연결 실패를 게임 패배나 시간초과로 판정하지 않는다.
- 프론트에 access token 또는 refresh token 저장소를 만들지 않는다.

## 관련 문서

- [[09_Approved_Contracts/19_PvP_미사용_및_구조_정리_계약]]
- [[09_Approved_Contracts/20_Django_Auth_보안_계약]]
- [[09_Approved_Contracts/21_AI_스토리_시간초과_판정_계약]]
- [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]
- [[09_Approved_Contracts/28_Production_배포_계약]]
