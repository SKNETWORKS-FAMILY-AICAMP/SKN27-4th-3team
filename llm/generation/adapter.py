"""Groq 기반 LLM 생성 adapter.

이 모듈은 백엔드에서 import 가능한 LLM 생성 함수를 제공한다.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm.prompts.prompt_templates import SUPPORTED_PURPOSES, build_generation_input

try:
    from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq
except ImportError:  # pragma: no cover - 로컬 실험 환경별 선택 의존성
    APIConnectionError = None
    APIStatusError = None
    APITimeoutError = None
    Groq = None


RESULT_REASONS = {"seal_success", "sanity_zero", "curse_marks_loss", "turn_limit", "unresolved"}
DEMO_REFERENCE_NAMES = {"이안", "피티", "피치", "엘리자베스", "무명(無名)의 저주", "무명의 저주"}

NEGATIVE_RESULT_WORDS = {"패배", "패배했다", "실패했다", "실패로 끝", "실종", "무너졌다", "빼앗겼"}
POSITIVE_RESULT_WORDS = {"승리", "승리했다", "성공했다", "해방되었다", "봉인했다", "완성되었다"}
OPS_FORBIDDEN_WORDS = {"보상", "랭킹", "제재", "매칭", "룰 변경", "운영 조치"}
PERSONALITY_JUDGMENT_WORDS = {
    "비겁",
    "비겁했",
    "잔혹",
    "악하다",
    "악했",
    "나약",
    "정신병",
    "미친",
}
NEXT_ACTION_WORDS = {"다음 행동", "다음 턴 괴이", "괴이는 다음"}
ACTION_JUDGMENT_WORDS = {"성공했다", "실패했다", "성공", "실패", "획득했다", "얻었다", "제공했다"}
UNSUPPORTED_CLUE_WORDS = {"진짜 단서", "거짓 단서", "단서 획득", "단서를 얻", "단서를 제공"}
UNSUPPORTED_TRUTH_WORDS = {"비밀", "진실", "드러났다", "밝혀졌다", "원인"}

TEXT_LIMITS = {
    "result_summary": {"min_chars": 80, "max_chars": 240, "min_sentences": 2, "max_sentences": 4},
    "turn_flavor_text": {"min_chars": 20, "max_chars": 90, "min_lines": 1, "max_lines": 2, "max_line_chars": 45},
    "style_summary": {"min_chars": 40, "max_chars": 120, "min_sentences": 1, "max_sentences": 2},
    "match_log_summary": {"min_lines": 3, "max_lines": 5, "max_line_chars": 100},
}


@dataclass(frozen=True)
class LlmOptions:
    provider: str
    api_key: str
    model_id: str
    base_url: str
    timeout_seconds: float
    max_output_tokens: int
    temperature: float
    disabled: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def read_options(root: Path) -> LlmOptions:
    load_dotenv(root / ".env")

    return LlmOptions(
        provider=os.environ.get("LLM_PROVIDER", "groq").strip() or "groq",
        api_key=os.environ.get("LLM_API_KEY", "").strip(),
        model_id=os.environ.get("LLM_MODEL_ID", "").strip(),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
        timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS", "30")),
        max_output_tokens=int(os.environ.get("LLM_MAX_OUTPUT_TOKENS", "400")),
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.4")),
        disabled=os.environ.get("LLM_DISABLED", "false").strip().lower() in {"1", "true", "yes", "on"},
    )


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    purpose = payload.get("purpose")
    if purpose not in SUPPORTED_PURPOSES:
        raise ValueError(f"지원하지 않는 purpose입니다: {purpose}")
    return payload


def generate_llm_result(
    purpose: str,
    payload: dict[str, Any],
    options: LlmOptions | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    input_payload = {**payload, "purpose": purpose}
    generation_input = build_generation_input(input_payload)
    llm_options = options or read_options(repo_root())
    return generate(generation_input, llm_options, dry_run)


def generate_llm_ui_text(
    purpose: str,
    payload: dict[str, Any],
    options: LlmOptions | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    input_payload = {**payload, "purpose": purpose}
    generation_input = build_generation_input(input_payload)
    llm_options = options or read_options(repo_root())
    generation_result = generate(generation_input, llm_options, dry_run)
    return frontend_payload(generation_input, generation_result)


def result_payload(
    generation_input: dict[str, Any],
    status: str,
    text: str | None,
    fallback_used: bool,
    options: LlmOptions,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "purpose": generation_input["purpose"],
        "status": status,
        "text": text,
        "fallback_used": fallback_used,
        "provider": options.provider,
        "model_id": options.model_id or None,
        "generation_id": None,
        "context_refs": generation_input.get("context_refs", []),
        "metadata": metadata,
    }


def frontend_payload(generation_input: dict[str, Any], generation_result: dict[str, Any]) -> dict[str, Any]:
    payload = generation_input["payload"]
    result_metadata = {
        key: value
        for key, value in generation_result.get("metadata", {}).items()
        if key not in {"system_prompt", "user_prompt"}
    }
    metadata = {
        "status": generation_result["status"],
        "provider": generation_result["provider"],
        "model_id": generation_result["model_id"],
        **result_metadata,
    }
    return {
        "enabled": generation_result["status"] == "succeeded" and generation_result.get("text") is not None,
        "purpose": generation_result["purpose"],
        "text": generation_result.get("text"),
        "display_slot": payload.get("display_slot"),
        "fallback_used": generation_result["fallback_used"],
        "generation_id": generation_result.get("generation_id"),
        "context_refs": generation_result.get("context_refs", []),
        "metadata": metadata,
    }


def skipped(generation_input: dict[str, Any], options: LlmOptions, reason: str) -> dict[str, Any]:
    return result_payload(generation_input, "skipped", None, True, options, {"reason": reason})


def has_valid_api_key_shape(api_key: str) -> bool:
    if not api_key:
        return False
    if any(ord(char) > 127 for char in api_key):
        return False
    lowered = api_key.lower()
    if "실제" in api_key or "여기에" in api_key or "placeholder" in lowered:
        return False
    return True


def failed(
    generation_input: dict[str, Any],
    options: LlmOptions,
    error_reason: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {"error_code": "LLM_SUMMARY_UNAVAILABLE", "error_reason": error_reason}
    if extra:
        metadata.update(extra)
    return result_payload(generation_input, "failed", None, True, options, metadata)


def call_groq(generation_input: dict[str, Any], options: LlmOptions) -> tuple[str, int]:
    if Groq is not None:
        return call_groq_sdk(generation_input, options)
    return call_groq_urllib(generation_input, options)


def call_groq_sdk(generation_input: dict[str, Any], options: LlmOptions) -> tuple[str, int]:
    client = Groq(api_key=options.api_key, base_url=sdk_base_url(options.base_url), timeout=options.timeout_seconds)
    started_at = time.perf_counter()
    response = client.chat.completions.create(
        model=options.model_id,
        messages=[
            {"role": "system", "content": generation_input["system_prompt"]},
            {"role": "user", "content": generation_input["user_prompt"]},
        ],
        temperature=options.temperature,
        max_tokens=options.max_output_tokens,
    )
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    text = response.choices[0].message.content
    if text is None or not text.strip():
        raise ValueError("empty response text")
    return normalize_generated_text(text), latency_ms


def normalize_generated_text(text: str) -> str:
    lines = []
    for line in text.strip().splitlines():
        normalized = line.strip().strip('"').strip("'").strip()
        if normalized:
            lines.append(normalized)
    return "\n".join(lines)


def sdk_base_url(base_url: str) -> str:
    openai_suffix = "/openai/v1"
    if base_url.endswith(openai_suffix):
        return base_url[: -len(openai_suffix)]
    return base_url


def call_groq_urllib(generation_input: dict[str, Any], options: LlmOptions) -> tuple[str, int]:
    body = {
        "model": options.model_id,
        "messages": [
            {"role": "system", "content": generation_input["system_prompt"]},
            {"role": "user", "content": generation_input["user_prompt"]},
        ],
        "temperature": options.temperature,
        "max_tokens": options.max_output_tokens,
    }
    request = urllib.request.Request(
        f"{options.base_url}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {options.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started_at = time.perf_counter()
    with urllib.request.urlopen(request, timeout=options.timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    payload = json.loads(raw)
    text = normalize_generated_text(payload["choices"][0]["message"]["content"])
    if not text:
        raise ValueError("empty response text")
    return text, latency_ms


def validate_output(generation_input: dict[str, Any], text: str) -> list[str]:
    purpose = generation_input["purpose"]
    payload = generation_input["payload"]
    violations: list[str] = []
    violations.extend(validate_text_shape(purpose, text))

    for name in DEMO_REFERENCE_NAMES:
        if name in text and name not in json.dumps(payload, ensure_ascii=False):
            violations.append("demo_reference_leak")
            break

    if any(word in text for word in OPS_FORBIDDEN_WORDS):
        violations.append("ops_decision_suggestion")
    if any(word in text for word in PERSONALITY_JUDGMENT_WORDS):
        violations.append("personality_judgment")
    if any(word in text for word in NEXT_ACTION_WORDS):
        violations.append("next_action_prediction")
    if purpose in {"turn_flavor_text", "match_log_summary", "style_summary"}:
        violations.extend(validate_non_judgmental_text(text, payload))

    if purpose == "result_summary":
        match_result = payload["match_result"]
        result = match_result["result"]
        reason = match_result["result_reason"]
        if reason not in RESULT_REASONS:
            violations.append("result_reason_conflict")
        if result == "player_win" and any(word in text for word in NEGATIVE_RESULT_WORDS):
            violations.append("result_conflict")
        if result == "player_loss" and any(word in text for word in POSITIVE_RESULT_WORDS):
            violations.append("result_conflict")
        if result == "unresolved" and any(word in text for word in POSITIVE_RESULT_WORDS | NEGATIVE_RESULT_WORDS):
            violations.append("result_conflict")

    if purpose == "style_summary":
        if any(char.isdigit() for char in text):
            violations.append("resource_conflict")

    if purpose == "turn_flavor_text":
        if any(
            word in text
            for word in {
                "공개 로그",
                "출력:",
                "예시",
                "무엇인가",
                "누군가",
                "보이기 시작",
                "온도에",
                "온도는",
                "뜨거움을 더",
                "냄새가 났다",
                "획득했다",
                "진짜 단서",
                "거짓 단서",
                "성공했다",
                "실패했다",
                "비밀",
                "진실",
                "드러났다",
                "밝혀졌다",
                "제공",
                "깨트",
                "부서",
                "달려 있었다",
                "원인",
                "다음 턴",
            }
        ):
            violations.append("unsupported_story_fact")
        public_log_text = payload["turn_result"]["public_log"]["text"]
        if "단서" in text and "단서" not in public_log_text:
            violations.append("unsupported_story_fact")
        if "?" in text or any(word in text for word in {"인가", "듯하다", "것 같다", "마치", "아마"}):
            violations.append("unsupported_story_fact")

    if purpose == "match_log_summary":
        if any(word in text for word in {"추정", "아마", "원인으로 보인다"}):
            violations.append("unsupported_story_fact")

    return sorted(set(violations))


# 판정자가 아닌 purpose에서 입력에 없는 행동 판정이나 단서 진위 표현을 걸러낸다.
def validate_non_judgmental_text(text: str, payload: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    payload_text = json.dumps(payload, ensure_ascii=False)
    if any(word in text for word in ACTION_JUDGMENT_WORDS):
        violations.append("unsupported_action_judgment")
    if any(word in text and word not in payload_text for word in UNSUPPORTED_CLUE_WORDS | UNSUPPORTED_TRUTH_WORDS):
        violations.append("unsupported_story_fact")
    return violations


def count_sentences(text: str) -> int:
    sentences = [part for part in re.split(r"[.!?。！？]+|\n+", text) if part.strip()]
    return len(sentences)


def visible_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def validate_text_shape(purpose: str, text: str) -> list[str]:
    limits = TEXT_LIMITS[purpose]
    violations: list[str] = []
    normalized = text.strip()

    if purpose in {"result_summary", "style_summary"}:
        text_length = len(normalized)
        if text_length < limits["min_chars"] or text_length > limits["max_chars"]:
            violations.append("length_violation")

        sentence_count = count_sentences(normalized)
        if sentence_count < limits["min_sentences"] or sentence_count > limits["max_sentences"]:
            violations.append("sentence_count_violation")
        return violations

    lines = visible_lines(normalized)
    if "min_chars" in limits or "max_chars" in limits:
        text_length = len(normalized)
        if text_length < limits["min_chars"] or text_length > limits["max_chars"]:
            violations.append("length_violation")
    if len(lines) < limits["min_lines"] or len(lines) > limits["max_lines"]:
        violations.append("line_count_violation")
    if any(len(line) > limits["max_line_chars"] for line in lines):
        violations.append("line_length_violation")
    return violations


def generate(generation_input: dict[str, Any], options: LlmOptions, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return result_payload(
            generation_input,
            "skipped",
            None,
            True,
            options,
            {
                "reason": "dry_run",
                "system_prompt": generation_input["system_prompt"],
                "user_prompt": generation_input["user_prompt"],
            },
        )
    if options.disabled:
        return skipped(generation_input, options, "llm_disabled")
    if options.provider != "groq":
        return skipped(generation_input, options, "unsupported_provider")
    if not options.api_key:
        return skipped(generation_input, options, "missing_api_key")
    if not has_valid_api_key_shape(options.api_key):
        return skipped(generation_input, options, "invalid_api_key_format")
    if not options.model_id:
        return skipped(generation_input, options, "missing_model_id")

    try:
        text, latency_ms = call_groq(generation_input, options)
    except Exception as error:
        sdk_failure = classify_groq_sdk_error(error)
        if sdk_failure is not None:
            return failed(generation_input, options, sdk_failure["error_reason"], sdk_failure.get("extra"))
        if isinstance(error, TimeoutError):
            return failed(generation_input, options, "timeout")
        if isinstance(error, urllib.error.HTTPError):
            return failed(generation_input, options, "provider_error", {"status_code": error.code})
        if isinstance(error, urllib.error.URLError):
            return failed(generation_input, options, "provider_error")
        if isinstance(error, (KeyError, IndexError, json.JSONDecodeError, ValueError)):
            return failed(generation_input, options, "response_parse_error")
        return failed(generation_input, options, "provider_error", {"error_type": type(error).__name__})

    violations = validate_output(generation_input, text)
    if violations:
        return failed(
            generation_input,
            options,
            "guardrail_violation",
            {"violations": violations, "rejected_text_preview": text[:120]},
        )
    return result_payload(generation_input, "succeeded", text, False, options, {"latency_ms": latency_ms})


def classify_groq_sdk_error(error: Exception) -> dict[str, Any] | None:
    if APITimeoutError is not None and isinstance(error, APITimeoutError):
        return {"error_reason": "timeout"}
    if APIConnectionError is not None and isinstance(error, APIConnectionError):
        return {
            "error_reason": "provider_error",
            "extra": {"error_type": type(error).__name__},
        }
    if APIStatusError is not None and isinstance(error, APIStatusError):
        extra: dict[str, Any] = {"status_code": error.status_code}
        response_text = getattr(error.response, "text", "")
        if response_text:
            extra["response_preview"] = response_text[:200]
            if "1010" in response_text:
                extra["gateway_error_code"] = "1010"
        return {"error_reason": "provider_error", "extra": extra}
    return None


def default_fixture_path(root: Path, purpose: str) -> Path:
    return root / "llm" / "fixtures" / f"{purpose}.sample.json"
