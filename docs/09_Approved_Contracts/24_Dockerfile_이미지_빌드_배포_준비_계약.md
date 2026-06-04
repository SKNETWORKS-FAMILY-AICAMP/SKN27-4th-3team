---
title: "Dockerfile 이미지 빌드 배포 준비 계약"
status: "approved"
type: "approved-dockerfile-deployment-readiness-contract"
source: "[[09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약]], [[09_Approved_Contracts/23_프로젝트_폴더_구조_계약]]"
created: "2026-06-04"
updated: "2026-06-04"
---

# Dockerfile 이미지 빌드 배포 준비 계약

이 문서는 Dockerfile 기반 백엔드 이미지 빌드와 Django 배포 준비를 언제 어떤 순서로 확정할지 정한다.

이 문서는 production 배포 구현값을 확정하지 않는다.

production 배포 구현은 이 문서의 결정 게이트를 통과한 뒤 별도 배포 계약으로 확정한다.

## 현재 확정 범위

| 항목 | 기준 |
|---|---|
| Dockerfile 위치 | `ops/docker/backend.Dockerfile` |
| Compose 위치 | `ops/docker/docker-compose.yml` |
| env template 위치 | `ops/env/backend.env.example` |
| 현재 Dockerfile 용도 | 로컬/dev 백엔드 이미지 빌드 시작점 |
| 현재 entrypoint | Django `runserver` |
| production entrypoint | 미확정 |
| 운영 배포 자동화 | 1차 MVP 구현 범위 제외 |

현재 Dockerfile은 production 배포 entrypoint로 간주하지 않는다.

## 결정 타이밍

### 지금 확정해야 하는 항목

아래 항목은 Dockerfile을 실제 이미지 빌드에 사용하기 전 확정한다.

| 항목 | 이유 |
|---|---|
| WSGI/ASGI 방향 | Dockerfile command와 runtime dependency에 직접 영향 |
| env 변수 이름과 secret 주입 원칙 | settings, env template, 배포 문서에 직접 영향 |
| health check endpoint 형태 | 컨테이너 기동 검증과 reverse proxy 기준에 영향 |
| migration 실행 원칙 | 컨테이너 시작 시 실행할지 별도 명령으로 둘지 결정 필요 |
| static/media 처리 책임 | Django image, reverse proxy, object storage 선택에 영향 |

이 단계에서는 구체 provider나 운영 플랫폼을 고정하지 않아도 된다.

다만 Dockerfile과 Django settings에 영향을 주는 방향은 먼저 정한다.

### 첫 컨테이너 배포 테스트 전에 확정할 항목

아래 항목은 staging 또는 team dev deploy 전에 확정한다.

| 항목 | 기준 |
|---|---|
| image tag 규칙 | 팀원이 같은 image를 재현할 수 있어야 한다. |
| DB 연결 방식 | 컨테이너에서 PostgreSQL 접속 기준을 고정한다. |
| `collectstatic` 실행 여부 | static 처리 방식과 연결한다. |
| migration 실행 방식 | 컨테이너 시작 자동 실행 또는 별도 명령 중 하나를 고른다. |
| health check 실패 기준 | container status와 배포 판단 기준을 분리하지 않는다. |
| 로그 출력 | 기본은 stdout/stderr로 둔다. |

이 단계의 목표는 production 공개가 아니라 컨테이너가 재현 가능하게 뜨는지 확인하는 것이다.

### production 공개 전에 확정할 항목

아래 항목은 외부 사용자에게 공개하기 전 확정한다.

| 항목 | 기준 |
|---|---|
| 배포 대상 환경 | cloud, VM, managed container, on-prem 중 하나를 명확히 한다. |
| image registry | push/pull 권한과 tag 보존 정책을 정한다. |
| reverse proxy | Django container 앞단의 routing 책임을 정한다. |
| TLS/domain | HTTPS, cookie Secure, CSRF trusted origin과 연결한다. |
| CI/CD 또는 수동 배포 절차 | 배포 실행자와 승인 흐름을 명확히 한다. |
| rollback 방식 | 실패 시 이전 image로 되돌리는 기준을 정한다. |
| 운영 secret 관리 | `.env` 파일 직접 배포, secret manager, host env 중 하나를 정한다. |
| backup/restore | PostgreSQL 데이터 보호 기준을 정한다. |
| monitoring/log retention | 장애 대응에 필요한 로그와 지표 보존 기준을 정한다. |

## 구현 게이트

| Gate | 목표 | 통과 기준 |
|---|---|---|
| Gate A | 문서 정렬 | 이 문서와 관련 계약에 미정 항목이 숨겨져 있지 않다. |
| Gate B | 이미지 빌드 검증 | `docker build -f ops/docker/backend.Dockerfile -t skn27-backend:local .` 또는 Compose build가 성공한다. |
| Gate C | 컨테이너 기동 검증 | Django container가 기동하고 health check 또는 `manage.py check`가 성공한다. |
| Gate D | DB runtime 검증 | PostgreSQL `pgvector` 컨테이너와 연결해 migration apply가 성공한다. |
| Gate E | staging 배포 검증 | staging/dev deploy에서 API, CSRF, cookie, DB 연결이 재현된다. |
| Gate F | production 배포 확정 | production 공개 전 항목이 별도 계약으로 확정된다. |

현재 구현은 Gate A와 Gate B 준비 단계에 있다.

Gate B 이후부터는 Docker image pull/build, 컨테이너 기동, DB 연결 같은 runtime 검증이 필요하다.

## 구현 금지선

- production WSGI/ASGI server를 문서 확정 없이 임의 선택하지 않는다.
- `runserver`를 production entrypoint로 확정하지 않는다.
- secret 실제값을 repository에 저장하지 않는다.
- migration을 컨테이너 시작 시 자동 실행할지 임의 결정하지 않는다.
- static/media 저장소를 임의 결정하지 않는다.
- reverse proxy, TLS, domain, registry, CI/CD를 임의 확정하지 않는다.

## 다음 문서화 대상

후속 production 배포 계약을 작성할 때는 아래 문서를 만든다.

- Django production runtime 계약
- Docker image tag와 registry 계약
- secret/env 주입 계약
- migration 실행 계약
- health check 계약
- reverse proxy와 TLS 계약
- 운영 배포 절차 계약
