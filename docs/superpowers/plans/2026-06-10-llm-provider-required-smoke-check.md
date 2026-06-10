# LLM Provider Required Smoke Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an operational LLM provider smoke check that fails only when `LLM_REQUIRED=true`.

**Architecture:** Keep normal API fallback behavior unchanged. Add settings/env contract, a pure service-level smoke check in `backend.apps.llm.services`, and a Django management command that exits non-zero on required-mode failure.

**Tech Stack:** Django 5.2 management command, existing backend LLM service, existing top-level `llm.generation.adapter`.

---

### Task 1: Contract And Settings

**Files:**
- Create: `docs/09_Approved_Contracts/33_LLM_Provider_Required_Smoke_Check_怨꾩빟.md`
- Modify: `docs/09_Approved_Contracts/00_?뱀씤蹂?紐⑹감.md`
- Modify: `backend/config/settings.py`
- Modify: `ops/env/backend.env.example`
- Modify: `ops/env/production.env.example`
- Test: `backend/tests/config/test_project_contract.py`

- [x] Add the approved LLM provider smoke check contract.
- [x] Add D-993 and approved document link to the index.
- [x] Add `LLM_REQUIRED` with default `false`.
- [x] Document `LLM_REQUIRED=false` in local and production env examples.
- [x] Write and run a failing settings contract test.

### Task 2: Service Smoke Check

**Files:**
- Modify: `backend/apps/llm/services.py`
- Test: `backend/tests/llm/test_llm_required_smoke_check_contract.py`

- [x] Write failing tests for `LLM_REQUIRED=false`, missing API key failure, disabled failure, provider failure, and provider success.
- [x] Add `LlmSmokeCheckResult`.
- [x] Add `run_required_provider_smoke_check()`.
- [x] Use existing adapter without creating `LlmGeneration` rows.
- [x] Verify provider secrets, raw prompt, raw response, and Authorization header are not returned.

### Task 3: Management Command

**Files:**
- Create: `backend/apps/llm/management/__init__.py`
- Create: `backend/apps/llm/management/commands/__init__.py`
- Create: `backend/apps/llm/management/commands/llm_smoke_check.py`
- Test: `backend/tests/llm/test_llm_required_smoke_check_contract.py`

- [x] Write failing command tests for success and failure exit behavior.
- [x] Implement command output without secret values.
- [x] Keep `/healthz` unchanged.

### Task 4: Verification And Memory

**Files:**
- Modify: `memory.md`

- [x] Update project memory with the contract and implementation result.
- [x] Run `.\.venv\Scripts\python.exe backend\manage.py check`.
- [x] Run `.\.venv\Scripts\python.exe backend\manage.py llm_smoke_check` with default `LLM_REQUIRED=false`.
- [x] Run `.\.venv\Scripts\python.exe -m pytest backend\tests -q`.
- [x] Run `git diff --check`.
