import os
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from rest_framework.test import APIClient

django.setup()


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
RETRIEVAL_DIR = BACKEND_DIR / "apps" / "retrieval"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def test_retrieval_manual_api_modules_routes_and_serializers_exist():
    serializers_source = _read(RETRIEVAL_DIR / "serializers.py")
    views_source = _read(RETRIEVAL_DIR / "views.py")
    urls_source = _read(RETRIEVAL_DIR / "urls.py")
    project_urls_source = _read(BACKEND_DIR / "config" / "urls.py")

    assert "class RagIngestRequestSerializer(" in serializers_source
    assert "class RagSearchRequestSerializer(" in serializers_source
    assert "class RagSearchResultSerializer(" in serializers_source
    assert "source_paths = serializers.ListField(" in serializers_source
    assert "max_length=20" in serializers_source
    assert "top_k = serializers.IntegerField(" in serializers_source
    assert "max_value=20" in serializers_source
    assert "score_threshold = serializers.FloatField(" in serializers_source

    assert "class RagIngestView(APIView):" in views_source
    assert "class RagSearchView(APIView):" in views_source
    assert "@method_decorator(csrf_protect, name=\"dispatch\")" in views_source
    assert "_require_staff_user(request)" in views_source
    assert "retrieval_services.manual_ingest_sources(" in views_source
    assert "retrieval_services.manual_search(" in views_source

    assert "app_name = \"retrieval\"" in urls_source
    assert "path(\"ingest\", RagIngestView.as_view()" in urls_source
    assert "path(\"search\", RagSearchView.as_view()" in urls_source
    assert "api/v1/retrieval/" in project_urls_source
    assert "backend.apps.retrieval.urls" in project_urls_source


def test_rag_ingest_without_csrf_returns_missing_csrf_error():
    response = APIClient(enforce_csrf_checks=True).post(
        "/api/v1/retrieval/ingest",
        {"source_paths": ["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"]},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_TOKEN_MISSING"


def test_rag_search_without_auth_returns_auth_required_error():
    response = APIClient().post(
        "/api/v1/retrieval/search",
        {"query": "결전 조건", "caller": "manual_admin"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_rag_ingest_rejects_non_staff_user(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.retrieval import views as retrieval_views

    monkeypatch.setattr(
        auth_services,
        "get_current_session",
        lambda **_kwargs: SimpleNamespace(user={"id": "7"}),
    )
    monkeypatch.setattr(
        retrieval_views.User.objects,
        "get",
        lambda **_kwargs: SimpleNamespace(id=7, is_staff=False),
    )

    response = APIClient().post(
        "/api/v1/retrieval/ingest",
        {"source_paths": ["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"]},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "RAG_ACCESS_DENIED"


def test_rag_ingest_view_delegates_to_service_for_staff_user(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.retrieval import services as retrieval_services
    from backend.apps.retrieval import views as retrieval_views

    calls = []

    monkeypatch.setattr(
        auth_services,
        "get_current_session",
        lambda **_kwargs: SimpleNamespace(user={"id": "7"}),
    )
    monkeypatch.setattr(
        retrieval_views.User.objects,
        "get",
        lambda **_kwargs: SimpleNamespace(id=7, is_staff=True),
    )
    monkeypatch.setattr(
        retrieval_services,
        "manual_ingest_sources",
        lambda **kwargs: calls.append(kwargs)
        or SimpleNamespace(ingested_documents=1, ingested_chunks=2, skipped_documents=0),
    )

    response = APIClient().post(
        "/api/v1/retrieval/ingest",
        {
            "source_paths": ["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"],
            "force": True,
        },
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "ingested_documents": 1,
        "ingested_chunks": 2,
        "skipped_documents": 0,
    }
    assert calls == [
        {
            "source_paths": ["docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md"],
            "force": True,
        }
    ]


def test_rag_search_view_delegates_to_service_for_staff_user(monkeypatch):
    from backend.apps.accounts import services as auth_services
    from backend.apps.retrieval import services as retrieval_services
    from backend.apps.retrieval import views as retrieval_views

    calls = []

    monkeypatch.setattr(
        auth_services,
        "get_current_session",
        lambda **_kwargs: SimpleNamespace(user={"id": "7"}),
    )
    monkeypatch.setattr(
        retrieval_views.User.objects,
        "get",
        lambda **_kwargs: SimpleNamespace(id=7, is_staff=True),
    )
    monkeypatch.setattr(
        retrieval_services,
        "manual_search",
        lambda **kwargs: calls.append(kwargs)
        or SimpleNamespace(
            results=[
                SimpleNamespace(
                    document_id="doc-1",
                    chunk_id="doc-1:1",
                    source_path="docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
                    score=0.81,
                    text_excerpt="검색 근거",
                )
            ],
            top_k=6,
            score_threshold=0.72,
        ),
    )

    response = APIClient().post(
        "/api/v1/retrieval/search",
        {"query": "결전 조건", "caller": "manual_admin"},
        format="json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "results": [
            {
                "document_id": "doc-1",
                "chunk_id": "doc-1:1",
                "source_path": "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
                "score": 0.81,
                "text_excerpt": "검색 근거",
            }
        ],
        "top_k": 6,
        "score_threshold": 0.72,
    }
    assert calls == [
        {
            "query": "결전 조건",
            "caller": "manual_admin",
            "top_k": 6,
            "score_threshold": 0.72,
        }
    ]
