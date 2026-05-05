from core.models import Pack
from rest_framework import serializers


class InReviewPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pack
        fields = ()

    def to_representation(self, instance):
        return {
            "id": instance.pack_id,
            "key": instance.pack_key,
            "source": instance.source,
            "submitter_comments": instance.submitter_comments,
            "tags": [tag.name for tag in instance.tags.all()],
        }
