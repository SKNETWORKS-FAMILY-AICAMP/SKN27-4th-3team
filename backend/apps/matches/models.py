from django.db import models

from backend.apps.matches.constants import (
    ACTION_CODE_CHOICES,
    MATCH_MODE_CHOICES,
    MATCH_STATUS_CHOICES,
    PARTICIPANT_TYPE_CHOICES,
    TURN_STATUS_CHOICES,
)


class Match(models.Model):
    mode = models.TextField(choices=MATCH_MODE_CHOICES)
    status = models.TextField(choices=MATCH_STATUS_CHOICES)
    winner_participant_id = models.PositiveBigIntegerField(null=True, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "matches"


class MatchParticipant(models.Model):
    match_id = models.PositiveBigIntegerField()
    participant_type = models.TextField(choices=PARTICIPANT_TYPE_CHOICES)
    user_id = models.PositiveBigIntegerField(null=True, blank=True)
    apparition_id = models.PositiveBigIntegerField(null=True, blank=True)
    side = models.TextField()
    sanity = models.PositiveIntegerField()
    ritual_power = models.PositiveIntegerField()
    curse_marks = models.PositiveIntegerField()
    secret_exposure = models.PositiveIntegerField()

    class Meta:
        db_table = "match_participants"


class Turn(models.Model):
    match_id = models.PositiveBigIntegerField()
    turn_number = models.PositiveIntegerField()
    status = models.TextField(choices=TURN_STATUS_CHOICES)
    deadline_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "turns"


class ActionSubmission(models.Model):
    turn_id = models.PositiveBigIntegerField()
    participant_id = models.PositiveBigIntegerField()
    action_code = models.TextField(choices=ACTION_CODE_CHOICES)
    info_target_key = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField()
    client_nonce = models.UUIDField()

    class Meta:
        db_table = "action_submissions"
        constraints = [
            models.UniqueConstraint(
                fields=("turn_id", "participant_id", "client_nonce"),
                name="action_submission_turn_participant_client_nonce_unique",
            )
        ]


class TurnResult(models.Model):
    turn_id = models.PositiveBigIntegerField()
    result_json = models.JSONField()
    public_log_json = models.JSONField()
    private_log_json = models.JSONField()
    schema_version = models.TextField()

    class Meta:
        db_table = "turn_results"
