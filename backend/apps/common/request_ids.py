from collections.abc import Callable
from typing import Any
from uuid import uuid4

from django.http import HttpRequest, HttpResponse


REQUEST_ID_ATTRIBUTE = "request_id"
REQUEST_ID_RESPONSE_HEADER = "X-Request-ID"
REQUEST_ID_PREFIX = "req_"


def generate_request_id() -> str:
    return f"{REQUEST_ID_PREFIX}{uuid4().hex}"


def get_request_id(request: Any) -> str:
    request_id = getattr(request, REQUEST_ID_ATTRIBUTE, "")
    if isinstance(request_id, str) and request_id.strip():
        return request_id

    fallback_request_id = generate_request_id()
    setattr(request, REQUEST_ID_ATTRIBUTE, fallback_request_id)
    return fallback_request_id


class RequestIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.request_id = generate_request_id()
        response = self.get_response(request)
        response[REQUEST_ID_RESPONSE_HEADER] = request.request_id
        return response
