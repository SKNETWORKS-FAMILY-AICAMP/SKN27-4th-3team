from django.conf import settings
from django.middleware.csrf import get_token, rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

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
from backend.apps.common.exceptions import ServiceNotImplementedError
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


class SignupView(APIView):
    permission_classes = [AllowAny]
    request_serializer_class = SignupRequestSerializer
    response_serializer_class = SignupResponseSerializer

    def post(self, request):
        raise AuthServiceNotImplemented("auth.signup")


class LoginView(AuthCookieMixin, APIView):
    permission_classes = [AllowAny]
    request_serializer_class = LoginRequestSerializer
    response_serializer_class = LoginResponseSerializer

    def post(self, request):
        rotate_token(request)
        raise AuthServiceNotImplemented("auth.login")


class LogoutView(AuthCookieMixin, APIView):
    request_serializer_class = EmptyRequestSerializer
    response_serializer_class = LogoutResponseSerializer

    def post(self, request):
        raise AuthServiceNotImplemented("auth.logout")


class RefreshView(AuthCookieMixin, APIView):
    request_serializer_class = EmptyRequestSerializer
    response_serializer_class = RefreshResponseSerializer

    def post(self, request):
        raise AuthServiceNotImplemented("auth.refresh")


class MeView(APIView):
    response_serializer_class = MeResponseSerializer

    def get(self, request):
        raise AuthServiceNotImplemented("auth.me")
