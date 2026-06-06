from django.urls import path

from backend.apps.matches.views import (
    DuelDialogueView,
    MatchDetailView,
    MatchResultView,
    TurnLlmTextView,
    TurnSubmitView,
)


app_name = "matches"

urlpatterns = [
    path("<str:match_id>", MatchDetailView.as_view(), name="detail"),
    path("<str:match_id>/turns", TurnSubmitView.as_view(), name="turn-submit"),
    path(
        "<str:match_id>/turns/<str:turn_id>/llm-text",
        TurnLlmTextView.as_view(),
        name="turn-llm-text",
    ),
    path(
        "<str:match_id>/duel/dialogues",
        DuelDialogueView.as_view(),
        name="duel-dialogues",
    ),
    path("<str:match_id>/result", MatchResultView.as_view(), name="result"),
]
