from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

API_PREFIX = "/api/v1"
ENVIRONMENT = os.getenv("DJANGO_ENV", "local")


def _bool_env(name: str, *, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, *, default: tuple[str, ...] = ()) -> list[str]:
    raw_value = os.getenv(name)
    if not raw_value:
        return list(default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _origin_allowlist_env(name: str) -> list[str]:
    origins = _csv_env(name)
    if any("*" in origin for origin in origins):
        raise RuntimeError(f"{name} must be an explicit origin allowlist")
    return origins


def _positive_int_env(name: str, *, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


if ENVIRONMENT == "production" and not os.getenv("DJANGO_SECRET_KEY"):
    raise RuntimeError("DJANGO_SECRET_KEY is required in production")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "pilot-local-dev-secret-change-me")
DEBUG = _bool_env("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = _csv_env("DJANGO_ALLOWED_HOSTS", default=("localhost", "127.0.0.1"))
CSRF_TRUSTED_ORIGINS = _origin_allowlist_env("DJANGO_CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = _origin_allowlist_env("DJANGO_CORS_ALLOWED_ORIGINS")
DJANGO_TRUSTED_PROXY_IPS = tuple(_csv_env("DJANGO_TRUSTED_PROXY_IPS"))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "channels",
    "backend.apps.accounts.apps.AccountsConfig",
    "backend.apps.profiles.apps.ProfilesConfig",
    "backend.apps.game_rules.apps.GameRulesConfig",
    "backend.apps.matches.apps.MatchesConfig",
    "backend.apps.story.apps.StoryConfig",
    "backend.apps.ai_profile.apps.AIProfileConfig",
    "backend.apps.retrieval.apps.RetrievalConfig",
    "backend.apps.llm.apps.LlmConfig",
]

MIDDLEWARE = [
    "backend.apps.common.request_ids.RequestIdMiddleware",
    "backend.apps.common.trusted_proxy.TrustedProxyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"
ASGI_APPLICATION = "backend.config.asgi.application"
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "pilot"),
        "USER": os.getenv("POSTGRES_USER", "pilot"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "pilot"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = PROJECT_ROOT / "staticfiles"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "backend.apps.common.runtime.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

AUTH_COOKIE_SAMESITE = "Lax"
SECURE_COOKIES = _bool_env("DJANGO_SECURE_COOKIES", default=ENVIRONMENT == "production")
CSRF_COOKIE_SECURE = SECURE_COOKIES
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
SESSION_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
CSRF_FAILURE_VIEW = "backend.apps.common.csrf.csrf_failure"

ACCESS_TOKEN_COOKIE_NAME = "pilot_access"
REFRESH_TOKEN_COOKIE_NAME = "pilot_refresh"
ACCESS_TOKEN_COOKIE_PATH = API_PREFIX
REFRESH_TOKEN_COOKIE_PATH = f"{API_PREFIX}/auth"
ACCESS_TOKEN_TTL_SECONDS = 15 * 60
REFRESH_TOKEN_TTL_SECONDS = 14 * 24 * 60 * 60
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

AUTH_PASSWORD_MIN_LENGTH = 10
AUTH_PASSWORD_MAX_LENGTH = 128
LOGIN_FAILURE_WINDOW_SECONDS = 10 * 60
LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_LOCKOUT_SECONDS = 15 * 60
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("email", "nickname")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": AUTH_PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

RAG_EMBEDDING_MODEL_ID = os.getenv("RAG_EMBEDDING_MODEL_ID")
RAG_DEFAULT_TOP_K = 6
RAG_DEFAULT_SCORE_THRESHOLD = 0.72

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WEBSOCKET_HEARTBEAT_SECONDS = _positive_int_env("WEBSOCKET_HEARTBEAT_SECONDS", default=25)
WEBSOCKET_CONNECT_TIMEOUT_SECONDS = _positive_int_env(
    "WEBSOCKET_CONNECT_TIMEOUT_SECONDS",
    default=6,
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}
