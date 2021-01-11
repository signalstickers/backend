from api.serializers import (
    APIPackRequestSerializer,
    PackRequestSerializer,
    PackSerializer,
)
from api.services import check_api_key, check_contribution_request
from django.core.cache import cache
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
        cache_key = "view__api_packs_list"

        cached_data = cache.get(cache_key)

        if cached_data:
            print("###HIT")
            return Response(cached_data, headers={"X-Cache": "HIT"})

        print("### MISS")

        data = get_all_online_packs()
        serialized_data = PackSerializer(data, many=True).data
        cache.set(cache_key, serialized_data)
        print(cache.get(cache_key))

        return Response(serialized_data, headers={"X-Cache": "MISS"})

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
