from apps.api.serializers import PackSerializer
from apps.stickers.models import Pack
from rest_framework import parsers
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
