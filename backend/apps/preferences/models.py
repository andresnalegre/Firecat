from __future__ import annotations
from django.db import models


class Preferences(models.Model):
    session_key:    models.CharField[str, str]      = models.CharField(max_length=64, unique=True)
    theme:          models.CharField[str, str]      = models.CharField(max_length=40, default='Firecat Dark')
    mode:           models.CharField[str, str]      = models.CharField(max_length=10, default='dark')
    bg_color:       models.CharField[str, str]      = models.CharField(max_length=7,  default='#0f0f0f')
    accent:         models.CharField[str, str]      = models.CharField(max_length=7,  default='#FF5722')
    show_shortcuts: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    updated_at:     models.DateTimeField            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'preferences'

    def __str__(self) -> str:
        return f'Preferences({self.session_key})'