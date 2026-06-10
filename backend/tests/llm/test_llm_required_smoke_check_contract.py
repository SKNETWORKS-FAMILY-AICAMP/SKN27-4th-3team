import os
from io import StringIO

import pytest
from django.core.management import CommandError, call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()


def test_required_provider_smoke_check_skips_provider_call_when_not_required(monkeypatch):
    from backend.apps.llm import services as llm_services

    monkeypatch.setattr(llm_services.settings, "LLM_REQUIRED", False)
    monkeypatch.setattr(
        llm_services,
        "generate_llm_ui_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("provider must not be called when LLM_REQUIRED=false")
        ),
    )

    result = llm_services.run_required_provider_smoke_check()

    assert result.ok is True
    assert result.required is False
    assert result.status == "skipped"
    assert result.reason == "llm_not_required"


def test_required_provider_smoke_check_fails_without_api_key(monkeypatch):
    from backend.apps.llm import services as llm_services
    from llm.generation.adapter import LlmOptions

    monkeypatch.setattr(llm_services.settings, "LLM_REQUIRED", True)
    monkeypatch.setattr(
        llm_services,
        "build_llm_options",
        lambda purpose: LlmOptions(
            provider="groq",
            api_key="",
            model_id="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            timeout_seconds=3,
            max_output_tokens=160,
            temperature=0.4,
            disabled=False,
        ),
    )

    result = llm_services.run_required_provider_smoke_check()

    assert result.ok is False
    assert result.required is True
    assert result.status == "failed"
    assert result.reason == "missing_api_key"
    assert result.provider == "groq"
    assert result.model_id == "llama-3.1-8b-instant"
    assert "api_key" not in result.safe_details
    assert "Authorization" not in repr(result.safe_details)


def test_required_provider_smoke_check_fails_when_disabled(monkeypatch):
    from backend.apps.llm import services as llm_services
    from llm.generation.adapter import LlmOptions

    monkeypatch.setattr(llm_services.settings, "LLM_REQUIRED", True)
    monkeypatch.setattr(
        llm_services,
        "build_llm_options",
        lambda purpose: LlmOptions(
            provider="groq",
            api_key="test-key",
            model_id="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            timeout_seconds=3,
            max_output_tokens=160,
            temperature=0.4,
            disabled=True,
        ),
    )

    result = llm_services.run_required_provider_smoke_check()

    assert result.ok is False
    assert result.status == "failed"
    assert result.reason == "llm_disabled"


def test_required_provider_smoke_check_maps_provider_failure_without_raw_payload(monkeypatch):
    from backend.apps.llm import services as llm_services
    from llm.generation.adapter import LlmOptions

    monkeypatch.setattr(llm_services.settings, "LLM_REQUIRED", True)
    monkeypatch.setattr(
        llm_services,
        "build_llm_options",
        lambda purpose: LlmOptions(
            provider="groq",
            api_key="test-key",
            model_id="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            timeout_seconds=3,
            max_output_tokens=160,
            temperature=0.4,
            disabled=False,
        ),
    )
    monkeypatch.setattr(
        llm_services,
        "generate_llm_ui_text",
        lambda *_args, **_kwargs: {
            "enabled": False,
            "purpose": "turn_flavor_text",
            "text": None,
            "fallback_used": True,
            "generation_id": None,
            "context_refs": [],
            "metadata": {
                "status": "failed",
                "provider": "groq",
                "model_id": "llama-3.1-8b-instant",
                "error_reason": "timeout",
                "system_prompt": "raw prompt must not leak",
                "raw_response": "raw response must not leak",
            },
        },
    )

    result = llm_services.run_required_provider_smoke_check()

    assert result.ok is False
    assert result.status == "failed"
    assert result.reason == "timeout"
    assert result.safe_details == {"error_reason": "timeout"}


def test_required_provider_smoke_check_passes_on_provider_success(monkeypatch):
    from backend.apps.llm import services as llm_services
    from llm.generation.adapter import LlmOptions

    monkeypatch.setattr(llm_services.settings, "LLM_REQUIRED", True)
    monkeypatch.setattr(
        llm_services,
        "build_llm_options",
        lambda purpose: LlmOptions(
            provider="groq",
            api_key="test-key",
            model_id="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            timeout_seconds=3,
            max_output_tokens=160,
            temperature=0.4,
            disabled=False,
        ),
    )
    monkeypatch.setattr(
        llm_services,
        "generate_llm_ui_text",
        lambda *_args, **_kwargs: {
            "enabled": True,
            "purpose": "turn_flavor_text",
            "text": "거울 위로 차가운 숨이 잠깐 번졌다.",
            "fallback_used": False,
            "generation_id": None,
            "context_refs": [],
            "metadata": {
                "status": "succeeded",
                "provider": "groq",
                "model_id": "llama-3.1-8b-instant",
                "latency_ms": 120,
            },
        },
    )

    result = llm_services.run_required_provider_smoke_check()

    assert result.ok is True
    assert result.required is True
    assert result.status == "succeeded"
    assert result.reason is None
    assert result.safe_details == {"latency_ms": 120}


def test_llm_smoke_check_management_command_reports_success(monkeypatch):
    from backend.apps.llm import services as llm_services

    monkeypatch.setattr(
        llm_services,
        "run_required_provider_smoke_check",
        lambda: llm_services.LlmSmokeCheckResult(
            ok=True,
            required=False,
            status="skipped",
            reason="llm_not_required",
            provider="groq",
            model_id="llama-3.1-8b-instant",
            safe_details={},
        ),
    )
    out = StringIO()

    call_command("llm_smoke_check", stdout=out)

    output = out.getvalue()
    assert "llm smoke check ok" in output
    assert "api_key" not in output


def test_llm_smoke_check_management_command_fails_without_secret_leak(monkeypatch):
    from backend.apps.llm import services as llm_services

    monkeypatch.setattr(
        llm_services,
        "run_required_provider_smoke_check",
        lambda: llm_services.LlmSmokeCheckResult(
            ok=False,
            required=True,
            status="failed",
            reason="missing_api_key",
            provider="groq",
            model_id="llama-3.1-8b-instant",
            safe_details={},
        ),
    )

    with pytest.raises(CommandError) as error:
        call_command("llm_smoke_check", stdout=StringIO())

    message = str(error.value)
    assert "llm smoke check failed" in message
    assert "missing_api_key" in message
    assert "api_key=" not in message
