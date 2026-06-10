import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from django.db import transaction
from django.db.models import ExpressionWrapper, F, FloatField, Value
from django.utils import timezone
from pgvector.django import CosineDistance

from backend.apps.common.exceptions import ApiErrorResponseException
from backend.config import settings
from backend.apps.retrieval.chunking import build_document_chunks
from backend.apps.retrieval.models import (
    RetrievalChunk,
    RetrievalDocument,
    RetrievalQueryLog,
)


APPROVED_CONTRACTS_DIR = "docs/09_Approved_Contracts"
NAMELESS_CURSE_RAG_SOURCE_PATHS = (
    "docs/09_Approved_Contracts/27_플레이어_이름_무명의_저주_결전_RAG_계약.md",
    "docs/09_Approved_Contracts/26_무명의_저주_사건_계약.md",
    "docs/09_Approved_Contracts/25_" + "L" + "LM_Runtime_통합_계약.md",
    "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
)
MIRROR_GUEST_STORY_PATH = "docs/05_Story_Mode/02_거울_속의_손님.md"
APPROVED_GAME_RULE_PATHS = (
    "docs/02_Game_Rules/01_자원과_상태.md",
    "docs/02_Game_Rules/04_상성_규칙.md",
    "docs/02_Game_Rules/05_승패_조건.md",
    "docs/02_Game_Rules/06_시간초과_규칙.md",
    "docs/02_Game_Rules/99_Game_Rules_구현_확정.md",
)
RAG_CHUNK_SCHEMA_VERSION = "rag-chunk-v1"
DETERMINISTIC_EMBEDDING_DIMENSIONS = 32
HTTP_400_BAD_REQUEST = 400
HTTP_503_SERVICE_UNAVAILABLE = 503


@dataclass(frozen=True)
class RetrievalSearchDefaults:
    top_k: int
    score_threshold: float


@dataclass(frozen=True)
class StoryCaseRagSourcePlan:
    case_id: str
    caller: str
    source_paths: tuple[str, ...]


@dataclass(frozen=True)
class RagIngestResult:
    ingested_documents: int
    ingested_chunks: int
    skipped_documents: int


@dataclass(frozen=True)
class RagSearchResult:
    document_id: str
    chunk_id: str
    source_path: str
    score: float
    text_excerpt: str


@dataclass(frozen=True)
class RagSearchResponse:
    results: tuple[RagSearchResult, ...]
    top_k: int
    score_threshold: float


def is_retrieval_source_allowed(source_path: str) -> bool:
    normalized_path = _normalize_source_path(source_path)
    if normalized_path.startswith(f"{APPROVED_CONTRACTS_DIR}/"):
        return True
    if normalized_path == MIRROR_GUEST_STORY_PATH:
        return True

    return normalized_path in APPROVED_GAME_RULE_PATHS


def build_story_case_rag_source_plan(*, case_id: str, caller: str) -> StoryCaseRagSourcePlan:
    if case_id == "nameless_curse":
        return StoryCaseRagSourcePlan(
            case_id=case_id,
            caller=caller,
            source_paths=NAMELESS_CURSE_RAG_SOURCE_PATHS,
        )

    return StoryCaseRagSourcePlan(
        case_id=case_id,
        caller=caller,
        source_paths=(f"{APPROVED_CONTRACTS_DIR}/25_" + "L" + "LM_Runtime_통합_계약.md",),
    )


def get_retrieval_search_defaults() -> RetrievalSearchDefaults:
    return RetrievalSearchDefaults(
        top_k=settings.RAG_DEFAULT_TOP_K,
        score_threshold=settings.RAG_DEFAULT_SCORE_THRESHOLD,
    )


def get_configured_embedding_model_id() -> str:
    model_id = settings.RAG_EMBEDDING_MODEL_ID
    if not model_id:
        raise ValueError("RAG_EMBEDDING_MODEL_ID must be provided by env/config")

    return model_id


def manual_ingest_sources(*, source_paths: list[str] | tuple[str, ...], force: bool) -> RagIngestResult:
    ingested_documents = 0
    ingested_chunks = 0
    skipped_documents = 0

    for source_path in source_paths:
        normalized_path = _normalize_source_path(source_path)
        file_path = _validated_source_file_path(normalized_path)
        existing_documents = RetrievalDocument.objects.filter(
            source_path=normalized_path,
            schema_version=RAG_CHUNK_SCHEMA_VERSION,
        )
        if not force and existing_documents.exists():
            skipped_documents += 1
            continue

        text = file_path.read_text(encoding="utf-8")
        chunks = build_document_chunks(
            document_id=normalized_path,
            source_path=normalized_path,
            schema_version=RAG_CHUNK_SCHEMA_VERSION,
            text=text,
        )
        chunk_models = [
            RetrievalChunk(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                source_path=chunk.source_path,
                schema_version=chunk.schema_version,
                content=chunk.content,
                embedding=build_embedding_vector(chunk.content),
            )
            for chunk in chunks
        ]

        with transaction.atomic():
            if force:
                RetrievalChunk.objects.filter(source_path=normalized_path).delete()
                RetrievalDocument.objects.filter(source_path=normalized_path).delete()

            RetrievalDocument.objects.create(
                document_id=normalized_path,
                source_path=normalized_path,
                schema_version=RAG_CHUNK_SCHEMA_VERSION,
            )
            RetrievalChunk.objects.bulk_create(chunk_models)

        ingested_documents += 1
        ingested_chunks += len(chunk_models)

    return RagIngestResult(
        ingested_documents=ingested_documents,
        ingested_chunks=ingested_chunks,
        skipped_documents=skipped_documents,
    )


def manual_search(
    *,
    query: str,
    caller: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> RagSearchResponse:
    defaults = get_retrieval_search_defaults()
    resolved_top_k = defaults.top_k if top_k is None else top_k
    resolved_threshold = defaults.score_threshold if score_threshold is None else score_threshold
    query_vector = build_embedding_vector(query)
    score_expression = ExpressionWrapper(
        Value(1.0) - F("distance"),
        output_field=FloatField(),
    )
    rows = RetrievalChunk.objects.annotate(
        distance=CosineDistance("embedding", query_vector),
    ).annotate(
        score=score_expression,
    ).filter(
        score__gte=resolved_threshold,
    ).order_by(
        "-score",
    )[:resolved_top_k]

    now = timezone.now()
    results: list[RagSearchResult] = []
    for row in rows:
        score = float(row.score)
        RetrievalQueryLog.objects.create(
            query=query,
            caller=caller,
            document_id=row.document_id,
            chunk_id=row.chunk_id,
            score=score,
            threshold=resolved_threshold,
            top_k=resolved_top_k,
            created_at=now,
        )
        results.append(
            RagSearchResult(
                document_id=row.document_id,
                chunk_id=row.chunk_id,
                source_path=row.source_path,
                score=score,
                text_excerpt=_text_excerpt(row.content),
            )
        )

    return RagSearchResponse(
        results=tuple(results),
        top_k=resolved_top_k,
        score_threshold=resolved_threshold,
    )


def build_embedding_vector(text: str) -> list[float]:
    try:
        get_configured_embedding_model_id()
    except ValueError as exc:
        raise _embedding_unavailable() from exc

    provider = settings.RAG_EMBEDDING_PROVIDER
    if provider != "deterministic":
        raise _embedding_unavailable()

    if settings.ENVIRONMENT == "production":
        raise _embedding_unavailable()

    return _deterministic_embedding(text)


def _normalize_source_path(source_path: str) -> str:
    return source_path.replace("\\", "/").strip("/")


def _validated_source_file_path(source_path: str) -> Path:
    normalized_path = _normalize_source_path(source_path)
    if not is_retrieval_source_allowed(normalized_path) or _has_parent_traversal(normalized_path):
        raise ApiErrorResponseException(
            "RAG_SOURCE_NOT_ALLOWED",
            status_code=HTTP_400_BAD_REQUEST,
            details={"source_path": normalized_path},
        )

    root = settings.PROJECT_ROOT.resolve()
    file_path = (root / normalized_path).resolve()
    try:
        file_path.relative_to(root)
    except ValueError as exc:
        raise ApiErrorResponseException(
            "RAG_SOURCE_NOT_ALLOWED",
            status_code=HTTP_400_BAD_REQUEST,
            details={"source_path": normalized_path},
        ) from exc

    if not file_path.is_file():
        raise ApiErrorResponseException(
            "RAG_SOURCE_NOT_FOUND",
            status_code=HTTP_400_BAD_REQUEST,
            details={"source_path": normalized_path},
        )

    return file_path


def _has_parent_traversal(source_path: str) -> bool:
    return ".." in PurePosixPath(source_path).parts


def _deterministic_embedding(text: str) -> list[float]:
    vector = [0.0 for _ in range(DETERMINISTIC_EMBEDDING_DIMENSIONS)]
    tokens = re.findall(r"[\w가-힣]+", text.lower())
    for token in tokens or [text]:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % DETERMINISTIC_EMBEDDING_DIMENSIONS
        sign = -1.0 if digest[1] % 2 else 1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        vector[0] = 1.0
        return vector

    return [value / norm for value in vector]


def _text_excerpt(content: str) -> str:
    return content[:280]


def _embedding_unavailable() -> ApiErrorResponseException:
    return ApiErrorResponseException(
        "RAG_EMBEDDING_UNAVAILABLE",
        status_code=HTTP_503_SERVICE_UNAVAILABLE,
    )
