from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from backend.apps.accounts.managers import UserManager
from backend.apps.accounts.tokens import REFRESH_TOKEN_STATUSES, SECURITY_EVENT_TYPES


REFRESH_TOKEN_STATUS_CHOICES = tuple((status, status) for status in REFRESH_TOKEN_STATUSES)
SECURITY_EVENT_TYPE_CHOICES = tuple((event_type, event_type) for event_type in SECURITY_EVENT_TYPES)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email


class RefreshToken(models.Model):
    user_id = models.PositiveBigIntegerField()
    jti = models.UUIDField(unique=True)
    family_id = models.UUIDField()
    token_hash = models.TextField()
    status = models.TextField(choices=REFRESH_TOKEN_STATUS_CHOICES)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    rotated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    reused_at = models.DateTimeField(null=True, blank=True)
    replaced_by_jti = models.UUIDField(null=True, blank=True)


class SecurityEvent(models.Model):
    event_type = models.TextField(choices=SECURITY_EVENT_TYPE_CHOICES)
    user_id = models.PositiveBigIntegerField(null=True, blank=True)
    request_id = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
