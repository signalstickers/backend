from api.serializers import PackSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from stickers.models import Pack, PackStatus


class PacksListView(APIView):
    def get(self, request):
        data = Pack.objects.filter(status=PackStatus.ONLINE.name).order_by("-id")
        return Response(PackSerializer(data, many=True).data)


class PackView(APIView):
    def get(self, request, pack_id):
        data = Pack.objects.get(pack_id=pack_id)
        return Response(PackSerializer(data).data)
