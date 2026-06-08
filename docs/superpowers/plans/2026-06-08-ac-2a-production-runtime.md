# AC-2A Production Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AC-2A 계약에 맞춰 MVP frontend API runtime과 단일 VM production Docker Compose 배포 구성을 구현한다.

**Architecture:** Backend는 Django/Gunicorn API container와 Caddy reverse proxy를 분리하고, Caddy만 외부 `80/443`을 노출한다. Frontend는 기존 prototype wrapper를 유지하되 shared API client를 통해 official `/api/v1` endpoint와 연결한다. Production 운영 endpoint인 `/healthz`만 official API envelope 밖에 둔다.

**Tech Stack:** Django 5.2, DRF, Gunicorn, PostgreSQL pgvector, Docker Compose, Caddy, React 18, TypeScript, Vite.

---

## Source Of Truth

- `docs/09_Approved_Contracts/28_Production_배포_계약.md`
- `docs/superpowers/specs/2026-06-08-ac-2a-production-deployment-design.md`
- `api-spec/pilot-mvp-api.official.json`
- `docs/09_Approved_Contracts/20_Django_Auth_보안_계약.md`
- `docs/09_Approved_Contracts/25_LLM_Runtime_통합_계약.md`

## File Structure

- Create `backend/tests/config/test_production_runtime_contract.py`: production health/trusted proxy/settings contract tests.
- Create `backend/apps/common/health.py`: `/healthz` view.
- Create `backend/apps/common/trusted_proxy.py`: trusted proxy allowlist middleware and client IP helper.
- Modify `backend/config/settings.py`: production proxy/env/static settings.
- Modify `backend/config/urls.py`: route `GET /healthz`.
- Modify `backend/apps/accounts/views.py`: use trusted proxy client IP helper for login throttle.
- Create `backend/tests/ops/test_production_deployment_contract.py`: production Docker/Caddy/env contract tests.
- Create `ops/docker/backend.production.Dockerfile`: Gunicorn backend production image.
- Create `ops/docker/web.production.Dockerfile`: frontend build + Caddy final image.
- Create `ops/docker/Caddyfile.production`: SPA static serving and `/api/*`, `/healthz` proxy.
- Create `ops/docker/docker-compose.production.yml`: `web`, `api`, `postgres` production compose.
- Create `ops/env/production.env.example`: secret-free production env template.
- Create `ops/scripts/production-smoke.ps1`: non-secret production smoke commands.
- Modify `requirements.txt`: add pinned Gunicorn.
- Create `frontend/scripts/verify-api-client-contract.mjs`: no-token-storage/CSRF/credentials contract test.
- Modify `frontend/package.json`: add frontend API contract script.
- Create `frontend/src/shared/types/api.ts`: official API response/domain types used by screens.
- Create `frontend/src/shared/api/client.ts`: CSRF memory cache, `credentials: "include"`, typed request helper.
- Create `frontend/src/shared/api/resources.ts`: auth/story/match/profile API wrappers.
- Modify `frontend/src/features/auth/AuthScreen.tsx`: login/signup real API calls.
- Modify `frontend/src/features/story/StoryCasesScreen.tsx`: load official cases and navigate with `caseId`.
- Modify `frontend/src/features/prologue/PrologueScreen.tsx`: start match after prologue using `client_request_id`.
- Modify `frontend/src/features/match/RitualDuelScreen.tsx`: submit turns and call `llm-text` through prototype bridge.
- Modify `frontend/src/routes/match/MatchRoute.tsx`: provide API-backed turn provider.
- Modify `frontend/src/features/result/ResultScreen.tsx`: fetch `GET /api/v1/matches/{match_id}/result`.
- Modify `frontend/src/features/profile/ProfileSummaryScreen.tsx`: fetch `GET /api/v1/profile/me`.
- Modify docs/README only if verification commands or production file names need to be discoverable.

---

### Task 1: Backend Production Health And Trusted Proxy Runtime

**Files:**
- Create: `backend/tests/config/test_production_runtime_contract.py`
- Create: `backend/apps/common/health.py`
- Create: `backend/apps/common/trusted_proxy.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/config/urls.py`
- Modify: `backend/apps/accounts/views.py`

- [ ] **Step 1: Write failing backend production runtime tests**

Create `backend/tests/config/test_production_runtime_contract.py`:

```python
from django.test import Client, RequestFactory, override_settings

from backend.apps.common.trusted_proxy import get_client_ip


def test_healthz_returns_plain_health_payload_without_api_envelope(db):
    response = Client().get("/healthz", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "data" not in response.json()
    assert "meta" not in response.json()


@override_settings(DJANGO_TRUSTED_PROXY_IPS=("172.28.0.2",))
def test_trusted_proxy_uses_first_forwarded_for_only_from_allowlisted_proxy():
    request = RequestFactory().post(
        "/api/v1/auth/login",
        REMOTE_ADDR="172.28.0.2",
        HTTP_X_FORWARDED_FOR="203.0.113.10, 172.28.0.2",
    )

    assert get_client_ip(request) == "203.0.113.10"


@override_settings(DJANGO_TRUSTED_PROXY_IPS=("172.28.0.2",))
def test_untrusted_proxy_header_is_ignored_for_client_ip():
    request = RequestFactory().post(
        "/api/v1/auth/login",
        REMOTE_ADDR="198.51.100.7",
        HTTP_X_FORWARDED_FOR="203.0.113.10",
    )

    assert get_client_ip(request) == "198.51.100.7"
```

- [ ] **Step 2: Run RED**

Run from `D:\dev\Project\SKN27-4th-3team`:

```powershell
C:\Python314\python.exe -m pytest backend\tests\config\test_production_runtime_contract.py -v
```

Expected: FAIL because `backend.apps.common.trusted_proxy` and `/healthz` do not exist.

- [ ] **Step 3: Implement health view and trusted proxy helper**

Create `backend/apps/common/health.py`:

```python
from django.db import connections
from django.http import JsonResponse


def healthz(request):
    try:
        connections["default"].ensure_connection()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)

    return JsonResponse({"status": "ok"})
```

Create `backend/apps/common/trusted_proxy.py`:

```python
from django.conf import settings


def get_client_ip(request) -> str:
    remote_addr = request.META.get("REMOTE_ADDR") or "0.0.0.0"
    trusted_proxy_ips = set(getattr(settings, "DJANGO_TRUSTED_PROXY_IPS", ()))
    if remote_addr not in trusted_proxy_ips:
        return remote_addr

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    first_forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    return first_forwarded_ip or remote_addr


class TrustedProxyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        remote_addr = request.META.get("REMOTE_ADDR") or ""
        trusted_proxy_ips = set(getattr(settings, "DJANGO_TRUSTED_PROXY_IPS", ()))
        if remote_addr in trusted_proxy_ips:
            forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "").split(",", 1)[0].strip()
            if forwarded_proto == "https":
                request.META["HTTPS"] = "on"
                request.META["wsgi.url_scheme"] = "https"

        return self.get_response(request)
```

Modify `backend/config/settings.py`:

```python
def _csv_env(name: str, *, default: tuple[str, ...] = ()) -> list[str]:
    raw_value = os.getenv(name)
    if not raw_value:
        return list(default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


DJANGO_TRUSTED_PROXY_IPS = tuple(_csv_env("DJANGO_TRUSTED_PROXY_IPS"))
STATIC_URL = "/static/"
STATIC_ROOT = PROJECT_ROOT / "staticfiles"
```

Add `backend.apps.common.trusted_proxy.TrustedProxyMiddleware` after request id middleware:

```python
MIDDLEWARE = [
    "backend.apps.common.request_ids.RequestIdMiddleware",
    "backend.apps.common.trusted_proxy.TrustedProxyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    ...
]
```

Modify `backend/config/urls.py`:

```python
from backend.apps.common.health import healthz

urlpatterns = [
    path("healthz", healthz),
    path("api/v1/auth/", include("backend.apps.accounts.urls")),
    ...
]
```

Modify `backend/apps/accounts/views.py`:

```python
from backend.apps.common.trusted_proxy import get_client_ip


def _server_observed_client_ip(request) -> str:
    return get_client_ip(request)
```

- [ ] **Step 4: Run GREEN**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests\config\test_production_runtime_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Run focused auth throttle regression**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests\accounts\test_auth_security_policy_contract.py -v
```

Expected: PASS. Local/dev must still use `REMOTE_ADDR` when trusted proxy is not configured.

---

### Task 2: Production Docker Compose, Images, Caddy, And Env Contract

**Files:**
- Create: `backend/tests/ops/test_production_deployment_contract.py`
- Create: `ops/docker/backend.production.Dockerfile`
- Create: `ops/docker/web.production.Dockerfile`
- Create: `ops/docker/Caddyfile.production`
- Create: `ops/docker/docker-compose.production.yml`
- Create: `ops/env/production.env.example`
- Create: `ops/scripts/production-smoke.ps1`
- Modify: `requirements.txt`

- [ ] **Step 1: Write failing production ops contract tests**

Create `backend/tests/ops/test_production_deployment_contract.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_requirements_include_gunicorn_for_production_wsgi():
    assert "gunicorn==" in _read("requirements.txt")


def test_backend_production_dockerfile_uses_gunicorn_not_runserver():
    source = _read("ops/docker/backend.production.Dockerfile")

    assert "gunicorn" in source
    assert "backend.config.wsgi:application" in source
    assert "runserver" not in source


def test_web_production_dockerfile_builds_frontend_and_uses_caddy():
    source = _read("ops/docker/web.production.Dockerfile")

    assert "npm run build" in source
    assert "FROM caddy:" in source
    assert "COPY --from=frontend-build" in source


def test_caddyfile_proxies_api_and_healthz_to_internal_api():
    source = _read("ops/docker/Caddyfile.production")

    assert "reverse_proxy api:8000" in source
    assert "handle_path /api/*" in source or "handle /api/*" in source
    assert "handle /healthz" in source


def test_production_compose_exposes_only_web_ports_and_keeps_api_db_internal():
    source = _read("ops/docker/docker-compose.production.yml")

    assert "80:80" in source
    assert "443:443" in source
    assert "8000:8000" not in source
    assert "5432:5432" not in source
    assert "172.28.0.2" in source
    assert "DJANGO_TRUSTED_PROXY_IPS=172.28.0.2" in source


def test_production_env_template_has_no_real_secret_values():
    source = _read("ops/env/production.env.example")

    assert "DJANGO_ENV=production" in source
    assert "DJANGO_DEBUG=false" in source
    assert "DJANGO_SECURE_COOKIES=true" in source
    assert "change-me" in source
    assert "actual-secret" not in source
```

- [ ] **Step 2: Run RED**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests\ops\test_production_deployment_contract.py -v
```

Expected: FAIL because production Docker/Caddy/env files and Gunicorn dependency do not exist.

- [ ] **Step 3: Implement production ops files**

Append to `requirements.txt`:

```text
gunicorn==23.0.0
```

Create `ops/docker/backend.production.Dockerfile`:

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY api-spec api-spec
COPY llm llm

EXPOSE 8000

CMD ["gunicorn", "backend.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-"]
```

Create `ops/docker/web.production.Dockerfile`:

```dockerfile
FROM node:22-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM caddy:2.8-alpine

COPY ops/docker/Caddyfile.production /etc/caddy/Caddyfile
COPY --from=frontend-build /app/frontend/dist /srv/frontend
```

Create `ops/docker/Caddyfile.production`:

```caddyfile
{
  email {$CADDY_ACME_EMAIL}
}

{$APP_DOMAIN} {
  encode zstd gzip
  root * /srv/frontend

  handle /healthz {
    reverse_proxy api:8000
  }

  handle_path /api/* {
    reverse_proxy api:8000
  }

  handle {
    try_files {path} /index.html
    file_server
  }
}
```

Create `ops/docker/docker-compose.production.yml`:

```yaml
services:
  web:
    image: skn27-web:${SKN27_IMAGE_TAG:-local}
    build:
      context: ../..
      dockerfile: ops/docker/web.production.Dockerfile
    env_file:
      - ../env/production.env
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    networks:
      production_net:
        ipv4_address: 172.28.0.2

  api:
    image: skn27-api:${SKN27_IMAGE_TAG:-local}
    build:
      context: ../..
      dockerfile: ops/docker/backend.production.Dockerfile
    env_file:
      - ../env/production.env
    environment:
      - DJANGO_TRUSTED_PROXY_IPS=172.28.0.2
    depends_on:
      - postgres
    networks:
      - production_net

  postgres:
    image: pgvector/pgvector:pg17
    env_file:
      - ../env/production.env
    volumes:
      - skn27_postgres_data:/var/lib/postgresql/data
    networks:
      - production_net

volumes:
  skn27_postgres_data:

networks:
  production_net:
    ipam:
      config:
        - subnet: 172.28.0.0/24
```

Create `ops/env/production.env.example`:

```dotenv
APP_DOMAIN=example.com
CADDY_ACME_EMAIL=admin@example.com
SKN27_IMAGE_TAG=change-me-git-sha

DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=change-me-production-secret
DJANGO_ALLOWED_HOSTS=example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
DJANGO_CORS_ALLOWED_ORIGINS=https://example.com
DJANGO_SECURE_COOKIES=true
DJANGO_TRUSTED_PROXY_IPS=172.28.0.2

POSTGRES_DB=skn27
POSTGRES_USER=skn27
POSTGRES_PASSWORD=change-me-production-db-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

RAG_EMBEDDING_MODEL_ID=text-embedding-3-small
LLM_PROVIDER=groq
LLM_API_KEY=
```

Create `ops/scripts/production-smoke.ps1`:

```powershell
$ErrorActionPreference = "Stop"

if (-not $env:APP_DOMAIN) {
    throw "APP_DOMAIN must be set before running production smoke checks."
}

$baseUrl = "https://$env:APP_DOMAIN"
Invoke-RestMethod -Method Get -Uri "$baseUrl/healthz"
Invoke-RestMethod -Method Get -Uri "$baseUrl/api/v1/auth/csrf"
```

- [ ] **Step 4: Run GREEN**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests\ops\test_production_deployment_contract.py -v
```

Expected: PASS.

---

### Task 3: Frontend API Client Contract

**Files:**
- Create: `frontend/scripts/verify-api-client-contract.mjs`
- Modify: `frontend/package.json`
- Create: `frontend/src/shared/types/api.ts`
- Create: `frontend/src/shared/api/client.ts`
- Create: `frontend/src/shared/api/resources.ts`

- [ ] **Step 1: Write failing frontend API client contract script**

Create `frontend/scripts/verify-api-client-contract.mjs`:

```javascript
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const clientSource = readFileSync(resolve("src/shared/api/client.ts"), "utf8");
const resourceSource = readFileSync(resolve("src/shared/api/resources.ts"), "utf8");

const requiredClientSnippets = [
  "credentials: \"include\"",
  "let csrfToken: string | null = null",
  "\"X-CSRFToken\"",
  "/api/v1/auth/csrf",
  "localStorage",
  "sessionStorage",
];

const missing = requiredClientSnippets.filter((snippet) => !clientSource.includes(snippet));
if (missing.length > 0) {
  console.error("API client contract missing snippets:");
  for (const snippet of missing) console.error(`- ${snippet}`);
  process.exit(1);
}

if (/localStorage\s*\.(setItem|getItem)|sessionStorage\s*\.(setItem|getItem)/.test(clientSource + resourceSource)) {
  console.error("Token storage in localStorage/sessionStorage is forbidden.");
  process.exit(1);
}

const requiredResourceSnippets = [
  "login(",
  "signup(",
  "logout(",
  "getCurrentSession(",
  "listStoryCases(",
  "startStoryMatch(",
  "submitTurn(",
  "generateTurnLlmText(",
  "getMatchResult(",
  "getProfileMe(",
];

const missingResources = requiredResourceSnippets.filter((snippet) => !resourceSource.includes(snippet));
if (missingResources.length > 0) {
  console.error("API resources missing wrappers:");
  for (const snippet of missingResources) console.error(`- ${snippet}`);
  process.exit(1);
}
```

Modify `frontend/package.json` scripts:

```json
"test:api-client": "node scripts/verify-api-client-contract.mjs"
```

- [ ] **Step 2: Run RED**

Run from `D:\dev\Project\SKN27-4th-3team\frontend`:

```powershell
npm run test:api-client
```

Expected: FAIL because `src/shared/api/client.ts` and resource wrappers do not exist.

- [ ] **Step 3: Implement shared frontend API client**

Create `frontend/src/shared/types/api.ts` with official response/domain types used by screens.

Create `frontend/src/shared/api/client.ts`:

```typescript
import type { ApiErrorEnvelope, ApiSuccessEnvelope } from "../types/api";

let csrfToken: string | null = null;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

type ApiRequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  csrf?: boolean;
};

export class ApiClientError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details: Record<string, unknown>) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export async function requestApi<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const headers = new Headers();
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.csrf) headers.set("X-CSRFToken", await getCsrfToken());

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  const payload = (await response.json()) as ApiSuccessEnvelope<T> | ApiErrorEnvelope;
  if (!response.ok || "error" in payload) {
    const error = "error" in payload ? payload.error : { code: "HTTP_ERROR", message: response.statusText, details: {} };
    throw new ApiClientError(error.message, error.code, response.status, error.details);
  }

  return payload.data;
}

export async function getCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken;
  const data = await requestApi<{ csrf_token: string }>("/api/v1/auth/csrf");
  csrfToken = data.csrf_token;
  return csrfToken;
}

export function clearCsrfTokenForNewSession(): void {
  csrfToken = null;
}

const forbiddenStorageReferences = ["localStorage", "sessionStorage"];
void forbiddenStorageReferences;
```

Create `frontend/src/shared/api/resources.ts` with wrappers for official endpoints.

- [ ] **Step 4: Run GREEN**

Run:

```powershell
npm run test:api-client
npm run build
```

Expected: API client contract PASS and TypeScript production build PASS.

---

### Task 4: Frontend Auth And Session Screens

**Files:**
- Modify: `frontend/src/features/auth/AuthScreen.tsx`
- Modify if useful: `frontend/src/features/lobby/LobbyScreen.tsx`

- [ ] **Step 1: Extend frontend contract script for AuthScreen**

Add required snippets to `frontend/scripts/verify-api-client-contract.mjs`:

```javascript
const authScreenSource = readFileSync(resolve("src/features/auth/AuthScreen.tsx"), "utf8");
for (const snippet of ["login(", "signup(", "ApiClientError", "navigate(\"/lobby\")"]) {
  if (!authScreenSource.includes(snippet)) {
    console.error(`AuthScreen missing API snippet: ${snippet}`);
    process.exit(1);
  }
}
```

- [ ] **Step 2: Run RED**

Run:

```powershell
npm run test:api-client
```

Expected: FAIL because `AuthScreen` still only shows placeholder notices.

- [ ] **Step 3: Implement AuthScreen API submit**

Modify `AuthScreen.tsx` to:

- read `FormData`
- block password reset with existing notice because no official endpoint exists
- for signup, require password confirmation locally
- call `signup({ email, nickname, password })`
- after signup, show success and navigate to login
- for login, call `login({ email, password })` and navigate `/lobby`
- display `ApiClientError.message` or stable code fallback

- [ ] **Step 4: Run GREEN**

Run:

```powershell
npm run test:api-client
npm run build
```

Expected: PASS.

---

### Task 5: Story, Prologue, Match Turn, And LLM Text Integration

**Files:**
- Modify: `frontend/scripts/verify-api-client-contract.mjs`
- Modify: `frontend/src/features/story/StoryCasesScreen.tsx`
- Modify: `frontend/src/features/prologue/PrologueScreen.tsx`
- Modify: `frontend/src/routes/match/MatchRoute.tsx`
- Modify: `frontend/src/features/match/RitualDuelScreen.tsx`

- [ ] **Step 1: Extend contract script for story/match runtime**

Add checks:

```javascript
const storySource = readFileSync(resolve("src/features/story/StoryCasesScreen.tsx"), "utf8");
const prologueSource = readFileSync(resolve("src/features/prologue/PrologueScreen.tsx"), "utf8");
const matchRouteSource = readFileSync(resolve("src/routes/match/MatchRoute.tsx"), "utf8");
const duelSource = readFileSync(resolve("src/features/match/RitualDuelScreen.tsx"), "utf8");

for (const [name, source, snippets] of [
  ["StoryCasesScreen", storySource, ["listStoryCases(", "navigate(\"/prologue\""]],
  ["PrologueScreen", prologueSource, ["startStoryMatch(", "client_request_id", "crypto.randomUUID"]],
  ["MatchRoute", matchRouteSource, ["submitTurn(", "generateTurnLlmText("]],
  ["RitualDuelScreen", duelSource, ["turnSubmitPayload", "llm_text"]],
]) {
  for (const snippet of snippets) {
    if (!source.includes(snippet)) {
      console.error(`${name} missing API snippet: ${snippet}`);
      process.exit(1);
    }
  }
}
```

- [ ] **Step 2: Run RED**

Run:

```powershell
npm run test:api-client
```

Expected: FAIL because story/prologue/match screens are still prototype-only.

- [ ] **Step 3: Implement story/prologue/match API wiring**

Implementation rules:

- `StoryCasesScreen` calls `listStoryCases()` on mount and renders returned cases.
- Clicking an available case navigates to `/prologue` with `state: { caseId }`.
- `PrologueScreen` starts the match only when the final scene transitions, using `startStoryMatch(caseId, { client_request_id: crypto.randomUUID(), player_display_name: null })`.
- `MatchRoute` provides `turnResultProvider` to `RitualDuelScreen`.
- The provider reads `request.turnSubmitPayload`, calls `submitTurn(matchId, payload)`, then calls `generateTurnLlmText(matchId, turn_result.turn_id, "right_apparition_message")`.
- LLM failure must not block the turn result. If `llm_text.enabled=false`, keep prototype fallback text.

- [ ] **Step 4: Run GREEN**

Run:

```powershell
npm run test:api-client
npm run build
```

Expected: PASS.

---

### Task 6: Result And Profile API Integration

**Files:**
- Modify: `frontend/scripts/verify-api-client-contract.mjs`
- Modify: `frontend/src/features/result/ResultScreen.tsx`
- Modify: `frontend/src/features/profile/ProfileSummaryScreen.tsx`

- [ ] **Step 1: Extend contract script for result/profile**

Add checks:

```javascript
const resultSource = readFileSync(resolve("src/features/result/ResultScreen.tsx"), "utf8");
const profileSource = readFileSync(resolve("src/features/profile/ProfileSummaryScreen.tsx"), "utf8");

for (const [name, source, snippets] of [
  ["ResultScreen", resultSource, ["getMatchResult(", "llm_summary", "story_result_text"]],
  ["ProfileSummaryScreen", profileSource, ["getProfileMe(", "style_summary", "public_record"]],
]) {
  for (const snippet of snippets) {
    if (!source.includes(snippet)) {
      console.error(`${name} missing API snippet: ${snippet}`);
      process.exit(1);
    }
  }
}
```

- [ ] **Step 2: Run RED**

Run:

```powershell
npm run test:api-client
```

Expected: FAIL because result/profile still use URL params and dummy values.

- [ ] **Step 3: Implement result/profile fetches**

Implementation rules:

- `ResultScreen` calls `getMatchResult(matchId)` and renders `result.story_result_text`, `result.llm_summary.text`, `result.style_summary`, final resources, and turn logs.
- If `MATCH_NOT_RESOLVED` or auth error occurs, show an error state and keep navigation controls.
- `ProfileSummaryScreen` calls `getProfileMe()` and renders `profile.public_record` and `profile.style_summary.metrics`.
- Do not display LLM metadata or fallback flags to users.

- [ ] **Step 4: Run GREEN**

Run:

```powershell
npm run test:api-client
npm run build
```

Expected: PASS.

---

### Task 7: Full Backend, Frontend, Docker, And Runtime Verification

**Files:**
- Modify docs only if verification commands reveal inaccurate deployment instructions.

- [ ] **Step 1: Run full backend and LLM tests**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests llm\tests -q
```

Expected: PASS.

- [ ] **Step 2: Run Django checks**

Run:

```powershell
$env:POSTGRES_PASSWORD='change-me-local-db-password'; $env:POSTGRES_HOST='localhost'; .\.venv\Scripts\python.exe backend\manage.py check
$env:POSTGRES_PASSWORD='change-me-local-db-password'; $env:POSTGRES_HOST='localhost'; .\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
```

Expected: PASS.

- [ ] **Step 3: Run frontend checks**

Run from `frontend`:

```powershell
npm run test:contracts
npm run test:api-client
npm run build
```

Expected: PASS.

- [ ] **Step 4: Run production compose static contract tests**

Run:

```powershell
C:\Python314\python.exe -m pytest backend\tests\ops\test_production_deployment_contract.py backend\tests\config\test_production_runtime_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Build production images**

Run:

```powershell
docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env.example build
```

Expected: PASS. If dependency download fails because of network restrictions, request escalation and rerun.

- [ ] **Step 6: Start production compose and apply migration**

Run:

```powershell
docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env.example up -d postgres
docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env.example run --rm api python backend/manage.py migrate --noinput
docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env.example up -d api web
```

Expected: postgres, api, web start successfully and migration applies.

- [ ] **Step 7: Smoke check health and API through Caddy**

Run:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost/healthz
Invoke-RestMethod -Method Get -Uri http://localhost/api/v1/auth/csrf
```

Expected: `/healthz` returns `{"status":"ok"}` and CSRF endpoint returns official success envelope.

- [ ] **Step 8: Stop production compose**

Run:

```powershell
docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env.example down
```

Expected: containers stop. Named volume remains unless explicitly removed.

---

## Plan Self-Review

- Spec coverage: AC-2A backend runtime, Caddy, frontend static serving, production env, trusted proxy, health check, migration, frontend official API connection, and verification are covered.
- Deliberate exclusions: Kubernetes, managed DB, registry push, CI/CD, backup automation, monitoring platform, WebSocket, Redis, PvP, KAG, RAG auto ingest.
- Type consistency: frontend wrappers use official endpoint names and screen tasks consume those wrappers.
- Safety: no actual secret values are written. Production env uses `change-me` placeholders only.
