import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
MATCHES_DIR = BACKEND_DIR / "apps" / "matches"
OFFICIAL_API_SPEC = ROOT_DIR / "api-spec" / "pilot-mvp-api.official.json"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _class_source(source: str, class_name: str) -> str:
    marker = f"class {class_name}(models.Model):"
    assert marker in source
    return source.split(marker, maxsplit=1)[1].split("\n\nclass ", maxsplit=1)[0]


def _official_domain_enums() -> dict[str, list[str]]:
    spec = json.loads(OFFICIAL_API_SPEC.read_text(encoding="utf-8"))
    return spec["domain_enums"]


def test_match_storage_modules_exist_for_task_6_contract():
    assert (MATCHES_DIR / "constants.py").exists()
    assert (MATCHES_DIR / "models.py").exists()
    assert (MATCHES_DIR / "services.py").exists()


def test_match_storage_constants_follow_official_domain_enums_without_duplication():
    constants_source = _read(MATCHES_DIR / "constants.py")
    domain_enums = _official_domain_enums()

    assert domain_enums["match_mode"] == ["ai_story"]
    assert "pvp" not in domain_enums["match_mode"]
    assert "MATCH_MODE_PVP" not in constants_source
    assert '= "pvp"' not in constants_source

    for match_mode in domain_enums["match_mode"]:
        assert f'= "{match_mode}"' in constants_source
    for match_status in domain_enums["match_status"]:
        assert f'= "{match_status}"' in constants_source
    for turn_status in domain_enums["turn_status"]:
        assert f'= "{turn_status}"' in constants_source
    for participant_type in domain_enums["participant_type"]:
        assert f'= "{participant_type}"' in constants_source

    assert "from backend.apps.game_rules.matchups import ACTION_CODES" in constants_source
    assert "ACTION_CODE_CHOICES" in constants_source


def test_match_models_define_approved_tables_and_fields_without_unapproved_foreign_keys():
    source = _read(MATCHES_DIR / "models.py")
    migration_source = _read(MATCHES_DIR / "migrations" / "0001_initial.py")

    for class_name in (
        "Match",
        "MatchParticipant",
        "MatchTrueNameFragmentOwnership",
        "MatchFalseClueOwnership",
        "Turn",
        "ActionSubmission",
        "TurnResult",
        "MatchStartRequest",
        "DuelDialogue",
    ):
        assert f"class {class_name}(models.Model):" in source

    assert "('pvp', 'pvp')" not in migration_source
    assert "db_table = \"matches\"" in source
    assert "db_table = \"match_participants\"" in source
    assert "db_table = \"match_true_name_fragments\"" in source
    assert "db_table = \"match_false_clues\"" in source
    assert "db_table = \"turns\"" in source
    assert "db_table = \"action_submissions\"" in source
    assert "db_table = \"turn_results\"" in source
    assert "db_table = \"match_start_requests\"" in source
    assert "db_table = \"duel_dialogues\"" in source
    assert "models.ForeignKey" not in source
    assert "on_delete=" not in source

    match_source = _class_source(source, "Match")
    assert "mode = models.TextField(choices=MATCH_MODE_CHOICES)" in match_source
    assert "status = models.TextField(choices=MATCH_STATUS_CHOICES)" in match_source
    assert "winner_participant_id = models.PositiveBigIntegerField(null=True, blank=True)" in match_source
    assert "started_at = models.DateTimeField()" in match_source
    assert "ended_at = models.DateTimeField(null=True, blank=True)" in match_source
    assert "user_id" not in match_source
    assert "story_case_id" not in match_source
    assert "stage_id" not in match_source

    participant_source = _class_source(source, "MatchParticipant")
    assert "match_id = models.PositiveBigIntegerField()" in participant_source
    assert "participant_type = models.TextField(choices=PARTICIPANT_TYPE_CHOICES)" in participant_source
    assert "user_id = models.PositiveBigIntegerField(null=True, blank=True)" in participant_source
    assert "apparition_id = models.PositiveBigIntegerField(null=True, blank=True)" in participant_source
    assert "side = models.TextField()" in participant_source
    assert "sanity = models.PositiveIntegerField()" in participant_source
    assert "ritual_power = models.PositiveIntegerField()" in participant_source
    assert "curse_marks = models.PositiveIntegerField()" in participant_source
    assert "secret_exposure = models.PositiveIntegerField()" in participant_source
    assert "true_name_fragments = models.PositiveIntegerField()" in participant_source
    assert "incomplete_true_name_fragments = models.PositiveIntegerField()" in participant_source
    assert "false_clues = models.PositiveIntegerField()" in participant_source
    assert "suspicion = models.PositiveIntegerField()" in participant_source
    assert "shield = models.PositiveIntegerField()" in participant_source
    assert "timeout_count = models.PositiveIntegerField()" in participant_source

    true_fragment_source = _class_source(source, "MatchTrueNameFragmentOwnership")
    assert "match_id = models.PositiveBigIntegerField()" in true_fragment_source
    assert "participant_id = models.PositiveBigIntegerField()" in true_fragment_source
    assert "true_name_fragment_id = models.PositiveBigIntegerField()" in true_fragment_source
    assert "source_turn_id = models.PositiveBigIntegerField()" in true_fragment_source
    assert "source_turn_number = models.PositiveIntegerField()" in true_fragment_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in true_fragment_source

    false_clue_source = _class_source(source, "MatchFalseClueOwnership")
    assert "match_id = models.PositiveBigIntegerField()" in false_clue_source
    assert "participant_id = models.PositiveBigIntegerField()" in false_clue_source
    assert "false_clue_id = models.PositiveBigIntegerField()" in false_clue_source
    assert "truth_state = models.TextField(choices=CLUE_TRUTH_STATE_CHOICES)" in false_clue_source
    assert "source_turn_id = models.PositiveBigIntegerField()" in false_clue_source
    assert "source_turn_number = models.PositiveIntegerField()" in false_clue_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in false_clue_source

    turn_source = _class_source(source, "Turn")
    assert "match_id = models.PositiveBigIntegerField()" in turn_source
    assert "turn_number = models.PositiveIntegerField()" in turn_source
    assert "status = models.TextField(choices=TURN_STATUS_CHOICES)" in turn_source
    assert "started_at = models.DateTimeField()" in turn_source
    assert "deadline_at = models.DateTimeField()" in turn_source
    assert "resolved_at = models.DateTimeField(null=True, blank=True)" in turn_source

    submission_source = _class_source(source, "ActionSubmission")
    assert "turn_id = models.PositiveBigIntegerField()" in submission_source
    assert "participant_id = models.PositiveBigIntegerField()" in submission_source
    assert "action_code = models.TextField(choices=ACTION_CODE_CHOICES)" in submission_source
    assert "info_target_key = models.TextField(null=True, blank=True)" in submission_source
    assert "submitted_at = models.DateTimeField()" in submission_source
    assert "client_nonce = models.UUIDField()" in submission_source

    result_source = _class_source(source, "TurnResult")
    assert "turn_id = models.PositiveBigIntegerField()" in result_source
    assert "result_json = models.JSONField()" in result_source
    assert "public_log_json = models.JSONField()" in result_source
    assert "private_log_json = models.JSONField()" in result_source
    assert "schema_version = models.TextField()" in result_source

    start_request_source = _class_source(source, "MatchStartRequest")
    assert "user_id = models.PositiveBigIntegerField()" in start_request_source
    assert "client_request_id = models.UUIDField()" in start_request_source
    assert "case_id = models.TextField()" in start_request_source
    assert "player_display_name = models.TextField(null=True, blank=True)" in start_request_source
    assert "match_id = models.PositiveBigIntegerField()" in start_request_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in start_request_source
    assert (MATCHES_DIR / "migrations" / "0005_matchstartrequest_player_display_name.py").exists()

    duel_dialogue_source = _class_source(source, "DuelDialogue")
    assert "match_id = models.PositiveBigIntegerField()" in duel_dialogue_source
    assert "user_id = models.PositiveBigIntegerField()" in duel_dialogue_source
    assert "client_nonce = models.UUIDField()" in duel_dialogue_source
    assert "player_message = models.TextField()" in duel_dialogue_source
    assert "apparition_message = models.TextField(null=True, blank=True)" in duel_dialogue_source
    assert "generation_id = models.PositiveBigIntegerField(null=True, blank=True)" in duel_dialogue_source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in duel_dialogue_source


def test_action_submission_nonce_is_unique_in_participant_and_turn_scope_only():
    source = _read(MATCHES_DIR / "models.py")
    submission_source = _class_source(source, "ActionSubmission")

    assert "models.UniqueConstraint(" in submission_source
    assert "fields=(\"turn_id\", \"participant_id\", \"client_nonce\")" in submission_source
    assert "client_nonce = models.UUIDField(unique=True)" not in submission_source
    assert "user_id" not in submission_source


def test_match_start_request_is_unique_per_user_and_client_request_id():
    source = _read(MATCHES_DIR / "models.py")
    start_request_source = _class_source(source, "MatchStartRequest")

    assert "models.UniqueConstraint(" in start_request_source
    assert "fields=(\"user_id\", \"client_request_id\")" in start_request_source
    assert "name=\"match_start_request_user_client_request_unique\"" in start_request_source
    assert "client_request_id = models.UUIDField(unique=True)" not in start_request_source


def test_match_clue_ownership_is_unique_per_match_participant_and_source_definition():
    source = _read(MATCHES_DIR / "models.py")
    true_fragment_source = _class_source(source, "MatchTrueNameFragmentOwnership")
    false_clue_source = _class_source(source, "MatchFalseClueOwnership")

    assert "models.UniqueConstraint(" in true_fragment_source
    assert (
        "fields=(\"match_id\", \"participant_id\", \"true_name_fragment_id\")"
        in true_fragment_source
    )
    assert "name=\"match_true_name_fragment_ownership_unique\"" in true_fragment_source

    assert "models.UniqueConstraint(" in false_clue_source
    assert (
        "fields=(\"match_id\", \"participant_id\", \"false_clue_id\")"
        in false_clue_source
    )
    assert "name=\"match_false_clue_ownership_unique\"" in false_clue_source


def test_match_storage_services_validate_participant_identity_and_json_schema_version():
    services_source = _read(MATCHES_DIR / "services.py")
    constants_source = _read(MATCHES_DIR / "constants.py")

    assert "def validate_participant_identity(" in services_source
    assert "PARTICIPANT_TYPE_HUMAN" in services_source
    assert "PARTICIPANT_TYPE_APPARITION" in services_source
    assert "def validate_json_snapshot_payload(" in services_source
    assert "MATCH_STORAGE_SCHEMA_VERSION_FIELD = \"schema_version\"" in constants_source
    assert "MATCH_STORAGE_SCHEMA_VERSION_FIELD" in services_source
    assert "jsonschema" in services_source
    assert "Draft202012Validator" in services_source
