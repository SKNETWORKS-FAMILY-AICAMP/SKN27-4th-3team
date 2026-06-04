from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
RETRIEVAL_DIR = BACKEND_DIR / "apps" / "retrieval"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(models.Model):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def test_retrieval_modules_exist_for_task_10_contract():
    assert (RETRIEVAL_DIR / "models.py").exists()
    assert (RETRIEVAL_DIR / "chunking.py").exists()
    assert (RETRIEVAL_DIR / "services.py").exists()


def test_retrieval_models_define_document_chunk_embedding_and_query_log_structure():
    source = _read(RETRIEVAL_DIR / "models.py")

    assert "from pgvector.django import VectorField" in source
    assert "db_table" not in source
    assert "models.JSONField" not in source
    assert "models.ForeignKey" not in source
    assert "on_delete=" not in source

    document_source = _class_source(source, "RetrievalDocument")
    assert "document_id = models.TextField()" in document_source
    assert "source_path = models.TextField()" in document_source
    assert "schema_version = models.TextField()" in document_source

    chunk_source = _class_source(source, "RetrievalChunk")
    assert "document_id = models.TextField()" in chunk_source
    assert "chunk_id = models.TextField()" in chunk_source
    assert "source_path = models.TextField()" in chunk_source
    assert "schema_version = models.TextField()" in chunk_source
    assert "content = models.TextField()" in chunk_source
    assert "embedding = VectorField()" in chunk_source

    query_log_source = _class_source(source, "RetrievalQueryLog")
    assert "query = models.TextField()" in query_log_source
    assert "caller = models.TextField()" in query_log_source
    assert "document_id = models.TextField()" in query_log_source
    assert "chunk_id = models.TextField()" in query_log_source
    assert "score = models.FloatField()" in query_log_source
    assert "threshold = models.FloatField()" in query_log_source
    assert "top_k = models.PositiveIntegerField()" in query_log_source
    assert "created_at = models.DateTimeField()" in query_log_source


def test_retrieval_initial_migration_creates_pgvector_extension_before_vector_field():
    migration_source = _read(RETRIEVAL_DIR / "migrations" / "0001_initial.py")

    assert "from pgvector.django import VectorExtension" in migration_source
    assert "VectorExtension()" in migration_source
    assert migration_source.index("VectorExtension()") < migration_source.index("RetrievalChunk")


def test_retrieval_source_allowlist_includes_only_approved_targets():
    from backend.apps.retrieval.services import is_retrieval_source_allowed

    assert is_retrieval_source_allowed("docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md")
    assert is_retrieval_source_allowed("docs/05_Story_Mode/02_거울_속의_손님.md")
    assert is_retrieval_source_allowed("docs/02_Game_Rules/04_상성_규칙.md")
    assert is_retrieval_source_allowed("docs/02_Game_Rules/99_Game_Rules_구현_확정.md")

    assert not is_retrieval_source_allowed("docs/02_Game_Rules/02_행동_정의.md")
    assert not is_retrieval_source_allowed("docs/02_Game_Rules/07_확률_판정.md")
    assert not is_retrieval_source_allowed("docs/08_Implementation_Contracts/05_프론트_API_연결_계약_초안.md")
    assert not is_retrieval_source_allowed("docs/07_LLM/01_prompt_draft.md")


def test_chunking_uses_approved_size_bounds_overlap_and_payload_fields():
    from backend.apps.retrieval.chunking import (
        DEFAULT_CHUNK_MAX_CHARS,
        DEFAULT_CHUNK_MIN_CHARS,
        MAX_CHUNK_OVERLAP_CHARS,
        build_document_chunks,
    )

    assert DEFAULT_CHUNK_MIN_CHARS == 500
    assert DEFAULT_CHUNK_MAX_CHARS == 900
    assert MAX_CHUNK_OVERLAP_CHARS == 100

    paragraph = "가" * 420
    text = "\n\n".join(paragraph for _ in range(5))
    chunks = build_document_chunks(
        document_id="doc-1",
        source_path="docs/02_Game_Rules/04_상성_규칙.md",
        schema_version="rag-chunk-v1",
        text=text,
    )

    assert len(chunks) >= 2
    for chunk in chunks[:-1]:
        assert DEFAULT_CHUNK_MIN_CHARS <= len(chunk.content) <= DEFAULT_CHUNK_MAX_CHARS
    for index, chunk in enumerate(chunks, start=1):
        assert len(chunk.content) <= DEFAULT_CHUNK_MAX_CHARS
        assert chunk.document_id == "doc-1"
        assert chunk.chunk_id == f"doc-1:{index}"
        assert chunk.source_path == "docs/02_Game_Rules/04_상성_규칙.md"
        assert chunk.schema_version == "rag-chunk-v1"


def test_retrieval_defaults_use_settings_and_embedding_model_has_no_code_default(monkeypatch):
    from backend.config import settings as project_settings
    from backend.apps.retrieval.services import (
        get_configured_embedding_model_id,
        get_retrieval_search_defaults,
    )

    monkeypatch.setattr(project_settings, "RAG_DEFAULT_TOP_K", 6)
    monkeypatch.setattr(project_settings, "RAG_DEFAULT_SCORE_THRESHOLD", 0.72)
    monkeypatch.setattr(project_settings, "RAG_EMBEDDING_MODEL_ID", None)

    defaults = get_retrieval_search_defaults()

    assert defaults.top_k == 6
    assert defaults.score_threshold == 0.72
    with pytest.raises(ValueError, match="RAG_EMBEDDING_MODEL_ID"):
        get_configured_embedding_model_id()

    monkeypatch.setattr(project_settings, "RAG_EMBEDDING_MODEL_ID", "configured-model")
    assert get_configured_embedding_model_id() == "configured-model"

    settings_source = _read(BACKEND_DIR / "config" / "settings.py")
    retrieval_sources = "\n".join(
        _read(RETRIEVAL_DIR / filename)
        for filename in ("models.py", "chunking.py", "services.py")
        if (RETRIEVAL_DIR / filename).exists()
    )
    assert "text-embedding-3-small" not in settings_source
    assert "text-embedding-3-small" not in retrieval_sources


def test_retrieval_code_does_not_implement_provider_llm_or_rule_mutation():
    source = "\n".join(
        _read(RETRIEVAL_DIR / filename)
        for filename in ("models.py", "chunking.py", "services.py")
        if (RETRIEVAL_DIR / filename).exists()
    ).lower()

    forbidden = (
        "openai",
        "llm",
        "generate",
        "provider",
        "mutate_rule",
        "change_outcome",
        "true_name_fragment:+",
        "false_clue:+",
    )
    for word in forbidden:
        assert word not in source
