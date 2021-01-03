from rest_framework import serializers


class StatsPingSerializer(serializers.Serializer):
    target = serializers.CharField(max_length=32, required=True)
