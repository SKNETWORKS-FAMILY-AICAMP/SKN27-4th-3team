from django.db import models


class LlmGeneration(models.Model):
    purpose = models.TextField()
    provider = models.TextField()
    model_id = models.TextField(null=True, blank=True)
    status = models.TextField()
    fallback_used = models.BooleanField()
    generated_text = models.TextField(null=True, blank=True)
    match_id = models.PositiveBigIntegerField(null=True, blank=True)
    turn_id = models.PositiveBigIntegerField(null=True, blank=True)
    user_id = models.PositiveBigIntegerField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict)
    context_refs_json = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_generations"
