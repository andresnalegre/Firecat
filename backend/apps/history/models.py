from __future__ import annotations
from django.db import models


class HistoryEntry(models.Model):
    session_key: models.CharField[str, str] = models.CharField(max_length=64, db_index=True)
    title:       models.CharField[str, str] = models.CharField(max_length=255)
    url:         models.URLField[str, str]  = models.URLField(max_length=2000)
    visited_at:  models.DateTimeField       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visited_at']

    def __str__(self) -> str:
        return f'{self.title} @ {self.visited_at:%Y-%m-%d %H:%M}'