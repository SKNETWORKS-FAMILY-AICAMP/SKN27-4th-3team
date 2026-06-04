from rest_framework.views import APIView

from backend.apps.common.exceptions import ServiceNotImplementedError
from backend.apps.matches.serializers import (
    MatchDetailResponseSerializer,
    MatchResultResponseSerializer,
    TurnSubmitRequestSerializer,
    TurnSubmitResponseSerializer,
)


class MatchAPIServiceNotImplemented(ServiceNotImplementedError):
    pass


class MatchDetailView(APIView):
    response_serializer_class = MatchDetailResponseSerializer

    def get(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("matches.detail")


class TurnSubmitView(APIView):
    request_serializer_class = TurnSubmitRequestSerializer
    response_serializer_class = TurnSubmitResponseSerializer

    def post(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("matches.turns.submit")


class MatchResultView(APIView):
    response_serializer_class = MatchResultResponseSerializer

    def get(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("matches.result")
