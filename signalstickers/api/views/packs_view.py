from api.serializers import PackRequestSerializer, PackSerializer
from api.services import check_contribution_request
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from stickers.models import PackStatus
from stickers.services import get_all_online_packs, new_pack


# /packs/{}
class PacksView(APIView):
    parser_classes = (parsers.JSONParser,)

    def get(self, request):
        """
        Get the list of all published packs on the site.
        """
        data = get_all_online_packs()
        return Response(PackSerializer(data, many=True).data)

    def put(self, request):

        req_srl = PackRequestSerializer(data=request.data)

        if not req_srl.is_valid():
            # These errors should be caught by the UI before sending, so no
            # pretty message here.
            return Response(
                {"errors": req_srl.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check contribution request
        is_cont_req_valid, cont_req_errors = check_contribution_request(
            req_srl.validated_data.get("contribution_id"),
            req_srl.validated_data.get("contribution_answer"),
            request.META.get("REMOTE_ADDR"),
        )

        if not is_cont_req_valid:
            return Response({"error": cont_req_errors})

        try:
            pack = new_pack(
                status=PackStatus.IN_REVIEW.name,
                **req_srl.validated_data["pack"],
                submitter_comments=req_srl.validated_data.get("submitter_comments"),
            )
        except ValidationError as val_err:
            return Response(
                {"error": val_err.message}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"success": bool(pack)})
