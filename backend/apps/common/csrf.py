from typing import Any

from django.conf import settings
from django.http import JsonResponse

from backend.apps.common.errors import make_api_error
from backend.apps.common.request_ids import get_request_id
from backend.apps.common.responses import error_envelope


HTTP_403_FORBIDDEN = 403


def csrf_failure(request: Any, reason: str = "") -> JsonResponse:
    return JsonResponse(
        error_envelope(
            make_api_error(_csrf_error_code(request=request)),
            request_id=get_request_id(request),
        ),
        status=HTTP_403_FORBIDDEN,
    )


def _csrf_error_code(*, request: Any) -> str:
    if not request.COOKIES.get(settings.CSRF_COOKIE_NAME):
        return "CSRF_TOKEN_MISSING"
    if not _submitted_csrf_token(request=request):
        return "CSRF_TOKEN_MISSING"
    return "CSRF_TOKEN_INVALID"


def _submitted_csrf_token(*, request: Any) -> str | None:
    return request.META.get(settings.CSRF_HEADER_NAME) or request.POST.get("csrfmiddlewaretoken")
