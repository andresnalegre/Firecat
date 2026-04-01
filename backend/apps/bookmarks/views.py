from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Bookmark
from .serializers import BookmarkSerializer

def _session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

class BookmarkListView(APIView):
    def get(self, request):
        qs = Bookmark.objects.filter(session_key=_session(request))
        return Response(BookmarkSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BookmarkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(session_key=_session(request))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookmarkDetailView(APIView):
    def delete(self, request, pk):
        try:
            bookmark = Bookmark.objects.get(pk=pk, session_key=_session(request))
            bookmark.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Bookmark.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)