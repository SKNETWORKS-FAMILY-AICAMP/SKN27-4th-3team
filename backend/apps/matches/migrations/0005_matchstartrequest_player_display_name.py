from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0004_turn_started_at_and_duel_dialogue"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchstartrequest",
            name="player_display_name",
            field=models.TextField(blank=True, null=True),
        ),
    ]
