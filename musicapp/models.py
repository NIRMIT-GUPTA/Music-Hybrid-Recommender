from django.conf import settings
from django.db import models
from django.db.models import Q


class Favourite(models.Model):
    """A saved song, owned by a registered user (or legacy guest session)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    track_id = models.CharField(max_length=100)
    track_name = models.CharField(max_length=500)
    artists = models.CharField(max_length=500)
    track_genre = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "track_id"], condition=Q(user__isnull=False), name="unique_user_favourite"),
            models.UniqueConstraint(fields=["session_key", "track_id"], condition=Q(user__isnull=True, session_key__isnull=False), name="unique_guest_favourite"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.track_name} — {self.artists}"


class SearchHistory(models.Model):
    """Recent recommendations owned by a registered user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    mode = models.CharField(max_length=5, choices=[("song", "Song"), ("genre", "Genre")])
    query_label = models.CharField(max_length=500)
    track_id = models.CharField(max_length=100, null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.query_label
