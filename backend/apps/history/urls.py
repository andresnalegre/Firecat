from django.urls import path
from .views import HistoryListView, HistoryDetailView

urlpatterns = [
    path('',          HistoryListView.as_view(),   name='history-list'),
    path('<int:pk>/', HistoryDetailView.as_view(), name='history-detail'),
]