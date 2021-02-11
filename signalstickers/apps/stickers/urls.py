from django.conf.urls import include, url
from django.urls import path

from apps.stickers.views import IndexView

urlpatterns = [
    # Packs
    path("", IndexView.as_view())
]
