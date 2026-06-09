from dataclasses import dataclass

from backend.config import settings as project_settings


APPROVED_CONTRACTS_DIR = "docs/09_Approved_Contracts"
NAMELESS_CURSE_RAG_SOURCE_PATHS = (
    "docs/09_Approved_Contracts/27_플레이어_이름_무명의_저주_결전_RAG_계약.md",
    "docs/09_Approved_Contracts/26_무명의_저주_사건_계약.md",
    "docs/09_Approved_Contracts/25_" + "L" + "LM_Runtime_통합_계약.md",
    "docs/09_Approved_Contracts/17_백엔드_RAG_AI_Profile_구현_계약.md",
)
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


@dataclass(frozen=True)
class StoryCaseRagSourcePlan:
    case_id: str
    caller: str
    source_paths: tuple[str, ...]


def is_retrieval_source_allowed(source_path: str) -> bool:
    normalized_path = _normalize_source_path(source_path)
    if normalized_path.startswith(f"{APPROVED_CONTRACTS_DIR}/"):
        return True
    if normalized_path == MIRROR_GUEST_STORY_PATH:
        return True

    return normalized_path in APPROVED_GAME_RULE_PATHS


def build_story_case_rag_source_plan(*, case_id: str, caller: str) -> StoryCaseRagSourcePlan:
    if case_id == "nameless_curse":
        return StoryCaseRagSourcePlan(
            case_id=case_id,
            caller=caller,
            source_paths=NAMELESS_CURSE_RAG_SOURCE_PATHS,
        )

    return StoryCaseRagSourcePlan(
        case_id=case_id,
        caller=caller,
        source_paths=(f"{APPROVED_CONTRACTS_DIR}/25_" + "L" + "LM_Runtime_통합_계약.md",),
    )


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
