import os
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()


ROOT_DIR = Path(__file__).resolve().parents[3]


def test_manual_ingest_rejects_source_outside_allowlist():
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.retrieval import services as retrieval_services

    with pytest.raises(ApiErrorResponseException) as error:
        retrieval_services.manual_ingest_sources(
            source_paths=["docs/07_LLM/01_prompt_draft.md"],
            force=False,
        )

    assert error.value.code == "RAG_SOURCE_NOT_ALLOWED"
    assert error.value.status_code == 400


def test_manual_ingest_rejects_missing_allowed_source():
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.retrieval import services as retrieval_services

    missing_path = "docs/09_Approved_Contracts/not-found-rag-source.md"

    with pytest.raises(ApiErrorResponseException) as error:
        retrieval_services.manual_ingest_sources(
            source_paths=[missing_path],
            force=False,
        )

    assert error.value.code == "RAG_SOURCE_NOT_FOUND"
    assert error.value.status_code == 400
    assert error.value.details == {"source_path": missing_path}


def test_embedding_provider_rejects_disabled_missing_model_and_production_deterministic(monkeypatch):
    from backend.apps.common.exceptions import ApiErrorResponseException
    from backend.apps.retrieval import services as retrieval_services

    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_PROVIDER", "disabled")
    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_MODEL_ID", "deterministic-test")

    with pytest.raises(ApiErrorResponseException) as disabled_error:
        retrieval_services.build_embedding_vector("검색어")
    assert disabled_error.value.code == "RAG_EMBEDDING_UNAVAILABLE"
    assert disabled_error.value.status_code == 503

    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_PROVIDER", "deterministic")
    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_MODEL_ID", None)

    with pytest.raises(ApiErrorResponseException) as missing_model_error:
        retrieval_services.build_embedding_vector("검색어")
    assert missing_model_error.value.code == "RAG_EMBEDDING_UNAVAILABLE"

    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_MODEL_ID", "deterministic-test")
    monkeypatch.setattr(retrieval_services.settings, "ENVIRONMENT", "production")

    with pytest.raises(ApiErrorResponseException) as production_error:
        retrieval_services.build_embedding_vector("검색어")
    assert production_error.value.code == "RAG_EMBEDDING_UNAVAILABLE"


def test_deterministic_embedding_is_stable_normalized_and_not_zero(monkeypatch):
    from backend.apps.retrieval import services as retrieval_services

    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_PROVIDER", "deterministic")
    monkeypatch.setattr(retrieval_services.settings, "RAG_EMBEDDING_MODEL_ID", "deterministic-test")
    monkeypatch.setattr(retrieval_services.settings, "ENVIRONMENT", "local")

    first = retrieval_services.build_embedding_vector("결전 조건 진명 조각")
    second = retrieval_services.build_embedding_vector("결전 조건 진명 조각")

    assert first == second
    assert len(first) == retrieval_services.DETERMINISTIC_EMBEDDING_DIMENSIONS
    assert any(value != 0 for value in first)
    assert abs(sum(value * value for value in first) - 1.0) < 0.000001


def test_manual_ingest_skips_existing_document_without_force(monkeypatch):
    from backend.apps.retrieval import services as retrieval_services

    class ExistingDocumentQuery:
        def exists(self):
            return True

    monkeypatch.setattr(
        retrieval_services,
        "_validated_source_file_path",
        lambda source_path: ROOT_DIR / source_path,
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalDocument.objects,
        "filter",
        lambda **_kwargs: ExistingDocumentQuery(),
    )

    result = retrieval_services.manual_ingest_sources(
        source_paths=["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"],
        force=False,
    )

    assert result.ingested_documents == 0
    assert result.ingested_chunks == 0
    assert result.skipped_documents == 1


def test_manual_ingest_replaces_documents_and_chunks_when_forced(monkeypatch):
    from backend.apps.retrieval import services as retrieval_services

    documents_deleted = []
    chunks_deleted = []
    created_documents = []
    created_chunks = []

    class Query:
        def exists(self):
            return False

        def delete(self):
            documents_deleted.append(True)

    class ChunkQuery:
        def delete(self):
            chunks_deleted.append(True)

    monkeypatch.setattr(retrieval_services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(retrieval_services, "build_embedding_vector", lambda text: [1.0, 0.0])
    monkeypatch.setattr(
        retrieval_services,
        "_validated_source_file_path",
        lambda source_path: ROOT_DIR / source_path,
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalDocument.objects,
        "filter",
        lambda **_kwargs: Query(),
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalChunk.objects,
        "filter",
        lambda **_kwargs: ChunkQuery(),
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalDocument.objects,
        "create",
        lambda **kwargs: created_documents.append(kwargs),
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalChunk.objects,
        "bulk_create",
        lambda chunks: created_chunks.extend(chunks),
    )

    result = retrieval_services.manual_ingest_sources(
        source_paths=["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"],
        force=True,
    )

    assert documents_deleted == [True]
    assert chunks_deleted == [True]
    assert created_documents == [
        {
            "document_id": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
            "source_path": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
            "schema_version": retrieval_services.RAG_CHUNK_SCHEMA_VERSION,
        }
    ]
    assert result.ingested_documents == 1
    assert result.ingested_chunks == len(created_chunks)
    assert result.skipped_documents == 0


def test_manual_search_uses_defaults_and_writes_query_log_for_each_returned_result(monkeypatch):
    from backend.apps.retrieval import services as retrieval_services

    now = retrieval_services.timezone.now()
    logged = []
    query_vector = [1.0, 0.0]
    chunk = SimpleNamespace(
        document_id="doc-1",
        chunk_id="doc-1:1",
        source_path="docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
        content="결전 조건과 진명 조각 근거 문장",
        score=0.81,
    )

    class FakeChunkQuery:
        def annotate(self, **_kwargs):
            return self

        def filter(self, **_kwargs):
            return self

        def order_by(self, *_args):
            return self

        def __getitem__(self, item):
            assert item == slice(None, 6, None)
            return [chunk]

    monkeypatch.setattr(retrieval_services.timezone, "now", lambda: now)
    monkeypatch.setattr(retrieval_services, "build_embedding_vector", lambda text: query_vector)
    monkeypatch.setattr(
        retrieval_services.RetrievalChunk.objects,
        "annotate",
        lambda **_kwargs: FakeChunkQuery(),
    )
    monkeypatch.setattr(
        retrieval_services.RetrievalQueryLog.objects,
        "create",
        lambda **kwargs: logged.append(kwargs),
    )

    result = retrieval_services.manual_search(query="결전 조건", caller="manual_admin")

    assert result.top_k == 6
    assert result.score_threshold == 0.72
    assert [item.chunk_id for item in result.results] == ["doc-1:1"]
    assert result.results[0].text_excerpt == "결전 조건과 진명 조각 근거 문장"
    assert logged == [
        {
            "query": "결전 조건",
            "caller": "manual_admin",
            "document_id": "doc-1",
            "chunk_id": "doc-1:1",
            "score": 0.81,
            "threshold": 0.72,
            "top_k": 6,
            "created_at": now,
        }
    ]
