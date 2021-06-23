from rest_framework import serializers


class StatusSerializer(serializers.Serializer):
    pack_id = serializers.CharField(max_length=32, min_length=32, required=True)
    pack_key = serializers.CharField(max_length=64, min_length=64, required=True)
