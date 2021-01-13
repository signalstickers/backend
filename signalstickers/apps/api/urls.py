from django.conf.urls import include, url
from django.urls import path

from apps.api.views import ContributionRequestView, PacksView

urlpatterns = [
    # Packs
    path("packs/", PacksView.as_view()),
    # Contribution request
    path("contributionrequest/", ContributionRequestView.as_view()),
]
