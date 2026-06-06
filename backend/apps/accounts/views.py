from django.conf import settings
from django.middleware.csrf import get_token, rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.accounts import services as auth_services
from backend.apps.accounts.serializers import (
    CsrfResponseSerializer,
    EmptyRequestSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    LogoutResponseSerializer,
    MeResponseSerializer,
    RefreshResponseSerializer,
    SignupRequestSerializer,
    SignupResponseSerializer,
)
from backend.apps.common.exceptions import ApiErrorResponseException, ServiceNotImplementedError
from backend.apps.common.request_ids import get_request_id
from backend.apps.common.runtime import api_success_response


class AuthServiceNotImplemented(ServiceNotImplementedError):
    pass


class AuthCookieMixin:
    def set_access_cookie(self, response, value: str) -> None:
        response.set_cookie(
            key=settings.ACCESS_TOKEN_COOKIE_NAME,
            value=value,
            max_age=settings.ACCESS_TOKEN_TTL_SECONDS,
            path=settings.ACCESS_TOKEN_COOKIE_PATH,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

    def set_refresh_cookie(self, response, value: str) -> None:
        response.set_cookie(
            key=settings.REFRESH_TOKEN_COOKIE_NAME,
            value=value,
            max_age=settings.REFRESH_TOKEN_TTL_SECONDS,
            path=settings.REFRESH_TOKEN_COOKIE_PATH,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

    def clear_auth_cookies(self, response) -> None:
        response.delete_cookie(
            key=settings.ACCESS_TOKEN_COOKIE_NAME,
            path=settings.ACCESS_TOKEN_COOKIE_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        response.delete_cookie(
            key=settings.REFRESH_TOKEN_COOKIE_NAME,
            path=settings.REFRESH_TOKEN_COOKIE_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = CsrfResponseSerializer

    def get(self, request):
        return api_success_response(request, {"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class SignupView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = SignupRequestSerializer
    response_serializer_class = SignupResponseSerializer

    def post(self, request):
        serializer = self.request_serializer_class(data=request.data)
        if not serializer.is_valid():
            raise ApiErrorResponseException(
                "VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        signup_result = auth_services.signup(
            email=serializer.validated_data["email"],
            nickname=serializer.validated_data["nickname"],
            password=serializer.validated_data["password"],
        )
        return api_success_response(
            request,
            {"user": signup_result.user},
            status_code=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(AuthCookieMixin, APIView):
    permission_classes = [AllowAny]
    request_serializer_class = LoginRequestSerializer
    response_serializer_class = LoginResponseSerializer

    def post(self, request):
        serializer = self.request_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        login_result = auth_services.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            request_id=get_request_id(request),
        )
        rotate_token(request)
        response = api_success_response(
            request,
            {
                "user": login_result.user,
                "profile": login_result.profile,
                "session": {
                    "authenticated": True,
                    "access_expires_in_seconds": login_result.access_expires_in_seconds,
                },
            },
        )
        self.set_access_cookie(response, login_result.access_token)
        self.set_refresh_cookie(response, login_result.refresh_token)
        return response


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(AuthCookieMixin, APIView):
    permission_classes = [AllowAny]
    request_serializer_class = EmptyRequestSerializer
    response_serializer_class = LogoutResponseSerializer

    def post(self, request):
        raise AuthServiceNotImplemented("auth.logout")


@method_decorator(csrf_protect, name="dispatch")
class RefreshView(AuthCookieMixin, APIView):
    permission_classes = [AllowAny]
    request_serializer_class = EmptyRequestSerializer
    response_serializer_class = RefreshResponseSerializer

    def post(self, request):
        refresh_result = auth_services.refresh(
            raw_refresh_token=request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME),
            request_id=get_request_id(request),
        )
        response = api_success_response(
            request,
            {
                "refreshed": True,
                "access_expires_in_seconds": refresh_result.access_expires_in_seconds,
            },
        )
        self.set_access_cookie(response, refresh_result.access_token)
        self.set_refresh_cookie(response, refresh_result.refresh_token)
        return response


class MeView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = MeResponseSerializer

    def get(self, request):
        session = auth_services.get_current_session(
            raw_access_token=request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        )
        return api_success_response(
            request,
            {
                "authenticated": session.authenticated,
                "user": session.user,
                "profile": session.profile,
            },
        )
