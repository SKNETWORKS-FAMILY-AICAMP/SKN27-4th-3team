from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    nickname = models.TextField()
    ai_story_matches = models.PositiveIntegerField()
    ai_story_wins = models.PositiveIntegerField()
    ai_story_losses = models.PositiveIntegerField()
    style_label = models.TextField(null=True, blank=True)
    style_display_text = models.TextField(null=True, blank=True)
    style_summary_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.nickname
