from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
OPS_DIR = ROOT_DIR / "ops"
COMPOSE_FILE = OPS_DIR / "docker" / "docker-compose.yml"
BACKEND_DOCKERFILE = OPS_DIR / "docker" / "backend.Dockerfile"
BACKEND_ENV_EXAMPLE = OPS_DIR / "env" / "backend.env.example"

FORBIDDEN_RUNTIME_WORDS = (
    "llm-provider",
    "llm_provider",
    "kag-store",
    "kag_store",
    "neo4j",
)


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def test_local_docker_compose_includes_only_approved_mvp_runtime_services():
    compose = _read(COMPOSE_FILE)

    assert "services:" in compose
    assert "api:" in compose
    assert "postgres:" in compose
    assert "redis:" in compose
    assert "pgvector/pgvector:" in compose
    assert "redis:" in compose
    assert "backend.Dockerfile" in compose
    assert "8000:8000" in compose
    assert "5432:5432" in compose
    assert "6379:6379" in compose
    assert "REDIS_URL=redis://redis:6379/0" in compose

    lowered = compose.lower()
    for forbidden in FORBIDDEN_RUNTIME_WORDS:
        assert forbidden not in lowered


def test_backend_dockerfile_uses_locked_requirements_and_django_entrypoint():
    dockerfile = _read(BACKEND_DOCKERFILE)

    assert "python:3.14" in dockerfile
    assert "requirements.txt" in dockerfile
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "backend.config.asgi:application" in dockerfile
    assert "uvicorn" in dockerfile
    assert "--host" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "--port" in dockerfile
    assert "8000" in dockerfile


def test_backend_env_example_documents_required_local_runtime_values_without_real_secret():
    env_example = _read(BACKEND_ENV_EXAMPLE)

    required_keys = (
        "DJANGO_ENV=local",
        "DJANGO_DEBUG=true",
        "DJANGO_SECRET_KEY=change-me-local-only",
        "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1",
        "DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173",
        "DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173",
        "DJANGO_SECURE_COOKIES=false",
        "POSTGRES_DB=pilot",
        "POSTGRES_USER=pilot",
        "POSTGRES_PASSWORD=change-me-local-db-password",
        "POSTGRES_HOST=postgres",
        "POSTGRES_PORT=5432",
        "REDIS_URL=redis://redis:6379/0",
        "WEBSOCKET_HEARTBEAT_SECONDS=25",
        "WEBSOCKET_CONNECT_TIMEOUT_SECONDS=6",
        "RAG_EMBEDDING_MODEL_ID=text-embedding-3-small",
    )
    for key in required_keys:
        assert key in env_example

    assert "production" not in env_example.lower()
    assert "real-secret" not in env_example.lower()
    assert "Bearer" not in env_example
    assert "localStorage" not in env_example
