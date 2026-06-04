from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
STORY_DIR = BACKEND_DIR / "apps" / "story"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(models.Model):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def test_story_storage_modules_exist_for_task_7_contract():
    assert (STORY_DIR / "models.py").exists()
    assert (STORY_DIR / "services.py").exists()


def test_story_models_define_approved_storage_tables_and_fields_only():
    source = _read(STORY_DIR / "models.py")

    expected_models = (
        "StoryCase",
        "Apparition",
        "Stage",
        "TrueNameFragment",
        "FalseClue",
        "PlayerStoryProgress",
    )
    for class_name in expected_models:
        assert f"class {class_name}(models.Model):" in source

    assert "db_table = \"story_cases\"" in source
    assert "db_table = \"apparitions\"" in source
    assert "db_table = \"stages\"" in source
    assert "db_table = \"true_name_fragments\"" in source
    assert "db_table = \"false_clues\"" in source
    assert "db_table = \"player_story_progress\"" in source

    story_case_source = _class_source(source, "StoryCase")
    assert "title = models.TextField()" in story_case_source
    assert "summary = models.TextField()" in story_case_source
    assert "difficulty = models.TextField()" in story_case_source
    assert "status = models.TextField()" in story_case_source

    apparition_source = _class_source(source, "Apparition")
    assert "name = models.TextField()" in apparition_source
    assert "category = models.TextField()" in apparition_source
    assert "description = models.TextField()" in apparition_source
    assert "taboo = models.TextField()" in apparition_source
    assert "base_policy_json = models.JSONField()" in apparition_source

    stage_source = _class_source(source, "Stage")
    assert "case_id = models.PositiveBigIntegerField()" in stage_source
    assert "apparition_id = models.PositiveBigIntegerField()" in stage_source
    assert "order = models.PositiveIntegerField()" in stage_source
    assert "victory_condition_json = models.JSONField()" in stage_source

    true_name_fragment_source = _class_source(source, "TrueNameFragment")
    assert "apparition_id = models.PositiveBigIntegerField()" in true_name_fragment_source
    assert "label = models.TextField()" in true_name_fragment_source
    assert "content = models.TextField()" in true_name_fragment_source
    assert "reveal_condition_json = models.JSONField()" in true_name_fragment_source

    false_clue_source = _class_source(source, "FalseClue")
    assert "apparition_id = models.PositiveBigIntegerField()" in false_clue_source
    assert "content = models.TextField()" in false_clue_source
    assert "trigger_condition_json = models.JSONField()" in false_clue_source

    progress_source = _class_source(source, "PlayerStoryProgress")
    assert "user_id = models.PositiveBigIntegerField()" in progress_source
    assert "stage_id = models.PositiveBigIntegerField()" in progress_source
    assert "status = models.TextField()" in progress_source
    assert "attempts = models.PositiveIntegerField()" in progress_source
    assert "completed_at = models.DateTimeField(null=True, blank=True)" in progress_source


def test_story_models_keep_case_apparition_stage_and_owned_clue_state_normalized():
    source = _read(STORY_DIR / "models.py")

    assert "story_case_json" not in source
    assert "apparition_json" not in source
    assert "stage_json" not in source
    assert "owned_true_name_fragments_json" not in source
    assert "owned_false_clues_json" not in source
    assert "models.ForeignKey" not in source
    assert "on_delete=" not in source


def test_story_services_validate_policy_json_schema_version_without_llm_or_rag_generation():
    services_source = _read(STORY_DIR / "services.py")

    assert "STORY_POLICY_SCHEMA_VERSION_FIELD = \"schema_version\"" in services_source
    assert "def validate_story_policy_payload(" in services_source
    assert "jsonschema" in services_source
    assert "Draft202012Validator" in services_source

    forbidden_generation_sources = (
        "llm",
        "generation",
        "rag",
        "retrieval",
        "embedding",
        "generate_true_name",
        "generate_false_clue",
    )
    lowered_source = services_source.lower()
    for forbidden in forbidden_generation_sources:
        assert forbidden not in lowered_source
