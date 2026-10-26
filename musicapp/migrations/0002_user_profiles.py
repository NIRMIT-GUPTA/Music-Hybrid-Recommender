from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("musicapp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="favourite",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="searchhistory",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(model_name="favourite", name="session_key", field=models.CharField(blank=True, max_length=40, null=True)),
        migrations.AlterField(model_name="searchhistory", name="session_key", field=models.CharField(blank=True, max_length=40, null=True)),
        migrations.RemoveConstraint(model_name="favourite", name="unique_session_favourite"),
        migrations.AddConstraint(
            model_name="favourite",
            constraint=models.UniqueConstraint(condition=Q(("user__isnull", False)), fields=("user", "track_id"), name="unique_user_favourite"),
        ),
        migrations.AddConstraint(
            model_name="favourite",
            constraint=models.UniqueConstraint(condition=Q(("session_key__isnull", False), ("user__isnull", True)), fields=("session_key", "track_id"), name="unique_guest_favourite"),
        ),
    ]
