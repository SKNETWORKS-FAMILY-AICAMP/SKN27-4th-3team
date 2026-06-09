from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
LLM_DIR = BACKEND_DIR / "apps" / "llm"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(models.Model):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def test_llm_app_defines_generation_log_model_without_prompt_or_raw_response_storage():
    source = _read(LLM_DIR / "models.py")

    assert "class LlmGeneration(models.Model):" in source
    assert "db_table = \"llm_generations\"" in source
    assert "models.ForeignKey" not in source
    assert "on_delete=" not in source

    generation_source = _class_source(source, "LlmGeneration")
    assert "purpose = models.TextField()" in generation_source
    assert "provider = models.TextField()" in generation_source
    assert "model_id = models.TextField(null=True, blank=True)" in generation_source
    assert "status = models.TextField()" in generation_source
    assert "fallback_used = models.BooleanField()" in generation_source
    assert "generated_text = models.TextField(null=True, blank=True)" in generation_source
    assert "match_id = models.PositiveBigIntegerField(null=True, blank=True)" in generation_source
    assert "turn_id = models.PositiveBigIntegerField(null=True, blank=True)" in generation_source
    assert "user_id = models.PositiveBigIntegerField(null=True, blank=True)" in generation_source
    assert "metadata_json = models.JSONField(default=dict)" in generation_source
    assert "context_refs_json = models.JSONField(default=list)" in generation_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in generation_source

    forbidden_fields = (
        "prompt",
        "system_prompt",
        "user_prompt",
        "raw_response",
        "provider_response",
        "api_key",
        "authorization",
        "cookie",
        "csrf",
    )
    lowered_source = generation_source.lower()
    for field_name in forbidden_fields:
        assert field_name not in lowered_source


def test_llm_purpose_defaults_follow_owner_decision_and_can_be_overridden(monkeypatch):
    from backend.apps.llm import services as llm_services

    assert llm_services.LLM_PURPOSE_DEFAULTS["turn_flavor_text"].model_id == (
        "llama-3.1-8b-instant"
    )
    assert llm_services.LLM_PURPOSE_DEFAULTS["turn_flavor_text"].timeout_seconds == 3
    assert llm_services.LLM_PURPOSE_DEFAULTS["turn_flavor_text"].temperature == 0.4
    assert llm_services.LLM_PURPOSE_DEFAULTS["turn_flavor_text"].max_output_tokens == 160

    assert llm_services.LLM_PURPOSE_DEFAULTS["final_duel_dialogue"].model_id == (
        "llama-3.3-70b-versatile"
    )
    assert llm_services.LLM_PURPOSE_DEFAULTS["final_duel_dialogue"].timeout_seconds == 5
    assert llm_services.LLM_PURPOSE_DEFAULTS["final_duel_dialogue"].temperature == 0.5
    assert llm_services.LLM_PURPOSE_DEFAULTS["final_duel_dialogue"].max_output_tokens == 400

    assert llm_services.LLM_PURPOSE_DEFAULTS["result_summary"].model_id == (
        "llama-3.3-70b-versatile"
    )
    assert llm_services.LLM_PURPOSE_DEFAULTS["result_summary"].timeout_seconds == 5
    assert llm_services.LLM_PURPOSE_DEFAULTS["result_summary"].temperature == 0.4
    assert llm_services.LLM_PURPOSE_DEFAULTS["result_summary"].max_output_tokens == 500

    monkeypatch.setenv("LLM_TURN_FLAVOR_TEXT_MODEL_ID", "override-model")
    options = llm_services.build_llm_options("turn_flavor_text")

    assert options.provider == "groq"
    assert options.model_id == "override-model"
    assert options.timeout_seconds == 3


def test_llm_disabled_summary_shape_is_stable():
    from backend.apps.llm.services import build_disabled_llm_summary

    assert build_disabled_llm_summary() == {
        "enabled": False,
        "text": None,
        "generation_id": None,
    }
