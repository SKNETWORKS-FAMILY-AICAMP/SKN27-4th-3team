from dataclasses import dataclass
from typing import Any

from backend.apps.accounts import services as auth_services


@dataclass(frozen=True)
class ProfileMeResult:
    user: dict[str, Any]
    profile: dict[str, Any]


def get_profile_me(*, raw_access_token: str | None) -> ProfileMeResult:
    session = auth_services.get_current_session(raw_access_token=raw_access_token)
    return ProfileMeResult(user=session.user, profile=session.profile)
