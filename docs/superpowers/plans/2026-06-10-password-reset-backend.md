# Password Reset Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved password reset backend endpoints from `docs/09_Approved_Contracts/31_Password_Reset_API_Schema_계약.md`.

**Architecture:** Extend the existing `accounts` app boundaries. Token creation/hash helpers live in `tokens.py`, persistent reset token and throttle state live in `models.py`, business rules live in `services.py`, HTTP request/response shape lives in serializers/views/urls, and official API/schema/error contracts stay in `api-spec` plus common error catalog tests.

**Tech Stack:** Django 5.2, Django REST Framework, PyJWT/HMAC helpers, Django console email backend for local/dev, pytest.

---

### Task 1: Official API And Error Contract

**Files:**
- Modify: `api-spec/pilot-mvp-api.official.jsonc`
- Modify: `api-spec/pilot-mvp-api.official.json`
- Modify: `backend/apps/common/errors.py`
- Modify: `backend/tests/api/test_official_api_spec_contract.py`
- Modify: `backend/tests/common/test_response_contract.py`

- [ ] **Step 1: Add a failing API schema test**

```python
def test_official_api_spec_includes_password_reset_contract_endpoints_and_errors():
    spec = json.loads(OFFICIAL_API_JSON.read_text(encoding="ascii"))
    endpoints = {
        endpoint["id"]: endpoint
        for endpoint in spec["endpoints"]
        if endpoint["id"].startswith("auth.password_reset.")
    }
    assert set(endpoints) == {
        "auth.password_reset.request",
        "auth.password_reset.confirm",
    }
```

- [ ] **Step 2: Run the schema test**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_official_api_spec_contract.py -v`

Expected: FAIL before schema update because password reset endpoints are missing.

- [ ] **Step 3: Add official endpoints and error codes**

Add `auth.password_reset.request`, `auth.password_reset.confirm`, and the four password reset error codes to both official schema files. Generate strict JSON with `ensure_ascii=True`.

- [ ] **Step 4: Sync common API error messages**

Add the same four error codes to `backend/apps/common/errors.py` so envelope generation accepts official password reset failures.

- [ ] **Step 5: Verify schema and error catalog**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\api backend\tests\common -v`

Expected: PASS.

### Task 2: Password Reset Storage And Token Helpers

**Files:**
- Modify: `backend/apps/accounts/models.py`
- Modify: `backend/apps/accounts/tokens.py`
- Create: `backend/apps/accounts/migrations/0004_passwordreset.py`
- Create: `backend/tests/accounts/test_password_reset_contract.py`

- [ ] **Step 1: Add failing model/helper tests**

Test that `PasswordResetToken` has `user_id`, `token_hash`, `requested_email`, `request_ip`, `created_at`, `expires_at`, and `used_at`, and that token helpers generate URL-safe raw token plus HMAC hash without exposing raw token in model fields.

- [ ] **Step 2: Run focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_contract.py -v`

Expected: FAIL because model/helper does not exist.

- [ ] **Step 3: Implement model and helpers**

Add `PasswordResetToken`, reset token security event constants, `new_password_reset_token()`, `hash_password_reset_token()`, and `email_hmac()`.

- [ ] **Step 4: Create migration**

Run: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts`

Expected: creates the next accounts migration for password reset token storage.

- [ ] **Step 5: Verify focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_contract.py -v`

Expected: PASS.

### Task 3: Password Reset Service

**Files:**
- Modify: `backend/apps/accounts/services.py`
- Modify: `backend/config/settings.py`
- Modify: `ops/env/backend.env.example`
- Modify: `ops/env/backend.production.env.example`
- Modify: `backend/tests/accounts/test_password_reset_runtime_contract.py`

- [ ] **Step 1: Add failing service tests**

Test request acceptance without account enumeration, active-user token creation, `email_hmac` SecurityEvent metadata, rate limiting, valid confirm password change, token used/expired/invalid errors, and refresh token family revoke.

- [ ] **Step 2: Run focused runtime tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_runtime_contract.py -v`

Expected: FAIL because service functions do not exist.

- [ ] **Step 3: Implement service functions**

Add `request_password_reset()` and `confirm_password_reset()` with token TTL 30 minutes, single-use handling, email backend check, password validation reuse, and refresh-token revoke.

- [ ] **Step 4: Verify focused runtime tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_runtime_contract.py -v`

Expected: PASS.

### Task 4: Password Reset API Runtime

**Files:**
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/views.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/tests/accounts/test_auth_api_contract.py`
- Create: `backend/tests/accounts/test_password_reset_api_contract.py`

- [ ] **Step 1: Add failing API tests**

Test URL routes, serializers, CSRF protection, no response body token, accepted request response, confirm success response, and official error envelope for invalid token.

- [ ] **Step 2: Run focused API tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_api_contract.py backend\tests\accounts\test_auth_api_contract.py -v`

Expected: FAIL because views/routes/serializers do not exist.

- [ ] **Step 3: Implement serializers, views, and routes**

Add request/response serializers, `PasswordResetRequestView`, `PasswordResetConfirmView`, and `password-reset/request`, `password-reset/confirm` URL patterns under `/api/v1/auth/`.

- [ ] **Step 4: Verify focused API tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\accounts\test_password_reset_api_contract.py backend\tests\accounts\test_auth_api_contract.py -v`

Expected: PASS.

### Task 5: Final Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run Django system checks**

Run: `.\.venv\Scripts\python.exe backend\manage.py check`

Expected: `System check identified no issues`.

- [ ] **Step 2: Run migration dry check**

Run: `.\.venv\Scripts\python.exe backend\manage.py makemigrations accounts --dry-run --check`

Expected: no pending model changes after migration file is created.

- [ ] **Step 3: Run backend tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests -q`

Expected: all backend tests pass.
