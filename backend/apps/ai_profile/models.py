from django.db import models

from backend.apps.matches.constants import ACTION_CODE_CHOICES


class PlayerActionEvent(models.Model):
    user_id = models.PositiveBigIntegerField()
    mode = models.TextField()
    match_id = models.PositiveBigIntegerField()
    stage_id = models.PositiveBigIntegerField()
    turn_number = models.PositiveIntegerField()
    action_code = models.TextField(choices=ACTION_CODE_CHOICES)
    info_target_key = models.TextField(null=True, blank=True)
    decision_duration_ms = models.PositiveIntegerField()
    sanity_before = models.PositiveIntegerField()
    ritual_power_before = models.PositiveIntegerField()
    curse_marks_before = models.PositiveIntegerField()
    opponent_action_code = models.TextField(choices=ACTION_CODE_CHOICES)
    result_code = models.TextField()
    acquired_clue_id = models.TextField(null=True, blank=True)
    clue_truth_state = models.TextField(null=True, blank=True)
    match_outcome = models.TextField(null=True, blank=True)


class StyleMetricSnapshot(models.Model):
    user_id = models.PositiveBigIntegerField()
    aggression = models.FloatField()
    defense = models.FloatField()
    insight_focus = models.FloatField()
    deception = models.FloatField()
    risk_preference = models.FloatField()
    silence_reliance = models.FloatField()
    crisis_guard_rate = models.FloatField()
    crisis_contract_rate = models.FloatField()
    late_choice_rate = models.FloatField()
