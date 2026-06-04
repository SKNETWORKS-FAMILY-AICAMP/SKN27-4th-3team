from rest_framework.views import APIView

from backend.apps.matches.serializers import (
    MatchDetailResponseSerializer,
    MatchResultResponseSerializer,
    TurnSubmitRequestSerializer,
    TurnSubmitResponseSerializer,
)


class MatchAPIServiceNotImplemented(NotImplementedError):
    pass


class MatchDetailView(APIView):
    response_serializer_class = MatchDetailResponseSerializer

    def get(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("match detail service is not implemented")


class TurnSubmitView(APIView):
    request_serializer_class = TurnSubmitRequestSerializer
    response_serializer_class = TurnSubmitResponseSerializer

    def post(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("turn submit service is not implemented")


class MatchResultView(APIView):
    response_serializer_class = MatchResultResponseSerializer

    def get(self, request, match_id: str):
        raise MatchAPIServiceNotImplemented("match result service is not implemented")
