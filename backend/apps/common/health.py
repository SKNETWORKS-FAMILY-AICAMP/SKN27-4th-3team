from django.db import connections
from django.http import JsonResponse


def healthz(request):
    if not _database_is_healthy():
        return JsonResponse({"status": "unhealthy"}, status=503)

    return JsonResponse({"status": "ok"})


def _database_is_healthy() -> bool:
    try:
        connections["default"].ensure_connection()
    except Exception:
        return False

    return True
