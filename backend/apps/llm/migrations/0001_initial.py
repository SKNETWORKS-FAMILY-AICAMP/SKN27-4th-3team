from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LlmGeneration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("purpose", models.TextField()),
                ("provider", models.TextField()),
                ("model_id", models.TextField(blank=True, null=True)),
                ("status", models.TextField()),
                ("fallback_used", models.BooleanField()),
                ("generated_text", models.TextField(blank=True, null=True)),
                ("match_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("turn_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("user_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("metadata_json", models.JSONField(default=dict)),
                ("context_refs_json", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "llm_generations",
            },
        ),
    ]
