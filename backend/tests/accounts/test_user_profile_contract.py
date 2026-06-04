from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
ACCOUNTS_DIR = ROOT_DIR / "backend" / "apps" / "accounts"
PROFILES_DIR = ROOT_DIR / "backend" / "apps" / "profiles"


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def test_accounts_user_model_uses_approved_custom_user_contract():
    source = _read(ACCOUNTS_DIR / "models.py")

    assert "class User(AbstractBaseUser, PermissionsMixin):" in source
    assert 'USERNAME_FIELD = "email"' in source
    assert "REQUIRED_FIELDS = []" in source
    assert "objects = UserManager()" in source
    assert "email = models.EmailField(" in source
    assert "unique=True" in source
    assert "created_at = models.DateTimeField(auto_now_add=True)" in source
    assert "nickname" not in source


def test_user_model_keeps_auth_and_permission_state_only():
    source = _read(ACCOUNTS_DIR / "models.py")

    assert "is_active = models.BooleanField(default=True)" in source
    assert "is_staff = models.BooleanField(default=False)" in source
    assert "db_table" not in source

    forbidden_profile_fields = (
        "ai_story_matches",
        "ai_story_wins",
        "ai_story_losses",
        "style_label",
        "style_display_text",
    )
    for field_name in forbidden_profile_fields:
        assert field_name not in source


def test_user_manager_normalizes_email_and_never_handles_nickname():
    source = _read(ACCOUNTS_DIR / "managers.py")

    assert "class UserManager(BaseUserManager):" in source
    assert "def create_user(" in source
    assert "def create_superuser(" in source
    assert "self.normalize_email(email)" in source
    assert "user.set_password(password)" in source
    assert 'extra_fields.setdefault("is_staff", True)' in source
    assert 'extra_fields.setdefault("is_superuser", True)' in source
    assert "nickname" not in source


def test_profiles_model_owns_nickname_public_record_and_style_display_data():
    source = _read(PROFILES_DIR / "models.py")

    assert "class Profile(models.Model):" in source
    assert "user = models.OneToOneField(" in source
    assert "settings.AUTH_USER_MODEL" in source
    assert "related_name=\"profile\"" in source
    assert "nickname = models.TextField()" in source
    assert "ai_story_matches = models.PositiveIntegerField(" in source
    assert "ai_story_wins = models.PositiveIntegerField(" in source
    assert "ai_story_losses = models.PositiveIntegerField(" in source
    assert "ai_story_matches = models.PositiveIntegerField(default=0)" not in source
    assert "ai_story_wins = models.PositiveIntegerField(default=0)" not in source
    assert "ai_story_losses = models.PositiveIntegerField(default=0)" not in source
    assert "style_label = models.TextField(null=True, blank=True)" in source
    assert "style_display_text = models.TextField(null=True, blank=True)" in source
    assert "style_summary_updated_at = models.DateTimeField(null=True, blank=True)" in source
    assert "db_table" not in source


def test_profile_creation_side_effect_is_not_hidden_in_signals():
    account_files = list(ACCOUNTS_DIR.glob("*.py"))
    profile_files = list(PROFILES_DIR.glob("*.py"))
    joined_source = "\n".join(path.read_text(encoding="utf-8") for path in account_files + profile_files)

    assert "post_save" not in joined_source
    assert "Signal" not in joined_source
    assert "@receiver" not in joined_source
