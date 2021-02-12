from apps.api.serializers import (
    APIPackRequestSerializer,
    PackRequestSerializer,
    PackSerializer,
)
from apps.api.services import check_api_key, check_contribution_request
from apps.stickers.models import Pack, PackStatus
from apps.stickers.services import new_pack
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView


class PacksView(APIView):
    parser_classes = (parsers.JSONParser,)

    def get(self, request):
        """
        List all packs
        """
        all_packs = Pack.objects.onlines()
        serializer = PackSerializer(all_packs, many=True)
        return Response(serializer.data)

    def put(self, request):
        """
        Propose a new pack
        """

        api_key = request.headers.get("X-Auth-Token")

        if api_key:
            req_srl = APIPackRequestSerializer(data=request.data)
        else:
            req_srl = PackRequestSerializer(data=request.data)

        # Validate the received data
        if not req_srl.is_valid():
            return Response(
                {"notvaliderrors": req_srl.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        if api_key:
            # Check API key
            api_obj = check_api_key(api_key)
            if not api_obj:
                return Response({"error": "Bad API key."})
            api_via = api_obj.name
        else:
            # Check contribution request
            is_cont_req_valid, cont_req_errors = check_contribution_request(
                req_srl.validated_data.get("contribution_id"),
                req_srl.validated_data.get("contribution_answer"),
                request.META.get("REMOTE_ADDR"),
            )
            if not is_cont_req_valid:
                return Response(
                    {"error": cont_req_errors}, status=status.HTTP_400_BAD_REQUEST
                )
            api_via = ""

        # Create pack in review
        try:
            pack = new_pack(
                status=PackStatus.IN_REVIEW.name,
                **req_srl.validated_data["pack"],
                submitter_comments=req_srl.validated_data.get("submitter_comments", ""),
                api_via=api_via
            )
        except ValidationError as val_err:
            return Response(
                {"error": val_err.message}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"success": bool(pack)})
