from rest_framework.views import APIView

from backend.apps.story.serializers import (
    StoryCaseBriefingResponseSerializer,
    StoryCaseListResponseSerializer,
    StoryCaseMatchStartRequestSerializer,
    StoryCaseMatchStartResponseSerializer,
)


class StoryAPIServiceNotImplemented(NotImplementedError):
    pass


class StoryCaseListView(APIView):
    response_serializer_class = StoryCaseListResponseSerializer

    def get(self, request):
        raise StoryAPIServiceNotImplemented("story case list service is not implemented")


class StoryCaseBriefingView(APIView):
    response_serializer_class = StoryCaseBriefingResponseSerializer

    def get(self, request, case_id: str):
        raise StoryAPIServiceNotImplemented("story case briefing service is not implemented")


class StoryCaseMatchStartView(APIView):
    request_serializer_class = StoryCaseMatchStartRequestSerializer
    response_serializer_class = StoryCaseMatchStartResponseSerializer

    def post(self, request, case_id: str):
        raise StoryAPIServiceNotImplemented("story match start service is not implemented")
