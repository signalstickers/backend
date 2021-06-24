from rest_framework import serializers

from .pack_serializer import PackSerializer


class PackRequestSerializer(serializers.Serializer):
    pack = PackSerializer()
    contribution_id = serializers.UUIDField(format="hex_verbose", required=True)
    contribution_answer = serializers.CharField(max_length=200, required=True)
    submitter_comments = serializers.CharField(
        max_length=400, required=False, allow_blank=True
    )


class APIPackRequestSerializer(serializers.Serializer):
    pack = PackSerializer()

