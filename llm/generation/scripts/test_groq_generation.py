"""Groq 기반 LLM 실험용 CLI.

이 스크립트는 fixture를 prompt로 조립하고, 설정이 준비된 경우 Groq
OpenAI-compatible chat completion API를 호출한다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PURPOSES = {"result_summary", "style_summary", "match_log_summary"}
RESULT_REASONS = {"seal_success", "sanity_zero", "curse_marks_loss", "turn_limit", "unresolved"}
DEMO_REFERENCE_NAMES = {"이안", "피티", "피치", "엘리자베스", "무명(無名)의 저주", "무명의 저주"}

NEGATIVE_RESULT_WORDS = {"패배", "실패", "실종", "무너", "빼앗"}
POSITIVE_RESULT_WORDS = {"승리", "성공", "해방", "봉인했다", "완성"}
OPS_FORBIDDEN_WORDS = {"보상", "랭킹", "제재", "매칭", "룰 변경", "운영 조치"}
PERSONALITY_JUDGMENT_WORDS = {"비겁", "잔혹", "악하다", "나약", "정신병", "미친"}
NEXT_ACTION_WORDS = {"다음 행동", "다음 턴 괴이", "괴이는 다음"}


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
    return Path(__file__).resolve().parents[3]


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


def join_story_result_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value or "")


def build_generation_input(payload: dict[str, Any]) -> dict[str, Any]:
    purpose = payload["purpose"]
    if purpose == "result_summary":
        return build_result_summary_input(payload)
    if purpose == "style_summary":
        return build_style_summary_input(payload)
    if purpose == "match_log_summary":
        return build_match_log_summary_input(payload)
    raise ValueError(f"지원하지 않는 purpose입니다: {purpose}")


def base_system_prompt(extra: str) -> str:
    return "\n".join(
        [
            "너는 게임 판정자가 아니라 서버 판정 이후의 보조 기록자다.",
            "서버가 확정한 결과만 사용해 한국어로 작성한다.",
            "승패, 수치 변화, 진명 조각 획득, 거짓 단서 판정은 새로 판단하지 않는다.",
            "공식 설정이나 룰을 추가하지 않고, 입력에 없는 사실을 만들지 않는다.",
            "데모 스토리 참고 문서는 분위기 참고용이며 입력에 없는 인물명, 사건명, 과거사를 생성하지 않는다.",
            extra,
        ]
    )


def build_result_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    match_result = payload["match_result"]
    resources = match_result["final_resources"]
    story_result_text = join_story_result_text(match_result.get("story_result_text"))
    user_prompt = f"""아래 서버 결과를 바탕으로 결과 화면용 서사 요약을 작성해줘.

[사건]
{match_result["case"]["title"]}

[서버 판정]
- 결과: {match_result["result"]}
- 종료 사유: {match_result["result_reason"]}
- 최종 이성: {resources["sanity"]}
- 최종 의식력: {resources["ritual_power"]}
- 최종 저주 흔적: {resources["curse_marks"]}
- 획득한 진명 조각 수: {resources["true_name_fragments"]}
- 턴 수: {len(match_result.get("turn_logs", []))}

[정적 fallback 문장]
{story_result_text}

[금지]
- 승패를 바꾸지 않는다.
- 수치와 단서 상태를 새로 판단하지 않는다.
- 공식 설정을 추가하지 않는다.

출력은 2~4문장으로 작성한다."""
    return {
        "purpose": "result_summary",
        "system_prompt": base_system_prompt("세계관 톤은 어둡고 절제된 미스터리 분위기를 유지한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


def build_style_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["style_summary"]["metrics"]
    user_prompt = f"""아래 스타일 지표를 바탕으로 플레이 스타일 요약을 작성해줘.

[스타일 지표]
- 공격성: {metrics["aggression"]}
- 방어성: {metrics["defense"]}
- 정보 집중: {metrics["insight_focus"]}
- 기만성: {metrics["deception"]}
- 위험 선호: {metrics["risk_preference"]}
- 침묵 의존: {metrics["silence_reliance"]}
- 위기 방어율: {metrics["crisis_guard_rate"]}
- 위기 계약율: {metrics["crisis_contract_rate"]}
- 늦은 선택률: {metrics["late_choice_rate"]}

[금지]
- 지표를 새로 계산하지 않는다.
- 플레이어의 실제 성격을 단정하지 않는다.
- 승패 원인을 LLM이 판정하지 않는다.

출력은 1~3문장으로 작성한다."""
    return {
        "purpose": "style_summary",
        "system_prompt": base_system_prompt("플레이어를 비난하지 않고, 관찰 가능한 경향만 차분하게 표현한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


def build_match_log_summary_input(payload: dict[str, Any]) -> dict[str, Any]:
    log_lines = []
    for item in payload.get("turn_logs", []):
        log_lines.append(
            "- {turn}턴: player_action={player_action}, info_target_key={info_target_key}, "
            "match_outcome={match_outcome}, public_log={public_log}".format(**item)
        )
    user_prompt = f"""아래 매치 로그를 운영자 확인용으로 요약해줘.

[매치 정보]
- match_id: {payload["match_id"]}
- case_id: {payload["case_id"]}
- 결과: {payload["result"]}
- 종료 사유: {payload["result_reason"]}
- 턴 수: {payload["turn_count"]}
- 시간초과 횟수: {payload["timeout_count"]}

[주요 로그]
{chr(10).join(log_lines)}

[금지]
- 서버 판정을 바꾸지 않는다.
- 로그에 없는 행동이나 원인을 만들지 않는다.
- 보상, 랭킹, 매칭 판단을 하지 않는다.

출력은 핵심 흐름 3~5줄로 작성한다."""
    return {
        "purpose": "match_log_summary",
        "system_prompt": base_system_prompt("문장은 간결하고 운영자가 검토하기 쉽게 작성한다."),
        "user_prompt": user_prompt,
        "context_refs": [],
        "payload": payload,
    }


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
    text = payload["choices"][0]["message"]["content"].strip()
    if not text:
        raise ValueError("empty response text")
    return text, latency_ms


def validate_output(generation_input: dict[str, Any], text: str) -> list[str]:
    purpose = generation_input["purpose"]
    payload = generation_input["payload"]
    violations: list[str] = []

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

    if purpose == "match_log_summary":
        if any(word in text for word in {"추정", "아마", "원인으로 보인다"}):
            violations.append("unsupported_story_fact")

    return sorted(set(violations))


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
    except TimeoutError:
        return failed(generation_input, options, "timeout")
    except urllib.error.HTTPError as error:
        return failed(generation_input, options, "provider_error", {"status_code": error.code})
    except urllib.error.URLError:
        return failed(generation_input, options, "provider_error")
    except (KeyError, IndexError, json.JSONDecodeError, ValueError):
        return failed(generation_input, options, "response_parse_error")

    violations = validate_output(generation_input, text)
    if violations:
        return failed(generation_input, options, "guardrail_violation", {"violations": violations})
    return result_payload(generation_input, "succeeded", text, False, options, {"latency_ms": latency_ms})


def default_fixture_path(root: Path, purpose: str) -> Path:
    return root / "llm" / "fixtures" / f"{purpose}.sample.json"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM fixture 기반 Groq 생성 실험")
    parser.add_argument(
        "--purpose",
        choices=sorted(SUPPORTED_PURPOSES),
        default="result_summary",
        help="실험할 LLM purpose",
    )
    parser.add_argument("--fixture", type=Path, help="fixture JSON 경로. 생략하면 purpose별 sample을 사용한다.")
    parser.add_argument("--dry-run", action="store_true", help="provider 호출 없이 조립된 prompt만 결과 metadata에 출력한다.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    root = repo_root()
    args = parse_args(argv)
    fixture_path = args.fixture or default_fixture_path(root, args.purpose)
    payload = load_fixture(fixture_path)
    generation_input = build_generation_input(payload)
    options = read_options(root)
    result = generate(generation_input, options, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
