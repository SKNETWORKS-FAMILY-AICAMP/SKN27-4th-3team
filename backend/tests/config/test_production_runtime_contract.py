import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from django.test import Client, RequestFactory, override_settings

from backend.apps.common.trusted_proxy import get_client_ip


django.setup()


def test_healthz_returns_plain_health_payload_without_api_envelope(monkeypatch):
    from backend.apps.common import health as health_module

    monkeypatch.setattr(health_module, "_database_is_healthy", lambda: True)

    response = Client().get("/healthz", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "data" not in response.json()
    assert "meta" not in response.json()


@override_settings(DJANGO_TRUSTED_PROXY_IPS=("172.28.0.2",))
def test_trusted_proxy_uses_first_forwarded_for_only_from_allowlisted_proxy():
    request = RequestFactory().post(
        "/api/v1/auth/login",
        REMOTE_ADDR="172.28.0.2",
        HTTP_X_FORWARDED_FOR="203.0.113.10, 172.28.0.2",
    )

    assert get_client_ip(request) == "203.0.113.10"


@override_settings(DJANGO_TRUSTED_PROXY_IPS=("172.28.0.2",))
def test_untrusted_proxy_header_is_ignored_for_client_ip():
    request = RequestFactory().post(
        "/api/v1/auth/login",
        REMOTE_ADDR="198.51.100.7",
        HTTP_X_FORWARDED_FOR="203.0.113.10",
    )

    assert get_client_ip(request) == "198.51.100.7"
