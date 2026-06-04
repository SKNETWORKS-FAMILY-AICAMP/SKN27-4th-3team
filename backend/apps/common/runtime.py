from collections.abc import Mapping
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from backend.apps.common.errors import make_api_error
from backend.apps.common.exceptions import ServiceNotImplementedError
from backend.apps.common.request_ids import get_request_id
from backend.apps.common.responses import error_envelope, success_envelope


def api_success_response(
    request: Any,
    data: Any,
    *,
    status_code: int = status.HTTP_200_OK,
    meta: Mapping[str, Any] | None = None,
) -> Response:
    return Response(
        success_envelope(data, request_id=get_request_id(request), meta=meta),
        status=status_code,
    )


def api_error_response(
    request: Any,
    code: str,
    *,
    status_code: int,
    details: Mapping[str, Any] | None = None,
    meta: Mapping[str, Any] | None = None,
) -> Response:
    api_error = make_api_error(code, details=details)
    return Response(
        error_envelope(api_error, request_id=get_request_id(request), meta=meta),
        status=status_code,
    )


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, ServiceNotImplementedError):
        return api_error_response(
            context.get("request"),
            "SERVICE_NOT_IMPLEMENTED",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details={"service": exc.service},
        )

    return drf_exception_handler(exc, context)
