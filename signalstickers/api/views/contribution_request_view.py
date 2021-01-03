from api.serializers import ContributionRequestSerializer
from api.services import new_contribution_request
from rest_framework.response import Response
from rest_framework.views import APIView
from stickers.models import Pack, PackStatus


class ContributionRequestView(APIView):
    def post(self, request):
        cont_req = new_contribution_request(request.META.get("REMOTE_ADDR"))
        return Response(ContributionRequestSerializer(cont_req).data)
