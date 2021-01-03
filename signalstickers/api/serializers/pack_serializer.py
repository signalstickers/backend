from rest_framework import serializers
from stickers.models import Pack, Tag


class PackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pack

    def to_representation(self, obj):
        return {
            "meta": {
                "id": obj.pack_id,
                "key": obj.pack_key,
                "source": obj.source,
                "tags": [tag.name for tag in obj.tags.all()],
                "nsfw": obj.nsfw,
                "original": obj.original,
                "animated": obj.animated,
            },
            "manifest": {
                "title": obj.title,
                "author": obj.author,
                "cover": {"id": 0},  # FIXME
            },
        }
