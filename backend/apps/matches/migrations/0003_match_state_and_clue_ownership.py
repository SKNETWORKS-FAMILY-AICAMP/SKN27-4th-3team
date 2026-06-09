from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0002_matchstartrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchparticipant",
            name="false_clues",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="matchparticipant",
            name="incomplete_true_name_fragments",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="matchparticipant",
            name="shield",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="matchparticipant",
            name="suspicion",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="matchparticipant",
            name="timeout_count",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="matchparticipant",
            name="true_name_fragments",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="MatchFalseClueOwnership",
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
                ("participant_id", models.PositiveBigIntegerField()),
                ("false_clue_id", models.PositiveBigIntegerField()),
                (
                    "truth_state",
                    models.TextField(
                        choices=[
                            ("unknown", "unknown"),
                            ("true_revealed", "true_revealed"),
                            ("false_revealed", "false_revealed"),
                        ]
                    ),
                ),
                ("source_turn_id", models.PositiveBigIntegerField()),
                ("source_turn_number", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "match_false_clues",
            },
        ),
        migrations.CreateModel(
            name="MatchTrueNameFragmentOwnership",
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
                ("participant_id", models.PositiveBigIntegerField()),
                ("true_name_fragment_id", models.PositiveBigIntegerField()),
                ("source_turn_id", models.PositiveBigIntegerField()),
                ("source_turn_number", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "match_true_name_fragments",
            },
        ),
        migrations.AddConstraint(
            model_name="matchfalseclueownership",
            constraint=models.UniqueConstraint(
                fields=("match_id", "participant_id", "false_clue_id"),
                name="match_false_clue_ownership_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="matchtruenamefragmentownership",
            constraint=models.UniqueConstraint(
                fields=("match_id", "participant_id", "true_name_fragment_id"),
                name="match_true_name_fragment_ownership_unique",
            ),
        ),
    ]
