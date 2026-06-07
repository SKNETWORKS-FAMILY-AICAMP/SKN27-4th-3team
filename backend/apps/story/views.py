from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.common.exceptions import ApiErrorResponseException, ServiceNotImplementedError
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


@method_decorator(csrf_protect, name="dispatch")
class StoryCaseMatchStartView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = StoryCaseMatchStartRequestSerializer
    response_serializer_class = StoryCaseMatchStartResponseSerializer

    def post(self, request, case_id: str):
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        match_start = story_services.start_story_case_match(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            case_id=case_id,
            client_request_id=serializer.validated_data["client_request_id"],
            player_display_name=serializer.validated_data.get("player_display_name"),
        )
        return api_success_response(
            request,
            {"match": match_start.match},
            status_code=status.HTTP_201_CREATED,
        )
