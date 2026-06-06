from typing import Any


def build_disabled_llm_summary() -> dict[str, Any]:
    return {
        "enabled": False,
        "text": None,
        "generation_id": None,
    }
