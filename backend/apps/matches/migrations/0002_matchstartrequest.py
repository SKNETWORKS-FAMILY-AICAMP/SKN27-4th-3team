from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchStartRequest",
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
                ("user_id", models.PositiveBigIntegerField()),
                ("client_request_id", models.UUIDField()),
                ("case_id", models.TextField()),
                ("match_id", models.PositiveBigIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "match_start_requests",
            },
        ),
        migrations.AddConstraint(
            model_name="matchstartrequest",
            constraint=models.UniqueConstraint(
                fields=("user_id", "client_request_id"),
                name="match_start_request_user_client_request_unique",
            ),
        ),
    ]
