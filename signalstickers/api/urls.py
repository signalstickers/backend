from django.conf.urls import include, url
from django.urls import path

from api.views import PacksListView, PackView

urlpatterns = [
    path("packs/", PacksListView.as_view()),
    path("packs/<pack_id>/", PackView.as_view()),
]
