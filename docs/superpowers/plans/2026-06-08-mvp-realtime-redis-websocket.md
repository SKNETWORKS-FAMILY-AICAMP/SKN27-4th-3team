# MVP Realtime Redis WebSocket Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1차 MVP에 Redis/Channels/WebSocket을 포함해 AI 스토리 매치 상태를 실시간 동기화하되, REST API와 PostgreSQL이 계속 권위 있는 상태 변경 경로가 되게 한다.

**Architecture:** Redis는 Django Channels channel layer로만 사용하고, WebSocket은 `/ws/matches/{match_id}`에서 match snapshot과 서버 이벤트를 내려준다. Backend runtime은 production에서 Gunicorn ASGI worker를 사용하고, Caddy는 `/ws/*`, `/api/*`, `/healthz`를 내부 API로 proxy한다.

**Tech Stack:** Django 5.2, Django Channels, channels_redis, Gunicorn, uvicorn-worker, websockets, Redis, PostgreSQL/pgvector, React/Vite native WebSocket.

---

### Task 1: Contract Tests Update

**Files:**
- Modify: `backend/tests/config/test_project_contract.py`
- Modify: `backend/tests/ops/test_local_runtime_contract.py`
- Modify: `backend/tests/ops/test_production_deployment_contract.py`

- [ ] **Step 1: Write failing backend dependency/config contract tests**

Update `EXPECTED_REQUIREMENTS` to include `channels`, `channels_redis`, `uvicorn`, `uvicorn-worker`, `websockets`, and assert `channels` is installed while `backend.apps.realtime` remains forbidden.

```python
EXPECTED_REQUIREMENTS = {
    "Django": "5.2.14",
    "djangorestframework": "3.17.1",
    "gunicorn": "23.0.0",
    "uvicorn": "0.49.0",
    "uvicorn-worker": "0.4.0",
    "websockets": "16.0",
    "channels": "4.3.2",
    "channels_redis": "4.3.0",
    "PyJWT": "2.13.0",
    "jsonschema": "4.26.0",
    "pgvector": "0.4.2",
    "psycopg[binary]": "3.3.4",
}
```

- [ ] **Step 2: Verify RED**

Run: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py backend\tests\ops\test_local_runtime_contract.py backend\tests\ops\test_production_deployment_contract.py -q`

Expected: FAIL because requirements, compose, Dockerfile, and Caddy have not been updated yet.

- [ ] **Step 3: Write failing realtime unit/consumer tests**

Create `backend/tests/matches/test_match_realtime_contract.py` with tests for:

```python
def test_match_realtime_group_name_uses_public_match_id_without_raw_token():
    assert realtime.match_group_name(public_match_id="match_2") == "match.match_2"


def test_match_realtime_payload_reuses_rest_match_shape():
    event = realtime.build_match_snapshot_event(match={"match_id": "match_2"})
    assert event["type"] == "match.snapshot"
    assert event["match"] == {"match_id": "match_2"}
```

- [ ] **Step 4: Verify RED**

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_realtime_contract.py -q`

Expected: FAIL because `backend.apps.matches.realtime` does not exist yet.

### Task 2: Backend Runtime Foundation

**Files:**
- Modify: `requirements.txt`
- Modify: `backend/config/settings.py`
- Modify: `backend/config/asgi.py`
- Create: `backend/apps/matches/routing.py`
- Create: `backend/apps/matches/realtime.py`
- Create: `backend/apps/matches/consumers.py`

- [ ] **Step 1: Add pinned dependencies**

Add pinned `uvicorn`, `channels`, `channels_redis` to `requirements.txt`.

- [ ] **Step 2: Add Channels settings**

Add `channels` to `INSTALLED_APPS`, keep `backend.apps.realtime` absent, and define:

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WEBSOCKET_HEARTBEAT_SECONDS = int(os.getenv("WEBSOCKET_HEARTBEAT_SECONDS", "25"))
WEBSOCKET_CONNECT_TIMEOUT_SECONDS = int(os.getenv("WEBSOCKET_CONNECT_TIMEOUT_SECONDS", "6"))
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}
```

- [ ] **Step 3: Wire ASGI routing**

Update `backend/config/asgi.py` to route HTTP to Django and WebSocket to `backend.apps.matches.routing.websocket_urlpatterns`.

- [ ] **Step 4: Implement realtime helpers**

Create deterministic helper functions for group names and event payloads. These helpers must not touch Redis or the database directly.

- [ ] **Step 5: Implement match consumer**

Consumer accepts only authenticated match participants, sends `match.snapshot` after connect, joins the match group, and rejects unauthorized connections.

- [ ] **Step 6: Verify GREEN**

Run: `C:\Python314\python.exe -m pytest backend\tests\config\test_project_contract.py backend\tests\matches\test_match_realtime_contract.py -q`

Expected: PASS for config and helper/consumer contract tests.

### Task 3: Event Publishing From Existing REST Flow

**Files:**
- Modify: `backend/apps/matches/services.py`
- Modify: `backend/apps/matches/realtime.py`
- Modify: `backend/tests/matches/test_match_realtime_contract.py`

- [ ] **Step 1: Add failing publish-on-commit test**

Test that `submit_match_turn` schedules a `turn.resolved` event after DB commit and does not make Redis delivery part of the authoritative transaction.

- [ ] **Step 2: Verify RED**

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_realtime_contract.py -q`

Expected: FAIL because the publish hook is not called.

- [ ] **Step 3: Publish events after turn resolve**

Call a realtime publisher after `_resolve_and_persist_turn` builds `turn_result` and `match` response. Use `transaction.on_commit()` so WebSocket events are emitted only after DB commit.

- [ ] **Step 4: Handle Redis delivery failure explicitly**

Catch channel layer delivery errors inside the publisher, log them, and return without changing the REST response.

- [ ] **Step 5: Verify GREEN**

Run: `C:\Python314\python.exe -m pytest backend\tests\matches\test_match_realtime_contract.py backend\tests\matches -q`

Expected: PASS.

### Task 4: Ops Runtime

**Files:**
- Modify: `ops/docker/docker-compose.yml`
- Modify: `ops/docker/docker-compose.production.yml`
- Modify: `ops/docker/backend.Dockerfile`
- Modify: `ops/docker/backend.production.Dockerfile`
- Modify: `ops/docker/Caddyfile.production`
- Modify: `ops/env/backend.env.example`
- Modify: `ops/env/production.env.example`

- [ ] **Step 1: Add Redis service without external production port**

Local compose may expose Redis for developer diagnostics. Production compose must not expose `6379:6379`.

- [ ] **Step 2: Add REDIS_URL env**

Local default: `redis://redis:6379/0`. Production template uses placeholder password guidance without real secret.

- [ ] **Step 3: Switch production command to Gunicorn ASGI worker**

Use:

```text
gunicorn backend.config.asgi:application --worker-class uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000
```

- [ ] **Step 4: Proxy `/ws/*` in Caddy**

Add a Caddy handle for `/ws/*` to `reverse_proxy api:8000`.

- [ ] **Step 5: Verify ops contracts**

Run: `C:\Python314\python.exe -m pytest backend\tests\ops -q`

Expected: PASS.

### Task 5: Frontend WebSocket Client And Fallback

**Files:**
- Create: `frontend/src/shared/api/realtime.ts`
- Modify: `frontend/src/routes/match/MatchRoute.tsx`
- Modify: `frontend/package.json`
- Create: `frontend/scripts/verify-realtime-contract.mjs`

- [ ] **Step 1: Add failing frontend contract script**

The script must assert no token is read from `localStorage` or `sessionStorage`, WebSocket URL is derived from current origin, and REST fallback remains present.

- [ ] **Step 2: Verify RED**

Run: `npm run test:realtime-contract`

Expected: FAIL because realtime client does not exist.

- [ ] **Step 3: Implement native WebSocket client**

Create a small client that connects to `/ws/matches/${matchId}`, parses known event types, applies timeout from configuration, and exposes close/retry cleanup.

- [ ] **Step 4: Integrate MatchRoute**

On match route mount, connect WebSocket and update existing match state from `match.snapshot` and `turn.resolved`. If WebSocket fails, keep existing REST fetch/retry path.

- [ ] **Step 5: Verify frontend contracts and build**

Run: `npm run test:contracts`

Run: `npm run test:realtime-contract`

Run: `npm run build`

Expected: PASS.

### Task 6: End-To-End Verification And README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document local and production commands with Redis startup, WebSocket endpoint, fallback behavior, and AWS cost notes.

- [ ] **Step 2: Run backend tests**

Run: `C:\Python314\python.exe -m pytest backend\tests -q`

Expected: PASS.

- [ ] **Step 3: Run frontend tests/build**

Run from `frontend`: `npm run test:contracts`, `npm run test:api-client`, `npm run test:nameless-flow`, `npm run test:realtime-contract`, `npm run build`

Expected: PASS.

- [ ] **Step 4: Run production compose smoke**

Run: `docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env build`

Run: `docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env up -d postgres redis api web`

Run: `docker compose -f ops\docker\docker-compose.production.yml --env-file ops\env\production.env exec api python backend/manage.py check --deploy`

Run: `Invoke-RestMethod http://localhost/healthz`

Expected: containers start, health returns `{"status":"ok"}`. Production deploy warnings caused by placeholder env are recorded as remaining risk, not hidden.
