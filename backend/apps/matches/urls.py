from django.urls import path

from backend.apps.matches.views import MatchDetailView, MatchResultView, TurnSubmitView


app_name = "matches"

urlpatterns = [
    path("<str:match_id>", MatchDetailView.as_view(), name="detail"),
    path("<str:match_id>/turns", TurnSubmitView.as_view(), name="turn-submit"),
    path("<str:match_id>/result", MatchResultView.as_view(), name="result"),
]
