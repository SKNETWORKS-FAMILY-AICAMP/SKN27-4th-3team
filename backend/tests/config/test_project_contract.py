import importlib
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

EXPECTED_REQUIREMENTS = {
    "Django": "5.2.14",
    "djangorestframework": "3.17.1",
    "gunicorn": "23.0.0",
    "uvicorn": "0.49.0",
    "uvicorn-worker": "0.4.0",
    "websockets": "16.0",
    "channels": "4.3.2",
    "channels_redis": "4.3.0",
    "PyJWT": "2.13.0",
    "jsonschema": "4.26.0",
    "pgvector": "0.4.2",
    "psycopg[binary]": "3.3.4",
}

EXPECTED_PROJECT_APPS = {
    "backend.apps.accounts.apps.AccountsConfig",
    "backend.apps.profiles.apps.ProfilesConfig",
    "backend.apps.game_rules.apps.GameRulesConfig",
    "backend.apps.matches.apps.MatchesConfig",
    "backend.apps.story.apps.StoryConfig",
    "backend.apps.ai_profile.apps.AIProfileConfig",
    "backend.apps.retrieval.apps.RetrievalConfig",
    "backend.apps.llm.apps.LlmConfig",
}

FORBIDDEN_APP_FRAGMENTS = (
    "backend.apps.realtime",
    "backend.apps.knowledge",
    "corsheaders",
)

FORBIDDEN_PROJECT_APP_DIRS = (
    BACKEND_DIR / "apps" / "realtime",
)


def _active_requirement_lines() -> list[str]:
    assert REQUIREMENTS_FILE.exists(), "requirements.txt must exist at project root"
    lines = REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def _settings_module():
    return importlib.import_module("backend.config.settings")


def _reload_settings_module():
    return importlib.reload(_settings_module())


def test_backend_dependencies_are_pinned_to_approved_official_versions():
    requirement_lines = _active_requirement_lines()
    requirements = dict(line.split("==", 1) for line in requirement_lines)

    assert requirements == EXPECTED_REQUIREMENTS
    assert all("==" in line for line in requirement_lines)
    assert not any("simplejwt" in line.lower() for line in requirement_lines)


def test_django_project_entrypoints_exist_and_use_backend_config_settings():
    expected_files = (
        BACKEND_DIR / "manage.py",
        BACKEND_DIR / "config" / "settings.py",
        BACKEND_DIR / "config" / "urls.py",
        BACKEND_DIR / "config" / "asgi.py",
        BACKEND_DIR / "config" / "wsgi.py",
    )

    for expected_file in expected_files:
        assert expected_file.exists(), f"{expected_file} must exist"

    assert "backend.config.settings" in (BACKEND_DIR / "manage.py").read_text(encoding="utf-8")
    assert "backend.config.settings" in (BACKEND_DIR / "config" / "asgi.py").read_text(
        encoding="utf-8"
    )
    assert "backend.config.settings" in (BACKEND_DIR / "config" / "wsgi.py").read_text(
        encoding="utf-8"
    )
    assert "urlpatterns" in (BACKEND_DIR / "config" / "urls.py").read_text(encoding="utf-8")


def test_backend_manage_py_adds_project_root_to_python_path():
    manage_text = (BACKEND_DIR / "manage.py").read_text(encoding="utf-8")

    assert "Path(__file__).resolve().parent.parent" in manage_text
    assert "sys.path.insert" in manage_text


def test_settings_keep_approved_api_auth_and_cookie_contracts():
    settings = _settings_module()

    assert settings.API_PREFIX == "/api/v1"
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert settings.ACCESS_TOKEN_COOKIE_PATH == "/api/v1"
    assert settings.REFRESH_TOKEN_COOKIE_PATH == "/api/v1/auth"
    assert settings.ACCESS_TOKEN_TTL_SECONDS == 15 * 60
    assert settings.REFRESH_TOKEN_TTL_SECONDS == 14 * 24 * 60 * 60
    assert settings.CSRF_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"


def test_settings_enable_csrf_and_reject_wildcard_origins():
    settings = _settings_module()

    assert "django.middleware.csrf.CsrfViewMiddleware" in settings.MIDDLEWARE
    assert getattr(settings, "CSRF_TRUSTED_ORIGINS") == []
    assert getattr(settings, "CORS_ALLOWED_ORIGINS") == []
    assert "*" not in settings.ALLOWED_HOSTS
    assert not getattr(settings, "CSRF_EXEMPT_ALL", False)


def test_settings_rejects_wildcard_csrf_and_cors_origin_env(monkeypatch):
    for env_name in ("DJANGO_CSRF_TRUSTED_ORIGINS", "DJANGO_CORS_ALLOWED_ORIGINS"):
        monkeypatch.setenv(env_name, "https://*.example.com")

        with pytest.raises(RuntimeError, match=env_name):
            _reload_settings_module()

        monkeypatch.delenv(env_name, raising=False)
        _reload_settings_module()


def test_rag_embedding_model_id_is_injected_from_env_without_code_default(monkeypatch):
    settings_text = (BACKEND_DIR / "config" / "settings.py").read_text(encoding="utf-8")

    assert "text-embedding-3-small" not in settings_text

    monkeypatch.setenv("RAG_EMBEDDING_MODEL_ID", "contract-test-embedding-model")
    settings = _reload_settings_module()
    assert settings.RAG_EMBEDDING_MODEL_ID == "contract-test-embedding-model"

    monkeypatch.delenv("RAG_EMBEDDING_MODEL_ID", raising=False)
    settings = _reload_settings_module()
    assert settings.RAG_EMBEDDING_MODEL_ID is None


def test_settings_install_only_in_scope_mvp_apps():
    settings = _settings_module()
    installed_apps = set(settings.INSTALLED_APPS)

    assert EXPECTED_PROJECT_APPS.issubset(installed_apps)
    assert "channels" in installed_apps
    for forbidden_fragment in FORBIDDEN_APP_FRAGMENTS:
        assert not any(forbidden_fragment in app for app in installed_apps)


def test_settings_configure_redis_channel_layer_from_env(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://contract-redis:6379/7")

    settings = _reload_settings_module()

    assert settings.REDIS_URL == "redis://contract-redis:6379/7"
    assert settings.CHANNEL_LAYERS == {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": ["redis://contract-redis:6379/7"]},
        }
    }

    monkeypatch.delenv("REDIS_URL", raising=False)
    _reload_settings_module()


def test_settings_configure_websocket_runtime_timeouts_from_env(monkeypatch):
    monkeypatch.setenv("WEBSOCKET_HEARTBEAT_SECONDS", "31")
    monkeypatch.setenv("WEBSOCKET_CONNECT_TIMEOUT_SECONDS", "9")

    settings = _reload_settings_module()

    assert settings.WEBSOCKET_HEARTBEAT_SECONDS == 31
    assert settings.WEBSOCKET_CONNECT_TIMEOUT_SECONDS == 9

    monkeypatch.delenv("WEBSOCKET_HEARTBEAT_SECONDS", raising=False)
    monkeypatch.delenv("WEBSOCKET_CONNECT_TIMEOUT_SECONDS", raising=False)
    _reload_settings_module()


def test_out_of_scope_realtime_app_scaffold_does_not_exist():
    for forbidden_app_dir in FORBIDDEN_PROJECT_APP_DIRS:
        assert not forbidden_app_dir.exists(), f"{forbidden_app_dir} must not exist"


def test_settings_app_config_modules_exist_for_installed_project_apps():
    for app_config_path in EXPECTED_PROJECT_APPS:
        module_path, class_name = app_config_path.rsplit(".", 1)
        module_file = ROOT_DIR / Path(*module_path.split(".")).with_suffix(".py")

        assert module_file.exists()
        module_text = module_file.read_text(encoding="utf-8")
        assert f"class {class_name}" in module_text
        assert "django.apps" in module_text
