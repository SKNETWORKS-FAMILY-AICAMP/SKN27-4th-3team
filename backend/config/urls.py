from django.urls import include, path

from backend.apps.common.health import healthz


urlpatterns = [
    path("healthz", healthz),
    path("api/v1/auth/", include("backend.apps.accounts.urls")),
    path("api/v1/story/", include("backend.apps.story.urls")),
    path("api/v1/matches/", include("backend.apps.matches.urls")),
    path("api/v1/profile/", include("backend.apps.profiles.urls")),
    path("api/v1/retrieval/", include("backend.apps.retrieval.urls")),
]
