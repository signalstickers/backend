from api.serializers import ContributionRequestSerializer
from core.services import new_contribution_request
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class ContributionRequestView(APIView):
    def post(self, request):
        """
        Create a new bot-prevention challenge for the client's IP
        """
        cont_req = new_contribution_request(request.META.get(settings.HEADER_IP))
        return Response(ContributionRequestSerializer(cont_req).data)
