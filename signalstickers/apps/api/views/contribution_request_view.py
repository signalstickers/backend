from apps.api.serializers import ContributionRequestSerializer
from apps.api.services import new_contribution_request
from apps.stickers.models import Pack, PackStatus
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class ContributionRequestView(APIView):
    def post(self, request):
        cont_req = new_contribution_request(request.META.get(settings.HEADER_IP))
        return Response(ContributionRequestSerializer(cont_req).data)
