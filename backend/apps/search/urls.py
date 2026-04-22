from django.urls import path
from .views        import SearchProxyView, SearchGroupsView
from .proxy_views  import WebProxyView
from .inspect_view import InspectView

urlpatterns = [
    path("",         SearchProxyView.as_view(),  name="search"),
    path("groups/",  SearchGroupsView.as_view(), name="search-groups"),
    path("inspect/", InspectView.as_view(),      name="search-inspect"),
    path("proxy/",   WebProxyView.as_view(),     name="web-proxy"),
]