from django.conf.urls import include, url
from django.urls import path

from apps.api.views import ContributionRequestView, ContributionView, PacksView

urlpatterns = [
    # Packs
    path("packs/", PacksView.as_view(), name="packs"),
    path("contribute/", ContributionView.as_view(), name="contribute"),
    # Contribution request
    path(
        "contributionrequest/",
        ContributionRequestView.as_view(),
        name="contributionrequest",
    ),
]
