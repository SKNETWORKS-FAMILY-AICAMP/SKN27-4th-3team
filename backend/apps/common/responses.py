from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from backend.apps.common.errors import ApiError


REQUIRED_META_FIELDS = frozenset({"request_id", "server_time"})


def _format_server_time(server_time: datetime | None) -> str:
    value = datetime.now(timezone.utc) if server_time is None else server_time
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("server_time must be timezone-aware")
    utc_value = value.astimezone(timezone.utc).replace(microsecond=0)
    return utc_value.isoformat().replace("+00:00", "Z")


def _build_meta(
    *,
    request_id: str,
    server_time: datetime | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id is required")

    meta = {
        "request_id": request_id,
        "server_time": _format_server_time(server_time),
    }
    if extra is None:
        return meta

    forbidden_keys = REQUIRED_META_FIELDS.intersection(extra)
    if forbidden_keys:
        blocked = ", ".join(sorted(forbidden_keys))
        raise ValueError(f"meta cannot override required fields: {blocked}")

    meta.update(dict(extra))
    return meta


def success_envelope(
    data: Any,
    *,
    request_id: str,
    server_time: datetime | None = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "data": data,
        "meta": _build_meta(request_id=request_id, server_time=server_time, extra=meta),
    }


def error_envelope(
    error: ApiError,
    *,
    request_id: str,
    server_time: datetime | None = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(error, ApiError):
        raise TypeError("error must be an ApiError")

    return {
        "error": error.to_dict(),
        "meta": _build_meta(request_id=request_id, server_time=server_time, extra=meta),
    }
