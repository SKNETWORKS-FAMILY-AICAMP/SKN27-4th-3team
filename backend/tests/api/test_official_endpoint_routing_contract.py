import json
import os
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import Resolver404, resolve


ROOT_DIR = Path(__file__).resolve().parents[3]
OFFICIAL_API_SPEC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"

CONCRETE_PATHS = {
    "/api/v1/story/cases/{case_id}/briefing": "/api/v1/story/cases/mirror_guest/briefing",
    "/api/v1/story/cases/{case_id}/matches": "/api/v1/story/cases/mirror_guest/matches",
    "/api/v1/matches/{match_id}": "/api/v1/matches/match_1",
    "/api/v1/matches/{match_id}/turns": "/api/v1/matches/match_1/turns",
    "/api/v1/matches/{match_id}/result": "/api/v1/matches/match_1/result",
}

EXPECTED_VIEW_CLASSES = {
    ("GET", "/api/v1/auth/csrf"): "CsrfTokenView",
    ("POST", "/api/v1/auth/signup"): "SignupView",
    ("POST", "/api/v1/auth/login"): "LoginView",
    ("POST", "/api/v1/auth/logout"): "LogoutView",
    ("POST", "/api/v1/auth/refresh"): "RefreshView",
    ("GET", "/api/v1/auth/me"): "MeView",
    ("GET", "/api/v1/story/cases"): "StoryCaseListView",
    ("GET", "/api/v1/story/cases/{case_id}/briefing"): "StoryCaseBriefingView",
    ("POST", "/api/v1/story/cases/{case_id}/matches"): "StoryCaseMatchStartView",
    ("GET", "/api/v1/matches/{match_id}"): "MatchDetailView",
    ("POST", "/api/v1/matches/{match_id}/turns"): "TurnSubmitView",
    ("GET", "/api/v1/matches/{match_id}/result"): "MatchResultView",
    ("GET", "/api/v1/profile/me"): "ProfileMeView",
}

DRAFT_PATHS_NOT_COVERED_BY_OFFICIAL_DYNAMIC_SEGMENTS = (
    "/api/v1/auth/register",
    "/api/v1/matches/match_1/turns/turn_1/actions",
)


def _official_endpoint_keys() -> set[tuple[str, str]]:
    spec = json.loads(OFFICIAL_API_SPEC.read_text(encoding="utf-8"))
    return {(endpoint["method"], endpoint["path"]) for endpoint in spec["endpoints"]}


def _concrete_path(path: str) -> str:
    return CONCRETE_PATHS.get(path, path)


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    try:
        import django

        django.setup()
    except ImproperlyConfigured as exc:
        raise AssertionError("Django settings must load for URL resolution") from exc


def test_all_official_endpoint_paths_resolve_to_named_views():
    _setup_django()

    assert _official_endpoint_keys() == set(EXPECTED_VIEW_CLASSES)

    for endpoint_key, expected_view_name in EXPECTED_VIEW_CLASSES.items():
        method, official_path = endpoint_key
        match = resolve(_concrete_path(official_path))
        view_class = match.func.view_class

        assert view_class.__name__ == expected_view_name
        assert hasattr(view_class, method.lower())


@pytest.mark.parametrize("path", DRAFT_PATHS_NOT_COVERED_BY_OFFICIAL_DYNAMIC_SEGMENTS)
def test_draft_api_paths_are_not_routed(path):
    _setup_django()

    with pytest.raises(Resolver404):
        resolve(path)


def test_draft_ai_story_start_path_is_not_a_dedicated_route():
    _setup_django()

    match = resolve("/api/v1/matches/ai-story")

    assert match.func.view_class.__name__ == "MatchDetailView"
    assert match.kwargs == {"match_id": "ai-story"}
