from api.serializers import ReportSerializer
from core.models import Pack, Report
from core.notifications import NotificationPriority, notify
from core.services import check_contribution_request
from core.utils import admin_url
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
        if not req_srl.is_valid():
            return Response(
                {"error": "Invalid report."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = req_srl.validated_data

        is_cont_req_valid, _ = check_contribution_request(
            data.get("contribution_id"),
            data.get("contribution_answer"),
            request.META.get(settings.HEADER_IP),
        )
        if not is_cont_req_valid:
            return Response(
                {"error": "Invalid contribution request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pack = Pack.objects.get(pack_id=data["pack_id"])
        except Pack.DoesNotExist:
            return Response(
                {"error": "Unknown pack."}, status=status.HTTP_404_NOT_FOUND
            )

        report = Report.objects.create(content=data["content"], pack=pack)

        notify(
            "signalstickers-packs",
            "Pack reported",
            f"Pack reported: {pack.title}",
            priority=NotificationPriority.HIGH,
            click_url=admin_url(),
        )

        return Response({"success": bool(report)})
