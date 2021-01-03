from api.serializers import PackSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from stickers.services import get_pack


class PackDetailsView(APIView):
    def get(self, request, pack_id):
        pack = get_pack(pack_id)
        return Response(PackSerializer(pack).data)
