from apps.api.models import BotPreventionQuestion, ContributionRequest
from rest_framework import serializers


class ContributionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionRequest
        fields = ("id", "question")

    def to_representation(self, obj):
        return {
            "contribution_id": obj.id,
            "contribution_question": obj.question.question,
        }
