from apps.api.utils import remove_empty_values
from apps.stickers.models import Pack, Tag
from rest_framework import serializers


class TagSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        return data


class PackSerializer(serializers.ModelSerializer):
    tags = TagSlugRelatedField(
        many=True, slug_field="name", queryset=Tag.objects.none()
    )

    class Meta:
        model = Pack
        fields = (
            "pack_id",
            "pack_key",
            "source",
            "tags",
            "nsfw",
            "original",
            "editorschoice",
        )

    def to_representation(self, obj):

        return remove_empty_values(
            {
                "meta": {
                    "id": obj.pack_id,
                    "key": obj.pack_key,
                    "source": obj.source,
                    "tags": [tag.name for tag in obj.tags.all()],
                    "nsfw": obj.nsfw,
                    "original": obj.original,
                    "animated": obj.animated,
                    "editorschoice": obj.editorschoice,
                },
                "manifest": {
                    "title": obj.title,
                    "author": obj.author,
                    "cover": {"id": obj.id_cover},
                },
            }
        )
