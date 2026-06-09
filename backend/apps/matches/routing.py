from django.urls import path

from backend.apps.matches.consumers import MatchRealtimeConsumer


websocket_urlpatterns = [
    path("ws/matches/<str:match_id>", MatchRealtimeConsumer.as_asgi()),
]
