import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
OFFICIAL_API_JSONC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.jsonc"
OFFICIAL_API_JSON = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"


def test_official_strict_json_is_ascii_safe_for_default_powershell_pipeline():
    raw = OFFICIAL_API_JSON.read_bytes()

    assert raw.isascii()
    json.loads(raw.decode("ascii"))


def test_official_strict_json_matches_jsonc_source_semantics():
    source_spec = json.loads(OFFICIAL_API_JSONC.read_text(encoding="utf-8"))
    strict_spec = json.loads(OFFICIAL_API_JSON.read_text(encoding="ascii"))

    assert strict_spec == source_spec


def test_official_api_spec_includes_password_reset_contract_endpoints_and_errors():
    spec = json.loads(OFFICIAL_API_JSON.read_text(encoding="ascii"))

    endpoints = {
        endpoint["id"]: endpoint
        for endpoint in spec["endpoints"]
        if endpoint["id"].startswith("auth.password_reset.")
    }

    assert set(endpoints) == {
        "auth.password_reset.request",
        "auth.password_reset.confirm",
    }

    request_endpoint = endpoints["auth.password_reset.request"]
    assert request_endpoint["method"] == "POST"
    assert request_endpoint["path"] == "/api/v1/auth/password-reset/request"
    assert request_endpoint["auth_required"] is False
    assert request_endpoint["csrf_required"] is True
    assert request_endpoint["request"]["body"] == {"email": "string:email"}
    assert request_endpoint["response"]["data"] == {"accepted": True}
    assert "PASSWORD_RESET_DELIVERY_UNAVAILABLE" in request_endpoint["errors"]

    confirm_endpoint = endpoints["auth.password_reset.confirm"]
    assert confirm_endpoint["method"] == "POST"
    assert confirm_endpoint["path"] == "/api/v1/auth/password-reset/confirm"
    assert confirm_endpoint["auth_required"] is False
    assert confirm_endpoint["csrf_required"] is True
    assert confirm_endpoint["request"]["body"] == {
        "token": "string",
        "new_password": "string",
    }
    assert confirm_endpoint["response"]["data"] == {"password_reset": True}
    assert {
        "PASSWORD_RESET_TOKEN_INVALID",
        "PASSWORD_RESET_TOKEN_EXPIRED",
        "PASSWORD_RESET_TOKEN_USED",
    }.issubset(set(confirm_endpoint["errors"]))

    assert "PASSWORD_RESET_TOKEN_INVALID" in spec["error_codes"]
    assert "PASSWORD_RESET_TOKEN_EXPIRED" in spec["error_codes"]
    assert "PASSWORD_RESET_TOKEN_USED" in spec["error_codes"]
    assert "PASSWORD_RESET_DELIVERY_UNAVAILABLE" in spec["error_codes"]


def test_official_api_spec_includes_rag_manual_ingest_search_contract():
    spec = json.loads(OFFICIAL_API_JSON.read_text(encoding="ascii"))

    endpoints = {
        endpoint["id"]: endpoint
        for endpoint in spec["endpoints"]
        if endpoint["id"].startswith("retrieval.")
    }

    assert set(endpoints) == {
        "retrieval.ingest",
        "retrieval.search",
    }

    ingest_endpoint = endpoints["retrieval.ingest"]
    assert ingest_endpoint["method"] == "POST"
    assert ingest_endpoint["path"] == "/api/v1/retrieval/ingest"
    assert ingest_endpoint["auth_required"] is True
    assert ingest_endpoint["staff_required"] is True
    assert ingest_endpoint["csrf_required"] is True
    assert ingest_endpoint["request"]["body"] == {
        "source_paths": "array:string:minItems=1,maxItems=20",
        "force": "boolean:default=false",
    }
    assert ingest_endpoint["response"]["data"] == {
        "ingested_documents": "integer",
        "ingested_chunks": "integer",
        "skipped_documents": "integer",
    }
    assert "RAG_SOURCE_NOT_ALLOWED" in ingest_endpoint["errors"]
    assert "RAG_SOURCE_NOT_FOUND" in ingest_endpoint["errors"]
    assert "RAG_EMBEDDING_UNAVAILABLE" in ingest_endpoint["errors"]

    search_endpoint = endpoints["retrieval.search"]
    assert search_endpoint["method"] == "POST"
    assert search_endpoint["path"] == "/api/v1/retrieval/search"
    assert search_endpoint["auth_required"] is True
    assert search_endpoint["staff_required"] is True
    assert search_endpoint["csrf_required"] is True
    assert search_endpoint["request"]["body"] == {
        "query": "string:minLength=1,maxLength=300",
        "caller": "string:minLength=1,maxLength=80",
        "top_k": "integer:min=1,max=20,default=6",
        "score_threshold": "number:min=0,max=1,default=0.72",
    }
    assert search_endpoint["response"]["data"] == {
        "results": [{"$ref": "shared_schemas.RetrievalSearchResult"}],
        "top_k": "integer",
        "score_threshold": "number",
    }
    assert "RAG_ACCESS_DENIED" in search_endpoint["errors"]
    assert "RAG_EMBEDDING_UNAVAILABLE" in search_endpoint["errors"]

    assert "RetrievalSearchResult" in spec["shared_schemas"]
    assert "RAG_ACCESS_DENIED" in spec["error_codes"]
    assert "RAG_SOURCE_NOT_ALLOWED" in spec["error_codes"]
    assert "RAG_SOURCE_NOT_FOUND" in spec["error_codes"]
    assert "RAG_EMBEDDING_UNAVAILABLE" in spec["error_codes"]
