from django.db import models


class StoryCase(models.Model):
    title = models.TextField()
    summary = models.TextField()
    difficulty = models.TextField()
    status = models.TextField()

    class Meta:
        db_table = "story_cases"


class Apparition(models.Model):
    name = models.TextField()
    category = models.TextField()
    description = models.TextField()
    taboo = models.TextField()
    base_policy_json = models.JSONField()

    class Meta:
        db_table = "apparitions"


class Stage(models.Model):
    case_id = models.PositiveBigIntegerField()
    apparition_id = models.PositiveBigIntegerField()
    order = models.PositiveIntegerField()
    victory_condition_json = models.JSONField()

    class Meta:
        db_table = "stages"


class TrueNameFragment(models.Model):
    apparition_id = models.PositiveBigIntegerField()
    label = models.TextField()
    content = models.TextField()
    reveal_condition_json = models.JSONField()

    class Meta:
        db_table = "true_name_fragments"


class FalseClue(models.Model):
    apparition_id = models.PositiveBigIntegerField()
    content = models.TextField()
    trigger_condition_json = models.JSONField()

    class Meta:
        db_table = "false_clues"


class PlayerStoryProgress(models.Model):
    user_id = models.PositiveBigIntegerField()
    stage_id = models.PositiveBigIntegerField()
    status = models.TextField()
    attempts = models.PositiveIntegerField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "player_story_progress"
