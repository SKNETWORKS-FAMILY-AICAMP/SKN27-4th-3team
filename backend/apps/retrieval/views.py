from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.accounts import services as auth_services
from backend.apps.accounts.models import User
from backend.apps.common.exceptions import ApiErrorResponseException
from backend.apps.common.runtime import api_success_response
from backend.apps.retrieval import services as retrieval_services
from backend.apps.retrieval.serializers import (
    RagIngestRequestSerializer,
    RagIngestResponseSerializer,
    RagSearchRequestSerializer,
    RagSearchResponseSerializer,
)


@method_decorator(csrf_protect, name="dispatch")
class RagIngestView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = RagIngestRequestSerializer
    response_serializer_class = RagIngestResponseSerializer

    def post(self, request):
        _require_staff_user(request)
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        result = retrieval_services.manual_ingest_sources(
            source_paths=serializer.validated_data["source_paths"],
            force=serializer.validated_data["force"],
        )
        return api_success_response(
            request,
            {
                "ingested_documents": result.ingested_documents,
                "ingested_chunks": result.ingested_chunks,
                "skipped_documents": result.skipped_documents,
            },
        )


@method_decorator(csrf_protect, name="dispatch")
class RagSearchView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = RagSearchRequestSerializer
    response_serializer_class = RagSearchResponseSerializer

    def post(self, request):
        _require_staff_user(request)
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        defaults = retrieval_services.get_retrieval_search_defaults()
        result = retrieval_services.manual_search(
            query=serializer.validated_data["query"],
            caller=serializer.validated_data["caller"],
            top_k=serializer.validated_data.get("top_k", defaults.top_k),
            score_threshold=serializer.validated_data.get(
                "score_threshold",
                defaults.score_threshold,
            ),
        )
        return api_success_response(
            request,
            {
                "results": [
                    {
                        "document_id": item.document_id,
                        "chunk_id": item.chunk_id,
                        "source_path": item.source_path,
                        "score": item.score,
                        "text_excerpt": item.text_excerpt,
                    }
                    for item in result.results
                ],
                "top_k": result.top_k,
                "score_threshold": result.score_threshold,
            },
        )


def _require_staff_user(request) -> User:
    session = auth_services.get_current_session(
        raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
    )
    user = User.objects.get(id=int(session.user["id"]), is_active=True)
    if user.is_staff:
        return user

    raise ApiErrorResponseException(
        "RAG_ACCESS_DENIED",
        status_code=status.HTTP_403_FORBIDDEN,
    )
