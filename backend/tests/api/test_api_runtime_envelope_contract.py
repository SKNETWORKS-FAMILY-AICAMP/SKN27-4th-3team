import os
import re
import uuid


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from rest_framework.test import APIClient

django.setup()

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{32}$")


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def test_rest_framework_uses_common_api_exception_handler():
    from backend.config import settings

    assert (
        settings.REST_FRAMEWORK["EXCEPTION_HANDLER"]
        == "backend.apps.common.runtime.api_exception_handler"
    )


def test_csrf_endpoint_returns_success_envelope_and_server_request_id_header():
    response = APIClient().get(
        "/api/v1/auth/csrf",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 200
    body = response.json()

    assert set(body) == {"data", "meta"}
    assert isinstance(body["data"]["csrf_token"], str)
    assert body["data"]["csrf_token"]
    assert "csrftoken" in response.cookies
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])
    assert body["meta"]["server_time"].endswith("Z")


def test_unimplemented_service_returns_501_error_envelope_with_stable_service_key():
    response = APIClient().post(
        "/api/v1/auth/login",
        {"email": "user@example.com", "password": "password"},
        format="json",
        HTTP_HOST="localhost",
        HTTP_X_REQUEST_ID="external-trace",
    )

    assert response.status_code == 501
    body = response.json()

    assert set(body) == {"error", "meta"}
    assert body["error"] == {
        "code": "SERVICE_NOT_IMPLEMENTED",
        "message": "Service is not implemented yet.",
        "details": {"service": "auth.login"},
    }
    assert body["meta"]["request_id"] == response["X-Request-ID"]
    assert body["meta"]["request_id"] != "external-trace"
    _assert_server_request_id(body["meta"]["request_id"])
