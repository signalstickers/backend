from api.serializers import StatsPingSerializer
from core.models import Pack, SiteStat
from core.utils import get_current_ym_date
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView


class StatsPingView(APIView):
    parser_classes = (parsers.FormParser,)

    def post(self, request):
        """
        Add a visit to the pack given in JSON parameter for the current month
        """

        req_srl = StatsPingSerializer(data=request.data)
        if not req_srl.is_valid():
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        req_target = req_srl.validated_data["target"]
        current_ym = get_current_ym_date()

        if req_target == "home":
            # Hit the homepage
            month_visit = SiteStat.objects.get_or_create(month=current_ym)[0]
            month_visit.visits += 1
            month_visit.save()
            return Response({})

        # Pack stats
        try:
            pack = Pack.objects.get(pack_id=req_target)
            try:
                pack.stats[current_ym] += 1
            except KeyError:
                pack.stats[current_ym] = 1
            pack.save()
            return Response({})
        except Pack.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
