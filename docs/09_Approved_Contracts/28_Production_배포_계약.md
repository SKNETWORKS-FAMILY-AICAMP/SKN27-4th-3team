---
title: "Production 배포 계약"
status: "approved"
type: "approved-production-deployment-contract"
source: "2026-06-08 user decision: AC-2A"
created: "2026-06-08"
updated: "2026-06-08"
---

# Production 배포 계약

이 문서는 1차 MVP를 실제 production 환경에 배포하기 위한 구현 기준을 확정한다.

## 결정

AC-2A를 production 배포 기준으로 사용한다.

| 항목 | 확정값 |
|---|---|
| 배포 형태 | 단일 VM |
| 실행 구성 | Docker Compose |
| Backend runtime | Django + Gunicorn ASGI worker |
| Reverse proxy | Caddy |
| TLS | Caddy 자동 HTTPS |
| DB | Compose 내부 PostgreSQL `pgvector/pgvector:pg17` |
| Redis | Compose 내부 Redis channel layer |
| Frontend | Vite build 결과를 Caddy가 정적 서빙 |
| image tag | VM 내부 local image tag |
| 배포 절차 | 수동 배포 우선 |
| CI/CD | 이번 범위 제외 |
| image registry | 이번 범위 제외 |
| Kubernetes | 제외 |
| managed DB | 이번 범위 제외 |

## 서비스 구성

production Compose는 아래 서비스를 가진다.

| 서비스 | 책임 |
|---|---|
| `web` | Caddy reverse proxy, HTTPS, frontend 정적 파일 서빙 |
| `api` | Gunicorn ASGI worker 기반 Django API/WebSocket |
| `postgres` | PostgreSQL + pgvector 저장소 |
| `redis` | Django Channels channel layer |

`web`만 VM 외부 포트 `80`, `443`에 노출한다.

`api:8000`, `postgres:5432`, `redis:6379`는 Docker 내부 네트워크에서만 접근한다.

production image tag는 아래 기준을 따른다.

| 이미지 | tag 기준 |
|---|---|
| `skn27-api` | `skn27-api:${SKN27_IMAGE_TAG}` |
| `skn27-web` | `skn27-web:${SKN27_IMAGE_TAG}` |

production 배포의 `SKN27_IMAGE_TAG`는 git short SHA 또는 `YYYYMMDDHHMM` 형식 배포 태그를 사용한다.

registry push는 이번 구현 범위에서 제외한다.

## Backend runtime

production backend entrypoint는 아래 기준을 따른다.

```text
gunicorn backend.config.asgi:application --worker-class uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000
```

`runserver`는 local/dev 전용이다.

production에서 `runserver`를 사용하지 않는다.

WebSocket을 지원하기 위해 WSGI application이 아니라 ASGI application을 실행한다.

## Reverse proxy와 TLS

Caddy는 아래 책임을 가진다.

- HTTP에서 HTTPS로 연결 처리
- TLS 인증서 자동 발급과 갱신
- frontend 정적 파일 서빙
- `/api/*`를 Django API container로 proxy
- `/api/v1/ws/*`를 Django API container로 proxy
- `/healthz`를 Django API container로 proxy

domain은 실제 VM 환경변수로 주입한다.

repository에 실제 domain, TLS secret, 인증서 파일을 저장하지 않는다.

## Static과 Media

frontend 정적 파일은 Caddy final image가 서빙한다.

Django static public serving은 이번 MVP production 범위에서 제외한다.

사용자 업로드 media 기능도 이번 MVP production 범위에서 제외한다.

따라서 이번 production 구현에서 Django `collectstatic`을 필수 배포 단계로 두지 않는다.

## Env와 Secret

repository에는 production env template만 저장한다.

실제 secret 값은 VM에만 둔다.

필수 환경 변수는 아래와 같다.

| 변수 | 기준 |
|---|---|
| `APP_DOMAIN` | production domain |
| `DJANGO_ENV` | `production` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | production secret, repository 저장 금지 |
| `DJANGO_ALLOWED_HOSTS` | production domain allowlist |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://<APP_DOMAIN>` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | frontend와 API가 같은 origin이면 `https://<APP_DOMAIN>` |
| `DJANGO_SECURE_COOKIES` | `true` |
| `POSTGRES_DB` | production DB name |
| `POSTGRES_USER` | production DB user |
| `POSTGRES_PASSWORD` | production DB password, repository 저장 금지 |
| `POSTGRES_HOST` | `postgres` |
| `POSTGRES_PORT` | `5432` |
| `REDIS_URL` | `redis://redis:6379/0` 또는 password 포함 URL |
| `REDIS_PASSWORD` | production Redis password, repository 저장 금지 |
| `WEBSOCKET_HEARTBEAT_SECONDS` | WebSocket heartbeat 주기 |
| `WEBSOCKET_CONNECT_TIMEOUT_SECONDS` | 프론트 WebSocket 연결 대기 시간 |
| `DJANGO_TRUSTED_PROXY_IPS` | Caddy internal proxy IP allowlist |

`LLM_API_KEY`는 실제 LLM provider 호출을 사용할 때만 VM 환경에 주입한다.

`LLM_API_KEY`가 없거나 provider 오류가 발생하면 [[09_Approved_Contracts/25_LLM_Runtime_통합_계약]]의 fallback 정책을 따른다.

## Trusted Proxy

production에서는 Caddy에서 온 요청만 trusted proxy로 취급한다.

기본 production Compose는 Caddy 내부 IP를 `172.28.0.2`로 고정하고 `DJANGO_TRUSTED_PROXY_IPS=172.28.0.2`를 사용한다.

VM 네트워크와 충돌하면 compose network 대역과 `DJANGO_TRUSTED_PROXY_IPS`를 함께 변경한다.

Django는 `REMOTE_ADDR`가 `DJANGO_TRUSTED_PROXY_IPS`에 포함된 경우에만 `X-Forwarded-For`와 `X-Forwarded-Proto`를 신뢰한다.

그 외 요청의 `X-Forwarded-*` header는 무시한다.

로그인 실패 rate limit의 client IP 계산도 이 trusted proxy 정책을 따른다.

local/dev 환경은 기존처럼 `REMOTE_ADDR`만 사용한다.

## Health check

production health check endpoint는 아래와 같다.

```text
GET /healthz
```

이 endpoint는 product API가 아니므로 official `/api/v1` response envelope를 사용하지 않는다.

| 상태 | 응답 |
|---|---|
| 정상 | HTTP 200, `{"status":"ok"}` |
| 비정상 | HTTP 503, `{"status":"unhealthy"}` |

health check는 Django process와 DB connection을 확인한다.

응답에는 상세 DB 오류, secret, 내부 설정값을 포함하지 않는다.

## Migration

production migration은 명시 명령으로만 실행한다.

컨테이너 시작 시 migration을 자동 실행하지 않는다.

배포 절차의 migration 기준 명령은 아래와 같다.

```powershell
docker compose -f ops/docker/docker-compose.production.yml run --rm api python backend/manage.py migrate --noinput
```

migration 실행 전에는 `migrate --plan` 또는 그에 준하는 migration plan 확인을 수행한다.

destructive migration이 있는 경우 production 적용 전에 별도 승인과 DB backup이 필요하다.

## DB와 Backup

PostgreSQL 데이터는 production Compose named volume에 저장한다.

자동 backup system은 이번 구현 범위에 포함하지 않는다.

production 배포 전과 schema migration 전에는 최소 수동 `pg_dump` 절차를 문서화한다.

## Log와 Monitoring

application log는 stdout/stderr를 기본으로 한다.

첫 production 구현에서 별도 monitoring system, alerting, log retention platform은 구축하지 않는다.

운영자는 VM에서 `docker compose logs`와 host log 관리 정책으로 1차 장애 대응을 수행한다.

## 배포 절차

첫 production 배포는 수동 절차로 진행한다.

1. VM에 Docker와 Docker Compose를 준비한다.
2. repository를 VM에 배치한다.
3. 실제 production env 파일을 VM에만 작성한다.
4. production image를 build한다.
5. PostgreSQL container를 기동한다.
6. migration plan을 확인한다.
7. migration을 명시적으로 실행한다.
8. `redis`를 기동한다.
9. `api`와 `web` 서비스를 기동한다.
10. `/healthz`를 확인한다.
11. `/api/v1/auth/csrf`, `/api/v1/ws/matches/{match_id}`, frontend route smoke check를 수행한다.

## Rollback

첫 production 구현의 rollback은 수동 절차다.

- 이전 git ref를 기록한다.
- 이전 env 파일을 보존한다.
- schema migration 전에는 DB backup을 생성한다.
- 배포 실패 시 이전 git ref로 checkout 후 image를 rebuild하고 서비스를 재기동한다.

DB schema rollback 자동화는 이번 범위에 포함하지 않는다.

## 구현 범위

이번 AC-2A 구현에 포함한다.

- production Compose 파일
- Caddy 설정
- frontend build를 포함한 web image
- Gunicorn ASGI worker backend runtime
- production env template
- health check endpoint
- trusted proxy allowlist 처리
- production 배포 문서
- MVP frontend official API 연결
- Redis service
- WebSocket reverse proxy

이번 AC-2A 구현에서 제외한다.

- Kubernetes
- managed PostgreSQL 전환
- image registry push
- CI/CD 자동 배포
- backup 자동화
- monitoring/alerting platform
- PvP
- KAG
- RAG 서버 시작 자동 ingest

## 구현 금지선

- 실제 secret 값을 repository에 저장하지 않는다.
- production에서 `runserver`를 사용하지 않는다.
- Caddy를 거치지 않은 외부 요청을 Django API로 직접 노출하지 않는다.
- migration을 container startup에 숨겨 자동 실행하지 않는다.
- `X-Forwarded-*` header를 allowlist 없이 신뢰하지 않는다.
- frontend에 access token 또는 refresh token 저장소를 만들지 않는다.
- RAG, LLM, KAG가 룰, 승패, 인증, 권한, 공식 단서를 바꾸게 하지 않는다.
- Redis를 PostgreSQL 대체 저장소나 token 저장소로 사용하지 않는다.
- WebSocket으로 authoritative action submit을 처리하지 않는다.
