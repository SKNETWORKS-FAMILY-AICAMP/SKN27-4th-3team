from dataclasses import dataclass

from backend.config import settings as project_settings


APPROVED_CONTRACTS_DIR = "docs/09_Approved_Contracts"
MIRROR_GUEST_STORY_PATH = "docs/05_Story_Mode/02_거울_속의_손님.md"
APPROVED_GAME_RULE_PATHS = (
    "docs/02_Game_Rules/01_자원과_상태.md",
    "docs/02_Game_Rules/04_상성_규칙.md",
    "docs/02_Game_Rules/05_승패_조건.md",
    "docs/02_Game_Rules/06_시간초과_규칙.md",
    "docs/02_Game_Rules/99_Game_Rules_구현_확정.md",
)


@dataclass(frozen=True)
class RetrievalSearchDefaults:
    top_k: int
    score_threshold: float


def is_retrieval_source_allowed(source_path: str) -> bool:
    normalized_path = _normalize_source_path(source_path)
    if normalized_path.startswith(f"{APPROVED_CONTRACTS_DIR}/"):
        return True
    if normalized_path == MIRROR_GUEST_STORY_PATH:
        return True

    return normalized_path in APPROVED_GAME_RULE_PATHS


def get_retrieval_search_defaults() -> RetrievalSearchDefaults:
    return RetrievalSearchDefaults(
        top_k=project_settings.RAG_DEFAULT_TOP_K,
        score_threshold=project_settings.RAG_DEFAULT_SCORE_THRESHOLD,
    )


def get_configured_embedding_model_id() -> str:
    model_id = project_settings.RAG_EMBEDDING_MODEL_ID
    if not model_id:
        raise ValueError("RAG_EMBEDDING_MODEL_ID must be provided by env/config")

    return model_id


def _normalize_source_path(source_path: str) -> str:
    return source_path.replace("\\", "/").strip("/")
