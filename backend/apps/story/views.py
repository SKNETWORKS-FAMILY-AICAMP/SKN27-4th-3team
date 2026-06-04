from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.common.exceptions import ServiceNotImplementedError
from backend.apps.common.runtime import api_success_response
from backend.apps.story import services as story_services
from backend.apps.story.serializers import (
    StoryCaseBriefingResponseSerializer,
    StoryCaseListResponseSerializer,
    StoryCaseMatchStartRequestSerializer,
    StoryCaseMatchStartResponseSerializer,
)


class StoryAPIServiceNotImplemented(ServiceNotImplementedError):
    pass


class StoryCaseListView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = StoryCaseListResponseSerializer

    def get(self, request):
        case_list = story_services.list_story_cases(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        )
        return api_success_response(request, {"cases": case_list.cases})


class StoryCaseBriefingView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = StoryCaseBriefingResponseSerializer

    def get(self, request, case_id: str):
        briefing = story_services.get_story_case_briefing(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            case_id=case_id,
        )
        return api_success_response(request, {"case": briefing.case})


class StoryCaseMatchStartView(APIView):
    request_serializer_class = StoryCaseMatchStartRequestSerializer
    response_serializer_class = StoryCaseMatchStartResponseSerializer

    def post(self, request, case_id: str):
        raise StoryAPIServiceNotImplemented("story.cases.matches.start")
