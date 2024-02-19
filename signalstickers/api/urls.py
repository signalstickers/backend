from api.views import (
    ContributionRequestView,
    ContributionView,
    PacksView,
    ReportView,
    StatsPingView,
    StatusView,
)
from django.urls import path

urlpatterns = [
    # Packs
    path("packs/", PacksView.as_view(), name="packs"),
    path("ping/", StatsPingView.as_view(), name="statsping"),
    path("packs/status/", StatusView.as_view(), name="packstatus"),
    path("report/", ReportView.as_view(), name="report"),
    path("contribute/", ContributionView.as_view(), name="contribute"),
    # Contribution request
    path(
        "contributionrequest/",
        ContributionRequestView.as_view(),
        name="contributionrequest",
    ),
]
