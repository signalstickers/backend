import logging

from api.serializers import StatusSerializer
from core.models import Pack, PackStatus
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class StatusView(APIView):
    parser_classes = (parsers.JSONParser,)

    def post(self, request):
        """
        Get the status of a pack
        """

        req_srl = StatusSerializer(data=request.data)

        # Validate the received data
        if not req_srl.is_valid():
            return Response(
                {"error": "Bad request."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pack = Pack.objects.get(
                pack_id=req_srl.validated_data.get("pack_id"),
                pack_key=req_srl.validated_data.get("pack_key"),
            )
            logger.info("Request to StatusView")
            return Response(
                {
                    "error": "",
                    "pack_title": pack.title,
                    "pack_id": pack.pack_id,
                    "status": PackStatus[pack.status].name,
                    "status_comments": (
                        pack.status_comments
                        if PackStatus[pack.status] == PackStatus.REFUSED
                        else ""
                    ),
                }
            )
        except:  # pylint: disable=bare-except
            return Response(
                {
                    "error": "Unknown pack. Check that the signal.art URL is correct, and that you submitted your pack on signalstickers."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
