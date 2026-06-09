from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.common.exceptions import ApiErrorResponseException, ServiceNotImplementedError
from backend.apps.common.runtime import api_success_response
from backend.apps.matches import services as match_services
from backend.apps.matches.serializers import (
    DuelDialogueRequestSerializer,
    DuelDialogueResponseSerializer,
    MatchDetailResponseSerializer,
    MatchResultResponseSerializer,
    TurnLlmTextRequestSerializer,
    TurnLlmTextResponseSerializer,
    TurnSubmitRequestSerializer,
    TurnSubmitResponseSerializer,
)


class MatchAPIServiceNotImplemented(ServiceNotImplementedError):
    pass


class MatchDetailView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = MatchDetailResponseSerializer

    def get(self, request, match_id: str):
        match_detail = match_services.get_match_detail(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            public_match_id=match_id,
        )
        return api_success_response(request, {"match": match_detail.match})


@method_decorator(csrf_protect, name="dispatch")
class TurnSubmitView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = TurnSubmitRequestSerializer
    response_serializer_class = TurnSubmitResponseSerializer

    def post(self, request, match_id: str):
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        submit_result = match_services.submit_match_turn(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            public_match_id=match_id,
            action_code=serializer.validated_data["action_code"],
            info_target_key=serializer.validated_data.get("info_target_key"),
            client_nonce=serializer.validated_data["client_nonce"],
        )
        return api_success_response(
            request,
            {
                "turn_result": submit_result.turn_result,
                "match": submit_result.match,
            },
        )


@method_decorator(csrf_protect, name="dispatch")
class TurnLlmTextView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = TurnLlmTextRequestSerializer
    response_serializer_class = TurnLlmTextResponseSerializer

    def post(self, request, match_id: str, turn_id: str):
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        llm_result = match_services.generate_turn_llm_text(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            public_match_id=match_id,
            public_turn_id=turn_id,
            display_slot=serializer.validated_data.get(
                "display_slot",
                "right_apparition_message",
            ),
        )
        return api_success_response(request, {"llm_text": llm_result.llm_text})


@method_decorator(csrf_protect, name="dispatch")
class DuelDialogueView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = DuelDialogueRequestSerializer
    response_serializer_class = DuelDialogueResponseSerializer

    def post(self, request, match_id: str):
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        dialogue_result = match_services.create_duel_dialogue(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            public_match_id=match_id,
            message=serializer.validated_data["message"],
            client_nonce=serializer.validated_data["client_nonce"],
        )
        return api_success_response(request, {"dialogue": dialogue_result.dialogue})


class MatchResultView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = MatchResultResponseSerializer

    def get(self, request, match_id: str):
        match_result = match_services.get_match_result(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
            public_match_id=match_id,
        )
        return api_success_response(request, {"result": match_result.result})
