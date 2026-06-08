from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _service_block(source: str, service_name: str) -> str:
    lines = source.splitlines()
    start = lines.index(f"  {service_name}:")
    end = len(lines)

    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = index
            break

    return "\n".join(lines[start:end])


def test_requirements_include_gunicorn_for_production_wsgi():
    assert "gunicorn==" in _read("requirements.txt")


def test_backend_production_dockerfile_uses_gunicorn_not_runserver():
    source = _read("ops/docker/backend.production.Dockerfile")

    assert "gunicorn" in source
    assert "backend.config.wsgi:application" in source
    assert "runserver" not in source


def test_web_production_dockerfile_builds_frontend_and_uses_caddy():
    source = _read("ops/docker/web.production.Dockerfile")

    assert "npm run build" in source
    assert "FROM caddy:" in source
    assert "COPY --from=frontend-build" in source


def test_caddyfile_proxies_api_and_healthz_to_internal_api():
    source = _read("ops/docker/Caddyfile.production")

    assert "reverse_proxy api:8000" in source
    assert "handle_path /api/*" in source or "handle /api/*" in source
    assert "handle /healthz" in source


def test_production_compose_exposes_only_web_ports_and_keeps_api_db_internal():
    source = _read("ops/docker/docker-compose.production.yml")

    assert "80:80" in source
    assert "443:443" in source
    assert "8000:8000" not in source
    assert "5432:5432" not in source
    assert "172.28.0.2" in source
    assert "DJANGO_TRUSTED_PROXY_IPS=172.28.0.2" in source


def test_production_compose_reserves_caddy_proxy_ip_when_db_starts_first():
    source = _read("ops/docker/docker-compose.production.yml")

    assert "ipv4_address: 172.28.0.2" in _service_block(source, "web")
    assert "ipv4_address: 172.28.0.10" in _service_block(source, "api")
    assert "ipv4_address: 172.28.0.11" in _service_block(source, "postgres")


def test_production_env_template_has_no_real_secret_values():
    source = _read("ops/env/production.env.example")

    assert "DJANGO_ENV=production" in source
    assert "DJANGO_DEBUG=false" in source
    assert "DJANGO_SECURE_COOKIES=true" in source
    assert "change-me" in source
    assert "actual-secret" not in source
