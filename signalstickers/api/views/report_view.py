from api.serializers import ReportSerializer
from api.services import check_contribution_request
from core.models import Pack, Report
from django.conf import settings
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView


class ReportView(APIView):
    parser_classes = (parsers.JSONParser,)

    def put(self, request):
        """
        Create a report for a pack
        """

        req_srl = ReportSerializer(data=request.data)

        if req_srl.is_valid():

            is_cont_req_valid, _ = check_contribution_request(
                req_srl.validated_data.get("contribution_id"),
                req_srl.validated_data.get("contribution_answer"),
                request.META.get(settings.HEADER_IP),
            )
            if not is_cont_req_valid:
                return Response(
                    {"error": "Invalid contribution request."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                pack = Pack.objects.get(pack_id=req_srl.validated_data["pack_id"])
            except Pack.DoesNotExist:
                return Response(
                    {"error": "Unknown pack."}, status=status.HTTP_404_NOT_FOUND
                )

            report = Report.objects.create(
                content=req_srl.validated_data["content"],
                pack=pack,
            )

            return Response({"success": bool(report)})

        return Response(
            {"error": "Invalid report."}, status=status.HTTP_400_BAD_REQUEST
        )
