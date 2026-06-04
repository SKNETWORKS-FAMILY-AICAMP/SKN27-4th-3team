"""LLM fixture 기반 Groq 생성 실험용 CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.generation.adapter import (  # noqa: E402
    SUPPORTED_PURPOSES,
    build_generation_input,
    default_fixture_path,
    frontend_payload,
    generate,
    load_fixture,
    read_options,
)


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
    parser.add_argument("--frontend-output", action="store_true", help="프론트 전달용 응답 계약 형태로 출력한다.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    fixture_path = args.fixture or default_fixture_path(ROOT, args.purpose)
    payload = load_fixture(fixture_path)
    generation_input = build_generation_input(payload)
    options = read_options(ROOT)
    result = generate(generation_input, options, args.dry_run)
    output = frontend_payload(generation_input, result) if args.frontend_output else result
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
