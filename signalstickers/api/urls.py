from django.conf.urls import include, url
from django.urls import path

from api.views import ContributionRequestView, PackDetailsView, PacksView

urlpatterns = [
    # Packs
    path("packs/", PacksView.as_view()),
    path("packs/<pack_id>/", PackDetailsView.as_view()),
    # Contribution request
    path("contributionrequest/", ContributionRequestView.as_view()),
]
