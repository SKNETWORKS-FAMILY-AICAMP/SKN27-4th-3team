from datetime import timedelta

from django.db import migrations, models


def backfill_turn_started_at(apps, _schema_editor):
    Turn = apps.get_model("matches", "Turn")
    for turn in Turn.objects.all().only("id", "deadline_at"):
        turn.started_at = turn.deadline_at - timedelta(seconds=25)
        turn.save(update_fields=("started_at",))


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0003_match_state_and_clue_ownership"),
    ]

    operations = [
        migrations.AddField(
            model_name="turn",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_turn_started_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="turn",
            name="started_at",
            field=models.DateTimeField(),
        ),
        migrations.CreateModel(
            name="DuelDialogue",
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
                ("match_id", models.PositiveBigIntegerField()),
                ("user_id", models.PositiveBigIntegerField()),
                ("client_nonce", models.UUIDField()),
                ("player_message", models.TextField()),
                ("apparition_message", models.TextField(blank=True, null=True)),
                ("generation_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "duel_dialogues",
            },
        ),
        migrations.AddConstraint(
            model_name="dueldialogue",
            constraint=models.UniqueConstraint(
                fields=("match_id", "user_id", "client_nonce"),
                name="duel_dialogue_match_user_client_nonce_unique",
            ),
        ),
    ]
