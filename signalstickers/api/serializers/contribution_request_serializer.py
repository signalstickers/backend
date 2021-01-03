from api.models import ContributionRequest
from rest_framework import serializers


class ContributionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionRequest
        fields = ("id", "question")

    def to_representation(self, instance):
        return {
            "contribution_id": instance.id,
            "contribution_question": instance.question.question,
        }
