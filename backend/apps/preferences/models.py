from django.db import models

class Preferences(models.Model):
    session_key    = models.CharField(max_length=64, unique=True)
    theme          = models.CharField(max_length=40, default='Firecat Dark')
    mode           = models.CharField(max_length=10, default='dark')
    bg_color       = models.CharField(max_length=7,  default='#0f0f0f')
    accent         = models.CharField(max_length=7,  default='#FF5722')
    show_shortcuts = models.BooleanField(default=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'preferences'

    def __str__(self):
        return f'Preferences({self.session_key})'