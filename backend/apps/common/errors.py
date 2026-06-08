from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


API_ERROR_MESSAGES = MappingProxyType(
    {
        "AUTH_REQUIRED": "인증이 필요하다.",
        "SESSION_EXPIRED": "세션이 만료되었거나 refresh에 실패했다.",
        "INVALID_CREDENTIALS": "로그인 정보가 올바르지 않다.",
        "LOGIN_RATE_LIMITED": "로그인 실패가 반복되어 일시적으로 로그인이 차단되었다.",
        "CSRF_TOKEN_MISSING": "CSRF token이 없다.",
        "CSRF_TOKEN_INVALID": "CSRF token이 유효하지 않다.",
        "VALIDATION_ERROR": "요청 payload가 schema 또는 서버 검증을 통과하지 못했다.",
        "CASE_NOT_FOUND": "사건을 찾을 수 없다.",
        "CASE_NOT_AVAILABLE": "사건이 1차 MVP에서 사용 가능하지 않다.",
        "MATCH_NOT_FOUND": "매치를 찾을 수 없다.",
        "MATCH_ACCESS_DENIED": "요청 사용자가 해당 match participant가 아니다.",
        "MATCH_ALREADY_FINISHED": "매치가 이미 종료되었다.",
        "MATCH_NOT_RESOLVED": "결과 조회 시점에 매치가 아직 종료되지 않았다.",
        "TURN_ALREADY_SUBMITTED": "현재 participant가 해당 턴에 이미 행동을 제출했다.",
        "TURN_DEADLINE_EXPIRED": "제출이 서버 deadline_at 이후 도착했다.",
        "ACTION_NOT_AVAILABLE": "선택할 수 없는 행동이다.",
        "INFO_TARGET_REQUIRED": "정보 행동에 필요한 info_target_key가 없다.",
        "INSUFFICIENT_RITUAL_POWER": "의식력이 부족하다.",
        "REFRESH_TOKEN_REUSED": "refresh token 재사용이 감지되어 token family가 폐기되었다.",
        "IDEMPOTENCY_CONFLICT": "동일 idempotency key가 다른 요청 내용으로 재사용되었다.",
        "RATE_LIMITED": "요청 제한에 걸렸다.",
        "LLM_SUMMARY_UNAVAILABLE": "LLM 요약을 사용할 수 없어 정적 문장을 표시해야 한다.",
        "DUEL_DIALOGUE_LIMIT_EXCEEDED": "결전 대화 생성 제한을 초과했다.",
        "SERVICE_NOT_IMPLEMENTED": "Service is not implemented yet.",
    }
)


@dataclass(frozen=True)
class ApiError:
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.code not in API_ERROR_MESSAGES:
            raise ValueError(f"Unknown API error code: {self.code}")
        if self.message != API_ERROR_MESSAGES[self.code]:
            raise ValueError(f"ApiError message must match official schema for code: {self.code}")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


def make_api_error(code: str, *, details: Mapping[str, Any] | None = None) -> ApiError:
    if code not in API_ERROR_MESSAGES:
        raise ValueError(f"Unknown API error code: {code}")
    return ApiError(
        code=code,
        message=API_ERROR_MESSAGES[code],
        details={} if details is None else dict(details),
    )
