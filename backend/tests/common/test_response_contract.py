import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
OFFICIAL_API_SPEC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"
FIXED_SERVER_TIME = datetime(2026, 6, 2, 0, 0, 0, tzinfo=timezone.utc)


def _official_error_messages() -> dict[str, str]:
    spec = json.loads(OFFICIAL_API_SPEC.read_text(encoding="utf-8"))
    return spec["error_codes"]


def test_error_code_catalog_matches_official_schema_and_is_immutable():
    from backend.apps.common.errors import API_ERROR_MESSAGES

    assert dict(API_ERROR_MESSAGES) == _official_error_messages()

    with pytest.raises(TypeError):
        API_ERROR_MESSAGES["NEW_ERROR"] = "런타임에서 계약 error code를 추가할 수 없다."


def test_make_api_error_uses_official_message_and_copies_details():
    from backend.apps.common.errors import make_api_error

    details = {"match_id": "match_1"}
    api_error = make_api_error("MATCH_NOT_FOUND", details=details)
    details["match_id"] = "changed"

    assert api_error.to_dict() == {
        "code": "MATCH_NOT_FOUND",
        "message": _official_error_messages()["MATCH_NOT_FOUND"],
        "details": {"match_id": "match_1"},
    }


def test_api_error_direct_construction_cannot_override_official_message():
    from backend.apps.common.errors import ApiError

    with pytest.raises(ValueError, match="message"):
        ApiError(
            code="MATCH_NOT_FOUND",
            message="wrong message",
        )


def test_make_api_error_rejects_codes_outside_official_schema():
    from backend.apps.common.errors import make_api_error

    with pytest.raises(ValueError, match="UNKNOWN_ERROR"):
        make_api_error("UNKNOWN_ERROR")


def test_success_envelope_wraps_payload_under_data_and_meta_only():
    from backend.apps.common.responses import success_envelope

    envelope = success_envelope(
        {"match_id": "match_1"},
        request_id="req_1",
        server_time=FIXED_SERVER_TIME,
    )

    assert envelope == {
        "data": {"match_id": "match_1"},
        "meta": {
            "request_id": "req_1",
            "server_time": "2026-06-02T00:00:00Z",
        },
    }
    assert "error" not in envelope


def test_error_envelope_wraps_error_under_error_and_meta_only():
    from backend.apps.common.errors import make_api_error
    from backend.apps.common.responses import error_envelope

    envelope = error_envelope(
        make_api_error("CSRF_TOKEN_MISSING"),
        request_id="req_2",
        server_time=FIXED_SERVER_TIME,
    )

    assert envelope == {
        "error": {
            "code": "CSRF_TOKEN_MISSING",
            "message": _official_error_messages()["CSRF_TOKEN_MISSING"],
            "details": {},
        },
        "meta": {
            "request_id": "req_2",
            "server_time": "2026-06-02T00:00:00Z",
        },
    }
    assert "data" not in envelope


def test_meta_extra_fields_are_allowed_but_cannot_override_required_fields():
    from backend.apps.common.responses import success_envelope

    envelope = success_envelope(
        {"items": []},
        request_id="req_3",
        server_time=FIXED_SERVER_TIME,
        meta={"pagination": {"next": None}},
    )

    assert envelope["meta"] == {
        "request_id": "req_3",
        "server_time": "2026-06-02T00:00:00Z",
        "pagination": {"next": None},
    }

    with pytest.raises(ValueError, match="request_id"):
        success_envelope(
            {},
            request_id="req_4",
            server_time=FIXED_SERVER_TIME,
            meta={"request_id": "other"},
        )


def test_request_id_is_required_at_response_boundary():
    from backend.apps.common.responses import success_envelope

    with pytest.raises(ValueError, match="request_id"):
        success_envelope({}, request_id="", server_time=FIXED_SERVER_TIME)
