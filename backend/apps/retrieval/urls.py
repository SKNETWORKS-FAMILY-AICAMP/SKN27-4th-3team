from django.urls import path

from backend.apps.retrieval.views import RagIngestView, RagSearchView


app_name = "retrieval"

urlpatterns = [
    path("ingest", RagIngestView.as_view(), name="ingest"),
    path("search", RagSearchView.as_view(), name="search"),
]
