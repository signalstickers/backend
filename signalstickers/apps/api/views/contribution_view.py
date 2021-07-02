from apps.api.serializers import APIPackRequestSerializer, PackRequestSerializer
from apps.api.services import check_api_key, check_contribution_request
from apps.core.services import send_email_on_pack_propose
from apps.stickers.models import Pack, PackStatus
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiException(Exception):
    def __init__(self, message, status=status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.status = status


class ContributionView(APIView):
    parser_classes = (parsers.JSONParser,)

    def put(self, request):
        """
        Propose a new pack
        """
        try:
            api_key = request.headers.get("X-Auth-Token")

            if api_key:
                api_obj = check_api_key(api_key)
                if not api_obj:
                    raise ApiException(
                        "Bad API key", status=status.HTTP_401_UNAUTHORIZED
                    )

                api_via = api_obj.name
                req_srl = APIPackRequestSerializer(data=request.data)

            else:
                req_srl = PackRequestSerializer(data=request.data)

            # Validate the received data
            if not req_srl.is_valid():

                errs_list = []
                for err_cat, err_list in req_srl.errors.items():
                    if err_cat == "contribution_answer":
                        err_list.append("Please answer the question.")
                        continue
                    if err_cat == "contribution_id":
                        errs_list.append("Invalid contribution request. Try again.")
                        continue
                    for err in err_list.values():
                        if err[0].startswith("pack with this pack id already exists"):
                            errs_list.append(
                                "This pack already exists, or has already been proposed (and is waiting for its approval)."
                            )
                        else:
                            errs_list.append(err[0])

                raise ApiException(", ".join(errs_list))

            if not api_key:
                # Check contribution request
                is_cont_req_valid, cont_req_errors = check_contribution_request(
                    req_srl.validated_data.get("contribution_id"),
                    req_srl.validated_data.get("contribution_answer"),
                    request.META.get(settings.HEADER_IP),
                )
                if not is_cont_req_valid:
                    raise ApiException(str(cont_req_errors))

                api_via = ""

            # Create pack in review
            try:
                pack = Pack.objects.new(
                    status=PackStatus.IN_REVIEW.name,
                    **req_srl.validated_data["pack"],
                    submitter_comments=req_srl.validated_data.get(
                        "submitter_comments", ""
                    ),
                    api_via=api_via,
                )
            except ValidationError as val_err:
                raise ApiException(str(val_err))

            send_email_on_pack_propose(pack)
            return Response({"success": bool(pack)})

        except ApiException as api_err:
            return Response({"error": str(api_err)}, status=api_err.status)
