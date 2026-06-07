import json
import unittest
from pathlib import Path

from llm.generation.adapter import validate_output
from llm.prompts.prompt_templates import build_generation_input


ROOT = Path(__file__).resolve().parents[2]


# fixture 파일을 읽어 guardrail 검사용 generation input을 만든다.
def _generation_input(fixture_name: str) -> dict:
    payload = json.loads((ROOT / "llm" / "fixtures" / fixture_name).read_text(encoding="utf-8"))
    return build_generation_input(payload)


class GuardrailContractTest(unittest.TestCase):
    # 턴 연출 문구가 판정이나 입력 밖 사실을 만들면 guardrail이 막는지 확인한다.
    def test_turn_flavor_text_rejects_judgment_and_unsupported_facts(self) -> None:
        generation_input = _generation_input("turn_flavor_text.official.sample.json")
        cases = [
            ("이 행동은 단서를 획득했다.", "unsupported_action_judgment"),
            ("다음 턴 괴이가 저주를 속삭인다.", "next_action_prediction"),
            ("거울 속 비밀이 드러났다.", "unsupported_story_fact"),
            ("피티가 거울 뒤에서 이름을 부른다.", "demo_reference_leak"),
        ]

        for text, expected_violation in cases:
            with self.subTest(text=text):
                violations = validate_output(generation_input, text)

                self.assertIn(expected_violation, violations)

    # 공개 로그에 이미 있는 표현은 새 사실로 오판하지 않는지 확인한다.
    def test_turn_flavor_text_allows_public_log_words_from_payload(self) -> None:
        generation_input = _generation_input("turn_flavor_text.official.sample.json")
        text = "거울 표면에 남은 손자국이 차갑게 번졌다."

        violations = validate_output(generation_input, text)

        self.assertEqual([], violations)

    # 프론트 화면 상한을 넘는 턴 연출 문구는 표시 전에 막는다.
    def test_turn_flavor_text_rejects_frontend_length_overflow(self) -> None:
        generation_input = _generation_input("turn_flavor_text.official.sample.json")
        text = "거울 표면에 남은 손자국이 차갑게 번지고, 식은 손끝의 기척이 벽면을 따라 아주 길게 이어졌다."

        violations = validate_output(generation_input, text)

        self.assertIn("line_length_violation", violations)

    # 피티는 nameless_curse 입력에 들어올 때만 공식 괴이 이름으로 허용한다.
    def test_turn_flavor_text_prompt_uses_piti_persona_only_when_alias_is_piti(self) -> None:
        generation_input = _generation_input("turn_flavor_text.official.sample.json")

        self.assertNotIn("피티", generation_input["system_prompt"])

        payload = json.loads(
            (ROOT / "llm" / "fixtures" / "turn_flavor_text.official.sample.json").read_text(
                encoding="utf-8"
            )
        )
        payload["apparition_alias"] = "피티"
        generation_input = build_generation_input(payload)

        self.assertIn("피티", generation_input["system_prompt"])
        self.assertEqual([], validate_output(generation_input, "피티는 유리 안쪽에서 이름을 붙잡았다."))
        self.assertIn("demo_reference_leak", validate_output(generation_input, "이안은 유리 안쪽에서 이름을 붙잡았다."))
        self.assertIn("demo_reference_leak", validate_output(generation_input, "엘리자베스는 유리 안쪽에서 이름을 붙잡았다."))

    # 입력 로그에 있는 "진실" 표현은 운영자 로그 요약에서 허용한다.
    def test_final_duel_dialogue_prompt_includes_player_name_and_duel_rules(self) -> None:
        generation_input = build_generation_input(
            {
                "purpose": "final_duel_dialogue",
                "case": {"case_id": "nameless_curse", "title": "nameless curse"},
                "match": {"match_id": "match_1", "turn_number": 7, "result": "unresolved"},
                "player": {"display_name": "Yunseo"},
                "player_message": "I will return your name.",
                "apparition_alias": "Piti",
                "public_context": {
                    "true_name_fragments": 2,
                    "false_clues": 2,
                    "curse_marks": 1,
                    "sanity": 6,
                    "recent_public_logs": [],
                },
                "duel_rules": {
                    "required_true_name_fragments": 2,
                    "win_condition": "recover_piti_true_name",
                    "false_clue_pressure": True,
                },
                "display_slot": "duel_dialogue",
            }
        )

        self.assertIn("Yunseo", generation_input["user_prompt"])
        self.assertIn("false_clues: 2", generation_input["user_prompt"])
        self.assertIn("required_true_name_fragments: 2", generation_input["user_prompt"])
        self.assertIn("recover_piti_true_name", generation_input["user_prompt"])
        self.assertIn("false_clue_pressure: True", generation_input["user_prompt"])

    def test_match_log_summary_allows_truth_word_when_it_exists_in_payload(self) -> None:
        generation_input = _generation_input("match_log_summary.sample.json")
        text = (
            "1턴에 다락방 일기장에서 벽 속에 묻힌 아이의 기록이 발견됐다.\n"
            "5턴에 무명실로 꿰매어진 입술의 흔적이 거울 표면에 떠올랐다.\n"
            "9턴에 진실의 거울 앞에서 피티의 이름이 불렸고, 무명실이 재처럼 흩어졌다."
        )

        violations = validate_output(generation_input, text)

        self.assertNotIn("unsupported_story_fact", violations)

    # result_reason enum을 잘못 번역한 표현은 운영 로그 요약에서 막는다.
    def test_match_log_summary_rejects_bad_enum_translation(self) -> None:
        generation_input = _generation_input("match_log_summary.sample.json")
        text = (
            "1턴에 다락방 일기장에서 벽 속에 묻힌 아이의 기록이 발견됐다.\n"
            "5턴에 무명실의 흔적이 거울 표면에 떠올랐다.\n"
            "9턴에 피티의 이름이 불렸고, 종료 사유는 인감 성공이었다."
        )

        violations = validate_output(generation_input, text)

        self.assertIn("unsupported_story_fact", violations)

    # 스타일 요약이 플레이어 성격 낙인이나 행동 판정을 하지 못하게 막는다.
    def test_style_summary_rejects_personality_judgment(self) -> None:
        generation_input = _generation_input("style_summary.sample.json")

        violations = validate_output(generation_input, "플레이어는 비겁했고 성공했다.")

        self.assertIn("personality_judgment", violations)
        self.assertIn("unsupported_action_judgment", violations)


if __name__ == "__main__":
    unittest.main()
