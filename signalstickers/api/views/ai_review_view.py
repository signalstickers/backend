import logging

from api.serializers import AIReviewRequestSerializer
from core.models import AIReview, Pack
from django.conf import settings
from rest_framework import parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("main")


class AIReviewView(APIView):
    parser_classes = (parsers.JSONParser,)

    def put(self, request):
        """
        Upsert an AI review for a pack
        """

        api_key = request.headers.get("X-Auth-Token")
        if not api_key or api_key != settings.AI_REVIEW_API_KEY:
            return Response(
                {"error": "Bad API key"}, status=status.HTTP_401_UNAUTHORIZED
            )

        req_srl = AIReviewRequestSerializer(data=request.data)

        if not req_srl.is_valid():
            errs_list = []
            for err_list in req_srl.errors.values():
                if isinstance(err_list, list):
                    for err in err_list:
                        errs_list.append(str(err))
                else:
                    for err in err_list.values():
                        errs_list.append(str(err[0]))
            return Response(", ".join(errs_list), status=status.HTTP_400_BAD_REQUEST)

        data = req_srl.validated_data

        try:
            pack = Pack.objects.get(pack_id=data["pack_id"])
        except Pack.DoesNotExist:
            return Response(
                {"error": "Unknown pack."}, status=status.HTTP_404_NOT_FOUND
            )

        review, created = AIReview.objects.update_or_create(
            pack=pack,
            defaults={
                "status": data["status"],
                "review_comment": data.get("review_comment", ""),
                "nsfw": data.get("nsfw", False),
                "tags_match": data.get("tags_match", False),
                "confidence": data["confidence"],
                "alert": data.get("alert", False),
            },
        )
        review.full_clean()
        review.save()

        logger.info(
            "AI review %s for pack %s",
            "created" if created else "updated",
            pack.pack_id,
        )
        return Response({"success": True})
