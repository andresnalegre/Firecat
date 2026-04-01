from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Preferences
from .serializers import PreferencesSerializer

def _get_or_create(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    return Preferences.objects.get_or_create(session_key=session_key)

class PreferencesView(APIView):
    def get(self, request):
        prefs, _ = _get_or_create(request)
        return Response(PreferencesSerializer(prefs).data)

    def post(self, request):
        prefs, _ = _get_or_create(request)
        serializer = PreferencesSerializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)