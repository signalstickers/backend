from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    contribution_id = serializers.UUIDField(format="hex_verbose", required=True)
    contribution_answer = serializers.CharField(max_length=200, required=True)
    pack_id = serializers.CharField(
        max_length=32,
        min_length=32,
        required=True,
    )
    content = serializers.CharField(
        max_length=2000,
        min_length=30,
        required=True,
    )
