---
title: "AC-2A Production Deployment Design"
status: "approved-by-user"
type: "deployment-design-spec"
source: "2026-06-08 user decision: AC-2A"
created: "2026-06-08"
updated: "2026-06-08"
---

# AC-2A Production Deployment Design

## 결정

AC-2A를 production 배포 방향으로 확정한다.

확정된 방향은 단일 VM + Docker Compose + Gunicorn + Caddy reverse proxy + PostgreSQL이다.

이 결정은 MVP runtime 완성 범위와 production 배포 준비 범위를 함께 다룬다. 프론트엔드는 official API와 연결하고, 백엔드는 production container runtime을 준비하며, 배포는 단일 VM에서 재현 가능한 수동 절차로 시작한다.

## 선택지 기록

| 옵션 | 내용 | 채택 여부 |
|---|---|---|
| A | MVP runtime 완성, 프론트 API 연결, Auth 보안, 문서 정리 | AC-2A에 포함 |
| C local/dev | Docker build와 local/dev 컨테이너 검증까지만 수행 | AC-2A에는 부족 |
| AC-2A | 단일 VM production 배포까지 확장 | 채택 |
| AC-2B | managed platform 또는 container platform | 미채택 |
| AC-2C | Kubernetes/cloud native 배포 | 미채택 |

## 구현 제약

- official API 외 endpoint를 임의로 추가하지 않는다. 예외는 운영 health check인 `GET /healthz`뿐이며, 이 endpoint는 product API envelope와 분리한다.
- frontend는 access token과 refresh token을 localStorage/sessionStorage에 저장하지 않는다.
- frontend API 호출은 HttpOnly cookie와 CSRF 정책을 전제로 `credentials: "include"`를 사용한다.
- production Django entrypoint는 `gunicorn backend.config.wsgi:application`이다.
- Django `runserver`는 local/dev 전용이며 production entrypoint로 사용하지 않는다.
- Caddy만 VM 외부 포트 `80`과 `443`에 노출한다.
- Django API `8000`과 PostgreSQL `5432`는 Docker 내부 네트워크에서만 사용한다.
- migration은 컨테이너 시작 시 자동 실행하지 않는다. 배포 절차의 명시 단계에서 실행한다.
- 실제 secret 값을 repository에 저장하지 않는다. repository에는 `.env.production.example`만 둔다.
- Caddy에서 온 요청만 trusted proxy로 취급한다. 임의 client가 보낸 `X-Forwarded-*` header는 신뢰하지 않는다.
- RAG 자동 ingest, KAG, PvP, WebSocket, Redis, Kubernetes, CI/CD 자동화, registry push, managed DB 전환은 이번 구현 범위에서 제외한다.

## 아키텍처

```text
Internet
  |
  | 80/443
  v
Caddy web container
  |-- serves frontend dist
  |-- reverse_proxy /api/* -> api:8000
  |-- reverse_proxy /healthz -> api:8000
  v
Gunicorn Django api container
  |
  v
PostgreSQL pgvector container
```

## 서비스 구성

| 서비스 | 이미지/런타임 | 책임 |
|---|---|---|
| `web` | Caddy final image | HTTPS, frontend 정적 파일 서빙, `/api/*`와 `/healthz` reverse proxy |
| `api` | Python slim + Gunicorn | Django API, Auth, Match, Story, LLM runtime boundary |
| `postgres` | `pgvector/pgvector:pg17` | PostgreSQL DB와 pgvector extension 기반 저장소 |

production image tag는 VM 내부 local image tag로 시작한다.

- `skn27-api:${SKN27_IMAGE_TAG}`
- `skn27-web:${SKN27_IMAGE_TAG}`

production 배포 시 `SKN27_IMAGE_TAG`는 git short SHA 또는 `YYYYMMDDHHMM` 형식 배포 태그를 사용한다. registry push는 이번 범위에 포함하지 않는다.

## Frontend 처리

`web` 이미지는 multi-stage build로 생성한다.

1. Node build stage에서 `frontend/` 의존성을 설치하고 `npm run build`를 실행한다.
2. Caddy final stage가 `frontend/dist`를 정적 파일로 복사한다.
3. SPA fallback은 API 경로를 제외하고 `index.html`로 처리한다.

Django static/media public serving은 이번 MVP production 구현 범위에서 제외한다. 사용자 업로드 media도 이번 범위에 없다.

## Backend 처리

`api` 이미지는 backend runtime용으로 구성한다.

- `requirements.txt`에 `gunicorn`을 추가한다.
- production command는 `gunicorn backend.config.wsgi:application --bind 0.0.0.0:8000`이다.
- local/dev compose는 기존처럼 command override로 `runserver`를 사용할 수 있다.
- API response envelope와 Auth cookie/CSRF 정책은 기존 official contract를 따른다.

## Env와 Secret

production env template은 `ops/env/production.env.example`에 둔다.

필수 계열은 아래와 같다.

- `APP_DOMAIN`
- `DJANGO_ENV=production`
- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_SECURE_COOKIES=true`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `DJANGO_TRUSTED_PROXY_IPS`

`LLM_API_KEY`는 실제 provider 호출이 필요할 때만 주입한다. 값이 없으면 승인된 LLM fallback 정책을 따른다.

## Trusted Proxy

production compose는 Caddy의 내부 proxy IP를 고정하거나, 그에 준하는 명시 allowlist를 제공한다.

기본 production compose는 Caddy 내부 IP를 `172.28.0.2`로 고정하고 `DJANGO_TRUSTED_PROXY_IPS=172.28.0.2`를 사용한다.

VM 네트워크와 충돌하면 compose network 대역과 `DJANGO_TRUSTED_PROXY_IPS`를 함께 변경한다.

Django는 `REMOTE_ADDR`가 allowlist에 포함된 경우에만 `X-Forwarded-For`와 `X-Forwarded-Proto`를 신뢰한다.

로그인 실패 rate limit의 client IP 계산도 이 정책을 따른다. local/dev에서는 기존처럼 `REMOTE_ADDR`만 사용한다.

## Health Check

운영 health check는 `GET /healthz`로 둔다.

- 인증 없음
- CSRF 없음
- product API envelope 없음
- 정상: HTTP 200, `{"status":"ok"}`
- 비정상: HTTP 503, `{"status":"unhealthy"}`

health check는 Django process와 DB connection을 확인한다. 상세 오류와 secret 값은 응답하지 않는다.

## Migration

production migration은 배포 절차에서 명시적으로 실행한다.

```powershell
docker compose -f ops/docker/docker-compose.production.yml run --rm api python backend/manage.py migrate --noinput
```

컨테이너 시작 command, Dockerfile entrypoint, Caddy 설정 안에서 migration을 자동 실행하지 않는다.

## 배포 절차

첫 production 배포는 수동 절차로 시작한다.

1. VM에 repository와 Docker Compose 환경을 준비한다.
2. 실제 production env 파일을 VM에만 배치한다.
3. production image를 build한다.
4. PostgreSQL을 기동한다.
5. migration을 명시적으로 실행한다.
6. `web`과 `api`를 기동한다.
7. `/healthz`와 핵심 API smoke check를 수행한다.
8. 문제가 있으면 이전 git ref와 이전 env 기준으로 되돌린다.

CI/CD 자동화와 image registry push는 이번 범위에서 제외한다.

## 검증 기준

- backend 전체 테스트 통과
- frontend contract test 통과
- frontend production build 통과
- Django `manage.py check` 통과
- Django `makemigrations --check --dry-run` 통과
- production compose build 통과
- production compose 기동 통과
- production migration apply 통과
- `/healthz` 200 확인
- frontend route와 `/api/v1` proxy smoke 확인

## 남은 운영 리스크

- VM provider, domain DNS 연결, 실제 TLS 발급은 환경 의존 작업이다.
- PostgreSQL backup 자동화는 이번 구현 범위가 아니다. production 배포 전 최소 수동 `pg_dump` 절차를 문서화한다.
- monitoring/log retention system은 이번 구현 범위가 아니다. 우선 Docker stdout/stderr와 VM 로그 관리 기준만 둔다.
- destructive migration rollback은 자동화하지 않는다. schema 변경 전 백업과 migration plan 확인을 필수로 둔다.
