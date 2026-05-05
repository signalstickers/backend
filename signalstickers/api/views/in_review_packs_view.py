from api.serializers import InReviewPackSerializer
from core.models import Pack
from django.conf import settings
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView


class InReviewPacksView(APIView):
    parser_classes = (parsers.JSONParser,)

    def get(self, request):
        api_key = request.headers.get("X-Auth-Token")
        if not api_key or api_key != settings.AI_REVIEW_API_KEY:
            return Response(
                {"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )
        packs = Pack.objects.in_review_with_tags().order_by("id")
        serializer = InReviewPackSerializer(packs, many=True)
        return Response(serializer.data)
