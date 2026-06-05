import json
import unittest
from pathlib import Path

from llm.generation.adapter import LlmOptions, generate
from llm.prompts.prompt_templates import build_generation_input


ROOT = Path(__file__).resolve().parents[2]


# provider 호출 없이 dry-run 검증에 사용할 안전한 LLM 옵션을 만든다.
def _dry_run_options() -> LlmOptions:
    return LlmOptions(
        provider="groq",
        api_key="",
        model_id="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        timeout_seconds=30,
        max_output_tokens=400,
        temperature=0.4,
        disabled=False,
    )


# official fixture를 읽고 prompt 조립 입력으로 변환한다.
def _generation_input(fixture_name: str) -> dict:
    payload = json.loads((ROOT / "llm" / "fixtures" / fixture_name).read_text(encoding="utf-8"))
    return build_generation_input(payload)


class OfficialFixtureContractTest(unittest.TestCase):
    # 결과 요약 official fixture가 provider 호출 없이 prompt로 조립되는지 확인한다.
    def test_result_summary_official_fixture_builds_prompt_in_dry_run(self) -> None:
        generation_input = _generation_input("result_summary.official.sample.json")

        result = generate(generation_input, _dry_run_options(), dry_run=True)

        self.assertEqual("skipped", result["status"])
        self.assertIs(True, result["fallback_used"])
        self.assertEqual("dry_run", result["metadata"]["reason"])
        self.assertIn("거울 속의 손님", result["metadata"]["user_prompt"])
        self.assertIn("서버 공개 로그 근거", result["metadata"]["user_prompt"])

    # 턴 연출 official fixture가 official enum 값을 포함해 prompt로 조립되는지 확인한다.
    def test_turn_flavor_text_official_fixture_builds_prompt_in_dry_run(self) -> None:
        generation_input = _generation_input("turn_flavor_text.official.sample.json")

        result = generate(generation_input, _dry_run_options(), dry_run=True)

        self.assertEqual("skipped", result["status"])
        self.assertIs(True, result["fallback_used"])
        self.assertEqual("dry_run", result["metadata"]["reason"])
        self.assertIn("mirror_surface", result["metadata"]["user_prompt"])
        self.assertIn("거울 표면에 남은 손자국", result["metadata"]["user_prompt"])


if __name__ == "__main__":
    unittest.main()
