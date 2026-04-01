from rest_framework import serializers
from .models import HistoryEntry

class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = HistoryEntry
        fields = ['id', 'title', 'url', 'visited_at']
        read_only_fields = ['id', 'visited_at']