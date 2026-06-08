import re
import os
import uuid

from django.http import HttpResponse
from django.test import RequestFactory


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{32}$")


def _assert_server_request_id(value: str) -> None:
    assert REQUEST_ID_PATTERN.fullmatch(value)
    assert uuid.UUID(hex=value.removeprefix("req_")).version == 4


def test_request_id_generator_uses_server_generated_uuid4_hex():
    from backend.apps.common.request_ids import generate_request_id

    request_ids = {generate_request_id() for _ in range(10)}

    assert len(request_ids) == 10
    for request_id in request_ids:
        _assert_server_request_id(request_id)


def test_request_id_middleware_ignores_external_header_and_sets_response_header():
    from backend.apps.common.request_ids import REQUEST_ID_RESPONSE_HEADER, RequestIdMiddleware

    captured_request_id = None

    def get_response(request):
        nonlocal captured_request_id
        captured_request_id = request.request_id
        return HttpResponse("ok")

    request = RequestFactory().get("/api/v1/auth/csrf", HTTP_X_REQUEST_ID="external-trace")
    response = RequestIdMiddleware(get_response)(request)

    assert captured_request_id != "external-trace"
    _assert_server_request_id(captured_request_id)
    assert response[REQUEST_ID_RESPONSE_HEADER] == captured_request_id


def test_request_id_middleware_runs_before_proxy_and_security_middleware():
    from backend.config import settings

    assert settings.MIDDLEWARE[0] == "backend.apps.common.request_ids.RequestIdMiddleware"
    assert settings.MIDDLEWARE[1] == "backend.apps.common.trusted_proxy.TrustedProxyMiddleware"
    assert settings.MIDDLEWARE[2] == "django.middleware.security.SecurityMiddleware"


def test_get_request_id_uses_existing_request_value_or_creates_fallback():
    from backend.apps.common.request_ids import get_request_id

    request = RequestFactory().get("/api/v1/auth/csrf")
    request.request_id = "req_existing"
    assert get_request_id(request) == "req_existing"

    fallback_request = RequestFactory().get("/api/v1/auth/csrf")
    fallback_request_id = get_request_id(fallback_request)

    _assert_server_request_id(fallback_request_id)
    assert fallback_request.request_id == fallback_request_id
