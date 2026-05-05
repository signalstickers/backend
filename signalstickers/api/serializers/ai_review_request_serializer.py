from rest_framework import serializers


class AIReviewRequestSerializer(serializers.Serializer):
    pack_id = serializers.CharField(max_length=32, min_length=32, required=True)
    status = serializers.CharField(required=True)
    review_comment = serializers.CharField(required=False, allow_blank=True)
    tags_match = serializers.BooleanField(required=False, default=False)
    nsfw = serializers.BooleanField(required=False, default=False)
    confidence = serializers.FloatField(required=True)
    alert = serializers.BooleanField(required=False, default=False)
