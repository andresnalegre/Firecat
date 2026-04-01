from rest_framework import serializers
from .models import Preferences

class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Preferences
        fields = ['theme', 'mode', 'bg_color', 'accent', 'show_shortcuts', 'updated_at']
        read_only_fields = ['updated_at']