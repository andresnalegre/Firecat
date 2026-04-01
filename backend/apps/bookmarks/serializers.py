from rest_framework import serializers
from .models import Bookmark


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bookmark
        fields = ['id', 'title', 'url', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            value = f'https://{value}'
        return value