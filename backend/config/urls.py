from django.urls import include, path


urlpatterns = [
    path("api/v1/auth/", include("backend.apps.accounts.urls")),
    path("api/v1/story/", include("backend.apps.story.urls")),
    path("api/v1/matches/", include("backend.apps.matches.urls")),
    path("api/v1/profile/", include("backend.apps.profiles.urls")),
]
