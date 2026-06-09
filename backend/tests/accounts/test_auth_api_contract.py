import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
ACCOUNTS_DIR = BACKEND_DIR / "apps" / "accounts"
OFFICIAL_API_SPEC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"

EXPECTED_AUTH_ENDPOINTS = {
    ("GET", "/api/v1/auth/csrf"),
    ("POST", "/api/v1/auth/signup"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/refresh"),
    ("GET", "/api/v1/auth/me"),
}


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _official_auth_endpoints() -> set[tuple[str, str]]:
    spec = json.loads(OFFICIAL_API_SPEC.read_text(encoding="utf-8"))
    return {
        (endpoint["method"], endpoint["path"])
        for endpoint in spec["endpoints"]
        if endpoint["path"].startswith("/api/v1/auth/")
    }


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(serializers.Serializer):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def test_official_auth_endpoint_set_is_the_task_5_source_of_truth():
    assert _official_auth_endpoints() == EXPECTED_AUTH_ENDPOINTS


def test_auth_api_modules_and_url_routes_exist_without_draft_paths():
    accounts_urls = _read(ACCOUNTS_DIR / "urls.py")
    project_urls = _read(BACKEND_DIR / "config" / "urls.py")

    assert "app_name = \"accounts\"" in accounts_urls
    assert "CsrfTokenView.as_view()" in accounts_urls
    assert "SignupView.as_view()" in accounts_urls
    assert "LoginView.as_view()" in accounts_urls
    assert "LogoutView.as_view()" in accounts_urls
    assert "RefreshView.as_view()" in accounts_urls
    assert "MeView.as_view()" in accounts_urls
    assert "path(\"csrf\"" in accounts_urls
    assert "path(\"signup\"" in accounts_urls
    assert "path(\"login\"" in accounts_urls
    assert "path(\"logout\"" in accounts_urls
    assert "path(\"refresh\"" in accounts_urls
    assert "path(\"me\"" in accounts_urls
    assert "register" not in accounts_urls

    assert "api/v1/auth/" in project_urls
    assert "backend.apps.accounts.urls" in project_urls


def test_auth_request_and_response_serializers_match_official_schema_without_tokens():
    serializers_source = _read(ACCOUNTS_DIR / "serializers.py")

    expected_classes = (
        "SignupRequestSerializer",
        "LoginRequestSerializer",
        "EmptyRequestSerializer",
        "CsrfResponseSerializer",
        "SignupResponseSerializer",
        "LoginResponseSerializer",
        "LogoutResponseSerializer",
        "RefreshResponseSerializer",
        "MeResponseSerializer",
    )
    for class_name in expected_classes:
        assert f"class {class_name}(" in serializers_source

    assert "email = serializers.EmailField()" in serializers_source
    assert "nickname = serializers.CharField()" in serializers_source
    assert "password = serializers.CharField(" in serializers_source
    assert "csrf_token = serializers.CharField()" in serializers_source
    assert "class LoginSessionSerializer(serializers.Serializer):" in serializers_source
    assert "session = LoginSessionSerializer()" in serializers_source
    assert "refreshed = serializers.BooleanField()" in serializers_source
    assert "logged_out = serializers.BooleanField()" in serializers_source
    assert "access_token" not in serializers_source
    assert "refresh_token" not in serializers_source


def test_login_response_serializer_keeps_session_fields_nested_like_official_schema():
    serializers_source = _read(ACCOUNTS_DIR / "serializers.py")
    login_session_source = _class_source(serializers_source, "LoginSessionSerializer")
    login_response_source = _class_source(serializers_source, "LoginResponseSerializer")

    assert "authenticated = serializers.BooleanField()" in login_session_source
    assert "access_expires_in_seconds = serializers.IntegerField()" in login_session_source
    assert "session = LoginSessionSerializer()" in login_response_source
    assert "authenticated = serializers.BooleanField()" not in login_response_source
    assert "access_expires_in_seconds = serializers.IntegerField()" not in login_response_source


def test_auth_views_enforce_csrf_cookie_contract_without_exemptions_or_bearer_tokens():
    views_source = _read(ACCOUNTS_DIR / "views.py")

    assert "csrf_exempt" not in views_source
    assert "Authorization" not in views_source
    assert "Bearer" not in views_source
    assert "localStorage" not in views_source
    assert "sessionStorage" not in views_source
    assert "ensure_csrf_cookie" in views_source
    assert "get_token(request)" in views_source
    assert "rotate_token(request)" in views_source


def test_auth_cookie_helpers_use_approved_paths_flags_and_ttls():
    views_source = _read(ACCOUNTS_DIR / "views.py")

    assert "settings.ACCESS_TOKEN_COOKIE_NAME" in views_source
    assert "settings.REFRESH_TOKEN_COOKIE_NAME" in views_source
    assert "settings.ACCESS_TOKEN_COOKIE_PATH" in views_source
    assert "settings.REFRESH_TOKEN_COOKIE_PATH" in views_source
    assert "settings.ACCESS_TOKEN_TTL_SECONDS" in views_source
    assert "settings.REFRESH_TOKEN_TTL_SECONDS" in views_source
    assert "httponly=True" in views_source
    assert "secure=settings.SECURE_COOKIES" in views_source
    assert "samesite=settings.AUTH_COOKIE_SAMESITE" in views_source
    assert "delete_cookie(" in views_source


def test_auth_views_delegate_runtime_to_service_layer_without_response_body_tokens():
    views_source = _read(ACCOUNTS_DIR / "views.py")
    signup_source = views_source.split("class SignupView", maxsplit=1)[1].split(
        "\n\nclass LoginView",
        maxsplit=1,
    )[0]

    assert "auth_services.signup(" in signup_source
    assert "auth_services.logout(" in views_source
    assert "clear_auth_cookies(response)" in views_source
    assert "auth_services.login(" in views_source
    assert "auth_services.refresh(" in views_source
    assert "auth_services.get_current_session(" in views_source
    assert "jwt.encode" not in views_source
    assert "RefreshToken.objects" not in views_source
    assert '"access_token":' not in views_source
    assert '"refresh_token":' not in views_source
