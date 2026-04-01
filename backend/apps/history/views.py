import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import HistoryEntry
from .serializers import HistorySerializer


def _session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def normalise_url(url):
    """Strip www, trailing slash and lowercase for deduplication."""
    if not url:
        return url
    url = url.strip().lower()
    url = re.sub(r'^https?://www\.', 'https://', url)
    url = url.rstrip('/')
    return url


class HistoryListView(APIView):

    def get(self, request):
        qs = HistoryEntry.objects.filter(session_key=_session(request)).order_by('-visited_at')[:500]
        return Response(HistorySerializer(qs, many=True).data)

    def post(self, request):
        url   = request.data.get('url', '').strip()
        title = request.data.get('title', '').strip()

        if not url:
            return Response({'error': 'URL required'}, status=status.HTTP_400_BAD_REQUEST)

        session_key = _session(request)
        norm        = normalise_url(url)

        for entry in HistoryEntry.objects.filter(session_key=session_key):
            if normalise_url(entry.url) == norm:
                entry.delete()

        serializer = HistorySerializer(data={'url': url, 'title': title})
        if serializer.is_valid():
            serializer.save(session_key=session_key)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        HistoryEntry.objects.filter(session_key=_session(request)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HistoryDetailView(APIView):

    def delete(self, request, pk):
        try:
            entry = HistoryEntry.objects.get(pk=pk, session_key=_session(request))
            entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except HistoryEntry.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)