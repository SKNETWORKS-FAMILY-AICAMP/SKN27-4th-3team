import os
from dataclasses import dataclass
from typing import Any

from llm.generation.adapter import (
    LlmOptions,
    generate_llm_ui_text,
    has_valid_api_key_shape,
    read_options,
    repo_root,
)

from backend.config import settings
from backend.apps.llm.models import LlmGeneration


PURPOSE_RESULT_SUMMARY = "result_summary"
PURPOSE_TURN_FLAVOR_TEXT = "turn_flavor_text"
PURPOSE_FINAL_DUEL_DIALOGUE = "final_duel_dialogue"
DISPLAY_SLOT_DUEL_DIALOGUE = "duel_dialogue"
LLM_SMOKE_PURPOSE = PURPOSE_TURN_FLAVOR_TEXT


@dataclass(frozen=True)
class LlmPurposeDefault:
    model_id: str
    timeout_seconds: float
    temperature: float
    max_output_tokens: int


LLM_PURPOSE_DEFAULTS = {
    PURPOSE_TURN_FLAVOR_TEXT: LlmPurposeDefault(
        model_id="llama-3.1-8b-instant",
        timeout_seconds=3,
        temperature=0.4,
        max_output_tokens=160,
    ),
    PURPOSE_FINAL_DUEL_DIALOGUE: LlmPurposeDefault(
        model_id="llama-3.3-70b-versatile",
        timeout_seconds=5,
        temperature=0.5,
        max_output_tokens=400,
    ),
    PURPOSE_RESULT_SUMMARY: LlmPurposeDefault(
        model_id="llama-3.3-70b-versatile",
        timeout_seconds=5,
        temperature=0.4,
        max_output_tokens=500,
    ),
}

SAFE_METADATA_KEYS = {
    "status",
    "provider",
    "model_id",
    "latency_ms",
    "reason",
    "error_code",
    "error_reason",
    "violations",
    "status_code",
    "error_type",
    "gateway_error_code",
}
SMOKE_SAFE_DETAIL_KEYS = {
    "reason",
    "error_reason",
    "status_code",
    "error_type",
    "gateway_error_code",
    "violations",
    "latency_ms",
}


@dataclass(frozen=True)
class LlmSmokeCheckResult:
    ok: bool
    required: bool
    status: str
    reason: str | None
    provider: str
    model_id: str | None
    safe_details: dict[str, Any]


def build_disabled_llm_summary() -> dict[str, Any]:
    return {
        "enabled": False,
        "text": None,
        "generation_id": None,
    }


def run_required_provider_smoke_check() -> LlmSmokeCheckResult:
    if not settings.LLM_REQUIRED:
        return LlmSmokeCheckResult(
            ok=True,
            required=False,
            status="skipped",
            reason="llm_not_required",
            provider=os.environ.get("LLM_PROVIDER", "groq").strip() or "groq",
            model_id=LLM_PURPOSE_DEFAULTS[LLM_SMOKE_PURPOSE].model_id,
            safe_details={},
        )

    options = build_llm_options(LLM_SMOKE_PURPOSE)
    precheck_failure = _llm_smoke_precheck_failure(options)
    if precheck_failure is not None:
        return precheck_failure

    llm_text = generate_llm_ui_text(
        LLM_SMOKE_PURPOSE,
        _llm_smoke_payload(),
        options=options,
        dry_run=False,
    )
    metadata = dict(llm_text.get("metadata") or {})
    status = str(metadata.get("status") or "unknown")
    if llm_text.get("enabled") is True and status == "succeeded" and llm_text.get("text"):
        return LlmSmokeCheckResult(
            ok=True,
            required=True,
            status="succeeded",
            reason=None,
            provider=options.provider,
            model_id=options.model_id,
            safe_details=_safe_smoke_details(metadata),
        )

    return LlmSmokeCheckResult(
        ok=False,
        required=True,
        status="failed",
        reason=_llm_smoke_failure_reason(metadata),
        provider=options.provider,
        model_id=options.model_id,
        safe_details=_safe_smoke_details(metadata),
    )


def build_llm_options(purpose: str) -> LlmOptions:
    defaults = _purpose_defaults(purpose)
    base_options = read_options(repo_root())
    env_prefix = f"LLM_{purpose.upper()}".replace("-", "_")

    return LlmOptions(
        provider=os.environ.get("LLM_PROVIDER", base_options.provider).strip() or "groq",
        api_key=base_options.api_key,
        model_id=os.environ.get(
            f"{env_prefix}_MODEL_ID",
            defaults.model_id,
        ).strip(),
        base_url=base_options.base_url,
        timeout_seconds=float(
            os.environ.get(f"{env_prefix}_TIMEOUT_SECONDS", defaults.timeout_seconds)
        ),
        max_output_tokens=int(
            os.environ.get(f"{env_prefix}_MAX_OUTPUT_TOKENS", defaults.max_output_tokens)
        ),
        temperature=float(
            os.environ.get(f"{env_prefix}_TEMPERATURE", defaults.temperature)
        ),
        disabled=base_options.disabled,
    )


def _llm_smoke_precheck_failure(options: LlmOptions) -> LlmSmokeCheckResult | None:
    reason = None
    if options.disabled:
        reason = "llm_disabled"
    elif options.provider != "groq":
        reason = "unsupported_provider"
    elif not options.api_key:
        reason = "missing_api_key"
    elif not has_valid_api_key_shape(options.api_key):
        reason = "invalid_api_key_format"
    elif not options.model_id:
        reason = "missing_model_id"

    if reason is None:
        return None

    return LlmSmokeCheckResult(
        ok=False,
        required=True,
        status="failed",
        reason=reason,
        provider=options.provider,
        model_id=options.model_id or None,
        safe_details={"reason": reason},
    )


def _llm_smoke_payload() -> dict[str, Any]:
    return {
        "turn_result": {
            "turn_number": 1,
            "player_action": {
                "code": "insight",
                "display_name": "간파",
                "info_target_key": "mirror_surface",
                "timeout_applied": False,
            },
            "public_log": {
                "turn_number": 1,
                "text": "거울 표면에 희미한 금속성 안개가 번졌다.",
                "log_key": "smoke_check",
            },
            "match_outcome": "unresolved",
        },
        "display_slot": "right_apparition_message",
        "apparition_alias": "괴이",
    }


def _llm_smoke_failure_reason(metadata: dict[str, Any]) -> str:
    reason = metadata.get("error_reason") or metadata.get("reason")
    if isinstance(reason, str) and reason:
        return reason
    return "provider_error"


def _safe_smoke_details(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if key in SMOKE_SAFE_DETAIL_KEYS
    }


def generate_result_summary(
    *,
    match_result: dict[str, Any],
    match_id: int,
    user_id: int,
) -> dict[str, Any]:
    llm_text = generate_ui_text(
        purpose=PURPOSE_RESULT_SUMMARY,
        payload={"match_result": match_result},
        match_id=match_id,
        turn_id=None,
        user_id=user_id,
    )
    if not llm_text["enabled"] or llm_text["text"] is None:
        return build_disabled_llm_summary()

    return {
        "enabled": True,
        "text": llm_text["text"],
        "generation_id": llm_text["generation_id"],
    }


def generate_turn_flavor_text(
    *,
    turn_result: dict[str, Any],
    match_id: int,
    turn_id: int,
    user_id: int,
    display_slot: str,
    apparition_alias: str | None,
) -> dict[str, Any]:
    return generate_ui_text(
        purpose=PURPOSE_TURN_FLAVOR_TEXT,
        payload={
            "turn_result": turn_result,
            "display_slot": display_slot,
            "apparition_alias": apparition_alias,
        },
        match_id=match_id,
        turn_id=turn_id,
        user_id=user_id,
    )


def generate_final_duel_dialogue(
    *,
    match_payload: dict[str, Any],
    player_message: str,
    match_id: int,
    user_id: int,
) -> dict[str, Any]:
    return generate_ui_text(
        purpose=PURPOSE_FINAL_DUEL_DIALOGUE,
        payload={
            **match_payload,
            "player_message": player_message,
            "display_slot": DISPLAY_SLOT_DUEL_DIALOGUE,
        },
        match_id=match_id,
        turn_id=None,
        user_id=user_id,
    )


def generate_ui_text(
    *,
    purpose: str,
    payload: dict[str, Any],
    match_id: int | None,
    turn_id: int | None,
    user_id: int | None,
) -> dict[str, Any]:
    options = build_llm_options(purpose)
    llm_text = generate_llm_ui_text(
        purpose,
        payload,
        options=options,
        dry_run=False,
    )
    generation = _record_generation(
        llm_text=llm_text,
        match_id=match_id,
        turn_id=turn_id,
        user_id=user_id,
    )
    if not llm_text["enabled"]:
        return {**llm_text, "generation_id": None}

    return {**llm_text, "generation_id": _public_generation_id(generation.id)}


def _record_generation(
    *,
    llm_text: dict[str, Any],
    match_id: int | None,
    turn_id: int | None,
    user_id: int | None,
) -> LlmGeneration:
    metadata = _safe_metadata(llm_text.get("metadata", {}))
    return LlmGeneration.objects.create(
        purpose=llm_text["purpose"],
        provider=str(metadata.get("provider") or ""),
        model_id=metadata.get("model_id"),
        status=str(metadata.get("status") or "unknown"),
        fallback_used=bool(llm_text["fallback_used"]),
        generated_text=llm_text.get("text"),
        match_id=match_id,
        turn_id=turn_id,
        user_id=user_id,
        metadata_json=metadata,
        context_refs_json=list(llm_text.get("context_refs") or []),
    )


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if key in SAFE_METADATA_KEYS
    }


def _purpose_defaults(purpose: str) -> LlmPurposeDefault:
    try:
        return LLM_PURPOSE_DEFAULTS[purpose]
    except KeyError as exc:
        raise ValueError(f"unsupported llm purpose: {purpose}") from exc


def _public_generation_id(value: int) -> str:
    return f"llm_generation_{value}"
