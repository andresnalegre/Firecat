from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve
from apps.search.views import SearchProxyView
from apps.search.proxy_views import WebProxyView

urlpatterns = [
    path('admin/',           admin.site.urls),
    path('api/preferences/', include('apps.preferences.urls')),
    path('api/bookmarks/',   include('apps.bookmarks.urls')),
    path('api/history/',     include('apps.history.urls')),
    path('api/search/',      SearchProxyView.as_view(), name='search-proxy'),
    path('api/proxy/',       WebProxyView.as_view(),    name='web-proxy'),

    re_path(r'^assets/(?P<path>.*)$', serve, {
        'document_root': str(settings.FRONTEND_DIST / 'assets'),
    }),

    re_path(r'^(?P<path>.*\..*)$', serve, {
        'document_root': str(settings.FRONTEND_DIST),
    }),

    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
]