from rest_framework.views import APIView

from backend.apps.common.exceptions import ServiceNotImplementedError
from backend.apps.story.serializers import (
    StoryCaseBriefingResponseSerializer,
    StoryCaseListResponseSerializer,
    StoryCaseMatchStartRequestSerializer,
    StoryCaseMatchStartResponseSerializer,
)


class StoryAPIServiceNotImplemented(ServiceNotImplementedError):
    pass


class StoryCaseListView(APIView):
    response_serializer_class = StoryCaseListResponseSerializer

    def get(self, request):
        raise StoryAPIServiceNotImplemented("story.cases.list")


class StoryCaseBriefingView(APIView):
    response_serializer_class = StoryCaseBriefingResponseSerializer

    def get(self, request, case_id: str):
        raise StoryAPIServiceNotImplemented("story.cases.briefing")


class StoryCaseMatchStartView(APIView):
    request_serializer_class = StoryCaseMatchStartRequestSerializer
    response_serializer_class = StoryCaseMatchStartResponseSerializer

    def post(self, request, case_id: str):
        raise StoryAPIServiceNotImplemented("story.cases.matches.start")
