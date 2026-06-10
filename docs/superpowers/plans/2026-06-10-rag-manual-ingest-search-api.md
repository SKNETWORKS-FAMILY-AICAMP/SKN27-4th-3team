# RAG Manual Ingest/Search API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add staff-only manual RAG ingest/search API within the approved RAG boundary.

**Architecture:** Keep the API in `backend.apps.retrieval`. Views handle CSRF, session, staff authorization, serializers validate payloads, and services own ingest/search, source allowlist, deterministic local/test embedding, pgvector query, and query logging.

**Tech Stack:** Django 5.2, Django REST Framework, PostgreSQL pgvector, existing cookie auth service.

---

### Task 1: Contract And Official Schema

**Files:**
- Create: `docs/09_Approved_Contracts/32_RAG_Manual_Ingest_Search_API_怨꾩빟.md`
- Modify: `docs/09_Approved_Contracts/00_?뱀씤蹂?紐⑹감.md`
- Modify: `api-spec/pilot-mvp-api.official.jsonc`
- Modify: `api-spec/pilot-mvp-api.official.json`
- Test: `backend/tests/api/test_official_api_spec_contract.py`
- Test: `backend/tests/api/test_official_endpoint_routing_contract.py`

- [x] Add the approved contract document.
- [x] Add D-992 and the approved document link to the index.
- [x] Add official endpoint schema for `POST /api/v1/retrieval/ingest`.
- [x] Add official endpoint schema for `POST /api/v1/retrieval/search`.
- [x] Add RAG error codes.
- [x] Run `.\.venv\Scripts\python.exe -m pytest backend\tests\api -q` and verify the new tests fail before implementation routes exist.

### Task 2: Retrieval API Boundary

**Files:**
- Create: `backend/apps/retrieval/serializers.py`
- Create: `backend/apps/retrieval/views.py`
- Create: `backend/apps/retrieval/urls.py`
- Modify: `backend/config/urls.py`
- Test: `backend/tests/retrieval/test_retrieval_manual_api_contract.py`

- [x] Write failing tests for serializer classes, URL routing, CSRF requirement, and staff-only access.
- [x] Implement serializers for ingest/search request and response payloads.
- [x] Implement views that delegate to service functions.
- [x] Reuse `accounts.services.get_current_session()` and query `accounts.User` for `is_staff`.
- [x] Run the focused retrieval API tests and verify they pass.

### Task 3: Retrieval Services

**Files:**
- Modify: `backend/apps/retrieval/services.py`
- Test: `backend/tests/retrieval/test_retrieval_manual_runtime_contract.py`

- [x] Write failing tests for source path normalization, allowlist rejection, missing file rejection, deterministic embedding guard, ingest skip/force behavior, and query log creation.
- [x] Implement deterministic embedding only for non-production local/test when configured.
- [x] Implement `manual_ingest_sources`.
- [x] Implement `manual_search`.
- [x] Ensure no server startup auto ingest exists.
- [x] Run focused service tests and verify they pass.

### Task 4: Settings, Errors, And Verification

**Files:**
- Modify: `backend/config/settings.py`
- Modify: `backend/apps/common/errors.py`
- Modify: `ops/env/backend.env.example`
- Modify: `ops/env/production.env.example`
- Modify: `memory.md`

- [x] Add `RAG_EMBEDDING_PROVIDER`.
- [x] Add RAG API error messages.
- [x] Add env examples without enabling production deterministic provider.
- [x] Update project memory.
- [x] Run `.\.venv\Scripts\python.exe backend\manage.py check`.
- [x] Run `.\.venv\Scripts\python.exe -m pytest backend\tests -q`.
- [x] Run `Get-Content -Raw api-spec\pilot-mvp-api.official.json | ConvertFrom-Json`.
- [x] Run `git diff --check`.
