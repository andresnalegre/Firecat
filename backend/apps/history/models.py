from django.db import models

class HistoryEntry(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    title       = models.CharField(max_length=255)
    url         = models.URLField(max_length=2000)
    visited_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visited_at']

    def __str__(self):
        return f'{self.title} @ {self.visited_at:%Y-%m-%d %H:%M}'