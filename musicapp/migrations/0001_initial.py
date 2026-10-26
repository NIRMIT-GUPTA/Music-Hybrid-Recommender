# Generated as the initial schema for anonymous favourites and search history.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Favourite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(max_length=40)),
                ("track_id", models.CharField(max_length=100)),
                ("track_name", models.CharField(max_length=500)),
                ("artists", models.CharField(max_length=500)),
                ("track_genre", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SearchHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(max_length=40)),
                ("mode", models.CharField(choices=[("song", "Song"), ("genre", "Genre")], max_length=5)),
                ("query_label", models.CharField(max_length=500)),
                ("track_id", models.CharField(blank=True, max_length=100, null=True)),
                ("genre", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="favourite",
            constraint=models.UniqueConstraint(fields=("session_key", "track_id"), name="unique_session_favourite"),
        ),
    ]
