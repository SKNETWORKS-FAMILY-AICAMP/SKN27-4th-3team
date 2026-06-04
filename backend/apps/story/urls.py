from django.urls import path

from backend.apps.story.views import (
    StoryCaseBriefingView,
    StoryCaseListView,
    StoryCaseMatchStartView,
)


app_name = "story"

urlpatterns = [
    path("cases", StoryCaseListView.as_view(), name="case-list"),
    path("cases/<str:case_id>/briefing", StoryCaseBriefingView.as_view(), name="case-briefing"),
    path("cases/<str:case_id>/matches", StoryCaseMatchStartView.as_view(), name="case-match-start"),
]
