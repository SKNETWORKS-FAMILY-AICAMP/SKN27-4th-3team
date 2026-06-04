from django.urls import path

from backend.apps.accounts.views import (
    CsrfTokenView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    SignupView,
)


app_name = "accounts"

urlpatterns = [
    path("csrf", CsrfTokenView.as_view(), name="csrf"),
    path("signup", SignupView.as_view(), name="signup"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("refresh", RefreshView.as_view(), name="refresh"),
    path("me", MeView.as_view(), name="me"),
]
